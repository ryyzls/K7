"""Semua akses ke Fuseki lewat modul ini (milik P4). Query = bukti penggunaan SPARQL di paper."""
import re

import httpx

from app.config import settings
from app.services.website import public_website
from app.services import sirs

PREFIXES = f"""PREFIX hf: <{settings.onto_ns}>
PREFIX schema: <https://schema.org/>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def lit(s: str) -> str:
    """Escape string menjadi literal SPARQL (cegah injeksi query)."""
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    return f'"{s}"'


def rs_uri(rs_id: str) -> str:
    if not ID_RE.match(rs_id):
        raise ValueError("id tidak valid")
    return f"{settings.base_uri}/rs/{rs_id}"


def build_search_query(q="", kelas="", jenis="", kabkota="", layanan="", bpjs=None, fasilitas="", spesialisasi="", limit=50, offset=0, uri=None) -> str:
    f = []
    if q:
        f.append(f"FILTER(CONTAINS(LCASE(?nama), {lit(q.lower())}) || CONTAINS(LCASE(?alamat), {lit(q.lower())}))")
    if kelas:
        f.append(f"FILTER(?kelas = {lit(kelas)})")
    if jenis:
        f.append(f"FILTER(?jenis = {lit(jenis)})")
    if kabkota:
        f.append(f"FILTER(STR(?kabkota) = {lit(kabkota)})")
    if layanan:
        from app.services.specialty_service import ALL_ACTIVE_SPECIALTIES, sirs_specialty_pattern
        if layanan in ALL_ACTIVE_SPECIALTIES:
            f.append(f"FILTER EXISTS {{ {sirs_specialty_pattern(layanan, '?rs', '?sirsFilter')} }}")
        else:
            f.append(f"FILTER EXISTS {{ {sirs.pattern(lit(layanan), '?sirsFilter')} }}")
    if spesialisasi:
        from app.services.specialty_service import sirs_specialty_pattern
        f.append(f"FILTER EXISTS {{ {sirs_specialty_pattern(spesialisasi, '?rs', '?sirsSpecFilter')} }}")
    if bpjs is not None:
        f.append('FILTER(STR(?bpjs) = "' + ('true' if bpjs else 'false') + '")')
    if fasilitas:
        facility = fasilitas.lower()
        if facility in ("farmasi", "apotek", "instalasi farmasi"):
            condition = 'LCASE(STR(?flbl)) IN ("apotek", "farmasi", "instalasi farmasi")'
        elif facility in ("icu", "laboratorium", "lab"):
            condition = f'STRSTARTS(LCASE(STR(?flbl)), {lit("laboratorium" if facility == "lab" else facility)})'
        else:
            condition = f'CONTAINS(LCASE(STR(?flbl)), {lit(facility)})'
        f.append(f"FILTER EXISTS {{ ?rs hf:memilikiFasilitas ?fac . ?fac rdfs:label ?flbl . FILTER({condition}) }}")
    values = f"VALUES ?rs {{ <{uri}> }}" if uri else ""
    filters = "\n  ".join(f)
    return f"""SELECT ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?websiteStatus ?websiteEvidence ?websiteCheckedAt ?websiteScope ?lat ?lon ?bpjs ?pemilik ?sumberKoordinat ?kodeKemenkes
       (GROUP_CONCAT(DISTINCT COALESCE(?lay, ""); separator="|") AS ?layanan)
       (GROUP_CONCAT(DISTINCT COALESCE(?fas, ""); separator="|") AS ?fasilitas)
       (GROUP_CONCAT(DISTINCT COALESCE(?img, ""); separator="|") AS ?galeri)
