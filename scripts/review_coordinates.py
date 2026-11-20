#!/usr/bin/env python3
"""CariSehat: offline review coordinates and stage manually verified corrections.

Never edits data/koordinat.csv or Fuseki. Stdlib only.
Usage:
  python scripts/review_coordinates.py
  python scripts/review_coordinates.py --reviewed docs/coordinate-review/verified_input.csv
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ['kode','nama','kab_kota','alamat','lat_lama','lon_lama','sumber_lama',
          'prioritas','masalah','osm_search_url','maps_search_url',
          'lat_baru','lon_baru','source_url','verified_at','catatan_verifikasi']
BOX = (0.0, 4.5, 96.0, 101.0)  # broad sanity box incl. Nias & south Sumut, not proof of RS location

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as fp:
        return list(csv.DictReader(fp))

def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as fp:
        writer=csv.DictWriter(fp, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)

def valid_xy(lat,lon):
    try:
        a,b=float(lat),float(lon)
        return math.isfinite(a) and math.isfinite(b) and BOX[0] <= a <= BOX[1] and BOX[2] <= b <= BOX[3]
    except (TypeError,ValueError):
        return False

def build(master, coords):
    if len(master)!=206:
        raise ValueError(f'Expected 206 master RS, found {len(master)}; inspect project version before proceeding')
    codes=[f'rs-{i:03d}' for i in range(1,len(master)+1)]
    coord_ids=[c.get('kode','').strip() for c in coords]
    if len(coord_ids)!=len(set(coord_ids)) or set(coord_ids)!=set(codes):
        raise ValueError('IDs in coordinate CSV are duplicate/missing/extra; stop and inspect')
    cm={c['kode']:c for c in coords}
    occupied=defaultdict(list)
    for c in coords:
        if valid_xy(c.get('lat'),c.get('lon')):
            occupied[(round(float(c['lat']),6),round(float(c['lon']),6))].append(c['kode'])
    result=[]
    for i,rs in enumerate(master,1):
        code=f'rs-{i:03d}'; c=cm[code]
        src=(c.get('sumber') or '').strip().lower()
        lat=(c.get('lat') or '').strip();lon=(c.get('lon') or '').strip()
        problems=[]
        if not valid_xy(lat,lon): problems.append('koordinat_kosong_atau_di_luar_batas')
        elif src in ('kabkota','jalan'): problems.append('koordinat_perkiraan_'+src)
        elif src not in ('nama','osm'): problems.append('kategori_sumber_tidak_dikenal')
        if valid_xy(lat,lon) and len(occupied[(round(float(lat),6),round(float(lon),6))])>1:
            problems.append('titik_sama_dengan_'+','.join(k for k in occupied[(round(float(lat),6),round(float(lon),6))] if k!=code))
        if c.get('nama','').strip().casefold()!=rs['Rumah Sakit'].strip().casefold():
            problems.append('nama_koordinat_berbeda_dari_master')
        priority='P0' if not valid_xy(lat,lon) else ('P1' if src in ('kabkota','jalan') else 'P2')
        search=f"{rs['Rumah Sakit']}, {rs['Alamat']}, {rs['Kab/Kota']}, Sumatera Utara"
        result.append(dict(kode=code,nama=rs['Rumah Sakit'],kab_kota=rs['Kab/Kota'],alamat=rs['Alamat'],
                           lat_lama=lat,lon_lama=lon,sumber_lama=src or 'unknown',prioritas=priority,
                           masalah=';'.join(problems),
                           osm_search_url='https://www.openstreetmap.org/search?query='+quote(search),
                           maps_search_url='https://www.google.com/maps/search/?api=1&query='+quote(search),
                           lat_baru='',lon_baru='',source_url='',verified_at='',catatan_verifikasi=''))
    return result

def apply_review(rows, reviewed, original):
    byid={r['kode']:r for r in rows}
    accepted={}; errors=[]
    for idx,r in enumerate(reviewed,2):
        code=(r.get('kode') or '').strip(); lat=(r.get('lat_baru') or '').strip(); lon=(r.get('lon_baru') or '').strip()
        if not lat and not lon: continue
        if code not in byid: errors.append(f'row {idx}: unknown kode {code}');continue
        if code in accepted: errors.append(f'row {idx}: duplicated correction for {code}');continue
        url=(r.get('source_url') or '').strip(); when=(r.get('verified_at') or '').strip()
        if not valid_xy(lat,lon): errors.append(f'row {idx}: coordinates invalid for {code}'); continue
        if not url.startswith(('https://','http://')) or ' ' in url:
            errors.append(f'row {idx}: source_url must be a traceable URL for {code}');continue
        try:
            d=date.fromisoformat(when)
            if d>date.today(): raise ValueError('future verification date')
        except ValueError:
            errors.append(f'row {idx}: verified_at must be past/present YYYY-MM-DD for {code}');continue
        # Confirm the original name is unchanged between review and stage, if provided.
        if r.get('nama') and r['nama'].strip()!=byid[code]['nama'].strip():
            errors.append(f'row {idx}: name mismatch for {code}');continue
        accepted[code]=(lat,lon,url,when,(r.get('catatan_verifikasi') or '').strip())
    if errors: raise ValueError('\n'.join(errors))
    out=[]
    for r in original:
        c=dict(r); key=c['kode']
        if key in accepted:
            lat,lon,*_=accepted[key];c.update(lat=f'{float(lat):.6f}',lon=f'{float(lon):.6f}',sumber='manual_verified')
        out.append(c)
    return out, accepted

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reviewed',type=Path,help='CSV with manually confirmed coordinates; stages proposed output only')
    args=ap.parse_args()
    cpath=ROOT/'data/koordinat.csv'; mpath=ROOT/'data/rumah_sakit_sumut.csv'
    output=ROOT/'docs/coordinate-review';output.mkdir(parents=True,exist_ok=True)
    originals=read_csv(cpath); master=read_csv(mpath)
    rows=build(master,originals)
    priority=sorted(rows,key=lambda r:({'P0':0,'P1':1,'P2':2}[r['prioritas']],r['kode']))
    queue=output/'review_queue.csv'
    # Preserve users' hand-entered corrections: do not overwrite the review queue.
    if not queue.exists(): write_csv(queue,priority,FIELDS)
    summary=dict(hospitals=len(rows),source_sha256=hashlib.sha256(cpath.read_bytes()).hexdigest(),
                 priority_counts=dict(Counter(r['prioritas'] for r in rows)),
                 source_counts=dict(Counter(r['sumber_lama'] for r in rows)),
                 repeated_coordinate_rows=sum('titik_sama_dengan_' in r['masalah'] for r in rows),
                 queue=str(queue),notes=['P0 = missing/invalid; P1 = approximate street/city; P2 = name/OSM (still not verified)',
                 'OSM and Google Maps links are search shortcuts, NOT evidence or a source of verified coordinates.',
                 'Neither the RDF graph nor the live DB/website is modified.'])
    if args.reviewed:
        reviewed=read_csv(args.reviewed)
        proposed,accepted=apply_review(rows,reviewed,originals)
        dest=output/'koordinat.PROPOSED.csv'
        # Do not overwrite an earlier proposed output without manual deletion.
        if dest.exists(): raise ValueError(f'{dest} already exists; inspect/move it before restaging')
        write_csv(dest,proposed,['kode','nama','lat','lon','sumber'])
        write_csv(output/'accepted_corrections.csv',
                  [dict(kode=k,lat_baru=v[0],lon_baru=v[1],source_url=v[2],verified_at=v[3],catatan_verifikasi=v[4]) for k,v in accepted.items()],
                  ['kode','lat_baru','lon_baru','source_url','verified_at','catatan_verifikasi'])
        summary.update(accepted_corrections=len(accepted),proposed_csv=str(dest))
    (output/'review_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
