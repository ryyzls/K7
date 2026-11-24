"""Formatters dan Pembangun Respons per Intent Chatbot CariSehat.

Memisahkan builder respons per intent:
- DETAIL (profil lengkap 1 RS tanpa header terdekat)
- ATRIBUT (jawaban langsung ringkas untuk atribut spesifik)
- LIST_FILTER (daftar RS + jumlah total sebenarnya + paging)
- NEARBY (daftar berjarak dengan header terdekat HANYA di sini)
- COMPARE (tabel perbandingan 2 RS)
- DISAMBIGUASI (tanya kandidat nama RS kembar / sama kuat)
- NOT_FOUND (topik RS tidak ditemukan + saran)
- EMERGENCY (hotline di atas, tanpa emoji, RS UGD siaga)
- GREETING / FAQ / KLARIFIKASI / OUT_OF_SCOPE
"""
from __future__ import annotations

import math
from typing import Any

from app.services.chatbot.models import (
    DATA_NOTE,
    DISCLAIMER,
    DISCLAIMER_EMERGENCY,
    OUT_OF_SCOPE_TEXT,
    QR_AFTER_EMPTY,
    QR_AFTER_EMERGENCY,
    QR_AFTER_GREETING,
    QR_AFTER_RESULTS,
    QR_CLARIFICATION,
    QR_OUT_OF_SCOPE,
)

