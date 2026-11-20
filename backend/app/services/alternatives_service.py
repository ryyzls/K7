"""Layanan pencarian rumah sakit alternatif berbasis kecocokan spesialisasi SIRS & wilayah.

Prioritas deterministik yang dapat dijelaskan:
1. Kesamaan spesialisasi/layanan SIRS yang lolos kebijakan kurasi.
2. Kesamaan wilayah administratif (kabupaten/kota).
3. Kesetaraan kelas atau tipe rumah sakit.
4. Alasan rekomendasi yang eksplisit dan faktual tanpa mengarang jarak perkiraan koordinat.
"""
from __future__ import annotations

from typing import Any
from fastapi import HTTPException

from app.services import sparql_service as sp
from app.services import sirs
from app.services.specialty_service import get_hospital_specialties


async def find_alternatives(rs_id: str, limit: int = 4) -> dict[str, Any]:
    """Mencari 3-5 rumah sakit alternatif terbaik berdasarkan kesamaan layanan SIRS dan wilayah."""
    limit = max(1, min(limit, 5))
    try:
        target = await sp.get_hospital(rs_id)
    except Exception:
        target = None
    if not target:
        raise HTTPException(status_code=404, detail=f"Rumah sakit dengan ID '{rs_id}' tidak ditemukan.")

    # Kumpulkan seluruh layanan dan spesialisasi target
    target_specs = {s["label"] for s in get_hospital_specialties(rs_id)}
    target_services = set(target.get("layanan", [])) | target_specs
    target_kabkota = target.get("kabkota") or ""
    target_kelas = target.get("kelas") or ""
    target_jenis = target.get("jenis") or ""

    # Ambil kandidat rumah sakit (ambil semua faskes di Sumut untuk scoring akurat)
    candidates = await sp.search_hospitals(limit=500)

    scored: list[dict[str, Any]] = []
    for cand in candidates:
        if cand["id"] == rs_id:
            continue

        cand_specs = {s["label"] for s in get_hospital_specialties(cand["id"])}
        cand_services = set(cand.get("layanan", [])) | cand_specs
        common_services = sorted(list(target_services & cand_services))

        # Hitung skor
        score = 0
        alasan_parts = []

        # 1. Wilayah administratif
        same_kabkota = bool(target_kabkota and cand.get("kabkota") == target_kabkota)
        if same_kabkota:
            score += 50
            alasan_parts.append(f"Sama-sama berada di {target_kabkota}")
        else:
            cand_kab = cand.get("kabkota") or "wilayah lain"
            alasan_parts.append(f"Berada di {cand_kab}")

        # 2. Kesamaan layanan SIRS
        n_common = len(common_services)
        if n_common > 0:
            score += n_common * 15
            # Sorot layanan penting (misal UGD, spesialis jantung/anak/penyakit dalam)
            top_shared = common_services[:3]
            alasan_parts.append(
                f"memiliki {n_common} layanan serupa yang tercatat di SIRS ({', '.join(top_shared)})"
            )
        else:
            # Jika tidak ada layanan sama sekali yang cocok, kurangi relevansi
            score -= 30

        # Bonus gawat darurat
        if sirs.EMERGENCY in common_services:
            score += 25

        # 3. Kesetaraan kelas & jenis
        cand_kelas = cand.get("kelas") or ""
        if target_kelas and cand_kelas == target_kelas:
            score += 20
            alasan_parts.append(f"kelas setara (Kelas {cand_kelas})")
        elif target_kelas and cand_kelas:
            score += 5

        if target_jenis and cand.get("jenis") == target_jenis:
            score += 10

        if n_common > 0 or same_kabkota:
            # Susun narasi alasan yang dapat dijelaskan
            alasan_rekomendasi = "; ".join(alasan_parts) + "."
            scored.append({
                "id": cand["id"],
                "nama": cand["nama"],
                "kelas": cand.get("kelas") or "Belum terklasifikasi",
                "jenis": cand.get("jenis") or "Rumah Sakit Umum",
                "kabkota": cand.get("kabkota") or "Belum tersedia",
                "alamat": cand.get("alamat") or "Alamat belum tersedia",
                "telepon": cand.get("telepon") or "Belum tersedia",
                "foto": cand.get("foto") or f"/images/rs/{cand['id']}/foto_1.jpg",
                "score": score,
                "layanan_serupa": common_services,
                "jumlah_layanan_serupa": n_common,
                "alasan_rekomendasi": alasan_rekomendasi,
                "layanan_facts_count": len(cand_services),
            })

    # Urutkan berdasarkan skor tertinggi lalu jumlah layanan sama
    scored.sort(key=lambda x: (x["score"], x["jumlah_layanan_serupa"]), reverse=True)
    top_alternatives = scored[:limit]

    has_alternatives = len(top_alternatives) > 0
    message = (
        f"Ditemukan {len(top_alternatives)} rumah sakit alternatif yang relevan."
        if has_alternatives
        else "Tidak ada rumah sakit alternatif dengan kriteria layanan spesialisasi serupa yang terdata di wilayah ini."
    )

    return {
        "target_rs": {
            "id": target["id"],
            "nama": target["nama"],
            "kabkota": target_kabkota,
            "kelas": target_kelas,
            "jenis": target_jenis,
            "layanan_sirs_count": len(target_services),
        },
        "count": len(top_alternatives),
        "has_alternatives": has_alternatives,
        "message": message,
        "alternatives": top_alternatives,
        "disclaimer": "Rekomendasi alternatif dihitung berdasarkan kesamaan wilayah administratif dan catatan layanan SIRS Kemenkes, bukan estimasi jarak rute GPS atau ketersediaan dokter real-time.",
    }
