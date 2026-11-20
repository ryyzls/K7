"""
Generate comprehensive RDF Turtle for CariSehat Final Semantic Freeze
Named Graph: http://carisehat.id/graph/enrichment/2026-11-20
"""
import json, pathlib
from datetime import datetime, timezone, timedelta
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, XSD

WIB = timezone(timedelta(hours=7))

ROOT = pathlib.Path(".")
DATA_DIR = ROOT / "data" / "enrichment" / "final_info_rs"
OUTPUT_TTL = ROOT / "semantic" / "named_graphs" / "carisehat-enrichment-freeze.ttl"

# Load data
profil_list = json.loads((DATA_DIR / "profil_lengkap_206.json").read_text(encoding='utf-8'))
kontak_list = json.loads((DATA_DIR / "kontak_dan_website_206.json").read_text(encoding='utf-8'))
jam_list = json.loads((DATA_DIR / "jam_operasional_unit_206.json").read_text(encoding='utf-8'))
fasilitas_list = json.loads((DATA_DIR / "fasilitas_medis_berbasis_bukti_206.json").read_text(encoding='utf-8'))
igd_list = json.loads((DATA_DIR / "igd_24jam_terlapor_206.json").read_text(encoding='utf-8'))

kontak_map = {r['id_carisehat']: r for r in kontak_list}
jam_map = {r['id_carisehat']: r for r in jam_list}
fasilitas_map = {r['id_carisehat']: r for r in fasilitas_list}
igd_map = {r['id_carisehat']: r for r in igd_list}

# Namespaces
CS = Namespace("http://carisehat.id/ontology/sirs/")
HF = Namespace("http://carisehat.id/ontology/")
SCHEMA = Namespace("https://schema.org/")
GRAPH_ENRICHMENT = URIRef("http://carisehat.id/graph/enrichment/2026-11-20")

g = Graph()
g.bind("cs", CS)
g.bind("hf", HF)
g.bind("schema", SCHEMA)
g.bind("xsd", XSD)
g.bind("rdfs", RDFS)

for p in profil_list:
    rs_id = p['id_carisehat']
    rs_uri = URIRef(f"http://localhost:8000/rs/{rs_id}")
    kode = p.get('kode_kemenkes', '')
    
    # Types & Identifiers
    g.add((rs_uri, RDF.type, HF.RumahSakit))
    g.add((rs_uri, CS.kodeRegistrasiKemenkes, Literal(kode)))
    
    # Profile
    if p.get('direktur'):
        g.add((rs_uri, SCHEMA.director, Literal(p['direktur'])))
    if p.get('kepemilikan'):
        g.add((rs_uri, HF.kepemilikanSirs, Literal(p['kepemilikan'])))
    if p.get('luas_tanah'):
        g.add((rs_uri, HF.luasTanah, Literal(p['luas_tanah'])))
    if p.get('luas_bangunan'):
        g.add((rs_uri, HF.luasBangunan, Literal(p['luas_bangunan'])))
        
    # Kontak & Website
    k = kontak_map.get(rs_id, {})
    if k.get('telepon'):
        g.add((rs_uri, SCHEMA.telephone, Literal(k['telepon'])))
    if k.get('website_url'):
        g.add((rs_uri, SCHEMA.url, URIRef(k['website_url'])))
        g.add((rs_uri, HF.statusWebsite, Literal(k.get('website_status', 'TERSEDIA'))))
    else:
        g.add((rs_uri, HF.statusWebsite, Literal("BELUM_TERSEDIA")))
        
    if k.get('email'):
        g.add((rs_uri, SCHEMA.email, Literal(k['email'])))
        g.add((rs_uri, HF.statusEmail, Literal(k.get('email_status', 'TERSEDIA'))))
    else:
        g.add((rs_uri, HF.statusEmail, Literal("BELUM_TERSEDIA")))
        
    # IGD 24 Jam
    igd_info = igd_map.get(rs_id, {})
    has_igd = igd_info.get('status_igd_24jam') == 'TERLAPOR_SIRS'
    g.add((rs_uri, HF.statusIgd24Jam, Literal("TERLAPOR_SIRS" if has_igd else "TIDAK_TERLAPOR")))
    
    # Jam Operasional
    j = jam_map.get(rs_id, {})
    g.add((rs_uri, HF.statusJamOperasional, Literal(j.get('status_jam_operasional', 'JAM_BELUM_TERSEDIA'))))
    
    units = j.get('units', {})
    for u_key, u_val in units.items():
        if isinstance(u_val, dict) and u_val.get('jam_display') and u_val.get('jam_display') != 'Belum tersedia':
            oh_node = BNode()
            g.add((rs_uri, SCHEMA.openingHoursSpecification, oh_node))
            g.add((oh_node, RDF.type, SCHEMA.OpeningHoursSpecification))
            g.add((oh_node, RDFS.label, Literal(u_val.get('unit', u_key))))
            g.add((oh_node, SCHEMA.description, Literal(u_val['jam_display'])))
            if u_val.get('jam_buka'):
                g.add((oh_node, SCHEMA.opens, Literal(u_val['jam_buka'])))
            if u_val.get('jam_tutup'):
                g.add((oh_node, SCHEMA.closes, Literal(u_val['jam_tutup'])))

    # Fasilitas Medis
    f = fasilitas_map.get(rs_id, {})
    tt_kritis = f.get('tempat_tidur_khusus', {})
    for bed_type, count in tt_kritis.items():
        if count and count > 0:
            bnode = BNode()
            g.add((rs_uri, HF.fasilitasKritis, bnode))
            g.add((bnode, RDF.type, HF.FasilitasTempatTidurKritis))
            g.add((bnode, CS.jenisFasilitas, Literal(bed_type)))
            g.add((bnode, CS.kapasitasTerlapor, Literal(count, datatype=XSD.integer)))
            
    diag = f.get('diagnostik_dan_penunjang', {})
    for d_name, available in diag.items():
        if available:
            g.add((rs_uri, HF.memilikiFasilitasDiagnostik, Literal(d_name)))

OUTPUT_TTL.parent.mkdir(parents=True, exist_ok=True)
g.serialize(OUTPUT_TTL, format="turtle")
print(f"Generated RDF Turtle: {OUTPUT_TTL} ({len(g)} triples)")
