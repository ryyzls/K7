"""Router: Booking Kamar Rawat Inap (Tubes MSBD).

Transaksi ACID: pembuatan booking dipanggil lewat stored function sp_buat_booking
(advisory lock per RS+jenis kamar, cek kuota, INSERT) dalam satu transaksi dengan
ledger idempotency. Semua SQL diparameterisasi. Data deskriptif RS tidak disimpan di
SQL: nama RS selalu diambil dari RDF.
"""
import datetime
import hashlib
import json
import secrets
import string
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.database.models import BookingKamar
from app.database.orm_models import User
from app.routers.auth_pasien import get_optional_user
from app.services import sparql_service as sp
from app.services.availability_service import hospital_name, kamar_availability

router = APIRouter(prefix="/api", tags=["Booking"])

_SCOPE = "POST:/api/booking:v1"
_PGCODE_STATUS = {"CS409": 409, "CS404": 404, "CS422": 422}


# ─── Pydantic Schema ─────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    _request_hash: str = PrivateAttr(default="")
    model_config = ConfigDict(str_strip_whitespace=True)
    kode_rs: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    nama_rs: str = Field(min_length=1, max_length=200)
    nama_pasien: str = Field(min_length=1, max_length=100)
    no_telp: str = Field(min_length=1, max_length=20)
    tanggal_masuk: datetime.date
    tanggal_keluar: datetime.date | None = None
    jenis_kamar: str
    catatan: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validasi_tanggal(self):
        if self.tanggal_keluar and self.tanggal_keluar < self.tanggal_masuk:
            raise ValueError("tanggal_keluar harus setelah atau sama dengan tanggal_masuk")
        if self.tanggal_keluar and (self.tanggal_keluar - self.tanggal_masuk).days > 365:
            raise ValueError("lama rawat inap maksimal 365 hari")
        return self

    @field_validator("jenis_kamar")
    @classmethod
    def validasi_jenis(cls, v: str) -> str:
        pilihan = {"VIP", "Kelas I", "Kelas II", "Kelas III", "ICU"}
        if v not in pilihan:
            raise ValueError(f"jenis_kamar harus salah satu dari: {', '.join(sorted(pilihan))}")
        return v


class BookingResponse(BaseModel):
    id: int
    kode_booking: str
    kode_rs: str
    nama_rs: str
    nama_pasien: str
    no_telp: str
    tanggal_masuk: datetime.date
    tanggal_keluar: datetime.date | None
    jenis_kamar: str
    catatan: str | None
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ─── Helper ──────────────────────────────────────────────────────────────────

def _generate_kode() -> str:
    today = datetime.date.today().strftime("%Y%m%d")
    suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"BK-{today}-{suffix}"


def _response(b: BookingKamar, nama_rs: str | None = None) -> BookingResponse:
    """Nama RS dari RDF (golden rule polyglot); kolom lama hanya fallback."""
    nama = nama_rs or hospital_name(b.kode_rs) or b.nama_rs or b.kode_rs
    return BookingResponse(
        id=b.id, kode_booking=b.kode_booking, kode_rs=b.kode_rs, nama_rs=nama,
        nama_pasien=b.nama_pasien, no_telp=b.no_telp, tanggal_masuk=b.tanggal_masuk,
        tanggal_keluar=b.tanggal_keluar, jenis_kamar=b.jenis_kamar, catatan=b.catatan,
        status=b.status, created_at=b.created_at,
    )


def _digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def _pg_error(exc: DBAPIError) -> tuple[str, str]:
    orig = getattr(exc, "orig", None)
    code = getattr(orig, "pgcode", "") or ""
    diag = getattr(orig, "diag", None)
    msg = getattr(diag, "message_primary", "") or ""
    return code, msg


# ─── Endpoints ───────────────────────────────────────────────────────────────

