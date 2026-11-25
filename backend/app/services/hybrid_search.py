"""Read-only hybrid semantic search: bounded parsing, SKOS/OWL graph evidence, deterministic ranking.

No medical inference or patient database access. Graph snapshot cache expires after 30 seconds.
"""
from __future__ import annotations

import asyncio
import difflib
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException

from app.services import sirs, sparql_service as sp
from app.services.fuzzy_search import ALIAS_RS, generate_auto_aliases
from app.services.operating_hours import day_indexes
from app.services.specialty_service import (
    ALL_ACTIVE_SPECIALTIES,
    SYNONYM_MAP,
    sirs_specialty_pattern,
)

E = "http://carisehat.id/graph/enrichment/2026-11-20"
F = "http://carisehat.id/graph/search/facilities/2026-11-25"
C = "http://carisehat.id/graph/search/concepts/2026-11-25"
CS = sirs.CS
try:
    WIB = ZoneInfo("Asia/Jakarta")
except ZoneInfoNotFoundError:
    WIB = timezone(timedelta(hours=7))
TTL = 30
_cache = None
_lock = asyncio.Lock()

# Medical and hospital acronyms that must NEVER be fuzzy-substituted into another acronym
NO_FUZZY = {
    "icu", "nicu", "picu", "hcu", "iccu", "igd", "ugd",
    "rsia", "rsud", "rsup", "rsu", "rsj", "mri", "ct", "usg", "tht", "bpjs",
}

STOP_WORDS = {
    "rumah", "sakit", "cari", "saya", "mau", "mencari", "yang", "punya",
    "dengan", "ada", "dokter", "layanan", "poli", "di", "dan", "atau",
    "bukan", "tanpa", "selain", "memiliki", "menyediakan", "tetapi", "rs", "kelas",
    "berada", "wilayah", "daerah", "buka", "hari", "jam", "sampai",
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^\w\s()]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def compact_initials(text: str) -> str:
    """Join consecutive single-letter tokens (e.g. 'jl a h nasution' -> 'jl ah nasution')."""
    tokens = text.split()
    out: list[str] = []
    i = 0
    while i < len(tokens):
        if len(tokens[i]) == 1 and tokens[i].isalpha():
            buf = [tokens[i]]
            j = i + 1
            while j < len(tokens) and len(tokens[j]) == 1 and tokens[j].isalpha():
                buf.append(tokens[j])
                j += 1
            out.append("".join(buf))
            i = j
        else:
            out.append(tokens[i])
            i += 1
    return " ".join(out)


def lit(value: str) -> str:
    return sp.lit(str(value))


@dataclass(frozen=True)
class Atom:
    field: str
    value: str
    start: int = 0
    end: int = 0
    label: str = ""


BASE = """SELECT ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?pemilik ?lat ?lon ?sumberKoordinat ?bpjs
WHERE {
 ?rs a hf:RumahSakit; schema:name ?nama; hf:jenis ?jenis; hf:kelas ?kelas; hf:alamat ?alamat; hf:beradaDiKabupatenKota/rdfs:label ?kabkota .
 OPTIONAL {?rs schema:telephone ?telepon} OPTIONAL {?rs hf:pemilik ?pemilik}
 OPTIONAL {?rs geo:lat ?lat; geo:long ?lon} OPTIONAL {?rs hf:sumberKoordinat ?sumberKoordinat}
 OPTIONAL {?rs hf:menerimaBPJS ?bpjs}
} ORDER BY ?rs"""

FACTS = f"""SELECT ?rs ?kind ?value WHERE {{
 {{ {sirs.pattern('?value')} BIND("service" AS ?kind) }}
 UNION {{ GRAPH <{sirs.GRAPH_URI}> {{?rs <{CS.catatanPelayanan}> ?o . ?o <{CS.labelPelayanan}> ?value}} BIND("label" AS ?kind) }}
 UNION {{ GRAPH <{E}> {{?rs <{CS.kodeRegistrasiKemenkes}> ?value}} BIND("code" AS ?kind) }}
 UNION {{ GRAPH <{F}> {{?rs hf:memilikiFasilitasDiagnostik ?value}} BIND("diagnostic" AS ?kind) }}
 UNION {{ GRAPH <{F}> {{?rs hf:fasilitasKritis ?f . ?f <{CS.jenisFasilitas}> ?value; <{CS.kapasitasTerlapor}> ?cap . FILTER(?cap > 0)}} BIND("critical" AS ?kind) }}
 UNION {{ ?rs schema:image ?value BIND("photo" AS ?kind) }}
}}"""

HOURS = f"""SELECT ?rs ?unit ?days ?opens ?closes WHERE {{ GRAPH <{E}> {{
 ?rs schema:openingHoursSpecification ?o . ?o rdfs:label ?unit; schema:description ?days; schema:opens ?opens; schema:closes ?closes .
}}}}"""

