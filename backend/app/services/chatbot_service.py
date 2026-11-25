"""Layanan Chatbot Asisten Semantik CariSehat.

100% lokal rule-based menggunakan ontologi RDF & SPARQL tanpa dependensi API eksternal.
Mendukung:
- Resolusi nama toleran typo, singkatan, dan alias
- Whitelist scope classifier
- Format jawaban per intent (DETAIL, ATRIBUT, LIST_FILTER, NEARBY, COMPARE, DISAMBIGUASI, NOT_FOUND, EMERGENCY)
- Penggunaan lokasi GPS browser HANYA untuk pertanyaan kedekatan/jarak
- State percakapan eksplisit multi-turn & paginasi
- Kompatibilitas mundur penuh
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.services import hospital_repo
from app.services import sparql_service as sp
from app.services.chatbot.formatters import (
    format_attribute_rs,
    format_clinic_explain,
    format_compare_table,
    format_detail_rs,
    format_disambiguation,
    format_emergency,
    format_list_filter,
    format_nearby_results,
    format_not_found_hospital,
    format_out_of_scope,
    haversine_distance,
    pick_template,
)
from app.services.chatbot.intents import (
    classify_message_intent,
    extract_search_entities,
)
from app.services.chatbot.models import (
    DATA_NOTE,
    DISCLAIMER,
    DISCLAIMER_EMERGENCY,
    EMERGENCY_KEYWORDS,
    EMPATHY_TRIGGERS,
    FAQ_KEYWORDS,
    FASILITAS_SYNONYMS,
    GREETING_KEYWORDS,
    HOSPITAL_EXPLICIT_ROOTS,
    KABKOTA_MAP,
    LAYANAN_SYNONYMS,
    NEARBY_KEYWORDS,
    OUT_OF_SCOPE_TEXT,
    QR_AFTER_EMPTY,
    QR_AFTER_EMERGENCY,
    QR_AFTER_GREETING,
    QR_AFTER_RESULTS,
    QR_CLARIFICATION,
    QR_OUT_OF_SCOPE,
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

log = logging.getLogger("carisehat.chatbot")


# ---------------------------------------------------------------------------
# Fungsi Pembantu Ekstraksi & Konteks (Kompatibilitas Mundur & Pengujian)
# ---------------------------------------------------------------------------
def _extract_entities(text: str, history: list[dict] | None = None) -> dict:
    """Ekstraksi entitas dari input teks (kompatibel mundur)."""
    return extract_search_entities(text)


def _classify_intent(tl: str, entities: dict, history: list[dict] | None = None) -> str:
    """Klasifikasi intent (kompatibel mundur untuk tests yang menguji modul langsung)."""
    hospitals = hospital_repo.get_all_hospitals()
    classified = classify_message_intent(tl, hospitals, history=history)
    intent = classified["intent"]
    if intent == "ATRIBUT":
        return "DETAIL"
    return intent


def _build_context_filters(history: list[dict] | None, current_entities: dict) -> dict:
    """Gabungkan filter percakapan: nilai TERBARU menimpa nilai lama (perbaiki B9)."""
    ctx_filters: dict = {}
    if history:
        for msg in history:
            if msg.get("role") == "user":
                prev_ent = extract_search_entities(msg.get("text", ""))
                for key in ("kabkota", "kelas", "jenis", "layanan", "bpjs", "fasilitas"):
                    if key in prev_ent:
                        ctx_filters[key] = prev_ent[key]

    for key in ("kabkota", "kelas", "jenis", "layanan", "bpjs", "fasilitas"):
        if key in current_entities:
            ctx_filters[key] = current_entities[key]

    for key in ("is_near", "is_emergency", "compare_pair", "rs_detail_name"):
        if key in current_entities:
            ctx_filters[key] = current_entities[key]

    return ctx_filters


def _is_in_scope(tl: str, entities: dict | None = None, history: list[dict] | None = None) -> bool:
    """Pemeriksaan whitelist cakupan (kompatibel mundur)."""
    hospitals = hospital_repo.get_all_hospitals()
    res = resolve_hospital_name(tl, hospitals)
    has_rs = res["status"] == "dominant"
    is_disam = res["status"] == "disambiguate"
    is_not_found = res["status"] == "not_found"
    return is_in_scope_whitelist(
        tl,
        has_resolved_rs=has_rs,
        is_disambiguate=is_disam,
        is_not_found_rs=is_not_found,
        history=history,
    )


def _enrich_hospitals(
    hospitals: list[dict],
    filters: dict,
    user_loc: tuple[float, float] | None = None,
) -> list[dict]:
    """Menambahkan distance_km jika lokasi pengguna tersedia."""
    enriched = []
    for rs in hospitals:
        rsc = dict(rs)
        if user_loc and rs.get("lat") and rs.get("lon") and "distance_km" not in rsc:
            rsc["distance_km"] = haversine_distance(user_loc[0], user_loc[1], rs["lat"], rs["lon"])
        enriched.append(rsc)
    return enriched


def _format_search_results(hospitals: list[dict], filters: dict, is_near: bool = False) -> str:
    """Format hasil pencarian (kompatibel mundur).
    
    Header 'terdekat' HANYA keluar jika is_near bernilai True (perbaiki bug utama).
    """
    if not hospitals:
        return pick_template("EMPTY")

    if is_near:
        header = "📍 **Berikut rumah sakit terdekat yang siap melayani Anda:**\n"
    else:
        header = f"Berikut {len(hospitals)} rumah sakit yang sesuai dengan kebutuhan Anda:\n"

    lines = [header]
    for i, rs in enumerate(hospitals, 1):
        dist = f" (~{rs['distance_km']} km)" if rs.get("distance_km") is not None else ""
        bpjs_badge = " • ✅ BPJS" if rs.get("bpjs") else ""
        lines.append(f"{i}. **{rs['nama']}**{dist}{bpjs_badge}")
        lines.append(f"   📍 {rs.get('kabkota', '-')} – Kelas {rs.get('kelas', '-')} ({rs.get('jenis', 'Umum')})")
        if rs.get("alamat"):
            lines.append(f"   🏠 {rs['alamat']}")
        if rs.get("telepon"):
            lines.append(f"   📞 {rs['telepon']}")
        if rs.get("layanan"):
            lines.append(f"   🩺 Layanan: {', '.join(rs['layanan'][:3])}")
        lines.append(f"   🔗 [Lihat Detail](/rs/{rs['id']})\n")

    return "\n".join(lines)

def _build_alasan(rs: dict, filters: dict) -> str:
    """Buat penjelasan singkat mengapa RS ini cocok dengan filter pencarian."""
    parts = []
    if filters.get("kelas"):
        parts.append(f"Kelas {filters['kelas']}")
    if filters.get("jenis"):
        parts.append(f"Jenis {filters['jenis']}")
    if filters.get("kabkota"):
        parts.append(f"di {filters['kabkota']}")
    if filters.get("bpjs"):
        parts.append("Menerima BPJS")
    if filters.get("layanan"):
        parts.append(f"Layanan {filters['layanan']}")
    if filters.get("fasilitas"):
        parts.append(f"Fasilitas {filters['fasilitas']}")
    return ", ".join(parts) if parts else f"Kelas {rs.get('kelas', '-')} di {rs.get('kabkota', '-')}"



async def process_chat_message_legacy(
    user_text: str,
    lat: float | None = None,
    lon: float | None = None,
    history: list[dict] | None = None,
    state: dict | None = None,
    location_status: str | None = None,
    seed: int | None = None,
) -> dict:
    """Proses input pesan pengguna secara 100% lokal berbasis rule-based & RDF.
    
    Mengembalikan dict:
    - text: str
    - is_emergency: bool
    - quick_replies: list[str]
    - hospitals: list[dict]
    - data_note: str
    - state: dict
    """
    # 1. Validasi input awal
    if not isinstance(user_text, str):
        return {
            "text": "Pesan harus berupa teks.",
            "is_emergency": False,
            "quick_replies": QR_AFTER_GREETING,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": state or {},
        }

    text = user_text.strip()
    history = history or []

    # Validasi koordinat GPS
    if lat is not None and not (-90.0 <= lat <= 90.0):
        lat = None
    if lon is not None and not (-180.0 <= lon <= 180.0):
        lon = None
    user_loc: tuple[float, float] | None = (lat, lon) if lat is not None and lon is not None else None

    # Pesan kosong -> Sambutan
    if not text:
        greet_text = pick_template("GREETING", seed=seed)
        return {
            "text": greet_text + DISCLAIMER,
            "is_emergency": False,
            "quick_replies": QR_AFTER_GREETING,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": state or {},
        }

    tl = normalize(text)

    # Muat seluruh data rumah sakit dari repositori
    all_hospitals = hospital_repo.get_all_hospitals()
    if not all_hospitals:
        # Fuseki dan rdflib fallback sama-sama gagal
        return {
            "text": "Mohon maaf, server pangkalan data rumah sakit kami sedang mengalami kendala koneksi saat ini. Silakan coba kembali beberapa saat lagi ya 🙏" + DISCLAIMER,
            "is_emergency": False,
            "quick_replies": QR_AFTER_EMPTY,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": state or {},
        }

    # Inisialisasi state percakapan
    curr_state = {
        "pending": state.get("pending") if state else None,
        "filters": dict(state.get("filters", {})) if state else {},
        "last_hospital_ids": list(state.get("last_hospital_ids", [])) if state else [],
        "offset": state.get("offset", 0) if state else 0,
        "last_intent": state.get("last_intent") if state else None,
    }

    # Cek apakah query saat ini adalah paginasi
    is_pagination = tl in ("lihat lainnya", "lainnya", "selanjutnya", "berikutnya", "rs lainnya")

    # Klasifikasi intent
    classified = classify_message_intent(text, all_hospitals, state=curr_state, history=history)
    intent = classified["intent"]
    search_ent = classified["entities"]
    res_hospital = classified["res_hospital"]

    # Deteksi empati (hanya jika pengguna mengeluhkan kondisi sakit)
    empathy = ""
    if any(re.search(rf"\b{kw}\b", tl) for kw in EMPATHY_TRIGGERS) and intent != "EMERGENCY":
        empathy = "Semoga lekas pulih dan sehat kembali. "

    previous_bot_text = ""
    if history:
        for m in reversed(history):
            if m.get("role") == "assistant":
                previous_bot_text = m.get("text", "")
                break

    # =======================================================================
    # INTENT: OUT_OF_SCOPE (T2)
    # =======================================================================
    if intent == "OUT_OF_SCOPE":
        res = format_out_of_scope()
        curr_state["last_intent"] = "OUT_OF_SCOPE"
        res["state"] = curr_state
        return res

    # =======================================================================
    # INTENT: EMERGENCY
    # =======================================================================
    if intent == "EMERGENCY":
        # Ambil RS dengan UGD 24 Jam
        emergency_rs = hospital_repo.filter_in_memory(is_emergency=True)
        if user_loc:
            # Urutkan jarak hanya untuk RS dengan koordinat andal
            with_dist = []
            for rs in emergency_rs:
                rsc = dict(rs)
                if rs.get("lat") and rs.get("lon") and rs.get("sumber_koordinat") in ("osm", "jalan", "nama"):
                    rsc["distance_km"] = haversine_distance(user_loc[0], user_loc[1], rs["lat"], rs["lon"])
                    with_dist.append(rsc)
            with_dist.sort(key=lambda x: x["distance_km"])
            if with_dist:
                emergency_rs = with_dist

        res = format_emergency(emergency_rs)
        curr_state["last_intent"] = "EMERGENCY"
        res["state"] = curr_state
        return res

    # =======================================================================
    # INTENT: CLINIC_EXPLAIN (Kasus tepi)
    # =======================================================================
    if intent == "CLINIC_EXPLAIN":
        res = format_clinic_explain()
        curr_state["last_intent"] = "CLINIC_EXPLAIN"
        res["state"] = curr_state
        return res

    # =======================================================================
    # INTENT: GREETING
    # =======================================================================
    if intent == "GREETING":
        greet_body = pick_template("GREETING", previous_bot_text, seed=seed) + DISCLAIMER
        curr_state["last_intent"] = "GREETING"
        return {
            "text": greet_body,
            "is_emergency": False,
            "quick_replies": QR_AFTER_GREETING,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": curr_state,
        }

    # =======================================================================
    # INTENT: FAQ
    # =======================================================================
    if intent == "FAQ":
        faq_text = (
            "**CariSehat** adalah direktori rumah sakit se-Sumatera Utara berbasis Web Semantik (RDF & SPARQL).\n\n"
            "✨ **Fitur yang dapat Anda gunakan:**\n"
            "- 🔍 **Pencarian Cerdas**: Cari RS berdasarkan kota, kelas (A/B/C/D), jenis (Umum/Khusus), dan BPJS.\n"
            "- 🩺 **Spesialisasi Medis**: Cari RS berdasarkan layanan poli (Bedah, Anak, Mata, Gigi, Jiwa, dll).\n"
            "- 📍 **Deteksi RS Terdekat**: Temukan rumah sakit terdekat langsung dari koordinat GPS Anda.\n"
            "- ⚖️ **Bandingkan RS**: Bandingkan fasilitas dan kelas dua rumah sakit sekaligus.\n"
            "- 🆘 **Mode Darurat**: Akses cepat ke UGD 24 Jam dan hotline gawat darurat nasional (119/112).\n\n"
            "Data bersumber resmi dari Permenkes No. 3/2020 dan OpenStreetMap."
        )
        curr_state["last_intent"] = "FAQ"
        return {
            "text": faq_text + DISCLAIMER,
            "is_emergency": False,
            "quick_replies": QR_AFTER_GREETING,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": curr_state,
        }

    # =======================================================================
    # INTENT: DISAMBIGUASI (Nama RS kembar / sama kuat)
    # =======================================================================
    if intent == "DISAMBIGUASI":
        candidates = res_hospital.get("candidates", [])
        cleaned_name = res_hospital.get("cleaned_name", text)
        res = format_disambiguation(candidates, cleaned_name)
        curr_state["pending"] = "disambiguate"
        curr_state["last_intent"] = "DISAMBIGUASI"
        res["state"] = curr_state
        return res

    # =======================================================================
    # INTENT: RATING_INQUIRY (Keterbatasan data: tidak ada rating/ulasan)
    # =======================================================================
    if intent == "RATING_INQUIRY":
        rating_text = (
            "Saat ini, database CariSehat belum memuat data penilaian/rating bintang "
            "atau ulasan pengguna untuk rumah sakit.\n\n"
            "Sebagai gantinya, Anda dapat mempertimbangkan:\n"
            "- **Kelas A & B** sebagai indikator kualitas pelayanan terstandarisasi\n"
            "- **Kelengkapan Fasilitas** seperti ICU, Ambulans, dan Kamar Operasi\n"
            "- **Status BPJS** dan kelengkapan layanan medis\n\n"
            "Data kami bersumber dari Permenkes No. 3/2020 dan tidak memuat rating subjektif."
        )
        curr_state["last_intent"] = "RATING_INQUIRY"
        return {
            "text": rating_text + DISCLAIMER,
            "is_emergency": False,
            "quick_replies": QR_AFTER_RESULTS,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": curr_state,
        }

    # =======================================================================
    # INTENT: JAM_BUKA_INQUIRY (Keterbatasan data: jam operasional tidak ada di RDF)
    # =======================================================================
    if intent == "JAM_BUKA_INQUIRY":
        jam_text = (
            "Informasi IGD 24 Jam dan Poliklinik berbeda untuk setiap rumah sakit. "
            "Sebutkan nama rumah sakit untuk melihat jadwal yang tercatat, "
            "atau buka bagian Jam Operasional pada profilnya. "
            "Jam yang belum ada datanya ditampilkan sebagai Belum tersedia."
        )
        curr_state["last_intent"] = "JAM_BUKA_INQUIRY"
        return {
            "text": jam_text + DISCLAIMER,
            "is_emergency": False,
            "quick_replies": QR_AFTER_RESULTS,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": curr_state,
        }

    # =======================================================================
    # INTENT: NOT_FOUND (Topik RS tidak ditemukan di data)
    # =======================================================================
    if intent == "NOT_FOUND":
        cleaned_name = res_hospital.get("cleaned_name", text)
        suggestions = res_hospital.get("suggestions", [])
        res = format_not_found_hospital(cleaned_name, suggestions)
        curr_state["last_intent"] = "NOT_FOUND"
        res["state"] = curr_state
        return res

    # =======================================================================
    # INTENT: DETAIL (Profil lengkap 1 RS)
    # =======================================================================
    if intent == "DETAIL":
        target_rs = res_hospital["target_rs"]
        res = format_detail_rs(target_rs, user_loc, empathy)
        curr_state["last_hospital_ids"] = [target_rs["id"]]
        curr_state["last_intent"] = "DETAIL"
        curr_state["pending"] = None
        res["state"] = curr_state
        return res

    # =======================================================================
    # INTENT: ATRIBUT (Jawaban ringkas atribut spesifik 1 RS)
    # =======================================================================
    if intent == "ATRIBUT":
        target_rs = res_hospital["target_rs"]
        attr = search_ent.get("attribute") or res_hospital.get("attribute") or "info"
        res = format_attribute_rs(target_rs, attr, empathy, user_loc=user_loc)
        curr_state["last_hospital_ids"] = [target_rs["id"]]
        curr_state["last_intent"] = "ATRIBUT"
        curr_state["pending"] = None
        res["state"] = curr_state
        return res

    # =======================================================================
    # INTENT: COMPARE (Perbandingan dua RS)
    # =======================================================================
    if intent == "COMPARE":
        pair = search_ent.get("compare_pair", [])
        use_last = search_ent.get("use_last_rs", False)

        rs_a = None
        rs_b = None

        if use_last and curr_state.get("last_hospital_ids"):
            rs_a = hospital_repo.get_hospital_by_id(curr_state["last_hospital_ids"][0])
            cand_b = resolve_hospital_name(pair[0], all_hospitals)
            rs_b = cand_b.get("target_rs")
        elif len(pair) >= 2:
            cand_a = resolve_hospital_name(pair[0], all_hospitals)
            cand_b = resolve_hospital_name(pair[1], all_hospitals)
            rs_a = cand_a.get("target_rs")
            rs_b = cand_b.get("target_rs")

        if rs_a and rs_b:
            res = format_compare_table(rs_a, rs_b)
            curr_state["last_hospital_ids"] = [rs_a["id"], rs_b["id"]]
            curr_state["last_intent"] = "COMPARE"
            res["state"] = curr_state
            return res
        else:
            missing = []
            if not rs_a:
                missing.append(pair[0] if pair else "RS pertama")
            if not rs_b:
                missing.append(pair[1] if len(pair) > 1 else "RS kedua")
            miss_text = " dan ".join(missing)
            body = f"Mohon maaf, data untuk **{miss_text}** belum dapat ditemukan di database kami untuk dibandingkan." + DISCLAIMER
            return {
                "text": body,
                "is_emergency": False,
                "quick_replies": QR_AFTER_EMPTY,
                "hospitals": [],
                "data_note": DATA_NOTE,
                "state": curr_state,
            }

    # =======================================================================
    # INTENT: SEARCH_NEARBY (Pencarian berjarak)
    # =======================================================================
    if intent == "SEARCH_NEARBY":
        # Saring filter pendamping jika ada (misal: "ICU terdekat", "RS kelas B terdekat")
        kw_filter = {}
        for k in ("kelas", "jenis", "kabkota", "layanan", "bpjs", "fasilitas"):
            if k in search_ent:
                kw_filter[k] = search_ent[k]

        filtered = hospital_repo.filter_in_memory(**kw_filter)

        # Hitung jarak HANYA untuk RS dengan koordinat andal
        with_distance = []
        if user_loc:
            for rs in filtered:
                sumber = rs.get("sumber_koordinat")
                if rs.get("lat") and rs.get("lon") and sumber in ("osm", "jalan", "nama"):
                    rsc = dict(rs)
                    rsc["distance_km"] = haversine_distance(user_loc[0], user_loc[1], rs["lat"], rs["lon"])
                    with_distance.append(rsc)

            with_distance.sort(key=lambda x: x["distance_km"])

        top_nearby = with_distance[:5]
        res = format_nearby_results(
            top_nearby,
            len(with_distance),
            user_loc,
            location_status=location_status,
            previous_text=previous_bot_text,
            empathy=empathy,
            seed=seed,
        )
        curr_state["last_intent"] = "SEARCH_NEARBY"
        curr_state["pending"] = "ask_city" if not user_loc else None
        curr_state["filters"] = kw_filter
        res["state"] = curr_state
        return res

    # =======================================================================
    # INTENT: CLARIFICATION_ANSWER / SEARCH_FILTER
    # =======================================================================
    # Update filters in state (Pewarisan konteks multi-turn, nilai terbaru menimpa nilai lama)
    if is_pagination:
        filters = dict(curr_state.get("filters", {}))
        offset = curr_state.get("offset", 0) + 5
    elif intent == "CLARIFICATION_ANSWER":
        filters = dict(curr_state.get("filters", {}))
        if "kabkota" in search_ent:
            filters["kabkota"] = search_ent["kabkota"]
        offset = 0
        curr_state["pending"] = None
    elif any(tl.startswith(c) for c in ["yang ", "kalau ", "ada ", "apakah ", "bisa ", "kelas ", "lihat rs kelas "]):
        # Follow-up bertahap: gabungkan konteks dari history + current
        # (nilai terbaru menimpa nilai lama — B9 fix)
        filters = dict(curr_state.get("filters", {}))
        filters.update(_build_context_filters(history if not filters else [], search_ent))
        # Hanya ambil field filter sah
        filters = {k: v for k, v in filters.items() if k in ("kelas", "jenis", "kabkota", "layanan", "bpjs", "fasilitas")}
        offset = 0
    else:
        # Pencarian filter baru mandiri (reset filter lama)
        filters = {}
        for k in ("kelas", "jenis", "kabkota", "layanan", "bpjs", "fasilitas"):
            if k in search_ent:
                filters[k] = search_ent[k]
        offset = 0

    # KLARIFIKASI: Jika sama sekali tidak ada filter, tanyakan ke pengguna
    if not filters and not is_pagination:
        klarifikasi_text = (
            "Tentu, saya siap membantu menemukan rumah sakit yang sesuai! 🏥\n\n"
            "Agar pencarian lebih akurat, bisakah Anda menyebutkan:\n"
            "- **Wilayah/kota** yang diinginkan? (mis: Kota Medan, Kab. Deli Serdang)\n"
            "- **Kelas RS** (A/B/C/D) atau jenis layanan tertentu?\n"
            "- Atau gunakan opsi cepat di bawah ini:"
        )
        curr_state["pending"] = "ask_city"
        curr_state["last_intent"] = "KLARIFIKASI"
        return {
            "text": klarifikasi_text + DISCLAIMER,
            "is_emergency": False,
            "quick_replies": QR_CLARIFICATION,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": curr_state,
        }

    # Eksekusi search melalui sp.search_hospitals (agar testable via mock)
    try:
        raw_results = await hospital_repo.search_hospitals(
            kelas=filters.get("kelas", ""),
            jenis=filters.get("jenis", ""),
            kabkota=filters.get("kabkota", ""),
            layanan=filters.get("layanan", ""),
            bpjs=filters.get("bpjs"),
            fasilitas=filters.get("fasilitas", ""),
            limit=500,
            offset=0,
        )
        if raw_results is None:
            raise ValueError("sp.search_hospitals returned None")
        matched_hospitals = raw_results
    except Exception as e:
        log.error("SEARCH_FILTER sp.search_hospitals gagal: %s", e)
        return {
            "text": (
                "Mohon maaf, server pangkalan data rumah sakit kami sedang mengalami "
                "kendala koneksi saat ini. Silakan coba kembali beberapa saat lagi."
                + DISCLAIMER
            ),
            "is_emergency": False,
            "quick_replies": QR_AFTER_EMPTY,
            "hospitals": [],
            "data_note": DATA_NOTE,
            "state": curr_state,
        }

    total_found = len(matched_hospitals)
    sliced_hospitals = matched_hospitals[offset: offset + 5]

    # Tambahkan field 'alasan' ke setiap RS dalam hasil
    for rs in sliced_hospitals:
        if "alasan" not in rs:
            rs["alasan"] = _build_alasan(rs, filters)

    res = format_list_filter(
        sliced_hospitals,
        total_found,
        filters,
        offset=offset,
        previous_text=previous_bot_text,
        empathy=empathy,
        seed=seed,
    )

    # Catatan keterbatasan data jika mencari jantung/kardiologi (B12)
    if search_ent.get("is_cardio_inquiry") and sliced_hospitals:
        cardio_note = (
            "\n\n💡 *Catatan:* Direktori data perizinan Permenkes No. 3/2020 belum memuat layanan spesialis Jantung/Kardiologi "
            "secara terpisah. Ditampilkan rumah sakit dengan layanan **Penyakit Dalam** yang relevan."
        )
        res["text"] = res["text"].replace(DISCLAIMER, cardio_note + DISCLAIMER)

    curr_state["filters"] = filters
    curr_state["offset"] = offset
    curr_state["last_hospital_ids"] = [h["id"] for h in sliced_hospitals]
    curr_state["last_intent"] = "SEARCH_FILTER"
    res["state"] = curr_state

    return res


# Public entry point retained for API callers and existing integrations.
from app.services.chatbot.engine import process as process_chat_message
