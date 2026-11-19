import re
import sys
sys.path.insert(0, 'C:/K7/backend')

from app.services import hospital_repo
from app.services.fuzzy_search import normalize, skor, skor_rs, ALIAS_RS

# Words to strip
STRIP_PATTERNS = [
    r"\bapa\s+itu\b", r"\bapakah\s+kamu\s+tau\b", r"\bapakah\s+tahu\b", r"\bapakah\b",
    r"\btolong\b", r"\bbantu\b", r"\bcari\b", r"\blihat\b", r"\btampilkan\b",
    r"\bdetail\b", r"\binfo\b", r"\binformasi\b", r"\btentang\b", r"\bprofil\b",
    r"\balamat(?:nya)?\b", r"\blokasi(?:nya)?\b", r"\bdimana(?:kah)?\b", r"\bdi\s+mana(?:kah)?\b",
    r"\bletak(?:nya)?\b", r"\bposisi(?:nya)?\b", r"\bberada\b",
    r"\bnomor\s+telepon\b", r"\bno\s+telp\b", r"\bno\s+telepon\b", r"\bno\s+hp\b",
    r"\btelepon(?:nya)?\b", r"\btelp(?:nya)?\b", r"\bkontak(?:nya)?\b", r"\bhubungi\b",
    r"\bterima\s+bpjs\b", r"\bbisa\s+bpjs\b", r"\bbpjs\b",
    r"\bjam\s+buka\b", r"\bjam\s+operasional\b", r"\bjadwal\s+dokter\b", r"\bjadwal\b", r"\bbuka\s+jam\s+berapa\b",
    r"\bpunya\s+icu\b", r"\bada\s+icu\b", r"\bicu\b",
    r"\blayanan\s+apa\s+saja\b", r"\blayanan(?:nya)?\b", r"\bpoli(?:nya)?\b", r"\bspesialis(?:nya)?\b",
    r"\bfasilitas(?:nya)?\b", r"\bjenis(?:nya)?\b", r"\bkelas(?:nya)?\b", r"\btipe(?:nya)?\b",
    r"\bpemilik(?:nya)?\b", r"\bmilik(?:nya)?\b",
    r"\bpunya\b", r"\bada\b", r"\bapa\b", r"\bsaja\b", r"\bdi\b", r"\bdari\b",
    r"\bitu\b", r"\bini\b", r"\bya\b", r"\byah\b", r"\bdong\b", r"\bsih\b", r"\bkan\b",
    r"\brumah\s+sakit\s+umum\s+daerah\b", r"\brumah\s+sakit\s+umum\s+pusat\b", r"\brumah\s+sakit\s+umum\b",
    r"\brumah\s+sakit\b", r"\brsud\b", r"\brsup\b", r"\brsu\b", r"\brsia\b", r"\brsk\b", r"\brsj\b", r"\brsau\b",
    r"\brs\b",
]

def clean_query(text: str) -> str:
    t = normalize(text)
    for p in STRIP_PATTERNS:
        t = re.sub(p, " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

hospitals = hospital_repo.get_all_hospitals()
print(f"Loaded {len(hospitals)} hospitals")

queries = [
    "detail rs adam malik", "adam malik", "rsup ham", "rs adam malek",
    "detail pirngadi", "rs pringadi dimana", "info siloam", "alamat royal prima",
    "telp hermina", "apa itu rs elisabeth", "hermina", "martha friska",
    "rs metta medika", "rs xyzabc", "adam malik terima bpjs?", "pirngadi punya icu?",
    "telp adam malik", "alamat adam malik", "layanan apa saja di rs elisabeth",
    "jenis rs ildrem", "jam buka rs adam malik"
]

for q in queries:
    cleaned = clean_query(q)
    print(f"'{q}' -> cleaned: '{cleaned}'")
