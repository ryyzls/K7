"""Additional held-out utterances, evaluated after the primary rules were written."""
import sys,asyncio,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_nara3 import oracle_ids
from app.services.chatbot.engine import process
cases=[
 ('RS di Binjai dengan NICU', {'region':'Kota Binjai','facility':'NICU'}),
 ('RS kelas C di Medan', {'region':'Kota Medan','classes':{'C'}}),
 ('RS dengan PICU di Deli Serdang',{'region':'Kab. Deli Serdang','facility':'PICU'}),
 ('Cari dokter mata di Medan',{'region':'Kota Medan','service':'Mata'}),
 ('RS dengan poliklinik kandungan di Binjai',{'region':'Kota Binjai','service':'Obstetri dan ginekologi'}),
 ('RS kelas B yang ada NICU',{'classes':{'B'},'facility':'NICU'}),
]
async def main():
 rows=[]
 for q,kwargs in cases:
  r=await process(q); expected=oracle_ids(**kwargs);actual={h['id'] for h in r['hospitals']}
  ok=r.get('total')==len(expected) and actual<=expected and (bool(actual)==bool(expected))
  rows.append({'prompt':q,'passed':ok,'expected_total':len(expected),'actual_total':r.get('total'),'ids':sorted(actual),'response':r['text']})
 for q,expected in [('Bapak tidak sadarkan diri sekarang',True),('Saya tidak sesak napas',False),('Kalau orang pingsan harus ke mana?',False),('Kemarin saya nyeri dada',False),('Tidak ada perdarahan berat',False),('Saya kesulitan bernapas berat',True)]:
  r=await process(q);rows.append({'prompt':q,'passed':r['is_emergency']==expected,'expected_emergency':expected,'actual_emergency':r['is_emergency']})
 target=Path(__file__).resolve().parents[1]/'docs/NARA_3_HELDOUT_RESULTS.json'
 if target.exists() and not target.with_name('NARA_3_HELDOUT_INITIAL.json').exists():
  target.with_name('NARA_3_HELDOUT_INITIAL.json').write_text(target.read_text(encoding='utf8'),encoding='utf8')
 target.write_text(json.dumps({'label':'Additional phrasing; initial held-out results preserved separately, subsequent runs are regression results','passed':sum(r['passed'] for r in rows),'total':len(rows),'results':rows},ensure_ascii=False,indent=2),encoding='utf8')
 print(sum(r['passed'] for r in rows),'/',len(rows))
asyncio.run(main())
