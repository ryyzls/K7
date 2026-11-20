"""Modul Klasifikasi Intent & Ekstraksi Entitas Chatbot CariSehat."""
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
from app.services.chatbot.resolver import (
    clean_hospital_query,
    extract_attribute,
    extract_compare_pair,
    resolve_hospital_name,
)
from app.services.chatbot.scope import (
    _matches_any_word_bounded,
    is_in_scope_whitelist,
    match_city,
)
from app.services.fuzzy_search import normalize


def extract_search_entities(text: str) -> dict:
    """Ekstraksi filter pencarian umum (kelas, jenis, bpjs, kabkota, layanan, fasilitas, is_near)."""
    result: dict = {}
    tl = text.lower()

    # Kelas RS (A, B, C, D)
    m_kelas = re.search(r"\b(?:kelas|kls|tipe)\s*([a-dA-D])\b", tl)
    if m_kelas:
        result["kelas"] = m_kelas.group(1).upper()

    # Jenis RS (Umum, Khusus)
    if re.search(r"\b(?:khusus|rsia|rsk|ibu dan anak|jiwa|mata|paru)\b", tl):
        result["jenis"] = "Khusus"
    elif re.search(r"\b(?:umum|rsu|rsud|rsup)\b", tl):
        result["jenis"] = "Umum"

    # BPJS
    if re.search(r"\b(tanpa bpjs|non bpjs|bukan bpjs|tidak terima bpjs)\b", tl):
        result["bpjs"] = False
    elif re.search(r"\b(bpjs|askes|kis|kartu indonesia sehat|jaminan kesehatan)\b", tl):
        result["bpjs"] = True

    # Kab/Kota
    city = match_city(tl)
    if city:
        result["kabkota"] = city

    # Layanan (Longest match first)
    sorted_lay = sorted(LAYANAN_SYNONYMS.keys(), key=len, reverse=True)
    for kw in sorted_lay:
        pat = rf"\b{re.escape(kw)}\b"
        if re.search(pat, tl):
            result["layanan"] = LAYANAN_SYNONYMS[kw]
            if kw in ("jantung", "kardiologi", "nyeri dada", "angina"):
                result["is_cardio_inquiry"] = True
            break

    # Fasilitas (Longest match first)
    sorted_fas = sorted(FASILITAS_SYNONYMS.keys(), key=len, reverse=True)
    for kw in sorted_fas:
        pat = rf"\b{re.escape(kw)}\b"
        if re.search(pat, tl):
            result["fasilitas"] = FASILITAS_SYNONYMS[kw]
            break

    # Nearby indicator (HANYA turn saat ini)
    if any(re.search(p, tl) for p in NEARBY_KEYWORDS):
        non_med_near = [
            "mobil", "motor", "makan", "restoran", "rumah makan", "hotel", "cafe",
            "kafe", "spbu", "bengkel", "toko", "warung", "wisata", "pantai", "tiket"
        ]
        if not any(re.search(rf"\b{w}\b", tl) for w in non_med_near):
            result["is_near"] = True

    return result


