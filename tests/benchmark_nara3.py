"""Rerun all 138 legacy scenarios without overwriting historical artifacts.
Independent mandatory-criteria checks use RDF triples, not chatbot plans or search outputs.
"""
import sys, asyncio, csv, json, time, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'scratch')]
import runtime_fixture
import chatbot_benchmark as old
from test_nara3 import oracle_ids
from app.services.chatbot.engine import process
from app.services.chatbot_service import process_chat_message_legacy
from app.services import hybrid_search as hs
from rdflib import RDF
from test_nara3 import G, HF, SC

# Exact identity independently looked up from RDF labels; no manual replacement hospital creation.
vita=[str(h).rsplit('/',1)[-1] for h in G.default_graph.subjects(RDF.type,HF.RumahSakit) if 'Vita Insani' in str(G.default_graph.value(h,SC.name))]
assert vita==['rs-199'],vita

SERVICE_CASES={'C02':'Jantung dan Pembuluh Darah','C09':'Jantung dan Pembuluh Darah','E01':'Jantung dan Pembuluh Darah','E02':'Saraf','E03':'Mata','E04':'Kesehatan Anak','E05':'Obstetri dan Ginekologi','G02':'Jantung dan Pembuluh Darah','G08':'Jantung dan Pembuluh Darah','J01':'Jantung dan Pembuluh Darah'}
FACILITY_CASES={'C10':['Hemodialisis'],'E06':['Hemodialisis'],'E07':['Hemodialisis'],'F01':['ICU'],'F02':['NICU'],'F03':['PICU'],'F04':['CT Scan'],'F05':['MRI'],'F06':['Radiologi'],'F07':['Laboratorium Klinik'],'F08':['ICU','Ventilator'],'G01':['ICU'],'G04':['ICU','NICU'],'G06':['CT Scan'],'G08':['ICU','CT Scan']}

def checks_for(tid,checks):
    checks=[(kind,vita[0] if kind=='expect_id' and val=='rs-200' else val) for kind,val in checks]
    # These are distinct requested intents in NARA 3; accepting them is not a data correction.
    if tid=='A06': checks=[('intent_in',['GREETING','GRATITUDE'])]
    if tid=='A07': checks=[('intent_in',['GREETING','FAREWELL'])]
    if tid=='B04': checks=[('intent_in',['DETAIL','DISAMBIGUASI']),('expect_id','rs-157')]
    if tid=='F05' and not oracle_ids(facility='MRI'):
        checks=[('max_hospitals',0),('contains_any',['tidak ditemukan'])]
    return checks

