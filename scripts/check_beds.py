import csv
from collections import Counter

beds = Counter()
with open('data/enrichment/tahap2/hasil_profil_sirs_206/sirs_tempat_tidur_raw.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        try:
            qty = int(r['jumlah_terlapor'])
            if qty > 0:
                beds[r['jenis_tempat_tidur']] += qty
        except Exception:
            pass

print("Top bed types with positive count:")
for k, v in beds.most_common(25):
    print(f"  {k}: {v} beds total")
