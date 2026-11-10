"""Model ORM awal (SQLAlchemy 2.0). Skema sebenarnya dibuat oleh database/schema.sql; P2 melengkapi."""
import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Provinsi(Base):
    __tablename__ = "provinsi"
    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(100), unique=True)


class KabupatenKota(Base):
    __tablename__ = "kabupaten_kota"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_provinsi: Mapped[int] = mapped_column(ForeignKey("provinsi.id"))
    nama: Mapped[str] = mapped_column(String(100))
    jenis: Mapped[str] = mapped_column(String(10))


class RumahSakit(Base):
    __tablename__ = "rumah_sakit"
    id: Mapped[int] = mapped_column(primary_key=True)
    kode_rs: Mapped[str] = mapped_column(String(20), unique=True)
    id_kabkota: Mapped[int] = mapped_column(ForeignKey("kabupaten_kota.id"))
    nama: Mapped[str] = mapped_column(String(200))
    jenis: Mapped[str] = mapped_column(String(20))
    kelas: Mapped[str | None] = mapped_column(String(1))
    alamat: Mapped[str | None]
    telepon: Mapped[str | None] = mapped_column(String(30))
    website: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    status: Mapped[str] = mapped_column(String(10), default="aktif")
    kabkota: Mapped[KabupatenKota] = relationship()


class BookingKamar(Base):
    """Model ORM untuk tabel booking_kamar (simulasi pemesanan rawat inap)."""
    __tablename__ = "booking_kamar"

    id: Mapped[int] = mapped_column(primary_key=True)
    kode_booking: Mapped[str] = mapped_column(String(20), unique=True)
    kode_rs: Mapped[str] = mapped_column(String(20), index=True)
    nama_rs: Mapped[str] = mapped_column(String(200))
    nama_pasien: Mapped[str] = mapped_column(String(100))
    no_telp: Mapped[str] = mapped_column(String(20))
    tanggal_masuk: Mapped[datetime.date]
    tanggal_keluar: Mapped[datetime.date | None]
    jenis_kamar: Mapped[str] = mapped_column(String(30))
    catatan: Mapped[str | None]
    status: Mapped[str] = mapped_column(String(15), default="menunggu")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
