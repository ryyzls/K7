from __future__ import annotations

import secrets
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.database.orm_models import (
    FavoritRS,
    ReservasiKonsultasi,
    UlasanRS,
    User,
    get_poliklinik_by_rs_orm,
)
from app.routers.auth_pasien import get_optional_user, require_user

router = APIRouter(prefix="/api", tags=["Poliklinik, Favorit & Ulasan RS"])


class ReservasiPoliIn(BaseModel):
    jadwal_id: int
    nama_pasien: str = Field(..., min_length=2, max_length=100)
    no_telp: str = Field(..., min_length=8, max_length=20)
    tanggal: date
    keluhan: Optional[str] = Field(default=None, max_length=500)


class FavoritIn(BaseModel):
    catatan: Optional[str] = Field(default=None, max_length=200)


class UlasanIn(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    komentar: str = Field(..., min_length=5, max_length=1000)


@router.get("/poliklinik/{rs_id}")
def daftar_poliklinik_rs(rs_id: str, db: Session = Depends(get_db)):
    # 1. Data unit poli + jadwal dokter via ORM eager loading
    poli_list = get_poliklinik_by_rs_orm(db, rs_id)

    # 2. Data okupansi hari ini dari Database View v_okupansi_poliklinik
    okupansi_rows = db.execute(
        text("SELECT * FROM v_okupansi_poliklinik WHERE rs_id = :rs_id"),
        {"rs_id": rs_id},
    ).mappings().all()
    okupansi_map = {row["poliklinik_id"]: dict(row) for row in okupansi_rows}

    hasil = []
    for p in poli_list:
        ok = okupansi_map.get(p.id, {})
        hasil.append(
            {
                "id": p.id,
                "rs_id": p.rs_id,
                "kode_poli": p.kode_poli,
                "nama_poli": p.nama_poli,
                "spesialisasi": p.spesialisasi,
                "lokasi_ruangan": p.lokasi_ruangan,
                "jam_operasional": p.jam_operasional,
                "kuota_harian": p.kuota_harian,
                "terisi_hari_ini": ok.get("terisi_hari_ini", 0),
                "sisa_hari_ini": ok.get("sisa_hari_ini", p.kuota_harian),
                "jadwal_dokter": [
                    {
                        "id": j.id,
                        "nama_dokter": j.nama_dokter,
                        "hari": j.hari,
                        "jam_mulai": j.jam_mulai.strftime("%H:%M"),
                        "jam_selesai": j.jam_selesai.strftime("%H:%M"),
                        "kuota_per_sesi": j.kuota_per_sesi,
                    }
                    for j in p.jadwal_list
                    if j.aktif
                ],
            }
        )
    return {"rs_id": rs_id, "total_poli": len(hasil), "poliklinik": hasil}


@router.post("/poliklinik/reservasi", status_code=status.HTTP_201_CREATED)
def buat_reservasi_poliklinik(
    payload: ReservasiPoliIn,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    kode_res = f"POL-{secrets.token_hex(4).upper()}"
    idem = idempotency_key.strip() if idempotency_key else None

    try:
        row = db.execute(
            text(
                """
                SELECT * FROM sp_buat_reservasi_poliklinik(
                    :kode, :jadwal, :uid, :pasien, :telp, :tanggal, :keluhan, :idem
                )
                """
            ),
            {
                "kode": kode_res,
                "jadwal": payload.jadwal_id,
                "uid": current_user.id if current_user else None,
                "pasien": payload.nama_pasien.strip(),
                "telp": payload.no_telp.strip(),
                "tanggal": payload.tanggal,
                "keluhan": payload.keluhan.strip() if payload.keluhan else None,
                "idem": idem,
            },
        ).mappings().first()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pasien sudah memiliki reservasi aktif pada jadwal dan tanggal tersebut.",
        )
    except DBAPIError as exc:
        db.rollback()
        code = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
        msg = str(exc.orig).split("\n")[0]
        if code == "CS404":
            raise HTTPException(status_code=404, detail=msg)
        if code == "CS409":
            raise HTTPException(status_code=409, detail=msg)
        if code == "CS422":
            raise HTTPException(status_code=422, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

    return {
        "status": "simulasi_terdaftar",
        "reservasi_id": row["reservasi_id"],
        "kode_reservasi": kode_res,
        "kode_tiket": row["kode_tiket"],
        "nomor_antrean": row["nomor_antrean"],
        "terhubung_akun": current_user is not None,
    }


@router.patch("/pasien/reservasi/{kode_reservasi}/batal")
def batalkan_reservasi_pasien(
    kode_reservasi: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    stmt = select(ReservasiKonsultasi).where(
        ReservasiKonsultasi.kode_reservasi == kode_reservasi,
        ReservasiKonsultasi.user_id == current_user.id,
    )
    res = db.scalar(stmt)
    if res is None:
        raise HTTPException(status_code=404, detail="Reservasi tidak ditemukan pada akun Anda.")
    if res.status == "dibatalkan":
        raise HTTPException(status_code=400, detail="Reservasi sudah dibatalkan sebelumnya.")
    if res.status == "selesai":
        raise HTTPException(status_code=400, detail="Kunjungan yang sudah selesai tidak dapat dibatalkan.")

    res.status = "dibatalkan"
    db.commit()
    return {"kode_reservasi": res.kode_reservasi, "status": res.status}


@router.post("/pasien/favorit/{rs_id}", status_code=status.HTTP_201_CREATED)
def tambah_favorit_rs(
    rs_id: str,
    payload: FavoritIn = FavoritIn(),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    existing = db.get(FavoritRS, (current_user.id, rs_id))
    if existing:
        existing.catatan = payload.catatan
    else:
        db.add(FavoritRS(user_id=current_user.id, rs_id=rs_id, catatan=payload.catatan))
    db.commit()
    return {"user_id": current_user.id, "rs_id": rs_id, "favorit": True}


@router.delete("/pasien/favorit/{rs_id}")
def hapus_favorit_rs(
    rs_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    existing = db.get(FavoritRS, (current_user.id, rs_id))
    if existing:
        db.delete(existing)
        db.commit()
    return {"user_id": current_user.id, "rs_id": rs_id, "favorit": False}


@router.post("/rs/{rs_id}/ulasan", status_code=status.HTTP_201_CREATED)
def kirim_ulasan_rs(
    rs_id: str,
    payload: UlasanIn,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    stmt = select(UlasanRS).where(
        UlasanRS.user_id == current_user.id,
        UlasanRS.rs_id == rs_id,
    )
    ulasan = db.scalar(stmt)
    if ulasan:
        ulasan.rating = payload.rating
        ulasan.komentar = payload.komentar.strip()
        ulasan.status_moderasi = "disetujui"
    else:
        ulasan = UlasanRS(
            user_id=current_user.id,
            rs_id=rs_id,
            rating=payload.rating,
            komentar=payload.komentar.strip(),
        )
        db.add(ulasan)
    db.commit()
    db.refresh(ulasan)
    return {
        "id": ulasan.id,
        "rs_id": ulasan.rs_id,
        "rating": ulasan.rating,
        "komentar": ulasan.komentar,
    }


@router.get("/rs/{rs_id}/ulasan")
def daftar_ulasan_rs(
    rs_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    total = db.scalar(
        select(func.count(UlasanRS.id)).where(
            UlasanRS.rs_id == rs_id, UlasanRS.status_moderasi == "disetujui"
        )
    )
    stmt = (
        select(UlasanRS)
        .options(joinedload(UlasanRS.user))
        .where(UlasanRS.rs_id == rs_id, UlasanRS.status_moderasi == "disetujui")
        .order_by(UlasanRS.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = db.scalars(stmt).all()
    return {
        "rs_id": rs_id,
        "total": total or 0,
        "page": page,
        "ulasan": [
            {
                "id": u.id,
                "nama_pengguna": u.user.nama_lengkap if u.user else "Pengguna",
                "rating": u.rating,
                "komentar": u.komentar,
                "created_at": u.created_at,
            }
            for u in items
        ],
    }


@router.get("/rs-peringkat")
def peringkat_rumah_sakit(
    min_ulasan: int = Query(default=1, ge=1, le=100),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text(
            """
            SELECT * FROM v_peringkat_rs
            WHERE total_ulasan >= :min_ulasan
            ORDER BY peringkat_rating ASC, total_ulasan DESC
            LIMIT :limit
            """
        ),
        {"min_ulasan": min_ulasan, "limit": limit},
    ).mappings().all()
    return {"min_ulasan": min_ulasan, "peringkat": [dict(r) for r in rows]}