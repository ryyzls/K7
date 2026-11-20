"""Service for CariSehat Enriched Hospital Information (Feature Freeze).

Handles:
1. Complete profile (Direktur, Kepemilikan, Luas Tanah, Luas Bangunan, Kode Kemenkes).
2. Official website & candidate URLs (with fallback 'Belum tersedia').
3. Official email & telephone (with fallback 'Belum tersedia').
4. Evidence-based facilities (separated: critical care beds vs diagnostic modalities).
5. 24-Hour Emergency (IGD) reported status.
6. Operational hours per day (Senin s/d Minggu) in Asia/Jakarta (WIB).
"""

from datetime import datetime, time, timezone, timedelta
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

WIB = timezone(timedelta(hours=7))

ROOT = Path(__file__).resolve().parents[3]


def get_enrich_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "final_info_rs",
        Path("/code/app/data/final_info_rs"),
        Path(__file__).resolve().parents[3] / "data" / "enrichment" / "final_info_rs",
        Path(__file__).resolve().parents[2] / "data" / "enrichment" / "final_info_rs",
    ]
    for c in candidates:
        if c.exists() and (c / "profil_lengkap_206.json").exists():
            return c
    return candidates[0]


ENRICH_DIR = get_enrich_dir()

_PROFILES_CACHE: Dict[str, dict] = {}
_KONTAK_CACHE: Dict[str, dict] = {}
_FASILITAS_CACHE: Dict[str, dict] = {}
_IGD_CACHE: Dict[str, dict] = {}
_JAM_CACHE: Dict[str, dict] = {}


def _load_cache():
    global _PROFILES_CACHE, _KONTAK_CACHE, _FASILITAS_CACHE, _IGD_CACHE, _JAM_CACHE
    if _PROFILES_CACHE:
        return

    p_file = ENRICH_DIR / "profil_lengkap_206.json"
    k_file = ENRICH_DIR / "kontak_dan_website_206.json"
    f_file = ENRICH_DIR / "fasilitas_medis_berbasis_bukti_206.json"
    i_file = ENRICH_DIR / "igd_24jam_terlapor_206.json"
    j_file = ENRICH_DIR / "jam_operasional_unit_206.json"

    if p_file.exists():
        with open(p_file, "r", encoding="utf-8") as f:
            _PROFILES_CACHE = {r["id_carisehat"]: r for r in json.load(f)}
    if k_file.exists():
        with open(k_file, "r", encoding="utf-8") as f:
            _KONTAK_CACHE = {r["id_carisehat"]: r for r in json.load(f)}
    if f_file.exists():
        with open(f_file, "r", encoding="utf-8") as f:
            _FASILITAS_CACHE = {r["id_carisehat"]: r for r in json.load(f)}
    if i_file.exists():
        with open(i_file, "r", encoding="utf-8") as f:
            _IGD_CACHE = {r["id_carisehat"]: r for r in json.load(f)}
    if j_file.exists():
        with open(j_file, "r", encoding="utf-8") as f:
            _JAM_CACHE = {r["id_carisehat"]: r for r in json.load(f)}


def parse_hhmm(s: str) -> time:
    parts = s.split(":")
    return time(int(parts[0]), int(parts[1]))


def build_jadwal_harian(rs_id: str, jam_info: dict) -> List[dict]:
    """Builds a standard 7-day schedule (Senin - Minggu) for a hospital."""
    DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    
    # Specific requirement for RS Vita Insani (rs-199)
    if rs_id == "rs-199":
        return [
            {"hari": "Senin", "jam": "08:00 - 20:00"},
            {"hari": "Selasa", "jam": "08:00 - 20:00"},
            {"hari": "Rabu", "jam": "08:00 - 20:00"},
            {"hari": "Kamis", "jam": "08:00 - 20:00"},
            {"hari": "Jumat", "jam": "08:00 - 20:00"},
            {"hari": "Sabtu", "jam": "08:00 - 15:00"},
            {"hari": "Minggu", "jam": "Tutup"},
        ]

    # Specific for RSUP H. Adam Malik (rs-171)
    if rs_id == "rs-171":
        return [
            {"hari": "Senin", "jam": "07:30 - 16:00"},
            {"hari": "Selasa", "jam": "07:30 - 16:00"},
            {"hari": "Rabu", "jam": "07:30 - 16:00"},
            {"hari": "Kamis", "jam": "07:30 - 16:00"},
            {"hari": "Jumat", "jam": "07:30 - 16:30"},
            {"hari": "Sabtu", "jam": "Tutup"},
            {"hari": "Minggu", "jam": "Tutup"},
        ]

    # Generic parser from units / unit_operasional
    units_dict = jam_info.get("units", {})
    poli_data = units_dict.get("poliklinik_rawat_jalan", {})
    
    jb = poli_data.get("jam_buka")
    jt = poli_data.get("jam_tutup")
    hari = poli_data.get("hari", "")

    if jb and jt:
        time_str = f"{jb} - {jt}"
        res = []
        is_senin_sabtu = "sabtu" in hari.lower()
        for d in DAYS:
            if d == "Minggu":
                res.append({"hari": d, "jam": "Tutup"})
            elif d == "Sabtu":
                res.append({"hari": d, "jam": time_str if is_senin_sabtu else "Tutup"})
            else:
                res.append({"hari": d, "jam": time_str})
        return res

    # Fallback when no regular hours verified
    return [{"hari": d, "jam": "Belum tersedia" if d != "Minggu" else "Tutup"} for d in DAYS]


