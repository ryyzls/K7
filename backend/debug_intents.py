import sys
sys.path.insert(0, r"C:\K7\backend")
from app.services.chatbot.intents import classify_message_intent, extract_search_entities
from app.services import hospital_repo

all_rs = hospital_repo.get_all_hospitals()
print(f"Loaded {len(all_rs)} hospitals")

# Test 01: 'RS kelas B di Medan'
r = classify_message_intent('RS kelas B di Medan', all_rs)
print(f"\nTest01 'RS kelas B di Medan':")
print(f"  intent: {r['intent']}")
print(f"  entities: {r['entities']}")

# Test 04: 'anak saya demam tinggi butuh dokter anak'
r2 = classify_message_intent('anak saya demam tinggi butuh dokter anak', all_rs)
print(f"\nTest04 'anak saya demam tinggi butuh dokter anak':")
print(f"  intent: {r2['intent']}")
print(f"  entities: {r2['entities']}")

# Test 05: 'rmh skt kls a di mddan'
r5 = classify_message_intent('rmh skt kls a di mddan', all_rs)
print(f"\nTest05 'rmh skt kls a di mddan':")
print(f"  intent: {r5['intent']}")
print(f"  entities: {r5['entities']}")

# Test 08: 'Cari rumah sakit'
r3 = classify_message_intent('Cari rumah sakit', all_rs)
print(f"\nTest08 'Cari rumah sakit':")
print(f"  intent: {r3['intent']}")
print(f"  entities: {r3['entities']}")

# Test 09: 'RS kelas A di Kota Sibolga' (empty result expected)
r9 = classify_message_intent('RS kelas A di Kota Sibolga', all_rs)
print(f"\nTest09 'RS kelas A di Kota Sibolga':")
print(f"  intent: {r9['intent']}")
print(f"  entities: {r9['entities']}")

# Test 12: rating
r4 = classify_message_intent('Apakah ada rating atau ulasan RS di Medan?', all_rs)
print(f"\nTest12 'Apakah ada rating atau ulasan RS di Medan?':")
print(f"  intent: {r4['intent']}")

# Test 13: jam buka
r6 = classify_message_intent('Jam buka RS jam berapa ya?', all_rs)
print(f"\nTest13 'Jam buka RS jam berapa ya?':")
print(f"  intent: {r6['intent']}")