CONCEPTS = f"""PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?pref ?alt ?narrowerPref WHERE {{ GRAPH <{C}> {{
 ?c a skos:Concept ; skos:prefLabel ?pref .
 OPTIONAL {{ ?c skos:altLabel ?alt }}
 OPTIONAL {{ ?c skos:narrower ?n . ?n skos:prefLabel ?narrowerPref }}
}}}}"""


async def snapshot():
    global _cache
    if _cache and time.monotonic() - _cache["time"] < TTL:
        return _cache
    async with _lock:
        if _cache and time.monotonic() - _cache["time"] < TTL:
            return _cache
        base, facts, hours, concepts = await asyncio.gather(
            sp.select(BASE), sp.select(FACTS), sp.select(HOURS), sp.select(CONCEPTS)
        )
        rows = {r["rs"]: dict(r) for r in base}
        labels, services, diagnostics, criticals = set(), set(), set(), set()
        for r in rows.values():
            r.update(
                services=set(),
                photos=set(),
                codes=set(),
                diagnostics=set(),
                criticals=set(),
                hours=[],
            )
        for f in facts:
            if f["rs"] not in rows:
                continue
            r = rows[f["rs"]]
            k, v = f["kind"], f["value"]
            if k == "label":
                labels.add(v)
                if v in ALL_ACTIVE_SPECIALTIES:
                    r["services"].add(v)
                    services.add(v)
            elif k == "service":
                r["services"].add(v)
                services.add(v)
            elif k == "diagnostic":
                r["diagnostics"].add(v)
                diagnostics.add(v)
            elif k == "critical":
                r["criticals"].add(v)
                criticals.add(v)
            elif k == "photo":
                r["photos"].add(v)
            elif k == "code":
                r["codes"].add(v)
        for h in hours:
            if h["rs"] in rows:
                rows[h["rs"]]["hours"].append(h)

        # Build SKOS concept hierarchy & altLabels from Fuseki named graph
        concept_children: dict[str, list[str]] = {}
        skos_alts: dict[str, str] = {}
        for row in concepts:
            pref = row["pref"]
            if row.get("alt"):
                skos_alts[norm(row["alt"])] = pref
            if row.get("narrowerPref"):
                concept_children.setdefault(norm(pref), [])
                if row["narrowerPref"] not in concept_children[norm(pref)]:
                    concept_children[norm(pref)].append(row["narrowerPref"])

        vocabulary: dict[str, tuple[str, str]] = {}

        def add(term: str, field: str, value: str):
            nt = norm(term)
            if nt:
                vocabulary[nt] = (field, value)

        # Regions (33 Kab/Kota)
        for region in sorted({r["kabkota"] for r in rows.values()}):
            add(region, "region", region)
            short = re.sub(r"^(Kota|Kabupaten|Kab\.)\s+", "", region)
            add(short, "region", region)
            if region.startswith("Kab. "):
                add("kabupaten " + short, "region", region)
            if "Siantar" in region:
                for x in ["siantar", "p siantar", "pematangsiantar"]:
                    add(x, "region", region)
            if "Padang" in region and "Sidempuan" in region:
                for x in ["padangsidimpuan", "padang sidimpuan", "psp"]:
                    add(x, "region", region)
            if "Tanjung Balai" in region:
                add("tanjungbalai", "region", region)
            if "Gunungsitoli" in region:
                add("gunung sitoli", "region", region)
            if "Toba Samosir" in region:
                add("toba", "region", region)
            if "Labuhan Batu" in region:
                add(short.lower().replace("labuhan batu", "labuhanbatu"), "region", region)
        add("kepulauan nias", "region_group", "kepulauan_nias")

        # Services & Specialties (SIRS + Curated 16 + SKOS altLabels)
        for label in sorted(labels | set(ALL_ACTIVE_SPECIALTIES)):
            if label in services:
                add(label, "service", label)
        for alias, label in SYNONYM_MAP.items():
            if label in services or label in ALL_ACTIVE_SPECIALTIES:
                add(alias, "service", label)

        # Facilities & Diagnostics (Evidence graph + SKOS altLabels)
        fac_aliases = {
            "cuci darah": "Hemodialisis",
            "hemodialisa": "Hemodialisis",
            "laboratorium": "Laboratorium Klinik",
            "lab": "Laboratorium Klinik",
            "lab klinik": "Laboratorium Klinik",
            "apotek": "Instalasi Farmasi",
            "farmasi": "Instalasi Farmasi",
            "rontgen": "Radiologi",
            "radiografi": "Radiologi",
            "x ray": "Radiologi",
            "xray": "Radiologi",
            "kamar operasi": "Kamar Bedah / Operasi",
            "kamar bedah": "Kamar Bedah / Operasi",
            "ultrasonografi": "USG",
        }
        for label in sorted(diagnostics):
            add(label, "facility", label)
        for alias, label in fac_aliases.items():
            if label in diagnostics:
                add(alias, "facility", label)
        for key in ["ICU", "NICU", "PICU", "HCU", "ICCU", "Ventilator", "MRI"]:
            add(key, "facility", key)
        for term in ["igd 24 jam", "ugd 24 jam", "igd", "ugd", "gawat darurat", "darurat 24 jam"]:
            add(term, "service", sirs.EMERGENCY)

        # Broader SKOS concepts
        for cname in [
            "pencitraan medis",
            "perawatan intensif",
            "layanan kesehatan anak",
            "kesehatan ibu dan kandungan",
            "pemeriksaan laboratorium",
        ]:
            add(cname, "concept", cname)
        for alt_norm, pref in skos_alts.items():
            if norm(pref) in concept_children and alt_norm not in vocabulary:
                add(alt_norm, "concept", norm(pref))

        # Hospital types, ownership, province
        for term in ["rsia", "rumah sakit ibu dan anak", "rs ibu dan anak", "ibu dan anak"]:
            add(term, "type", "RSIA")
        for term in ["rsud", "rsup", "rsu"]:
            add(term, "type", term.upper())
        for term in ["rumah sakit umum", "rs umum"]:
            add(term, "type", "Umum")
        for term in ["rumah sakit khusus", "rs khusus"]:
            add(term, "type", "Khusus")
        for term in ["pemerintah", "swasta", "tni", "polri", "rs tni", "rs polri"]:
            add(term, "owner", term.replace("rs ", ""))
        for term in ["sumatera utara", "sumut"]:
            add(term, "province", "Sumatera Utara")

        # Collect hospital name tokens (to prevent false-positive region fuzzy corrections like Medka->Medan)
        hospital_tokens: set[str] = set()
        generic_h = {"rs", "rsup", "rsu", "rsud", "rsia", "rumah", "sakit", "umum", "khusus", "daerah", "pusat", "h", "dr", "prof"}
        for r in rows.values():
            for tok in norm(r["nama"]).split():
                if len(tok) >= 4 and tok not in generic_h:
                    hospital_tokens.add(tok)

        _cache = {
            "time": time.monotonic(),
            "rows": rows,
            "vocab": vocabulary,
            "services": services,
            "labels": labels,
            "diagnostics": diagnostics,
            "concept_children": concept_children,
            "hospital_tokens": hospital_tokens,
        }
        return _cache


