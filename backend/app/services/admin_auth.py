"""Autentikasi & otorisasi sistem admin (tanpa dependensi tambahan).

- Password: PBKDF2-HMAC-SHA256 + salt acak (hashlib, stdlib).
- Sesi: token acak 256-bit; yang disimpan di DB hanya SHA-256-nya (admin_sessions).
- RBAC: role -> permission di tabel role_permissions; dicek via require_perm().
- Semua query SQL diparameterisasi (text() + bind), tidak ada f-string ke SQL.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import engine, get_db

log = logging.getLogger("carisehat.auth")
_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def ensure_default_admin() -> None:
    """Buat akun admin awal bila tabel admin_users masih kosong."""
    with engine.begin() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM admin_users")).scalar_one()
        if total:
            return
        conn.execute(
            text(
                "INSERT INTO admin_users (username, password_hash, nama_lengkap, role_kode) "
                "VALUES (:u, :p, 'Administrator Utama', 'superadmin')"
            ),
            {"u": settings.admin_username, "p": hash_password(settings.admin_password)},
        )
    log.warning("Akun admin awal dibuat: username=%s (segera ganti password di menu Pengguna).", settings.admin_username)


def ensure_demo_operator() -> None:
    """Buat akun demo ber-role 'operator' (idempotent: dilewati bila username sudah ada).

    Operator hanya mendapat permission dari role_permissions (booking, kuota kamar,
    jadwal, reservasi/poliklinik); tidak bisa mengelola pengguna, hapus data, atau audit log.
    """
    if not settings.demo_operator_enabled:
        return
    with engine.begin() as conn:
        created = conn.execute(
            text(
                "INSERT INTO admin_users (username, password_hash, nama_lengkap, role_kode) "
                "SELECT :u, :p, 'Operator Demo', 'operator' "
                "WHERE EXISTS (SELECT 1 FROM roles WHERE kode = 'operator') "
                "ON CONFLICT (username) DO NOTHING RETURNING id"
            ),
            {"u": settings.operator_username, "p": hash_password(settings.operator_password)},
        ).scalar()
    if created:
        log.warning("Akun demo operator dibuat: username=%s", settings.operator_username)


def current_admin(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> dict:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(401, "Login admin diperlukan", headers={"WWW-Authenticate": "Bearer"})
    try:
        db.execute(text("ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS scoped_rs_id VARCHAR(20)"))
        db.commit()
    except Exception:
        db.rollback()
    row = db.execute(
        text(
            "SELECT u.id, u.username, u.nama_lengkap, u.role_kode, u.scoped_rs_id "
            "FROM admin_sessions s JOIN admin_users u ON u.id = s.user_id "
            "WHERE s.token_hash = :h AND s.expires_at > now() AND u.aktif"
        ),
        {"h": hash_token(token.strip())},
    ).mappings().first()
    if not row:
        raise HTTPException(401, "Sesi tidak valid atau sudah berakhir", headers={"WWW-Authenticate": "Bearer"})
    perms = db.execute(
        text("SELECT permission FROM role_permissions WHERE role_kode = :r"), {"r": row["role_kode"]}
    ).scalars().all()
    return {**dict(row), "permissions": set(perms)}


def require_perm(permission: str):
    def dependency(user: dict = Depends(current_admin)) -> dict:
        if permission not in user["permissions"]:
            raise HTTPException(403, f"Hak akses '{permission}' diperlukan untuk aksi ini")
        return user

    return dependency


def set_actor(db: Session, user: dict) -> None:
    """Catat pelaku perubahan agar trigger audit_log mengisinya (berlaku per transaksi)."""
    db.execute(text("SELECT set_config('app.aktor', :a, true)"), {"a": user["username"]})
