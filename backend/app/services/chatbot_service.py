"""Layanan Chatbot Asisten Semantik CariSehat.
Menerjemahkan bahasa alami pengguna ke query SPARQL pada Apache Jena Fuseki.
Jika GEMINI_API_KEY tersedia, menggunakan Google Gemini sebagai AI backend.
"""
import re
import json
import logging

import httpx

from app.config import settings
from app.services import sparql_service as sp
from app.services import dbpedia_service as dbp

log = logging.getLogger("carisehat.chatbot")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

# Konteks sistem untuk Gemini — memahami domain CariSehat
SYSTEM_INSTRUCTION = """Kamu adalah Asisten CariSehat, helpdesk virtual yang membantu pengguna \
menemukan informasi rumah sakit di Sumatera Utara. Kamu berbicara dalam Bahasa Indonesia \
yang ramah, ringkas, dan informatif.

Kamu memiliki akses ke database semantik (RDF/SPARQL) berisi ratusan rumah sakit di \
Sumatera Utara, mencakup: nama, kelas (A/B/C/D), jenis (Umum/Khusus), alamat, \
kabupaten/kota, nomor telepon, website, layanan, dan fasilitas.

Ketika pengguna menanyakan rumah sakit, ekstrak informasi kunci dari pertanyaannya \
(kelas, kota, jenis, layanan) dan sampaikan hasilnya dengan format yang mudah dibaca. \
Gunakan emoji secukupnya untuk mempercantik tampilan (📍 🏥 📞 🩺 ⭐).

Jika konteks hasil database disertakan, rangkum dan presentasikan dengan baik.
Jika tidak ada hasil database, berikan saran pencarian alternatif.
Selalu akhiri respons dengan ajakan untuk berinteraksi lebih lanjut.
"""


async def _call_gemini(user_text: str, db_context: str = "") -> str | None:
    """Panggil Google Gemini API untuk menghasilkan respons AI."""
    if not settings.gemini_api_key or settings.gemini_api_key.startswith("ISI_"):
        return None

    # Susun prompt lengkap dengan konteks database
    prompt_parts = [user_text]
    if db_context:
        prompt_parts = [
            f"Pertanyaan pengguna: {user_text}\n\n"
            f"Data dari database semantik CariSehat:\n{db_context}\n\n"
            "Berdasarkan data di atas, berikan jawaban yang informatif dan ramah."
        ]

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"parts": [{"text": "\n".join(prompt_parts)}], "role": "user"}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
            "topP": 0.9,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                GEMINI_API_URL,
                params={"key": settings.gemini_api_key},
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
    except httpx.HTTPStatusError as e:
        log.error("Gemini API HTTP error: %s – %s", e.response.status_code, e.response.text[:200])
    except Exception as e:
        log.error("Gemini API error: %s", e)
    return None