def damerau_levenshtein(a: str, b: str) -> int:
    la, lb = len(a), len(b)
    if abs(la - lb) > 3:
        return 99
    d = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        d[i][0] = i
    for j in range(lb + 1):
        d[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[la][lb]


def similarity(q: str, t: str) -> float:
    if q == t:
        return 1.0
    if q in NO_FUZZY or t in NO_FUZZY:
        return 0.0
    if len(q) >= 3 and t.startswith(q):
        return 0.94
    if len(q) >= 4 and len(t) >= 4 and abs(len(q) - len(t)) <= 2:
        seq = difflib.SequenceMatcher(None, q, t).ratio()
        dl = damerau_levenshtein(q, t)
        dl_ratio = 1.0 - (dl / max(len(q), len(t)))
        return max(seq, dl_ratio)
    return 0.0


def name_score(q: str, r: dict) -> float:
    n = norm(r["nama"])
    ident = r["rs"].rsplit("/", 1)[-1]
    aliases = (
        [n]
        + [norm(x) for x in ALIAS_RS.get(ident, [])]
        + [norm(x) for x in generate_auto_aliases(r["nama"])]
    )
    if ident == "rs-171":
        aliases += ["rsham", "rsup ham", "rs adam malik"]
    if ident == "rs-003":
        aliases += ["rs bhayangkara", "bhayangkara"]
    if q in r["codes"]:
        return 990.0
    if q == n or compact_initials(q) == compact_initials(n):
        return 1000.0
    if q in aliases:
        return 980.0
    generic = {"rs", "rsup", "rsu", "rsud", "rsia", "rumah", "sakit", "umum", "h", "haji", "dr", "dokter"}
    qt = [t for t in q.split() if t not in generic]
    if not qt:
        return 0.0
    best = 0.0
    for alias in aliases:
        tokens = alias.split()
        scores = [max((similarity(t, u) for u in tokens), default=0.0) for t in qt]
        exact = all(t in tokens for t in qt)
        min_req = 0.75 if exact else 0.84
        if scores and min(scores) >= min_req:
            prefix = alias.startswith(q)
            base = 925.0 if prefix else 900.0 if exact else 700.0
            best = max(best, base + sum(scores) / len(scores) * 50.0)
    if best:
        return best

    # Secondary match: address (with compact initials for 'Jl. A.H. Nasution'), ownership, region
    addr_norm = norm(r.get("alamat", ""))
    addr_compact = compact_initials(addr_norm)
    target_tokens = set((addr_norm + " " + addr_compact + " " + norm(r.get("pemilik", "")) + " " + norm(r.get("kabkota", ""))).split())
    qt_addr = [t for t in qt if t not in {"di", "jalan", "jl"}]
    if qt_addr and all(t in target_tokens for t in qt_addr):
        return 300.0
    if qt_addr and all(max((similarity(t, u) for u in target_tokens), default=0.0) >= 0.84 for t in qt_addr):
        return 250.0
    return 0.0


def _parse_hours_atom(text: str, place):
    days_re = r"(senin|selasa|rabu|kamis|jumat|sabtu|minggu)"
    hm = re.search(r"\b(poliklinik|poli|pendaftaran|reguler|layanan)\b.*?\b" + days_re + r"\b", text)
    if hm:
        u = hm[1]
        unit = "pendaftaran" if u == "pendaftaran" else "poliklinik" if u in ("poli", "poliklinik") else "any" if u == "layanan" else "reguler"
        # A specialty between the unit and day ("poli anak ... Sabtu") is
        # an independent mandatory condition; do not consume its text span.
        middle = text[hm.end(1):hm.start(2)]
        medical_terms = re.sub(r'\b(yang|dan|buka|hari|pada)\b', '', middle).strip()
        span = (hm.start(2), hm.end(2)) if medical_terms else hm.span()
        place("hours", f"day:{unit}:{hm[2]}", *span)
        return None
    generic_day = re.search(r'\bbuka\s+hari\s+' + days_re + r'\b', text)
    if generic_day:
        place('hours', f'day:any:{generic_day[1]}', *generic_day.span())
        return None
    # "poli yang buka sampai jam 8 malam" or "sampai jam 20 00" / "sampai jam 20"
    cm = re.search(r"\b(?:poliklinik|poli)?\s*(?:yang\s+)?buka\s+sampai\s+jam\s+(\d{1,2})(?:\s+(\d{2}))?\s*(malam|sore|siang|pagi)?\b", text)
    if cm:
        hr = int(cm[1])
        mn = int(cm[2] or 0)
        period = cm[3] or ""
        if period in ("malam", "sore") and hr < 12:
            hr += 12
        place("hours", f"closes_ge:poliklinik:{hr:02d}:{mn:02d}", *cm.span())
        return None
    pm = re.search(r"\bpendaftaran\s+pagi\b", text)
    if pm:
        place("hours", "morning:pendaftaran", *pm.span())
        return None
    bm = re.search(r"\bbuka\s+sekarang\b", text)
    if bm:
        place("hours", "open_now", *bm.span())
        return "Status 'buka sekarang' dihitung berdasarkan jadwal unit tercatat (WIB), bukan ketersediaan real-time."
    if re.search(r"\bsampai jam\b", text):
        return "Format jam tidak dikenali. Gunakan contoh: 'buka sampai jam 8 malam'."
    return None


def parse(q: str, snap: dict):
    text = norm(q)
    atoms: list[Atom] = []
    corrections: list[dict] = []
    notices: list[str] = []
    did_you_mean: list[str] = []

    if not q or not q.strip():
        return None, [], [], [], []
    if len(q) > 240:
        raise HTTPException(422, "Pencarian maksimal 240 karakter.")
    # Reject SPARQL / REGEX / XSS injection payloads safely BEFORE norm() strips punctuation
    if re.search(r'[<>"\\{}\[\]*+$^|;()\']', q) or re.search(r"\b(select|union|where|insert|delete|drop|construct)\b", text):
        return ("none",), [], [], ["Masukkan nama rumah sakit, wilayah, layanan, atau fasilitas yang valid."], []
    if not text:
        return ("none",), [], [], ["Masukkan nama rumah sakit, wilayah, layanan, atau fasilitas yang valid."], []

    # Exact full hospital name or Kemenkes code wins immediately
    exact = [
        r for r in snap["rows"].values()
        if text == norm(r["nama"]) or compact_initials(text) == compact_initials(norm(r["nama"])) or text in r["codes"]
    ]
    if exact:
        return ("text", text), [], [], [], []

    occupied: list[tuple[int, int]] = []

    def place(field: str, value: str, start: int, end: int, label: str = "") -> bool:
        if any(start < b and end > a for a, b in occupied):
            return False
        atoms.append(Atom(field, value, start, end, label or text[start:end]))
        occupied.append((start, end))
        return True

    # Expand omitted class keyword: "kelas A atau B" -> "kelas A atau kelas B"
    text = re.sub(r"\bkelas ([abcd]) atau ([abcd])\b", r"kelas \1 atau kelas \2", text)
    for m in re.finditer(r"\bkelas\s+([abcd])\b", text):
        place("class", m[1].upper(), *m.span())

    # Operating hours extraction
    hr_notice = _parse_hours_atom(text, place)
    if hr_notice:
        notices.append(hr_notice)

    # 1. Exact multi-word vocabulary matches (>= 2 words) FIRST
    for term, (field, value) in sorted(snap["vocab"].items(), key=lambda x: -len(x[0])):
        if " " not in term:
            continue
        for m in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text):
            place(field, value, *m.span())

    # 2. Fuzzy 2-word vocabulary matches BEFORE 1-word exact (fixes "Pematng Siantar", "Deli Serdng")
    words = list(re.finditer(r"\b\w+\b", text))
    for i in range(len(words) - 1):
        chunk = words[i : i + 2]
        a, b = chunk[0].start(), chunk[-1].end()
        term = text[a:b]
        if any(a < y and b > x for x, y in occupied) or any(w[0] in STOP_WORDS for w in chunk):
            continue
        if any(w[0] in NO_FUZZY for w in chunk):
            continue
        candidates = []
        for v, (field, value) in snap["vocab"].items():
            if field not in ("region", "service", "facility") or len(v.split()) != 2:
                continue
            score = similarity(term, v)
            if score >= 0.78:
                candidates.append((score, v, field, value))
        candidates.sort(reverse=True)
        if candidates and (len(candidates) == 1 or candidates[0][3] == candidates[1][3] or candidates[0][0] - candidates[1][0] >= 0.08):
            _, v, field, value = candidates[0]
            if place(field, value, a, b):
                corrections.append({"from": term, "to": v})

    # 3. Exact 1-word vocabulary matches
    for term, (field, value) in sorted(snap["vocab"].items(), key=lambda x: -len(x[0])):
        if " " in term:
            continue
        for m in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text):
            place(field, value, *m.span())

    # 4. Fuzzy 1-word vocabulary matches (skip hospital name tokens like 'medka' when matching 'medika')
    has_hospital_word = any(w[0] in snap["hospital_tokens"] for w in words)
    for w in words:
        a, b = w.start(), w.end()
        term = w[0]
        if any(a < y and b > x for x, y in occupied) or term in STOP_WORDS or term in NO_FUZZY:
            continue
        if len(term) < 4:
            continue
        # If query already contains a hospital name token and this word fuzzy-matches a hospital token better, don't hijack as region
        best_h_score = max((similarity(term, ht) for ht in snap["hospital_tokens"]), default=0.0) if has_hospital_word else 0.0
        candidates = []
        for v, (field, value) in snap["vocab"].items():
            if field not in ("region", "service", "facility") or " " in v or len(v) < 4:
                continue
            score = similarity(term, v)
            if score >= 0.78:
                candidates.append((score, v, field, value))
        candidates.sort(reverse=True)
        if candidates:
            top_score, v, field, value = candidates[0]
            if best_h_score > top_score:
                continue
            if len(candidates) == 1 or candidates[0][3] == candidates[1][3] or candidates[0][0] - candidates[1][0] >= 0.08:
                if place(field, value, a, b):
                    corrections.append({"from": term, "to": v})
            else:
                # Ambiguous fuzzy match: never auto-correct silently
                did_you_mean.extend([c[1] for c in candidates[:3]])

    atoms.sort(key=lambda a: a.start)

    # Remove recognized atoms & narrative filler, preserving logical operators
    rest = list(text)
    for a in atoms:
        rest[a.start : a.end] = " " * (a.end - a.start)
    residual = "".join(rest)
    residual = re.sub(
        r"\b(?:rumah sakit|rs|cari|saya|mau|mencari|yang|punya|dengan|ada|dokter|layanan|poli|di|dan|atau|bukan|tanpa|selain|memiliki|menyediakan|tetapi|berada|buka|hari|jam|sampai|malam|pagi)\b",
        " ",
        residual,
    )
    residual = norm(residual).replace("(", "").replace(")", "").strip()

    if not atoms:
        return ("text", text), [], [], notices, list(dict.fromkeys(did_you_mean))

    if "(" in text or ")" in text:
        return ("none",), atoms, corrections, ["Gunakan kondisi tanpa tanda kurung; pengelompokan bertingkat belum didukung."], []

    nodes = []
    operators = []
    for i, a in enumerate(atoms):
        gap = text[atoms[i - 1].end if i else 0 : a.start]
        neg = bool(re.search(r"\b(bukan|tanpa|selain|not)\b", gap))
        if neg and a.field in ("service", "facility", "concept", "hours"):
            notices.append("Data yang tidak tercatat bukan bukti layanan tidak tersedia. Pencarian negatif layanan belum didukung.")
            return ("none",), atoms, corrections, notices, []
        node: tuple = ("atom", a)
        if neg:
            node = ("not", node)
        if i:
            operators.append("or" if re.search(r"\b(atau|or)\b", gap) else "and")
        nodes.append(node)

    def _node_field(n) -> str | None:
        if n[0] == "atom":
            return n[1].field
        if n[0] == "not":
            return _node_field(n[1])
        if n[0] == "or":
            return _node_field(n[1])
        return None

    # Group ALL consecutive OR chains on the same field first (e.g. "jantung atau saraf dengan icu atau nicu")
    i = 0
    while i < len(operators):
        if operators[i] == "or" and _node_field(nodes[i]) == _node_field(nodes[i + 1]):
            nodes[i : i + 2] = [("or", nodes[i], nodes[i + 1])]
            operators.pop(i)
        else:
            i += 1
    while "and" in operators:
        idx = operators.index("and")
        nodes[idx : idx + 2] = [("and", nodes[idx], nodes[idx + 1])]
        operators.pop(idx)
    while operators:
        nodes[0:2] = [("or", nodes[0], nodes[1])]
        operators.pop(0)

    tree = nodes[0]
    if residual:
        tree = ("and", tree, ("text", residual))
    for a in atoms:
        if a.field == "service" and a.value not in snap["services"]:
            notices.append("Layanan ini belum memiliki catatan yang layak ditampilkan dalam pencarian.")
    return tree, atoms, corrections, list(dict.fromkeys(notices)), list(dict.fromkeys(did_you_mean))