def evidence(tid,resp):
    actual={h['id'] for h in resp.get('hospitals',[])}
    allowed=oracle_ids()
    if tid in SERVICE_CASES: allowed &= oracle_ids(service=SERVICE_CASES[tid])
    for facility in FACILITY_CASES.get(tid,[]):
        if facility=='Ventilator':
            from test_nara3 import F,CS
            valid=set()
            for h in G.default_graph.subjects(RDF.type,HF.RumahSakit):
                if any(str(F.value(o,CS.jenisFasilitas)).endswith('_dengan_ventilator') and float(F.value(o,CS.kapasitasTerlapor) or 0)>0 for o in F.objects(h,HF.fasilitasKritis)):valid.add(str(h).rsplit('/',1)[-1])
            allowed &= valid
        else: allowed &= oracle_ids(facility=facility)
    if tid=='G05': allowed &= oracle_ids(service='Jantung dan Pembuluh Darah') | oracle_ids(service='Saraf')
    if tid=='E08': allowed &= oracle_ids(facility='Radiologi') | oracle_ids(facility='CT Scan') | oracle_ids(facility='USG')
    if tid=='E09': allowed &= oracle_ids(service='Orthopedi')
    if tid in ('G03','I02'): allowed &= oracle_ids(service='Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu')
    if tid=='G09': allowed &= oracle_ids(service='Kesehatan anak')
    if tid in ('C11','G09','I03','I04'):
        # Independently traverse recorded schedule literals, not the planner/engine.
        from rdflib import URIRef
        from test_nara3 import RDFS
        graph=G.graph(URIRef('http://carisehat.id/graph/enrichment/2026-11-20'))
        days=['senin','selasa','rabu','kamis','jumat','sabtu','minggu']
        wanted=6 if tid=='I04' else 5
        scheduled=set()
        for h in G.default_graph.subjects(RDF.type,HF.RumahSakit):
            for schedule in graph.objects(h,SC.openingHoursSpecification):
                label=str(graph.value(schedule,RDFS.label)).lower()
                if tid in ('G09','I03') and 'poliklinik' not in label:continue
                day=str(graph.value(schedule,SC.description)).lower()
                indexes=[days.index(m[0]) for m in re.finditer('|'.join(days),day)]
                if len(indexes)==2 and re.search(r'[-–—]|sampai|s/d',day):indexes=list(range(indexes[0],indexes[1]+1))
                opens=str(graph.value(schedule,SC.opens));closes=str(graph.value(schedule,SC.closes))
                if wanted in indexes and re.fullmatch(r'\d{2}:\d{2}',opens) and re.fullmatch(r'\d{2}:\d{2}',closes) and opens!=closes:
                    scheduled.add(str(h).rsplit('/',1)[-1])
        allowed &= scheduled
    if tid in ('G02','G03'):
        owner_words=('swasta','perusahaan','organisasi','yayasan','perorangan') if tid=='G02' else ('pemkab','pemkot','pemprop','kemkes','kementerian','tni','polri')
        owner_ids={str(h).rsplit('/',1)[-1] for h in G.default_graph.subjects(RDF.type,HF.RumahSakit) if any(w in str(G.default_graph.value(h,HF.pemilik)).lower() for w in owner_words)}
        allowed &= owner_ids
    bad=actual-allowed
    return 'mandatory RDF evidence mismatch: '+','.join(sorted(bad)) if bad else ''

runner=asyncio.Runner()
engine=process
responses=[]
def run_chat(client,text,state=None,history=None,lat=None,lon=None):
    begin=time.perf_counter()
    resp=runner.run(engine(text,state=state,history=history,lat=lat,lon=lon))
    responses.append(resp)
    return 200,resp,round((time.perf_counter()-begin)*1000,2)
old.run_chat=run_chat
original_evaluate=old.evaluate_case

def run_version(fn):
    global engine,responses
    engine=fn;responses=[];rows=[]
    for tid,cat,prompt,intent,checks in old.build_single_turn_cases():
        code,resp,ms=run_chat(None,prompt)
        status,reason=original_evaluate({'checks':checks_for(tid,checks)},code,resp,ms)
        mismatch=evidence(tid,resp)
        if mismatch: status='FAIL';reason+=' '+mismatch
        rows.append(dict(test_id=tid,category=cat,prompt=prompt,status=status,reason=reason,ms=ms,ids='|'.join(h['id'] for h in resp.get('hospitals',[])),response=resp.get('text',''),intent=resp.get('state',{}).get('last_intent')))
    start=len(responses)
    mt,_=old.run_multi_turn_scenarios(None)
    for row,resp in zip(mt,responses[start:]):
        tid=row['test_id'];status=row['status'];reason=row['failure_reason'];ids={h['id'] for h in resp.get('hospitals',[])}
        allowed=None
        if tid=='K1-T3': allowed=oracle_ids('Kota Medan',{'B'},facility='ICU')
        if tid in ('K1-T4','K1-T5'): allowed=oracle_ids('Kota Medan',{'B'},'Jantung dan Pembuluh Darah','ICU')
        if allowed is not None and ids-allowed:status='FAIL';reason+=' mandatory context evidence mismatch'
        rows.append(dict(test_id=tid,category=row['category'],prompt=row['prompt'],status=status,reason=reason,ms=row['response_ms'],ids='|'.join(ids),response=resp.get('text',''),intent=resp.get('state',{}).get('last_intent')))
    for tid,prompt in [('D05-GPS','Rumah sakit terdekat dari lokasi saya.'),('M03-GPS','Saya mengalami nyeri dada dan sesak napas.'),('H01-GPS','Berapa jarak ke RS Adam Malik?')]:
        code,resp,ms=run_chat(None,prompt,lat=3.5952,lon=98.6722)
        ok=bool(resp.get('is_emergency')) if tid.startswith('M') else bool(resp.get('hospitals')) and ('km' in resp.get('text','') or all(h.get('distance_km') is not None for h in resp['hospitals']))
        rows.append(dict(test_id=tid,category='GPS',prompt=prompt,status='PASS' if ok else 'FAIL',reason='' if ok else 'missing verified distance/emergency',ms=ms,ids='|'.join(h['id'] for h in resp.get('hospitals',[])),response=resp.get('text',''),intent=resp.get('state',{}).get('last_intent')))
    return rows

