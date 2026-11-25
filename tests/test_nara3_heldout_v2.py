"""Frozen before finalization changes: independent triple-based acceptance cases."""
import asyncio
import json
import sys
from pathlib import Path
from test_nara3 import oracle_ids, G, HF, RDFS, RDF
from app.services.chatbot.engine import process

ROOT = Path(__file__).resolve().parents[1]
# Explicit utterances, not generated from the production parser or benchmark.
SEARCH = [
 ('Tolong cari RS kelas C di Binjai dong',dict(region='Kota Binjai',classes={'C'})),
 ('RS di Medan yang kelas A atau kelas C',dict(region='Kota Medan',classes={'A','C'})),
 ('Cari rumah sakit kelas B dengan PICU',dict(classes={'B'},facility='PICU')),
 ('RS kelas D di Deli Serdang',dict(region='Kab. Deli Serdang',classes={'D'})),
 ('Cari RS di Siantar dengan NICU',dict(region='Kota Pematang Siantar',facility='NICU')),
 ('RS di Binjai dengan CT Scan',dict(region='Kota Binjai',facility='CT Scan')),
 ('Tolong cari dokter saraf di Binjai',dict(region='Kota Binjai',service='Saraf')),
 ('Cari poli mata di Siantar',dict(region='Kota Pematang Siantar',service='Mata')),
 ('RS dengan dokter anak di Medan',dict(region='Kota Medan',service='Kesehatan anak')),
 ('RS yg bs cuci drah di Binjai',dict(region='Kota Binjai',facility='Hemodialisis')),
 ('Cari RS kelas B dengan HCU',dict(classes={'B'},facility='HCU')),
 ('Cari RS kelas C yang punya ICU',dict(classes={'C'},facility='ICU')),
 ('Rumah sakit dengan MRI di Binjai',dict(region='Kota Binjai',facility='MRI')),
 ('Cari RS di Medan dengan ICCU',dict(region='Kota Medan',facility='ICCU')),
 ('Cari RS kelas A dengan NICU',dict(classes={'A'},facility='NICU')),
 ('RS di Deli Serdang yang punya dokter mata',dict(region='Kab. Deli Serdang',service='Mata')),
 ('Cari rumah sakit kelas B atau kelas D di Medan',dict(region='Kota Medan',classes={'B','D'})),
 ('Cari RS dengan poli jantng di siantarr',dict(region='Kota Pematang Siantar',service='Jantung dan Pembuluh Darah')),
 ('Tolong cari rumah sakit di Binjai yang punya dokter anak',dict(region='Kota Binjai',service='Kesehatan anak')),
 ('RS di Medan dengan ICU dan CT Scan',dict(region='Kota Medan',facility='ICU',second='CT Scan')),
 ('RS kelas C dengan NICU atau PICU',dict(classes={'C'},facility='NICU',either='PICU')),
 ('Cari RS di Medan selain kelas A',dict(region='Kota Medan',not_class='A')),
]
SAFETY = [
 ('Ayah sedang nyeri dada disertai sesak napas, RS terdekat?',True),
 ('Ibu mendadak wajah mencong dan bicara pelo',True),
 ('Teman saya tidak sadarkan diri di sini',True),
 ('Saya mengalami perdarahan hebat sekarang',True),
 ('Anak saya kesulitan bernapas sekarang',True),
 ('Kemarin ayah sesak napas tetapi sudah sembuh',False),
 ('Saya tidak mengalami nyeri dada',False),
 ('Seandainya terjadi perdarahan berat apa yang harus dilakukan?',False),
 ('Cari RS dengan IGD di Binjai',False),
 ('Tidak sesak napas, tetapi sekarang nyeri dada',True),
 ('Dulu saya pingsan, sekarang sehat',False),
 ('Apa arti gejala stroke?',False),
]
OTHER = [
 ('teleponnya dong', 'clarification'),
 ('Carikan RS di Surabaya dengan NICU','scope'),
 ('Saya ingin resep obat dan dosisnya','scope'),
 ('Cari RS tanpa NICU di Medan','clarification'),
 ('Cari tiga rumah sakit yang paling sesuai dengan kebutuhan saya','clarification'),
 ('Cari RS paling dekat dengan ICU','location_request'),
 ('RS yang ratingnya tertinggi di Binjai','clarification'),
 ('Berapa biaya rawat inap termurah?','clarification'),
 ('Cari RS di Medan Johor dengan PICU','empty'),
 ('Hermna Medan','hospital_list'),
]
PREFERENCES = [
 ('Cari RS di Binjai, kalau bisa kelas C',dict(region='Kota Binjai'),dict(classes={'C'})),
 ('Cari RS dengan NICU, lebih bagus kalau ada CT Scan',dict(facility='NICU'),dict(facility='CT Scan')),
 ('Cari RS kelas B, utamakan ICU',dict(classes={'B'}),dict(facility='ICU')),
 ('Cari RS di Siantar, kalau bisa MRI',dict(region='Kota Pematang Siantar'),dict(facility='MRI')),
]
MULTI = [
 (['Cari RS kelas C di Medan','Ganti ke Binjai'],dict(region='Kota Binjai',classes={'C'})),
 (['Cari RS dengan NICU di Medan','Tambah kelas B'],dict(region='Kota Medan',classes={'B'},facility='NICU')),
 (['Cari RS kelas B di Binjai','Hapus kelas B'],dict(region='Kota Binjai')),
 (['Cari RS kelas A di Medan','Cari RS kelas D di Deli Serdang'],dict(region='Kab. Deli Serdang',classes={'D'})),
 (['Cari RS di Medan','Bandingkan yang pertama dan kedua dan ketiga'],'compare'),
 (['Cari RS Adam Malik','Emailnya?'],'email'),
 (['Cari RS Adam Malik','Website resminya?'],'website'),
 (['Cari RS di Binjai','Yang kedua tadi','Nomor teleponnya?'],'contact'),
]