def atom_expr(a: Atom, index: int, snap: dict) -> str:
    v = lit(a.value)
    field = a.field
    suf = str(index)
    if field == "class":
        return f"?kelas = {v}"
    if field == "type":
        if a.value in ("Umum", "Khusus"):
            return f"?jenis = {v}"
        if a.value == "RSIA":
            return 'REGEX(STR(?nama), "^(RSIA|RS\\\\s+Ibu\\\\s+dan\\\\s+Anak|Rumah\\\\s+Sakit\\\\s+Ibu\\\\s+dan\\\\s+Anak)(\\\\s|$)", "i")'
        if a.value == "RSUD":
            return 'REGEX(STR(?nama), "^(RSUD|RS\\\\s+Umum\\\\s+Daerah)(\\\\s|$)", "i")'
        if a.value == "RSUP":
            return 'REGEX(STR(?nama), "^(RSUP|RS\\\\s+Umum\\\\s+Pusat)(\\\\s|$)", "i")'
        if a.value == "RSU":
            return '(?jenis = "Umum" || REGEX(STR(?nama), "^(RSU|RS\\\\s+Umum)(\\\\s|$)", "i"))'
        return "REGEX(STR(?nama), " + lit(r"^" + re.escape(a.value) + r"(\s|$)") + ', "i")'
    if field == "region":
        return f"?kabkota = {v}"
    if field == "region_group":
        if a.value == "kepulauan_nias":
            vals = " ".join(lit(x) for x in ["Kab. Nias", "Kab. Nias Barat", "Kab. Nias Selatan", "Kab. Nias Utara", "Kota Gunungsitoli"])
            return f"(?kabkota IN ({', '.join(lit(x) for x in ['Kab. Nias', 'Kab. Nias Barat', 'Kab. Nias Selatan', 'Kab. Nias Utara', 'Kota Gunungsitoli'])}))"
        return "false"
    if field == "province":
        return "true"
    if field == "owner":
        maps = {
            "pemerintah": ["Pemkab", "Pemkot", "Pemprop", "Kemkes", "Kementerian", "TNI", "POLRI"],
            "swasta": ["Perusahaan", "Swasta", "Organisasi", "Yayasan", "Perorangan"],
            "tni": ["TNI"],
            "polri": ["POLRI"],
        }
        return "(" + " || ".join("CONTAINS(LCASE(STR(?pemilik)), " + lit(t.lower()) + ")" for t in maps[a.value]) + ")"
    if field == "service":
        if a.value in ALL_ACTIVE_SPECIALTIES:
            return "EXISTS { " + sirs_specialty_pattern(a.value, "?rs", "?obs" + suf) + " }"
        return "EXISTS { " + sirs.pattern(v, "?obs" + suf) + " }"
    if field == "facility":
        low = a.value.lower()
        if low in ["icu", "nicu", "picu", "hcu", "iccu", "ventilator"]:
            keys = [low + "_dengan_ventilator", low + "_tanpa_ventilator"] if low in ["icu", "nicu", "picu"] else [low]
            if low == "ventilator":
                keys = [x + "_dengan_ventilator" for x in ["icu", "nicu", "picu"]]
            values = " ".join(lit(k) for k in keys)
            return (
                f"EXISTS {{ GRAPH <{F}> {{ ?rs hf:fasilitasKritis ?f{suf} . "
                f"?f{suf} <{CS.jenisFasilitas}> ?k{suf}; <{CS.kapasitasTerlapor}> ?cap{suf}; schema:citation ?src{suf} . "
                f"VALUES ?k{suf} {{ {values} }} FILTER(?cap{suf}>0) }} }}"
            )
        return (
            f"EXISTS {{ {{ GRAPH <{F}> {{ ?rs hf:memilikiFasilitasDiagnostik {v}; schema:citation ?src{suf} }} }} "
            f"UNION {{ {sirs.pattern(v, '?obs' + suf)} }} }}"
        )
    if field == "concept":
        children = snap["concept_children"].get(a.value, [])
        if not children:
            return "(1 = 0)"
        exprs = []
        for j, child_label in enumerate(children):
            cfield = "service" if child_label in ALL_ACTIVE_SPECIALTIES else "facility"
            exprs.append(atom_expr(Atom(cfield, child_label), index * 20 + j + 1, snap))
        return "(" + " || ".join(exprs) + ")"
    if field == "hours":
        parts = a.value.split(":")
        mode = parts[0]
        ids = []
        if mode == "day":
            _, unit, day = parts
            target_day = day_indexes(day)[0]
            for uri, r in snap["rows"].items():
                for h in r["hours"]:
                    if unit != "any" and unit not in norm(h["unit"]):
                        continue
                    if target_day not in day_indexes(h["days"]):
                        continue
                    if re.fullmatch(r"\d{2}:\d{2}", h["opens"]) and re.fullmatch(r"\d{2}:\d{2}", h["closes"]) and h["opens"] != h["closes"]:
                        ids.append(uri)
                        break
        elif mode == "closes_ge":
            _, unit, hh, mm = parts
            target_time = f"{hh}:{mm}"
            for uri, r in snap["rows"].items():
                for h in r["hours"]:
                    if unit not in norm(h["unit"]):
                        continue
                    if re.fullmatch(r"\d{2}:\d{2}", h["closes"]) and h["closes"] >= target_time:
                        ids.append(uri)
                        break
        elif mode == "morning":
            unit = parts[1]
            for uri, r in snap["rows"].items():
                for h in r["hours"]:
                    if unit not in norm(h["unit"]):
                        continue
                    if re.fullmatch(r"\d{2}:\d{2}", h["opens"]) and h["opens"] <= "08:30":
                        ids.append(uri)
                        break
        elif mode == "open_now":
            now = datetime.now(WIB)
            cur_day = now.weekday()
            cur_hm = now.strftime("%H:%M")
            for uri, r in snap["rows"].items():
                for h in r["hours"]:
                    if cur_day not in day_indexes(h["days"]):
                        continue
                    if re.fullmatch(r"\d{2}:\d{2}", h["opens"]) and re.fullmatch(r"\d{2}:\d{2}", h["closes"]):
                        if h["opens"] <= cur_hm < h["closes"]:
                            ids.append(uri)
                            break
        return id_expr(ids)
    return "(1 = 0)"