WHERE {{
  {values}
  ?rs a hf:RumahSakit ; schema:name ?nama ; hf:jenis ?jenis ; hf:kelas ?kelas ; hf:alamat ?alamat ;
      hf:beradaDiKabupatenKota ?kk .
  ?kk rdfs:label ?kabkota .
  OPTIONAL {{ ?rs geo:lat ?lat ; geo:long ?lon }}
  OPTIONAL {{ ?rs schema:telephone ?telepon }}
  OPTIONAL {{ ?rs schema:url ?website }}
  OPTIONAL {{ ?rs hf:websiteStatus ?websiteStatus }}
  OPTIONAL {{ ?rs hf:websiteEvidence ?websiteEvidence }}
  OPTIONAL {{ ?rs hf:websiteCheckedAt ?websiteCheckedAt }}
  OPTIONAL {{ ?rs hf:websiteScope ?websiteScope }}
  OPTIONAL {{ ?rs hf:menerimaBPJS ?bpjs }}
  OPTIONAL {{ ?rs hf:pemilik ?pemilik }}
  OPTIONAL {{ ?rs hf:sumberKoordinat ?sumberKoordinat }}
  OPTIONAL {{ ?rs schema:image ?img }}
  OPTIONAL {{ {sirs.pattern()} }}
  OPTIONAL {{ ?rs hf:memilikiFasilitas/rdfs:label ?fas }}
  OPTIONAL {{
    GRAPH <{sirs.GRAPH_URI}> {{
      ?rs <{sirs.CS.kodeRegistrasiKemenkes}> ?kodeKemenkes .
    }}
  }}
  {filters}
}}
GROUP BY ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?websiteStatus ?websiteEvidence ?websiteCheckedAt ?websiteScope ?lat ?lon ?bpjs ?pemilik ?sumberKoordinat ?kodeKemenkes
ORDER BY ?nama
LIMIT {int(limit)} OFFSET {int(offset)}"""


async def select(query: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{settings.fuseki_url}/query",
            data={"query": PREFIXES + query},
            headers={"Accept": "application/sparql-results+json"},
        )
        r.raise_for_status()
    return [{k: v["value"] for k, v in row.items()} for row in r.json()["results"]["bindings"]]


def to_hospital(r: dict) -> dict:
    parts = lambda s: sorted(x for x in (s or "").split("|") if x)
    galeri = parts(r.get("galeri"))
    h = sirs.annotate({
        "id": r["rs"].rsplit("/", 1)[-1], "uri": r["rs"], "nama": r["nama"], "jenis": r["jenis"],
        "kelas": r["kelas"], "alamat": r["alamat"], "kabkota": r["kabkota"],
        "telepon": r.get("telepon"), "website": public_website(r.get("website"), r.get("websiteStatus"), r.get("websiteEvidence"), r.get("websiteCheckedAt")),
        "website_status": r.get("websiteStatus", "unreviewed"),
        "website_evidence": r.get("websiteEvidence"),
        "website_checked_at": r.get("websiteCheckedAt"),
        "website_scope": r.get("websiteScope"),
        "bpjs": r.get("bpjs") == "true",
        "lat": float(r["lat"]) if r.get("lat") else None, "lon": float(r["lon"]) if r.get("lon") else None,
        "foto": galeri[0] if galeri else None,
        "galeri": galeri,
        "layanan": parts(r.get("layanan")), "fasilitas": parts(r.get("fasilitas")),
        "pemilik": r.get("pemilik"),
        "sumber_koordinat": r.get("sumberKoordinat"),
        "kode_kemenkes": r.get("kodeKemenkes"),
    })
    # Metadata spesialisasi & fasilitas penunjang SIRS
    from app.services.specialty_service import get_hospital_specialties
    from app.services.enrichment_service import get_hospital_enrichment

    spec_records = get_hospital_specialties(h["id"])
    h["spesialisasi"] = sorted(list({s["label"] for s in spec_records}))
    h["spesialisasi_facts"] = spec_records
    h["igd_tersedia"] = sirs.EMERGENCY in h.get("layanan", []) or any(s["label"] == sirs.EMERGENCY for s in spec_records)

    # 6 Fitur Final Data Enrichment Freeze
    enrichment = get_hospital_enrichment(h["id"])
    prof = enrichment.get("profil_lengkap", {})
    kontak = enrichment.get("kontak_dan_website", {})

    h["direktur"] = prof.get("direktur")
    h["kepemilikan"] = prof.get("kepemilikan")
    h["luas_tanah"] = prof.get("luas_tanah")
    h["luas_bangunan"] = prof.get("luas_bangunan")
    
    # Kontak (Telepon, Email, Website) integration
    clean_tel = kontak.get("telepon")
    if clean_tel:
        h["telepon"] = clean_tel
    h["telepon_display"] = h.get("telepon") or "Belum tersedia"

    cand_web = kontak.get("website_url")
    if cand_web:
        h["website"] = cand_web
        h["website_display"] = cand_web
        h["website_status"] = kontak.get("website_status", "TERSEDIA")
    else:
        h["website_display"] = "Belum tersedia"

    h["email"] = kontak.get("email")
    h["email_display"] = kontak.get("email_display", "Belum tersedia")
    h["email_status"] = kontak.get("email_status", "BELUM_TERSEDIA")
    h["fasilitas_medis_berbukti"] = enrichment.get("fasilitas_medis_berbukti", {})
    h["igd_24jam_terlapor"] = enrichment.get("igd_24jam", {})
    h["jam_operasional"] = enrichment.get("jam_operasional", {})

    # Specific override for RS Vita Insani (rs-199) UI requirements
    if h["id"] == "rs-199":
        h["spesialisasi"] = ["Konseling Kesehatan Mental", "Psikologi"]
        h["fasilitas"] = ["Layanan Kesehatan Rumah"]

    if not h.get("kode_kemenkes"):
        h["kode_kemenkes"] = prof.get("kode_kemenkes")
    if not h.get("kode_kemenkes") and spec_records:
        url = spec_records[0].get("source_url", "")
        parts_url = url.rstrip("/").split("/")
        if parts_url and parts_url[-1].isdigit():
            h["kode_kemenkes"] = parts_url[-1]
    return h


async def search_hospitals(**kw) -> list[dict]:
    return [to_hospital(r) for r in await select(build_search_query(**kw))]


async def get_hospital(rs_id: str) -> dict | None:
    rows = await select(build_search_query(uri=rs_uri(rs_id), limit=1))
    return to_hospital(rows[0]) if rows else None


async def filter_options() -> dict:
    kab = await select("SELECT DISTINCT ?v WHERE { ?k a hf:KabupatenKota ; rdfs:label ?v } ORDER BY ?v")
    lay = await select("SELECT DISTINCT ?v WHERE { " + sirs.pattern('?v') + " } ORDER BY ?v")
    return {"kabkota": [r["v"] for r in kab], "layanan": [r["v"] for r in lay]}


async def construct(uri: str | None, accept: str) -> str:
    if uri:
        q = (f"CONSTRUCT {{ ?s ?p ?o . ?x rdfs:label ?l }} WHERE {{ VALUES ?s {{ <{uri}> }} ?s ?p ?o . "
             f"OPTIONAL {{ ?s ?p2 ?x . ?x rdfs:label ?l }} }}")
    else:
        q = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
    scope = f'VALUES ?s {{ <{uri}> }}' if uri else ''
    q = f'''CONSTRUCT {{ ?s ?p ?o . ?x rdfs:label ?l . ?s <{sirs.CS.catatanPelayanan}> ?obs . ?obs ?op ?ov }}
    WHERE {{ {scope}
      {{ ?s ?p ?o . FILTER(?p != hf:menyediakanLayanan)
         OPTIONAL {{ ?s ?p2 ?x . ?x rdfs:label ?l }} }}
      UNION {{ GRAPH <{sirs.GRAPH_URI}> {{ ?s <{sirs.CS.catatanPelayanan}> ?obs .
         ?obs <{sirs.CS.layakPencarian}> true ; ?op ?ov . }} }}
    }}'''
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{settings.fuseki_url}/query", data={"query": PREFIXES + q}, headers={"Accept": accept})
        r.raise_for_status()
    return r.text


# ── New query templates ────────────────────────────────────────────────────────

def _legacy_emergency_query_not_used(limit: int = 5) -> str:
    """Hospitals with UGD 24 Jam AND (Ambulans OR Instalasi Gawat Darurat), ordered by kelas."""
    return f"""SELECT ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?websiteStatus ?websiteEvidence ?websiteCheckedAt ?websiteScope ?lat ?lon ?bpjs ?pemilik ?sumberKoordinat
   (GROUP_CONCAT(DISTINCT ?lay; separator="|") AS ?layanan)
   (GROUP_CONCAT(DISTINCT ?fas; separator="|") AS ?fasilitas)
   (GROUP_CONCAT(DISTINCT ?img; separator="|") AS ?galeri)
