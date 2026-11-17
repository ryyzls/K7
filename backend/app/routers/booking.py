"""Router: Booking Kamar Rawat Inap (simulasi untuk Tugas Besar MSBD/Web Semantik)."""
import datetime
import secrets
import string
import hashlib
import json
from typing import Annotated
from sqlalchemy import text

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from pydantic import PrivateAttr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.config import settings
from app.services import sparql_service as sp

from app.database.connection import get_db
from app.database.models import BookingKamar

router = APIRouter(prefix="/api", tags=["Booking"])

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


# ─── Endpoints ───────────────────────────────────────────────────────────────

async def verified_booking(data: BookingCreate) -> BookingCreate:
    data._request_hash = hashlib.sha256(json.dumps(data.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    hospital = await sp.get_hospital(data.kode_rs)
    if not hospital:
        raise HTTPException(404, "Rumah sakit tidak ditemukan dalam dataset semantik")
    # Canonical identity comes from RDF, never from the browser's display name.
    return data.model_copy(update={"nama_rs": hospital["nama"]})


@router.post("/booking", status_code=201, response_model=BookingResponse,
             summary="Buat booking kamar rawat inap (simulasi)")
def buat_booking(data: BookingCreate = Depends(verified_booking), db: Session = Depends(get_db),
                 idempotency_key: Annotated[str | None, Header(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")] = None):
    """Simpan pemesanan kamar rawat inap ke PostgreSQL.
    Ini adalah simulasi untuk keperluan demo Tugas Besar — bukan terhubung ke sistem RS asli.
    """
    for _ in range(5):
        booking = BookingKamar(kode_booking=_generate_kode(), **data.model_dump())
        try:
            if idempotency_key:
                key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
                payload_hash = data._request_hash or hashlib.sha256(json.dumps(data.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
                params = dict(scope="POST:/api/booking:v1", key_hash=key_hash, payload_hash=payload_hash)
                # A competing INSERT waits for the owner to commit/rollback. Ledger and
                # booking share one transaction; no committed in-progress reservation.
                owner = db.execute(text("INSERT INTO booking_idempotency (scope,key_hash,payload_hash) VALUES (:scope,:key_hash,:payload_hash) ON CONFLICT (scope,key_hash) DO NOTHING RETURNING key_hash"), params).scalar()
                if owner is None:
                    row = db.execute(text("SELECT payload_hash,booking_id FROM booking_idempotency WHERE scope=:scope AND key_hash=:key_hash"), params).mappings().one()
                    if row['payload_hash'] != payload_hash:
                        db.rollback()
                        raise HTTPException(409, "Idempotency-Key telah digunakan dengan payload berbeda")
                    previous = db.get(BookingKamar, row['booking_id'])
                    if previous is None:
                        db.rollback()
                        raise HTTPException(503, "Hasil booking belum tersedia")
                    response = BookingResponse.model_validate(previous)
                    db.rollback()
                    return response
            # Check only new operations: a legitimate replay may arrive on a later day.
            if data.tanggal_masuk < datetime.date.today():
                db.rollback()
                raise HTTPException(422, "tanggal_masuk tidak boleh di masa lalu")
            db.add(booking)
            if idempotency_key:
                db.flush()
                db.execute(text("UPDATE booking_idempotency SET booking_id=:booking_id WHERE scope=:scope AND key_hash=:key_hash"), dict(params, booking_id=booking.id))
            # Materialize before commit: no refresh/read failure can trigger another
            # insertion after a successful commit. Keyed retries recover uncertain commits.
            db.flush()
            response = BookingResponse.model_validate(booking)
            db.commit()
            return response
        except IntegrityError as exc:
            db.rollback()
            constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
            if "kode_booking" in constraint:
                continue
            raise HTTPException(409, "Data booking tidak memenuhi aturan database") from None
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(503, "Database booking tidak tersedia; coba lagi nanti") from None
    raise HTTPException(409, "Gagal membuat kode booking unik; coba lagi")


def require_booking_access(x_booking_key: str = Header(default="")):
    if not settings.booking_access_key or not secrets.compare_digest(x_booking_key.encode(), settings.booking_access_key.encode()):
        raise HTTPException(403, "Akses status/pembatalan hanya untuk operator simulasi yang berwenang")


@router.get("/booking/{kode_booking}", dependencies=[Depends(require_booking_access)], response_model=BookingResponse,
            summary="Cek status booking berdasarkan kode")
def cek_booking(kode_booking: str, db: Session = Depends(get_db)):
    b = db.query(BookingKamar).filter(BookingKamar.kode_booking == kode_booking.upper()).first()
    if not b:
        raise HTTPException(404, "Kode booking tidak ditemukan")
    return b


@router.get("/booking/rs/{kode_rs}", dependencies=[Depends(require_booking_access)], response_model=list[BookingResponse],
            summary="Daftar booking untuk suatu RS")
def daftar_booking_rs(kode_rs: str, db: Session = Depends(get_db)):
    return db.query(BookingKamar).filter(BookingKamar.kode_rs == kode_rs).all()


@router.delete("/booking/{kode_booking}", dependencies=[Depends(require_booking_access)], summary="Batalkan booking")
def batal_booking(kode_booking: str, db: Session = Depends(get_db)):
    b = db.query(BookingKamar).filter(BookingKamar.kode_booking == kode_booking.upper()).first()
    if not b:
        raise HTTPException(404, "Kode booking tidak ditemukan")
    if b.status == "dibatalkan":
        raise HTTPException(400, "Booking sudah dibatalkan sebelumnya")
    b.status = "dibatalkan"
    db.commit()
    return {"message": "Booking berhasil dibatalkan", "kode_booking": kode_booking}
