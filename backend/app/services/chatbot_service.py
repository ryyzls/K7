"""Layanan Chatbot Asisten Semantik CariSehat.
Menerjemahkan bahasa alami pengguna ke query SPARQL pada Apache Jena Fuseki.
"""
import re
from app.services import sparql_service as sp
from app.services import dbpedia_service as dbp


async def process_chat_message(user_text: str) -> str:
    """Proses teks masukan pengguna dan menghasilkan jawaban berbasis data semantik."""
    text = (user_text or "").strip().lower()
    if not text:
        return "Halo! Ada yang bisa saya bantu terkait informasi rumah sakit di Sumatera Utara?"

    # 1. Sapaan / Greeting
    if any(greet in text for greet in ["halo", "hai", "selamat", "pagi", "siang", "sore", "malam", "assalamualaikum"]):
        return (
            "Halo! Saya asisten virtual **CariSehat** berbasis Web Semantik.\n\n"
            "Anda bisa menanyakan informasi seperti:\n"
            "- *\"RS kelas A di Medan\"*\n"
            "- *\"Cari rumah sakit jiwa atau rumah sakit mata\"*\n"
            "- *\"Daftar rumah sakit di Deli Serdang\"*\n"
            "- *\"Informasi kota Medan dari DBpedia\"*"
        )

    # 2. Pertanyaan khusus DBpedia (External Linked Data)
    if "dbpedia" in text or "tentang kota" in text or "profil kota" in text:
        m = re.search(r"(medan|binjai|pematangsiantar|tebing tinggi|karo|deli serdang|simalungun)", text)
        city = m.group(1) if m else "medan"
        info = await dbp.get_dbpedia_info(city)
        if info.get("abstract"):
            abs_text = info["abstract"][:300] + "..." if len(info["abstract"]) > 300 else info["abstract"]
            res = f"🌐 **Data Eksternal DBpedia ({info.get('dbpedia_resource')}):**\n\n{abs_text}"
            if info.get("population"):
                res += f"\n\n👥 Populasi tercatat: {int(float(info['population'])):,} jiwa"
            return res
        return f"Belum berhasil memuat data eksternal DBpedia untuk wilayah {city}."

    # 3. Ekstraksi Entitas dari Pertanyaan Pengguna
    target_kelas = None
    if re.search(r"\bkelas a\b", text):
        target_kelas = "A"
    elif re.search(r"\bkelas b\b", text):
        target_kelas = "B"
    elif re.search(r"\bkelas c\b", text):
        target_kelas = "C"
    elif re.search(r"\bkelas d\b", text):
        target_kelas = "D"

    target_jenis = None
    if "umum" in text or "rsu" in text:
        target_jenis = "Umum"
    elif "khusus" in text or "rsk" in text or "jiwa" in text or "mata" in text or "bedah" in text or "ibu dan anak" in text or "rsia" in text:
        target_jenis = "Khusus"

    # Deteksi Kabupaten/Kota Sumut yang umum
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
        "langkat": "Kab. Langkat"
    }
    target_kabkota = None
    for k, v in daftar_kota.items():
        if k in text:
            target_kabkota = v
            break

    # Deteksi Layanan
    target_layanan = ""
    for l in ["Anak", "Bersalin", "Bedah", "Ginjal", "Gigi dan Mulut", "Jiwa", "Mata", "Paru"]:
        if l.lower() in text:
            target_layanan = l
            break

    # Ekstraksi kata kunci nama RS jika menyebut "rs" atau "rumah sakit" spesifik
    nama_query = ""
    name_match = re.search(r"(?:rs|rumah sakit)\s+([a-zA-Z\s]+)", text)
    if name_match:
        extracted = name_match.group(1).strip()
        # Cegah kata filter terdeteksi sebagai nama RS
        if extracted not in ["kelas a", "kelas b", "kelas c", "kelas d", "umum", "khusus", "jiwa", "mata", "di medan"]:
            nama_query = extracted[:30]

    # 4. Jalankan Query SPARQL Semantik ke Fuseki
    kw = {
        "limit": 5,
        "offset": 0
    }
    if target_kelas:
        kw["kelas"] = target_kelas
    if target_jenis:
        kw["jenis"] = target_jenis
    if target_kabkota:
        kw["kabkota"] = target_kabkota
    if target_layanan:
        kw["layanan"] = target_layanan
    if nama_query and not (target_kelas or target_kabkota):
        kw["q"] = nama_query

    try:
        results = await sp.search_hospitals(**kw)
    except Exception as e:
        return f"Maaf, terjadi kendala saat menghubungkan ke database semantik (Fuseki): {type(e).__name__}"

    # 5. Format Jawaban
    if not results:
        return (
            "Maaf, saya tidak menemukan rumah sakit yang sesuai kriteria tersebut di database kami.\n"
            "Coba tanyakan dengan kriteria lain, misalnya: *'Rumah sakit kelas B di Medan'* atau *'RS Khusus di Sumut'*."
        )

    kriteria_desc = []
    if target_kelas: kriteria_desc.append(f"Kelas {target_kelas}")
    if target_jenis: kriteria_desc.append(f"Jenis {target_jenis}")
    if target_kabkota: kriteria_desc.append(f"di {target_kabkota}")
    if target_layanan: kriteria_desc.append(f"layanan {target_layanan}")
    
    label_kriteria = " (" + ", ".join(kriteria_desc) + ")" if kriteria_desc else ""
    
    jawaban = [f"Ditemukan beberapa rumah sakit yang sesuai{label_kriteria}:\n"]
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
