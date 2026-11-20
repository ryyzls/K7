"""Konstanta, pemetaan ontologi, dan model state untuk Chatbot CariSehat."""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Out of Scope response (Wajib persis sesuai spesifikasi T2 & R3)
# ---------------------------------------------------------------------------
OUT_OF_SCOPE_TEXT = "Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini."

DATA_NOTE = "Layanan terlapor SIRS Kemenkes; lokasi OpenStreetMap"
DISCLAIMER = "\n\nLayanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fasilitas dan BPJS dari data lama belum terverifikasi. Sumber dan tanggal tersedia pada halaman detail. Chatbot ini bukan untuk diagnosis medis."
DISCLAIMER_EMERGENCY = "\n\nSEGERA HUBUNGI LAYANAN DARURAT DI ATAS ATAU DATANGI UGD TERDEKAT. Chatbot ini BUKAN pengganti pertolongan medis profesional darurat."

# ---------------------------------------------------------------------------
# Pemetaan 33 Kabupaten/Kota di Sumatera Utara & Ibukota / Alias
# ---------------------------------------------------------------------------
KABKOTA_MAP: dict[str, str] = {
    # Kota
    "medan": "Kota Medan",
    "kota medan": "Kota Medan",
    "binjai": "Kota Binjai",
    "kota binjai": "Kota Binjai",
    "pematangsiantar": "Kota Pematang Siantar",
    "pematang siantar": "Kota Pematang Siantar",
    "siantar": "Kota Pematang Siantar",
    "kota pematang siantar": "Kota Pematang Siantar",
    "tebing tinggi": "Kota Tebing Tinggi",
    "tebingtinggi": "Kota Tebing Tinggi",
    "kota tebing tinggi": "Kota Tebing Tinggi",
    "tanjungbalai": "Kota Tanjung Balai",
    "tanjung balai": "Kota Tanjung Balai",
    "kota tanjung balai": "Kota Tanjung Balai",
    "sibolga": "Kota Sibolga",
    "kota sibolga": "Kota Sibolga",
    "padangsidimpuan": "Kota Padang Sidempuan",
    "padang sidimpuan": "Kota Padang Sidempuan",
    "padangsidempuan": "Kota Padang Sidempuan",
    "padang sidempuan": "Kota Padang Sidempuan",
    "sidimpuan": "Kota Padang Sidempuan",
    "sidempuan": "Kota Padang Sidempuan",
    "gunungsitoli": "Kota Gunungsitoli",
    "gunung sitoli": "Kota Gunungsitoli",
    "kota gunungsitoli": "Kota Gunungsitoli",

    # Kabupaten & Pusat Administrasi
    "deli serdang": "Kab. Deli Serdang",
    "deliserdang": "Kab. Deli Serdang",
    "lubuk pakam": "Kab. Deli Serdang",
    "lubukpakam": "Kab. Deli Serdang",
    "karo": "Kab. Karo",
    "kabanjahe": "Kab. Karo",
    "berastagi": "Kab. Karo",
    "toba": "Kab. Toba Samosir",
    "toba samosir": "Kab. Toba Samosir",
    "balige": "Kab. Toba Samosir",
    "samosir": "Kab. Samosir",
    "pangururan": "Kab. Samosir",
    "simalungun": "Kab. Simalungun",
    "pematang raya": "Kab. Simalungun",
    "pematangraya": "Kab. Simalungun",
    "asahan": "Kab. Asahan",
    "kisaran": "Kab. Asahan",
    "tapanuli utara": "Kab. Tapanuli Utara",
    "taput": "Kab. Tapanuli Utara",
    "tarutung": "Kab. Tapanuli Utara",
    "tapanuli tengah": "Kab. Tapanuli Tengah",
    "tapteng": "Kab. Tapanuli Tengah",
    "pandan": "Kab. Tapanuli Tengah",
    "tapanuli selatan": "Kab. Tapanuli Selatan",
    "tapsel": "Kab. Tapanuli Selatan",
    "sipirok": "Kab. Tapanuli Selatan",
    "langkat": "Kab. Langkat",
    "stabat": "Kab. Langkat",
    "nias": "Kab. Nias",
    "nias selatan": "Kab. Nias Selatan",
    "nisel": "Kab. Nias Selatan",
    "teluk dalam": "Kab. Nias Selatan",
    "nias utara": "Kab. Nias Utara",
    "lotu": "Kab. Nias Utara",
    "nias barat": "Kab. Nias Barat",
    "lahomi": "Kab. Nias Barat",
    "batu bara": "Kab. Batu Bara",
    "batubara": "Kab. Batu Bara",
    "limapuluh": "Kab. Batu Bara",
    "mandailing natal": "Kab. Mandailing Natal",
    "madina": "Kab. Mandailing Natal",
    "panyabungan": "Kab. Mandailing Natal",
    "labuhan batu": "Kab. Labuhan Batu",
    "labuhanbatu": "Kab. Labuhan Batu",
    "rantau prapat": "Kab. Labuhan Batu",
    "rantauprapat": "Kab. Labuhan Batu",
    "labuhan batu utara": "Kab. Labuhan Batu Utara",
    "labura": "Kab. Labuhan Batu Utara",
    "aek kanopan": "Kab. Labuhan Batu Utara",
    "labuhan batu selatan": "Kab. Labuhan Batu Selatan",
    "labusel": "Kab. Labuhan Batu Selatan",
    "kotapinang": "Kab. Labuhan Batu Selatan",
    "dairi": "Kab. Dairi",
    "sidikalang": "Kab. Dairi",
    "humbang hasundutan": "Kab. Humbang Hasundutan",
    "humbahas": "Kab. Humbang Hasundutan",
    "dolok sanggul": "Kab. Humbang Hasundutan",
    "doloksanggul": "Kab. Humbang Hasundutan",
    "pakpak bharat": "Kab. Pakpak Bharat",
    "pakpak": "Kab. Pakpak Bharat",
    "salak": "Kab. Pakpak Bharat",
    "padang lawas": "Kab. Padang Lawas",
    "palas": "Kab. Padang Lawas",
    "sibuhuan": "Kab. Padang Lawas",
    "padang lawas utara": "Kab. Padang Lawas Utara",
    "paluta": "Kab. Padang Lawas Utara",
    "gunung tua": "Kab. Padang Lawas Utara",
    "gunungtua": "Kab. Padang Lawas Utara",
    "serdang bedagai": "Kab. Serdang Bedagai",
    "sergai": "Kab. Serdang Bedagai",
    "sei rampah": "Kab. Serdang Bedagai",
    "seirampah": "Kab. Serdang Bedagai",
}

