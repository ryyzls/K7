import urllib.request, json

sample_ids = ['rs-001', 'rs-003', 'rs-009', 'rs-055', 'rs-171']
for sid in sample_ids:
    url = f"http://localhost:8000/api/hospitals/{sid}"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        d = json.loads(resp.read().decode())
        web = d.get('website') or 'Belum tersedia'
        email = d.get('email') or 'Belum tersedia'
        direktur = d.get('direktur') or 'Belum tersedia'
        jam = d.get('jam_operasional', {})
        print(f"[{sid}] {d['nama']}")
        print(f"  Website: {web}")
        print(f"  Email: {email}")
        print(f"  Direktur: {direktur}")
        print(f"  Jam Badge: {jam.get('overall_badge')}")