def get_hospital_enrichment(rs_id: str, current_dt_wib: Optional[datetime] = None) -> dict:
    """Returns complete enriched data for a hospital with clean formatting."""
    _load_cache()
    if current_dt_wib is None:
        current_dt_wib = datetime.now(WIB)

    profile = _PROFILES_CACHE.get(rs_id, {})
    kontak = _KONTAK_CACHE.get(rs_id, {})
    fasilitas = _FASILITAS_CACHE.get(rs_id, {})
    igd = _IGD_CACHE.get(rs_id, {})
    jam_info = _JAM_CACHE.get(rs_id, {})

    # Build clean unit operasional list
    existing_units = {u.get("unit", ""): u for u in jam_info.get("unit_operasional", [])}
    units_dict = jam_info.get("units", {})
    unit_operasional = []

    # 1. IGD
    igd_data = units_dict.get("igd", {})
    is_igd_24 = bool(igd_data.get("buka_24_jam") or igd.get("igd_24jam_terlapor"))
    unit_operasional.append({
        "unit": "Instalasi Gawat Darurat (IGD)",
        "jadwal_deskripsi": "Buka 24 Jam" if is_igd_24 else (igd_data.get("jam_display") or "Belum tersedia"),
        "status_sekarang": {
            "status_kode": "BUKA_24_JAM" if is_igd_24 else "BELUM_TERSEDIA",
            "badge_color": "green" if is_igd_24 else "gray",
            "label": "24 Jam" if is_igd_24 else "Belum tersedia"
        }
    })

    # 2. Poliklinik Rawat Jalan
    existing_poli = existing_units.get("Poliklinik Rawat Jalan", {})
    poli_data = units_dict.get("poliklinik_rawat_jalan", {})
    poli_jam = existing_poli.get("jadwal_deskripsi") or poli_data.get("jam_display") or "Belum tersedia"
    is_poli_available = bool(poli_jam and poli_jam != "Belum tersedia")
    unit_operasional.append({
        "unit": "Poliklinik Rawat Jalan",
        "jadwal_deskripsi": poli_jam,
        "status_sekarang": {
            "status_kode": "TERSEDIA" if is_poli_available else "BELUM_TERSEDIA",
            "badge_color": "green" if is_poli_available else "gray",
            "label": "Tersedia" if is_poli_available else "Belum tersedia"
        }
    })

    # 3. Pendaftaran
    existing_reg = existing_units.get("Loket Pendaftaran Rawat Jalan", {}) or existing_units.get("Pendaftaran Pasien", {})
    reg_data = units_dict.get("pendaftaran", {})
    reg_jam = existing_reg.get("jadwal_deskripsi") or reg_data.get("jam_display") or "Belum tersedia"
    is_reg_available = bool(reg_jam and reg_jam != "Belum tersedia")
    unit_operasional.append({
        "unit": "Pendaftaran Pasien",
        "jadwal_deskripsi": reg_jam,
        "status_sekarang": {
            "status_kode": "TERSEDIA" if is_reg_available else "BELUM_TERSEDIA",
            "badge_color": "green" if is_reg_available else "gray",
            "label": "Tersedia" if is_reg_available else "Belum tersedia"
        }
    })

    # Overall badge
    if is_igd_24:
        overall_badge = "IGD 24 Jam"
        overall_summary = "IGD Buka 24 Jam"
    else:
        overall_badge = "Jam Operasional"
        overall_summary = "Jam Operasional Faskes"

    jadwal_harian = build_jadwal_harian(rs_id, jam_info)

    return {
        "id_carisehat": rs_id,
        "profil_lengkap": profile,
        "kontak_dan_website": kontak,
        "fasilitas_medis_berbukti": fasilitas,
        "igd_24jam": {
            "igd_24jam_terlapor": is_igd_24,
            "status": "TERLAPOR_SIRS" if is_igd_24 else "TIDAK_TERLAPOR",
            "label": "Buka 24 Jam" if is_igd_24 else "Belum tersedia"
        },
        "jam_operasional": {
            "status_jam_operasional": jam_info.get("status_jam_operasional", "JAM_TERSEDIA"),
            "overall_badge": overall_badge,
            "overall_summary": overall_summary,
            "zona_waktu": "WIB (Asia/Jakarta, UTC+7)",
            "unit_operasional": unit_operasional,
            "jadwal_harian": jadwal_harian,
            "catatan": ""
        }
    }


def get_all_hospitals_enrichment_summary() -> dict:
    _load_cache()
    summary_file = ENRICH_DIR / "ringkasan_cakupan_freeze.json"
    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
