import csv
from collections import Counter

services = Counter()
igd_hospitals = set()
diagnostic_hospitals = {
    'CT Scan': set(),
    'MRI': set(),
    'USG': set(),
    'Radiologi': set(),
    'Hemodialisis': set(),
    'Laboratorium': set(),
    'Kamar Bedah / Operasi': set(),
    'Farmasi': set(),
}

with open('data/enrichment/tahap2/hasil_profil_sirs_206/sirs_pelayanan_raw.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        svc = r['pelayanan_tercatat'].strip()
        services[svc] += 1
        h_id = r['id_carisehat']
        if '24 jam' in svc.lower() or 'gawat darurat' in svc.lower():
            igd_hospitals.add(h_id)
        if 'ct scan' in svc.lower() or 'ct-scan' in svc.lower():
            diagnostic_hospitals['CT Scan'].add(h_id)
        if 'mri' in svc.lower():
            diagnostic_hospitals['MRI'].add(h_id)
        if 'usg' in svc.lower():
            diagnostic_hospitals['USG'].add(h_id)
        if 'radiologi' in svc.lower():
            diagnostic_hospitals['Radiologi'].add(h_id)
        if 'hemodialisa' in svc.lower() or 'hemodialisis' in svc.lower() or 'dialisis' in svc.lower():
            diagnostic_hospitals['Hemodialisis'].add(h_id)
        if 'laboratorium' in svc.lower() or 'patologi' in svc.lower():
            diagnostic_hospitals['Laboratorium'].add(h_id)
        if 'bedah' in svc.lower() or 'operasi' in svc.lower():
            diagnostic_hospitals['Kamar Bedah / Operasi'].add(h_id)
        if 'farmasi' in svc.lower():
            diagnostic_hospitals['Farmasi'].add(h_id)

print(f"Hospitals with IGD 24h reported: {len(igd_hospitals)} / 206")
for k, v in diagnostic_hospitals.items():
    print(f"Hospitals with {k}: {len(v)} / 206")

print("\nServices matching keywords:")
for s, c in services.most_common():
    if any(k.lower() in s.lower() for k in ['darurat', 'scan', 'mri', 'dialisa', 'dialisis', 'radiologi', 'hemodialisa']):
        print(f"  {s}: {c}")