WHERE {{
  ?rs a hf:RumahSakit ; schema:name ?nama ; hf:jenis ?jenis ; hf:kelas ?kelas ; hf:alamat ?alamat ;
      hf:beradaDiKabupatenKota ?kk .
  ?kk rdfs:label ?kabkota .
  OPTIONAL {{ ?rs geo:lat ?lat ; geo:long ?lon }}
  OPTIONAL {{ ?rs schema:telephone ?telepon }}
  OPTIONAL {{ ?rs schema:url ?website }}
  OPTIONAL {{ ?rs hf:websiteStatus ?websiteStatus }}
  OPTIONAL {{ ?rs hf:websiteEvidence ?websiteEvidence }}
  OPTIONAL {{ ?rs hf:websiteCheckedAt ?websiteCheckedAt }}
  OPTIONAL {{ ?rs hf:websiteScope ?websiteScope }}
  OPTIONAL {{ ?rs hf:menerimaBPJS ?bpjs }}
  OPTIONAL {{ ?rs hf:pemilik ?pemilik }}
  OPTIONAL {{ ?rs hf:sumberKoordinat ?sumberKoordinat }}
  OPTIONAL {{ ?rs schema:image ?img }}
  OPTIONAL {{ {sirs.pattern()} }}
  OPTIONAL {{ ?rs hf:memilikiFasilitas/rdfs:label ?fas }}
  FILTER EXISTS {{
    ?rs hf:menyediakanLayanan ?lsvc .
    ?lsvc rdfs:label ?lbl .
    FILTER(STR(?lbl) = {lit("UGD 24 Jam")})
  }}
  FILTER EXISTS {{
    ?rs hf:memilikiFasilitas ?fac .
    ?fac rdfs:label ?flbl .
    FILTER(STR(?flbl) = {lit("Ambulans")} || STR(?flbl) = {lit("Instalasi Gawat Darurat")})
  }}
  BIND(IF(?kelas = {lit("A")}, 1,
       IF(?kelas = {lit("B")}, 2,
       IF(?kelas = {lit("C")}, 3,
       IF(?kelas = {lit("D")}, 4, 5)))) AS ?kelasSort)
}}
GROUP BY ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?websiteStatus ?websiteEvidence ?websiteCheckedAt ?websiteScope ?lat ?lon ?bpjs ?pemilik ?sumberKoordinat ?kelasSort
ORDER BY ?kelasSort ?nama
LIMIT {int(limit)}"""


def build_emergency_query(limit: int = 5) -> str:
    return build_search_query(layanan=sirs.EMERGENCY, limit=limit)


def build_bpjs_query(kabkota: str = "", kelas: str = "", limit: int = 10) -> str:
    """Hospitals accepting BPJS, optionally filtered by kabkota and kelas."""
    f = ['FILTER(STR(?bpjs) = "true")']
    if kabkota:
        f.append(f"FILTER(STR(?kabkota) = {lit(kabkota)})")
    if kelas:
        f.append(f"FILTER(?kelas = {lit(kelas)})")
    filters = "\n  ".join(f)
    return f"""SELECT ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?websiteStatus ?websiteEvidence ?websiteCheckedAt ?websiteScope ?lat ?lon ?bpjs ?pemilik ?sumberKoordinat
   (GROUP_CONCAT(DISTINCT ?lay; separator="|") AS ?layanan)
   (GROUP_CONCAT(DISTINCT ?fas; separator="|") AS ?fasilitas)
   (GROUP_CONCAT(DISTINCT ?img; separator="|") AS ?galeri)
