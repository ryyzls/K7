import csv

with open('data/enrichment/mass_discovery/candidate_websites.csv', mode='r', encoding='utf-8') as f:
    r = list(csv.DictReader(f))

seen_kab = set()
diverse_samples = []
for x in r:
    if x['status'] == 'VERIFIED_OFFICIAL' and x['kabkota'] not in seen_kab:
        seen_kab.add(x['kabkota'])
        diverse_samples.append(x)
        if len(diverse_samples) >= 12:
            break

for idx, x in enumerate(diverse_samples, 1):
    print(f"{idx}. [{x['id_carisehat']}] {x['nama']} | {x['kabkota']} -> {x['candidate_url']}")
