"""Import manually reviewed evidence into RDF; never crawl candidate URLs.

python scripts/enrich_websites.py --input data/website_reviews.json --batch-size 10
Runtime reads only RDF. Input JSON is an auditable review/import artifact.
"""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys
import time

import rdflib
from rdflib import Namespace, Literal, RDF, XSD

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.services.website import safe_website_url

HF = Namespace('http://carisehat.id/ontology/')
SCHEMA = Namespace('https://schema.org/')
FIELDS = ('websiteStatus', 'websiteEvidence', 'websiteCheckedAt', 'websiteScope', 'websiteNotes', 'websiteCandidate')
STATUSES = {'unreviewed', 'verified', 'needs_review', 'not_found'}


def enrich(source, output, records, batch_size=10, offset=0):
    if not 1 <= batch_size <= 100 or offset < 0:
        raise ValueError('batch-size must be 1..100 and offset must be nonnegative')
    base = rdflib.Graph().parse(source, format='turtle')
    hospitals = {str(s).rsplit('/', 1)[-1]: s for s in base.subjects(RDF.type, HF.RumahSakit)}
    graph = rdflib.Graph()
    graph.bind('hf', HF)
    graph.bind('schema', SCHEMA)
    if output.exists():
        graph.parse(output, format='turtle')
    for subject in hospitals.values():
        if not graph.value(subject, HF.websiteStatus):
            graph.add((subject, HF.websiteStatus, Literal('unreviewed')))
    seen = set()
    for record in records:
        if record['id'] in seen:
            raise ValueError('Duplicate review ID: ' + record['id'])
        seen.add(record['id'])
    processed = 0
    for record in records[offset:offset + batch_size]:
        subject = hospitals.get(record['id'])
        if subject is None:
            raise ValueError('Unknown stable RS identifier: ' + record['id'])
        # Guard against attaching a review to another branch or a changed source ID.
        for key, predicate in [('nama', SCHEMA.name), ('alamat', HF.alamat)]:
            if record.get(key) != str(base.value(subject, predicate)):
                raise ValueError('Identity mismatch for ' + record['id'] + ': ' + key)
        status = record['status']
        if status not in STATUSES:
            raise ValueError('Unknown status')
        checked = record.get('checked_at', '')
        if status != 'unreviewed':
            parsed = datetime.fromisoformat(checked.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                raise ValueError('checked_at requires timezone')
        url = record.get('url')
        evidence = record.get('evidence_url')
        if url and not safe_website_url(url):
            raise ValueError('Unsafe URL')
        if evidence and not safe_website_url(evidence):
            raise ValueError('Unsafe evidence URL')
        if status == 'verified' and not (url and evidence and record.get('notes') and record.get('scope') in ('hospital', 'branch', 'network')):
            raise ValueError('Verified records require URL, evidence, scope and identity notes')
        old_status = str(graph.value(subject, HF.websiteStatus) or '')
        old_date = str(graph.value(subject, HF.websiteCheckedAt) or '')
        if old_status == 'verified' and status != 'verified':
            continue
        if old_date and checked and datetime.fromisoformat(checked.replace('Z', '+00:00')) < datetime.fromisoformat(old_date.replace('Z', '+00:00')):
            continue
        for predicate in [SCHEMA.url] + [HF[field] for field in FIELDS]:
            graph.remove((subject, predicate, None))
        graph.add((subject, HF.websiteStatus, Literal(status)))
        if url:
            graph.add((subject, SCHEMA.url if status == 'verified' else HF.websiteCandidate, rdflib.URIRef(url)))
        if evidence:
            graph.add((subject, HF.websiteEvidence, rdflib.URIRef(evidence)))
        if checked:
            graph.add((subject, HF.websiteCheckedAt, Literal(checked, datatype=XSD.dateTime)))
        for key in ('scope', 'notes'):
            if record.get(key):
                graph.add((subject, HF['website' + key.title()], Literal(record[key])))
        processed += 1
    # Validate the entire batch before replacing the previous artifact.
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.ttl.tmp')
    graph.serialize(temporary, format='turtle')
    temporary.replace(output)
    counts = Counter(str(graph.value(s, HF.websiteStatus)) for s in hospitals.values())
    return {'processed': processed, 'total': len(hospitals), **{s: counts[s] for s in sorted(STATUSES)},
            'review_queue': [i for i, s in hospitals.items() if str(graph.value(s, HF.websiteStatus)) == 'needs_review']}


def publish(output):
    """Synchronize only website predicates, preserving every other RDF property."""
    import httpx
    from app.config import settings
    graph = rdflib.Graph().parse(output, format='turtle')
    subjects = ' '.join(s.n3() for s in set(graph.subjects()))
    predicates = ' '.join(p.n3() for p in [SCHEMA.url] + [HF[f] for f in FIELDS])
    triples = graph.serialize(format='nt')
    update = (f'DELETE {{ ?s ?p ?o }} WHERE {{ VALUES ?s {{ {subjects} }} VALUES ?p {{ {predicates} }} ?s ?p ?o }}; '
              f'INSERT DATA {{ {triples} }}')
    # This is the configured triplestore, never a URL from the review input.
    for attempt in range(2):
        try:
            response = httpx.post(settings.fuseki_url + '/update', data={'update': update}, timeout=15, follow_redirects=False)
            response.raise_for_status()
            return
        except httpx.HTTPError:
            if attempt:
                raise
            time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT / 'semantic/rdf/hospitals-sumut.ttl')
    parser.add_argument('--output', type=Path, default=ROOT / 'semantic/rdf/hospital-websites.ttl')
    parser.add_argument('--batch-size', type=int, default=10)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--publish', action='store_true', help='Sync website predicates to the configured Fuseki dataset')
    args = parser.parse_args()
    print(json.dumps(enrich(args.source, args.output, json.loads(args.input.read_text(encoding='utf-8')), args.batch_size, args.offset), indent=2))
    if args.publish:
        publish(args.output)
        print('Website RDF synchronized to Fuseki.')
