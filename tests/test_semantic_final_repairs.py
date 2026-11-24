import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['AUTO_LOAD_RDF'] = 'false'
from app.services.enrichment_service import get_hospital_enrichment


class ScheduleRegressionTests(unittest.TestCase):
    def test_not_found_does_not_create_hours_or_closed_sunday(self):
        hours = get_hospital_enrichment('rs-001')['jam_operasional']['jadwal_harian']
        self.assertEqual({row['jam'] for row in hours}, {'Belum tersedia'})

    def test_columbia_uses_existing_sourced_schedule(self):
        for ident in ['rs-007', 'rs-008']:
            hours = get_hospital_enrichment(ident)['jam_operasional']['jadwal_harian']
            self.assertEqual(hours[0]['jam'], '08:00 – 20:00')
            self.assertEqual(hours[6]['jam'], 'Tutup')

    def test_vita_uses_own_candidate_not_hardcoded_example(self):
        hours = get_hospital_enrichment('rs-199')['jam_operasional']['jadwal_harian']
        self.assertEqual(hours[0]['jam'], '08:00 – 19:00')
        self.assertEqual(hours[5]['jam'], '08:00 – 19:00')
        self.assertEqual(hours[6]['jam'], 'Belum tersedia')

    def test_all_schedule_values_have_provenance(self):
        for i in range(1, 207):
            hours = get_hospital_enrichment(f'rs-{i:03}')['jam_operasional']
            for unit in hours.get('unit_operasional', []):
                if any(r['jam'] != 'Belum tersedia' for r in unit.get('jadwal_harian', [])):
                    self.assertTrue(unit['facts'])
                    self.assertTrue(all(f['source_url'].startswith('http') for f in unit['facts']))

if __name__ == '__main__':
    unittest.main()
