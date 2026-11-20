"""
Integrate mass discovery candidates into final_info_rs datasets and update RDF.
Enforces the user's UI rules and stores audit metadata internally.
"""
import csv, json, os, pathlib
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))
NOW_STR = datetime.now(WIB).isoformat()

base_dir = pathlib.Path("data/enrichment/final_info_rs")
mass_dir = pathlib.Path("data/enrichment/mass_discovery")
docker_data_dir = pathlib.Path("backend/app/data/final_info_rs")

# 1. Load current master files
profil_list = json.loads((base_dir / "profil_lengkap_206.json").read_text(encoding='utf-8'))
kontak_list = json.loads((base_dir / "kontak_dan_website_206.json").read_text(encoding='utf-8'))
jam_list = json.loads((base_dir / "jam_operasional_unit_206.json").read_text(encoding='utf-8'))
fasilitas_list = json.loads((base_dir / "fasilitas_medis_berbasis_bukti_206.json").read_text(encoding='utf-8'))
igd_list = json.loads((base_dir / "igd_24jam_terlapor_206.json").read_text(encoding='utf-8'))

# Maps
profil_map = {r['id_carisehat']: r for r in profil_list}
kontak_map = {r['id_carisehat']: r for r in kontak_list}
jam_map = {r['id_carisehat']: r for r in jam_list}
igd_map = {r['id_carisehat']: r for r in igd_list}

# 2. Load mass discovery candidates
websites_cand = {}
with open(mass_dir / "candidate_websites.csv", mode='r', encoding='utf-8', errors='replace') as f:
    for row in csv.DictReader(f):
        rs_id = row.get('id_carisehat')
        if rs_id:
            websites_cand[rs_id] = row

emails_cand = {}
with open(mass_dir / "candidate_emails.csv", mode='r', encoding='utf-8', errors='replace') as f:
    for row in csv.DictReader(f):
        rs_id = row.get('id_carisehat')
        em = row.get('email', '').strip()
        if rs_id and em and em != 'EMAIL_BELUM_TERSEDIA':
            emails_cand[rs_id] = row

hours_cand = {}
with open(mass_dir / "candidate_hours.csv", mode='r', encoding='utf-8', errors='replace') as f:
    for row in csv.DictReader(f):
        rs_id = row.get('id_carisehat')
        if rs_id:
            if rs_id not in hours_cand:
                hours_cand[rs_id] = []
            hours_cand[rs_id].append(row)

# 3. Update Kontak dan Website
updated_kontak = []
website_count = 0
email_count = 0

for rs_id, k in kontak_map.items():
    entry = dict(k)
    
    # Website
    cand_w = websites_cand.get(rs_id)
    if entry.get('website_status') == 'verified' and entry.get('website_url'):
        # Keep existing verified
        entry['website_display'] = entry['website_url']
        website_count += 1
    elif cand_w and cand_w.get('candidate_url') and cand_w.get('status') != 'NOT_FOUND':
        entry['website_url'] = cand_w['candidate_url']
        entry['website_display'] = cand_w['candidate_url']
        entry['website_status'] = cand_w.get('status', 'CORROBORATED')
        entry['website_domain'] = cand_w.get('domain', '')
        entry['website_evidence'] = cand_w.get('evidence_snippet', '')
        entry['website_checked_at'] = cand_w.get('checked_at', '2026-11-20')
        website_count += 1
    else:
        entry['website_url'] = None
        entry['website_display'] = "Belum tersedia"
        entry['website_status'] = "NOT_FOUND"

    # Email
    cand_e = emails_cand.get(rs_id)
    if entry.get('email_status') == 'verified' and entry.get('email'):
        entry['email_display'] = entry['email']
        email_count += 1
    elif cand_e and cand_e.get('email'):
        entry['email'] = cand_e['email']
        entry['email_display'] = cand_e['email']
        entry['email_status'] = cand_e.get('status', 'CORROBORATED')
        entry['email_evidence'] = cand_e.get('evidence_snippet', '')
        entry['email_checked_at'] = cand_e.get('checked_at', '2026-11-20')
        email_count += 1
    else:
        entry['email'] = None
        entry['email_display'] = "Belum tersedia"
        entry['email_status'] = "NOT_FOUND"
        
    updated_kontak.append(entry)

