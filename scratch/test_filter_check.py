import sys
sys.path.insert(0, 'C:/K7/backend')

from app.services.chatbot.models import NEARBY_KEYWORDS, KABKOTA_MAP
from app.services.chatbot.resolver import clean_hospital_query

FILTER_ONLY_WORDS = {
    "a", "b", "c", "d", "umum", "khusus", "terdekat", "dekat", "sekitar",
    "semua", "daftar", "seluruh", "semua rs", "cari rs"
}
for k in KABKOTA_MAP:
    FILTER_ONLY_WORDS.add(k)
    for c in ["a", "b", "c", "d"]:
        FILTER_ONLY_WORDS.add(f"{c} {k}")

def is_pure_filter_query(cleaned: str) -> bool:
    c = cleaned.strip().lower()
    return c in FILTER_ONLY_WORDS or len(c) <= 1

print("is 'a medan' pure filter?", is_pure_filter_query("a medan"))
print("is 'terdekat' pure filter?", is_pure_filter_query("terdekat"))
print("is 'adam malik' pure filter?", is_pure_filter_query("adam malik"))