def classify_message_intent(
    raw_text: str,
    hospitals: list[dict],
    state: dict | None = None,
    history: list[dict] | None = None,
) -> dict:
    """Klasifikasi intent utama pengguna dengan resolusi entitas lengkap."""
    text = raw_text.strip()
    tl = normalize(text)

    # 1. Ekstraksi filter umum (is_near, kelas, jenis, kabkota, layanan, fasilitas)
    search_ent = extract_search_entities(raw_text)

    # 2. Resolusi nama RS kandidat dari teks
    res_hospital = resolve_hospital_name(text, hospitals)
    has_resolved_rs = res_hospital["status"] == "dominant"
    is_disambiguate = res_hospital["status"] == "disambiguate"
    is_not_found_rs = res_hospital["status"] == "not_found"

    # 3. Cek apakah pesan masuk ke dalam cakupan whitelist
    in_scope = is_in_scope_whitelist(
        text,
        has_resolved_rs=has_resolved_rs,
        is_disambiguate=is_disambiguate,
        is_not_found_rs=is_not_found_rs,
        state=state,
        history=history,
    )
    if not in_scope:
        return {
            "intent": "OUT_OF_SCOPE",
            "res_hospital": res_hospital,
            "entities": {},
        }

    # 4. Darurat Medis (EMERGENCY)
    if _matches_any_word_bounded(tl, EMERGENCY_KEYWORDS):
        return {
            "intent": "EMERGENCY",
            "res_hospital": res_hospital,
            "entities": {"is_emergency": True},
        }

    # 5. Kasus Tepi: Penjelasan Klinik / Puskesmas
    if re.search(r"\b(klinik|puskesmas|posyandu|dokter\s+praktik)\b", tl) and not has_resolved_rs:
        if not any(re.search(p, tl) for p in [r"\brs\b", r"\brumah\s*sakit\b", r"\brsud\b"]):
            return {
                "intent": "CLINIC_EXPLAIN",
                "res_hospital": res_hospital,
                "entities": {},
            }

    # 6. Pertanyaan Terdekat (NEARBY) - Prioritas sebelum not_found nama
    if search_ent.get("is_near") and not has_resolved_rs:
        return {
            "intent": "SEARCH_NEARBY",
            "res_hospital": res_hospital,
            "entities": search_ent,
        }

    # 7. Sapaan (GREETING)
    if _matches_any_word_bounded(tl, GREETING_KEYWORDS) and len(tl.split()) <= 6:
        if not any(k in tl for k in ["cari", "rs", "rumah sakit", "kelas", "bpjs", "dekat"]):
            return {
                "intent": "GREETING",
                "res_hospital": res_hospital,
                "entities": {},
            }

    # 8. FAQ
    if _matches_any_word_bounded(tl, FAQ_KEYWORDS):
        return {
            "intent": "FAQ",
            "res_hospital": res_hospital,
            "entities": {},
        }

    # 9. Compare dua RS
    compare_pair = extract_compare_pair(tl)
    if len(compare_pair) >= 2:
        return {
            "intent": "COMPARE",
            "res_hospital": res_hospital,
            "entities": {"compare_pair": compare_pair},
        }
    if len(compare_pair) == 1 and state and state.get("last_hospital_ids"):
        # Misal: "bandingkan dengan pirngadi"
        return {
            "intent": "COMPARE",
            "res_hospital": res_hospital,
            "entities": {"compare_pair": [compare_pair[0]], "use_last_rs": True},
        }

    # 10b. Rating / Ulasan Inquiry (keterbatasan data — harus sebelum NOT_FOUND)
    if re.search(r"\b(rating|ulasan|review|bintang|penilaian|rekomendasi\s+terbaik|nilai\s+rs)\b", tl):
        return {
            "intent": "RATING_INQUIRY",
            "res_hospital": res_hospital,
            "entities": {},
        }

    # 10c. Jam Buka Inquiry (keterbatasan data — harus sebelum NOT_FOUND)
    if re.search(r"\bjam\s+buka\b|\bjam\s+operasional\b|\bbuka\s+jam\b|\bwaktu\s+operasional\b", tl):
        return {
            "intent": "ATRIBUT" if has_resolved_rs else "JAM_BUKA_INQUIRY",
            "res_hospital": res_hospital,
            "entities": {"attribute": "jam_buka"},
        }

    if is_disambiguate:
        return {"intent": "DISAMBIGUASI", "res_hospital": res_hospital, "entities": {}}

    # 11. Nama RS tidak ditemukan
    if is_not_found_rs:
        return {
            "intent": "NOT_FOUND",
            "res_hospital": res_hospital,
            "entities": {},
        }

    # 12. Detail RS atau Atribut RS Spesifik
    if has_resolved_rs and res_hospital["target_rs"]:
        if res_hospital["attribute"]:
            return {
                "intent": "ATRIBUT",
                "res_hospital": res_hospital,
                "entities": {"attribute": res_hospital["attribute"]},
            }
        return {
            "intent": "DETAIL",
            "res_hospital": res_hospital,
            "entities": {},
        }

    # 12b. Follow-up pertanyaan atribut RS terakhir dari state percakapan
    attr_only = extract_attribute(raw_text)
    if attr_only and state and state.get("last_intent") in ("DETAIL", "ATRIBUT") and state.get("last_hospital_ids"):
        last_id = state["last_hospital_ids"][0]
        last_rs = next((h for h in hospitals if h["id"] == last_id), None)
        if last_rs:
            return {
                "intent": "ATRIBUT",
                "res_hospital": {
                    "status": "dominant",
                    "target_rs": last_rs,
                    "candidates": [last_rs],
                    "suggestions": [],
                    "attribute": attr_only,
                    "cleaned_name": last_rs["nama"],
                },
                "entities": {"attribute": attr_only},
            }

    # 13. Jawaban Klarifikasi Wilayah (CLARIFICATION_ANSWER)
    if state and state.get("pending") == "ask_city":
        city = match_city(tl)
        if city:
            search_ent["kabkota"] = city
            return {
                "intent": "CLARIFICATION_ANSWER",
                "res_hospital": res_hospital,
                "entities": search_ent,
            }

    # 14. General Search / Filter
    return {
        "intent": "SEARCH_FILTER",
        "res_hospital": res_hospital,
        "entities": search_ent,
    }
