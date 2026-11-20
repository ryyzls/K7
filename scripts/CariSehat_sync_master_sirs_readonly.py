#!/usr/bin/env python3
"""CariSehat — read-only master RS reconciliation with public SIRS endpoint.

Runs on a machine with public Internet connectivity. Does not write to the
repository's existing CSV/Turtle/SQL data, and does not load Fuseki.

Usage:
  python CariSehat_sync_master_sirs_readonly.py --input CariSehat_Master_206_Tahap1.csv --out results_sirs

The SIRS public endpoint is dynamic and may change format or block requests.
One fetch only; no CAPTCHA, login or access restriction bypass.
"""
import argparse,csv,hashlib,json,re,unicodedata,urllib.request,urllib.error
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone

URL='https://sirs.kemkes.go.id/fo/home/rekap_rs_all?id=0'
MAX_BYTES=24*1024*1024

def norm(s):
 s=unicodedata.normalize('NFKC',str(s or '')).casefold().strip()
 s=re.sub(r'[^\w]+',' ',s,flags=re.UNICODE)
 return ' '.join(s.split())

def load_raw_rows(body):
 decoded=body.decode('utf-8-sig')
 try:data=json.loads(decoded)
 except json.JSONDecodeError:
  # Public endpoint may wrap a JSON array in a pre block.
  from html import unescape
  m=re.search(r'<pre[^>]*>(.*?)</pre>',decoded,re.I|re.S)
  if not m:raise ValueError('Endpoint tidak mengembalikan JSON; simpan manual sumber resmi jika perlu.')
  data=json.loads(unescape(m.group(1)))
 if isinstance(data,dict):
  for key in ('data','results','rows','result'):
   if isinstance(data.get(key),list):data=data[key];break
 if not isinstance(data,list):raise ValueError('Struktur JSON SIRS tidak terduga; tidak ada data ditulis.')
 return [x for x in data if isinstance(x,dict)]

def read_response(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CariSehat-academic-readonly-audit/1.0','Accept':'application/json,text/plain,*/*'})
 with urllib.request.urlopen(req,timeout=35) as resp:
  raw=resp.read(MAX_BYTES+1)
  if len(raw)>MAX_BYTES:raise ValueError('Respons di atas 24 MB; hentikan untuk keamanan.')
 return raw

def run():
 pa=argparse.ArgumentParser();pa.add_argument('--input',required=True);pa.add_argument('--out',default='results_sirs');args=pa.parse_args()
 inp=Path(args.input);out=Path(args.out)
 with inp.open(encoding='utf-8-sig',newline='') as f: local=list(csv.DictReader(f))
 if len(local)!=206:raise ValueError(f'Input bukan master 206 RS (didapat {len(local)}).')
 print('Mengambil rekap publik Kemenkes, 1 permintaan GET...')
 body=read_response(URL);remote=load_raw_rows(body)
 remote=[r for r in remote if norm(r.get('nama_prop'))=='sumatera utara']
 remote_codes=[str(x.get('kode') or '').strip() for x in remote]
 if len(remote_codes)!=len(set(remote_codes)):raise ValueError('Kode duplikat pada source rekap; perlu manual review.')
 byname=defaultdict(list)
 for r in remote:byname[norm(r.get('nama'))].append(r)
 matched=[];review=[];unmatched=[]
 for row in local:
  candidates=byname[norm(row['nama_rs_csv'])]
  exact_city=[x for x in candidates if norm(x.get('kab'))==norm(row['kab_kota_csv'])]
  if len(exact_city)==1:
   rs=exact_city[0];matched.append([row['id_carisehat'],row['nama_rs_csv'],row['kab_kota_csv'],str(rs.get('kode','')),rs.get('nama',''),rs.get('kab',''),rs.get('alamat',''),rs.get('TELEPON',''),rs.get('kelas',''),rs.get('jenis',''),URL,'MATCH_NAMA_DAN_KAB_EXACT; alamat/identitas tetap perlu review'])
  elif candidates:
   review.append({'id_carisehat':row['id_carisehat'],'nama':row['nama_rs_csv'],'kab':row['kab_kota_csv'],'candidates':[{'kode':x.get('kode'),'nama':x.get('nama'),'kab':x.get('kab'),'alamat':x.get('alamat')} for x in candidates]})
  else:unmatched.append({'id_carisehat':row['id_carisehat'],'nama':row['nama_rs_csv'],'kab':row['kab_kota_csv']})
 # Only create output after fetch, parsing and consistency checks finish.
 out.mkdir(parents=True,exist_ok=True)
 with (out/'sirs_sumut_snapshot.json').open('w',encoding='utf-8') as f:json.dump({'source_url':URL,'downloaded_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(body).hexdigest(),'records':remote},f,ensure_ascii=False,indent=2)
 with (out/'matches_exact.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['id_carisehat','nama_lokal','kab_lokal','kode_rs_kemenkes_kandidat','nama_kemenkes','kab_kemenkes','alamat_kemenkes','telepon_kemenkes','kelas_kemenkes','jenis_kemenkes','url_sumber','status']);w.writerows(matched)
 for key,data in [('perlu_review_manual.json',review),('belum_cocok.json',unmatched)]:
  with (out/key).open('w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
 print(json.dumps({'status':'DONE_STAGING_ONLY','sirs_sumut_records':len(remote),'local_records':len(local),'match_exact_name_city':len(matched),'need_manual_review':len(review),'unmatched':len(unmatched),'output':str(out)},ensure_ascii=False,indent=2))
 print('PENTING: exact name/city match bukan bukti status operasi/izin terbaru; jangan auto-merge ke RDF atau SQL.')
if __name__=='__main__':
 try:run()
 except (ValueError,urllib.error.URLError,TimeoutError) as e:
  raise SystemExit('GAGAL AMBIL DATA RESMI: '+str(e)+'; dataset asli tidak diubah.')
