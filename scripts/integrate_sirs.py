"""Validate SIRS inputs and prepare an isolated, reversible named graph.

No live writes. Output lives outside rdf_loader's default-graph glob.
"""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from rdflib import Graph, Namespace, RDF, Literal, URIRef

ROOT = Path(__file__).resolve().parents[1]
CS = Namespace('http://carisehat.id/ontology/sirs/')
HF = Namespace('http://carisehat.id/ontology/')
GRAPH = 'http://carisehat.id/graph/sirs/2026-11-19'
ALLOWED = {'diagnostik_pemeriksaan', 'gawat_darurat_terlapor'}


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def prepare(root=ROOT):
    source = root / 'data/enrichment/tahap3'
    master = rows(root / 'data/enrichment/tahap1/CariSehat_Master_206_Rekonsiliasi_SIRS.csv')
    dictionary = rows(source / 'kamus_300_layanan.csv')
    services = rows(source / 'pelayanan_206_normalisasi.csv')
    mapping = {r['id_carisehat']: r['kode_rs_kemenkes'] for r in master}
    assert len(master) == len(mapping) == len(set(mapping.values())) == 206, 'identity duplicates'
    assert all(r['status_pencocokan'] in {'MATCH_EXACT_NAME_CITY','MATCH_MANUAL_REVIEWED'} for r in master), 'unresolved identity'
    labels = {r['label_asli']: r for r in dictionary}
    assert len(labels) == len(dictionary) == 300, 'dictionary duplicates'
    base = Graph().parse(root / 'semantic/rdf/hospitals-sumut.ttl')
    hospital_uris = {str(s).rsplit('/', 1)[-1]: s for s in base.subjects(RDF.type, HF.RumahSakit)}
    assert set(hospital_uris) == set(mapping), 'master/base hospital mismatch'
    graph = Graph().parse(source / 'carisehat_sirs_206_overlay_STAGING.ttl')
    assert len(graph) == 81967, 'unexpected staging triple count'
    observations = set(graph.subjects(RDF.type, CS.PelayananTercatat))
    assert len(observations) == len(services) == 10219
    assert len({r['record_id'] for r in services}) == len(services)
    assert len({(r['id_carisehat'],r['pelayanan_tercatat']) for r in services}) == len(services)
    assert set(graph.subjects(CS.kodeRegistrasiKemenkes, None)) == set(hospital_uris.values())
    for ident, uri in hospital_uris.items():
        assert list(graph.objects(uri, CS.kodeRegistrasiKemenkes)) == [Literal(mapping[ident])], ident
    accepted, excluded = [], Counter()
    for row in services:
        ident, label = row['id_carisehat'], row['pelayanan_tercatat']
        assert mapping[ident] == row['kode_rs_kemenkes'], ident
        uri = hospital_uris[ident]
        obs = URIRef('http://carisehat.id/sirs-observation/' + row['record_id'])
        assert obs in observations
        assert (uri, CS.catatanPelayanan, obs) in graph
        assert graph.value(obs, CS.untukRumahSakit) == uri
        expected_source = 'https://sirs.kemkes.go.id/fo/home/profile_rs/' + mapping[ident]
        assert row['url_sumber'] == expected_source
        for predicate, value in [(CS.labelPelayanan,label),(CS.kategoriKurasi,row['kategori']),
                                 (CS.sumberProfil,expected_source),(CS.tanggalPengambilan,row['waktu_ambil_utc']),
                                 (CS.statusPublikasi,row['status_publikasi'])]:
            values = list(graph.objects(obs,predicate))
            assert len(values) == 1 and str(values[0]) == value, (ident,label,str(predicate))
        assert datetime.fromisoformat(row['waktu_ambil_utc']).tzinfo
        entry = labels[label]
        assert entry['kategori'] == row['kategori']
        graph.add((obs, CS.statusKurasi, Literal(entry['status_validasi_kategori'])))
        if row['kategori'] in ALLOWED and entry['status_validasi_kategori'] == 'RULE_REVIEWED':
            graph.add((obs, CS.layakPencarian, Literal(True)))
            accepted.append(row)
        else:
            excluded[row['kategori']] += 1
    assert not list(graph.triples((None,HF.menyediakanLayanan,None)))
    beds = rows(source / 'kapasitas_tempat_tidur_206_staging.csv')
    staff = rows(source / 'sdm_206_staging.csv')
    assert len(beds) == 3466 and len(staff) == 9362
    for row in beds + staff:
        assert mapping[row['id_carisehat']] == row['kode_rs_kemenkes']
        assert row['url_sumber'] == 'https://sirs.kemkes.go.id/fo/home/profile_rs/' + row['kode_rs_kemenkes']
        assert datetime.fromisoformat(row['waktu_ambil_utc']).tzinfo
        assert row['status_publikasi'] == 'STAGING_TIDAK_REALTIME'
    report = {'hospitals':206, 'staging_triples':81967, 'prepared_triples':len(graph),
              'observations':len(services), 'accepted_observations':len(accepted),
              'accepted_labels':len({r['pelayanan_tercatat'] for r in accepted}),
              'hospitals_with_accepted_services':len({r['id_carisehat'] for r in accepted}),
              'excluded_observations':dict(excluded),
              'categories':dict(Counter(r['kategori'] for r in dictionary)),
              'bed_rows_not_published':len(beds), 'staff_rows_not_published':len(staff),
              'staff_missing_group':sum(not r['grup_sdm'] for r in staff),
              'named_graph':GRAPH, 'policy':'RULE_REVIEWED diagnostic/emergency only; no clinical inference',
              'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.iterdir()) if p.is_file()}}
    return graph, report


if __name__ == '__main__':
    graph, report = prepare()
    output = ROOT / 'semantic/sirs'
    output.mkdir(exist_ok=True)
    graph.serialize(output / 'services-reviewed.ttl', format='turtle')
    assert len(Graph().parse(output / 'services-reviewed.ttl')) == len(graph)
    (output / 'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'sha256'},indent=2))
