from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.orm_models import User, UserSession, get_dashboard_user_orm

router = APIRouter(prefix="/api", tags=["Auth & Dashboard Pasien"])

SESSION_TTL_HOURS = 24 * 7


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256$120000${salt.hex()}${dk.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        _, iter_str, salt_hex, dk_hex = stored_hash.split("$", 3)
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iter_str)
        )
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    raw_token = authorization.removeprefix("Bearer ").strip()
    if not raw_token:
        return None
    token_hash = _hash_token(raw_token)
    now = datetime.now(timezone.utc)
    stmt = (
        select(User)
        .join(UserSession, UserSession.user_id == User.id)
        .where(
            UserSession.token_hash == token_hash,
            UserSession.expires_at > now,
            User.aktif.is_(True),
        )
    )
    return db.scalar(stmt)


def require_user(user: Optional[User] = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Silakan login terlebih dahulu untuk mengakses fitur ini.",
        )
    return user


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    nama_lengkap: str = Field(..., min_length=2, max_length=100)
    no_telp: Optional[str] = Field(default=None, max_length=20)


class LoginIn(BaseModel):
    username_or_email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=1, max_length=128)


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_pasien(payload: RegisterIn, db: Session = Depends(get_db)):
    user = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        password_hash=_hash_password(payload.password),
        nama_lengkap=payload.nama_lengkap.strip(),
        no_telp=payload.no_telp.strip() if payload.no_telp else None,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username atau email sudah terdaftar.",
        )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nama_lengkap": user.nama_lengkap,
    }


@router.post("/auth/login")
def login_pasien(payload: LoginIn, db: Session = Depends(get_db)):
    ident = payload.username_or_email.strip()
    stmt = select(User).where(
        (User.username == ident) | (User.email == ident.lower()),
        User.aktif.is_(True),
    )
    user = db.scalar(stmt)
    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username/email atau kata sandi salah.",
        )

    raw_token = secrets.token_urlsafe(32)
    session_row = UserSession(
        token_hash=_hash_token(raw_token),
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS),
    )
    db.add(session_row)
    db.commit()

    return {
        "access_token": raw_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nama_lengkap": user.nama_lengkap,
            "no_telp": user.no_telp,
        },
    }


@router.post("/auth/logout")
def logout_pasien(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    if authorization and authorization.startswith("Bearer "):
        token_hash = _hash_token(authorization.removeprefix("Bearer ").strip())
        sess = db.get(UserSession, token_hash)
        if sess:
            db.delete(sess)
            db.commit()
    return {"message": "Logout berhasil."}


@router.get("/pasien/dashboard")
def dashboard_pasien(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    # 1. Statistik ringkas dari Database View v_ringkasan_aktivitas_user
    ringkasan = db.execute(
        text("SELECT * FROM v_ringkasan_aktivitas_user WHERE user_id = :uid"),
        {"uid": current_user.id},
    ).mappings().first()

    # 2. Seluruh relasi dimuat via SQLAlchemy ORM eager loading (anti N+1)
    user_detail = get_dashboard_user_orm(db, current_user.id)
    assert user_detail is not None

    return {
        "profil": {
            "id": user_detail.id,
            "username": user_detail.username,
            "email": user_detail.email,
            "nama_lengkap": user_detail.nama_lengkap,
            "no_telp": user_detail.no_telp,
        },
        "statistik": dict(ringkasan) if ringkasan else {},
        "favorit_rs": [
            {"rs_id": f.rs_id, "catatan": f.catatan, "created_at": f.created_at}
            for f in sorted(user_detail.favorit_list, key=lambda x: x.created_at, reverse=True)
        ],
        "ulasan_saya": [
            {
                "id": u.id,
                "rs_id": u.rs_id,
                "rating": u.rating,
                "komentar": u.komentar,
                "status_moderasi": u.status_moderasi,
                "created_at": u.created_at,
            }
            for u in sorted(user_detail.ulasan_list, key=lambda x: x.created_at, reverse=True)
        ],
        "riwayat_poliklinik": [
            {
                "id": r.id,
                "kode_reservasi": r.kode_reservasi,
                "kode_tiket": r.kode_tiket,
                "nomor_antrean": r.nomor_antrean,
                "rs_id": r.rs_id,
                "nama_dokter": r.jadwal.nama_dokter if r.jadwal else None,
                "spesialisasi": r.jadwal.spesialisasi if r.jadwal else None,
                "tanggal": r.tanggal,
                "status": r.status,
            }
            for r in sorted(user_detail.reservasi_poli, key=lambda x: x.tanggal, reverse=True)
        ],
        "riwayat_kamar": [
            {
                "id": b.id,
                "kode_booking": b.kode_booking,
                "rs_id": b.kode_rs,
                "jenis_kamar": b.jenis_kamar,
                "tanggal_masuk": b.tanggal_masuk,
                "tanggal_keluar": b.tanggal_keluar,
                "status": b.status,
            }
            for b in sorted(user_detail.booking_kamar_list, key=lambda x: x.created_at, reverse=True)
        ],
    }
