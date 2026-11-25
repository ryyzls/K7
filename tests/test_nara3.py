"""Independent RDF-backed regression tests for NARA. No generated hospital fixtures."""
import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import runtime_fixture as fixture
from app.services.chatbot.engine import process
from app.services.chatbot.planning import is_emergency, QueryPlan
from app.services import hybrid_search as hs
from app.routers.chat import ChatPayload, check_rate, _buckets
from rdflib import Namespace, RDF, URIRef

HF=Namespace('http://carisehat.id/ontology/')
CS=Namespace('http://carisehat.id/ontology/sirs/')
SC=Namespace('https://schema.org/')
RDFS=Namespace('http://www.w3.org/2000/01/rdf-schema#')
G=fixture.graph
S=G.graph(URIRef('http://carisehat.id/graph/sirs/2026-11-19'))
F=G.graph(URIRef('http://carisehat.id/graph/search/facilities/2026-11-25'))

def oracle_ids(region=None, classes=None, service=None, facility=None):
    result=set()
    for h in G.default_graph.subjects(RDF.type,HF.RumahSakit):
        if region and str(G.default_graph.value(G.default_graph.value(h,HF.beradaDiKabupatenKota),RDFS.label)) != region: continue
        if classes and str(G.default_graph.value(h,HF.kelas)) not in classes: continue
        if service and not any(str(S.value(o,CS.labelPelayanan)).casefold() == service.casefold() for o in S.objects(h,CS.catatanPelayanan)): continue
        if facility:
            if facility in ('ICU','NICU','PICU','ICCU','HCU'):
                if not any(str(F.value(o,CS.jenisFasilitas)).startswith(facility.lower()+'_') or str(F.value(o,CS.jenisFasilitas))==facility.lower() for o in F.objects(h,HF.fasilitasKritis) if float(F.value(o,CS.kapasitasTerlapor) or 0)>0): continue
            elif not any(str(v)==facility for v in F.objects(h,HF.memilikiFasilitasDiagnostik)) and not any(str(S.value(o,CS.labelPelayanan))==facility and str(S.value(o,CS.layakPencarian)).lower()=='true' for o in S.objects(h,CS.catatanPelayanan)): continue
        result.add(str(h).rsplit('/',1)[-1])
    return result

class Safety(unittest.TestCase):
    def test_emergencies(self):
        for t in ['Saya nyeri dada dan sesak napas','Ibu tidak sadarkan diri','perdarahan berat','kesulitan bernapas berat','wajah mencong dan bicara pelo','Saya mengalami kondisi darurat','Tidak nyeri dada tapi saya sesak napas']:
            with self.subTest(t=t): self.assertTrue(is_emergency(t))
    def test_nonemergencies(self):
        for t in ['Cari IGD','Apa itu stroke?','Kemarin nyeri dada','Saya tidak sesak napas','Jika saya nyeri dada bagaimana?','Tidak ada perdarahan berat','Saya punya riwayat sesak napas']:
            with self.subTest(t=t): self.assertFalse(is_emergency(t))
    def test_limits(self):
        with self.assertRaises(ValueError): QueryPlan(limit=100)
        with self.assertRaises(ValueError): QueryPlan(hospital_ids=['../rs-001'])
        with self.assertRaises(ValueError): ChatPayload(text='a'*4001)
    def test_rate_limit(self):
        _buckets.clear()
        for _ in range(40): check_rate('test')
        with self.assertRaises(Exception): check_rate('test')
        check_rate('other')
        _buckets.clear()