async def verified_booking(data: BookingCreate) -> BookingCreate:
    data._request_hash = hashlib.sha256(json.dumps(data.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    hospital = await sp.get_hospital(data.kode_rs)
    if not hospital:
        raise HTTPException(404, "Rumah sakit tidak ditemukan dalam dataset semantik")
    # Identitas kanonis berasal dari RDF, bukan dari nama yang dikirim browser.
    return data.model_copy(update={"nama_rs": hospital["nama"]})


@router.get("/availability/{kode_rs}", summary="Sisa kuota kamar per jenis (SQL) untuk RS (RDF)")
def ketersediaan_kamar(kode_rs: str, tanggal_masuk: datetime.date | None = None,
                       tanggal_keluar: datetime.date | None = None, db: Session = Depends(get_db)):
    if tanggal_masuk and tanggal_keluar and tanggal_keluar < tanggal_masuk:
        raise HTTPException(422, "tanggal_keluar harus setelah atau sama dengan tanggal_masuk")
    if not hospital_name(kode_rs):
        raise HTTPException(404, "Rumah sakit tidak ditemukan dalam dataset semantik")
    masuk = tanggal_masuk or datetime.date.today()
    return {
        "kode_rs": kode_rs,
        "tanggal_masuk": masuk,
        "tanggal_keluar": tanggal_keluar,
        "items": kamar_availability(db, kode_rs, masuk, tanggal_keluar),
    }


@router.post("/booking", status_code=201, response_model=BookingResponse,
             summary="Buat booking kamar rawat inap (transaksi ACID)")
def buat_booking(data: BookingCreate = Depends(verified_booking), db: Session = Depends(get_db),
                 idempotency_key: Annotated[str | None, Header(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")] = None,
                 current_user: User | None = Depends(get_optional_user)):
    """Simpan booking ke PostgreSQL. Ledger idempotency + stored function sp_buat_booking
    berjalan dalam SATU transaksi; kegagalan apa pun di-rollback."""
    for _ in range(5):
        kode = _generate_kode()
        try:
            params = None
            if idempotency_key:
                key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
                payload_hash = data._request_hash or hashlib.sha256(json.dumps(data.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
                params = dict(scope=_SCOPE, key_hash=key_hash, payload_hash=payload_hash)
                # INSERT pesaing menunggu pemilik kunci commit/rollback (tidak ada reservasi setengah jadi).
                owner = db.execute(text("INSERT INTO booking_idempotency (scope,key_hash,payload_hash) VALUES (:scope,:key_hash,:payload_hash) ON CONFLICT (scope,key_hash) DO NOTHING RETURNING key_hash"), params).scalar()
                if owner is None:
                    row = db.execute(text("SELECT payload_hash,booking_id FROM booking_idempotency WHERE scope=:scope AND key_hash=:key_hash"), params).mappings().one()
                    if row["payload_hash"] != payload_hash:
                        db.rollback()
                        raise HTTPException(409, "Idempotency-Key telah digunakan dengan payload berbeda")
                    previous = db.get(BookingKamar, row["booking_id"]) if row["booking_id"] else None
                    if previous is None:
                        db.rollback()
                        raise HTTPException(503, "Hasil booking belum tersedia")
                    if settings.idempotency_replay_as_409:
                        db.rollback()
                        raise HTTPException(409, f"Idempotency-Key sudah dipakai; booking {previous.kode_booking} sudah tercatat")
                    response = _response(previous, data.nama_rs)
                    db.rollback()
                    return response
            # Hanya operasi baru yang dicek: replay sah boleh datang di hari berikutnya.
            if data.tanggal_masuk < datetime.date.today():
                db.rollback()
                raise HTTPException(422, "tanggal_masuk tidak boleh di masa lalu")
            new_id = db.execute(
                text("SELECT sp_buat_booking(:kode,:rs,:pasien,:telp,:masuk,:keluar,:jenis,:catatan)"),
                dict(kode=kode, rs=data.kode_rs, pasien=data.nama_pasien, telp=data.no_telp,
                     masuk=data.tanggal_masuk, keluar=data.tanggal_keluar, jenis=data.jenis_kamar,
                     catatan=data.catatan),
            ).scalar_one()
            if current_user is not None:
                # Tautkan booking ke akun pasien yang login (transaksi yang sama) agar
                # muncul di Dashboard Pasien. Tamu tetap user_id = NULL.
                db.execute(text("UPDATE booking_kamar SET user_id=:uid WHERE id=:id"),
                           dict(uid=current_user.id, id=new_id))
            if params:
                db.execute(text("UPDATE booking_idempotency SET booking_id=:booking_id WHERE scope=:scope AND key_hash=:key_hash"), dict(params, booking_id=new_id))
            booking = db.get(BookingKamar, new_id)
            # Materialisasi sebelum commit agar kegagalan baca tidak memicu insert ulang.
            response = _response(booking, data.nama_rs)
            db.commit()
            return response
        except HTTPException:
            raise
        except IntegrityError as exc:
            db.rollback()
            constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
            if "kode_booking" in constraint:
                continue
            if "uq_booking_pasien_aktif" in constraint:
                raise HTTPException(409, "Pasien yang sama sudah memiliki booking aktif untuk kamar dan tanggal tersebut") from None
            raise HTTPException(409, "Data booking tidak memenuhi aturan database") from None
        except DBAPIError as exc:
            db.rollback()
            code, msg = _pg_error(exc)
            if code in _PGCODE_STATUS:
                raise HTTPException(_PGCODE_STATUS[code], msg or "Booking ditolak oleh aturan database") from None
            raise HTTPException(503, "Database booking tidak tersedia; coba lagi nanti") from None
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(503, "Database booking tidak tersedia; coba lagi nanti") from None
    raise HTTPException(409, "Gagal membuat kode booking unik; coba lagi")


def _operator_ok(x_booking_key: str) -> bool:
    return bool(settings.booking_access_key) and secrets.compare_digest(
        x_booking_key.encode(), settings.booking_access_key.encode()
    )


def require_booking_access(x_booking_key: str = Header(default="")):
    if not _operator_ok(x_booking_key):
        raise HTTPException(403, "Akses ini hanya untuk operator simulasi yang berwenang")


@router.get("/booking/rs/{kode_rs}", dependencies=[Depends(require_booking_access)],
            response_model=list[BookingResponse], summary="Daftar booking untuk suatu RS (operator)")
def daftar_booking_rs(kode_rs: str, db: Session = Depends(get_db)):
    rows = db.query(BookingKamar).filter(BookingKamar.kode_rs == kode_rs).all()
    return [_response(b) for b in rows]


@router.get("/booking/{kode_booking}", response_model=BookingResponse,
            summary="Cek status booking (kode + nomor telepon pemesan, atau kunci operator)")
def cek_booking(kode_booking: str, db: Session = Depends(get_db),
                x_booking_key: str = Header(default=""),
                no_telp: Annotated[str | None, Query(max_length=20)] = None):
    b = db.query(BookingKamar).filter(BookingKamar.kode_booking == kode_booking.upper()).first()
    proof = bool(no_telp) and b is not None and secrets.compare_digest(
        _digits(no_telp).encode(), _digits(b.no_telp).encode()
    ) and bool(_digits(no_telp))
    if not (_operator_ok(x_booking_key) or proof):
        # Respons sama untuk "tidak ada" dan "bukan pemilik" agar kode tidak bisa ditebak.
        raise HTTPException(403, "Kode booking dan nomor telepon pemesan tidak cocok")
    if b is None:
        raise HTTPException(404, "Kode booking tidak ditemukan")
    return _response(b)


@router.delete("/booking/{kode_booking}", dependencies=[Depends(require_booking_access)],
               summary="Batalkan booking (operator)")
def batal_booking(kode_booking: str, db: Session = Depends(get_db)):
    try:
        b = db.query(BookingKamar).filter(BookingKamar.kode_booking == kode_booking.upper()).first()
        if not b:
            raise HTTPException(404, "Kode booking tidak ditemukan")
        if b.status == "dibatalkan":
            raise HTTPException(400, "Booking sudah dibatalkan sebelumnya")
        db.execute(text("SELECT set_config('app.aktor', 'operator-api', true)"))
        b.status = "dibatalkan"
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Database booking tidak tersedia; coba lagi nanti") from None
    return {"message": "Booking berhasil dibatalkan", "kode_booking": kode_booking}
