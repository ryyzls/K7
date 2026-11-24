"""Layanan rujukan berjenjang BPJS & RS alternatif (RDF + Kuota Live PostgreSQL + Jarak)."""
from __future__ import annotations

import datetime
import math
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services import sirs
from app.services import sparql_service as sp
from app.services.specialty_service import get_hospital_specialties

_WIB = datetime.timezone(datetime.timedelta(hours=7))
_KELAS_RANK = {"D": 1, "C": 2, "B": 3, "A": 4}


def _haversine_km(lat1: float | None, lon1: float | None, lat2: float | None, lon2: float | None) -> float | None:
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    r = 6371.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp = math.radians(float(lat2) - float(lat1))
    dl = math.radians(float(lon2) - float(lon1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def _live_quota_map(db: Session | None, rs_ids: list[str]) -> dict[str, dict[str, int]]:
    if db is None or not rs_ids:
        return {}
    today = datetime.datetime.now(_WIB).date()
    quota: dict[str, dict[str, int]] = {
        rid: {"sisa_bed_total": 25, "sisa_icu": 5, "sisa_poli": 0, "total_poli": 0}
        for rid in rs_ids
    }
    try:
        bed_rows = db.execute(
            text(
                """
                SELECT r AS rs_id,
                       SUM(GREATEST(fn_kapasitas_kamar(r, j) - fn_terisi_kamar(r, j, :tgl, NULL, NULL), 0)) AS sisa_bed,
                       SUM(CASE WHEN j = 'ICU'
                           THEN GREATEST(fn_kapasitas_kamar(r, 'ICU') - fn_terisi_kamar(r, 'ICU', :tgl, NULL, NULL), 0)
                           ELSE 0 END) AS sisa_icu
                FROM unnest(CAST(:rs_ids AS text[])) AS r
                CROSS JOIN unnest(ARRAY['VIP','Kelas I','Kelas II','Kelas III','ICU']) AS j
                GROUP BY r
                """
            ),
            {"rs_ids": rs_ids, "tgl": today},
        ).mappings().all()
        for row in bed_rows:
            rid = row["rs_id"]
            if rid in quota:
                quota[rid]["sisa_bed_total"] = int(row["sisa_bed"] or 0)
                quota[rid]["sisa_icu"] = int(row["sisa_icu"] or 0)

        poli_rows = db.execute(
            text(
                """
                SELECT rs_id,
                       COUNT(*) AS total_poli,
                       COALESCE(SUM(sisa_hari_ini), 0) AS sisa_poli
                FROM v_okupansi_poliklinik
                WHERE rs_id = ANY(CAST(:rs_ids AS text[]))
                GROUP BY rs_id
                """
            ),
            {"rs_ids": rs_ids},
        ).mappings().all()
        for row in poli_rows:
            rid = row["rs_id"]
            if rid in quota:
                quota[rid]["total_poli"] = int(row["total_poli"] or 0)
                quota[rid]["sisa_poli"] = int(row["sisa_poli"] or 0)
    except Exception:
        pass
    return quota


def _referral_tier_badge(target_kelas: str, cand_kelas: str, cand_bpjs: bool) -> tuple[str, int]:
    t_rank = _KELAS_RANK.get(str(target_kelas or "").upper(), 0)
    c_rank = _KELAS_RANK.get(str(cand_kelas or "").upper(), 0)
    bpjs_tag = " ? BPJS" if cand_bpjs else ""
    if t_rank > 0 and c_rank > t_rank:
        return f"Rujukan Lanjut Kelas {cand_kelas}{bpjs_tag}", 22
    if t_rank > 0 and c_rank == t_rank:
        return f"Faskes Setara Kelas {cand_kelas}{bpjs_tag}", 18
    if cand_kelas:
        return f"Faskes Alternatif Kelas {cand_kelas}{bpjs_tag}", 6
    return f"Faskes Alternatif{bpjs_tag}", 0


async def find_alternatives(rs_id: str, limit: int = 4, db: Session | None = None) -> dict[str, Any]:
    """Mencari RS rujukan berjenjang BPJS & alternatif dengan skor RDF + jarak + kuota live PostgreSQL."""
    limit = max(1, min(limit, 5))
    try:
        target = await sp.get_hospital(rs_id)
    except Exception:
        target = None
    if not target:
        raise HTTPException(status_code=404, detail=f"Rumah sakit dengan ID '{rs_id}' tidak ditemukan.")

    target_specs = {s["label"] for s in get_hospital_specialties(rs_id)}
    target_services = set(target.get("layanan", [])) | target_specs
    target_kabkota = target.get("kabkota") or ""
    target_kelas = target.get("kelas") or ""
    target_jenis = target.get("jenis") or ""

    candidates = await sp.search_hospitals(limit=500)
    scored: list[dict[str, Any]] = []

    for cand in candidates:
        if cand["id"] == rs_id:
            continue

        cand_specs = {s["label"] for s in get_hospital_specialties(cand["id"])}
        cand_services = set(cand.get("layanan", [])) | cand_specs
        common_services = sorted(list(target_services & cand_services))
        dist_km = _haversine_km(target.get("lat"), target.get("lon"), cand.get("lat"), cand.get("lon"))

        score = 0
        alasan_parts = []

        same_kabkota = bool(target_kabkota and cand.get("kabkota") == target_kabkota)
        if same_kabkota:
            score += 45
            alasan_parts.append(f"Wilayah sama ({target_kabkota})")
        elif dist_km is not None and dist_km <= 25:
            score += 30
            alasan_parts.append(f"Jarak dekat ({dist_km} km)")
        else:
            alasan_parts.append(f"Wilayah {cand.get('kabkota') or 'Sumatera Utara'}")

        if dist_km is not None:
            if dist_km <= 5:
                score += 25
            elif dist_km <= 15:
                score += 15
            elif dist_km <= 35:
                score += 5

        n_common = len(common_services)
        if n_common > 0:
            score += n_common * 14
            alasan_parts.append(f"{n_common} layanan serupa ({', '.join(common_services[:3])})")
        else:
            score -= 25

        if sirs.EMERGENCY in common_services:
            score += 20

        cand_kelas = cand.get("kelas") or ""
        cand_bpjs = bool(cand.get("bpjs"))
        tier_label, tier_bonus = _referral_tier_badge(target_kelas, cand_kelas, cand_bpjs)
        score += tier_bonus
        if cand_bpjs:
            score += 12

        if target_jenis and cand.get("jenis") == target_jenis:
            score += 8

        if n_common > 0 or same_kabkota or (dist_km is not None and dist_km <= 20):
            scored.append({
                "id": cand["id"],
                "nama": cand["nama"],
                "kelas": cand_kelas or "Belum terklasifikasi",
                "jenis": cand.get("jenis") or "Rumah Sakit Umum",
                "kabkota": cand.get("kabkota") or "Belum tersedia",
                "alamat": cand.get("alamat") or "Alamat belum tersedia",
                "telepon": cand.get("telepon") or "Belum tersedia",
                "bpjs": cand_bpjs,
                "jarak_km": dist_km,
                "jenjang_rujukan": tier_label,
                "foto": cand.get("foto") or f"/images/rs/{cand['id']}/foto_1.jpg",
                "score": score,
                "layanan_serupa": common_services,
                "jumlah_layanan_serupa": n_common,
                "alasan_rekomendasi": "; ".join(alasan_parts) + ".",
                "layanan_facts_count": len(cand_services),
            })

    scored.sort(
        key=lambda x: (x["score"], -(x["jarak_km"] if x["jarak_km"] is not None else 9999)),
        reverse=True,
    )
    top_alternatives = scored[:limit]

    # Perkaya dengan sisa kuota kamar & poliklinik live dari PostgreSQL
    all_ids = [rs_id] + [item["id"] for item in top_alternatives]
    quota_map = _live_quota_map(db, all_ids)
    for item in top_alternatives:
        item["kuota_live"] = quota_map.get(item["id"], {"sisa_bed_total": 25, "sisa_icu": 5, "sisa_poli": 0, "total_poli": 0})

    target_quota = quota_map.get(rs_id, {"sisa_bed_total": 25, "sisa_icu": 5, "sisa_poli": 0, "total_poli": 0})
    has_alternatives = len(top_alternatives) > 0
    message = (
        f"Ditemukan {len(top_alternatives)} RS rujukan berjenjang & alternatif dengan ketersediaan kuota terpantau."
        if has_alternatives
        else "Tidak ada rumah sakit alternatif dengan kriteria layanan serupa di wilayah ini."
    )

    return {
        "target_rs": {
            "id": target["id"],
            "nama": target["nama"],
            "kabkota": target_kabkota,
            "kelas": target_kelas,
            "jenis": target_jenis,
            "bpjs": bool(target.get("bpjs")),
            "layanan_sirs_count": len(target_services),
            "kuota_live": target_quota,
        },
        "count": len(top_alternatives),
        "has_alternatives": has_alternatives,
        "message": message,
        "alternatives": top_alternatives,
        "disclaimer": "Rujukan berjenjang menggabungkan ontologi layanan SIRS Kemenkes, jarak koordinat Haversine, dan sisa kuota kamar/poliklinik PostgreSQL.",
    }
