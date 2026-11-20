#!/usr/bin/env python3
"""Audit read-only CariSehat RDF; output ONLY to docs/semantic-audit-output.
Run from repository root: python scripts/audit_semantic_quality.py
Requires: pip install rdflib (already used by the project where available).
"""
from collections import Counter
from pathlib import Path
import csv
import json
import sys
from rdflib import Graph, Namespace, RDF, URIRef

ROOT = Path(__file__).resolve().parents[1]
HF = Namespace('http://carisehat.id/ontology/')
SCHEMA = Namespace('https://schema.org/')
GEO = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
RS_PREFIX = 'http://localhost:8000/rs/'


def main():
    dataset = ROOT / 'semantic/rdf/hospitals-sumut.ttl'
    coord_file = ROOT / 'data/koordinat.csv'
    website_file = ROOT / 'semantic/rdf/hospital-websites.ttl'
    if not dataset.is_file() or not coord_file.is_file():
        sys.exit('ERROR: Jalankan di root repo CariSehat, dengan file RDF/koordinat tersedia.')
    graph = Graph().parse(dataset, format='turtle')
    hospitals = sorted({s for s in graph.subjects(RDF.type, HF.RumahSakit)}, key=str)
    coords = {}
    with coord_file.open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            coords[r['kode']] = r
    web = Graph()
    if website_file.is_file():
        web.parse(website_file, format='turtle')
    rows = []
    for hospital in hospitals:
        hid = str(hospital).rsplit('/', 1)[-1]
        source = (coords.get(hid) or {}).get('sumber', '').strip().lower()
        status = str(web.value(hospital, HF.websiteStatus) or 'not_recorded')
        official_url = web.value(hospital, SCHEMA.url)
        name = str(graph.value(hospital, SCHEMA.name) or graph.value(hospital, HF.nama) or '')
        services = len(set(graph.objects(hospital, HF.menyediakanLayanan)))
        facilities = len(set(graph.objects(hospital, HF.memilikiFasilitas)))
        bpjs = graph.value(hospital, HF.menerimaBPJS)
        has_coords = graph.value(hospital, GEO.lat) is not None and graph.value(hospital, GEO.long) is not None
        flags = []
        if source in ('jalan', 'kabkota', ''): flags.append('coordinate_approximate_or_missing')
        if status == 'verified' and official_url is None: flags.append('website_verified_without_url')
        if status != 'verified' and official_url is not None: flags.append('website_url_without_verified_status')
        if services: flags.append('services_generated_not_individually_verified')
        if facilities: flags.append('facilities_generated_not_individually_verified')
        if bpjs is not None: flags.append('bpjs_generated_not_individually_verified')
        rows.append({'id':hid,'uri':str(hospital),'name':name,'coordinate_source':source or 'unknown',
                     'has_coordinates':str(has_coords).lower(),'website_status':status,
                     'website_url':str(official_url or ''),'service_links':services,
                     'facility_links':facilities,'bpjs_value':str(bpjs or ''),
                     'review_flags':';'.join(flags)})
    website_verified = sum(r['website_status']=='verified' for r in rows)
    result = {'hospital_count':len(rows),'rdf_triple_count':len(graph),
              'coordinate_sources':dict(sorted(Counter(r['coordinate_source'] for r in rows).items())),
              'website_statuses':dict(sorted(Counter(r['website_status'] for r in rows).items())),
              'website_verified':website_verified,
              'missing_coordinates':sum(r['has_coordinates']=='false' for r in rows),
              'service_links_total':sum(r['service_links'] for r in rows),
              'facility_links_total':sum(r['facility_links'] for r in rows),
              'warnings':[]}
    if len(rows)!=206:result['warnings'].append(f'Expected 206 hospitals, found {len(rows)}')
    missing_coords = sorted(set(r['id'] for r in rows)-set(coords))
    if missing_coords:result['warnings'].append('Missing coordinate CSV IDs: '+', '.join(missing_coords))
    out = ROOT/'docs/semantic-audit-output'
    out.mkdir(parents=True, exist_ok=True)
    with (out/'hospital_quality_review.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=list(rows[0]) if rows else ['id'])
        writer.writeheader();writer.writerows(rows)
    (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('Output:',out)
    print('NOTE: flags indicate review needs, not proof of incorrect hospital data.')
    return 0 if len(rows)==206 else 1

if __name__=='__main__':raise SystemExit(main())
