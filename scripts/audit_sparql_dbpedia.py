#!/usr/bin/env python3
"""CariSehat Patch 04: non-destructive SPARQL / DBpedia runtime diagnostics.
Only SELECT requests. Does not update RDF, DB, or runtime configuration.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import httpx

FUSEKI = os.environ.get('FUSEKI_URL', 'http://fuseki:3030/hospital').rstrip('/') + '/query'
DBPEDIA = 'https://dbpedia.org/sparql'
OUTPUT = Path('docs/semantic-audit-output/patch04')
PREFIX = '''PREFIX hf: <http://carisehat.id/ontology/>
PREFIX schema: <https://schema.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
'''
TESTS = [
 ('hospital_count', 'SELECT (COUNT(DISTINCT ?rs) AS ?count) WHERE { ?rs a hf:RumahSakit . }'),
 ('cities_count', 'SELECT (COUNT(DISTINCT ?city) AS ?count) WHERE { ?city a hf:KabupatenKota . }'),
 ('linked_regions', '''SELECT (COUNT(DISTINCT ?region) AS ?count) WHERE {
     ?region owl:sameAs ?external . FILTER(STRSTARTS(STR(?external), "http://dbpedia.org/resource/")) }'''),
 ('hospital_sample', '''SELECT ?rs ?name ?cityName WHERE {
    ?rs a hf:RumahSakit ; schema:name ?name ; hf:beradaDiKabupatenKota ?city .
    ?city rdfs:label ?cityName . } ORDER BY ?name LIMIT 3'''),
 ('regional_grouping', '''SELECT ?cityName (COUNT(DISTINCT ?rs) AS ?count) WHERE {
    ?rs a hf:RumahSakit ; hf:beradaDiKabupatenKota ?city .
    ?city rdfs:label ?cityName . } GROUP BY ?cityName ORDER BY DESC(?count) LIMIT 5'''),
 ('linked_hospital_example', '''SELECT ?name ?cityName ?dbpedia WHERE {
    ?rs a hf:RumahSakit ; schema:name ?name ; hf:beradaDiKabupatenKota ?city .
    ?city rdfs:label ?cityName ; owl:sameAs ?dbpedia .
    FILTER(STRSTARTS(STR(?dbpedia), "http://dbpedia.org/resource/"))
    } ORDER BY ?name LIMIT 3'''),
]

def query(client, url, sparql):
    start = time.monotonic()
    try:
        response = client.post(url, data={'query': sparql},
            headers={'Accept': 'application/sparql-results+json'}, timeout=15.0)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload.get('results', {}).get('bindings'), list):
            raise ValueError('Unexpected SPARQL JSON result')
        return {'status': 'PASS', 'rows': [
            {k: v.get('value') for k, v in row.items()} for row in payload['results']['bindings']
        ], 'elapsed_ms': round((time.monotonic()-start)*1000)}
    except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
        return {'status':'BLOCKED', 'reason':type(exc).__name__,
                'http_status': getattr(getattr(exc,'response',None),'status_code',None),
                'elapsed_ms':round((time.monotonic()-start)*1000)}

def main():
    report = {'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope':'runtime SELECT only; no updates; DBpedia availability not guaranteed',
              'fuseki_endpoint':FUSEKI,'dbpedia_endpoint':DBPEDIA,'internal':{},'external':{}}
    with httpx.Client(follow_redirects=False) as client:
        for name, sparql in TESTS:
            r=query(client, FUSEKI, PREFIX+sparql)
            report['internal'][name]=r
            print(f'{name}: {r["status"]} ({len(r.get("rows",[]))} rows)')
        external_query='''PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?label WHERE { <http://dbpedia.org/resource/Medan> rdfs:label ?label .
FILTER(LANGMATCHES(LANG(?label), "en")) } LIMIT 1'''
        # External endpoints commonly require GET and may throttle / block.
        start=time.monotonic()
        try:
            response=client.get(DBPEDIA,params={'query':external_query,'format':'application/sparql-results+json'},
                headers={'Accept':'application/sparql-results+json','User-Agent':'CariSehat-semantic-audit/1.0 (student project)'},timeout=12.0)
            response.raise_for_status()
            rows=response.json().get('results',{}).get('bindings',[])
            report['external']={'status':'PASS' if rows else 'FAIL',
                'row_count':len(rows),'sample_label': rows[0].get('label',{}).get('value') if rows else None,
                'elapsed_ms':round((time.monotonic()-start)*1000)}
        except (httpx.HTTPError,ValueError,json.JSONDecodeError) as exc:
            report['external']={'status':'BLOCKED','reason':type(exc).__name__,
                'http_status':getattr(getattr(exc,'response',None),'status_code',None),
                'elapsed_ms':round((time.monotonic()-start)*1000)}
    # Verify result semantics. A successful HTTP response does NOT prove counts.
    expected={'hospital_count':206,'cities_count':33,'linked_regions':34}
    for name, value in expected.items():
        r=report['internal'][name]
        if r['status']=='PASS':
            try: actual=int(r['rows'][0]['count'])
            except (IndexError,KeyError,TypeError,ValueError):actual=None
            r['count']=actual
            r['expected']=value
            if actual != value:r['status']='FAIL'
    for name in ['hospital_sample','regional_grouping','linked_hospital_example']:
        r=report['internal'][name]
        if r['status']=='PASS' and not r['rows']:
            r['status']='FAIL'
    statuses=[r['status'] for r in report['internal'].values()]
    report['overall_internal']='PASS' if all(s=='PASS' for s in statuses) else ('FAIL' if 'FAIL' in statuses else 'BLOCKED')
    report['overall_external']=report['external']['status']
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/'sparql_dbpedia_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'internal':report['overall_internal'],'dbpedia':report['overall_external'],
        'counts':{k:report['internal'][k].get('count') for k in expected},
        'output':str(OUTPUT/'sparql_dbpedia_report.json')},ensure_ascii=False,indent=2))
    return 0 if report['overall_internal']=='PASS' else 2

if __name__ == '__main__':
    sys.exit(main())
