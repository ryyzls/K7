#!/usr/bin/env python3
"""CariSehat Patch 05: read-only HTTP semantic integration smoke tests.

Requires httpx and rdflib (available in CariSehat backend image).
No POST to application endpoints. No SPARQL UPDATE. Never loads RDF into Fuseki.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import httpx
from rdflib import Graph, URIRef, RDF
from rdflib.compare import isomorphic


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metas = []
        self.props = []
        self.rdfa_types = []
        self.ids = []
        self.title = False
        self.in_title = False
        self.title_text = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.metas.append(attrs)
        if attrs.get('property'):
            self.props.append(attrs['property'])
        if attrs.get('typeof'):
            self.rdfa_types.extend(attrs['typeof'].split())
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data


def main():
    parser = argparse.ArgumentParser(description='Read-only HTTP + RDF smoke tests for CariSehat')
    parser.add_argument('--base-url', default=os.getenv('CARISEHAT_URL', 'http://backend:8000'))
    parser.add_argument('--rs-id', default='rs-001')
    parser.add_argument('--out', default='docs/semantic-audit-output/patch05/semantic_e2e_report.json')
    parser.add_argument('--timeout', type=float, default=25.0)
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    tests = []

    def result(name, state, detail='', **extra):
        tests.append({'test': name, 'status': state, 'detail': str(detail)[:350], **extra})
        print(f'{name}: {state}' + (f' — {str(detail)[:110]}' if detail else ''), flush=True)

    def fetch(client, path, accept=None):
        r = client.get(base + path, headers={'Accept': accept} if accept else None)
        r.raise_for_status()
        return r

    with httpx.Client(timeout=args.timeout, follow_redirects=True) as c:
        try:
            r = fetch(c, '/api/health')
            h = r.json()
            ok = h.get('fuseki') == 'ok' and h.get('postgres') == 'ok' and h.get('jumlah_rs') == 206
            result('backend_health', 'PASS' if ok else 'FAIL', f"Fuseki={h.get('fuseki')}, PG={h.get('postgres')}, RS={h.get('jumlah_rs')}")
        except Exception as e:
            result('backend_health', 'BLOCKED', repr(e))

        items = None
        try:
            r = fetch(c, '/api/search?limit=500')
            data = r.json()
            items = data.get('items', [])
            unique = {item.get('id') for item in items}
            ok = len(items) == 206 and len(unique) == 206
            result('api_search_206_unique', 'PASS' if ok else 'FAIL', f'items={len(items)}, unique_ids={len(unique)}')
        except Exception as e:
            result('api_search_206_unique', 'BLOCKED', repr(e))

        if items:
            sample = next((x for x in items if x.get('id') == args.rs_id), None)
            if sample:
                try:
                    r = fetch(c, f'/api/search?kelas={sample["kelas"]}&limit=500')
                    filtered = r.json()['items']
                    ok = bool(filtered) and all(x.get('kelas') == sample['kelas'] for x in filtered)
                    result('api_class_filter', 'PASS' if ok else 'FAIL', f'kelas={sample["kelas"]}, items={len(filtered)}')
                except Exception as e:
                    result('api_class_filter', 'BLOCKED', repr(e))
            else:
                result('api_class_filter', 'BLOCKED', f'{args.rs_id} missing in search')
        else:
            result('api_class_filter', 'BLOCKED', 'Search was not available')

        detail_html = None
        try:
            r = fetch(c, f'/rs/{args.rs_id}')
            detail_html = r.text
            parsed = MetadataParser()
            parsed.feed(detail_html)
            meta = {m.get('property'): m.get('content') for m in parsed.metas}
            og_required = ['og:title', 'og:type', 'og:url', 'og:image', 'og:description']
            missing = [p for p in og_required if not meta.get(p)]
            result('detail_open_graph', 'PASS' if not missing else 'FAIL', 'missing=' + repr(missing), og_url=meta.get('og:url'))
            rdfa_ok = 'Hospital' in parsed.rdfa_types and 'name' in parsed.props and 'address' in parsed.props
            result('detail_rdfa_markup', 'PASS' if rdfa_ok else 'FAIL', f'Hospital type={"Hospital" in parsed.rdfa_types}; name={"name" in parsed.props}; address={"address" in parsed.props}')
            result('detail_html', 'PASS' if parsed.title_text.strip() else 'FAIL', parsed.title_text.strip()[:110])
        except Exception as e:
            for name in ('detail_open_graph', 'detail_rdfa_markup', 'detail_html'):
                result(name, 'BLOCKED', repr(e))

        graphs = {}
        for fmt, mime, graph_format in [('ttl', 'text/turtle', 'turtle'), ('rdf', 'application/rdf+xml', 'xml')]:
            try:
                r = fetch(c, f'/rs/{args.rs_id}.{fmt}', mime)
                ct = r.headers.get('content-type', '').split(';')[0].strip().lower()
                g = Graph()
                g.parse(data=r.content, format=graph_format)
                graphs[fmt] = g
                ok = len(g) > 0 and ct == mime
                result(f'export_{fmt}_parse_content_type', 'PASS' if ok else 'FAIL', f'triples={len(g)}, content_type={ct}')
            except Exception as e:
                result(f'export_{fmt}_parse_content_type', 'BLOCKED', repr(e))

        if 'ttl' in graphs and 'rdf' in graphs:
            same = isomorphic(graphs['ttl'], graphs['rdf'])
            result('ttl_rdfxml_graph_equivalence', 'PASS' if same else 'FAIL', f'TTL={len(graphs["ttl"])}, RDFXML={len(graphs["rdf"])}')
            subj = URIRef(f'{base}/rs/{args.rs_id}')
            # BASE_URI may differ from public hostname; match using last path segment also.
            rs_subjects = [s for s in graphs['ttl'].subjects(RDF.type, URIRef('http://carisehat.id/ontology/RumahSakit'))]
            result('export_rs_identity', 'PASS' if rs_subjects and any(str(s).endswith('/rs/' + args.rs_id) for s in rs_subjects) else 'FAIL', f'RS subjects={len(rs_subjects)}')
        else:
            result('ttl_rdfxml_graph_equivalence', 'BLOCKED', 'One or both exports unavailable')
            result('export_rs_identity', 'BLOCKED', 'Turtle export unavailable')

        try:
            r = fetch(c, '/sparql')
            # Check status+HTML and expected query editor mounting reference (without executing browser JS)
            valid = '<html' in r.text.lower() and ('yasgui' in r.text.lower() or 'sparql' in r.text.lower())
            result('sparql_studio_http', 'PASS' if valid else 'FAIL', f'http={r.status_code}, html={len(r.content)} bytes; browser JS not tested')
        except Exception as e:
            result('sparql_studio_http', 'BLOCKED', repr(e))

        try:
            query = ('PREFIX hf: <http://carisehat.id/ontology/> '
                     'SELECT (COUNT(DISTINCT ?rs) AS ?count) WHERE { ?rs a hf:RumahSakit }')
            r = c.get(base + '/sparql/query', params={'query': query}, headers={'Accept': 'application/sparql-results+json'})
            r.raise_for_status()
            bindings = r.json()['results']['bindings']
            count = int(bindings[0]['count']['value'])
            result('sparql_proxy_select', 'PASS' if count == 206 else 'FAIL', f'count={count}')
        except Exception as e:
            result('sparql_proxy_select', 'BLOCKED', repr(e))

        try:
            r = c.get(base + '/rs/not_a_real_rs_zz99')
            result('unknown_hospital_404', 'PASS' if r.status_code == 404 else 'FAIL', f'http={r.status_code}')
        except Exception as e:
            result('unknown_hospital_404', 'BLOCKED', repr(e))

    states = [t['status'] for t in tests]
    overall = ('FAIL' if 'FAIL' in states else 'BLOCKED' if 'BLOCKED' in states else 'PASS')
    report = {'status': overall, 'scope': 'live backend HTTP, RDF serialization, metadata presence; NO browser execution; NO DBpedia re-test',
              'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'base_url': base, 'rs_id': args.rs_id,
              'tests': tests, 'caveats': ['RDFa markup presence is not a full RDFa graph parser validation.',
              'SPARQL studio page HTTP does not prove YASGUI JavaScript executes.',
              'No write requests, no production booking writes, no Fuseki load/update.',
              'Results require live runtime; ZIP alone cannot prove PASS.']}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': overall, 'pass': states.count('PASS'), 'fail': states.count('FAIL'),
                      'blocked': states.count('BLOCKED'), 'output': str(out)}, ensure_ascii=False, indent=2))
    sys.exit(0 if overall == 'PASS' else 1)


if __name__ == '__main__':
    main()
