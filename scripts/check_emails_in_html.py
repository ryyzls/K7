import re
from pathlib import Path

html_dir = Path('data/enrichment/tahap2/hasil_profil_sirs_206/html_cache')
email_re = re.compile(r'<b>E-?mail:?</b>\s*<a[^>]*>(.*?)</a>|mailto:([^\s"\'<>]+)|([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', re.IGNORECASE)

found_emails = {}
for html_file in html_dir.glob('*.html'):
    content = html_file.read_text(encoding='utf-8', errors='ignore')
    matches = email_re.findall(content)
    cleaned = []
    for m in matches:
        for group in m:
            if group and '@' in group and not group.endswith('.png') and not group.endswith('.jpg') and 'example' not in group:
                cleaned.append(group.strip())
    if cleaned:
        found_emails[html_file.stem] = list(set(cleaned))

print(f"Found emails in {len(found_emails)} HTML cache files:")
for k, v in list(found_emails.items())[:10]:
    print(f"  Kode {k}: {v}")
