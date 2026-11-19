"""Pencarian toleran typo & singkatan untuk nama rumah sakit.

Modul ini mendukung pencocokan nama berbasis regex, kamus singkatan,
alias manual tervalidasi, alias otomatis yang digenerasi dari nama RDF,
serta toleransi typo 1-2 karakter melalui SequenceMatcher.
"""
from __future__ import annotations

import difflib
import re
from typing import Any

# ---------------------------------------------------------------------------
# 1. Kamus singkatan umum -> bentuk panjang
# ---------------------------------------------------------------------------
SINGKATAN: dict[str, str] = {
    "rs": "rumah sakit",
    "rsu": "rumah sakit umum",
    "rsud": "rumah sakit umum daerah",
    "rsup": "rumah sakit umum pusat",
    "rsia": "rumah sakit ibu dan anak",
    "rsj": "rumah sakit jiwa",
    "rskb": "rumah sakit khusus bedah",
    "rsau": "rumah sakit angkatan udara",
    "ham": "haji adam malik",
    "tk": "tingkat",
    "st": "santa",
    "dr": "dokter",
    "prof": "profesor",
    "h": "haji",
    "al": "angkatan laut",
    "og": "original",
}

# ---------------------------------------------------------------------------
# 2. Alias manual per RS (48 entri tervalidasi terhadap RDF)
# ---------------------------------------------------------------------------
ALIAS_RS: dict[str, list[str]] = {
    # --- Medan & sekitarnya ---
    "rs-001": ["original hospital", "og", "og hospital", "orijinal hospital"],
    "rs-008": ["columbia asia", "columbia asia medan", "cam"],
    "rs-007": ["columbia asia aksara", "aksara"],
    "rs-083": ["pirngadi", "rsud pirngadi", "dr pirngadi", "rumah sakit pirngadi"],
    "rs-171": ["adam malik", "ham", "rsup ham", "rs haji adam malik", "rs adam malik"],
    "rs-176": ["royal prima", "rs royal", "royal"],
    "rs-177": ["royal prima marelan", "royal marelan"],
    "rs-125": ["hermina", "hermina medan", "rs hermina"],
    "rs-185": ["siloam", "siloam medan", "siloam dhirga surya", "rs siloam"],
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

GENERIK = {"rs", "rumah", "sakit", "umum", "daerah", "pusat", "khusus"}

PREFIX_WORDS = {
    "rs", "rsu", "rsud", "rsup", "rsia", "rsk", "rskb", "rsau", "uptd",
    "rumah", "sakit", "umum", "daerah", "pusat", "khusus", "pendidikan",
    "tingkat", "tk", "ii", "iii", "iv",
}
TITLE_WORDS = {"dr", "prof", "h", "hj", "rm", "kolonel", "letkol", "al"}
CITY_WORDS = {
    "medan", "binjai", "tebing", "tinggi", "pematang", "siantar",
    "sibolga", "tanjung", "balai", "gunungsitoli", "sumut", "sumatera", "utara",
}

AMBANG = 0.65


# ---------------------------------------------------------------------------
# Normalisasi & Ekspansi
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


def tanpa_generik(query: str) -> str:
    """Buang kata generik (rs, rumah, sakit, umum, daerah) dari query."""
    kata = [k for k in normalize(query).split() if k not in GENERIK]
    return " ".join(kata) if kata else query


# ---------------------------------------------------------------------------
# Auto-generate Alias dari token nama RDF
# ---------------------------------------------------------------------------
def generate_auto_aliases(nama: str) -> list[str]:
    """Generasi alias otomatis dari nama RS untuk semua 206 rumah sakit.
    
    Membuang awalan rumah sakit, umum, daerah, gelar, serta nama kota di ujung.
    Contoh: 'RS Umum Hermina Medan' -> ['hermina', 'hermina medan', 'rs hermina']
    """
    clean = normalize(nama)
    tokens = clean.split()
    if not tokens:
        return []

    aliases: set[str] = set()
    full_str = " ".join(tokens)
    aliases.add(full_str)

    i = 0
    while i < len(tokens) and tokens[i] in PREFIX_WORDS:
        i += 1
    while i < len(tokens) and tokens[i] in TITLE_WORDS:
        i += 1

    core = tokens[i:]
    if core:
        core_str = " ".join(core)
        aliases.add(core_str)
        aliases.add("rs " + core_str)

        # Buang nama kota di ujung jika ada
        if len(core) > 1 and core[-1] in CITY_WORDS:
            no_city = core[:-1]
            if len(no_city) > 1 and no_city[-1] in CITY_WORDS:
                no_city = no_city[:-1]
            if no_city:
                nc_str = " ".join(no_city)
                aliases.add(nc_str)
                aliases.add("rs " + nc_str)

        # Kata pertama dari core (mis. 'siloam' dari 'siloam dhirga surya')
        if len(core) > 1 and len(core[0]) >= 4 and core[0] not in CITY_WORDS:
            aliases.add(core[0])
            aliases.add("rs " + core[0])

    # Versi tanpa spasi (mis. 'adammalik', 'herminamedan')
    for a in list(aliases):
        aliases.add(a.replace(" ", ""))

    return sorted(aliases, key=lambda x: (len(x), x))


# ---------------------------------------------------------------------------
# Skor Kemiripan
# ---------------------------------------------------------------------------
def skor(query: str, nama: str) -> float:
    """Skor kemiripan 0..1 antara query dan nama."""
    q_norm = normalize(query)
    n_norm = normalize(nama)
    if not q_norm or not n_norm:
        return 0.0

    # Cocok persis
    if q_norm == n_norm:
        return 1.0

    # Cocok tanpa spasi persis (misal 'adammalik' == 'adam malik')
    if q_norm.replace(" ", "") == n_norm.replace(" ", ""):
        return 1.0

    # Substring whole words
    padded_n = f" {n_norm} "
    padded_q = f" {q_norm} "
    if padded_q in padded_n:
        return 1.0

    q_words = expand(q_norm).split()
    n_words = expand(n_norm).split()
    if not q_words or not n_words:
        return 0.0

    total = 0.0
    for qw in q_words:
        best_ratio = max(difflib.SequenceMatcher(None, qw, nw).ratio() for nw in n_words)
        total += best_ratio

    ratio_avg = total / len(q_words)
    # Full sequence ratio as backup
    full_ratio = difflib.SequenceMatcher(None, q_norm, n_norm).ratio()
    return max(ratio_avg, full_ratio)


def akronim(nama: str) -> set[str]:
    """Akronim otomatis dari inisial kata di nama RS."""
    kata = normalize(nama).split()
    if len(kata) < 2:
        return set()
    hasil = {"".join(k[0] for k in kata)}
    inti = [k for k in kata if k not in GENERIK]
    if len(inti) >= 2:
        ini = "".join(k[0] for k in inti)
        hasil.update({ini, "rs" + ini})
    return hasil


# Cache auto-aliases per rs_id
_AUTO_ALIAS_CACHE: dict[str, list[str]] = {}


def get_all_aliases(rs_id: str, nama: str) -> list[str]:
    """Ambil semua alias untuk RS (manual + auto-generated)."""
    if rs_id not in _AUTO_ALIAS_CACHE:
        manual = ALIAS_RS.get(rs_id, [])
        auto = generate_auto_aliases(nama)
        merged = list(dict.fromkeys(manual + auto))
        _AUTO_ALIAS_CACHE[rs_id] = merged
    return _AUTO_ALIAS_CACHE[rs_id]


def skor_rs(query: str, h: dict) -> float:
    """Skor kemiripan satu RS: nama asli, alias manual & otomatis, dan akronim."""
    qn = normalize(query)
    q_inti = tanpa_generik(query)

    s = skor(query, h["nama"])
    if q_inti and q_inti != query:
        s = max(s, skor(q_inti, h["nama"]))

    # Periksa seluruh alias (manual & otomatis)
    aliases = get_all_aliases(h.get("id", ""), h.get("nama", ""))
    for alias in aliases:
        s = max(s, skor(query, alias))
        if q_inti:
            s = max(s, skor(q_inti, alias))

    # Cocokkan akronim
    kunci = qn.replace(" ", "")
    if kunci and kunci in akronim(h["nama"]):
        s = max(s, 0.95)

    return s


def rank(query: str, items: list[dict], ambang: float = AMBANG) -> list[dict]:
    """Urutkan RS berdasarkan kemiripan nama/alias."""
    nq = normalize(query)
    hasil: list[tuple[float, dict]] = []
    for h in items:
        s = skor_rs(query, h)
        if nq and nq in normalize(h.get("alamat", "")):
            s = max(s, 0.8)
        if s >= ambang:
            hasil.append((s, h))
    hasil.sort(key=lambda x: (-x[0], x[1]["nama"]))
    return [h for _, h in hasil]