# ---------------------------------------------------------------------------
# Layanan ontologi RDF & Sinonim/Keluhan Awam
# ---------------------------------------------------------------------------
LAYANAN_SYNONYMS: dict[str, str] = {
    # Gigi dan Mulut
    "sakit gigi": "Gigi dan Mulut",
    "cabut gigi": "Gigi dan Mulut",
    "tambal gigi": "Gigi dan Mulut",
    "gigi berlubang": "Gigi dan Mulut",
    "gusi bengkak": "Gigi dan Mulut",
    "dokter gigi": "Gigi dan Mulut",
    "poli gigi": "Gigi dan Mulut",
    "gigi": "Gigi dan Mulut",
    "penyakit mulut": "Gigi dan Mulut",
    "poli mulut": "Gigi dan Mulut",
    "sariawan": "Gigi dan Mulut",
    "operasi gigi bungsu": "Bedah Mulut",
    "bedah mulut": "Bedah Mulut",
    "behel": "Ortodonti",
    "kawat gigi": "Ortodonti",
    "ortodonti": "Ortodonti",

    # Penyakit Dalam / Kardiologi (Catatan jujur: ontologi belum punya poli jantung spesifik)
    "jantung": "Penyakit Dalam",
    "sakit jantung": "Penyakit Dalam",
    "penyakit jantung": "Penyakit Dalam",
    "kardiologi": "Penyakit Dalam",
    "nyeri dada": "Penyakit Dalam",
    "angina": "Penyakit Dalam",
    "darah tinggi": "Penyakit Dalam",
    "hipertensi": "Penyakit Dalam",
    "diabetes": "Penyakit Dalam",
    "gula darah": "Penyakit Dalam",
    "kencing manis": "Penyakit Dalam",
    "kolesterol": "Penyakit Dalam",
    "lambung": "Penyakit Dalam",
    "maag": "Penyakit Dalam",
    "gerd": "Penyakit Dalam",
    "asam lambung": "Penyakit Dalam",
    "penyakit hati": "Penyakit Dalam",
    "gangguan hati": "Penyakit Dalam",
    "spesialis hati": "Penyakit Dalam",
    "liver": "Penyakit Dalam",
    "hepatitis": "Penyakit Dalam",
    "penyakit dalam": "Penyakit Dalam",
    "internis": "Penyakit Dalam",

    # Cuci Darah / Dialisis
    "cuci darah": "Dialisis / Cuci Darah",
    "ginjal": "Dialisis / Cuci Darah",
    "gagal ginjal": "Dialisis / Cuci Darah",
    "hemodialisa": "Dialisis / Cuci Darah",
    "dialisis": "Dialisis / Cuci Darah",

    # Kebidanan dan Kandungan
    "hamil": "Kebidanan dan Kandungan",
    "melahirkan": "Kebidanan dan Kandungan",
    "persalinan": "Kebidanan dan Kandungan",
    "caesar": "Kebidanan dan Kandungan",
    "sesar": "Kebidanan dan Kandungan",
    "kandungan": "Kebidanan dan Kandungan",
    "kebidanan": "Kebidanan dan Kandungan",
    "bersalin": "Kebidanan dan Kandungan",
    "lahiran": "Kebidanan dan Kandungan",
    "obgyn": "Kebidanan dan Kandungan",
    "bidan": "Kebidanan dan Kandungan",
    "usg kandungan": "Kebidanan dan Kandungan",
    "ginekologi": "Kebidanan dan Kandungan",

    # Kesehatan Anak
    "anak sakit": "Kesehatan Anak",
    "anak demam": "Kesehatan Anak",
    "anak panas": "Kesehatan Anak",
    "anak saya demam": "Kesehatan Anak",
    "anak saya sakit": "Kesehatan Anak",
    "bayi": "Kesehatan Anak",
    "balita": "Kesehatan Anak",
    "pediatri": "Kesehatan Anak",
    "pediatrik": "Kesehatan Anak",
    "dokter anak": "Kesehatan Anak",
    "spesialis anak": "Kesehatan Anak",
    "poli anak": "Kesehatan Anak",
    "demam anak": "Kesehatan Anak",
    "kejang anak": "Kesehatan Anak",
    "stunting": "Kesehatan Anak",
    "panas tinggi anak": "Kesehatan Anak",

    # Kesehatan Jiwa / Psikiatri / Psikologi
    "jiwa": "Kesehatan Jiwa / Psikiatri",
    "psikiatri": "Kesehatan Jiwa / Psikiatri",
    "psikiater": "Kesehatan Jiwa / Psikiatri",
    "stres": "Kesehatan Jiwa / Psikiatri",
    "stress": "Kesehatan Jiwa / Psikiatri",
    "depresi": "Kesehatan Jiwa / Psikiatri",
    "mental": "Kesehatan Jiwa / Psikiatri",
    "skizofrenia": "Kesehatan Jiwa / Psikiatri",
    "bipolar": "Kesehatan Jiwa / Psikiatri",
    "gangguan jiwa": "Kesehatan Jiwa / Psikiatri",
    "psikologi": "Psikologi Klinis",
    "psikolog": "Psikologi Klinis",
    "konseling": "Psikologi Klinis",

    # Mata
    "mata": "Kesehatan Mata",
    "katarak": "Kesehatan Mata",
    "operasi katarak": "Bedah Katarak",
    "bedah katarak": "Bedah Katarak",
    "dokter mata": "Kesehatan Mata",
    "rabun": "Kesehatan Mata",
    "minus": "Kesehatan Mata",
    "oftalmologi": "Kesehatan Mata",
    "refraksi": "Refraksi",
    "kacamata": "Refraksi",
    "periksa kacamata": "Refraksi",

    # Pulmonologi / Paru / Pernapasan
    "paru": "Pulmonologi dan Kedokteran Respirasi",
    "tbc": "Pulmonologi dan Kedokteran Respirasi",
    "tb": "Pulmonologi dan Kedokteran Respirasi",
    "tuberkulosis": "Pulmonologi dan Kedokteran Respirasi",
    "sesak": "Pulmonologi dan Kedokteran Respirasi",
    "sesak nafas": "Pulmonologi dan Kedokteran Respirasi",
    "sesak napas": "Pulmonologi dan Kedokteran Respirasi",
    "asma": "Pulmonologi dan Kedokteran Respirasi",
    "batuk kronis": "Pulmonologi dan Kedokteran Respirasi",
    "batuk berdarah": "Pulmonologi dan Kedokteran Respirasi",
    "flek paru": "Pulmonologi dan Kedokteran Respirasi",
    "pneumonia": "Pulmonologi dan Kedokteran Respirasi",
    "respirasi": "Pulmonologi dan Kedokteran Respirasi",
    "pulmonologi": "Pulmonologi dan Kedokteran Respirasi",

    # Bedah
    "operasi": "Bedah",
    "bedah": "Bedah",
    "tumor": "Bedah",
    "kanker": "Bedah",
    "usus buntu": "Bedah",
    "appendisitis": "Bedah",
    "benjolan": "Bedah",
    "wasir": "Bedah",
    "ambeien": "Bedah",

    # Rawat Inap & UGD
    "igd": "UGD 24 Jam",
    "ugd": "UGD 24 Jam",
    "gawat darurat": "UGD 24 Jam",
    "darurat": "UGD 24 Jam",
    "rawat inap": "Rawat Inap",
    "opname": "Rawat Inap",
    "nginap": "Rawat Inap",
    "masuk rs": "Rawat Inap",
    "butuh kamar": "Rawat Inap",
    "kamar rawat": "Rawat Inap",

    # Laboratorium & Radiologi
    "laboratorium": "Laboratorium",
    "lab": "Laboratorium",
    "cek darah": "Laboratorium",
    "tes darah": "Laboratorium",
    "cek kolesterol": "Laboratorium",
    "rontgen": "Radiologi",
    "rontgen dada": "Radiologi Toraks",
    "toraks": "Radiologi Toraks",
    "ct scan": "Radiologi",
    "mri": "Radiologi",
    "radiologi": "Radiologi",
    "xray": "Radiologi",
    "x-ray": "Radiologi",
    "usg": "Radiologi",

    # Rehabilitasi Medik & Imunisasi
    "rehabilitasi": "Rehabilitasi Medik",
    "rehabilitasi medik": "Rehabilitasi Medik",
    "fisioterapi": "Rehabilitasi Medik",
    "rehab": "Rehabilitasi Medik",
    "terapi fisik": "Rehabilitasi Medik",
    "vaksin": "Imunisasi",
    "imunisasi": "Imunisasi",
    "anestesi": "Anestesi",
    "bius": "Anestesi",
    "dokter umum": "Pelayanan Medik Umum",
    "subspesialis": "Subspesialis",
}

