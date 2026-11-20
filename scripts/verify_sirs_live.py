"""Read-only SIRS live checks, no booking/SQL writes or paid AI requests."""
import csv
import json
from pathlib import Path
import httpx
from rdflib import Graph, Namespace, Literal
from rdflib.compare import isomorphic
from integrate_sirs import ROOT, GRAPH

CS=Namespace('http://carisehat.id/ontology/sirs/')
graph=Graph().parse(ROOT/'semantic/sirs/services-reviewed.ttl')
expected={}
for obs in graph.subjects(CS.layakPencarian,Literal(True)):
    ident=str(graph.value(obs,CS.untukRumahSakit)).rsplit('/',1)[-1]
    expected.setdefault(ident,set()).add(str(graph.value(obs,CS.labelPelayanan)))
tests=[]
def check(name,fn):
    try:
        detail=fn()
        tests.append({'name':name,'status':'PASS','detail':detail})
    except Exception as exc:
        tests.append({'name':name,'status':'FAIL','detail':str(exc)[:400]})
    print(name,tests[-1]['status'],flush=True)

with httpx.Client(base_url='http://127.0.0.1:8000',timeout=40) as client:
    def search(params=None):
        r=client.get('/api/search',params={'limit':500,**(params or {})})
        assert r.status_code==200,r.status_code
        return r.json()['items']
    def all_hospitals():
        hospitals=search()
        assert len(hospitals)==len({h['id'] for h in hospitals})==206
        for h in hospitals:
            assert set(h['layanan'])==expected.get(h['id'],set()),h['id']
            assert {f['label'] for f in h['layanan_facts']}==set(h['layanan'])
            assert all(f['category_status']=='RULE_REVIEWED' and f['source_url'] and f['retrieved_at'] for f in h['layanan_facts'])
        return 'HTTP 200; 206 identities; every service matches curated SIRS; complete provenance'
    check('206_hospitals_exact_services_provenance',all_hospitals)
    def filters():
        r=client.get('/api/filters');assert r.status_code==200
        assert set(r.json()['layanan'])==set().union(*expected.values())
        for label in r.json()['layanan']:
            actual={h['id'] for h in search({'layanan':label})}
            assert actual=={ident for ident,labels in expected.items() if label in labels},label
        return 'HTTP 200; all 35 filters return exact hospital sets'
    check('35_service_filters',filters)
    def excluded():
        assert search({'layanan':'Pelayanan medik dasar / umum'})==[]
        assert search({'layanan':'" } UNION { ?s ?p ?o } #'})==[]
        return 'HTTP 200; withheld clinical label and injected literal return no matches'
    check('clinical_and_injection_excluded',excluded)
    def export():
        r=client.get('/rs/rs-001.ttl');assert r.status_code==200
        out=Graph().parse(data=r.text,format='turtle')
        assert len(list(out.subjects(CS.layakPencarian,Literal(True))))==len(expected['rs-001'])
        assert not list(out.triples((None,Namespace('http://carisehat.id/ontology/').menyediakanLayanan,None)))
        return 'HTTP 200; exported observations have provenance; no inferred service predicate'
    check('export_curated_observations',export)
    def security():
        for query in ['CLEAR ALL','DROP ALL','INSERT DATA { <urn:a> <urn:b> <urn:c> }']:
            r=client.post('/sparql/query',data={'query':query});assert r.status_code==400
        r=client.get('/api/booking/rs/rs-001'); assert r.status_code in (401,403),r.status_code
        return 'SPARQL UPDATE blocked HTTP 400; operator read gate denied'
    check('security_unchanged',security)

with httpx.Client(timeout=40) as client:
    def default_unchanged():
        r=client.get('http://127.0.0.1:3030/hospital/data',params={'default':''},headers={'Accept':'text/turtle'});r.raise_for_status()
        before=Graph().parse(ROOT/'scratch/sirs-backup-20261120/default-before.ttl')
        after=Graph().parse(data=r.text,format='turtle')
        assert isomorphic(before,after)
        return f'HTTP 200; default graph unchanged ({len(after)} triples)'
    check('default_graph_unchanged',default_unchanged)
output=ROOT/'docs/sirs-tests/live.json';output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(tests,indent=2),encoding='utf-8')
raise SystemExit(int(any(t['status']!='PASS' for t in tests)))
