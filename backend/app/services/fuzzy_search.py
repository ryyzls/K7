"""Pencarian toleran typo & singkatan untuk nama rumah sakit.

Letakkan di: backend/app/services/fuzzy_search.py
"""
import difflib
import re

# ---------------------------------------------------------------------------
# 1. Kamus singkatan umum -> bentuk panjang. Tambah sendiri sesuai kebutuhan.
# ---------------------------------------------------------------------------
SINGKATAN = {
    "rs": "rumah sakit",
    "rsu": "rumah sakit umum",
    "rsud": "rumah sakit umum daerah",
    "rsup": "rumah sakit umum pusat",
    "rsia": "rumah sakit ibu dan anak",
    "rsj": "rumah sakit jiwa",
    "rskb": "rumah sakit khusus bedah",
    "ham": "haji adam malik",
    "tk": "tingkat",
    "st": "santa",
    "dr": "dokter",
}

# ---------------------------------------------------------------------------
# 2. Alias manual per RS. Kunci = id RS (rs-001, rs-002, ... sesuai urutan
#    baris di data/rumah_sakit_sumut.csv). Alias bisa berupa singkatan,
#    julukan, atau nama lain. Typo tetap ditoleransi karena alias dicocokkan
#    lewat skor() juga, jadi cukup tulis ejaan yang benar.
# ---------------------------------------------------------------------------
ALIAS_RS = {
    # --- Medan & sekitarnya ---
    "rs-001": ["original hospital", "og", "og hospital", "orijinal hospital"],
    "rs-008": ["columbia asia", "columbia asia medan", "cam"],
    "rs-007": ["columbia asia aksara", "aksara"],
    "rs-083": ["pirngadi", "rsud pirngadi", "dr pirngadi", "rumah sakit pirngadi"],
    "rs-171": ["adam malik", "ham", "rsup ham", "rs haji adam malik", "rs adam malik"],
    "rs-176": ["royal prima", "rs royal", "royal"],
    "rs-177": ["royal prima marelan", "royal marelan"],
    "rs-125": ["hermina", "hermina medan"],
    "rs-185": ["siloam", "siloam medan", "siloam dhirga surya"],
    "rs-178": ["elisabeth", "santa elisabeth", "st elisabeth", "rs elisabeth"],
    "rs-130": ["malahayati", "islam malahayati", "rs islam"],
    "rs-147": ["methodist", "rs methodist", "methodist medan"],
    "rs-157": ["murni teguh", "mtmh", "murni teguh memorial"],
    "rs-142": ["martha friska", "marta friska", "friska"],
    "rs-143": ["martha friska multatuli", "friska multatuli"],
    "rs-156": ["rs muhammadiyah", "muhammadiyah sumut", "rsmu"],
    "rs-057": ["advent", "advent medan", "rs advent"],
    "rs-069": ["bunda thamrin", "thamrin"],
    "rs-053": ["putri hijau", "rs putri hijau", "tk ii putri hijau"],
    "rs-003": ["bhayangkara medan", "polda", "rs polda", "rs bhayangkara"],
    "rs-042": ["rsp usu", "usu", "rs usu", "pendidikan usu", "chairuddin panusunan lubis"],
    "rs-025": ["rsj medan", "rs jiwa medan", "ildrem", "rs jiwa ildrem", "rumah sakit jiwa"],
    "rs-035": ["rs paru", "paru sumut", "rs paru sumatera utara"],
    "rs-204": ["rsau", "rsau medan", "rs angkatan udara", "abdul malik"],
    "rs-089": ["bachtiar djafar", "rs bachtiar", "rs pertamina"],
    "rs-122": ["rs haji medan", "haji medan", "rs haji"],
    "rs-128": ["imelda", "rs imelda", "imelda pekerja indonesia"],
    "rs-175": ["royal maternity", "maternity"],
    "rs-196": ["unprimdn", "uph", "rs unpri", "universitas prima indonesia"],
    "rs-168": ["prima husada", "rs prima husada"],
    "rs-205": ["herna", "rsu herna", "rs herna"],
    "rs-139": ["madani", "rs madani"],
    "rs-113": ["delima", "delima medan"],
    "rs-111": ["rs deli", "deli medan"],
    # --- Kota/kabupaten lain ---
    "rs-084": ["djoelham", "djoelham binjai", "rsud binjai", "rs binjai"],
    "rs-077": ["djasamen saragih", "rsud siantar", "rsud pematang siantar"],
    "rs-078": ["fl tobing", "rsud sibolga", "rsud fl tobing"],
    "rs-079": ["kumpulan pane", "rsud tebing tinggi", "rsud kumpulan pane"],
    "rs-085": ["tengku mansyur", "rsud tanjung balai", "rsud tengku mansyur"],
    "rs-101": ["rsud rantau prapat", "rsud rantauprapat", "rantau prapat"],
    "rs-104": ["rsud sidikalang", "sidikalang"],
    "rs-109": ["rsud tarutung", "tarutung"],
    "rs-090": ["rsud karo", "rsud kabanjahe", "kabanjahe"],
    "rs-127": ["hkbp balige", "rs balige", "balige"],
    "rs-094": ["rsud padang sidempuan", "rsud psp", "padangsidimpuan"],
    "rs-082": ["thomsen", "rsud gunungsitoli", "rsud nias", "thomsen nias"],
    "rs-073": ["bangun purba", "rsud bangun purba"],
    "rs-114": ["gerhard tobing", "rs gerhard", "rs gl tobing"],
}

