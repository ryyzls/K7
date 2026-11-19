import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.chatbot_service import (
    _extract_entities, _classify_intent, _build_context_filters, _is_in_scope
)

tests = [
    # (query, history, expected_intent)
    ('coba tebak namaku', [], 'OUT_OF_SCOPE'),
    ('cuaca di medan', [], 'OUT_OF_SCOPE'),
    ('rumah makan terdekat', [], 'OUT_OF_SCOPE'),
    ('kucing saya sakit', [], 'OUT_OF_SCOPE'),
    ('siapa presiden indonesia', [], 'OUT_OF_SCOPE'),
    ('apakah kamu tau dimana lokasi rs adam malik', [], 'DETAIL'),
    ('rs adam malik itu dimana', [], 'DETAIL'),
    ('dimana rs pirngadi berada', [], 'DETAIL'),
    ('lokasi rs herna', [], 'DETAIL'),
    ('rs terdekat dari saya', [], 'SEARCH_NEARBY'),
    ('rs kelas b di medan', [], 'SEARCH_FILTER'),
    ('rs yang terima bpjs di binjai', [], 'SEARCH_FILTER'),
    ('rs di medan', [], 'SEARCH_FILTER'),
    ('rs kelas a', [], 'SEARCH_FILTER'),
    ('halo', [], 'GREETING'),
    ('serangan jantung', [], 'EMERGENCY'),
    ('kecelakaan', [], 'EMERGENCY'),
]

print('=== Intent Classification Test ===')
all_pass = True
for query, hist, expected in tests:
    tl = query.lower()
    ent = _extract_entities(tl, hist)
    ctx = _build_context_filters(hist, ent)
    intent = _classify_intent(tl, ent, hist)
    status = 'PASS' if intent == expected else 'FAIL'
    if status == 'FAIL':
        all_pass = False
    print(f'  [{status}] "{query}" -> {intent} (expected: {expected})')
    if status == 'FAIL':
        print(f'         entities={ent}')

print()

# Test: multi-turn tidak mewarisi is_near
print('=== Multi-turn is_near isolation test ===')
history_with_near = [
    {'role': 'user', 'text': 'rs terdekat dari saya'},
    {'role': 'assistant', 'text': 'Ini RS terdekat...'},
]
query2 = 'rs kelas a di medan'
tl2 = query2.lower()
ent2 = _extract_entities(tl2, history_with_near)
ctx2 = _build_context_filters(history_with_near, ent2)
intent2 = _classify_intent(tl2, ent2, history_with_near)
expected2 = 'SEARCH_FILTER'
ok2 = intent2 == expected2 and not ctx2.get('is_near')
status2 = 'PASS' if ok2 else 'FAIL'
print(f'  [{status2}] After nearby query -> "{query2}" = {intent2}, is_near={ctx2.get("is_near")} (expected: {expected2}, is_near=None)')
if not ok2:
    all_pass = False

# Test: multi-turn follow-up yang sah (yang terima bpjs setelah RS di Medan)
print()
print('=== Multi-turn follow-up test ===')
history_rs_medan = [
    {'role': 'user', 'text': 'rs di medan'},
    {'role': 'assistant', 'text': 'Ini beberapa RS di Medan...'},
]
query3 = 'yang terima bpjs?'
tl3 = query3.lower()
ent3 = _extract_entities(tl3, history_rs_medan)
ctx3 = _build_context_filters(history_rs_medan, ent3)
intent3 = _classify_intent(tl3, ent3, history_rs_medan)
status3 = 'PASS' if intent3 in ('SEARCH_FILTER', 'CLARIFICATION_ANSWER') else 'FAIL'
print(f'  [{status3}] "{query3}" after RS Medan -> {intent3}, bpjs={ctx3.get("bpjs")}, kabkota={ctx3.get("kabkota")}')
if status3 == 'FAIL':
    all_pass = False

print()
print('=== RESULT:', 'ALL PASSED' if all_pass else 'SOME FAILED', '===')
