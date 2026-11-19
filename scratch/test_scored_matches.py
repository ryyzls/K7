import sys
sys.path.insert(0, 'C:/K7/backend')
sys.path.insert(0, 'C:/K7')

from app.services import hospital_repo
from app.services.fuzzy_search import normalize, skor, skor_rs, rank, ALIAS_RS
from scratch.test_clean_and_resolve import clean_query

hospitals = hospital_repo.get_all_hospitals()

# Let's augment each hospital with auto-generated aliases
from collections import defaultdict
import re

PREFIX_WORDS = {
    'rs', 'rsu', 'rsud', 'rsup', 'rsia', 'rsk', 'rskb', 'rsau', 'uptd',
    'rumah', 'sakit', 'umum', 'daerah', 'pusat', 'khusus', 'pendidikan',
    'tingkat', 'tk', 'ii', 'iii', 'iv',
}
TITLE_WORDS = {'dr', 'dr.', 'prof', 'prof.', 'h', 'h.', 'hj', 'hj.', 'rm', 'r.m.', 'kolonel', 'letkol', 'al'}
CITY_WORDS = {'medan', 'binjai', 'tebing', 'tinggi', 'pematang', 'siantar', 'sibolga', 'tanjung', 'balai', 'gunungsitoli', 'sumut', 'sumatera', 'utara'}

AUTO_ALIASES = defaultdict(list)
for h in hospitals:
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', h['nama'].lower())
    tokens = clean.split()
    if not tokens:
        continue
    aliases = set()
    aliases.add(' '.join(tokens))
    
    i = 0
    while i < len(tokens) and tokens[i] in PREFIX_WORDS:
        i += 1
    while i < len(tokens) and tokens[i] in TITLE_WORDS:
        i += 1
    core = tokens[i:]
    if core:
        core_str = ' '.join(core)
        aliases.add(core_str)
        aliases.add('rs ' + core_str)
        if len(core) > 1 and core[-1] in CITY_WORDS:
            no_city = core[:-1]
            if len(no_city) > 1 and no_city[-1] in CITY_WORDS:
                no_city = no_city[:-1]
            if no_city:
                aliases.add(' '.join(no_city))
                aliases.add('rs ' + ' '.join(no_city))
    for a in list(aliases):
        aliases.add(a.replace(' ', ''))
    AUTO_ALIASES[h['id']] = list(aliases)

def custom_skor_rs(q: str, h: dict) -> float:
    # 1. Base score
    s = skor_rs(q, h)
    # 2. Check auto aliases
    for a in AUTO_ALIASES.get(h['id'], []):
        s = max(s, skor(q, a))
    return s

queries = [
    ("adam malik", "detail rs adam malik"),
    ("adam malik", "adam malik"),
    ("adam malik", "rsup ham"),
    ("adam malik", "rs adam malek"),
    ("pirngadi", "detail pirngadi"),
    ("pirngadi", "rs pringadi dimana"),
    ("siloam", "info siloam"),
    ("royal prima", "alamat royal prima"),
    ("hermina", "telp hermina"),
    ("elisabeth", "apa itu rs elisabeth"),
    ("hermina", "hermina"),
    ("martha friska", "martha friska"),
    ("metta medika", "rs metta medika"),
    ("xyzabc", "rs xyzabc")
]

for target, raw_q in queries:
    cleaned = clean_query(raw_q)
    scored = []
    for h in hospitals:
        s = custom_skor_rs(cleaned, h)
        if s >= 0.65:
            scored.append((s, h))
    scored.sort(key=lambda x: (-x[0], x[1]['nama']))
    
    if not scored:
        status = "NOT_FOUND"
        cand_str = "None"
    elif len(scored) == 1:
        status = "DOMINANT"
        cand_str = scored[0][1]['nama'] + f" ({scored[0][0]:.2f})"
    else:
        # Check if top score is dominant or disambiguate
        top_s = scored[0][0]
        second_s = scored[1][0]
        if top_s >= 0.85 and (top_s - second_s) >= 0.12:
            status = "DOMINANT"
            cand_str = scored[0][1]['nama'] + f" ({top_s:.2f})"
        elif top_s >= 0.75 and (top_s - second_s) < 0.12:
            status = "DISAMBIGUATE"
            cand_str = ", ".join(f"{h['nama']} ({s:.2f})" for s, h in scored[:3])
        else:
            status = "DOMINANT"
            cand_str = scored[0][1]['nama'] + f" ({top_s:.2f})"
            
    print(f"[{status}] '{raw_q}' (cleaned: '{cleaned}') -> {cand_str}")