def id_expr(ids: list[str]) -> str:
    safe = [x for x in ids if re.fullmatch(r"https?://[A-Za-z0-9.:_-]+/rs/rs-\d{3}", x)]
    return "?rs IN (" + ", ".join("<" + x + ">" for x in safe) + ")" if safe else "(1 = 0)"


def compile_tree(tree, snap: dict, scores: dict, counter: list[int]) -> str:
    if tree is None:
        return "true"
    op = tree[0]
    if op == "none":
        return "(1 = 0)"
    if op == "atom":
        counter[0] += 1
        return atom_expr(tree[1], counter[0], snap)
    if op == "not":
        return "!(" + compile_tree(tree[1], snap, scores, counter) + ")"
    if op in ("and", "or"):
        return (
            "("
            + compile_tree(tree[1], snap, scores, counter)
            + (" && " if op == "and" else " || ")
            + compile_tree(tree[2], snap, scores, counter)
            + ")"
        )
    if op == "text":
        matched = []
        for uri, r in snap["rows"].items():
            score = name_score(tree[1], r)
            if score:
                matched.append(uri)
                scores[uri] = max(scores.get(uri, 0.0), score)
        return id_expr(matched)
    return "(1 = 0)"


def _suggest_corrections_for_empty(q: str, snap: dict) -> list[str]:
    text = norm(q)
    if not text or len(text) < 3:
        return []
    candidates = []
    for r in snap["rows"].values():
        n = norm(r["nama"])
        tokens = [t for t in n.split() if len(t) >= 4]
        for qtok in text.split():
            if len(qtok) < 4 or qtok in NO_FUZZY:
                continue
            for tok in tokens:
                s = similarity(qtok, tok)
                if s >= 0.78:
                    candidates.append((s, r["nama"]))
    for term in snap["vocab"]:
        if len(term) >= 4 and term not in NO_FUZZY:
            s = similarity(text, term)
            if s >= 0.75:
                candidates.append((s, term))
    candidates.sort(key=lambda x: -x[0])
    return list(dict.fromkeys(c[1] for c in candidates[:3]))


