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
from app.services.operating_hours import schedules
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
_CANDIDATE_HOURS = []


def _load_cache():
    global _PROFILES_CACHE, _KONTAK_CACHE, _FASILITAS_CACHE, _IGD_CACHE, _JAM_CACHE, _CANDIDATE_HOURS
    if _PROFILES_CACHE:
        return

    candidate_file = ENRICH_DIR / "candidate_hours.json"
    if candidate_file.exists():
        _CANDIDATE_HOURS = json.loads(candidate_file.read_text(encoding="utf8"))

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
    """Compatibility: daily outpatient schedule from traceable records only."""
    return schedules(rs_id, jam_info.get("kode_kemenkes"), jam_info, _CANDIDATE_HOURS)["poliklinik_rawat_jalan"]["jadwal_harian"]


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

    normalized = schedules(rs_id, profile.get("kode_kemenkes"), jam_info, _CANDIDATE_HOURS)
    for key in ("reguler", "poliklinik_rawat_jalan", "pendaftaran"):
        unit = normalized[key]
        available = any(row["jam"] != "Belum tersedia" for row in unit["jadwal_harian"])
        unit_operasional.append({
            **unit,
            "jadwal_deskripsi": "; ".join(f"{r['hari']}: {r['jam']}" for r in unit["jadwal_harian"]
                                            if r["jam"] != "Belum tersedia") or "Belum tersedia",
            "status_sekarang": {"status_kode": "TERSEDIA" if available else "BELUM_TERSEDIA",
                                "label": "Tersedia" if available else "Belum tersedia"},
        })

    # Overall badge
    if is_igd_24:
        overall_badge = "IGD 24 Jam"
        overall_summary = "IGD Buka 24 Jam"
    else:
        overall_badge = "Jam Operasional"
        overall_summary = "Jam Operasional Faskes"

    jadwal_harian = normalized["poliklinik_rawat_jalan"]["jadwal_harian"]

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
