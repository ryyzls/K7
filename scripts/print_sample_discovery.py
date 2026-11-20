import csv

with open('data/enrichment/mass_discovery/candidate_websites.csv', mode='r', encoding='utf-8') as f:
    r = list(csv.DictReader(f))

verified = [x for x in r if x['status'] == 'VERIFIED_OFFICIAL'][:15]
for idx, x in enumerate(verified, 1):
    print(f"{idx}. [{x['id_carisehat']}] {x['nama']} ({x['kabkota']}) -> {x['candidate_url']} (Domain: {x['domain']})")
