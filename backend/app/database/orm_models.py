from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional
from app.database.models import BookingKamar

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship, selectinload

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    nama_lengkap: Mapped[str] = mapped_column(String(100), nullable=False)
    no_telp: Mapped[Optional[str]] = mapped_column(String(20))
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sessions: Mapped[List["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorit_list: Mapped[List["FavoritRS"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    ulasan_list: Mapped[List["UlasanRS"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reservasi_poli: Mapped[List["ReservasiKonsultasi"]] = relationship(back_populates="user")
    booking_kamar_list: Mapped[List[BookingKamar]] = relationship()

class UserSession(Base):
    __tablename__ = "user_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


class Poliklinik(Base):
    __tablename__ = "poliklinik"
    __table_args__ = (
        UniqueConstraint("rs_id", "kode_poli", name="uq_poliklinik_rs_kode"),
        UniqueConstraint("rs_id", "spesialisasi", name="uq_poliklinik_rs_spesialisasi"),
        CheckConstraint("kuota_harian >= 0 AND kuota_harian <= 1000", name="ck_poliklinik_kuota"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rs_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    kode_poli: Mapped[str] = mapped_column(String(24), nullable=False)
    nama_poli: Mapped[str] = mapped_column(String(100), nullable=False)
    spesialisasi: Mapped[str] = mapped_column(String(80), nullable=False)
    lokasi_ruangan: Mapped[Optional[str]] = mapped_column(String(100))
    jam_operasional: Mapped[Optional[str]] = mapped_column(String(60))
    kuota_harian: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    jadwal_list: Mapped[List["JadwalKonsultasi"]] = relationship(
        back_populates="poliklinik", lazy="selectin"
    )


class JadwalKonsultasi(Base):
    __tablename__ = "jadwal_konsultasi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rs_id: Mapped[str] = mapped_column(String(20), nullable=False)
    poliklinik_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("poliklinik.id", ondelete="RESTRICT")
    )
    nama_dokter: Mapped[str] = mapped_column(String(120), nullable=False)
    spesialisasi: Mapped[str] = mapped_column(String(80), nullable=False)
    hari: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    jam_mulai: Mapped[time] = mapped_column(Time, nullable=False)
    jam_selesai: Mapped[time] = mapped_column(Time, nullable=False)
    kuota_per_sesi: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    poliklinik: Mapped[Optional["Poliklinik"]] = relationship(back_populates="jadwal_list")
    reservasi_list: Mapped[List["ReservasiKonsultasi"]] = relationship(back_populates="jadwal")


class ReservasiKonsultasi(Base):
    __tablename__ = "reservasi_konsultasi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kode_reservasi: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    kode_tiket: Mapped[Optional[str]] = mapped_column(String(32), unique=True)
    jadwal_id: Mapped[int] = mapped_column(
        ForeignKey("jadwal_konsultasi.id", ondelete="RESTRICT"), nullable=False
    )
    rs_id: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    nama_pasien: Mapped[str] = mapped_column(String(100), nullable=False)
    no_telp: Mapped[str] = mapped_column(String(20), nullable=False)
    tanggal: Mapped[date] = mapped_column(Date, nullable=False)
    nomor_antrean: Mapped[Optional[int]] = mapped_column(Integer)
    keluhan: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(15), default="menunggu", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    jadwal: Mapped["JadwalKonsultasi"] = relationship(back_populates="reservasi_list")
    user: Mapped[Optional["User"]] = relationship(back_populates="reservasi_poli")


if "user_id" not in BookingKamar.__table__.c:
    BookingKamar.user_id = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class FavoritRS(Base):
    __tablename__ = "favorit_rs"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    rs_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    catatan: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="favorit_list")


class UlasanRS(Base):
    __tablename__ = "ulasan_rs"
    __table_args__ = (
        UniqueConstraint("user_id", "rs_id", name="uq_ulasan_user_rs"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_ulasan_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rs_id: Mapped[str] = mapped_column(String(20), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    komentar: Mapped[str] = mapped_column(Text, nullable=False)
    status_moderasi: Mapped[str] = mapped_column(String(20), default="disetujui", nullable=False)
    dimoderasi_oleh: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="ulasan_list")
    
    # Tambahkan pada Poliklinik & UlasanRS:
__table_args__ = (
    UniqueConstraint("rs_id", "kode_poli", name="uq_poliklinik_rs_kode"),
    UniqueConstraint("rs_id", "spesialisasi", name="uq_poliklinik_rs_spesialisasi"),
    CheckConstraint("kuota_harian >= 0 AND kuota_harian <= 1000", name="ck_poliklinik_kuota"),
    {"extend_existing": True},
)

# Tambahkan pada User, UserSession, JadwalKonsultasi, ReservasiKonsultasi, BookingKamar, FavoritRS:
__table_args__ = {"extend_existing": True}


def get_poliklinik_by_rs_orm(db: Session, rs_id: str) -> List[Poliklinik]:
    stmt = (
        select(Poliklinik)
        .options(selectinload(Poliklinik.jadwal_list))
        .where(Poliklinik.rs_id == rs_id, Poliklinik.aktif.is_(True))
        .order_by(Poliklinik.nama_poli.asc())
    )
    return list(db.scalars(stmt).all())


def get_dashboard_user_orm(db: Session, user_id: int) -> Optional[User]:
    stmt = (
        select(User)
        .options(
            selectinload(User.favorit_list),
            selectinload(User.ulasan_list),
            selectinload(User.reservasi_poli).selectinload(ReservasiKonsultasi.jadwal),
            selectinload(User.booking_kamar_list),
        )
        .where(User.id == user_id)
    )
    return db.scalar(stmt)