def summary(rows):
    return {'total':len(rows),'passed':sum(r['status']=='PASS' for r in rows),'failed':sum(r['status']!='PASS' for r in rows),'pass_rate':round(100*sum(r['status']=='PASS' for r in rows)/len(rows),2)}

if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'after'
    if mode == 'archive':
        rows=[]
        with (ROOT/'docs/CHATBOT_BENCHMARK_RESULTS.csv').open(encoding='utf-8-sig') as f:
            for oldrow in csv.DictReader(f):
                tid=oldrow['test_id']; ids=oldrow['actual_hospital_ids'].split('|') if oldrow['actual_hospital_ids'] else []
                status=oldrow['status'];reason=oldrow['failure_reason']
                if "expected rs-200 not in" in reason and ';' not in reason and 'rs-199' in ids:
                    status='PASS';reason='Vita Insani ID independently corrected to rs-199'
                mismatch=evidence(tid,{'hospitals':[{'id':hid} for hid in ids]})
                if mismatch:status='FAIL';reason+=' '+mismatch
                rows.append({'test_id':tid,'status':status,'reason':reason,'ids':'|'.join(ids)})
        (ROOT/'docs/NARA_3_BEFORE_RAW.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
        print(json.dumps(summary(rows)));sys.exit(0)
    rows=run_version(process_chat_message_legacy if mode=='before' else process)
    (ROOT/f'docs/NARA_3_{mode.upper()}_RAW.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
    if mode=='after':
        with (ROOT/'docs/NARA_3_BENCHMARK_RESULTS.csv').open('w',newline='',encoding='utf8') as f:
            writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
        before_path=ROOT/'docs/NARA_3_BEFORE_RAW.json'
        result={'environment':'RDFLib over existing RDF/named graphs; SQLite fixture; not live Fuseki/PostgreSQL','historical_raw':{'passed':75,'total':138,'pass_rate':54.35},'corrected_archived_baseline':summary(json.loads(before_path.read_text(encoding='utf8'))) if before_path.exists() else None,'baseline_method':'Archived IDs revalidated against RDF; historical failures retained except isolated wrong Vita Insani ID. Legacy rerun interrupted after prolonged execution. Not a fresh baseline runtime.','after':summary(rows),'oracle_corrections':['All Vita Insani expected IDs resolved from RDF: rs-199','Gratitude/farewell accept explicit intents','Murni Teguh accepts clarification because multiple real entities match','MRI has zero affirmative evidence: empty is correct','Service/facility/ownership/context evidence checked independently from RDF; case-preserving source labels compared case-insensitively'],'acceptance_target_met':summary(rows)['pass_rate']>=95}
        result['benchmark_target_met']=result.pop('acceptance_target_met')
        result['overall_acceptance_complete']=False
        result['medical_safety_legacy_suite']=summary([r for r in rows if r['category'].startswith('M.')])
        result['security_legacy_suite']=summary([r for r in rows if r['category'].startswith('O.')])
        (ROOT/'docs/NARA_3_BENCHMARK_SUMMARY.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        (ROOT/'docs/NARA_3_CONVERSATION_SAMPLES.md').write_text('# NARA 3 — Actual RDF-backed conversation samples\n\n'+'\n\n'.join(f"## {r['test_id']} — {r['status']}\n\nUser: {r['prompt']}\n\nNARA: {r['response']}\n\nIDs: {r['ids']}\n\nEvaluation: {r['reason']}" for r in rows if r['test_id'].startswith(('K','G','M'))),encoding='utf8')
    print(json.dumps(summary(rows)),flush=True)
