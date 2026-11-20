"""
Aggregate batch 1 to 7 CSVs into final mass discovery staging files.
Generates statistics and summary.
"""
import csv, glob, os, pathlib, json

base_dir = pathlib.Path('data/enrichment/mass_discovery')

files_to_merge = [
    'candidate_websites',
    'candidate_emails',
    'candidate_hours',
    'source_evidence'
]

stats = {
    'total_processed': 0,
    'websites': {'total': 0, 'VERIFIED_OFFICIAL': 0, 'CORROBORATED': 0, 'REVIEW_REQUIRED': 0, 'NOT_FOUND': 0},
    'emails': {'total': 0, 'VERIFIED_OFFICIAL': 0, 'CORROBORATED': 0, 'REVIEW_REQUIRED': 0, 'NOT_FOUND': 0},
    'hours': {'total_entries': 0, 'rs_with_hours': set()},
    'review_queue': []
}

for prefix in files_to_merge:
    out_file = base_dir / f"{prefix}.csv"
    batch_files = sorted(base_dir.glob(f"{prefix}_batch*.csv"))
    
    header = None
    all_rows = []
    
    for bf in batch_files:
        with open(bf, mode='r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.reader(f)
            try:
                file_header = next(reader)
                if header is None:
                    header = file_header
                for row in reader:
                    if row and any(field.strip() for field in row):
                        all_rows.append(row)
            except StopIteration:
                pass
                
    if header and all_rows:
        with open(out_file, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(all_rows)
        print(f"Merged {len(all_rows)} rows into {out_file.name} from {len(batch_files)} batches.")

# Now parse aggregated files to calculate metrics
web_file = base_dir / "candidate_websites.csv"
if web_file.exists():
    with open(web_file, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        seen_rs = set()
        for r in reader:
            rs_id = r.get('id_carisehat')
            seen_rs.add(rs_id)
            st = r.get('status', '').strip().upper()
            if st in stats['websites']:
                stats['websites'][st] += 1
            else:
                stats['websites']['NOT_FOUND'] += 1
            stats['websites']['total'] += 1
            
            if st == 'REVIEW_REQUIRED':
                stats['review_queue'].append({
                    'id_carisehat': rs_id,
                    'kode_kemenkes': r.get('kode_kemenkes'),
                    'nama': r.get('nama'),
                    'kabkota': r.get('kabkota'),
                    'field_type': 'website',
                    'value': r.get('candidate_url'),
                    'conflict_reason': r.get('notes', ''),
                    'sources': r.get('source_url', ''),
                    'priority': 'MEDIUM',
                    'added_at': '2026-11-20'
                })
        stats['total_processed'] = len(seen_rs)

email_file = base_dir / "candidate_emails.csv"
if email_file.exists():
    with open(email_file, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for r in reader:
            st = r.get('status', '').strip().upper()
            em = r.get('email', '').strip()
            if em and em != 'EMAIL_BELUM_TERSEDIA':
                if st in stats['emails']:
                    stats['emails'][st] += 1
                else:
                    stats['emails']['CORROBORATED'] += 1
                stats['emails']['total'] += 1
            else:
                stats['emails']['NOT_FOUND'] += 1

hours_file = base_dir / "candidate_hours.csv"
if hours_file.exists():
    with open(hours_file, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for r in reader:
            stats['hours']['total_entries'] += 1
            stats['hours']['rs_with_hours'].add(r.get('id_carisehat'))

# Write review_queue.csv
rq_file = base_dir / "review_queue.csv"
rq_headers = ['id_carisehat','kode_kemenkes','nama','kabkota','field_type','value','conflict_reason','sources','priority','added_at']
with open(rq_file, mode='w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rq_headers)
    writer.writeheader()
    writer.writerows(stats['review_queue'])
print(f"Written {len(stats['review_queue'])} items to {rq_file.name}")

stats_summary = {
    'total_rs_processed': stats['total_processed'],
    'websites': stats['websites'],
    'emails': stats['emails'],
    'rs_with_hours': len(stats['hours']['rs_with_hours']),
    'total_hours_entries': stats['hours']['total_entries'],
    'review_queue_count': len(stats['review_queue'])
}

(base_dir / "discovery_summary.json").write_text(json.dumps(stats_summary, indent=2), encoding='utf-8')
print("Summary:")
print(json.dumps(stats_summary, indent=2))
