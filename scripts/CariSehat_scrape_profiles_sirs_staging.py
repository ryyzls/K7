#!/usr/bin/env python3
"""Read-only, resumable SIRS profile data collector for CariSehat.

Reads reconciliation CSV; fetches only official SIRS profile pages; writes staging files.
Never edits source CSV, database, RDF, or frontend. Treat all figures as reported,
not real-time availability or a guarantee of services.
"""
import argparse
import csv
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
from difflib import SequenceMatcher
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = 'https://sirs.kemkes.go.id/fo/home/profile_rs/'
HEADERS = {'User-Agent':'CariSehatUniversityResearch/1.0 (read-only; public hospital profile audit)', 'Accept':'text/html'}

def tidy(s):
    return re.sub(r'\s+', ' ', s or '').strip()

def norm(s):
    return re.sub(r'[^a-z0-9]+',' ', tidy(s).lower()).strip()

def save_csv(path, cols, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(data)
    temp.replace(path)

class SIRSHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headers=[]; self.rows=[]; self.tables=[]
        self._tag_depth=0; self._heading=None; self._heading_level=None
        self._in_table=False; self._table_depth=0; self._table_heading=''
        self._in_row=False; self._cell=None; self._cell_tag=None; self._table_rows=[]; self._row=[]
        self._current_heading=''; self._headings=[]; self._title=''
    def handle_starttag(self,tag,attrs):
        if tag in ('h1','h2','h3','h4','h5','h6') and not self._in_table:
            self._heading=[]; self._heading_level=tag
        elif tag=='table':
            if not self._in_table:
                self._in_table=True; self._table_depth=1; self._table_heading=self._current_heading; self._table_rows=[]
            else: self._table_depth+=1
        elif tag=='tr' and self._in_table:
            self._in_row=True; self._row=[]
        elif tag in ('td','th') and self._in_table and self._in_row:
            self._cell=[]; self._cell_tag=tag
    def handle_data(self,data):
        if self._heading is not None: self._heading.append(data)
        if self._cell is not None: self._cell.append(data)
    def handle_endtag(self,tag):
        if self._heading is not None and tag==self._heading_level:
            h=tidy(''.join(self._heading)); self._headings.append(h)
            if h: self._current_heading=h
            self._heading=None; self._heading_level=None
        elif tag in ('td','th') and self._cell is not None and self._cell_tag==tag:
            self._row.append(tidy(''.join(self._cell))); self._cell=None; self._cell_tag=None
        elif tag=='tr' and self._in_table:
            if self._row: self._table_rows.append(self._row)
            self._in_row=False; self._row=[]
        elif tag=='table' and self._in_table:
            self._table_depth-=1
            if self._table_depth==0:
                self.tables.append((self._table_heading, self._table_rows))
                self._in_table=False; self._table_rows=[]

def parse_profile(html):
    p=SIRSHTML(); p.feed(html)
    hospital=''
    for i,h in enumerate(p._headings):
        if 'profile fasyankes' in h.lower() and i+1<len(p._headings):
            hospital=p._headings[i+1]; break
    if not hospital:
        for h in p._headings:
            if h.lower().startswith(('rs ','rsu ','rsud ','rumah sakit','og hospital')):
                hospital=h;break
    sections={'pelayanan': [],'tempat_tidur': [],'sdm': []}
    for heading, rows in p.tables:
        h=norm(heading)
        # The source uses headings 'Data Pelayanan', 'Data Tempat Tidur', 'Data Sumber Daya Manusia'.
        section = ('pelayanan' if 'pelayanan' in h else
                   'tempat_tidur' if 'tempat tidur' in h else
                   'sdm' if 'sumber daya manusia' in h else None)
        # Fallback to semantic table header if the heading is nested away.
        if section is None and rows:
            first=' '.join(norm(v) for v in rows[0])
            if 'no' in first and 'pelayanan' in first: section='pelayanan'
            elif 'no' in first and 'kelas' in first and 'jumlah' in first: section='tempat_tidur'
            elif 'no' in first and 'sdm' in first and 'jumlah' in first: section='sdm'
        if section is None: continue
        for row in rows:
            if not row or norm(row[0]) in ('no','nomor'): continue
            if not re.fullmatch(r'\d+',row[0]): continue
            if section=='pelayanan' and len(row)>=2 and row[1]: sections[section].append({'pelayanan_tercatat':row[1]})
            elif section=='tempat_tidur' and len(row)>=3 and row[1] and re.fullmatch(r'\d+',row[2].replace(',','')):
                sections[section].append({'jenis_tempat_tidur':row[1], 'jumlah_terlapor':int(row[2].replace(',',''))})
            elif section=='sdm' and len(row)>=4 and row[2] and re.fullmatch(r'\d+',row[3].replace(',','')):
                sections[section].append({'grup_sdm':row[1],'jenis_sdm':row[2],'jumlah_terlapor':int(row[3].replace(',',''))})
    return hospital,sections

def main():
    a=argparse.ArgumentParser(description='Read-only public SIRS profile enrichment (staging only)')
    a.add_argument('--input',required=True,help='Reconciled 206 hospital CSV')
    a.add_argument('--out',required=True,help='New staging directory')
    a.add_argument('--limit',type=int,default=206,help='Max hospital profiles this run (default:206)')
    a.add_argument('--delay',type=float,default=1.0,help='Pause between new downloads in seconds')
    a.add_argument('--timeout',type=int,default=15)
    a.add_argument('--offline',action='store_true',help='Only parse HTML previously cached by this script')
    args=a.parse_args()
    inp=Path(args.input).resolve();out=Path(args.out).resolve()
    if not inp.is_file(): sys.exit(f'ERROR: CSV not found: {inp}')
    if args.limit<1 or args.limit>206:sys.exit('ERROR: --limit must be 1..206')
    if args.delay<0.5:sys.exit('ERROR: --delay must be >= 0.5 s')
    if inp==out or inp in out.parents:sys.exit('ERROR: invalid output path')
    with inp.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    ids=[r['id_carisehat'] for r in rows]; codes=[r['kode_rs_kemenkes'] for r in rows]
    if len(set(ids))!=len(rows) or len(set(codes))!=len(rows) or not all(re.fullmatch(r'\d{7}',c) for c in codes):
        sys.exit('ERROR: nonunique hospital IDs or registration codes, or invalid code format')
    out.mkdir(parents=True,exist_ok=True)
    cached=out/'html_cache';cached.mkdir(exist_ok=True)
    statuses=[]; services=[]; beds=[]; sdms=[]
    selected=rows[:args.limit];fetched=0
    for n,rec in enumerate(selected,1):
        code=rec['kode_rs_kemenkes']; url=BASE+code;f=cached/(code+'.html')
        status={'id_carisehat':rec['id_carisehat'],'kode_rs_kemenkes':code,'nama_master':rec['nama_sirs'],
                'nama_halaman':'','status':'','jumlah_pelayanan':0,'jumlah_tempat_tidur':0,'jumlah_sdm':0,
                'url_sumber':url,'waktu_ambil_utc':'','error':''}
        try:
            if f.exists() and f.stat().st_size>200:
                raw=f.read_bytes();status['status']='CACHE'
            elif args.offline:
                status['status']='NOT_CACHED';statuses.append(status);continue
            else:
                if fetched:time.sleep(args.delay)
                request=Request(url,headers=HEADERS)
                with urlopen(request,timeout=args.timeout) as response:
                    if response.status!=200:raise ValueError(f'HTTP {response.status}')
                    raw=response.read(3_000_001)
                    if len(raw)>3_000_000:raise ValueError('HTML over 3MB; review manually')
                if len(raw)<200:raise ValueError('Short/empty HTML')
                tmp=f.with_suffix('.tmp');tmp.write_bytes(raw);tmp.replace(f)
                fetched+=1;status['status']='FETCHED'
            page=raw.decode('utf-8','replace')
            name, data=parse_profile(page)
            status['nama_halaman']=name
            status['waktu_ambil_utc']=datetime.now(timezone.utc).isoformat()
            # A missing heading or sections means the parser is not validated for this page.
            if not name or not any(data.values()):status['status']='PARSE_REVIEW'
            else:
                similarity=SequenceMatcher(None,norm(name),norm(rec['nama_sirs'])).ratio()
                if similarity<0.72:status['status']='IDENTITY_REVIEW'
                elif status['status']=='FETCHED':status['status']='EXTRACTED'
                elif status['status']=='CACHE':status['status']='EXTRACTED_CACHE'
            for item in data['pelayanan']:
                services.append({'id_carisehat':rec['id_carisehat'],'kode_rs_kemenkes':code,**item,
                                 'status_identitas':status['status'],'url_sumber':url,'waktu_ambil_utc':status['waktu_ambil_utc'],
                                 'interpretasi':'TERCATAT_DI_PROFIL_BUKAN_KETERSEDIAAN_REALTIME'})
            for item in data['tempat_tidur']:
                beds.append({'id_carisehat':rec['id_carisehat'],'kode_rs_kemenkes':code,**item,
                             'status_identitas':status['status'],'url_sumber':url,'waktu_ambil_utc':status['waktu_ambil_utc'],
                             'interpretasi':'KAPASITAS_TERLAPOR_BUKAN_TT_KOSONG'})
            for item in data['sdm']:
                sdms.append({'id_carisehat':rec['id_carisehat'],'kode_rs_kemenkes':code,**item,
                             'status_identitas':status['status'],'url_sumber':url,'waktu_ambil_utc':status['waktu_ambil_utc'],
                             'interpretasi':'JUMLAH_SDM_TERLAPOR_BUKAN_JADWAL_DOKTER'})
            status['jumlah_pelayanan']=len(data['pelayanan']);status['jumlah_tempat_tidur']=len(data['tempat_tidur']);status['jumlah_sdm']=len(data['sdm'])
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
            status['status']='FETCH_ERROR';status['error']=str(e)[:250]
        statuses.append(status)
        print(f"[{n}/{len(selected)}] {code} {status['status']} pelayanan={status['jumlah_pelayanan']} tt={status['jumlah_tempat_tidur']} sdm={status['jumlah_sdm']}",flush=True)
    common=['id_carisehat','kode_rs_kemenkes']
    save_csv(out/'profile_fetch_status.csv',common+['nama_master','nama_halaman','status','jumlah_pelayanan','jumlah_tempat_tidur','jumlah_sdm','url_sumber','waktu_ambil_utc','error'],statuses)
    save_csv(out/'sirs_pelayanan_raw.csv',common+['pelayanan_tercatat','status_identitas','url_sumber','waktu_ambil_utc','interpretasi'],services)
    save_csv(out/'sirs_tempat_tidur_raw.csv',common+['jenis_tempat_tidur','jumlah_terlapor','status_identitas','url_sumber','waktu_ambil_utc','interpretasi'],beds)
    save_csv(out/'sirs_sdm_raw.csv',common+['grup_sdm','jenis_sdm','jumlah_terlapor','status_identitas','url_sumber','waktu_ambil_utc','interpretasi'],sdms)
    manifest={'source':BASE,'input':str(inp),'records_selected':len(selected),'total_input':len(rows),
              'successful_extractions':sum(x['status'] in ('EXTRACTED','EXTRACTED_CACHE') for x in statuses),
              'needs_review':sum(x['status'] in ('PARSE_REVIEW','IDENTITY_REVIEW') for x in statuses),
              'errors':sum(x['status'] in ('FETCH_ERROR','NOT_CACHED') for x in statuses),
              'service_records':len(services),'bed_records':len(beds),'sdm_records':len(sdms),
              'generated_utc':datetime.now(timezone.utc).isoformat(),
              'warning':'STAGING ONLY. Do not automatically merge into application. Verify parser and identity matches; figures may be stale.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(manifest,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
