#!/usr/bin/env python3
"""CariSehat Patch 02: read-only RDF provenance audit + optional draft overlay.

Never updates Fuseki, production Turtle, or SQL. Output goes to docs only.
The origin of class-generated claims is determined from generator source logic,
NOT from a field-level official hospital verification.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD

ROOT = Path(__file__).resolve().parent.parent
HF = Namespace('http://carisehat.id/ontology/')
GEO = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
PROV = Namespace('http://www.w3.org/ns/prov#')
CS = Namespace('http://carisehat.id/provenance/')
RS_URI_BASE = 'http://localhost:8000/rs/'
GENERATED = {
    HF.menyediakanLayanan: 'classification_rule_not_hospital_verified',
    HF.memilikiFasilitas: 'classification_rule_not_hospital_verified',
    HF.menerimaBPJS: 'owner_class_rule_not_hospital_verified',
}
GEO_PREDICATES = (GEO.lat, GEO.long)


def source_quality(s):
    # Evidence level, NOT assertion about real-world point precision.
    return {'osm': 'candidate_osm_not_independently_verified',
            'nama': 'name_match_not_independently_verified',
            'jalan': 'street_approximation',
            'kabkota': 'municipality_approximation'}.get(s, 'unknown')


def build(root: Path, out: Path, expected_count: int = 206):
    src = root / 'semantic/rdf/hospitals-sumut.ttl'
    master = root / 'data/rumah_sakit_sumut.csv'
    coord = root / 'data/koordinat.csv'
    for p in [src, master, coord]:
        if not p.is_file():
            raise FileNotFoundError(p)
    graph = Graph().parse(src, format='turtle')
    with master.open(encoding='utf-8-sig', newline='') as f:
        master_rows = list(csv.DictReader(f))
    with coord.open(encoding='utf-8-sig', newline='') as f:
        coord_rows = list(csv.DictReader(f))
    if len(master_rows) != expected_count:
        raise ValueError(f'Expected {expected_count} CSV hospitals; found {len(master_rows)}')
    coords = {r['kode']: r for r in coord_rows}
    if len(coords) != len(coord_rows):
        raise ValueError('Duplicate coordinate codes')
    hospitals = set(graph.subjects(RDF.type, HF.RumahSakit))
    expected = {URIRef(f'{RS_URI_BASE}rs-{i:03d}') for i in range(1, expected_count + 1)}
    if hospitals != expected:
        raise ValueError(f'RDF hospital URI mismatch: missing={len(expected-hospitals)}, unexpected={len(hospitals-expected)}')

    overlay = Graph()
    overlay.bind('rdf', RDF)
    overlay.bind('prov', PROV)
    overlay.bind('cs', CS)
    overlay.bind('hf', HF)
    overview = []
    examples = []
    totals = Counter()
    # Records are RDF reified statements: not a claim of formal OWL inference.
    # Per-statement URI stable so regeneration doesn't create duplicates.
    for i in range(1, expected_count+1):
        code = f'rs-{i:03d}'
        rs = URIRef(f'{RS_URI_BASE}{code}')
        co = coords.get(code, {})
        coordinate_source = (co.get('sumber') or '').strip().lower()
        if (co.get('lat') and co.get('lon')) and not (graph.value(rs, GEO.lat) and graph.value(rs, GEO.long)):
            raise ValueError(f'Coordinates disagree between CSV and RDF: {code}')
        service_count = len(list(graph.objects(rs, HF.menyediakanLayanan)))
        facility_count = len(list(graph.objects(rs, HF.memilikiFasilitas)))
        bpjs_count = len(list(graph.objects(rs, HF.menerimaBPJS)))
        totals.update(services=service_count, facilities=facility_count, bpjs=bpjs_count)
        geo_quality = source_quality(coordinate_source)
        overview.append({
            'hospital_id': code,
            'hospital_uri': str(rs),
            'name': str(graph.value(rs, URIRef('https://schema.org/name')) or ''),
            'service_links_assumed_from_class': service_count,
            'facility_links_assumed_from_class': facility_count,
            'bpjs_value_assumed_from_rule': str(graph.value(rs, HF.menerimaBPJS) or ''),
            'coordinate_source': coordinate_source or 'unknown',
            'coordinate_evidence': geo_quality,
            'hospital_level_service_verification': 'not_provided',
            'hospital_level_facility_verification': 'not_provided',
            'hospital_level_bpjs_verification': 'not_provided',
        })
        for predicate, rule in GENERATED.items():
            for obj in graph.objects(rs, predicate):
                signature = f'{rs}|{predicate}|{obj.n3()}'.encode('utf-8')
                statement = URIRef(str(CS) + 'statement/' + hashlib.sha256(signature).hexdigest())
                overlay.add((statement, RDF.type, RDF.Statement))
                overlay.add((statement, RDF.subject, rs))
                overlay.add((statement, RDF.predicate, predicate))
                overlay.add((statement, RDF.object, obj))
                overlay.add((statement, CS.evidenceStatus, Literal('derived_by_generator_not_verified')))
                overlay.add((statement, CS.method, Literal(rule)))
                if len(examples) < 3:
                    examples.append({'subject': str(rs), 'predicate': str(predicate), 'object': str(obj), 'status': 'derived_by_generator_not_verified'})
        # Coordinate quality is hospital metadata; don't overwrite source coordinates.
        overlay.add((rs, CS.coordinateEvidence, Literal(geo_quality)))
        overlay.add((rs, CS.coordinateSource, Literal(coordinate_source or 'unknown')))
    # Verify that none of the new annotations overwrites an existing source triple.
    if set(overlay).intersection(set(graph)):
        raise ValueError('Provenance overlay overlaps source dataset')
    out.mkdir(parents=True, exist_ok=True)
    csv_file = out/'provenance_hospitals.csv'
    with csv_file.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(overview[0]))
        writer.writeheader()
        writer.writerows(overview)
    turtle_file = out/'provenance-overlay.DRAFT.ttl'
    overlay.serialize(destination=str(turtle_file), format='turtle', encoding='utf-8')
    report = {
        'status': 'PASS', 'scope': 'local files only; no live Fuseki check',
        'source_hospitals': len(hospitals), 'source_triples': len(graph),
        'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
        'provenance_overlay_triples': len(overlay),
        'derived_service_claims': totals['services'],
        'derived_facility_claims': totals['facilities'],
        'derived_bpjs_claims': totals['bpjs'],
        'coordinates_by_source': dict(Counter(row['coordinate_source'] for row in overview)),
        'examples': examples,
        'caveats': [
            'Derived claims are NOT verified hospital-specific facts.',
            'Coordinate labels refer to source method, NOT geographic verification.',
            'No source provenance for administrative CSV has been independently verified.',
            'This draft overlay is NOT loaded into Fuseki or used by website until explicitly integrated.',
        ]}
    (out/'provenance_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    # Parse/validate output and expected statement counts before proclaiming PASS.
    parsed = Graph().parse(str(turtle_file), format='turtle')
    if len(parsed) != len(overlay) or len(list(parsed.subjects(RDF.type, RDF.Statement))) != sum(totals.values()):
        raise ValueError('Overlay RDF round-trip validation failed')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('Output:', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--out', type=Path, default=ROOT/'docs/semantic-audit-output/patch02')
    args = ap.parse_args()
    build(args.root.resolve(), args.out.resolve())
