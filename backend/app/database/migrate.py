"""Runner migrasi SQL sederhana (tanpa Alembic) untuk PostgreSQL.

- Membaca database/migrations/NNN_nama.up.sql, menjalankan yang belum tercatat
  di tabel schema_migrations, masing-masing dalam SATU transaksi.
- Hanya nomor >= 3 yang otomatis dijalankan. Migrasi 001/002 adalah legacy manual
  dan efeknya sudah diserap (idempotent) oleh 003.
- Memakai advisory lock agar dua proses (mis. uvicorn --reload) tidak berebut.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from app.config import settings

log = logging.getLogger("carisehat.migrate")

AUTO_FROM = 3
_LOCK_ID = 727001
_NAME_RE = re.compile(r"^(\d{3})_(.+)\.up\.sql$")


def find_migrations_dir() -> Path | None:
    candidates = [
        Path(settings.migrations_dir),
        Path(__file__).resolve().parents[3] / "database" / "migrations",
        Path(__file__).resolve().parents[2] / "database" / "migrations",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def run_migrations(engine) -> list[str]:
    """Jalankan migrasi tertunda. Mengembalikan daftar versi yang baru diterapkan."""
    directory = find_migrations_dir()
    if directory is None:
        log.warning("Folder migrations tidak ditemukan; fitur admin butuh database/migrations (lihat docker-compose volume).")
        return []

    files = []
    for f in sorted(directory.glob("*.up.sql")):
        m = _NAME_RE.match(f.name)
        if m and int(m.group(1)) >= AUTO_FROM:
            files.append((f.name[: -len(".up.sql")], f))

    applied_now: list[str] = []
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute("SELECT pg_advisory_lock(%s)", (_LOCK_ID,))
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
        )
        raw.commit()
        cur.execute("SELECT version FROM schema_migrations")
        done = {r[0] for r in cur.fetchall()}
        raw.commit()

        for version, path in files:
            if version in done:
                continue
            sql = path.read_text(encoding="utf-8")
            try:
                cur.execute(sql)  # tanpa parameter: karakter % di PL/pgSQL aman
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
                raw.commit()
                applied_now.append(version)
                log.info("Migrasi diterapkan: %s", version)
            except Exception:
                raw.rollback()
                log.exception("Migrasi %s GAGAL dan di-rollback; migrasi berikutnya dihentikan.", version)
                break
    finally:
        try:
            raw.rollback()
            cur = raw.cursor()
            cur.execute("SELECT pg_advisory_unlock(%s)", (_LOCK_ID,))
            raw.commit()
        except Exception:  # pragma: no cover - koneksi sudah rusak
            pass
        raw.close()
    return applied_now