# ---------------------------------------------------------------------------
# Fasilitas ontologi RDF & Sinonim
# ---------------------------------------------------------------------------
FASILITAS_SYNONYMS: dict[str, str] = {
    "icu": "ICU",
    "intensive care": "ICU",
    "unit rawat intensif": "ICU",
    "iccu": "ICU / ICCU",
    "nicu": "ICU / ICCU / NICU",
    "picu": "ICU / ICCU / NICU",
    "ambulans": "Ambulans",
    "ambulance": "Ambulans",
    "apotek": "Apotek",
    "farmasi": "Instalasi Farmasi",
    "instalasi farmasi": "Instalasi Farmasi",
    "kamar operasi": "Kamar Operasi",
    "ruang operasi": "Kamar Operasi",
    "kamar bersalin": "Kamar Bersalin",
    "ruang bersalin": "Kamar Bersalin",
    "cuci darah": "Unit Hemodialisa",
    "hemodialisa": "Unit Hemodialisa",
    "bangsal jiwa": "Bangsal Perawatan Jiwa",
    "laboratorium": "Laboratorium",
    "lab": "Laboratorium",
}

# ---------------------------------------------------------------------------
# Kata Kunci Darurat Medis (Gunakan batas kata)
# ---------------------------------------------------------------------------
EMERGENCY_KEYWORDS: list[str] = [
    "serangan jantung", "henti jantung", "stroke", "pendarahan", "perdarahan",
    "kecelakaan", "tabrakan", "tidak sadarkan diri", "hilang kesadaran",
    "pingsan mendadak", "overdosis", "keracunan", "sesak napas parah",
    "sesak nafas parah", "luka parah", "bakar parah", "luka bakar", "tenggelam",
    "kejang parah", "kejang-kejang", "koma", "kritis", "darurat", "gawat darurat",
    "patah tulang terbuka", "panggil ambulans", "hubungi 119",
]

