"""Semua akses ke Fuseki lewat modul ini (milik P4). Query = bukti penggunaan SPARQL di paper."""
import re

import httpx

from app.config import settings

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


def build_search_query(q="", kelas="", jenis="", kabkota="", layanan="", limit=50, offset=0, uri=None) -> str:
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
        f.append(f"FILTER EXISTS {{ ?rs hf:menyediakanLayanan ?l . ?l rdfs:label ?ll . FILTER(STR(?ll) = {lit(layanan)}) }}")
    values = f"VALUES ?rs {{ <{uri}> }}" if uri else ""
    filters = "\n  ".join(f)
    return f"""SELECT ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?lat ?lon
       (GROUP_CONCAT(DISTINCT ?lay; separator="|") AS ?layanan)
       (GROUP_CONCAT(DISTINCT ?fas; separator="|") AS ?fasilitas)
WHERE {{
  {values}
  ?rs a hf:RumahSakit ; schema:name ?nama ; hf:jenis ?jenis ; hf:kelas ?kelas ; hf:alamat ?alamat ;
      hf:beradaDiKabupatenKota ?kk ; geo:lat ?lat ; geo:long ?lon .
  ?kk rdfs:label ?kabkota .
  OPTIONAL {{ ?rs schema:telephone ?telepon }}
  OPTIONAL {{ ?rs schema:url ?website }}
  OPTIONAL {{ ?rs hf:menyediakanLayanan/rdfs:label ?lay }}
  OPTIONAL {{ ?rs hf:memilikiFasilitas/rdfs:label ?fas }}
  {filters}
}}
GROUP BY ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?telepon ?website ?lat ?lon
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
    return {
        "id": r["rs"].rsplit("/", 1)[-1], "uri": r["rs"], "nama": r["nama"], "jenis": r["jenis"],
        "kelas": r["kelas"], "alamat": r["alamat"], "kabkota": r["kabkota"],
        "telepon": r.get("telepon"), "website": r.get("website"),
        "lat": float(r["lat"]), "lon": float(r["lon"]),
        "layanan": parts(r.get("layanan")), "fasilitas": parts(r.get("fasilitas")),
    }


async def search_hospitals(**kw) -> list[dict]:
    return [to_hospital(r) for r in await select(build_search_query(**kw))]


async def get_hospital(rs_id: str) -> dict | None:
    rows = await select(build_search_query(uri=rs_uri(rs_id), limit=1))
    return to_hospital(rows[0]) if rows else None


async def filter_options() -> dict:
    kab = await select("SELECT DISTINCT ?v WHERE { ?k a hf:KabupatenKota ; rdfs:label ?v } ORDER BY ?v")
    lay = await select("SELECT DISTINCT ?v WHERE { ?l a hf:Layanan ; rdfs:label ?v } ORDER BY ?v")
    return {"kabkota": [r["v"] for r in kab], "layanan": [r["v"] for r in lay]}


async def construct(uri: str | None, accept: str) -> str:
    if uri:
        q = (f"CONSTRUCT {{ ?s ?p ?o . ?x rdfs:label ?l }} WHERE {{ VALUES ?s {{ <{uri}> }} ?s ?p ?o . "
             f"OPTIONAL {{ ?s ?p2 ?x . ?x rdfs:label ?l }} }}")
    else:
        q = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{settings.fuseki_url}/query", data={"query": PREFIXES + q}, headers={"Accept": accept})
        r.raise_for_status()
    return r.text