def _extract_entities(text: str) -> dict:
    """Ekstrak entitas (kelas, jenis, kabkota, layanan) dari teks bebas."""
    result: dict = {}

    # Kelas RS
    if re.search(r"\bkelas\s*a\b", text):
        result["kelas"] = "A"
    elif re.search(r"\bkelas\s*b\b", text):
        result["kelas"] = "B"
    elif re.search(r"\bkelas\s*c\b", text):
        result["kelas"] = "C"
    elif re.search(r"\bkelas\s*d\b", text):
        result["kelas"] = "D"

    # Jenis RS
    if "umum" in text or " rsu " in text:
        result["jenis"] = "Umum"
    elif any(k in text for k in ["khusus", "rsk", "jiwa", "mata", "bedah", "ibu dan anak", "rsia"]):
        result["jenis"] = "Khusus"

    # Kabupaten/Kota Sumut
    daftar_kota = {
        "medan": "Kota Medan",
        "binjai": "Kota Binjai",
        "pematangsiantar": "Kota Pematangsiantar",
        "siantar": "Kota Pematangsiantar",
        "tebing tinggi": "Kota Tebing Tinggi",
        "tanjungbalai": "Kota Tanjungbalai",
        "sibolga": "Kota Sibolga",
        "padangsidimpuan": "Kota Padangsidimpuan",
        "gunungsitoli": "Kota Gunungsitoli",
        "deli serdang": "Kab. Deli Serdang",
        "karo": "Kab. Karo",
        "kabanjahe": "Kab. Karo",
        "toba": "Kab. Toba",
        "samosir": "Kab. Samosir",
        "simalungun": "Kab. Simalungun",
        "asahan": "Kab. Asahan",
        "tapanuli utara": "Kab. Tapanuli Utara",
        "tarutung": "Kab. Tapanuli Utara",
        "langkat": "Kab. Langkat",
        "nias": "Kab. Nias",
        "batubara": "Kab. Batu Bara",
        "mandailing natal": "Kab. Mandailing Natal",
        "labuhanbatu": "Kab. Labuhanbatu",
    }
    for k, v in daftar_kota.items():
        if k in text:
            result["kabkota"] = v
            break

    # Layanan spesifik
    for layanan in ["Anak", "Bersalin", "Bedah", "Ginjal", "Gigi dan Mulut", "Jiwa", "Mata", "Paru"]:
        if layanan.lower() in text:
            result["layanan"] = layanan
            break

    # Nama RS jika disebutkan eksplisit
    name_match = re.search(r"(?:rs|rumah sakit)\s+([a-zA-Z\s]+)", text)
    if name_match:
        extracted = name_match.group(1).strip()
        skip_words = {
            "kelas a", "kelas b", "kelas c", "kelas d",
            "umum", "khusus", "jiwa", "mata", "di medan",
            "di binjai", "terdekat", "bagus", "terbaik",
        }
        if extracted not in skip_words:
            result["q"] = extracted[:30]

    return result


def _format_db_results(results: list[dict], kriteria: dict) -> str:
    """Format hasil database menjadi teks konteks untuk Gemini."""
    if not results:
        return ""
    lines = [f"Ditemukan {len(results)} rumah sakit:\n"]
    for i, rs in enumerate(results, 1):
        line = f"{i}. {rs['nama']} (Kelas {rs['kelas']} – {rs['jenis']})\n"
        line += f"   Lokasi: {rs['kabkota']}, {rs['alamat']}\n"
        if rs.get("telepon"):
            line += f"   Telepon: {rs['telepon']}\n"
        if rs.get("layanan"):
            line += f"   Layanan: {', '.join(rs['layanan'][:5])}\n"
        lines.append(line)
    return "\n".join(lines)


def _format_fallback(results: list[dict], kriteria: dict) -> str:
    """Format jawaban rule-based (fallback tanpa Gemini)."""
    if not results:
        return (
            "Maaf, saya tidak menemukan rumah sakit yang sesuai kriteria tersebut di database kami.\n"
            "Coba tanyakan dengan kriteria lain, misalnya: *'Rumah sakit kelas B di Medan'* atau *'RS Khusus di Sumut'*."
        )

    desc_parts = []
    if kriteria.get("kelas"):
        desc_parts.append(f"Kelas {kriteria['kelas']}")
    if kriteria.get("jenis"):
        desc_parts.append(f"Jenis {kriteria['jenis']}")
    if kriteria.get("kabkota"):
        desc_parts.append(f"di {kriteria['kabkota']}")
    if kriteria.get("layanan"):
        desc_parts.append(f"layanan {kriteria['layanan']}")

    label = " (" + ", ".join(desc_parts) + ")" if desc_parts else ""
    jawaban = [f"Ditemukan beberapa rumah sakit yang sesuai{label}:\n"]

    for i, rs in enumerate(results, 1):
        info_line = f"{i}. **{rs['nama']}** (Kelas {rs['kelas']} - {rs['jenis']})\n"
        info_line += f"   📍 *{rs['kabkota']}*, {rs['alamat']}\n"
        if rs.get("telepon"):
            info_line += f"   📞 Telp: {rs['telepon']}\n"
        if rs.get("layanan"):
            info_line += f"   🩺 Layanan: {', '.join(rs['layanan'])}\n"
        jawaban.append(info_line)

    jawaban.append("💡 *Klik pada daftar atau penanda peta untuk melihat rute dan data RDF lengkapnya.*")
    return "\n".join(jawaban)


