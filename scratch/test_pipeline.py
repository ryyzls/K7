import sys
sys.path.insert(0, 'C:/K7/backend')

from app.services import hospital_repo
from app.services.chatbot.intents import classify_message_intent, extract_search_entities
from app.services.chatbot.formatters import (
    format_detail_rs, format_attribute_rs, format_list_filter,
    format_nearby_results, format_disambiguation, format_not_found_hospital,
    format_emergency, format_compare_table, format_out_of_scope
)

hospitals = hospital_repo.get_all_hospitals()
print(f"Loaded {len(hospitals)} hospitals in test pipeline.")

test_queries = [
    # (query, lat, lon, state, expected_intent)
    ("cuaca hari ini", None, None, {}, "OUT_OF_SCOPE"),
    ("cuaca di medan", None, None, {}, "OUT_OF_SCOPE"),
    ("ada matahari", None, None, {}, "OUT_OF_SCOPE"),
    ("apotek terdekat", None, None, {}, "OUT_OF_SCOPE"),
    ("detail rs adam malik", None, None, {}, "DETAIL"),
    ("adam malik", None, None, {}, "DETAIL"),
    ("rs adam malek", None, None, {}, "DETAIL"),
    ("telp hermina", None, None, {}, "ATRIBUT"),
    ("adam malik terima bpjs?", None, None, {}, "ATRIBUT"),
    ("pirngadi punya icu?", None, None, {}, "ATRIBUT"),
    ("jam buka rs adam malik", None, None, {}, "ATRIBUT"),
    ("martha friska", None, None, {}, "DISAMBIGUASI"),
    ("rs metta medika", None, None, {}, "DISAMBIGUASI"),
    ("rs xyzabc", None, None, {}, "NOT_FOUND"),
    ("serangan jantung", None, None, {}, "EMERGENCY"),
    ("Hubungi 119", None, None, {}, "EMERGENCY"),
    ("Panggil Ambulans", None, None, {}, "EMERGENCY"),
    ("rs kelas a di medan", None, None, {}, "SEARCH_FILTER"),
    ("rs terdekat dari saya", 3.5952, 98.6722, {}, "SEARCH_NEARBY"),
]

for q, lat, lon, st, exp in test_queries:
    classified = classify_message_intent(q, hospitals, state=st)
    intent = classified["intent"]
    ok = intent == exp
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] '{q}' -> intent: {intent} (expected: {exp})")
