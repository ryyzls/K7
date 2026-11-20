"""Exercise the chat API contract with real RDF and an unavailable Fuseki."""
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.routers.chat import ChatPayload, chat_endpoint
from app.services import hospital_repo
from app.services.sparql_service import PREFIXES, build_search_query


class ChatIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fuseki = patch('app.services.sparql_service.search_hospitals',
                            new=AsyncMock(side_effect=ConnectionError('offline')))
        self.fuseki.start()
        self.addCleanup(self.fuseki.stop)

    async def ask(self, text, previous=None, **kwargs):
        return await chat_endpoint(ChatPayload(text=text, state=(previous or {}).get('state'), **kwargs))

    async def test_location_and_city_fallback(self):
        result = await self.ask('RS terdekat dari saya', lat=3.59, lon=98.67, location_status='available')
        distances = [h['distance_km'] for h in result['hospitals']]
        self.assertEqual(len(distances), 5)
        self.assertEqual(distances, sorted(distances))
        denied = await self.ask('RS terdekat dari saya', location_status='denied')
        self.assertFalse(denied['hospitals'])
        city = await self.ask('Kota Binjai', denied)
        self.assertTrue(city['hospitals'])
        self.assertTrue(all(h['kabkota'] == 'Kota Binjai' for h in city['hospitals']))

    async def test_pagination_and_filter_followup(self):
        first = await self.ask('Cari RS di Medan')
        second = await self.ask('Lihat lainnya', first)
        self.assertEqual(second['state']['offset'], 5)
        self.assertTrue(second['hospitals'])
        self.assertFalse(set(first['state']['last_hospital_ids']) & set(second['state']['last_hospital_ids']))
        filtered = await self.ask('Yang terima BPJS?', second)
        self.assertEqual(filtered['state']['last_intent'], 'SEARCH_FILTER')
        self.assertEqual(filtered['state']['filters']['kabkota'], 'Kota Medan')
        self.assertTrue(all(h['bpjs'] for h in filtered['hospitals']))

    async def test_detail_followup_and_compare(self):
        detail = await self.ask('Detail RS Adam Malik')
        phone = await self.ask('teleponnya?', detail)
        self.assertEqual(phone['state']['last_intent'], 'ATRIBUT')
        comparison = await self.ask('Bandingkan dengan RS Pirngadi', detail)
        self.assertEqual(comparison['state']['last_intent'], 'COMPARE')
        self.assertEqual(len(comparison['hospitals']), 2)

    async def test_non_bpjs_and_empty_filters(self):
        result = await self.ask('RS non BPJS')
        self.assertTrue(result['hospitals'])
        self.assertTrue(all(not h['bpjs'] for h in result['hospitals']))
        self.assertEqual(len(hospital_repo.get_all_hospitals()), 206)

    async def test_distance_to_named_hospital(self):
        for question in ('berapa jarak ke RS Adam Malik?', 'seberapa jauh RS Adam Malik dari lokasi saya?'):
            result = await self.ask(question, lat=3.59, lon=98.67)
            self.assertEqual(result['state']['last_hospital_ids'], ['rs-171'])
            self.assertIn('10.52 km', result['text'])
            self.assertIn('garis lurus', result['text'])
        denied = await self.ask('berapa jarak ke RS Adam Malik?', location_status='denied')
        self.assertIn('izinkan akses lokasi', denied['text'])
        self.assertNotIn(' km', denied['text'])

    async def test_sparql_matches_rdf_filter_results(self):
        import rdflib
        graph = rdflib.Graph()
        for path in hospital_repo.find_rdf_dir().glob('*.ttl'):
            graph.parse(path, format='turtle')
        for filters in ({'bpjs': False}, {'fasilitas': 'ICU'}, {'fasilitas': 'Laboratorium'}, {'bpjs': True, 'kabkota': 'Kota Medan'}):
            with self.subTest(filters=filters):
                rows = graph.query(PREFIXES + build_search_query(**filters, limit=500))
                actual = {str(row.rs).rsplit('/', 1)[-1] for row in rows}
                expected = {h['id'] for h in hospital_repo.filter_in_memory(**filters)}
                self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