class Engine(unittest.IsolatedAsyncioTestCase):
    async def test_multiturn(self):
        state=None
        for q in ['Cari RS di Medan yang punya dokter jantung','Kelas B aja','Yang ada ICU juga','Tambah CT Scan','Eh ganti ke Siantar','Gausah CT Scan']:
            r=await process(q,state=state);state=r['state'];self.assertNotEqual(r['kind'],'error',r)
        values={f['value'] for f in state['active_filters']}
        self.assertEqual(values,{'Kota Pematang Siantar','B','Jantung dan Pembuluh Darah','ICU'})
        allowed=oracle_ids('Kota Pematang Siantar',{'B'},'Jantung dan Pembuluh Darah','ICU')
        self.assertTrue(r['hospitals']);self.assertEqual(r['total'],len(allowed));self.assertLessEqual({h['id'] for h in r['hospitals']},allowed)
    async def test_search_criteria(self):
        cases=[('ada dokter saraf di medan?',dict(region='Kota Medan',service='Saraf')),
               ('rs kelas b yg ada icu sama ct scan',dict(classes={'B'},facility='CT Scan')),
               ('rs yg bs cuci drah di siantarr',dict(region='Kota Pematang Siantar',facility='Hemodialisis')),
               ('Cari RS di Medan dengan NICU',dict(region='Kota Medan',facility='NICU'))]
        for q,criteria in cases:
            with self.subTest(q=q):
                r=await process(q); allowed=oracle_ids(**criteria)
                self.assertTrue(r['hospitals'],r); self.assertLessEqual({h['id'] for h in r['hospitals']},allowed)
    async def test_grouped(self):
        r=await process('RS di Medan dan (kelas A atau kelas B) dan ICU selain Adam Malik')
        self.assertTrue(r['hospitals'],r)
        allowed=oracle_ids('Kota Medan',{'A','B'},facility='ICU')-{'rs-171'}
        self.assertEqual(r['total'],len(allowed));self.assertLessEqual({h['id'] for h in r['hospitals']},allowed)
    async def test_names(self):
        for q in ['adam malk','rsham','Cari RS Adam Malik','Malik Adam']:
            with self.subTest(q=q): self.assertEqual([h['id'] for h in (await process(q))['hospitals']],['rs-171'])
    async def test_selection_contact_comparison(self):
        r=await process('RS di Medan');ids=[h['id'] for h in r['hospitals']]
        c=await process('Bandingkan yang pertama dan kedua',state=r['state']);self.assertEqual(c['kind'],'comparison');self.assertEqual([h['id'] for h in c['hospitals']],ids[:2])
        d=await process('Yang pertama tadi',state=r['state']);self.assertEqual(d['hospitals'][0]['id'],ids[0])
        p=await process('Nomor teleponnya?',state=d['state']);self.assertEqual(p['kind'],'contact');self.assertEqual(p['hospitals'][0]['id'],ids[0])
    async def test_fresh_search(self):
        r=await process('Cari RS Adam Malik'); n=await process('Cari RS di Siantar',state=r['state'])
        self.assertTrue(n['hospitals']);self.assertTrue(all(h['kabkota']=='Kota Pematang Siantar' for h in n['hospitals']))
    async def test_isolation(self):
        a=await process('RS di Medan');b=await process('RS di Binjai');before=json.dumps(a['state'])
        c=await process('Kelas B saja',state=a['state']);self.assertEqual(json.dumps(a['state']),before)
        self.assertTrue(all(h['kabkota']=='Kota Binjai' for h in b['hospitals']));self.assertTrue(all(h['kabkota']=='Kota Medan' for h in c['hospitals']))
    async def test_limit(self):
        r=await process('RS di Medan');r=await process('tiga aja',state=r['state']);self.assertEqual(len(r['hospitals']),3)
    async def test_location(self):
        r=await process('RS terdekat');self.assertEqual(r['kind'],'location_request')
        r=await process('RS terdekat',lat=3.59,lon=98.67);dist=[h['distance_km'] for h in r['hospitals']];self.assertTrue(dist);self.assertEqual(dist,sorted(dist))
    async def test_failure(self):
        with patch.object(hs,'snapshot',side_effect=RuntimeError('secret')):
            r=await process('RS di Medan');self.assertEqual(r['kind'],'error');self.assertNotIn('secret',r['text'])
            r=await process('nyeri dada dan sesak napas');self.assertTrue(r['is_emergency'])
    async def test_injection(self):
        for q in ['SELECT ?s WHERE {?s ?p ?o}',"' OR 1=1; DROP TABLE users",'<script>alert(1)</script>','.*'*100]:
            r=await process(q);self.assertFalse(r['hospitals']);self.assertNotIn('traceback',r['text'])
    async def test_empty_and_unknown(self):
        r=await process('RS kelas A di Nias Barat dengan MRI');self.assertFalse(r['hospitals']);self.assertEqual(r['kind'],'empty')
        self.assertFalse((await process('Rumah sakit di Jakarta'))['hospitals'])
    async def test_no_silent_negative_service(self):
        r=await process('RS tanpa ICU');self.assertFalse(r['hospitals']);self.assertEqual(r['kind'],'clarification')
    async def test_searchbar_regression(self):
        for q,criteria in [('Medan kelas B',dict(region='Kota Medan',classes={'B'})),('NICU',dict(facility='NICU')),('CT Scan',dict(facility='CT Scan'))]:
            r=await hs.search(q=q,limit=500);self.assertEqual({h['id'] for h in r['items']},oracle_ids(**criteria))
    async def test_schedule_retains_specialty(self):
        r=await process('RS di Siantar yang memiliki poli anak dan buka hari Sabtu')
        fields=r['state']['active_filters']
        self.assertTrue(any(f['field']=='service' and f['value']=='Kesehatan anak' for f in fields),fields)
        self.assertTrue(any(f['field']=='hours' for f in fields),fields)

    async def test_multitool_workflow(self):
        q='Carikan tiga RS terdekat yang punya layanan jantung dan ICU, bandingkan fasilitasnya, terus kasih nomor teleponnya.'
        r=await process(q)
        self.assertEqual(r['kind'],'location_request',r)
        r=await process(q,lat=3.59,lon=98.67)
        self.assertEqual(r['kind'],'comparison',r)
        self.assertEqual(len(r['comparison']['hospitals']),3)
        allowed=oracle_ids(service='Jantung dan Pembuluh Darah',facility='ICU')
        self.assertLessEqual({h['id'] for h in r['hospitals']},allowed)
        self.assertTrue(all('telepon' in h for h in r['comparison']['hospitals']))

    async def test_alternatives_preserve_filters(self):
        r=await process('RS di Medan kelas B')
        d=await process('Yang pertama tadi',state=r['state'])
        a=await process('Ada alternatif lain?',state=d['state'])
        self.assertEqual(a['kind'],'alternatives',a)
        self.assertTrue(a['hospitals'])
        self.assertLessEqual({h['id'] for h in a['hospitals']},oracle_ids('Kota Medan',{'B'}))
        self.assertNotIn(d['hospitals'][0]['id'],[h['id'] for h in a['hospitals']])

    async def test_regional_failure_is_optional(self):
        from app.services.chatbot.engine import TOOLS
        async def offline(*args,**kwargs): raise RuntimeError('offline')
        with patch.dict(TOOLS,{'region':offline}):
            r=await process('Info wilayah Medan')
            self.assertEqual(r['kind'],'region')
            self.assertIsNone(r['regional_info'])
            self.assertIn('belum dapat diakses',r['text'])
        self.assertTrue((await process('RS di Medan'))['hospitals'])

if __name__=='__main__': unittest.main(verbosity=2)