async def search(
    q: str = "",
    kelas: str = "",
    jenis: str = "",
    kabkota: str = "",
    layanan: str = "",
    spesialisasi: str = "",
    fasilitas: str = "",
    limit: int = 50,
    offset: int = 0,
    omit: str = "",
    planned_tree=None,
):
    snap = await snapshot()
    tree, atoms, corrections, notices, did_you_mean = parse(q, snap)
    # Internal validated conversation plan; never exposed as a public query argument.
    if planned_tree is not None:
        tree = planned_tree
    if omit:
        omitted = set(omit.split("|"))

        def prune(t):
            if not t:
                return None
            if t[0] == "atom" and f"{t[1].start}:{t[1].end}" in omitted:
                return None
            if t[0] in ("and", "or"):
                a, b = prune(t[1]), prune(t[2])
                return (t[0], a, b) if a and b else a or b
            if t[0] == "not":
                a = prune(t[1])
                return ("not", a) if a else None
            return t

        tree = prune(tree)

    for field, value in [
        ("class", kelas),
        ("type", jenis),
        ("region", kabkota),
        ("service", layanan or spesialisasi),
        ("facility", fasilitas),
    ]:
        if not value:
            continue
        mapped = snap["vocab"].get(norm(value))
        if mapped and field in ("service", "facility"):
            field, value = mapped
        if any(a.field == field and a.value != value for a in atoms):
            notices.append("Filter pilihan dan kata pencarian berbeda. Keduanya tetap diterapkan.")
        node = ("atom", Atom(field, value))
        tree = ("and", tree, node) if tree else node

    scores: dict[str, float] = {}
    expr = compile_tree(tree, snap, scores, [0])

    if expr == "(1 = 0)":
        ordered = []
        query = ""
    else:
        query = (
            "SELECT DISTINCT ?rs WHERE { "
            "?rs a hf:RumahSakit; schema:name ?nama; hf:kelas ?kelas; hf:jenis ?jenis; "
            "hf:beradaDiKabupatenKota/rdfs:label ?kabkota . "
            "OPTIONAL {?rs hf:pemilik ?pemilik} "
            f"FILTER({expr}) }} ORDER BY ?rs"
        )
        hits = await sp.select(query)
        ordered = sorted(
            {r["rs"] for r in hits if r["rs"] in snap["rows"]},
            key=lambda uri: (
                -scores.get(uri, 800.0),
                {"A": 0, "B": 1, "C": 2, "D": 3}.get(snap["rows"][uri].get("kelas", "Z"), 4),
                norm(snap["rows"][uri]["nama"]),
                uri,
            ),
        )

    if not ordered and q.strip() and not did_you_mean and not notices:
        did_you_mean = _suggest_corrections_for_empty(q, snap)

    items = []
    for uri in ordered[offset : offset + limit]:
        r = snap["rows"][uri]
        row = {k: v for k, v in r.items() if k not in ("services", "photos", "codes", "diagnostics", "criticals", "hours")}
        row.update(
            layanan="|".join(sorted(r["services"])),
            galeri="|".join(sorted(r["photos"])),
            kodeKemenkes=next(iter(sorted(r["codes"])), ""),
        )
        item = sp.to_hospital(row)
        item["spesialisasi"] = [x for x in item.get("spesialisasi", []) if x in r["services"]]
        items.append(item)

    omitted_set = set(omit.split("|")) if omit else set()
    return {
        "items": items,
        "count": len(items),
        "total": len(ordered),
        "offset": offset,
        "limit": limit,
        "corrections": corrections,
        "did_you_mean": did_you_mean,
        "notices": list(dict.fromkeys(notices)),
        "recognized_filters": [
            {"id": f"{a.start}:{a.end}", "field": a.field, "value": a.value, "label": a.label}
            for a in atoms
            if f"{a.start}:{a.end}" not in omitted_set
        ],
        "query_type": "hybrid_semantic",
        "_query": query,
    }


