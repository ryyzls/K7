"""SIRS policy and SPARQL tests, isolated RDFLib Dataset, no live writes."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'scripts'))
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['RDF_DIR'] = str(ROOT / 'semantic/rdf')
from rdflib import Dataset, URIRef
from app.services import sirs, sparql_service as sp
from integrate_sirs import prepare


class SIRSIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph, cls.report = prepare()
        cls.dataset = Dataset()
        for p in (ROOT / 'semantic/rdf').glob('*.ttl'):
            cls.dataset.default_context.parse(p)
        target = cls.dataset.graph(URIRef(sirs.GRAPH_URI))
        for triple in cls.graph:
            target.add(triple)

    def query(self, query):
        return [{str(k): str(v) for k,v in row.asdict().items()}
                for row in self.dataset.query(sp.PREFIXES + query)]

    def test_identity_and_policy_counts(self):
        self.assertEqual(self.report['hospitals'],206)
        self.assertEqual(self.report['accepted_labels'],35)
        self.assertEqual(self.report['accepted_observations'],1409)
        self.assertEqual(self.report['hospitals_with_accepted_services'],200)

    def test_no_clinical_or_ambiguous_published(self):
        rows = self.query('SELECT DISTINCT ?category WHERE { GRAPH <'+sirs.GRAPH_URI+'> { ?obs <'+str(sirs.CS.layakPencarian)+'> true ; <'+str(sirs.CS.kategoriKurasi)+'> ?category } }')
        self.assertEqual({r['category'] for r in rows},{'diagnostik_pemeriksaan','gawat_darurat_terlapor'})

    def test_206_hospitals_no_inferred_service_fallback(self):
        rows = self.query(sp.build_search_query(limit=500))
        self.assertEqual(len(rows),206)
        for row in rows:
            h = sp.to_hospital(row)
            expected = {r['label'] for r in sirs.records().get(h['id'],[])}
            self.assertEqual(set(h['layanan']),expected)
            self.assertEqual(len(h['layanan']),len(h['layanan_facts']))
            for fact in h['layanan_facts']:
                self.assertTrue(fact['source_url'].startswith('https://sirs.kemkes.go.id/'))
                self.assertEqual(fact['category_status'],'RULE_REVIEWED')

    def test_service_filter_exact_hospital_set(self):
        label = sirs.EMERGENCY
        actual = {r['rs'].rsplit('/',1)[-1] for r in self.query('SELECT DISTINCT ?rs WHERE { '+sirs.pattern(sp.lit(label))+' }')}
        expected = {ident for ident,records in sirs.records().items() if any(r['label']==label for r in records)}
        self.assertTrue(expected)
        self.assertEqual(actual,expected)

    def test_clinical_filter_not_published(self):
        self.assertEqual(self.query('SELECT ?rs WHERE { '+sirs.pattern(sp.lit('Pelayanan medik dasar / umum'))+' }'),[])

    def test_missing_graph_fails_closed(self):
        isolated = Dataset()
        isolated.default_context.parse(ROOT / 'semantic/rdf/hospitals-sumut.ttl')
        rows = list(isolated.query(sp.PREFIXES+sp.build_search_query(limit=500)))
        self.assertEqual(len(rows),206)
        self.assertTrue(all(not str(row.asdict().get('layanan','')) for row in rows))

    def test_filter_injection_is_literal(self):
        self.assertEqual(self.query('SELECT ?rs WHERE { '+sirs.pattern(sp.lit('" } UNION { ?s ?p ?o } #'))+' }'),[])

    def test_local_fallback_uses_same_policy(self):
        from app.services import hospital_repo
        hospital_repo.reload_cache()
        hospitals = hospital_repo.get_all_hospitals()
        self.assertEqual(len(hospitals),206)
        for h in hospitals:
            self.assertEqual(set(h['layanan']),{r['label'] for r in sirs.records().get(h['id'],[])})


if __name__ == '__main__':
    unittest.main()
