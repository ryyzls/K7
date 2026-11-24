"""Read-only HTTP audit; use --base explicitly to distinguish fixture from live."""
import argparse
import concurrent.futures
import json
import statistics
import time
from pathlib import Path
import httpx
from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.compare import isomorphic

parser=argparse.ArgumentParser()
parser.add_argument('--base',required=True)
parser.add_argument('--label',required=True)
args=parser.parse_args()
out=Path('docs/semantic-audit-output/2026-11-24');out.mkdir(parents=True,exist_ok=True)
results=[]
client=httpx.Client(base_url=args.base,timeout=90)
def check(name,fn):
    start=time.perf_counter()
    try: detail=fn();status='PASS'
    except Exception as e: detail=str(e);status='FAIL'
    results.append({'name':name,'status':status,'detail':detail,'seconds':round(time.perf_counter()-start,3)})
    print(name,status,flush=True)

def get(path,**kwargs):
    r=client.get(path,**kwargs);assert r.status_code==200,(path,r.status_code);return r

def catalog():
    rows=get('/api/search?limit=500').json()['items']
    assert len(rows)==206 and len({r['id'] for r in rows})==206
    assert len({r['kode_kemenkes'] for r in rows})==206
    assert len({r['kabkota'] for r in rows})==33
    return {'hospitals':206,'regions':33,'codes':206,'bytes':len(json.dumps(rows))}
check('catalog_206',catalog)

def profiles():
    def one(i):
        ident=f'rs-{i:03}'; r=get('/api/hospitals/'+ident).json()
        assert r['id']==ident
        assert all(k in r for k in ['kode_kemenkes','nama','jenis','kelas','alamat','direktur','kepemilikan','luas_tanah','luas_bangunan','jam_operasional','spesialisasi','email'])
        return (ident,r['kode_kemenkes'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: identities=list(pool.map(one,range(1,207)))
    assert len(set(code for _,code in identities))==206
    return '206 details with unique matching identities and expected fields'
check('all_206_profiles',profiles)

for params in [{'kelas':'A'},{'jenis':'Khusus'},{'kabkota':'Kota Medan'},{'kelas':'B','jenis':'Umum','kabkota':'Kota Medan'},{'spesialisasi':'Mata'},{'q':'dokter jantung'}]:
    def test(p=params):
        data=get('/api/search',params={**p,'limit':500}).json(); rows=data['items'];assert rows
        for key,value in p.items():
            if key in ('kelas','jenis','kabkota'):assert all(row[key]==value for row in rows)
            if key=='spesialisasi':assert all(value in row['spesialisasi'] for row in rows)
        return {'count':len(rows),'query_type':data.get('query_type')}
    check('filter_'+json.dumps(params),test)

def pagination():
    a=get('/api/search?limit=10&offset=0').json()['items'];b=get('/api/search?limit=10&offset=10').json()['items']
    assert len(a)==len(b)==10 and not ({r['id'] for r in a}&{r['id'] for r in b});return 'two disjoint pages'
check('pagination',pagination)
for q in ['zzzzzzzzznotfoundzzzz','\" } UNION { ?s ?p ?o } #','<script>alert(1)</script>']:
    check('search_edge_'+q,lambda q=q: {'count':len(get('/api/search',params={'q':q}).json()['items'])})

for ids in ['rs-001,rs-008','rs-001,rs-008,rs-171']:
    def compare(ids=ids):
        d=get('/api/compare',params={'ids':ids}).json();assert {h['id'] for h in d['hospitals']}==set(ids.split(','));return d['count']
    check('compare_'+ids,compare)
def alternatives():
    d=get('/api/hospitals/rs-171/alternatives').json();assert all(h['id']!='rs-171' for h in d['alternatives']);return len(d['alternatives'])
check('alternatives_exclude_self',alternatives)

def exports():
    ttl=get('/rs/rs-007.ttl');xml=get('/rs/rs-007.rdf')
    assert 'text/turtle' in ttl.headers['content-type'] and 'application/rdf+xml' in xml.headers['content-type']
    g=Graph().parse(data=ttl.text,format='turtle');h=Graph().parse(data=xml.text,format='xml');assert isomorphic(g,h)
    assert (URIRef('http://localhost:8000/rs/rs-007'),Namespace('https://schema.org/').email,None) in g
    return {'triples':len(g),'roundtrip_isomorphic':True}
check('RDF_XML_Turtle_roundtrip',exports)
for path in ['/rs/rs-007','/sparql']:
    check('page_'+path,lambda path=path:{'bytes':len(get(path).content)})
for query in ['SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {?s a <http://carisehat.id/ontology/RumahSakit>}','ASK {?s ?p ?o}','CONSTRUCT {?s ?p ?o} WHERE {?s ?p ?o} LIMIT 5','DESCRIBE ?s WHERE {?s a <http://carisehat.id/ontology/RumahSakit>} LIMIT 1']:
    def sparql(q=query):
        r=client.post('/sparql/query',content=q,headers={'Content-Type':'application/sparql-query','Accept':'application/sparql-results+json' if q.startswith(('SELECT','ASK')) else 'text/turtle'})
        assert r.status_code==200,r.status_code
        if q.startswith('SELECT'):assert r.json()['results']['bindings'][0]['n']['value']=='206'
        elif q.startswith('ASK'):assert r.json()['boolean']
        else:assert len(Graph().parse(data=r.text,format='turtle'))>0
        return r.status_code
    check('SPARQL_'+query.split()[0],sparql)
for query in ['CLEAR ALL','INSERT DATA {<urn:a> <urn:b> <urn:c>}','SELECT * WHERE {SERVICE <http://127.0.0.1/> {?s ?p ?o}}']:
    def rejected(q=query):
        r=client.post('/sparql/query',content=q,headers={'Content-Type':'application/sparql-query'});assert r.status_code==400;return r.status_code
    check('blocked_'+query.split()[0],rejected)
def operator_gate():
    r=client.get('/api/booking/rs/rs-001');assert r.status_code==403;return 403
check('operator_default_deny',operator_gate)
def performance():
    samples=[]
    for _ in range(20):
        start=time.perf_counter();get('/api/search?kelas=A&limit=500');samples.append((time.perf_counter()-start)*1000)
    return {'n':20,'median_ms':round(statistics.median(samples),1),'p95_ms':round(sorted(samples)[18],1),'environment':args.label}
check('search_performance',performance)
client.close()
(out/f'http-{args.label}.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps({'label':args.label,'passed':sum(r['status']=='PASS' for r in results),'failed':sum(r['status']=='FAIL' for r in results)}))
