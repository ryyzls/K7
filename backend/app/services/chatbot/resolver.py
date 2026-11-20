"""Modul Resolusi Nama Rumah Sakit & Ekstraksi Atribut.

Mendukung:
- Pembersihan kata perintah & atribut
- Pencocokan nama toleran typo, singkatan, dan alias
- Disambiguasi cerdas jika terdapat beberapa kandidat seimbang
- Ekstraksi atribut spesifik (telepon, alamat, BPJS, ICU, jam buka, kelas, jenis, pemilik, layanan, fasilitas)
"""
from __future__ import annotations

import re
from typing import Any

from app.services.chatbot.models import KABKOTA_MAP, LAYANAN_SYNONYMS, FASILITAS_SYNONYMS
from app.services.fuzzy_search import (
    AMBANG,
    normalize,
    skor,
    skor_rs,
)

# Kumpulan kata yang hanya merupakan filter pencarian (bukan nama RS spesifik)
FILTER_ONLY_WORDS: set[str] = {
    "a", "b", "c", "d", "umum", "khusus", "terdekat", "dekat", "sekitar",
    "semua", "daftar", "seluruh", "semua rs", "cari rs", "cari rumah sakit",
    "faskes", "rujukan", "berobat", "pasien", "dokter", "spesialis",
}
for _k in KABKOTA_MAP:
    FILTER_ONLY_WORDS.add(_k)
    for _c in ["a", "b", "c", "d"]:
        FILTER_ONLY_WORDS.add(f"{_c} {_k}")
for _l in LAYANAN_SYNONYMS:
    FILTER_ONLY_WORDS.add(_l)
for _f in FASILITAS_SYNONYMS:
    FILTER_ONLY_WORDS.add(_f)


def is_pure_filter_query(cleaned: str) -> bool:
    """Cek apakah string hasil pembersihan hanya berupa filter umum (bukan nama RS)."""
    c = cleaned.strip().lower()
    if not c or len(c) <= 1:
        return True
    if c in FILTER_ONLY_WORDS:
        return True
    return False

# ---------------------------------------------------------------------------
# Pola Kata Perintah & Atribut untuk Dibersihkan dari Query Nama
# ---------------------------------------------------------------------------
STRIP_PATTERNS = [
    r"\bapa\s+itu\b", r"\bapakah\s+kamu\s+tau\b", r"\bapakah\s+tahu\b", r"\bapakah\b",
    r"\btolong\b", r"\bbantu\b", r"\bcari\b", r"\blihat\b", r"\btampilkan\b",
    r"\bdetail\b", r"\binfo\b", r"\binformasi\b", r"\btentang\b", r"\bprofil\b",
    r"\balamat(?:nya)?\b", r"\blokasi(?:nya)?\b", r"\bdimana(?:kah)?\b", r"\bdi\s+mana(?:kah)?\b",
    r"\bletak(?:nya)?\b", r"\bposisi(?:nya)?\b", r"\bberada\b",
    r"\bnomor\s+telepon\b", r"\bno\s+telp\b", r"\bno\s+telepon\b", r"\bno\s+hp\b",
    r"\btelepon(?:nya)?\b", r"\btelp(?:nya)?\b", r"\bkontak(?:nya)?\b", r"\bhubungi\b",
    r"\bterima\s+bpjs\b", r"\bbisa\s+bpjs\b", r"\bbpjs\b",
    r"\bjam\s+buka\b", r"\bjam\s+operasional\b", r"\bjadwal\s+dokter\b", r"\bjadwal\b", r"\bbuka\s+jam\s+berapa\b",
    r"\bpunya\s+icu\b", r"\bada\s+icu\b", r"\bicu\b",
    r"\blayanan\s+apa\s+saja\b", r"\blayanan(?:nya)?\b", r"\bpoli(?:nya)?\b", r"\bspesialis(?:nya)?\b",
    r"\bfasilitas(?:nya)?\b", r"\bjenis(?:nya)?\b", r"\bkelas(?:nya)?\b", r"\btipe(?:nya)?\b",
    r"\bpemilik(?:nya)?\b", r"\bmilik(?:nya)?\b",
    r"\byang\b", r"\bkalau\b", r"\bbagaimana\b", r"\bdengan\b",
    r"\bpunya\b", r"\bada\b", r"\bapa\b", r"\bsaja\b", r"\bdi\b", r"\bdari\b",
    r"\bse-sumut\b", r"\bsumut\b", r"\bsumatera\s+utara\b", r"\bse\b",
    r"\bitu\b", r"\bini\b", r"\bya\b", r"\byah\b", r"\bdong\b", r"\bsih\b", r"\bkan\b",
    r"\brumah\s+sakit\s+umum\s+daerah\b", r"\brumah\s+sakit\s+umum\s+pusat\b", r"\brumah\s+sakit\s+umum\b",
    r"\brumah\s+sakit\b", r"\brsud\b", r"\brsup\b", r"\brsu\b", r"\brsia\b", r"\brsk\b", r"\brsj\b", r"\brsau\b",
    r"\brs\b",
]


