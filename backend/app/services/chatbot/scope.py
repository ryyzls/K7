"""Modul Validasi Cakupan Domain (Whitelist Scope Classifier).

Menerapkan aturan Whitelist (default tolak):
Sebuah pesan in-scope HANYA jika memenuhi salah satu kriteria sah.
Semua pencocokan kata kunci memakai batas kata (word boundary) untuk mencegah
false positive (misal 'matahari' memicu 'mata', atau 'komando' memicu 'koma').
"""
from __future__ import annotations

import re
from typing import Any

from app.services.chatbot.models import (
    EMERGENCY_KEYWORDS,
    FAQ_KEYWORDS,
    FASILITAS_SYNONYMS,
    GREETING_KEYWORDS,
    HOSPITAL_EXPLICIT_ROOTS,
    KABKOTA_MAP,
    LAYANAN_SYNONYMS,
    NEARBY_KEYWORDS,
)
from app.services.fuzzy_search import normalize

# Quick replies resmi yang dikeluarkan chatbot
KNOWN_QUICK_REPLIES = {
    "hubungi 119",
    "panggil ambulans",
    "rs dengan ugd 24 jam terdekat",
    "rs dengan ugd 24 jam",
    "rs terdekat dari saya",
    "rs kelas a di medan",
    "lihat rs kelas a saja",
    "lihat semua rs di medan",
    "rs yang terima bpjs",
    "rs yang punya icu",
    "yang terima bpjs?",
    "yang punya icu?",
    "yang terima bpjs",
    "yang punya icu",
    "lihat lainnya",
    "lainnya",
    "cari rs di medan",
    "kota medan",
    "kab. deli serdang",
    "kota binjai",
    "kota pematang siantar",
    "tanpa filter kelas",
}

NON_HOSPITAL_PATTERNS = [
    r"\btebak\b", r"\bnamaku\b", r"\bnama\s+saya\b", r"\bumurku\b",
    r"\bsiapa\s+(?:kamu|namamu|anda|dia|mereka|presiden)\b",
    r"\bkamu\s+(?:siapa|lagi\s+apa|bisa\s+apa)\b",
    r"\bcuaca\b", r"\bprakiraan\b", r"\bhujan\b",
    r"\bresep\b", r"\bmasak\b", r"\bkuliner\b", r"\bmakanan\b", r"\bnasi\s+goreng\b", r"\brendang\b",
    r"\brumah\s+makan\b", r"\brestoran\b", r"\bresto\b", r"\bcafe\b", r"\bkafe\b", r"\bwarung\b",
    r"\bhotel\b", r"\bpenginapan\b", r"\bvilla\b", r"\bwisata\b", r"\bpantai\b",
    r"\bfilm\b", r"\bbioskop\b", r"\blagu\b", r"\bmusik\b", r"\bgitar\b",
    r"\bmobil\b", r"\bmotor\b", r"\bbengkel\b", r"\bspbu\b", r"\bpom\s+bensin\b",
    r"\bkucing\b", r"\banjing\b", r"\bkelinci\b", r"\bhewan\b",
    r"\bpresiden\b", r"\bsejarah\b", r"\bmatematika\b", r"\bcoding\b", r"\bpython\b", r"\bjavascript\b",
    r"\bpuisi\b", r"\bcerita\b", r"\blelucon\b", r"\bjoke\b", r"\bhumor\b",
    r"\btiket\b", r"\bpesawat\b", r"\bmatahari\b",
]

STOPWORDS_CITY = {
    "coba", "tebak", "nama", "namaku", "namamu", "siapa", "kamu", "saya", "aku", "dia",
    "hari", "lagi", "bisa", "buat", "mau", "ada", "apa", "kucing", "anjing",
    "mobil", "motor", "makan", "minum", "tidur", "main", "kerja", "belajar",
    "rumah", "buku", "uang", "lagu", "film", "game", "halo", "kabar", "tahu",
    "bantu", "tolong", "mohon", "kenapa", "bagaimana", "mana", "yang", "dari",
    "oleh", "pada", "untuk", "dengan", "dan", "atau", "tidak", "bukan", "tentang",
    "bagus", "paling", "resep", "cuaca", "presiden", "sebutkan", "ceritakan", "lelucon",
    "salak", "pandan", "lotu", "karo", "toba", "matahari", "wisata", "tiket", "pesawat",
}


def _matches_any_word_bounded(text: str, keywords: list[str] | set[str]) -> bool:
    """Cek kecocokan kata kunci dengan batas kata (\b)."""
    for kw in keywords:
        pat = rf"\b{re.escape(kw.strip().lower())}\b"
        if re.search(pat, text):
            return True
    return False


