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
    "rs-125": ["hermina", "hermina medan", "rs hermina", "hermna", "hermna medan", "hermina umum"],
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
def _token_fragment_score(query: str, target: str, allow_internal_fragment: bool = True) -> float:
    """Skor 0..1 untuk token query terhadap token target.

    - Token sama: 1.00
    - Awalan token (minimal 2 karakter): 0.94
    - Potongan di tengah token (minimal 2 karakter): 0.84 untuk 2 karakter,
      dan 0.88 untuk 3 karakter atau lebih.
    - Fuzzy typo hanya untuk token minimal 5 karakter.

    Batas minimum mencegah query satu huruf dan substring dua huruf yang terlalu
    umum menghasilkan terlalu banyak kecocokan palsu.
    """
    q = normalize(query)
    t = normalize(target)
    if not q or not t:
        return 0.0
    if q == t:
        return 1.0
    if len(q) >= 2 and t.startswith(q):
        return 0.94
    if allow_internal_fragment and len(q) >= 2 and q in t:
        # Fragmen 2 karakter diperbolehkan agar query seperti "djo"/"jo"
        # dapat mengenali Djoelham; skor lebih rendah untuk mengurangi false positive.
        return 0.84 if len(q) == 2 else 0.88
    if len(q) >= 5 and abs(len(q) - len(t)) <= 2:
        ratio = difflib.SequenceMatcher(None, q, t).ratio()
        if ratio >= 0.72:
            return ratio
    return 0.0


def _partial_text_score(query: str, target: str, allow_internal_fragment: bool = True) -> float:
    """Cocokkan seluruh token query dengan token pada teks target."""
    q_norm = normalize(query)
    t_norm = normalize(target)
    if not q_norm or not t_norm:
        return 0.0

    if q_norm == t_norm or q_norm.replace(" ", "") == t_norm.replace(" ", ""):
        return 1.0

    # Query multi-kata yang muncul berurutan tetap mendapat skor tertinggi.
    if f" {q_norm} " in f" {t_norm} ":
        return 1.0

    q_tokens = q_norm.split()
    t_tokens = t_norm.split()
    scores: list[float] = []

    for q_token in q_tokens:
        best = max(
            (
                _token_fragment_score(q_token, target_token, allow_internal_fragment)
                for target_token in t_tokens
            ),
            default=0.0,
        )
        if best == 0.0:
            return 0.0
        scores.append(best)

    return sum(scores) / len(scores) if scores else 0.0


def skor(query: str, nama: str, *, allow_internal_fragment: bool = True) -> float:
    """Skor kemiripan 0..1, termasuk prefix dan potongan kata."""
    q_norm = normalize(query)
    n_norm = normalize(nama)
    if not q_norm or not n_norm:
        return 0.0

    if q_norm == n_norm:
        return 1.0

    if q_norm.replace(" ", "") == n_norm.replace(" ", ""):
        return 1.0

    # Pertahankan pencocokan frasa utuh yang sudah digunakan sebelumnya.
    if f" {q_norm} " in f" {n_norm} ":
        return 1.0

    # Matching partial: contoh co/col -> Columbia, lum/bia -> Columbia.
    partial_score = _partial_text_score(q_norm, n_norm, allow_internal_fragment)

    # Tetap dukung ekspansi singkatan yang sudah ada.
    q_expanded = expand(q_norm)
    n_expanded = expand(n_norm)
    expanded_score = _partial_text_score(q_expanded, n_expanded, allow_internal_fragment)

    # Every query token must match. Dropping short words (e.g. "adam") made
    # "Adam Malik" score equally with "Abdul Malik" merely on "malik".
    return max(partial_score, expanded_score)


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


def _skor_nama_rs(query: str, h: dict) -> float:
    """Skor nama RS dari nama RDF, alias manual/otomatis, dan akronim."""
    qn = normalize(query)
    q_inti = tanpa_generik(query)

    s = skor(query, h.get("nama", ""))
    if q_inti and q_inti != query:
        s = max(s, skor(q_inti, h.get("nama", "")))

    aliases = get_all_aliases(h.get("id", ""), h.get("nama", ""))
    for alias in aliases:
        # Alias tanpa spasi umumnya hasil penggabungan otomatis (contoh matasiantar).
        # Hindari substring di tengah gabungan itu agar query "asia" tidak salah
        # cocok dengan "mata siantar"; prefix dan exact alias tetap didukung.
        allow_internal = " " in normalize(alias)
        s = max(s, skor(query, alias, allow_internal_fragment=allow_internal))
        if q_inti:
            s = max(s, skor(q_inti, alias, allow_internal_fragment=allow_internal))

    kunci = qn.replace(" ", "")
    if kunci and kunci in akronim(h.get("nama", "")):
        s = max(s, 0.95)

    return s


def skor_alamat(query: str, alamat: str) -> float:
    """Skor alamat yang sengaja dibatasi agar kalah dari kecocokan nama RS."""
    raw_score = _partial_text_score(query, alamat)
    if raw_score <= 0.0:
        return 0.0

    # Maksimum 0.78: hasil nama yang valid (partial mulai 0.88) selalu di atas alamat.
    return min(0.78, raw_score * 0.78)


def skor_rs(query: str, h: dict) -> float:
    """Skor satu RS dari nama/alias dan alamat; nama selalu berbobot lebih tinggi."""
    nama_score = _skor_nama_rs(query, h)
    alamat_score = skor_alamat(query, h.get("alamat", ""))
    return max(nama_score, alamat_score)


def rank(query: str, items: list[dict], ambang: float = AMBANG) -> list[dict]:
    """Urutkan hasil: kecocokan nama RS lebih dahulu, kemudian kecocokan alamat."""
    hasil: list[tuple[int, float, float, str, dict]] = []

    for h in items:
        nama_score = _skor_nama_rs(query, h)
        alamat_score = skor_alamat(query, h.get("alamat", ""))

        # Kandidat lolos jika cocok pada nama atau alamat.
        if max(nama_score, alamat_score) < ambang:
            continue

        # Seluruh kandidat yang cocok pada nama ditempatkan sebelum alamat-only.
        nama_priority = 0 if nama_score >= ambang else 1
        hasil.append((nama_priority, -nama_score, -alamat_score, h.get("nama", ""), h))

    hasil.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    return [item[-1] for item in hasil]
