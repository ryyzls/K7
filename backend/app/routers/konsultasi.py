"""Router publik: jadwal & reservasi konsultasi dokter (data dinamis di SQL, RS dari RDF).

Validasi ketersediaan dilakukan di database (stored function sp_buat_reservasi_konsultasi):
hari praktik, sesi belum lewat, dan kuota sesi, semuanya atomik dengan advisory lock.
"""
import datetime
import hashlib
import secrets
import string
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.availability_service import hospital_name

router = APIRouter(prefix="/api/konsultasi", tags=["Konsultasi"])
_PGCODE_STATUS = {"CS409": 409, "CS404": 404, "CS422": 422}


class ReservasiCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    jadwal_id: int = Field(gt=0)
    nama_pasien: str = Field(min_length=1, max_length=100)
    no_telp: str = Field(min_length=5, max_length=20)
    tanggal: datetime.date
    keluhan: str | None = Field(default=None, max_length=1000)


def _kode() -> str:
    suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"KS-{datetime.date.today():%Y%m%d}-{suffix}"


def _digits(v: str) -> str:
    return "".join(c for c in v if c.isdigit())


@router.get("/{kode_rs}", summary="Jadwal praktik dokter di RS; beri ?tanggal= untuk sisa kuota pada hari itu")
def jadwal_rs(kode_rs: str, tanggal: datetime.date | None = None, db: Session = Depends(get_db)):
    if not hospital_name(kode_rs):
        raise HTTPException(404, "Rumah sakit tidak ditemukan dalam dataset semantik")
    rows = db.execute(
        text(
            "SELECT j.id, j.nama_dokter, j.spesialisasi, j.hari, "
            "to_char(j.jam_mulai,'HH24:MI') AS jam_mulai, to_char(j.jam_selesai,'HH24:MI') AS jam_selesai, "
            "j.kuota_per_sesi, "
            "CASE WHEN CAST(:t AS date) IS NULL THEN NULL ELSE fn_sisa_kuota_konsultasi(j.id, CAST(:t AS date)) END AS sisa "
            "FROM jadwal_konsultasi j "
            "WHERE j.rs_id = :rs AND j.aktif "
            "AND (CAST(:t AS date) IS NULL OR j.hari = EXTRACT(ISODOW FROM CAST(:t AS date))::int) "
            "ORDER BY j.hari, j.jam_mulai"
        ),
        {"rs": kode_rs, "t": tanggal},
    ).mappings().all()
    return {"kode_rs": kode_rs, "tanggal": tanggal, "items": [dict(r) for r in rows]}


@router.post("/reservasi", status_code=201, summary="Buat reservasi konsultasi (transaksi ACID)")
def buat_reservasi(data: ReservasiCreate, db: Session = Depends(get_db),
                   idempotency_key: Annotated[str | None, Header(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")] = None):
    idem = hashlib.sha256(idempotency_key.encode()).hexdigest() if idempotency_key else None
    for _ in range(5):
        kode = _kode()
        try:
            new_id = db.execute(
                text("SELECT sp_buat_reservasi_konsultasi(:kode,:jadwal,:pasien,:telp,:tgl,:keluhan,:idem)"),
                dict(kode=kode, jadwal=data.jadwal_id, pasien=data.nama_pasien, telp=data.no_telp,
                     tgl=data.tanggal, keluhan=data.keluhan, idem=idem),
            ).scalar_one()
            row = db.execute(
                text("SELECT id, kode_reservasi, jadwal_id, rs_id, nama_pasien, no_telp, tanggal, keluhan, status, created_at "
                     "FROM reservasi_konsultasi WHERE id = :id"), {"id": new_id}).mappings().one()
            result = dict(row)
            db.commit()
            result["nama_rs"] = hospital_name(result["rs_id"]) or result["rs_id"]
            return result
        except IntegrityError as exc:
            db.rollback()
            c = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
            if "kode_reservasi" in c:
                continue
            if "idempotency_key" in c:
                raise HTTPException(409, "Idempotency-Key sudah dipakai; reservasi sudah tercatat") from None
            if "uq_reservasi_pasien_aktif" in c:
                raise HTTPException(409, "Nomor telepon ini sudah punya reservasi aktif pada sesi tersebut") from None
            raise HTTPException(409, "Data reservasi tidak memenuhi aturan database") from None
        except DBAPIError as exc:
            db.rollback()
            orig = getattr(exc, "orig", None)
            code = getattr(orig, "pgcode", "") or ""
            msg = getattr(getattr(orig, "diag", None), "message_primary", "") or ""
            if code in _PGCODE_STATUS:
                raise HTTPException(_PGCODE_STATUS[code], msg) from None
            raise HTTPException(503, "Database tidak tersedia; coba lagi nanti") from None
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(503, "Database tidak tersedia; coba lagi nanti") from None
    raise HTTPException(409, "Gagal membuat kode reservasi unik; coba lagi")


@router.get("/reservasi/{kode}", summary="Cek status reservasi (kode + nomor telepon)")
def cek_reservasi(kode: str, no_telp: Annotated[str, Query(min_length=5, max_length=20)], db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT r.kode_reservasi, r.rs_id, r.nama_pasien, r.no_telp, r.tanggal, r.status, "
             "j.nama_dokter, j.spesialisasi, to_char(j.jam_mulai,'HH24:MI') AS jam_mulai, "
             "to_char(j.jam_selesai,'HH24:MI') AS jam_selesai "
             "FROM reservasi_konsultasi r JOIN jadwal_konsultasi j ON j.id = r.jadwal_id "
             "WHERE r.kode_reservasi = :k"), {"k": kode.upper()}).mappings().first()
    if not row or not secrets.compare_digest(_digits(no_telp).encode(), _digits(row["no_telp"]).encode()):
        raise HTTPException(403, "Kode reservasi dan nomor telepon tidak cocok")
    out = dict(row)
    out["nama_rs"] = hospital_name(out["rs_id"]) or out["rs_id"]
    return out
