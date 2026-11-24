"""Read-only RDF/data audit. Does not contact a database or mutate source datasets."""
import collections
import csv
import hashlib
import json
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/semantic-audit-output/2026-11-24'
HF=Namespace('http://carisehat.id/ontology/')
CS=Namespace('http://carisehat.id/ontology/sirs/')
SCHEMA=Namespace('https://schema.org/')
GEO=Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')

def main():
    graphs={}
    default=Graph()
    for path in sorted((ROOT/'semantic/rdf').glob('*.ttl')):
        default.parse(path)
    graphs['default']=default
    for key,path in [('sirs','semantic/sirs/services-reviewed.ttl'),('enrichment','semantic/named_graphs/carisehat-enrichment-freeze.ttl')]:
        graphs[key]=Graph().parse(ROOT/path)
    hospitals=set(default.subjects(RDF.type,HF.RumahSakit))
    expected={URIRef(f'http://localhost:8000/rs/rs-{i:03}') for i in range(1,207)}
    codes=collections.defaultdict(list)
    for h in hospitals:
        for code in graphs['sirs'].objects(h,CS.kodeRegistrasiKemenkes):codes[str(code)].append(str(h))
    profiles=json.loads((ROOT/'backend/app/data/final_info_rs/profil_lengkap_206.json').read_text(encoding='utf8'))
    mismatches=[p['id_carisehat'] for p in profiles if URIRef('http://localhost:8000/rs/'+p['id_carisehat']) not in
                [URIRef(h) for h in codes.get(p['kode_kemenkes'],[])]]
    coords=collections.defaultdict(list)
    for h in hospitals:
        coords[(str(default.value(h,GEO.lat)),str(default.value(h,GEO.long)))].append(str(h).rsplit('/',1)[-1])
    hours=list(csv.DictReader((ROOT/'data/enrichment/mass_discovery/candidate_hours.csv').open(encoding='utf-8-sig')))
    final=json.loads((ROOT/'backend/app/data/final_info_rs/jam_operasional_unit_206.json').read_text(encoding='utf8'))
    defaults=[p['id_carisehat'] for p in final if p.get('units',{}).get('poliklinik_rawat_jalan',{}).get('jam_buka')]
    notfound={r['id_carisehat'] for r in hours if r['status']=='NOT_FOUND'}
    duplicates={str(k):v for k,v in coords.items() if len(v)>1}
    known=set(default.subjects(RDF.type,None))
    ontology=Graph().parse(ROOT/'semantic/rdf/ontologi.ttl')
    defined=set(ontology.subjects(None,None))
    defined.update(Graph().parse(ROOT/'semantic/rdf/enrichment-ontology.ttl').subjects(None,None))
    undefined=sorted({str(p) for g in graphs.values() for _,p,_ in g if str(p).startswith(str(HF)) and p not in defined})
    result={
      'scope':'local files, not live Fuseki',
      'triples':{key:len(g) for key,g in graphs.items()},
      'hospitals':len(hospitals),'identity_exact':hospitals==expected,
      'regions':len(set(default.subjects(RDF.type,HF.KabupatenKota))),
      'unique_kemenkes_codes':len(codes),'duplicate_codes':{k:v for k,v in codes.items() if len(v)>1},
      'profile_identity_mismatches':mismatches,
      'sirs_observations':len(set(graphs['sirs'].subjects(CS.untukRumahSakit,None))),
      'invalid_typed_literals':sum(getattr(o,'ill_typed',False) is True for g in graphs.values() for _,_,o in g if isinstance(o,Literal)),
      'undefined_local_predicates':undefined,
      'duplicate_coordinate_groups':duplicates,
      'coordinate_sources':dict(collections.Counter(str(default.value(h,HF.sumberKoordinat)) for h in hospitals)),
      'candidate_hours_rows':len(hours),'candidate_hours_hospitals':len({r['id_carisehat'] for r in hours}),
      'candidate_hours_status':dict(collections.Counter(r['status'] for r in hours)),
      'legacy_final_hours_populated':len(defaults),'legacy_populated_despite_not_found':sorted(set(defaults)&notfound),
      'legacy_structured_schedule_hospitals':sum(any(u.get('jadwal') and u.get('sumber') for u in r['unit_operasional'] if 'poli' in u.get('unit','').lower()) for r in final),
      'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'semantic/rdf').glob('*.ttl')},
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'dataset-audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_hashes','duplicate_coordinate_groups','undefined_local_predicates')},ensure_ascii=True))
    assert hospitals==expected and len(codes)==206 and not mismatches

if __name__=='__main__':main()