WHERE {{
  ?rs a hf:RumahSakit ; schema:name ?nama ; hf:jenis ?jenis ; hf:kelas ?kelas ; hf:alamat ?alamat ;
      hf:beradaDiKabupatenKota ?kk ; hf:menerimaBPJS ?bpjs .
  ?kk rdfs:label ?kabkota .
  OPTIONAL {{ ?rs geo:lat ?lat ; geo:long ?lon }}
  OPTIONAL {{ ?rs schema:telephone ?telepon }}
  OPTIONAL {{ ?rs schema:url ?website }}
  OPTIONAL {{ ?rs hf:websiteStatus ?websiteStatus }}
  OPTIONAL {{ ?rs hf:websiteEvidence ?websiteEvidence }}
  OPTIONAL {{ ?rs hf:websiteCheckedAt ?websiteCheckedAt }}
  OPTIONAL {{ ?rs hf:websiteScope ?websiteScope }}
  OPTIONAL {{ ?rs hf:pemilik ?pemilik }}
  OPTIONAL {{ ?rs hf:sumberKoordinat ?sumberKoordinat }}
  OPTIONAL {{ ?rs schema:image ?img }}
  OPTIONAL {{ {sirs.pattern()} }}
  OPTIONAL {{ ?rs hf:memilikiFasilitas/rdfs:label ?fas }}
  {filters}
}}
GROUP BY ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?websiteStatus ?websiteEvidence ?websiteCheckedAt ?websiteScope ?lat ?lon ?bpjs ?pemilik ?sumberKoordinat
ORDER BY ?nama
LIMIT {int(limit)}"""


def build_facility_query(fasilitas_label: str, kabkota: str = "", limit: int = 10) -> str:
    """Hospitals that have a specific fasilitas, optionally filtered by kabkota."""
    f = [f"""FILTER EXISTS {{
    ?rs hf:memilikiFasilitas ?fac .
    ?fac rdfs:label ?flbl .
    FILTER(STR(?flbl) = {lit(fasilitas_label)})
  }}"""]
    if kabkota:
        f.append(f"FILTER(STR(?kabkota) = {lit(kabkota)})")
    filters = "\n  ".join(f)
    return f"""SELECT ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?websiteStatus ?websiteEvidence ?websiteCheckedAt ?websiteScope ?lat ?lon ?bpjs ?pemilik ?sumberKoordinat
   (GROUP_CONCAT(DISTINCT ?lay; separator="|") AS ?layanan)
   (GROUP_CONCAT(DISTINCT ?fas; separator="|") AS ?fasilitas)
   (GROUP_CONCAT(DISTINCT ?img; separator="|") AS ?galeri)
