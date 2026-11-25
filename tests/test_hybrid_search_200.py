"""Comprehensive 210-scenario Hybrid Semantic Search test suite against live FastAPI + Apache Jena Fuseki.

Computes independent ground truth directly from RDF datasets (never from the search engine itself).
Saves structured results to docs/search_test_results_200.json and docs/search_test_results_200.csv.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import sys
import time
import unittest
from pathlib import Path

import httpx
from rdflib import Dataset, Literal, Namespace, URIRef

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
API_BASE = "http://127.0.0.1:8000"

HF = Namespace("http://carisehat.id/ontology/")
CS = Namespace("http://carisehat.id/ontology/sirs/")
SCHEMA = Namespace("https://schema.org/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")


def load_ground_truth():
    ds = Dataset()
    for p in (ROOT / "semantic/rdf").glob("*.ttl"):
        ds.default_graph.parse(p, format="turtle")
    ds.graph(URIRef("http://carisehat.id/graph/sirs/2026-11-19")).parse(
        ROOT / "semantic/sirs/services-reviewed.ttl", format="turtle"
    )
    ds.graph(URIRef("http://carisehat.id/graph/enrichment/2026-11-20")).parse(
        ROOT / "semantic/named_graphs/carisehat-enrichment-freeze.ttl", format="turtle"
    )
    ds.graph(URIRef("http://carisehat.id/graph/search/facilities/2026-11-25")).parse(
        ROOT / "semantic/search/facilities-evidence.ttl", format="turtle"
    )

    hospitals: dict[str, dict] = {}
    q_base = """
    PREFIX hf: <http://carisehat.id/ontology/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?rs ?nama ?jenis ?kelas ?alamat ?kabkota ?pemilik WHERE {
      ?rs a hf:RumahSakit ; schema:name ?nama ; hf:jenis ?jenis ; hf:kelas ?kelas ; hf:alamat ?alamat ;
          hf:beradaDiKabupatenKota/rdfs:label ?kabkota .
      OPTIONAL { ?rs hf:pemilik ?pemilik }
    }"""
    for r in ds.query(q_base):
        hid = str(r.rs).rsplit("/", 1)[-1]
        hospitals[hid] = {
            "id": hid,
            "nama": str(r.nama),
            "jenis": str(r.jenis),
            "kelas": str(r.kelas),
            "alamat": str(r.alamat),
            "kabkota": str(r.kabkota),
            "pemilik": str(r.pemilik) if r.pemilik else "",
            "services": set(),
            "diagnostics": set(),
            "criticals": set(),
            "code": "",
            "hours": [],
        }

    # Codes & Hours
    g_enr = ds.graph(URIRef("http://carisehat.id/graph/enrichment/2026-11-20"))
    for s, _, o in g_enr.triples((None, CS.kodeRegistrasiKemenkes, None)):
        hid = str(s).rsplit("/", 1)[-1]
        if hid in hospitals:
            hospitals[hid]["code"] = str(o)
    for r in httpx.post(
        "http://127.0.0.1:3030/hospital/query",
        data={"query": """
        PREFIX schema: <https://schema.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?rs ?unit ?days ?opens ?closes WHERE {
          GRAPH <http://carisehat.id/graph/enrichment/2026-11-20> {
            ?rs schema:openingHoursSpecification ?o .
            ?o rdfs:label ?unit ; schema:description ?days ; schema:opens ?opens ; schema:closes ?closes .
          }
        }"""},
        headers={"Accept": "application/sparql-results+json"},
        timeout=10,
    ).json()["results"]["bindings"]:
        hid = r["rs"]["value"].rsplit("/", 1)[-1]
        if hid in hospitals:
            hospitals[hid]["hours"].append((r["unit"]["value"], r["days"]["value"], r["opens"]["value"], r["closes"]["value"]))

    # SIRS services (all labels for active specialties + layakPencarian true)
    for r in ds.query("""
        SELECT ?rs ?lbl ?layak WHERE {
          GRAPH <http://carisehat.id/graph/sirs/2026-11-19> {
            ?rs <http://carisehat.id/ontology/sirs/catatanPelayanan> ?o .
            ?o <http://carisehat.id/ontology/sirs/labelPelayanan> ?lbl .
            OPTIONAL { ?o <http://carisehat.id/ontology/sirs/layakPencarian> ?layak }
          }
        }"""):
        hid = str(r.rs).rsplit("/", 1)[-1]
        if hid in hospitals:
            hospitals[hid]["services"].add(str(r.lbl))

    # Facilities evidence
    for r in ds.query("""
        PREFIX hf: <http://carisehat.id/ontology/>
        PREFIX cs: <http://carisehat.id/ontology/sirs/>
        SELECT ?rs ?d WHERE {
          GRAPH <http://carisehat.id/graph/search/facilities/2026-11-25> {
            ?rs hf:memilikiFasilitasDiagnostik ?d .
          }
        }"""):
        hid = str(r.rs).rsplit("/", 1)[-1]
        if hid in hospitals:
            hospitals[hid]["diagnostics"].add(str(r.d))

    for r in ds.query("""
        PREFIX hf: <http://carisehat.id/ontology/>
        PREFIX cs: <http://carisehat.id/ontology/sirs/>
        SELECT ?rs ?k ?cap WHERE {
          GRAPH <http://carisehat.id/graph/search/facilities/2026-11-25> {
            ?rs hf:fasilitasKritis ?f .
            ?f cs:jenisFasilitas ?k ; cs:kapasitasTerlapor ?cap .
          }
        }"""):
        hid = str(r.rs).rsplit("/", 1)[-1]
        if hid in hospitals and int(r.cap) > 0:
            hospitals[hid]["criticals"].add(str(r.k))

    return hospitals


def has_fac(h: dict, key: str) -> bool:
    lk = key.lower()
    if lk in ("icu", "nicu", "picu"):
        return f"{lk}_dengan_ventilator" in h["criticals"] or f"{lk}_tanpa_ventilator" in h["criticals"]
    if lk == "ventilator":
        return any(x.endswith("_dengan_ventilator") for x in h["criticals"])
    if lk in ("hcu", "iccu", "isolasi"):
        return lk in h["criticals"]
    return key in h["diagnostics"] or key in h["services"]


def is_gov(h: dict) -> bool:
    return any(x in h["pemilik"].lower() for x in ["pemkab", "pemkot", "pemprop", "kemkes", "kementerian", "tni", "polri"])


def is_priv(h: dict) -> bool:
    return any(x in h["pemilik"].lower() for x in ["perusahaan", "swasta", "organisasi", "yayasan", "perorangan"])


def build_scenarios(gt: dict) -> list[dict]:
    all_ids = set(gt.keys())
    def ids_where(pred):
        return {hid for hid, h in gt.items() if pred(h)}

    adam_malik = {"rs-171"}
    vita_insani = {"rs-199"}
    columbia = {"rs-007", "rs-008"}
    mitra_medika = ids_where(lambda h: "mitra medika" in h["nama"].lower())
    murni_teguh = ids_where(lambda h: "murni teguh" in h["nama"].lower())
    bunda_thamrin = ids_where(lambda h: "thamrin" in h["nama"].lower())
    pirngadi = {"rs-083"}
    royal_prima = ids_where(lambda h: "royal prima" in h["nama"].lower())
    hermina = {"rs-125"}
    siloam = {"rs-185"}
    elisabeth = ids_where(lambda h: "elisabeth" in h["nama"].lower())
    bhayangkara = ids_where(lambda h: "bhayangkara" in h["nama"].lower())
    rsia_ids = ids_where(lambda h: "ibu dan anak" in h["nama"].lower())
    rsud_ids = ids_where(lambda h: "umum daerah" in h["nama"].lower())
    medan_ids = ids_where(lambda h: h["kabkota"] == "Kota Medan")
    siantar_ids = ids_where(lambda h: h["kabkota"] == "Kota Pematang Siantar")
    deli_ids = ids_where(lambda h: h["kabkota"] == "Kab. Deli Serdang")
    tebing_ids = ids_where(lambda h: h["kabkota"] == "Kota Tebing Tinggi")
    binjai_ids = ids_where(lambda h: h["kabkota"] == "Kota Binjai")
    sibolga_ids = ids_where(lambda h: h["kabkota"] == "Kota Sibolga")
    gunungsitoli_ids = ids_where(lambda h: h["kabkota"] == "Kota Gunungsitoli")
    nias_ids = ids_where(lambda h: h["kabkota"] == "Kab. Nias")
    kep_nias_ids = ids_where(lambda h: "nias" in h["kabkota"].lower() or h["kabkota"] == "Kota Gunungsitoli")
    karo_ids = ids_where(lambda h: h["kabkota"] == "Kab. Karo")
    asahan_ids = ids_where(lambda h: h["kabkota"] == "Kab. Asahan")
    simalungun_ids = ids_where(lambda h: h["kabkota"] == "Kab. Simalungun")
    langkat_ids = ids_where(lambda h: h["kabkota"] == "Kab. Langkat")
    sergai_ids = ids_where(lambda h: h["kabkota"] == "Kab. Serdang Bedagai")
    toba_ids = ids_where(lambda h: "toba" in h["kabkota"].lower())
    labuhanbatu_ids = ids_where(lambda h: h["kabkota"] in ("Kab. Labuhan Batu", "Kab. Labuhanbatu"))

    jantung_ids = ids_where(lambda h: "Jantung dan Pembuluh Darah" in h["services"])
    anak_ids = ids_where(lambda h: "Kesehatan anak" in h["services"])
    obgyn_ids = ids_where(lambda h: "Obstetri dan ginekologi" in h["services"])
    saraf_ids = ids_where(lambda h: "Saraf" in h["services"])
    kulit_ids = ids_where(lambda h: "Kulit dan Kelamin" in h["services"])
    mata_ids = ids_where(lambda h: "Mata" in h["services"])
    tht_ids = ids_where(lambda h: "Telinga Hidung Tenggorok Kepala Leher" in h["services"])
    penyakit_dalam_ids = ids_where(lambda h: "Penyakit dalam" in h["services"])
    bedah_ids = ids_where(lambda h: "Bedah" in h["services"])
    paru_ids = ids_where(lambda h: "Paru" in h["services"])
    ortopedi_ids = ids_where(lambda h: "Orthopedi" in h["services"])
    urologi_ids = ids_where(lambda h: "Urologi" in h["services"])
    jiwa_ids = ids_where(lambda h: "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA" in h["services"])
    gigi_ids = ids_where(lambda h: "Pelayanan medik gigi mulut" in h["services"])
    rehab_ids = ids_where(lambda h: "Rehabilitasi Medik" in h["services"])
    anestesi_ids = ids_where(lambda h: "Anestesi" in h["services"])
    igd_ids = ids_where(lambda h: "Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu" in h["services"])

    icu_ids = ids_where(lambda h: has_fac(h, "ICU"))
    nicu_ids = ids_where(lambda h: has_fac(h, "NICU"))
    picu_ids = ids_where(lambda h: has_fac(h, "PICU"))
    hcu_ids = ids_where(lambda h: has_fac(h, "HCU"))
    iccu_ids = ids_where(lambda h: has_fac(h, "ICCU"))
    vent_ids = ids_where(lambda h: has_fac(h, "Ventilator"))
    ct_ids = ids_where(lambda h: has_fac(h, "CT Scan"))
    hemo_ids = ids_where(lambda h: has_fac(h, "Hemodialisis"))
    rad_ids = ids_where(lambda h: has_fac(h, "Radiologi"))
    lab_ids = ids_where(lambda h: has_fac(h, "Laboratorium Klinik"))
    farmasi_ids = ids_where(lambda h: has_fac(h, "Instalasi Farmasi"))
    ok_ids = ids_where(lambda h: has_fac(h, "Kamar Bedah / Operasi"))
    usg_ids = ids_where(lambda h: has_fac(h, "USG"))

    kelas_a = ids_where(lambda h: h["kelas"] == "A")
    kelas_b = ids_where(lambda h: h["kelas"] == "B")
    kelas_c = ids_where(lambda h: h["kelas"] == "C")
    kelas_d = ids_where(lambda h: h["kelas"] == "D")
    gov_ids = ids_where(is_gov)
    priv_ids = ids_where(is_priv)

    S: list[dict] = []
    def add(cat: str, q: str, expected_ids: set[str] | None = None, **kw):
        S.append({"id": f"T{len(S)+1:03d}", "category": cat, "query": q, "expected_ids": expected_ids, **kw})

    # 1. Nama, kapitalisasi, normalisasi, partial match (25)
    add("Nama & Normalisasi", "Adam Malik", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "ADAM MALIK", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "adam malik", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "aDaM mALiK", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "RSUP H. Adam Malik", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "RSUP H Adam Malik", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "RSUP H.Adam Malik", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "RSUP   Adam   Malik", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "RS Umum Pusat H. Adam Malik", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "Adam", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "Malik", ids_where(lambda h: "malik" in h["nama"].lower()), top1="rs-171")
    add("Nama & Normalisasi", "Malik Adam", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "Vita", ids_where(lambda h: "vita" in h["nama"].lower()), top1="rs-199")
    add("Nama & Normalisasi", "Vita Insani", vita_insani, top1="rs-199")
    add("Nama & Normalisasi", "Insani Vita", vita_insani, top1="rs-199")
    add("Nama & Normalisasi", "Columbia", columbia)
    add("Nama & Normalisasi", "Columbia Asia", columbia)
    add("Nama & Normalisasi", "Murni", murni_teguh)
    add("Nama & Normalisasi", "Murni Teguh", murni_teguh)
    add("Nama & Normalisasi", "Thamrin", ids_where(lambda h: "thamrin" in h["nama"].lower() or "thamrin" in h["alamat"].lower()))
    add("Nama & Normalisasi", "Mitra", ids_where(lambda h: "mitra" in h["nama"].lower()))
    add("Nama & Normalisasi", "Mitra Medika", mitra_medika)
    add("Nama & Normalisasi", "Pirngadi", pirngadi, top1="rs-083")
    add("Nama & Normalisasi", "Royal Prima", royal_prima)
    add("Nama & Normalisasi", "1275655", adam_malik, top1="rs-171")
    add("Nama & Normalisasi", "1276079", {"rs-001"}, top1="rs-001")

    # 2. Typo & Fuzzy Matching (25)
    add("Typo & Fuzzy", "Adam Malk", adam_malik, top1="rs-171")
    add("Typo & Fuzzy", "Adamm Malik", adam_malik, top1="rs-171")
    add("Typo & Fuzzy", "Kolumbia", columbia)
    add("Typo & Fuzzy", "Vita Insni", vita_insani, top1="rs-199")
    add("Typo & Fuzzy", "Mitra Medka", mitra_medika)
    add("Typo & Fuzzy", "Pirngdi", pirngadi, top1="rs-083")
    add("Typo & Fuzzy", "Herminaa", hermina, top1="rs-125")
    add("Typo & Fuzzy", "Siloamm", siloam, top1="rs-185")
    add("Typo & Fuzzy", "Elisabet", elisabeth)
    add("Typo & Fuzzy", "Murni Tguh", murni_teguh)
    add("Typo & Fuzzy", "Jantng", jantung_ids)
    add("Typo & Fuzzy", "Sarf", saraf_ids)
    add("Typo & Fuzzy", "Ortopdi", ortopedi_ids)
    add("Typo & Fuzzy", "Urolgi", urologi_ids)
    add("Typo & Fuzzy", "Radiolgi", rad_ids)
    add("Typo & Fuzzy", "Hemodialisa", hemo_ids)
    add("Typo & Fuzzy", "Hemodialis", hemo_ids)
    add("Typo & Fuzzy", "Pematng Siantar", siantar_ids)
    add("Typo & Fuzzy", "Medn", medan_ids)
    add("Typo & Fuzzy", "Deli Serdng", deli_ids)
    add("Typo & Fuzzy", "Binji", binjai_ids)
    add("Typo & Fuzzy", "Sibolgaa", sibolga_ids)
    add("Typo & Fuzzy", "Tebing Tingi", tebing_ids)
    add("Typo & Fuzzy", "Gunungsitli", gunungsitoli_ids)
    add("Typo & Fuzzy", "Simalungn", simalungun_ids)

    # 3. Sinonim, Alias & Singkatan (20)
    add("Sinonim & Alias", "RSHAM", adam_malik, top1="rs-171")
    add("Sinonim & Alias", "RS Adam Malik", adam_malik, top1="rs-171")
    add("Sinonim & Alias", "RSUP HAM", adam_malik, top1="rs-171")
    add("Sinonim & Alias", "RSIA", rsia_ids)
    add("Sinonim & Alias", "RSUD", rsud_ids)
    add("Sinonim & Alias", "RSUP", adam_malik)
    add("Sinonim & Alias", "RSU", ids_where(lambda h: h["jenis"] == "Umum" or h["nama"].lower().startswith("rs umum")))
    add("Sinonim & Alias", "RS TNI", ids_where(lambda h: "tni" in h["pemilik"].lower()))
    add("Sinonim & Alias", "RS Bhayangkara", bhayangkara)
    add("Sinonim & Alias", "Dokter jantung", jantung_ids)
    add("Sinonim & Alias", "Kardiologi", jantung_ids)
    add("Sinonim & Alias", "Dokter anak", anak_ids)
    add("Sinonim & Alias", "Pediatri", anak_ids)
    add("Sinonim & Alias", "Dokter kandungan", obgyn_ids)
    add("Sinonim & Alias", "Obgyn", obgyn_ids)
    add("Sinonim & Alias", "Dokter saraf", saraf_ids)
    add("Sinonim & Alias", "Neurologi", saraf_ids)
    add("Sinonim & Alias", "Dokter kulit", kulit_ids)
    add("Sinonim & Alias", "Dokter mata", mata_ids)
    add("Sinonim & Alias", "Dokter THT", tht_ids)
    add("Sinonim & Alias", "Cuci darah", hemo_ids)
    add("Sinonim & Alias", "Rontgen", rad_ids)
    add("Sinonim & Alias", "UGD", igd_ids)

    # 4. Layanan, Spesialisasi & Fasilitas (30)
    add("Layanan & Fasilitas", "ICU", icu_ids)
    add("Layanan & Fasilitas", "icu", icu_ids)
    add("Layanan & Fasilitas", "NICU", nicu_ids)
    add("Layanan & Fasilitas", "PICU", picu_ids)
    add("Layanan & Fasilitas", "HCU", hcu_ids)
    add("Layanan & Fasilitas", "ICCU", iccu_ids)
    add("Layanan & Fasilitas", "CT Scan", ct_ids)
    add("Layanan & Fasilitas", "MRI", set())
    add("Layanan & Fasilitas", "Laboratorium", lab_ids)
    add("Layanan & Fasilitas", "Radiologi", rad_ids)
    add("Layanan & Fasilitas", "Hemodialisis", hemo_ids)
    add("Layanan & Fasilitas", "Ventilator", vent_ids)
    add("Layanan & Fasilitas", "IGD", igd_ids)
    add("Layanan & Fasilitas", "IGD 24 jam", igd_ids)
    add("Layanan & Fasilitas", "USG", usg_ids)
    add("Layanan & Fasilitas", "Kamar operasi", ok_ids)
    add("Layanan & Fasilitas", "Instalasi Farmasi", farmasi_ids)
    add("Layanan & Fasilitas", "Jantung", jantung_ids)
    add("Layanan & Fasilitas", "JANTUNG", jantung_ids)
    add("Layanan & Fasilitas", "Poli jantung", jantung_ids)
    add("Layanan & Fasilitas", "Poli mata", mata_ids)
    add("Layanan & Fasilitas", "Poli anak", anak_ids)
    add("Layanan & Fasilitas", "Poli kandungan", obgyn_ids)
    add("Layanan & Fasilitas", "Poli gigi", gigi_ids)
    add("Layanan & Fasilitas", "Poli saraf", saraf_ids)
    add("Layanan & Fasilitas", "Penyakit dalam", penyakit_dalam_ids)
    add("Layanan & Fasilitas", "Bedah", bedah_ids)
    add("Layanan & Fasilitas", "Paru", paru_ids)
    add("Layanan & Fasilitas", "Orthopedi", ortopedi_ids)
    add("Layanan & Fasilitas", "Urologi", urologi_ids)
    add("Layanan & Fasilitas", "Psikiatri", jiwa_ids)
    add("Layanan & Fasilitas", "Rehabilitasi Medik", rehab_ids)
    add("Layanan & Fasilitas", "Anestesi", anestesi_ids)

    # 5. Wilayah & Alamat (20)
    add("Wilayah & Alamat", "Medan", medan_ids)
    add("Wilayah & Alamat", "Kota Medan", medan_ids)
    add("Wilayah & Alamat", "Deli Serdang", deli_ids)
    add("Wilayah & Alamat", "Siantar", siantar_ids)
    add("Wilayah & Alamat", "P. Siantar", siantar_ids)
    add("Wilayah & Alamat", "Pematangsiantar", siantar_ids)
    add("Wilayah & Alamat", "Tebing Tinggi", tebing_ids)
    add("Wilayah & Alamat", "Binjai", binjai_ids)
    add("Wilayah & Alamat", "Sibolga", sibolga_ids)
    add("Wilayah & Alamat", "Gunungsitoli", gunungsitoli_ids)
    add("Wilayah & Alamat", "Nias", nias_ids)
    add("Wilayah & Alamat", "Kepulauan Nias", kep_nias_ids)
    add("Wilayah & Alamat", "Karo", karo_ids)
    add("Wilayah & Alamat", "Asahan", asahan_ids)
    add("Wilayah & Alamat", "Simalungun", simalungun_ids)
    add("Wilayah & Alamat", "Langkat", langkat_ids)
    add("Wilayah & Alamat", "Serdang Bedagai", sergai_ids)
    add("Wilayah & Alamat", "Toba", toba_ids)
    add("Wilayah & Alamat", "Labuhanbatu", labuhanbatu_ids)
    add("Wilayah & Alamat", "Jalan AH Nasution", ids_where(lambda h: "nasution" in h["alamat"].lower()))
    add("Wilayah & Alamat", "Jalan Gatot Subroto", ids_where(lambda h: "gatot subroto" in h["alamat"].lower()))
    add("Wilayah & Alamat", "Medan Johor", ids_where(lambda h: "medan johor" in h["alamat"].lower() or "johor" in h["alamat"].lower()))

    # 6. Natural Language & Multi-Condition (25)
    add("Natural Language", "RS kelas A", kelas_a)
    add("Natural Language", "RS pemerintah", gov_ids)
    add("Natural Language", "RS swasta", priv_ids)
    add("Natural Language", "Rumah sakit dengan layanan jantung", jantung_ids)
    add("Natural Language", "Cari rumah sakit yang ada dokter mata", mata_ids)
    add("Natural Language", "Rumah sakit kelas B di Medan", kelas_b & medan_ids)
    add("Natural Language", "RS yang punya ICU di Medan", icu_ids & medan_ids)
    add("Natural Language", "RS yang punya ICU di Siantar", icu_ids & siantar_ids)
    add("Natural Language", "Rumah sakit yang menyediakan cuci darah", hemo_ids)
    add("Natural Language", "Saya mau mencari rumah sakit dengan CT Scan di Deli Serdang", ct_ids & deli_ids)
    add("Natural Language", "Rumah sakit ibu dan anak di Medan", rsia_ids & medan_ids)
    add("Natural Language", "Rumah sakit pemerintah yang punya layanan saraf", gov_ids & saraf_ids)
    add("Natural Language", "Rumah sakit kelas A yang memiliki ICU dan NICU", kelas_a & icu_ids & nicu_ids)
    add("Natural Language", "RS jantung yang punya ICU", jantung_ids & icu_ids)
    add("Natural Language", "Jantng di Medn", jantung_ids & medan_ids)
    add("Natural Language", "RS ibu dan anak di Deli Serdang", rsia_ids & deli_ids)
    add("Natural Language", "Rumah sakit dengan layanan cuci darah di Siantar", hemo_ids & siantar_ids)
    add("Natural Language", "Rumah sakit dengan IGD 24 jam di Medan", igd_ids & medan_ids)
    add("Natural Language", "Rumah sakit swasta kelas B di Medan", priv_ids & kelas_b & medan_ids)
    add("Natural Language", "Rumah sakit pemerintah di Deli Serdang", gov_ids & deli_ids)
    add("Natural Language", "RSUD di Medan", rsud_ids & medan_ids)
    add("Natural Language", "Rumah sakit dengan dokter anak di Binjai", anak_ids & binjai_ids)
    add("Natural Language", "Rumah sakit dengan layanan paru di Medan", paru_ids & medan_ids)
    add("Natural Language", "Rumah sakit dengan radiologi di Tebing Tinggi", rad_ids & tebing_ids)
    add("Natural Language", "Rumah sakit dengan hemodialisis di Medan", hemo_ids & medan_ids)
    add("Natural Language", "RS kelas C dengan ICU di Deli Serdang", kelas_c & icu_ids & deli_ids)

    # 7. Boolean Search (15)
    add("Boolean Search", "ICU dan NICU", icu_ids & nicu_ids)
    add("Boolean Search", "ICU dan PICU", icu_ids & picu_ids)
    add("Boolean Search", "CT Scan atau MRI", ct_ids)
    add("Boolean Search", "CT Scan dan Hemodialisis", ct_ids & hemo_ids)
    add("Boolean Search", "RS kelas A atau B di Medan", (kelas_a | kelas_b) & medan_ids)
    add("Boolean Search", "RS kelas A atau B", kelas_a | kelas_b)
    add("Boolean Search", "RS Medan selain kelas C", medan_ids - kelas_c)
    add("Boolean Search", "Rumah sakit pemerintah dengan ICU dan CT Scan", gov_ids & icu_ids & ct_ids)
    add("Boolean Search", "Rumah sakit dengan layanan jantung atau saraf di Siantar", (jantung_ids | saraf_ids) & siantar_ids)
    add("Boolean Search", "RS kelas B yang punya ICU tetapi bukan RSIA", (kelas_b & icu_ids) - rsia_ids)
    add("Boolean Search", "Jantung dan Saraf di Medan", jantung_ids & saraf_ids & medan_ids)
    add("Boolean Search", "Mata atau THT di Binjai", (mata_ids | tht_ids) & binjai_ids)
    add("Boolean Search", "Rumah sakit di Deli Serdang selain kelas D", deli_ids - kelas_d)
    add("Boolean Search", "Rumah sakit swasta di Medan bukan RSIA", (priv_ids & medan_ids) - rsia_ids)
    add("Boolean Search", "Jantung atau Paru dengan ICU atau NICU", (jantung_ids | paru_ids) & (icu_ids | nicu_ids))
    # Negative facility OWA check (must return 0 with notice)
    add("Boolean Search", "Rumah sakit tanpa ICU", set(), expect_notice=True)

    # 8. Jam Operasional (10) - computed from live Fuseki enrichment graph
    from app.services.operating_hours import day_indexes
    def hours_match(unit_sub: str, day_name: str | None = None, closes_ge: str | None = None, morning: bool = False):
        out = set()
        td = day_indexes(day_name)[0] if day_name else None
        for hid, h in gt.items():
            for unit, days, opens, closes in h["hours"]:
                if unit_sub and unit_sub not in unit.lower():
                    continue
                if td is not None and td not in day_indexes(days):
                    continue
                if closes_ge and closes < closes_ge:
                    continue
                if morning and opens > "08:30":
                    continue
                out.add(hid)
                break
        return out

    add("Jam Operasional", "Poliklinik buka hari Sabtu", hours_match("poliklinik", "sabtu"))
    add("Jam Operasional", "Poliklinik buka hari Minggu", hours_match("poliklinik", "minggu"))
    add("Jam Operasional", "Poliklinik buka hari Senin", hours_match("poliklinik", "senin"))
    add("Jam Operasional", "Poli yang buka sampai jam 8 malam", hours_match("poliklinik", closes_ge="20:00"))
    add("Jam Operasional", "Rumah sakit dengan pendaftaran pagi", hours_match("pendaftaran", morning=True))
    add("Jam Operasional", "Rumah sakit dengan layanan hari Senin", hours_match("", "senin"))
    add("Jam Operasional", "Rumah sakit dengan layanan hari Minggu", hours_match("", "minggu"))
    add("Jam Operasional", "Poliklinik buka hari Sabtu di Medan", hours_match("poliklinik", "sabtu") & medan_ids)
    add("Jam Operasional", "IGD 24 jam di Siantar", igd_ids & siantar_ids)
    add("Jam Operasional", "buka sekarang", None, check_notice_substr="WIB")

    # 9. Semantic Concept, Autocomplete & Ranking (15)
    add("Semantic & Ranking", "Pencitraan medis", rad_ids | ct_ids | usg_ids)
    add("Semantic & Ranking", "Perawatan intensif", icu_ids | nicu_ids | picu_ids | hcu_ids | iccu_ids)
    add("Semantic & Ranking", "Layanan kesehatan anak", anak_ids | nicu_ids | picu_ids)
    add("Semantic & Ranking", "Kesehatan ibu dan kandungan", obgyn_ids)
    add("Semantic & Ranking", "Pemeriksaan laboratorium", lab_ids | ids_where(lambda h: "Patologi Klinik" in h["services"] or "Laboratorium mikrobiologi" in h["services"]))
    add("Semantic & Ranking", "RSUP H. Adam Malik", adam_malik, top1="rs-171")
    add("Semantic & Ranking", "Adam Malik", adam_malik, top1="rs-171")
    add("Semantic & Ranking", "1278013", ids_where(lambda h: h["code"] == "1278013"))
    add("Semantic & Ranking", "jan", None, endpoint="suggest", expect_min=3)
    add("Semantic & Ranking", "med", None, endpoint="suggest", expect_min=3)
    add("Semantic & Ranking", "ada", None, endpoint="suggest", expect_min=1)
    add("Semantic & Ranking", "icu", None, endpoint="suggest", expect_min=1)
    add("Semantic & Ranking", "sia", None, endpoint="suggest", expect_min=1)
    add("Semantic & Ranking", "Rumah sakit kelas B di Medan", kelas_b & medan_ids, params={"kelas": "B", "kabkota": "Kota Medan"})
    add("Semantic & Ranking", "", None, params={"limit": 20, "offset": 0}, expect_count=20)

    # 10. Keamanan & Edge Case (15)
    for sec_q in [
        ".*",
        "[a-z]+",
        "(",
        '"',
        "'",
        "\\",
        '"} UNION {',
        "(a+)+$",
        "SELECT * WHERE {?s ?p ?o}",
        "<script>alert(1)</script>",
        "'; DROP TABLE hospitals; --",
        "a" * 241,
        "xyzzy_tidak_ada_rs_12345",
        "Rumah sakit di Mars",
    ]:
        add("Keamanan & Edge Case", sec_q, set(), is_security=True)
    add("Keamanan & Edge Case", "   ", all_ids, is_security=True)

    return S


def run_suite():
    gt = load_ground_truth()
    scenarios = build_scenarios(gt)
    print(f"Loaded ground truth: {len(gt)} hospitals, running {len(scenarios)} scenarios against {API_BASE}...")

    results = []
    client = httpx.Client(base_url=API_BASE, timeout=15.0)

    # Warm up cache
    client.get("/api/search", params={"limit": 1})

    for sc in scenarios:
        t0 = time.perf_counter()
        passed = True
        reason = ""
        actual_total = 0
        actual_ids: list[str] = []
        top1_hit = None
        top3_hit = None
        rr = None
        prec = None
        rec = None
        f1 = None
        dup_count = 0

        try:
            if sc.get("endpoint") == "suggest":
                r = client.get("/api/search/suggestions", params={"q": sc["query"], "limit": 8})
                dt = (time.perf_counter() - t0) * 1000
                if r.status_code != 200:
                    passed = False
                    reason = f"HTTP {r.status_code}"
                else:
                    items = r.json().get("items", [])
                    actual_total = len(items)
                    if actual_total < sc.get("expect_min", 1):
                        passed = False
                        reason = f"Expected >= {sc.get('expect_min', 1)} suggestions, got {actual_total}"
            else:
                params = {"q": sc["query"], "limit": 500}
                params.update(sc.get("params") or {})
                r = client.get("/api/search", params=params)
                dt = (time.perf_counter() - t0) * 1000

                if len(sc["query"]) > 240:
                    if r.status_code != 422:
                        passed = False
                        reason = f"Expected 422 for >240 chars, got {r.status_code}"
                elif r.status_code != 200:
                    passed = False
                    reason = f"HTTP {r.status_code}: {r.text[:120]}"
                else:
                    data = r.json()
                    items = data.get("items", [])
                    actual_total = data.get("total", len(items))
                    actual_ids = [x["id"] for x in items]
                    dup_count = len(actual_ids) - len(set(actual_ids))
                    if dup_count > 0:
                        passed = False
                        reason = f"Duplicate IDs: {dup_count}"

                    if sc.get("expect_notice") and not data.get("notices"):
                        passed = False
                        reason = "Expected OWA notice, got none"
                    if sc.get("check_notice_substr"):
                        if not any(sc["check_notice_substr"] in n for n in data.get("notices", [])):
                            passed = False
                            reason = f"Expected notice containing {sc['check_notice_substr']}"
                    if sc.get("expect_count") is not None and len(items) != sc["expect_count"]:
                        passed = False
                        reason = f"Expected {sc['expect_count']} items, got {len(items)}"

                    exp = sc.get("expected_ids")
                    if exp is not None:
                        act_set = set(actual_ids)
                        if len(exp) == 0 and len(act_set) == 0:
                            prec = rec = f1 = 1.0
                        elif len(exp) == 0:
                            prec = rec = f1 = 0.0
                            passed = False
                            reason = f"Expected 0 results, got {len(act_set)}"
                        else:
                            tp = len(act_set & exp)
                            prec = tp / len(act_set) if act_set else 0.0
                            rec = tp / len(exp)
                            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
                            if prec < 1.0 or rec < 1.0:
                                missing = sorted(exp - act_set)[:5]
                                extra = sorted(act_set - exp)[:5]
                                passed = False
                                reason = f"P={prec:.3f} R={rec:.3f} missing={missing} extra={extra}"

                        if sc.get("top1"):
                            t1 = sc["top1"]
                            top1_hit = bool(actual_ids and actual_ids[0] == t1)
                            top3_hit = t1 in actual_ids[:3]
                            rr = (1.0 / (actual_ids.index(t1) + 1)) if t1 in actual_ids else 0.0
                            if not top1_hit:
                                passed = False
                                reason = f"Top-1 expected {t1}, got {actual_ids[0] if actual_ids else None}"
        except Exception as e:
            dt = (time.perf_counter() - t0) * 1000
            passed = False
            reason = f"Exception: {e}"

        results.append({
            "id": sc["id"],
            "category": sc["category"],
            "query": sc["query"][:60],
            "expected_count": len(sc["expected_ids"]) if sc.get("expected_ids") is not None else "",
            "actual_total": actual_total,
            "actual_top3": ",".join(actual_ids[:3]),
            "status": "PASS" if passed else "FAIL",
            "response_ms": round(dt, 2),
            "precision": round(prec, 4) if prec is not None else "",
            "recall": round(rec, 4) if rec is not None else "",
            "f1": round(f1, 4) if f1 is not None else "",
            "top1_hit": top1_hit if top1_hit is not None else "",
            "top3_hit": top3_hit if top3_hit is not None else "",
            "mrr": round(rr, 4) if rr is not None else "",
            "duplicates": dup_count,
            "failure_reason": reason,
        })

    # Save JSON & CSV
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    with open(docs_dir / "search_test_results_200.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    with open(docs_dir / "search_test_results_200.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    # Compute summary metrics
    total = len(results)
    passed_n = sum(1 for r in results if r["status"] == "PASS")
    failed = [r for r in results if r["status"] == "FAIL"]
    precs = [r["precision"] for r in results if isinstance(r["precision"], float)]
    recs = [r["recall"] for r in results if isinstance(r["recall"], float)]
    f1s = [r["f1"] for r in results if isinstance(r["f1"], float)]
    t1s = [r["top1_hit"] for r in results if isinstance(r["top1_hit"], bool)]
    t3s = [r["top3_hit"] for r in results if isinstance(r["top3_hit"], bool)]
    mrrs = [r["mrr"] for r in results if isinstance(r["mrr"], float)]
    typo_rows = [r for r in results if r["category"] == "Typo & Fuzzy"]
    sec_rows = [r for r in results if r["category"] == "Keamanan & Edge Case"]
    auto_times = [r["response_ms"] for r in results if r["category"] == "Semantic & Ranking" and len(r["query"]) <= 4]
    complex_times = [r["response_ms"] for r in results if r["category"] in ("Natural Language", "Boolean Search")]
    simple_times = [r["response_ms"] for r in results if r["category"] in ("Nama & Normalisasi", "Wilayah & Alamat", "Layanan & Fasilitas")]

    def pct(vals, p):
        if not vals:
            return 0.0
        s = sorted(vals)
        idx = min(len(s) - 1, math.ceil(p / 100 * len(s)) - 1)
        return round(s[idx], 2)

    summary = {
        "total_scenarios": total,
        "passed": passed_n,
        "failed": len(failed),
        "pass_rate": round(passed_n / total * 100, 2),
        "mean_precision": round(statistics.mean(precs) * 100, 2) if precs else 0,
        "mean_recall": round(statistics.mean(recs) * 100, 2) if recs else 0,
        "mean_f1": round(statistics.mean(f1s) * 100, 2) if f1s else 0,
        "top1_accuracy": round(sum(t1s) / len(t1s) * 100, 2) if t1s else 0,
        "top3_accuracy": round(sum(t3s) / len(t3s) * 100, 2) if t3s else 0,
        "mrr": round(statistics.mean(mrrs), 4) if mrrs else 0,
        "typo_recovery_rate": round(sum(1 for r in typo_rows if r["status"] == "PASS") / len(typo_rows) * 100, 2),
        "security_pass_rate": round(sum(1 for r in sec_rows if r["status"] == "PASS") / len(sec_rows) * 100, 2),
        "duplicate_rate": round(sum(r["duplicates"] for r in results) / total * 100, 4),
        "simple_p50_ms": pct(simple_times, 50),
        "simple_p95_ms": pct(simple_times, 95),
        "complex_p50_ms": pct(complex_times, 50),
        "complex_p95_ms": pct(complex_times, 95),
        "autocomplete_p95_ms": pct(auto_times, 95),
    }
    print("SUMMARY:", json.dumps(summary, indent=2))
    if failed:
        print(f"FAILED ({len(failed)}):")
        for r in failed[:20]:
            print(" ", r["id"], r["category"], repr(r["query"]), "->", r["failure_reason"])
    return summary, failed


class HybridSearch200Tests(unittest.TestCase):
    def test_200_scenarios_live(self):
        summary, failed = run_suite()
        self.assertGreaterEqual(summary["total_scenarios"], 200)
        self.assertEqual(summary["duplicate_rate"], 0.0)
        self.assertEqual(summary["security_pass_rate"], 100.0)
        self.assertEqual(len(failed), 0, f"{len(failed)} scenarios failed")


if __name__ == "__main__":
    run_suite()
