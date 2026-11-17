import unittest, datetime
from fastapi.testclient import TestClient
from runtime_fixture import app, graph

class RuntimeTests(unittest.TestCase):
    def setUp(self): self.c=TestClient(app)
    def test_health(self):
        r=self.c.get('/api/health'); self.assertEqual(r.status_code,200); self.assertEqual(r.json()['jumlah_rs'],206)
    def test_search_filters_detail_rdf(self):
        r=self.c.get('/api/search',params={'q':'Adam Malik'});self.assertEqual(r.status_code,200)
        items=r.json()['items'];self.assertTrue(items)
        self.assertEqual(self.c.get('/rs/'+items[0]['id']).status_code,200)
        from rdflib import Graph
        for ext,fmt in [('ttl','turtle'),('rdf','xml')]:
            response=self.c.get('/rs/'+items[0]['id']+'.'+ext)
            self.assertTrue(len(Graph().parse(data=response.text,format=fmt)))
        self.assertEqual(len(self.c.get('/api/filters').json()['kabkota']),33)
        self.assertEqual(self.c.get('/api/search',params={'q':'zzzz-no-result'}).json()['items'],[])
    def test_chat_payload(self):
        self.assertEqual(self.c.post('/api/chat',json={'messages':[{'role':'user','text':'RS kelas A di Medan'}]}).status_code,200)
        self.assertEqual(self.c.post('/api/chat',json={'messages':[{'text':123}]}).status_code,422)
    def test_booking_operator(self):
        p=dict(kode_rs='rs-001',nama_rs="RS O'Connor",nama_pasien='TEST SYNTHETIC',no_telp='000000',tanggal_masuk=str(datetime.date.today()),jenis_kamar='VIP')
        r=self.c.post('/api/booking',json=p);self.assertEqual(r.status_code,201)
        self.assertNotEqual(r.json()['nama_rs'],p['nama_rs'])
        missing=dict(p,kode_rs='rs-not-existing')
        self.assertEqual(self.c.post('/api/booking',json=missing).status_code,404)
        self.assertEqual(self.c.post('/api/booking',json=dict(p,kode_rs='../invalid')).status_code,422)
        code=r.json()['kode_booking'];url='/api/booking/'+code
        self.assertEqual(self.c.get(url).status_code,403)
        self.assertEqual(self.c.delete(url).status_code,403)
        self.assertEqual(self.c.get('/api/booking/rs/rs-001').status_code,403)
        headers={'X-Booking-Key':'test-operator-only'}
        self.assertEqual(self.c.get(url,headers=headers).status_code,200)
        self.assertEqual(self.c.delete(url,headers=headers).status_code,200)
    def test_fuseki_failure(self):
        from unittest.mock import AsyncMock,patch
        import httpx
        with patch('app.services.sparql_service.select',new=AsyncMock(side_effect=httpx.ConnectError('test offline'))):
            self.assertEqual(self.c.get('/api/search').status_code,502)
            self.assertEqual(self.c.get('/api/health').status_code,503)
            r=self.c.post('/api/chat',json={'text':'RS kelas A di Medan'})
            self.assertIn('kendala',r.json()['text'])