WHERE {{
  ?rs a hf:RumahSakit ; schema:name ?nama ; hf:jenis ?jenis ; hf:kelas ?kelas ; hf:alamat ?alamat ;
      hf:beradaDiKabupatenKota ?kk .
  ?kk rdfs:label ?kabkota .
  OPTIONAL {{ ?rs geo:lat ?lat ; geo:long ?lon }}
  OPTIONAL {{ ?rs schema:telephone ?telepon }}
  OPTIONAL {{ ?rs schema:url ?website }}
  OPTIONAL {{ ?rs hf:websiteStatus ?websiteStatus }}
  OPTIONAL {{ ?rs hf:websiteEvidence ?websiteEvidence }}
  OPTIONAL {{ ?rs hf:websiteCheckedAt ?websiteCheckedAt }}
  OPTIONAL {{ ?rs hf:websiteScope ?websiteScope }}
  OPTIONAL {{ ?rs hf:menerimaBPJS ?bpjs }}
  OPTIONAL {{ ?rs hf:pemilik ?pemilik }}
  OPTIONAL {{ ?rs hf:sumberKoordinat ?sumberKoordinat }}
  OPTIONAL {{ ?rs schema:image ?img }}
  OPTIONAL {{ {sirs.pattern()} }}
  OPTIONAL {{ ?rs hf:memilikiFasilitas/rdfs:label ?fas }}
  {filters}
}}
GROUP BY ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?websiteStatus ?websiteEvidence ?websiteCheckedAt ?websiteScope ?lat ?lon ?bpjs ?pemilik ?sumberKoordinat
ORDER BY ?nama
LIMIT {int(limit)}"""


# ── New async helpers ──────────────────────────────────────────────────────────

async def search_emergency_hospitals(limit: int = 5) -> list[dict]:
    return await search_hospitals(layanan=sirs.EMERGENCY, limit=limit)


async def search_bpjs_hospitals(kabkota: str = "", kelas: str = "", limit: int = 10) -> list[dict]:
    return [to_hospital(r) for r in await select(build_bpjs_query(kabkota, kelas, limit))]


async def search_by_facility(fasilitas_label: str, kabkota: str = "", limit: int = 10) -> list[dict]:
    return [to_hospital(r) for r in await select(build_facility_query(fasilitas_label, kabkota, limit))]


async def search_hospitals_by_name(name_fragment: str, limit: int = 5) -> list[dict]:
    return [to_hospital(r) for r in await select(build_search_query(q=name_fragment, limit=limit))]
