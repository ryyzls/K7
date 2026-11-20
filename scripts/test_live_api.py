"""Quick live test of 3 new API endpoints."""
import urllib.request, json

endpoints = [
    ('GET /api/enrichment/summary', 'http://localhost:8000/api/enrichment/summary'),
    ('GET /api/hospitals/rs-171', 'http://localhost:8000/api/hospitals/rs-171'),
    ('GET /api/hospitals/rs-001/operational-hours', 'http://localhost:8000/api/hospitals/rs-001/operational-hours'),
]

for name, url in endpoints:
    try:
        r = urllib.request.urlopen(url, timeout=5)
        d = json.loads(r.read().decode())
        if 'coverage_6_fitur' in d:
            meta = d.get('metadata', {})
            print(f"PASS {name}: total_rs={meta.get('total_rumah_sakit')}, triples={meta.get('rdf_triples_overlay')}")
        elif 'rs_id' in d:
            print(f"PASS {name}: rs_id={d.get('rs_id')}, direktur={str(d.get('direktur',''))[:30]}, email={d.get('email_display','?')}, igd={d.get('igd_24jam_terlapor','?')}")
        else:
            print(f"PASS {name}: HTTP 200, keys={list(d.keys())[:6]}")
    except Exception as e:
        print(f"FAIL {name}: {e}")