print(f"Total RS with website: {website_count} / {len(kontak_map)}")
print(f"Total RS with email: {email_count} / {len(kontak_map)}")

# 4. Update Jam Operasional
updated_jam = []
jam_active_count = 0

for rs_id, j in jam_map.items():
    entry = dict(j)
    rs_cand_h = hours_cand.get(rs_id, [])
    units = entry.get('units', {})
    
    # Check if already verified in full (e.g. rs-171, rs-008, rs-007)
    if entry.get('status_jam_operasional') == 'JADWAL_TERVERIFIKASI' and units.get('poliklinik_rawat_jalan', {}).get('status') == 'TERVERIFIKASI':
        jam_active_count += 1
        updated_jam.append(entry)
        continue
        
    # IGD info from igd_map
    igd_info = igd_map.get(rs_id, {})
    is_igd_24 = igd_info.get('status_igd_24jam') == 'TERLAPOR_SIRS'
    if is_igd_24:
        units['igd'] = {
            'unit': 'Instalasi Gawat Darurat (IGD)',
            'buka_24_jam': True,
            'jam_display': 'Buka 24 Jam',
            'jadwal': [{'hari': 'Senin - Minggu', 'jam_buka': '00:00', 'jam_tutup': '24:00'}]
        }
    else:
        units['igd'] = {
            'unit': 'Instalasi Gawat Darurat (IGD)',
            'buka_24_jam': False,
            'jam_display': 'Belum tersedia',
            'jadwal': []
        }

    # Poliklinik & Pendaftaran from candidate hours
    poli_entries = [r for r in rs_cand_h if 'poli' in r.get('unit_type','').lower() or 'rawat jalan' in r.get('unit_type','').lower()]
    reg_entries = [r for r in rs_cand_h if 'daftar' in r.get('unit_type','').lower() or 'loket' in r.get('unit_type','').lower()]
    umum_entries = [r for r in rs_cand_h if 'umum' in r.get('unit_type','').lower() or 'rs' in r.get('unit_type','').lower()]

    has_active_poli = False
    if poli_entries:
        p = poli_entries[0]
        hari = p.get('hari') or 'Senin - Jumat'
        jb = p.get('jam_buka') or '08:00'
        jt = p.get('jam_tutup') or '16:00'
        units['poliklinik_rawat_jalan'] = {
            'unit': 'Poliklinik Rawat Jalan',
            'status': 'TERSEDIA',
            'jam_display': f"{hari} {jb} - {jt} WIB",
            'hari': hari,
            'jam_buka': jb,
            'jam_tutup': jt
        }
        has_active_poli = True
    elif umum_entries:
        u = umum_entries[0]
        hari = u.get('hari') or 'Senin - Jumat'
        jb = u.get('jam_buka') or '08:00'
        jt = u.get('jam_tutup') or '16:00'
        units['poliklinik_rawat_jalan'] = {
            'unit': 'Poliklinik Rawat Jalan',
            'status': 'TERSEDIA',
            'jam_display': f"{hari} {jb} - {jt} WIB",
            'hari': hari,
            'jam_buka': jb,
            'jam_tutup': jt
        }
        has_active_poli = True
    else:
        units['poliklinik_rawat_jalan'] = {
            'unit': 'Poliklinik Rawat Jalan',
            'status': 'BELUM_TERSEDIA',
            'jam_display': 'Belum tersedia',
            'hari': None,
            'jam_buka': None,
            'jam_tutup': None
        }

    if reg_entries:
        r = reg_entries[0]
        hari = r.get('hari') or 'Senin - Jumat'
        jb = r.get('jam_buka') or '07:30'
        jt = r.get('jam_tutup') or '14:00'
        units['pendaftaran'] = {
            'unit': 'Pendaftaran Pasien',
            'status': 'TERSEDIA',
            'jam_display': f"{hari} {jb} - {jt} WIB",
            'hari': hari,
            'jam_buka': jb,
            'jam_tutup': jt
        }
    else:
        units['pendaftaran'] = {
            'unit': 'Pendaftaran Pasien',
            'status': 'BELUM_TERSEDIA',
            'jam_display': 'Belum tersedia',
            'hari': None,
            'jam_buka': None,
            'jam_tutup': None
        }

    if has_active_poli:
        entry['status_jam_operasional'] = 'JADWAL_TERSEDIA'
        jam_active_count += 1
    elif is_igd_24:
        entry['status_jam_operasional'] = 'IGD_24_JAM_ONLY'
    else:
        entry['status_jam_operasional'] = 'JAM_BELUM_TERSEDIA'

    entry['units'] = units
    updated_jam.append(entry)

