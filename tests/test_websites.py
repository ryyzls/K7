import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import rdflib
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'scripts')]
from enrich_websites import enrich, HF, SCHEMA
from app.services.website import safe_website_url, public_website
from app.services import hospital_repo, sparql_service


class WebsiteTests(unittest.TestCase):
    def test_public_url_policy(self):
        for url in ('javascript:alert(1)', 'data:text/html,hello', '//example.com', 'http://127.0.0.1', 'http://10.0.0.1', 'http://[::1]', 'http://localhost', 'http://metadata.google.internal', 'https://user:pass@example.com', 'https://example.com\\@evil.com', 'http://2130706433'):
            self.assertIsNone(safe_website_url(url), url)
        self.assertEqual(safe_website_url('https://rsham.go.id/'), 'https://rsham.go.id/')
        self.assertIsNone(public_website('https://rsham.go.id/', 'needs_review', 'https://rsham.go.id/', '2026-11-19'))
        self.assertIsNone(public_website('https://rsham.go.id/', 'verified'))

    def test_rdf_records_and_branch_identity(self):
        hospital_repo.reload_cache()
        hs = {h['id']: h for h in hospital_repo.get_all_hospitals()}
        self.assertEqual(len(hs), 206)
        self.assertEqual(sum(bool(h['website']) for h in hs.values()), 3)
        self.assertIn('/rs-columbia-asia-aksara/', hs['rs-007']['website'])
        self.assertIn('/rs-columbia-asia-medan/', hs['rs-008']['website'])
        self.assertIsNone(hs['rs-125']['website'])
        self.assertIsNone(hs['rs-001']['website'])
        self.assertEqual(hs['rs-125']['website_status'], 'needs_review')

    def test_idempotent_batch_and_no_downgrade(self):
        reviews = json.loads((ROOT / 'data/website_reviews.json').read_text(encoding='utf-8'))
        source = ROOT / 'semantic/rdf/hospitals-sumut.ttl'
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'websites.ttl'
            summary = enrich(source, output, reviews)
            first = rdflib.Graph().parse(output)
            enrich(source, output, reviews)
            self.assertTrue(isomorphic(first, rdflib.Graph().parse(output)))
            self.assertEqual(summary['verified'], 3)
            weak = copy.deepcopy(reviews[:1])
            weak[0].update(status='not_found', url=None)
            enrich(source, output, weak)
            self.assertTrue(isomorphic(first, rdflib.Graph().parse(output)))
            wrong = copy.deepcopy(reviews[:1])
            wrong[0]['id'] = 'rs-008'
            with self.assertRaisesRegex(ValueError, 'Identity mismatch'):
                enrich(source, output, wrong)
            self.assertTrue(isomorphic(first, rdflib.Graph().parse(output)))

    def test_sparql_conversion_gates_links(self):
        row = dict(rs='http://localhost:8000/rs/rs-007', nama='Aksara', jenis='Umum', kelas='B', alamat='Medan', kabkota='Kota Medan', website='https://columbiaasia.co.id/rs-columbia-asia-aksara/')
        self.assertIsNone(sparql_service.to_hospital(row)['website'])
        row.update(websiteStatus='verified', websiteEvidence='https://columbiaasia.co.id/hubungi-kami/', websiteCheckedAt='2026-11-19T14:15:52Z')
        self.assertEqual(sparql_service.to_hospital(row)['website'], row['website'])
        row['website'] = 'javascript:alert(1)'
        self.assertIsNone(sparql_service.to_hospital(row)['website'])


if __name__ == '__main__':
    unittest.main()
