import os
import re
import csv
from pathlib import Path

html_dir = Path('data/enrichment/tahap2/hasil_profil_sirs_206/html_cache')
staging_csv = Path('data/enrichment/tahap2/CariSehat_Tahap2_Profil_206_Staging.csv')

mapping = []
with open(staging_csv, 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        mapping.append(row)

print(f"Total RS in staging: {len(mapping)}")

parsed_count = 0
direktur_found = 0
kepemilikan_found = 0
luas_found = 0

sample_data = []

re_direktur = re.compile(r'<b>Direktur:</b>\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
re_kepemilikan = re.compile(r'<b>Kepemilikan:</b>\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
re_luas_tanah = re.compile(r'<b>Luas Tanah:</b>\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
re_luas_bangunan = re.compile(r'<b>Luas Bangunan:</b>\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)

for rs in mapping:
    kode = rs['kode_rs_kemenkes'].strip()
    html_file = html_dir / f"{kode}.html"
    if html_file.exists():
        parsed_count += 1
        content = html_file.read_text(encoding='utf-8', errors='ignore')
        
        dir_m = re_direktur.search(content)
        kep_m = re_kepemilikan.search(content)
        lt_m = re_luas_tanah.search(content)
        lb_m = re_luas_bangunan.search(content)
        
        direktur = dir_m.group(1).strip() if dir_m else ""
        kepemilikan = kep_m.group(1).strip() if kep_m else ""
        luas_tanah = lt_m.group(1).strip() if lt_m else ""
        luas_bangunan = lb_m.group(1).strip() if lb_m else ""
        
        if direktur: direktur_found += 1
        if kepemilikan: kepemilikan_found += 1
        if luas_tanah: luas_found += 1
        
        if len(sample_data) < 5:
            sample_data.append({
                "id": rs["id_carisehat"],
                "nama": rs["nama_sirs"],
                "kode": kode,
                "direktur": direktur,
                "kepemilikan": kepemilikan,
                "luas_tanah": luas_tanah,
                "luas_bangunan": luas_bangunan
            })

print(f"Parsed {parsed_count}/206 HTML files:")
print(f"Direktur found: {direktur_found}/206")
print(f"Kepemilikan found: {kepemilikan_found}/206")
print(f"Luas tanah found: {luas_found}/206")

print("\nSample records:")
for s in sample_data:
    print(s)
