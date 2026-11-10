"""Router: Booking Kamar Rawat Inap (simulasi untuk Tugas Besar MSBD/Web Semantik)."""
import datetime
import random
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import BookingKamar

router = APIRouter(prefix="/api", tags=["Booking"])

# ─── Pydantic Schema ─────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    kode_rs: str
    nama_rs: str
    nama_pasien: str
    no_telp: str
    tanggal_masuk: datetime.date
    tanggal_keluar: datetime.date | None = None
    jenis_kamar: str
    catatan: str | None = None

    @field_validator("jenis_kamar")
    @classmethod
    def validasi_jenis(cls, v: str) -> str:
        pilihan = {"VIP", "Kelas I", "Kelas II", "Kelas III", "ICU"}
        if v not in pilihan:
            raise ValueError(f"jenis_kamar harus salah satu dari: {', '.join(sorted(pilihan))}")
        return v

    @field_validator("tanggal_masuk")
    @classmethod
    def tidak_lampau(cls, v: datetime.date) -> datetime.date:
        if v < datetime.date.today():
            raise ValueError("tanggal_masuk tidak boleh di masa lalu")
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
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"BK-{today}-{suffix}"


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/booking", status_code=201, response_model=BookingResponse,
             summary="Buat booking kamar rawat inap (simulasi)")
def buat_booking(data: BookingCreate, db: Session = Depends(get_db)):
    """Simpan pemesanan kamar rawat inap ke PostgreSQL.
    Ini adalah simulasi untuk keperluan demo Tugas Besar — bukan terhubung ke sistem RS asli.
    """
    # Generate kode unik, coba ulang jika tabrakan (sangat jarang)
    for _ in range(5):
        kode = _generate_kode()
        if not db.query(BookingKamar).filter(BookingKamar.kode_booking == kode).first():
            break
    else:
        raise HTTPException(500, "Gagal generate kode booking unik")

    booking = BookingKamar(kode_booking=kode, **data.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/booking/{kode_booking}", response_model=BookingResponse,
            summary="Cek status booking berdasarkan kode")
def cek_booking(kode_booking: str, db: Session = Depends(get_db)):
    b = db.query(BookingKamar).filter(BookingKamar.kode_booking == kode_booking.upper()).first()
    if not b:
        raise HTTPException(404, "Kode booking tidak ditemukan")
    return b


@router.get("/booking/rs/{kode_rs}", response_model=list[BookingResponse],
            summary="Daftar booking untuk suatu RS")
def daftar_booking_rs(kode_rs: str, db: Session = Depends(get_db)):
    return db.query(BookingKamar).filter(BookingKamar.kode_rs == kode_rs).all()


@router.delete("/booking/{kode_booking}", summary="Batalkan booking")
def batal_booking(kode_booking: str, db: Session = Depends(get_db)):
    b = db.query(BookingKamar).filter(BookingKamar.kode_booking == kode_booking.upper()).first()
    if not b:
        raise HTTPException(404, "Kode booking tidak ditemukan")
    if b.status == "dibatalkan":
        raise HTTPException(400, "Booking sudah dibatalkan sebelumnya")
    b.status = "dibatalkan"
    db.commit()
    return {"message": "Booking berhasil dibatalkan", "kode_booking": kode_booking}