print(f"Total RS with active poli hours: {jam_active_count} / {len(jam_map)}")

# 5. Save JSON and CSV with full union of keys
def save_data(data, json_name, csv_name):
    for target_dir in [base_dir, docker_data_dir]:
        target_dir.mkdir(parents=True, exist_ok=True)
        # JSON
        (target_dir / json_name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        # CSV with union of all keys
        if data and isinstance(data, list) and isinstance(data[0], dict):
            all_keys = []
            for row in data:
                for k in row.keys():
                    if k not in all_keys:
                        all_keys.append(k)
            with open(target_dir / csv_name, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=all_keys)
                writer.writeheader()
                for row in data:
                    row_clean = {}
                    for k in all_keys:
                        v = row.get(k)
                        if isinstance(v, (dict, list)):
                            row_clean[k] = json.dumps(v, ensure_ascii=False)
                        else:
                            row_clean[k] = v
                    writer.writerow(row_clean)
    print(f"Saved {json_name} and {csv_name}")

save_data(updated_kontak, "kontak_dan_website_206.json", "kontak_dan_website_206.csv")
save_data(updated_jam, "jam_operasional_unit_206.json", "jam_operasional_unit_206.csv")

# 6. Update summary freeze
summary_freeze = {
  "metadata": {
    "title": "CariSehat Final Mass Discovery Integration & Semantic Freeze Summary",
    "tanggal_rilis": NOW_STR,
    "total_rumah_sakit": 206,
    "wilayah_kabupaten_kota": 33
  },
  "coverage_6_fitur": {
    "fitur_1_profil_lengkap": {
      "kode_kemenkes_terverifikasi": 206,
      "direktur_tercatat": 206,
      "kepemilikan_tercatat": 206,
      "luas_tanah_tercatat": 204,
      "luas_bangunan_tercatat": 204
    },
    "fitur_2_website_resmi": {
      "tersedia": website_count,
      "belum_tersedia": 206 - website_count
    },
    "fitur_3_email_dan_kontak": {
      "telepon_tersedia": 204,
      "email_tersedia": email_count,
      "email_belum_tersedia": 206 - email_count
    },
    "fitur_4_fasilitas_medis_berbukti": {
      "rs_memiliki_icu": 187,
      "rs_memiliki_nicu": 163,
      "rs_memiliki_picu": 112,
      "rs_memiliki_ct_scan": 62,
      "rs_memiliki_radiologi": 177,
      "rs_memiliki_hemodialisis": 61,
      "rs_memiliki_laboratorium": 60,
      "rs_memiliki_kamar_operasi": 196
    },
    "fitur_5_igd_24jam_terlapor": {
      "terlapor_24jam": 198,
      "tidak_terlapor_24jam": 8
    },
    "fitur_6_jam_operasional": {
      "jadwal_poliklinik_tersedia": jam_active_count,
      "jadwal_poliklinik_belum_tersedia": 206 - jam_active_count,
      "igd_buka_24jam": 198
    }
  }
}

for d in [base_dir, docker_data_dir]:
    (d / "ringkasan_cakupan_freeze.json").write_text(json.dumps(summary_freeze, indent=2, ensure_ascii=False), encoding='utf-8')

print("Done integrating mass discovery.")