OPENING_TEMPLATES: dict[str, list[str]] = {
    "SEARCH_RESULTS": [
        "Berikut {total} rumah sakit yang sesuai dengan pencarian Anda:",
        "Saya menemukan {total} rumah sakit yang memenuhi kriteria Anda:",
        "Terdapat {total} rumah sakit di database kami yang cocok dengan kebutuhan Anda:",
        "Berikut {total} rumah sakit yang tercatat sesuai filter Anda:",
    ],
    "NEARBY_RESULTS": [
        "📍 **Berikut rumah sakit terdekat dari lokasi Anda:**\n",
        "📍 **Pilihan rumah sakit paling dekat yang siap melayani Anda:**\n",
    ],
    "EMPTY": [
        "Maaf, tidak ditemukan rumah sakit yang memenuhi seluruh kriteria tersebut di database kami.",
        "Belum ada data rumah sakit yang cocok persis dengan kombinasi filter tersebut.",
    ],
    "GREETING": [
        "Halo! Saya asisten **CariSehat** 🏥, siap membantu Anda menemukan informasi 206 rumah sakit di Sumatera Utara.\n\nAnda dapat mencari berdasarkan kota, kelas RS, spesialisasi, fasilitas, atau RS terdekat.\n\nAda yang bisa saya bantu hari ini?",
        "Hai! Selamat datang di **CariSehat** – direktori rumah sakit se-Sumatera Utara berbasis Web Semantik.\n\nSaya bisa membantu Anda:\n- Mencari RS berdasarkan kota, kelas (A/B/C/D), atau layanan\n- Menemukan RS terdekat dari lokasi Anda\n- Membandingkan fasilitas dua rumah sakit\n- Menampilkan RS yang menerima BPJS\n\nApa yang sedang Anda butuhkan?",
    ],
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Hitung jarak antara dua koordinat (lat, lon) dalam kilometer (Haversine)."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return round(r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def pick_template(category: str, previous_text: str = "", seed: int | None = None) -> str:
    """Pilih template pembuka dengan mekanisme anti-pengulangan."""
    templates = OPENING_TEMPLATES.get(category, [""])
    if not templates:
        return ""
    if seed is not None:
        return templates[seed % len(templates)]
    # Hindari pembuka yang sama dengan kalimat pertama respons bot sebelumnya
    prev_first_line = (previous_text.strip().splitlines() or [""])[0]
    for t in templates:
        if t not in prev_first_line and prev_first_line not in t:
            return t
    return templates[0]


def format_detail_rs(
    rs: dict,
    user_loc: tuple[float, float] | None = None,
    empathy: str = "",
) -> dict:
    """Format profil lengkap 1 Rumah Sakit (DETAIL).
    
    TIDAK menggunakan kata 'terdekat' di header.
    Jarak hanya ditampilkan jika GPS ada DAN sumber koordinat andal.
    """
    lines = []
    if empathy:
        lines.append(empathy)

    bpjs_badge = "✅ Menerima BPJS Kesehatan" if rs.get("bpjs") else "❌ Tidak Menerima BPJS Kesehatan"
    lines.append(f"### 🏥 {rs['nama']}")
    lines.append(f"**Kelas:** {rs.get('kelas', '-')} | **Jenis:** {rs.get('jenis', 'Umum')} | **BPJS:** {bpjs_badge}")
    if rs.get("pemilik"):
        lines.append(f"**Kepemilikan / Pengelola:** {rs['pemilik']}")
    lines.append(f"**Wilayah:** {rs.get('kabkota', '-')}")
    lines.append(f"**Alamat:** {rs.get('alamat', '-')}")

    telp = rs.get("telepon") or "Tidak tersedia di database"
    lines.append(f"**Nomor Telepon:** {telp}")

    # Jarak opsional jika koordinat andal
    if user_loc and rs.get("lat") and rs.get("lon"):
        sumber = rs.get("sumber_koordinat")
        if sumber in ("osm", "jalan", "nama"):
            dist = haversine_distance(user_loc[0], user_loc[1], rs["lat"], rs["lon"])
            lines.append(f"**Jarak dari lokasi Anda:** ~{dist} km")

    # Layanan lengkap
    layanan = rs.get("layanan") or []
    if layanan:
        lines.append(f"\n🩺 **Layanan terlapor SIRS ({len(layanan)}), belum diverifikasi operasional:**\n" + ", ".join(layanan))

    # Fasilitas lengkap
    fasilitas = rs.get("fasilitas") or []
    if fasilitas:
        lines.append(f"\n🏢 **Fasilitas Penunjang ({len(fasilitas)}):**\n" + ", ".join(fasilitas))

    lines.append(f"\n🔗 [Lihat Detail Lengkap di Portal](/rumah-sakit/{rs['id']})")

    body = "\n".join(lines) + DISCLAIMER
    qr = [
        "Yang terima BPJS?",
        "Yang punya ICU?",
        "RS terdekat dari saya",
        f"Bandingkan dengan RS Pirngadi" if rs["id"] != "rs-083" else "Bandingkan dengan RS Adam Malik",
    ]
    return {
        "text": body,
        "is_emergency": False,
        "quick_replies": qr,
        "hospitals": [rs],
        "data_note": DATA_NOTE,
    }


def format_attribute_rs(
    rs: dict,
    attribute: str,
    empathy: str = "",
    user_loc: tuple[float, float] | None = None,
) -> dict:
    """Format jawaban ringkas langsung untuk atribut spesifik 1 RS (ATRIBUT)."""
    lines = []
    if empathy:
        lines.append(empathy)

    nama = rs["nama"]
    attr = attribute.lower()

    if attr == "telepon":
        telp = rs.get("telepon")
        if telp:
            lines.append(f"📞 Nomor telepon **{nama}**: **{telp}**.")
        else:
            lines.append(f"Mohon maaf, nomor telepon untuk **{nama}** belum tersedia di database kami.")

    elif attr == "alamat":
        lines.append(f"📍 Alamat **{nama}**: **{rs.get('alamat', '-')}, {rs.get('kabkota', '-')}**.")

    elif attr == "bpjs":
        if rs.get("bpjs"):
            lines.append(f"✅ Ya, **{nama}** melayani pasien **BPJS Kesehatan**.")
        else:
            lines.append(f"❌ Tidak, **{nama}** saat ini tidak melayani pasien BPJS Kesehatan.")

    elif attr == "icu":
        fas = rs.get("fasilitas", [])
        icu_matches = [f for f in fas if f.startswith("ICU")]
        if icu_matches:
            lines.append(f"✅ Ya, **{nama}** memiliki fasilitas perawatan intensif: **{', '.join(icu_matches)}**.")
        else:
            lines.append(f"Data fasilitas **{nama}** belum mencantumkan ruang perawatan intensif (ICU).")

    elif attr == "jam_buka":
        from app.services.enrichment_service import get_hospital_enrichment
        hours = get_hospital_enrichment(rs.get("id", ""))["jam_operasional"]["jadwal_harian"]
        available = [row for row in hours if row["jam"] != "Belum tersedia"]
        if available:
            lines.append(f"Jadwal poliklinik tercatat untuk **{nama}**:")
            lines.extend(f"{row['hari']}: {row['jam']}" for row in hours)
        else:
            lines.append(f"Jadwal poliklinik **{nama}** belum tersedia. Hubungi rumah sakit untuk konfirmasi.")

    elif attr == "jenis":
        lines.append(f"🏥 **{nama}** adalah Rumah Sakit berjenis **{rs.get('jenis', 'Umum')}** Kelas {rs.get('kelas', '-')}.")

    elif attr == "kelas":
        lines.append(f"🏷️ **{nama}** merupakan Rumah Sakit **Kelas {rs.get('kelas', '-')}** ({rs.get('jenis', 'Umum')}).")

    elif attr == "pemilik":
        lines.append(f"🏛️ **{nama}** berstatus kepemilikan / dikelola oleh: **{rs.get('pemilik', 'Tidak tercantum')}**.")

    elif attr == "layanan":
        lay = rs.get("layanan", [])
        if lay:
            lines.append(f"🩺 Layanan terlapor SIRS (bukan ketersediaan saat ini) di **{nama}** ({len(lay)}):\n" + ", ".join(lay))
        else:
            lines.append(f"Belum ada daftar spesifik layanan medis terdaftar untuk **{nama}**.")

    elif attr == "fasilitas":
        fas = rs.get("fasilitas", [])
        if fas:
            lines.append(f"🏢 Fasilitas penunjang di **{nama}** ({len(fas)}):\n" + ", ".join(fas))
        else:
            lines.append(f"Belum ada daftar fasilitas penunjang terdaftar untuk **{nama}**.")

    elif attr == "jarak":
        if not user_loc:
            lines.append(f"Untuk menghitung jarak ke **{nama}**, silakan izinkan akses lokasi (GPS) di browser lalu tanyakan kembali.")
        elif rs.get("lat") is None or rs.get("lon") is None or rs.get("sumber_koordinat") not in ("osm", "jalan", "nama"):
            lines.append(f"Jarak ke **{nama}** belum dapat dihitung karena koordinat rumah sakit belum terverifikasi.")
        else:
            distance = haversine_distance(user_loc[0], user_loc[1], rs["lat"], rs["lon"])
            lines.append(f"Jarak **{nama}** dari lokasi Anda sekitar **{distance} km** (jarak garis lurus, bukan jarak perjalanan melalui jalan).")
    else:
        lines.append(f"Informasi mengenai **{nama}**:")
        lines.append(f"- Wilayah: {rs.get('kabkota')}")
        lines.append(f"- Alamat: {rs.get('alamat')}")
        if rs.get("telepon"):
            lines.append(f"- Telepon: {rs.get('telepon')}")

    lines.append(f"\nUntuk profil lengkap faskes ini, Anda dapat membuka [Detail {nama}](/rumah-sakit/{rs['id']}).")
    body = "\n".join(lines) + DISCLAIMER

    return {
        "text": body,
        "is_emergency": False,
        "quick_replies": [f"Detail {nama}", "Yang terima BPJS?", "RS terdekat dari saya"],
        "hospitals": [rs],
        "data_note": DATA_NOTE,
    }


def format_list_filter(
    hospitals: list[dict],
    total_count: int,
    filters: dict,
    offset: int = 0,
    previous_text: str = "",
    empathy: str = "",
    seed: int | None = None,
) -> dict:
    """Format daftar hasil pencarian / filter (LIST_FILTER).
    
    Menampilkan N RS ditemukan (total sebenarnya).
    Urutan default: Kelas (A->D), lalu nama; BUKAN jarak.
    """
    if not hospitals:
        # Penanganan hasil 0 dengan penjelasan filter spesifik
        empty_lines = []
        if empathy:
            empty_lines.append(empathy)
        filter_descs = []
        if filters.get("kabkota"):
            filter_descs.append(f"wilayah {filters['kabkota']}")
        if filters.get("kelas"):
            filter_descs.append(f"Kelas {filters['kelas']}")
        if filters.get("layanan"):
            filter_descs.append(f"layanan {filters['layanan']}")
        if filters.get("fasilitas"):
            filter_descs.append(f"fasilitas {filters['fasilitas']}")
        if filters.get("bpjs"):
            filter_descs.append("menerima BPJS")

        filter_str = ", ".join(filter_descs) if filter_descs else "kriteria tersebut"
        empty_lines.append(
            f"Maaf, belum menemukan rumah sakit yang memenuhi kombinasi kriteria **{filter_str}** di database kami (tidak ada data yang cocok / belum ditemukan).\n\n"
            "Silakan coba memperluas pencarian dengan menghilangkan salah satu filter atau mencari di wilayah terdekat."
        )
        body = "\n".join(empty_lines) + DISCLAIMER
        qr = list(QR_AFTER_EMPTY)
        if filters.get("kelas"):
            qr.insert(0, "Tanpa filter kelas")
        return {
            "text": body,
            "is_emergency": False,
            "quick_replies": qr,
            "hospitals": [],
            "data_note": DATA_NOTE,
        }

    lines = []
    if empathy:
        lines.append(empathy)

    tpl = pick_template("SEARCH_RESULTS", previous_text, seed=seed)
    header = tpl.format(total=total_count)
    lines.append(header + "\n")

    start_idx = offset + 1
    for i, rs in enumerate(hospitals, start=start_idx):
        bpjs_badge = " • ✅ BPJS" if rs.get("bpjs") else ""
        lines.append(f"{i}. **{rs['nama']}**{bpjs_badge}")
        lines.append(f"   📍 {rs['kabkota']} – Kelas {rs.get('kelas', '-')} ({rs.get('jenis', 'Umum')})")
        if rs.get("alamat"):
            lines.append(f"   🏠 {rs['alamat']}")
        if rs.get("telepon"):
            lines.append(f"   📞 {rs['telepon']}")
        if rs.get("layanan"):
            lines.append(f"   🩺 Layanan: {', '.join(rs['layanan'][:3])}")
        lines.append(f"   🔗 [Lihat Detail](/rumah-sakit/{rs['id']})\n")

    # Paging indicator
    remaining = total_count - (offset + len(hospitals))
    if remaining > 0:
        lines.append(f"*Menampilkan {len(hospitals)} dari {total_count} RS.*")

    body = "\n".join(lines) + DISCLAIMER
    qr = list(QR_AFTER_RESULTS)
    if remaining > 0:
        qr.insert(0, "Lihat lainnya")

    return {
        "text": body,
        "is_emergency": False,
        "quick_replies": qr,
        "hospitals": hospitals,
        "data_note": DATA_NOTE,
    }


def format_nearby_results(
    hospitals_with_distance: list[dict],
    total_count: int,
    user_loc: tuple[float, float] | None,
    location_status: str | None = None,
    previous_text: str = "",
    empathy: str = "",
    seed: int | None = None,
) -> dict:
    """Format hasil pencarian terdekat (NEARBY).
    
    Header 'rumah sakit terdekat' HANYA keluar di sini.
    Jarak dihitung hanya untuk RS dengan koordinat andal.
    """
    lines = []
    if empathy:
        lines.append(empathy)

    # Kasus: Lokasi tidak tersedia / ditolak
    if not user_loc or location_status in ("denied", "unavailable", "timeout", "none"):
        lines.append(
            "📍 Akses lokasi (GPS) pada peramban Anda belum aktif atau izin ditolak.\n\n"
            "Untuk melihat rumah sakit terdekat, silakan izinkan akses lokasi, atau Anda dapat memilih nama kota/kabupaten di bawah ini:"
        )
        return {
            "text": "\n".join(lines) + DISCLAIMER,
            "is_emergency": False,
            "quick_replies": QR_CLARIFICATION,
            "hospitals": [],
            "data_note": DATA_NOTE,
        }

    # Kasus: RS terdekat > 150 km (di luar Sumut)
    if hospitals_with_distance:
        closest_dist = hospitals_with_distance[0].get("distance_km", 0)
        if closest_dist > 150.0:
            lines.append(
                f"⚠️ Lokasi Anda tampaknya berada cukup jauh (~{closest_dist} km) atau di luar wilayah Sumatera Utara. "
                "CariSehat saat ini berfokus pada data rumah sakit di wilayah Provinsi Sumatera Utara.\n\n"
                "Berikut daftar rumah sakit dengan jarak aktual dari posisi Anda:"
            )

    tpl = pick_template("NEARBY_RESULTS", previous_text, seed=seed)
    lines.append(tpl)

    for i, rs in enumerate(hospitals_with_distance, 1):
        dist_str = f" (~{rs['distance_km']} km)" if rs.get("distance_km") is not None else ""
        bpjs_badge = " • ✅ BPJS" if rs.get("bpjs") else ""
        lines.append(f"{i}. **{rs['nama']}**{dist_str}{bpjs_badge}")
        lines.append(f"   📍 {rs['kabkota']} – Kelas {rs.get('kelas', '-')} ({rs.get('jenis', 'Umum')})")
        if rs.get("alamat"):
            lines.append(f"   🏠 {rs['alamat']}")
        if rs.get("telepon"):
            lines.append(f"   📞 {rs['telepon']}")
        lines.append(f"   🔗 [Lihat Detail](/rumah-sakit/{rs['id']})\n")

    body = "\n".join(lines) + DISCLAIMER
    return {
        "text": body,
        "is_emergency": False,
        "quick_replies": QR_AFTER_RESULTS,
        "hospitals": hospitals_with_distance,
        "data_note": DATA_NOTE,
    }


def format_disambiguation(
    candidates: list[dict],
    cleaned_query: str,
) -> dict:
    """Format klarifikasi saat ada beberapa kandidat RS sama kuat (DISAMBIGUASI)."""
    lines = [
        f"Saya menemukan beberapa rumah sakit yang sesuai dengan kata kunci **\"{cleaned_query}\"** di database kami.",
        "Maksud Anda rumah sakit yang mana?\n",
    ]
    quick_replies = []
    for i, rs in enumerate(candidates[:4], 1):
        lines.append(f"{i}. **{rs['nama']}**")
        lines.append(f"   📍 {rs['kabkota']} – Kelas {rs.get('kelas', '-')} ({rs.get('jenis', 'Umum')})")
        if rs.get("alamat"):
            lines.append(f"   🏠 {rs['alamat']}")
        lines.append("")
        quick_replies.append(rs["nama"])

    lines.append("Silakan pilih salah satu opsi di bawah ini untuk melihat informasi selengkapnya.")
    body = "\n".join(lines) + DISCLAIMER

    return {
        "text": body,
        "is_emergency": False,
        "quick_replies": quick_replies,
        "hospitals": candidates[:4],
        "data_note": DATA_NOTE,
    }


def format_not_found_hospital(
    name: str,
    suggestions: list[dict],
) -> dict:
    """Format jawaban jika nama RS yang dicari tidak ditemukan (NOT_FOUND)."""
    lines = [
        f"Mohon maaf, rumah sakit dengan nama **\"{name}\"** tidak ditemukan di database kami."
    ]
    qr = []
    if suggestions:
        lines.append("\nApakah maksud Anda salah satu rumah sakit berikut?")
        for i, rs in enumerate(suggestions[:3], 1):
            lines.append(f"{i}. **{rs['nama']}** ({rs['kabkota']})")
            qr.append(rs["nama"])
    else:
        qr = list(QR_AFTER_EMPTY)

    body = "\n".join(lines) + DISCLAIMER
    return {
        "text": body,
        "is_emergency": False,
        "quick_replies": qr,
        "hospitals": [],
        "data_note": DATA_NOTE,
    }


def format_emergency(
    hospitals: list[dict],
) -> dict:
    """Format mode darurat medis (EMERGENCY) tanpa emoji pada teks bot."""
    hotlines = (
        "HOTLINE GAWAT DARURAT NASIONAL:\n"
        "1. 119 - SPGDT (Gawat Darurat Medis Nasional)\n"
        "2. 112 - Panggilan Darurat Bebas Pulsa\n"
        "3. 118 - Ambulans PMI\n\n"
    )

    rs_lines = []
    for i, rs in enumerate(hospitals[:5], 1):
        dist_str = f" (~{rs['distance_km']} km)" if rs.get("distance_km") is not None else ""
        telp_str = f" - Telp: {rs.get('telepon')}" if rs.get("telepon") else ""
        rs_lines.append(f"{i}. {rs['nama']}{dist_str} - {rs['kabkota']}{telp_str}")

    rs_block = "\n".join(rs_lines) if rs_lines else "Data UGD sedang dimuat, segera hubungi 119."

    body = (
        "KONDISI DARURAT MEDIS TERDETEKSI.\n\n"
        + hotlines
        + "RUMAH SAKIT DENGAN UGD 24 JAM SIAGA:\n"
        + rs_block
        + DISCLAIMER_EMERGENCY
    )

    return {
        "text": body,
        "is_emergency": True,
        "quick_replies": QR_AFTER_EMERGENCY,
        "hospitals": hospitals[:5],
        "data_note": DATA_NOTE,
    }


def format_compare_table(
    rs_a: dict,
    rs_b: dict,
) -> dict:
    """Format tabel perbandingan dua rumah sakit (COMPARE)."""
    def v(d: dict, k: str, default: str = "-") -> str:
        val = d.get(k)
        if val is None:
            return default
        if isinstance(val, bool):
            return "Ya" if val else "Tidak"
        if isinstance(val, list):
            return ", ".join(val[:3]) if val else default
        return str(val)

    rows = [
        ("Nama Rumah Sakit", rs_a["nama"], rs_b["nama"]),
        ("Kelas Perizinan", v(rs_a, "kelas"), v(rs_b, "kelas")),
        ("Jenis Rumah Sakit", v(rs_a, "jenis"), v(rs_b, "jenis")),
        ("Wilayah (Kab/Kota)", v(rs_a, "kabkota"), v(rs_b, "kabkota")),
        ("Menerima BPJS", "Ya ✅" if rs_a.get("bpjs") else "Tidak ❌", "Ya ✅" if rs_b.get("bpjs") else "Tidak ❌"),
        ("Layanan Unggulan", v(rs_a, "layanan"), v(rs_b, "layanan")),
        ("Fasilitas Penunjang", v(rs_a, "fasilitas"), v(rs_b, "fasilitas")),
        ("Nomor Telepon", v(rs_a, "telepon"), v(rs_b, "telepon")),
    ]

    header = f"### 📊 Perbandingan Rumah Sakit\n\n| Atribut | {rs_a['nama']} | {rs_b['nama']} |\n|---|---|---|"
    table_rows = "\n".join(f"| {r} | {a} | {b} |" for r, a, b in rows)

    summary = (
        f"\n\n**Ringkasan Perbandingan:**\n"
        f"- **{rs_a['nama']}**: RS Kelas {rs_a.get('kelas')} ({rs_a.get('jenis')}) di {rs_a.get('kabkota')}, "
        f"{'menerima BPJS' if rs_a.get('bpjs') else 'tidak menerima BPJS'}, memiliki {len(rs_a.get('layanan', []))} layanan terdaftar.\n"
        f"- **{rs_b['nama']}**: RS Kelas {rs_b.get('kelas')} ({rs_b.get('jenis')}) di {rs_b.get('kabkota')}, "
        f"{'menerima BPJS' if rs_b.get('bpjs') else 'tidak menerima BPJS'}, memiliki {len(rs_b.get('layanan', []))} layanan terdaftar."
    )

    body = header + "\n" + table_rows + summary + DISCLAIMER
    return {
        "text": body,
        "is_emergency": False,
        "quick_replies": [f"Detail {rs_a['nama']}", f"Detail {rs_b['nama']}", "RS terdekat dari saya"],
        "hospitals": [rs_a, rs_b],
        "data_note": DATA_NOTE,
    }


def format_clinic_explain() -> dict:
    """Penjelasan kasus tepi klinik / puskesmas / dokter praktik."""
    body = (
        "Saat ini direktori **CariSehat** hanya mencakup **206 Rumah Sakit** (RS Umum & RS Khusus) se-Sumatera Utara "
        "sesuai data perizinan Permenkes No. 3/2020, dan belum menyediakan data puskesmas atau klinik pratama mandiri.\n\n"
        "Kami dapat membantu Anda mencari rumah sakit rujukan terdekat atau rumah sakit berdasarkan kota dan spesialisasi medis yang Anda butuhkan."
        + DISCLAIMER
    )
    return {
        "text": body,
        "is_emergency": False,
        "quick_replies": ["Cari RS di Medan", "RS terdekat dari saya", "RS yang terima BPJS"],
        "hospitals": [],
        "data_note": DATA_NOTE,
    }


def format_out_of_scope() -> dict:
    """Respons persis untuk pertanyaan di luar cakupan faskes (T2)."""
    return {
        "text": OUT_OF_SCOPE_TEXT,
        "is_emergency": False,
        "quick_replies": QR_OUT_OF_SCOPE,
        "hospitals": [],
        "data_note": DATA_NOTE,
    }