async def process_chat_message(user_text: str) -> str:
    """Proses teks masukan pengguna dan menghasilkan jawaban berbasis AI + data semantik."""
    text = (user_text or "").strip().lower()
    if not text:
        return "Halo! Ada yang bisa saya bantu terkait informasi rumah sakit di Sumatera Utara?"

    # 1. Sapaan / Greeting
    if any(greet in text for greet in ["halo", "hai", "selamat", "pagi", "siang", "sore", "malam", "assalamualaikum"]):
        greeting_reply = (
            "Halo! Saya asisten virtual **CariSehat** berbasis Web Semantik + AI.\n\n"
            "Anda bisa menanyakan informasi seperti:\n"
            "- *\"RS kelas A di Medan\"*\n"
            "- *\"Cari rumah sakit jiwa atau rumah sakit mata\"*\n"
            "- *\"Daftar rumah sakit di Deli Serdang\"*\n"
            "- *\"Informasi kota Medan dari DBpedia\"*\n\n"
            "Ada yang bisa saya bantu?"
        )
        # Coba lewatkan ke Gemini untuk sapaan lebih natural
        ai_reply = await _call_gemini(user_text)
        return ai_reply if ai_reply else greeting_reply

    # 2. Pertanyaan khusus DBpedia (External Linked Data)
    if "dbpedia" in text or "tentang kota" in text or "profil kota" in text:
        m = re.search(
            r"(medan|binjai|pematangsiantar|tebing tinggi|karo|deli serdang|simalungun|sibolga|nias)", text
        )
        city = m.group(1) if m else "medan"
        info = await dbp.get_dbpedia_info(city)
        if info.get("abstract"):
            abs_text = info["abstract"][:400] + "..." if len(info["abstract"]) > 400 else info["abstract"]
            db_ctx = f"Data DBpedia untuk {city}:\n{abs_text}"
            if info.get("population"):
                db_ctx += f"\nPopulasi: {int(float(info['population'])):,} jiwa"
            ai_reply = await _call_gemini(user_text, db_ctx)
            if ai_reply:
                return ai_reply
            # Fallback
            res = f"🌐 **Data Eksternal DBpedia ({info.get('dbpedia_resource')}):**\n\n{abs_text}"
            if info.get("population"):
                res += f"\n\n👥 Populasi tercatat: {int(float(info['population'])):,} jiwa"
            return res
        return f"Belum berhasil memuat data eksternal DBpedia untuk wilayah {city}."

    # 3. Pertanyaan umum yang tidak perlu database (FAQ)
    faq_keywords = ["apa itu", "bagaimana cara", "cara pakai", "fitur apa", "bisa apa", "tentang aplikasi"]
    if any(kw in text for kw in faq_keywords):
        ai_reply = await _call_gemini(user_text)
        if ai_reply:
            return ai_reply

    # 4. Ekstraksi entitas dan query ke database semantik (Fuseki)
    entities = _extract_entities(text)
    kw: dict = {"limit": 5, "offset": 0}
    kw.update(entities)
    # Jangan gunakan 'q' dan filter spesifik bersamaan
    if "q" in entities and (entities.get("kelas") or entities.get("kabkota")):
        kw.pop("q", None)

    try:
        results = await sp.search_hospitals(**kw)
    except Exception as e:
        log.error("SPARQL error: %s", e)
        # Jika Fuseki tidak tersedia, coba Gemini saja
        ai_reply = await _call_gemini(user_text)
        if ai_reply:
            return ai_reply
        return f"Maaf, terjadi kendala saat menghubungkan ke database semantik (Fuseki): {type(e).__name__}"

    # 5. Siapkan konteks dari database lalu kirim ke Gemini
    db_context = _format_db_results(results, entities)

    ai_reply = await _call_gemini(user_text, db_context)
    if ai_reply:
        return ai_reply

    # 6. Fallback rule-based jika Gemini tidak tersedia
    return _format_fallback(results, entities)