def clean_hospital_query(text: str) -> str:
    """Normalisasi & buang kata perintah, atribut, dan awalan tipe RS."""
    t = normalize(text)
    t = re.sub(r"\b(?:berapa|seberapa)\s+(?:jarak(?:nya)?|jauh)\b|\bjarak(?:nya)?\b|\bke\b|\blokasi\s+saya\b", " ", t)
    t = re.sub(r"\b(?:tanpa|non|bukan|tidak\s+terima)\s+bpjs\b", " ", t)
    for p in STRIP_PATTERNS:
        t = re.sub(p, " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_attribute(text: str) -> str | None:
    """Ekstraksi atribut spesifik yang ditanyakan pengguna mengenai RS."""
    tl = text.lower()
    if re.search(r"\b(jarak(?:nya)?|seberapa\s+jauh|berapa\s+jauh)\b", tl):
        return "jarak"
    tl = re.sub(r"\b(telepon|telp|alamat|lokasi|layanan|fasilitas|kelas|jenis|pemilik)nya\b", r"\1", tl)
    if re.search(r"\b(telepon|telp|nomor|kontak|hubungi|no telp|no hp|hotline)\b", tl):
        return "telepon"
    if re.search(r"\b(alamat|lokasi|dimana|di mana|letak|posisi|berada|letaknya|dimanakah|di manakah)\b", tl):
        return "alamat"
    if re.search(r"\b(bpjs|askes|kis|kartu indonesia sehat|jaminan kesehatan)\b", tl):
        return "bpjs"
    if re.search(r"\b(jam|buka|jadwal|operasional|waktu buka|hari kerja)\b", tl):
        return "jam_buka"
    if re.search(r"\b(icu|iccu|nicu|picu)\b", tl):
        return "icu"
    if re.search(r"\b(layanan|poli|spesialis|poliklinik|dokter)\b", tl):
        return "layanan"
    if re.search(r"\b(fasilitas|ambulans|ambulance|kamar operasi|ruang operasi|laboratorium|radiologi|apotek|farmasi)\b", tl):
        return "fasilitas"
    if re.search(r"\b(kelas|tipe|kls)\b", tl):
        return "kelas"
    if re.search(r"\b(jenis)\b", tl):
        return "jenis"
    if re.search(r"\b(pemilik|milik|swasta|pemerintah|tni|polri|bumn|yayasan)\b", tl):
        return "pemilik"
    if re.search(r"\b(foto|gambar|galeri)\b", tl):
        return "foto"
    if re.search(r"\b(rute|arah|jarak|ke sana)\b", tl):
        return "rute"
    return None


def extract_compare_pair(tl: str) -> list[str]:
    """Ekstraksi dua nama rumah sakit untuk intent COMPARE."""
    followup = re.search(r"^(?:bandingkan|banding)\s+dengan\s+(.+)", tl)
    if followup:
        name = clean_hospital_query(followup.group(1))
        return [name] if name else []
    m = re.search(
        r"(?:bandingkan|banding|perbandingan|mana yang lebih bagus antara)\s+(.+?)(?:\s+(?:dan|vs|versus|dengan)\s+)(.+)",
        tl,
    )
    if m:
        name_a = clean_hospital_query(m.group(1))
        name_b = clean_hospital_query(m.group(2))
        if name_a and name_b:
            return [name_a, name_b]

    m2 = re.search(r"(.+?)\s+(?:vs|versus)\s+(.+)", tl)
    if m2:
        name_a = clean_hospital_query(m2.group(1))
        name_b = clean_hospital_query(m2.group(2))
        if name_a and name_b:
            return [name_a, name_b]
    return []


def resolve_hospital_name(
    raw_query: str,
    hospitals: list[dict],
    threshold: float = 0.65,
) -> dict:
    """Resolusi nama rumah sakit dari teks pengguna.
    
    Mengembalikan dict:
    - status: 'dominant' | 'disambiguate' | 'not_found' | 'none'
    - target_rs: dict | None (jika dominan)
    - candidates: list[dict] (jika disambiguasi)
    - suggestions: list[dict] (jika not_found)
    - attribute: str | None
    - cleaned_name: str
    """
    cleaned = clean_hospital_query(raw_query)
    attribute = extract_attribute(raw_query)

    if not cleaned or len(cleaned) < 2 or is_pure_filter_query(cleaned):
        return {
            "status": "none",
            "target_rs": None,
            "candidates": [],
            "suggestions": [],
            "attribute": attribute,
            "cleaned_name": cleaned,
        }

    scored: list[tuple[float, dict]] = []
    all_scored: list[tuple[float, dict]] = []

    for h in hospitals:
        s = skor_rs(cleaned, h)
        all_scored.append((s, h))
        if s >= threshold:
            scored.append((s, h))

    scored.sort(key=lambda x: (-x[0], x[1]["nama"]))
    all_scored.sort(key=lambda x: (-x[0], x[1]["nama"]))

    # Jika tidak ada yang lolos ambang batas
    if not scored:
        is_rs_query = bool(re.search(r"\b(rs|rumah\s*sakit|rsud|rsup|rsu|rsia|rsk)\b", raw_query.lower()))
        suggestions = [h for _, h in all_scored[:3]]
        return {
            "status": "not_found" if is_rs_query else "none",
            "target_rs": None,
            "candidates": [],
            "suggestions": suggestions,
            "attribute": attribute,
            "cleaned_name": cleaned,
        }

    # Satu kandidat tunggal
    if len(scored) == 1:
        return {
            "status": "dominant",
            "target_rs": scored[0][1],
            "candidates": [scored[0][1]],
            "suggestions": [],
            "attribute": attribute,
            "cleaned_name": cleaned,
        }

    # Beberapa kandidat lolos ambang
    s1, h1 = scored[0]
    s2, h2 = scored[1]

    # Evaluasi dominan vs disambiguasi
    # Jika skor tertinggi dominan (selisih >= 0.12)
    if (s1 - s2) >= 0.12 or (s1 == 1.0 and s2 < 0.90):
        return {
            "status": "dominant",
            "target_rs": h1,
            "candidates": [h1],
            "suggestions": [],
            "attribute": attribute,
            "cleaned_name": cleaned,
        }

    # Jika sama kuat (mis. Martha Friska vs Martha Friska Multatuli, Royal Prima vs Royal Prima Marelan)
    # Tampilkan 2-4 kandidat teratas
    candidates = [h for _, h in scored[:4]]
    return {
        "status": "disambiguate",
        "target_rs": None,
        "candidates": candidates,
        "suggestions": [],
        "attribute": attribute,
        "cleaned_name": cleaned,
    }