def match_city(text: str) -> str | None:
    """Cocokkan nama kota/kabupaten di Sumatera Utara secara akurat dengan batas kata & toleransi typo."""
    import difflib

    tl = text.lower()
    sorted_keys = sorted(KABKOTA_MAP.keys(), key=len, reverse=True)
    for key in sorted_keys:
        # Hindari kata umum yang ambigu kecuali konteks nama daerah (mis. salak, pandan, toba, karo)
        if key in ("salak", "pandan", "lotu", "karo", "toba"):
            context_pat = rf"\b(?:kab|kabupaten|kota|daerah|wilayah|di)\s+{re.escape(key)}\b"
            if re.search(context_pat, tl):
                return KABKOTA_MAP[key]
            continue

        pat = rf"\b{re.escape(key)}\b"
        if re.search(pat, tl):
            return KABKOTA_MAP[key]

    # Fuzzy match untuk token typo bukan stopword dan panjang >= 5
    words = re.findall(r"\b[a-zA-Z]{5,}\b", tl)
    for word in words:
        if word in STOPWORDS_CITY:
            continue
        candidates = [k for k in KABKOTA_MAP.keys() if len(k) >= 5 and " " not in k] + ["medan"]
        matches = difflib.get_close_matches(word, candidates, n=1, cutoff=0.72)
        if matches:
            return KABKOTA_MAP[matches[0]]

    return None


def is_in_scope_whitelist(
    raw_text: str,
    has_resolved_rs: bool = False,
    is_disambiguate: bool = False,
    is_not_found_rs: bool = False,
    state: dict | None = None,
    history: list[dict] | None = None,
) -> bool:
    """Pemeriksaan whitelist cakupan: hanya lolos jika terbukti berkaitan dengan RS."""
    tl = normalize(raw_text)
    if not tl:
        return True

    # 1. Quick reply resmi bot sendiri
    if tl in KNOWN_QUICK_REPLIES or any(tl == normalize(qr) for qr in KNOWN_QUICK_REPLIES):
        return True
    if any(tl.startswith(qr) for qr in ["bandingkan rs ", "kab. ", "kota "]):
        return True

    # 2. Standalone Apotek terdekat (Kasus tepi R3) -> OUT OF SCOPE
    # Apotek berdiri sendiri bukan topik direktori RS
    if re.search(r"\bapotek\s+terdekat\b", tl) and not any(re.search(p, tl) for p in HOSPITAL_EXPLICIT_ROOTS):
        return False
    if tl in ("apotek", "apotik") and not has_resolved_rs:
        return False

    # 3. Kata/frasa non-RS yang jelas dilarang
    has_hospital_root = any(re.search(p, tl) for p in HOSPITAL_EXPLICIT_ROOTS)
    has_explicit_hospital = has_hospital_root or has_resolved_rs

    for p in NON_HOSPITAL_PATTERNS:
        if re.search(p, tl):
            if not has_explicit_hospital:
                return False

    # 4. Kriteria (a): Cocok nama / alias / akronim RS dari gazetteer
    if has_resolved_rs or is_disambiguate or is_not_found_rs:
        return True

    # 5. Kriteria (f): Darurat medis
    if _matches_any_word_bounded(tl, EMERGENCY_KEYWORDS):
        return True

    # 6. Kriteria (e): Sapaan sopan & FAQ tentang CariSehat
    if _matches_any_word_bounded(tl, GREETING_KEYWORDS) and len(tl.split()) <= 6:
        return True
    if _matches_any_word_bounded(tl, FAQ_KEYWORDS):
        return True

    # 7. Kriteria (d): Kata kunci eksplisit RS/faskes dengan batas kata
    if has_hospital_root:
        return True

    # 8. Kriteria (c): Layanan, spesialisasi, atau keluhan medis yang dikenal (word bounded)
    if _matches_any_word_bounded(tl, LAYANAN_SYNONYMS.keys()):
        return True
    if _matches_any_word_bounded(tl, FASILITAS_SYNONYMS.keys()):
        return True

    # 9. Kriteria (b): Memuat kab/kota Sumut + konteks pencarian RS
    matched_city = match_city(tl)
    if matched_city:
        if any(w in tl for w in ["rs", "rumah sakit", "cari", "faskes", "berobat", "dokter", "rsu", "rsud"]):
            return True
        # Jika menjawab pertanyaan pending=ask_city
        if state and state.get("pending") == "ask_city":
            return True
        if history and len(history) > 0:
            last_bot_msg = next((m.get("text", "") for m in reversed(history) if m.get("role") == "assistant"), "")
            if any(w in last_bot_msg.lower() for w in ["kota", "kabupaten", "wilayah", "mana"]):
                return True

    # 10. Kriteria (g): Follow-up sah berdasarkan state percakapan
    if state and (state.get("filters") or state.get("last_hospital_ids")):
        follow_up_starts = [
            "yang ", "kalau ", "bagaimana ", "berapa ", "ada ", "apakah ",
            "bisa ", "lanjut", "lainnya", "lihat lainnya", "alamatnya", "teleponnya",
            "terima bpjs", "punya icu", "kelas "
        ]
        if any(tl.startswith(c) or f" {c} " in tl for c in follow_up_starts):
            return True
        if re.search(r"\b(?:kelas|kls|tipe)\s*[a-dA-D]\b", tl):
            return True
        if re.search(r"\bbpjs\b", tl):
            return True

    # 11. Pertanyaan terdekat (Nearby)
    if any(re.search(p, tl) for p in NEARBY_KEYWORDS):
        non_med_near = [
            "mobil", "motor", "makan", "restoran", "rumah makan", "hotel", "cafe",
            "kafe", "spbu", "bengkel", "toko", "warung", "wisata", "pantai", "tiket"
        ]
        if not any(re.search(rf"\b{w}\b", tl) for w in non_med_near):
            return True

    # Di luar whitelist -> OUT OF SCOPE
    return False