async def suggest(q: str, limit: int = 8):
    snap = await snapshot()
    q_norm = norm(q)
    if len(q_norm) < 2:
        return []
    choices: dict[str, tuple[str, str]] = {}
    for r in snap["rows"].values():
        choices[r["nama"]] = ("hospital", r["nama"])
    for term, (field, value) in snap["vocab"].items():
        if field == "service" and value not in snap["services"]:
            continue
        if field in ("region", "service", "facility", "concept"):
            display = value if (field == "service" and term == norm(value)) else term.title() if field == "service" else term
            choices[display] = (field, term)
    # Natural-language suggestion for service prefixes (e.g. "jan" -> "Rumah sakit dengan layanan jantung")
    for label in snap["services"]:
        if norm(label).startswith(q_norm) or any(t.startswith(q_norm) for t in norm(label).split()):
            nl = f"Rumah sakit dengan layanan {label.lower()}"
            choices[nl] = ("nl", nl)
            if label not in choices:
                choices[label] = ("service", label)

    ranked = []
    for label, (kind, value) in choices.items():
        n = norm(label)
        if n.startswith(q_norm):
            score = 1.0
        elif any(t.startswith(q_norm) for t in n.split()):
            score = 0.95
        elif len(q_norm) >= 4:
            score = similarity(q_norm, n)
        else:
            score = 0.0
        if score >= 0.75:
            ranked.append((score, label, kind, value))
    ranked.sort(key=lambda x: (-x[0], len(x[1]), x[1]))
    return [{"label": label, "kind": kind, "value": value} for _, label, kind, value in ranked[:limit]]
