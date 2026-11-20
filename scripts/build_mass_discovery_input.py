"""
Build mass discovery input: exports per-batch JSON files for swarm workers.
206 RS dibagi 7 batch berdasarkan kabkota.
"""
import json, pathlib, os

profil = json.loads(pathlib.Path('data/enrichment/final_info_rs/profil_lengkap_206.json').read_text('utf-8'))
kontak = json.loads(pathlib.Path('data/enrichment/final_info_rs/kontak_dan_website_206.json').read_text('utf-8'))

kontak_map = {r['id_carisehat']: r for r in kontak}

# Build master list
master = []
for rs in profil:
    k = kontak_map.get(rs['id_carisehat'], {})
    master.append({
        'id': rs['id_carisehat'],
        'kode_kemenkes': rs['kode_kemenkes'],
        'nama': rs['nama'],
        'kabkota': rs.get('kabkota', ''),
        'kelas': rs.get('kelas', ''),
        'jenis': rs.get('jenis', ''),
        'alamat': rs.get('alamat', ''),
        'telepon': k.get('telepon', ''),
        'website_status': k.get('website_status', 'unreviewed'),
        'website_url': k.get('website_url'),
        'email': k.get('email'),
    })

# 7 batches - balanced by kabkota groups
# Batch 1: Kota Medan A (rs-* in Medan, first 33)
# Batch 2: Kota Medan B (Medan remaining 33)
# Batch 3: Deli Serdang + Binjai + Langkat
# Batch 4: Pematang Siantar + Tebing Tinggi + Simalungun + Karo
# Batch 5: Asahan + Labuhan Batu + Batu Bara + Serdang Bedagai + Tanjung Balai
# Batch 6: Tapanuli + Nias + Sibolga + Gunungsitoli + Mandailing
# Batch 7: Remaining kabkota

kabkota_batch = {
    'batch1': ['Kota Medan'],      # split A: first 33
    'batch2': ['Kota Medan'],      # split B: last 33
    'batch3': ['Deli Serdang', 'Kota Binjai', 'Langkat'],
    'batch4': ['Kota Pematang Siantar', 'Kota Tebing Tinggi', 'Simalungun', 'Karo', 'Dairi'],
    'batch5': ['Asahan', 'Labuhan Batu', 'Labuhan Batu Utara', 'Labuhan Batu Selatan', 'Batu Bara', 'Serdang Bedagai', 'Kota Tanjung Balai'],
    'batch6': ['Kota Padang Sidempuan', 'Tapanuli Selatan', 'Tapanuli Utara', 'Tapanuli Tengah', 'Mandailing Natal', 'Padang Lawas', 'Padang Lawas Utara', 'Humbang Hasundutan', 'Samosir', 'Toba Samosir', 'Pakpak Bharat'],
    'batch7': ['Kota Sibolga', 'Kota Gunungsitoli', 'Nias', 'Nias Selatan', 'Nias Barat', 'Nias Utara'],
}

# Medan RS sorted by id
medan_rs = sorted([r for r in master if r['kabkota'] == 'Kota Medan'], key=lambda x: x['id'])

out_dir = pathlib.Path('data/enrichment/mass_discovery')
out_dir.mkdir(parents=True, exist_ok=True)

batches = {}
batches['batch1'] = medan_rs[:33]
batches['batch2'] = medan_rs[33:]

for batch_key, kab_list in kabkota_batch.items():
    if batch_key in ('batch1', 'batch2'):
        continue
    batches[batch_key] = [r for r in master if r['kabkota'] in kab_list]

# Save each batch
for batch_key, items in batches.items():
    out_path = out_dir / f'{batch_key}_input.json'
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{batch_key}: {len(items)} RS → {out_path}')

# Save full master
(out_dir / 'master_206.json').write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nTotal: {sum(len(v) for v in batches.values())} RS across {len(batches)} batches')

# Create output staging files
for fname in ['candidate_websites.csv', 'candidate_emails.csv', 'candidate_hours.csv', 'review_queue.csv', 'source_evidence.csv']:
    fp = out_dir / fname
    if not fp.exists():
        headers = {
            'candidate_websites.csv': 'id_carisehat,kode_kemenkes,nama,kabkota,candidate_url,domain,status,confidence,source_type,source_url,evidence_snippet,checked_at,notes\n',
            'candidate_emails.csv': 'id_carisehat,kode_kemenkes,nama,kabkota,email,status,source_type,source_url,evidence_snippet,checked_at,notes\n',
            'candidate_hours.csv': 'id_carisehat,kode_kemenkes,nama,kabkota,unit_type,hari,jam_buka,jam_tutup,session,status,source_url,checked_at,notes\n',
            'review_queue.csv': 'id_carisehat,kode_kemenkes,nama,kabkota,field_type,value,conflict_reason,sources,priority,added_at\n',
            'source_evidence.csv': 'id_carisehat,kode_kemenkes,source_type,source_url,raw_snippet,field_found,checked_at,batch\n',
        }
        fp.write_text(headers[fname], encoding='utf-8')
        print(f'Created staging file: {fp}')

print('\nDone. Ready for swarm workers.')
