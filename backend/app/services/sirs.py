"""Strict publication policy for reported SIRS services; no inferred fallback."""
from functools import lru_cache
from pathlib import Path
from rdflib import Graph, Namespace, Literal
from app.config import settings

CS = Namespace('http://carisehat.id/ontology/sirs/')
GRAPH_URI = 'http://carisehat.id/graph/sirs/2026-11-19'
EMERGENCY = 'Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu'
NOTICE = ('Layanan dilaporkan dalam profil SIRS, bukan verifikasi operasional atau ketersediaan saat ini. '
          'Label klinis yang belum direview tidak disertakan. Konfirmasikan ke rumah sakit.')


def pattern(label='?lay', observation='?sirsObs'):
    return (f'GRAPH <{GRAPH_URI}> {{ ?rs <{CS.catatanPelayanan}> {observation} . '
            f'{observation} <{CS.layakPencarian}> true ; <{CS.labelPelayanan}> {label} . }}')


@lru_cache(maxsize=1)
def records():
    path = Path(settings.rdf_dir).parent / 'sirs/services-reviewed.ttl'
    if not path.exists():
        path = Path(__file__).resolve().parents[3] / 'semantic/sirs/services-reviewed.ttl'
    if not path.exists():
        return {}
    graph = Graph().parse(path)
    result = {}
    for obs in graph.subjects(CS.layakPencarian, Literal(True)):
        uri = graph.value(obs, CS.untukRumahSakit)
        ident = str(uri).rsplit('/',1)[-1]
        item = {'record_uri':str(obs), 'label':str(graph.value(obs,CS.labelPelayanan)),
                'category':str(graph.value(obs,CS.kategoriKurasi)),
                'source_url':str(graph.value(obs,CS.sumberProfil)),
                'retrieved_at':str(graph.value(obs,CS.tanggalPengambilan)),
                'source_status':str(graph.value(obs,CS.statusPublikasi)),
                'category_status':str(graph.value(obs,CS.statusKurasi)),
                'verification_status':'reported_not_operationally_verified'}
        result.setdefault(ident,[]).append(item)
    return result


def annotate(hospital):
    hospital['layanan_source'] = 'SIRS Kemenkes'
    hospital['layanan_notice'] = NOTICE
    labels = set(hospital.get('layanan',[]))
    hospital['layanan_facts'] = [dict(r) for r in records().get(hospital['id'],[]) if r['label'] in labels]
    hospital['fasilitas_status'] = 'legacy_unverified'
    hospital['bpjs_status'] = 'not_verified_by_sirs_services'
    return hospital