# ---------------------------------------------------------------------------
# Pemicu Empati
# ---------------------------------------------------------------------------
EMPATHY_TRIGGERS: list[str] = [
    "sakit", "parah", "darurat", "tolong", "bantu", "demam", "panas",
    "lemas", "nyeri", "pusing", "sesak", "muntah", "diare", "infeksi",
]

# ---------------------------------------------------------------------------
# Sapaan & FAQ
# ---------------------------------------------------------------------------
GREETING_KEYWORDS: list[str] = [
    "halo", "hai", "hello", "hi", "selamat pagi", "selamat siang", "selamat sore",
    "selamat malam", "assalamualaikum", "permisi", "hei", "terima kasih",
    "makasih", "thanks", "tengkyu",
]

FAQ_KEYWORDS: list[str] = [
    "apa itu carisehat", "apa itu cari sehat", "bagaimana cara", "cara pakai",
    "fitur apa", "bisa apa", "tentang aplikasi", "cara kerja", "apa fungsi",
    "bagaimana aplikasi", "website apa ini", "bantuan", "help", "panduan",
    "bisa bantu apa",
]

# ---------------------------------------------------------------------------
# Kata Kunci Rumah Sakit Eksplisit (Word Boundary)
# ---------------------------------------------------------------------------
HOSPITAL_EXPLICIT_ROOTS: list[str] = [
    r"\brs\b", r"\brmh\s*skt\b", r"\brumah\s*sakit\b", r"\brumahsakit\b",
    r"\brsu\b", r"\brsud\b", r"\brsup\b", r"\brsia\b", r"\brsk\b", r"\brsj\b", r"\brsau\b",
    r"\bfaskes\b", r"\brujukan\b",
    r"\bdokter\b", r"\bspesialis\b", r"\bpoliklinik\b", r"\bpoli\b",
    r"\bpasien\b", r"\brawat\s*inap\b", r"\brawat\s*jalan\b", r"\bopname\b",
    r"\bkamar\s*inap\b", r"\bkamar\s*rawat\b", r"\bkamar\s*operasi\b",
    r"\bugd\b", r"\bigd\b", r"\bicu\b", r"\biccu\b", r"\bnicu\b", r"\bpicu\b",
    r"\bambulans\b", r"\bambulance\b",
    r"\blaboratorium\b", r"\bradiologi\b", r"\brontgen\b", r"\bct\s*scan\b", r"\bmri\b",
    r"\bbpjs\b", r"\baskes\b", r"\bkis\b", r"\basuransi\b",
    r"\b(?:kelas|kls|tipe)\s*[a-dA-D]\b",
    r"\bberobat\b",
]