def expected(criteria):
 c=dict(criteria); second=c.pop('second',None); either=c.pop('either',None); excluded=c.pop('not_class',None)
 result=oracle_ids(**c)
 if second:result &= oracle_ids(facility=second)
 if either:result |= oracle_ids(**{**c,'facility':either})
 if excluded:result -= oracle_ids(classes={excluded})
 return result

def verify_search(r, criteria):
 allowed=expected(criteria); actual={h['id'] for h in r['hospitals']}
 return r.get('total')==len(allowed) and actual<=allowed and bool(actual)==bool(allowed)

async def main():
 rows=[]
 async def record(prompt,category,check,criteria=None,turns=None):
  state=None; prior=None
  for q in turns or [prompt]:
   prior=state; r=await process(q,state=state);state=r['state']
  ok=check(r,prior)
  rows.append(dict(id=f'V2-{len(rows)+1:02}',category=category,prompt=prompt,turns=turns,passed=bool(ok),criteria=criteria,response=r))
 for q,c in SEARCH:await record(q,'search',lambda r,s,c=c:verify_search(r,c),{k:sorted(v) if isinstance(v,set) else v for k,v in c.items()})
 for q,want in SAFETY:await record(q,'safety',lambda r,s,want=want:r['is_emergency']==want,{'emergency':want})
 for q,want in OTHER:
  await record(q,'behavior',lambda r,s,want=want: r['state'].get('last_intent')=='OUT_OF_SCOPE' if want=='scope' else r['state'].get('last_intent')=='DISAMBIGUASI' and len(r['hospitals'])>=2 if want=='ambiguous' else r['kind']==want,{'kind':want})
 for q,mandatory,pref in PREFERENCES:
  def check(r,s,mandatory=mandatory,pref=pref):
   if not verify_search(r,mandatory):return False
   preferred=expected(mandatory)&expected(pref)
   ids=[h['id'] for h in r['hospitals']]
   return all(i in preferred for i in ids[:min(len(preferred),len(ids))]) and bool(r['state']['plan'].get('preferences'))
  await record(q,'preference',check)
 for turns,c in MULTI:
  def check(r,s,c=c):
   if isinstance(c,dict):return verify_search(r,c)
   if c=='compare':return r['kind']=='comparison' and [h['id'] for h in r['hospitals']]==s['last_result_ids'][:3]
   if c=='contact':return r['kind']=='contact' and [h['id'] for h in r['hospitals']]==s['last_hospital_ids']
   return r['kind']=='contact' and [h['id'] for h in r['hospitals']]==['rs-171'] and c.capitalize() in r['text']
  await record(' → '.join(turns),'context',check,turns=turns)
 result={'environment':'Existing RDF/SIRS via RDFLib; no live Fuseki/PostgreSQL','total':len(rows),'passed':sum(x['passed'] for x in rows),'results':rows}
 initial=ROOT/'docs/NARA_3_HELDOUT_V2_INITIAL.json'
 if not initial.exists():initial.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 (ROOT/'docs/NARA_3_HELDOUT_V2_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print(result['passed'],'/',result['total'],flush=True)
 for r in rows:
  if not r['passed']:print(r['id'],r['prompt'],r['response']['kind'],r['response']['text'],flush=True)

if __name__=='__main__':asyncio.run(main())
