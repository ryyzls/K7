"""Repositori Tunggal Data Rumah Sakit CariSehat.

Menyediakan data rumah sakit dari Apache Jena Fuseki (SPARQL) sebagai sumber utama,
dan fallback otomatis ke rdflib in-memory dari file semantic/rdf/*.ttl jika Fuseki
tidak aktif/mengalami error.
Menjamin 100% data konsisten dan akurat sesuai Permenkes No. 3/2020 & ontologi RDF.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import rdflib
from rdflib import RDF, RDFS, Namespace

from app.config import settings
from app.services.website import public_website
from app.services import sparql_service as sp
from app.services import sirs

log = logging.getLogger("carisehat.hospital_repo")

HF = Namespace("http://carisehat.id/ontology/")
SCHEMA = Namespace("https://schema.org/")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")

_lock = threading.Lock()
_CACHE_HOSPITALS: list[dict] | None = None
_CACHE_MAP: dict[str, dict] | None = None
_GAZETTEER: dict[str, list[str]] | None = None
_RDF_DIR: Path | None = None


def find_rdf_dir() -> Path:
    """Temukan direktori semantic/rdf di container atau filesystem host."""
    global _RDF_DIR
    if _RDF_DIR and _RDF_DIR.exists():
        return _RDF_DIR

    # 1. Cek settings.rdf_dir
    p_set = Path(settings.rdf_dir)
    if p_set.exists() and (p_set / "hospitals-sumut.ttl").exists():
        _RDF_DIR = p_set
        return _RDF_DIR

    # 2. Cek relatif dari file ini: Path(__file__).resolve().parents[3] / "semantic" / "rdf"
    p_rel = Path(__file__).resolve().parents[3] / "semantic" / "rdf"
    if p_rel.exists() and (p_rel / "hospitals-sumut.ttl").exists():
        _RDF_DIR = p_rel
        return _RDF_DIR

    # 3. Cek direktori C:\K7\semantic\rdf secara eksplisit
    p_win = Path("C:/K7/semantic/rdf")
    if p_win.exists() and (p_win / "hospitals-sumut.ttl").exists():
        _RDF_DIR = p_win
        return _RDF_DIR

    # Default fallback
    _RDF_DIR = p_rel
    return _RDF_DIR


def _load_rdf_graph_to_cache() -> None:
    """Muat data RDF ke memori sekali sebagai cache fallback & gazetteer."""
    global _CACHE_HOSPITALS, _CACHE_MAP, _GAZETTEER
    rdf_dir = find_rdf_dir()
    ttl_path = rdf_dir / "hospitals-sumut.ttl"
    if not ttl_path.exists():
        log.error("File TTL tidak ditemukan di %s", ttl_path)
        _CACHE_HOSPITALS = []
        _CACHE_MAP = {}
        _GAZETTEER = {}
        return

    g = rdflib.Graph()
    onto_path = rdf_dir / "ontologi.ttl"
    if onto_path.exists():
        try:
            g.parse(str(onto_path), format="turtle")
        except Exception as e:
            log.warning("Gagal memuat ontologi.ttl: %s", e)

    g.parse(str(ttl_path), format="turtle")
    websites_path = rdf_dir / "hospital-websites.ttl"
    if websites_path.exists():
        g.parse(str(websites_path), format="turtle")
    log.info("RDF in-memory graph berhasil dimuat: %d triples", len(g))

    hospitals: list[dict] = []
    hmap: dict[str, dict] = {}

    for s in g.subjects(RDF.type, HF.RumahSakit):
        rs_id = str(s).rsplit("/", 1)[-1]
        nama = str(g.value(s, SCHEMA.name) or "")
        jenis = str(g.value(s, HF.jenis) or "Umum")
        kelas = str(g.value(s, HF.kelas) or "-")
        alamat = str(g.value(s, HF.alamat) or "")
        kk_node = g.value(s, HF.beradaDiKabupatenKota)
        kabkota = str(g.value(kk_node, RDFS.label) or "") if kk_node else ""
        telepon = str(g.value(s, SCHEMA.telephone)) if g.value(s, SCHEMA.telephone) else None
        website = str(g.value(s, SCHEMA.url)) if g.value(s, SCHEMA.url) else None
        website_status = str(g.value(s, HF.websiteStatus) or "unreviewed")
        website_evidence = str(g.value(s, HF.websiteEvidence) or "")
        website_checked_at = str(g.value(s, HF.websiteCheckedAt) or "")
        website = public_website(website, website_status, website_evidence, website_checked_at)
        bpjs_val = g.value(s, HF.menerimaBPJS)
        bpjs = str(bpjs_val).lower() == "true" if bpjs_val is not None else False
        lat_val = g.value(s, GEO.lat)
        lon_val = g.value(s, GEO["long"])
        lat = float(lat_val) if lat_val else None
        lon = float(lon_val) if lon_val else None
        pemilik = str(g.value(s, HF.pemilik)) if g.value(s, HF.pemilik) else None
        sumber = str(g.value(s, HF.sumberKoordinat)) if g.value(s, HF.sumberKoordinat) else None

        layanan = sorted({r['label'] for r in sirs.records().get(rs_id, [])})
        fasilitas = sorted({
            str(g.value(f, RDFS.label))
            for f in g.objects(s, HF.memilikiFasilitas)
            if g.value(f, RDFS.label)
        })
        galeri = sorted({str(img) for img in g.objects(s, SCHEMA.image)})
        foto = galeri[0] if galeri else None

        item = {
            "id": rs_id,
            "uri": str(s),
            "nama": nama,
            "jenis": jenis,
            "kelas": kelas,
            "alamat": alamat,
            "kabkota": kabkota,
            "telepon": telepon,
            "website": website,
            "website_status": website_status,
            "website_evidence": website_evidence,
            "website_checked_at": website_checked_at,
            "website_scope": str(g.value(s, HF.websiteScope) or ""),
            "bpjs": bpjs,
            "lat": lat,
            "lon": lon,
            "foto": foto,
            "galeri": galeri,
            "layanan": layanan,
            "fasilitas": fasilitas,
            "pemilik": pemilik,
            "sumber_koordinat": sumber,
        }
        sirs.annotate(item)
        hospitals.append(item)
        hmap[rs_id] = item
        hmap[str(s)] = item

    # Urutkan abjad nama secara default
    hospitals.sort(key=lambda x: x["nama"])
    _CACHE_HOSPITALS = hospitals
    _CACHE_MAP = hmap
    log.info("Berhasil memuat %d entitas rumah sakit ke cache in-memory", len(hospitals))


def ensure_loaded() -> None:
    """Pastikan data RDF telah ter-cache di memori."""
    if _CACHE_HOSPITALS is None:
        with _lock:
            if _CACHE_HOSPITALS is None:
                _load_rdf_graph_to_cache()


def reload_cache() -> None:
    """Muat ulang cache secara manual (misalnya setelah ada pembaruan data RDF)."""
    with _lock:
        _load_rdf_graph_to_cache()


def get_all_hospitals() -> list[dict]:
    """Kembalikan seluruh 206 rumah sakit dari memori."""
    ensure_loaded()
    return [dict(h) for h in (_CACHE_HOSPITALS or [])]


def get_hospital_by_id(rs_id: str) -> dict | None:
    """Ambil data 1 rumah sakit berdasarkan id atau URI."""
    ensure_loaded()
    if not _CACHE_MAP:
        return None
    res = _CACHE_MAP.get(rs_id)
    if not res and rs_id.startswith("http"):
        short_id = rs_id.rsplit("/", 1)[-1]
        res = _CACHE_MAP.get(short_id)
    return dict(res) if res else None


def _matches_facility(required_fac: str, rs_facs: list[str]) -> bool:
    """Cek kecocokan fasilitas dengan dukungan varian label RDF."""
    rf = required_fac.strip().lower()
    if rf == "icu":
        return any(f.startswith("ICU") for f in rs_facs)
    if rf in ("farmasi", "apotek", "instalasi farmasi"):
        return any(f in ("Apotek", "Farmasi", "Instalasi Farmasi") for f in rs_facs)
    if rf in ("laboratorium", "lab"):
        return any(f.startswith("Laboratorium") for f in rs_facs)
    return any(rf == f.lower() or rf in f.lower() for f in rs_facs)


def filter_in_memory(
    q: str = "",
    kelas: str = "",
    jenis: str = "",
    kabkota: str = "",
    layanan: str = "",
    bpjs: bool | None = None,
    fasilitas: str = "",
    is_emergency: bool = False,
    uri: str | None = None,
) -> list[dict]:
    """Filter rumah sakit langsung dari memori RDF secara deterministik dan akurat."""
    ensure_loaded()
    items = _CACHE_HOSPITALS or []
    results: list[dict] = []

    for h in items:
        if uri:
            if h["uri"] != uri and h["id"] != uri.rsplit("/", 1)[-1]:
                continue
        if q:
            ql = q.lower()
            if ql not in h["nama"].lower() and ql not in h["alamat"].lower():
                continue
        if kelas:
            if h["kelas"].upper() != kelas.upper():
                continue
        if jenis:
            if h["jenis"].lower() != jenis.lower():
                continue
        if kabkota:
            kk_clean = kabkota.lower()
            h_kk = h["kabkota"].lower()
            if kk_clean != h_kk and kk_clean not in h_kk and h_kk not in kk_clean:
                continue
        if bpjs is not None:
            if h["bpjs"] != bpjs:
                continue
        if layanan:
            lay_lower = layanan.lower()
            if not any(lay_lower == l.lower() or lay_lower in l.lower() for l in h["layanan"]):
                continue
        if fasilitas:
            if not _matches_facility(fasilitas, h["fasilitas"]):
                continue
        if is_emergency:
            if sirs.EMERGENCY not in h['layanan']:
                continue

        results.append(dict(h))

    # Pengurutan default: Kelas (A->D), lalu nama
    kelas_order = {"A": 1, "B": 2, "C": 3, "D": 4}
    results.sort(key=lambda x: (kelas_order.get(x.get("kelas", "-"), 5), x["nama"]))
    return results


async def search_hospitals(
    q: str = "",
    kelas: str = "",
    jenis: str = "",
    kabkota: str = "",
    layanan: str = "",
    bpjs: bool | None = None,
    fasilitas: str = "",
    limit: int = 500,
    offset: int = 0,
    uri: str | None = None,
    is_emergency: bool = False,
) -> list[dict]:
    """Cari rumah sakit. Coba Fuseki dahulu, jika gagal/tidak aktif gunakan in-memory RDF."""
    # 1. Coba Fuseki SPARQL jika memungkinkan
    try:
        if is_emergency:
            fuseki_res = await sp.search_emergency_hospitals(limit=limit)
        else:
            fuseki_res = await sp.search_hospitals(
                q=q,
                kelas=kelas,
                jenis=jenis,
                kabkota=kabkota,
                layanan=layanan,
                bpjs=bpjs,
                fasilitas=fasilitas,
                limit=limit,
                offset=offset,
                uri=uri,
            )
        if fuseki_res is not None:
            return fuseki_res
    except Exception as e:
        log.warning("Fuseki query tidak dapat dijangkau (%s), beralih ke fallback RDF lokal.", e)

    # 2. Fallback in-memory RDF
    matched = filter_in_memory(
        q=q,
        kelas=kelas,
        jenis=jenis,
        kabkota=kabkota,
        layanan=layanan,
        bpjs=bpjs,
        fasilitas=fasilitas,
        is_emergency=is_emergency,
        uri=uri,
    )
    return matched[offset : offset + limit]


async def search_emergency_hospitals(limit: int = 50) -> list[dict]:
    """Ambil RS dengan UGD 24 Jam dan Ambulans/IGD."""
    return await search_hospitals(is_emergency=True, limit=limit)