# Kata yang diabaikan saat membentuk akronim otomatis.
GENERIK = {"rs", "rumah", "sakit"}

# Skor minimum agar sebuah RS dianggap cocok (0..1).
AMBANG = 0.6


# ---------------------------------------------------------------------------
# Normalisasi
# ---------------------------------------------------------------------------
def normalize(teks: str) -> str:
    """Huruf kecil, hapus tanda baca, rapikan spasi."""
    teks = teks.lower()
    teks = re.sub(r"[^a-z0-9\s]", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


def expand(teks: str) -> str:
    """Ganti tiap kata yang ada di kamus singkatan dengan bentuk panjangnya."""
    kata = normalize(teks).split()
    return " ".join(SINGKATAN.get(k, k) for k in kata)


# ---------------------------------------------------------------------------
# Skor kemiripan
# ---------------------------------------------------------------------------
def skor(query: str, nama: str) -> float:
    """Skor kemiripan 0..1: tiap kata query dicocokkan ke kata terdekat di nama."""
    q = expand(query).split()
    n = expand(nama).split()
    if not q or not n:
        return 0.0
    # potongan persis di awal kata -> skor penuh ("rsau" tidak lagi cocok ke "bersaudara")
    if (" " + " ".join(n)).find(" " + " ".join(q)) != -1:
        return 1.0
    total = 0.0
    for kata_q in q:
        total += max(difflib.SequenceMatcher(None, kata_q, kata_n).ratio() for kata_n in n)
    return total / len(q)


def akronim(nama: str) -> set[str]:
    """Akronim otomatis dari inisial kata di nama RS.

    Contoh: "RS Columbia Asia Medan" -> {"rcam", "cam", "rscam"}
    """
    kata = normalize(nama).split()
    if len(kata) < 2:
        return set()
    hasil = {"".join(k[0] for k in kata)}
    inti = [k for k in kata if k not in GENERIK]
    if len(inti) >= 2:
        ini = "".join(k[0] for k in inti)
        hasil.update({ini, "rs" + ini})
    return hasil


def tanpa_generik(query: str) -> str:
    """Buang kata generik (rs, rumah, sakit) dari query; kalau habis, pakai query asli."""
    kata = [k for k in expand(query).split() if k not in GENERIK]
    return " ".join(kata) if kata else query


def skor_rs(query: str, h: dict) -> float:
    """Skor gabungan satu RS: nama, alias manual, dan akronim otomatis."""
    s = skor(query, h["nama"])
    inti = tanpa_generik(query)
    for alias in ALIAS_RS.get(h["id"], []):
        s = max(s, skor(query, alias), skor(inti, alias))
    kunci = normalize(query).replace(" ", "")
    if kunci and kunci in akronim(h["nama"]):
        s = max(s, 0.95)  # di bawah alias manual (1.0) supaya alias menang kalau akronim bentrok
    return s


def rank(query: str, items: list[dict], ambang: float = AMBANG) -> list[dict]:
    """Urutkan RS berdasarkan kemiripan (alamat yang memuat query juga ikut lolos)."""
    nq = normalize(query)
    hasil = []
    for h in items:
        s = skor_rs(query, h)
        if nq and nq in normalize(h["alamat"]):
            s = max(s, 0.8)
        if s >= ambang:
            hasil.append((s, h))
    hasil.sort(key=lambda x: (-x[0], x[1]["nama"]))
    return [h for _, h in hasil]