NEARBY_KEYWORDS: list[str] = [
    r"\bterdekat\b", r"\bdi\s+dekat\b", r"\bdidekat\b", r"\bdekat\s+saya\b",
    r"\bsekitar\s+saya\b", r"\bdari\s+sini\b", r"\bposisi\s+saya\b", r"\blokasi\s+saya\b",
    r"\bradius\b", r"\brs\s+dekat\b", r"\bpaling\s+dekat\b", r"\bdekat\s+sini\b",
]

# Quick replies
QR_AFTER_RESULTS = ["Yang terima BPJS?", "Yang punya ICU?", "RS terdekat dari saya", "Lihat RS Kelas A saja"]
QR_AFTER_EMERGENCY = ["Hubungi 119", "RS dengan UGD 24 Jam Terdekat", "Panggil Ambulans"]
QR_AFTER_EMPTY = ["Lihat semua RS di Medan", "RS terdekat dari saya", "RS yang terima BPJS", "RS dengan UGD 24 Jam"]
QR_AFTER_GREETING = ["RS terdekat dari saya", "RS Kelas A di Medan", "RS yang terima BPJS", "RS dengan UGD 24 Jam"]
QR_CLARIFICATION = ["Kota Medan", "Kab. Deli Serdang", "Kota Binjai", "Kota Pematang Siantar", "RS terdekat dari saya"]
QR_OUT_OF_SCOPE = ["Cari RS di Medan", "RS terdekat dari saya", "RS yang terima BPJS", "RS dengan UGD 24 Jam"]
