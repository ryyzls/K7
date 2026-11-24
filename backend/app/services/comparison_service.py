"""Layanan perbandingan rumah sakit (maksimal 3 RS).

Membandingkan atribut faktual:
- Nama & Kode registrasi Kemenkes
- Wilayah kabupaten/kota
- Kelas & jenis rumah sakit
- Alamat & kontak (telepon, email bila ada)
- Website resmi terverifikasi
- Layanan & spesialisasi terlapor SIRS (termasuk irisannya)
- Fasilitas (ditandai belum diverifikasi independen)
- Menandai data yang belum tersedia secara jujur tanpa mengarang rating/biaya/jadwal.
"""
from __future__ import annotations

from typing import Any
from fastapi import HTTPException

from app.services import sparql_service as sp
from app.services.specialty_service import get_hospital_specialties


async def compare_hospitals(rs_ids: list[str]) -> dict[str, Any]:
    """Menghasilkan data perbandingan matriks untuk 2 hingga 3 rumah sakit."""
    cleaned_ids = [i.strip() for i in rs_ids if i.strip()]
    # Hapus duplikat sambil menjaga urutan
    seen = set()
    unique_ids = []
    for i in cleaned_ids:
        if i not in seen:
            seen.add(i)
            unique_ids.append(i)

    if not unique_ids:
        raise HTTPException(status_code=400, detail="Daftar ID rumah sakit tidak boleh kosong.")
    if len(unique_ids) > 3:
        raise HTTPException(
            status_code=400,
            detail=f"Maksimal 3 rumah sakit yang dapat dibandingkan sekaligus (diminta: {len(unique_ids)} RS)."
        )

    hospitals_data: list[dict[str, Any]] = []
    for rs_id in unique_ids:
        try:
            h = await sp.get_hospital(rs_id)
        except Exception:
            h = None
        if not h:
            raise HTTPException(status_code=404, detail=f"Rumah sakit dengan ID '{rs_id}' tidak ditemukan.")

        # Ambil spesialisasi dan layanan SIRS
        specs = get_hospital_specialties(rs_id)
        spec_labels = sorted(list({s["label"] for s in specs}))
        approved_services = sorted(h.get("layanan", []))

        # Kode Kemenkes
        kode_kemenkes = h.get("kode_kemenkes")
        if not kode_kemenkes:
            # Ambil dari observation source url jika ada
            if specs and specs[0].get("source_url"):
                url = specs[0]["source_url"]
                parts = url.rstrip("/").split("/")
                if parts[-1].isdigit():
                    kode_kemenkes = parts[-1]

        # Website resmi: hanya sertakan jika terverifikasi
        official_web = None
        if h.get("website_status") == "verified" and h.get("website"):
            official_web = {
                "url": h["website"],
                "status": "verified",
                "scope": h.get("website_scope", "hospital"),
                "checked_at": h.get("website_checked_at"),
            }

        hospitals_data.append({
            "id": h["id"],
            "uri": h.get("uri"),
            "nama": h["nama"],
            "kode_kemenkes": kode_kemenkes or "Belum tersedia",
            "kabkota": h.get("kabkota") or "Belum tersedia",
            "kelas": h.get("kelas") or "Belum terklasifikasi",
            "jenis": h.get("jenis") or "Rumah Sakit Umum",
            "alamat": h.get("alamat") or "Alamat belum tersedia",
            "telepon": h.get("telepon") or "Belum tersedia",
            "website_resmi": official_web,
            "has_official_website": official_web is not None,
            "bpjs_info": {
                "menerima_bpjs": h.get("bpjs"),
                "status_verifikasi": "not_verified_by_sirs_services",
                "catatan": "Status BPJS merupakan data awal katalog; konfirmasikan langsung ke RS.",
            },
            "spesialisasi_sirs": spec_labels,
            "layanan_terkurasi": approved_services,
            "semua_layanan_sirs": sorted(list(set(spec_labels + approved_services))),
            "fasilitas": h.get("fasilitas", []),
            "fasilitas_status": "unverified_legacy",
            "lat": h.get("lat"),
            "lon": h.get("lon"),
            "foto": h.get("foto"),
        })

    # Hitung irisan layanan yang sama dan perbedaan
    sets_of_services = [set(h["semua_layanan_sirs"]) for h in hospitals_data]
    shared_services = sorted(list(set.intersection(*sets_of_services))) if sets_of_services else []
    union_services = sorted(list(set.union(*sets_of_services))) if sets_of_services else []

    # Layanan unik per RS
    unique_per_hospital: dict[str, list[str]] = {}
    for h in hospitals_data:
        other_services = set()
        for other in hospitals_data:
            if other["id"] != h["id"]:
                other_services.update(other["semua_layanan_sirs"])
        unique_per_hospital[h["id"]] = sorted(list(set(h["semua_layanan_sirs"]) - other_services))

    return {
        "count": len(hospitals_data),
        "hospitals": hospitals_data,
        "comparison_matrix": {
            "shared_services": shared_services,
            "all_distinct_services": union_services,
            "unique_services_per_hospital": unique_per_hospital,
        },
        "disclaimers": [
            "Informasi layanan dan spesialisasi bersumber dari profil Kementerian Kesehatan; perubahan terbaru mungkin belum tercatat.",
            "Fasilitas rumah sakit belum selalu diperiksa langsung.",
            "Informasi tempat tidur, biaya, jarak, dan jadwal dokter dapat berbeda atau belum tersedia.",
        ],
    }
