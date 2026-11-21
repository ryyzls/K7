"""Layanan ketersediaan (SQL) yang digabung dengan data RS dari RDF (Federated Mapping).

rs_id adalah satu-satunya perekat: SQL menyimpan kuota/booking, RDF menyimpan nama/alamat/fasilitas.
"""
from __future__ import annotations

import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

ROOM_TYPES = ["VIP", "Kelas I", "Kelas II", "Kelas III", "ICU"]
_WIB = datetime.timezone(datetime.timedelta(hours=7))


def wib_today() -> datetime.date:
    return datetime.datetime.now(_WIB).date()


def hospital_name(rs_id: str) -> str | None:
    """Nama RS dari RDF (cache in-memory). None bila id tidak dikenal."""
    from app.services import hospital_repo  # impor lambat: graf RDF dimuat saat pertama dipakai

    try:
        h = hospital_repo.get_hospital_by_id(rs_id)
    except Exception:
        return None
    return h["nama"] if h else None


def kamar_availability(db: Session, rs_id: str, masuk: datetime.date | None = None,
                       keluar: datetime.date | None = None) -> list[dict]:
    masuk = masuk or wib_today()
    rows = db.execute(
        text(
            "SELECT j AS jenis, fn_kapasitas_kamar(:rs, j) AS kapasitas, "
            "fn_terisi_kamar(:rs, j, CAST(:m AS date), CAST(:k AS date), NULL) AS terisi "
            "FROM unnest(CAST(:jenis AS text[])) AS j"
        ),
        {"rs": rs_id, "m": masuk, "k": keluar, "jenis": ROOM_TYPES},
    ).mappings().all()
    order = {name: i for i, name in enumerate(ROOM_TYPES)}
    out = [
        {
            "jenis_kamar": r["jenis"],
            "kapasitas": r["kapasitas"],
            "terisi": r["terisi"],
            "sisa": max(r["kapasitas"] - r["terisi"], 0),
        }
        for r in rows
    ]
    return sorted(out, key=lambda x: order[x["jenis_kamar"]])
