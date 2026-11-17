"""Model ORM awal (SQLAlchemy 2.0). Skema sebenarnya dibuat oleh database/schema.sql; P2 melengkapi."""
import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Provinsi(Base):
    __tablename__ = "provinsi"
    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(100), unique=True)


class KabupatenKota(Base):
    __tablename__ = "kabupaten_kota"
    __table_args__ = (
        CheckConstraint("jenis IN ('Kabupaten','Kota')", name="kabupaten_kota_jenis_check"),
        UniqueConstraint("id_provinsi", "nama", name="kabupaten_kota_id_provinsi_nama_key"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_provinsi: Mapped[int] = mapped_column(ForeignKey("provinsi.id"))
    nama: Mapped[str] = mapped_column(String(100))
    jenis: Mapped[str] = mapped_column(String(10))


class RumahSakit(Base):
    __tablename__ = "rumah_sakit"
    __table_args__ = (
        CheckConstraint("jenis IN ('Umum','Khusus')", name="rumah_sakit_jenis_check"),
        CheckConstraint("kelas IN ('A','B','C','D')", name="rumah_sakit_kelas_check"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="rumah_sakit_latitude_check"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="rumah_sakit_longitude_check"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    kode_rs: Mapped[str] = mapped_column(String(20), unique=True)
    id_kabkota: Mapped[int] = mapped_column(ForeignKey("kabupaten_kota.id"))
    nama: Mapped[str] = mapped_column(String(200))
    jenis: Mapped[str] = mapped_column(String(20))
    kelas: Mapped[str | None] = mapped_column(CHAR(1))
    alamat: Mapped[str | None] = mapped_column(Text)
    telepon: Mapped[str | None] = mapped_column(String(30))
    website: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    status: Mapped[str] = mapped_column(String(10), default="aktif", server_default=text("'aktif'"))
    kabkota: Mapped[KabupatenKota] = relationship()


class BookingKamar(Base):
    """Model ORM untuk tabel booking_kamar (simulasi pemesanan rawat inap)."""
    __tablename__ = "booking_kamar"
    __table_args__ = (
        CheckConstraint("jenis_kamar IN ('VIP','Kelas I','Kelas II','Kelas III','ICU')", name="booking_kamar_jenis_kamar_check"),
        CheckConstraint("status IN ('menunggu','dikonfirmasi','dibatalkan')", name="booking_kamar_status_check"),
        Index("idx_booking_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kode_booking: Mapped[str] = mapped_column(String(20), unique=True)
    kode_rs: Mapped[str] = mapped_column(String(20), index=True)
    nama_rs: Mapped[str] = mapped_column(String(200))
    nama_pasien: Mapped[str] = mapped_column(String(100))
    no_telp: Mapped[str] = mapped_column(String(20))
    tanggal_masuk: Mapped[datetime.date]
    tanggal_keluar: Mapped[datetime.date | None]
    jenis_kamar: Mapped[str] = mapped_column(String(30))
    catatan: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(15), default="menunggu", server_default=text("'menunggu'"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
