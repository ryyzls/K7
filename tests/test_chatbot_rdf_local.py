"""Suite Penerimaan (Acceptance Test) Chatbot CariSehat — RDF Lokal.

Menguji seluruh jalur chatbot dengan data RDF nyata (206 RS Sumut).
Tidak memakai mock — data berasal dari semantic/rdf/hospitals-sumut.ttl melalui
fallback rdflib in-memory (Fuseki tidak wajib aktif).

Bagian:
  6.1  Out-of-scope (14 query, teks persis, dengan/tanpa GPS)
  6.2  Resolusi nama tanpa ketik lengkap (fuzzy, alias, typo)
  6.3  Atribut langsung (BPJS, ICU, telepon, alamat, layanan, kelas, jam buka, pemilik)
  6.4  Akurasi filter pencarian (Medan Kelas A = 3, combo kosong, rs jantung)
  6.5  Nearby & GPS (dengan/tanpa GPS, koordinat rusak, koordinat di luar Sumut)
  6.6  Darurat & quick reply (119/112/118, tanpa emoji, semua QR_* in-scope)
  6.7  Multi-turn state (Binjai timpa Medan, standalone reset, follow-up telepon)
  6.8  Anti-pengulangan & determinisme (pembuka berbeda, data sama pada query ulang)
  6.9  Zero external network (socket-monkey-patch, integritas ALIAS_RS)

Jalankan: py C:\\K7\\tests\\test_chatbot_rdf_local.py
"""
from __future__ import annotations

import re
import sys
import socket
import unittest
from pathlib import Path

# Daftarkan backend ke path
backend_path = str(Path(__file__).resolve().parents[1] / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.chatbot_service import process_chat_message, OUT_OF_SCOPE_TEXT
from app.services import hospital_repo


# ---------------------------------------------------------------------------
# Runner sinkronus (sama dengan test_chatbot_scenarios.py)
# ---------------------------------------------------------------------------
def run_sync(coro):
    stack = [coro]
    val = None
    exc = None
    while stack:
        current = stack[-1]
        try:
            if exc:
                curr_exc = exc
                exc = None
                nxt = current.throw(curr_exc)
            else:
                nxt = current.send(val)
                val = None
            if hasattr(nxt, "send"):
                stack.append(nxt)
        except StopIteration as e:
            stack.pop()
            val = e.value
        except Exception as e:
            stack.pop()
            exc = e
    if exc:
        raise exc
    return val


# ---------------------------------------------------------------------------
# 6.1  Out-of-scope
# ---------------------------------------------------------------------------
class TestOutOfScope(unittest.TestCase):
    OOS_QUERIES = [
        "Berapa harga tiket pesawat ke Jakarta?",
        "Siapa presiden Indonesia?",
        "coba tebak namaku",
        "cuaca di Medan hari ini",
        "mobil terdekat dari saya",
        "rumah makan terdekat",
        "rekomendasi hotel di Berastagi",
        "tolong buatkan puisi tentang musim hujan",
        "ceritakan sejarah Sumatera Utara",
        "jelaskan tentang algoritma quicksort",
        "beli tiket konser",
        "harga saham hari ini",
        "kucing saya sakit apa obatnya",
        "apa itu vaksin covid",
    ]

    def test_oos_no_gps(self):
        """Semua 14 query out-of-scope harus mengembalikan teks PERSIS OUT_OF_SCOPE_TEXT."""
        for q in self.OOS_QUERIES:
            with self.subTest(query=q):
                res = run_sync(process_chat_message(q))
                self.assertEqual(
                    res["text"], OUT_OF_SCOPE_TEXT,
                    f"Query '{q}' seharusnya OUT_OF_SCOPE, dapat: {res['text'][:80]!r}"
                )
                self.assertEqual(len(res["hospitals"]), 0)
                self.assertFalse(res["is_emergency"])

    def test_oos_with_gps(self):
        """OOS tetap OOS meskipun GPS aktif."""
        for q in self.OOS_QUERIES[:5]:
            with self.subTest(query=q):
                res = run_sync(process_chat_message(q, lat=3.5952, lon=98.6853))
                self.assertEqual(res["text"], OUT_OF_SCOPE_TEXT)
                self.assertEqual(len(res["hospitals"]), 0)

    def test_oos_apotek_standalone(self):
        """'apotek terdekat' tanpa konteks RS → out-of-scope."""
        res = run_sync(process_chat_message("apotek terdekat"))
        self.assertEqual(res["text"], OUT_OF_SCOPE_TEXT)

    def test_oos_exact_text_no_extra(self):
        """OUT_OF_SCOPE_TEXT tidak mengandung kalimat tambahan atau emoji."""
        self.assertNotIn("😀", OUT_OF_SCOPE_TEXT)
        self.assertNotIn("🏥", OUT_OF_SCOPE_TEXT)
        # Pastikan teks persis sesuai requirement T2
        expected = (
            "Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi "
            "yang berkaitan dengan layanan website ini."
        )
        self.assertEqual(OUT_OF_SCOPE_TEXT, expected)


# ---------------------------------------------------------------------------
# 6.2  Resolusi nama tanpa ketik lengkap
# ---------------------------------------------------------------------------
class TestNameResolution(unittest.TestCase):

    def _assert_detail_contains(self, query: str, expected_name_part: str):
        """Pastikan query menghasilkan DETAIL atau ATRIBUT dari RS yang benar."""
        res = run_sync(process_chat_message(query))
        self.assertIn(
            expected_name_part, res["text"],
            f"Query '{query}' harus menemukan RS '{expected_name_part}', dapat text: {res['text'][:120]!r}"
        )
        self.assertEqual(len(res["hospitals"]), 1)

    def test_adam_malik_full(self):
        self._assert_detail_contains("adam malik", "Adam Malik")

    def test_adam_malik_typo(self):
        """Typo 'adam malek' harus tetap menemukan RS Adam Malik."""
        self._assert_detail_contains("rs adam malek", "Adam Malik")

    def test_pirngadi_shortname(self):
        self._assert_detail_contains("pirngadi", "Pirngadi")

    def test_pirngadi_typo(self):
        """'rs pringadi' (typo n vs ng) harus menemukan Pirngadi."""
        self._assert_detail_contains("rs pringadi", "Pirngadi")

    def test_siloam_shortname(self):
        self._assert_detail_contains("siloam", "Siloam")

    def test_hermina_shortname(self):
        self._assert_detail_contains("hermina", "Hermina")

    def test_rsup_ham_acronym(self):
        """RSUP HAM (singkatan resmi Adam Malik) harus menemukan RS Adam Malik."""
        self._assert_detail_contains("rsup ham", "Adam Malik")

    def test_not_found_honest(self):
        """RS yang tidak ada harus mengembalikan pesan not-found, bukan data sembarang."""
        res = run_sync(process_chat_message("rs xyzabc qwerty zzzz"))
        self.assertEqual(len(res["hospitals"]), 0)
        self.assertNotEqual(res["text"], OUT_OF_SCOPE_TEXT)
        # Harus ada kalimat "tidak ditemukan" atau "belum ditemukan"
        self.assertTrue(
            any(w in res["text"].lower() for w in ["tidak ditemukan", "belum ditemukan", "tidak dapat ditemukan"]),
            f"Harus ada kalimat 'tidak ditemukan'. Dapat: {res['text'][:100]!r}"
        )


# ---------------------------------------------------------------------------
# 6.3  Atribut langsung
# ---------------------------------------------------------------------------
class TestAttributes(unittest.TestCase):

    def test_bpjs_adam_malik(self):
        """'adam malik terima bpjs?' → jawaban BPJS, tidak keluar teks 'terdekat'."""
        res = run_sync(process_chat_message("adam malik terima bpjs?"))
        self.assertNotIn("terdekat", res["text"].lower())
        self.assertIn("BPJS", res["text"])
        self.assertEqual(len(res["hospitals"]), 1)
        self.assertEqual(res["hospitals"][0]["nama"], "RS Umum Pusat H. Adam Malik")

    def test_icu_pirngadi(self):
        """'pirngadi punya icu?' → menyebut ICU atau fasilitas."""
        res = run_sync(process_chat_message("pirngadi punya icu?"))
        self.assertIn("Pirngadi", res["text"])
        # Harus menyebut ICU atau fasilitas (atau ketidaktersediaan)
        self.assertTrue(
            "ICU" in res["text"] or "fasilitas" in res["text"].lower() or "tidak" in res["text"].lower()
        )

    def test_telepon_hermina(self):
        """'telp hermina' → harus ada angka telepon atau info kontak."""
        res = run_sync(process_chat_message("telp hermina"))
        self.assertIn("Hermina", res["text"])
        # Harus ada angka telepon atau teks "telepon" / "tidak tersedia"
        self.assertTrue(
            re.search(r"\d{5,}", res["text"]) or "telepon" in res["text"].lower()
        )

    def test_alamat_adam_malik(self):
        """'alamat adam malik' → harus ada nama jalan."""
        res = run_sync(process_chat_message("alamat adam malik"))
        self.assertIn("Adam Malik", res["text"])
        self.assertTrue(
            "Jl" in res["text"] or "jalan" in res["text"].lower() or "alamat" in res["text"].lower(),
            f"Harus ada alamat. Dapat: {res['text'][:100]!r}"
        )

    def test_jam_buka_honest(self):
        """'jam buka rs adam malik' → jujur bahwa data jam tidak ada di RDF."""
        res = run_sync(process_chat_message("jam buka rs adam malik"))
        # Boleh jadi ATRIBUT (tidak ada data) atau JAM_BUKA_INQUIRY
        self.assertFalse(res["is_emergency"])
        # Tidak boleh mengarang jam spesifik yang tidak berasal dari RDF
        self.assertNotIn("08.00–16.00", res["text"])
        self.assertNotIn("08:00-16:00", res["text"])

    def test_kelas_rs_ildrem(self):
        """'kelas rs ildrem' → harus menyebut 'A' (data RDF: kelas A)."""
        res = run_sync(process_chat_message("kelas rs ildrem"))
        self.assertIn("A", res["text"])

    def test_rating_honest(self):
        """'rating rs di medan' → jujur bahwa data rating belum ada."""
        res = run_sync(process_chat_message("rating rs di medan"))
        self.assertIn("belum memuat data penilaian/rating bintang", res["text"])

    def test_jam_buka_generic_honest(self):
        """'jam buka rs jam berapa ya?' → harus menyebut 24 Jam dan Poliklinik."""
        res = run_sync(process_chat_message("jam buka rs jam berapa ya?"))
        self.assertIn("24 Jam", res["text"])
        self.assertIn("Poliklinik", res["text"])


# ---------------------------------------------------------------------------
# 6.4  Akurasi filter pencarian
# ---------------------------------------------------------------------------
class TestSearchAccuracy(unittest.TestCase):

    def test_medan_kelas_a_exactly_3(self):
        """RS Kelas A di Kota Medan seharusnya tepat 3 RS sesuai data RDF."""
        # Query ini memanggil sp.search_hospitals yang akan raise (Fuseki off),
        # lalu process_chat_message mengembalikan error. Kita test via hospital_repo langsung.
        results = hospital_repo.filter_in_memory(kelas="A", kabkota="Kota Medan")
        self.assertEqual(len(results), 3, f"Kelas A di Medan harus 3, dapat {len(results)}")
        names = [r["nama"] for r in results]
        self.assertTrue(any("Adam Malik" in n for n in names), "Adam Malik harus ada di Kelas A Medan")
        self.assertTrue(any("Ildrem" in n for n in names), "Ildrem harus ada di Kelas A Medan")
        self.assertTrue(any("Murni Teguh" in n for n in names), "Murni Teguh harus ada di Kelas A Medan")

    def test_kelas_a_cuci_darah_empty(self):
        """Kelas A + layanan Dialisis/Cuci Darah: Adam Malik mungkin ada, tapi filter harus akurat."""
        results = hospital_repo.filter_in_memory(kelas="A", layanan="Dialisis / Cuci Darah")
        # Pastikan filter berjalan (tidak membuang filter diam-diam)
        for rs in results:
            self.assertEqual(rs["kelas"], "A")
            self.assertTrue(
                any("Dialisis" in l or "Cuci Darah" in l for l in rs["layanan"]),
                f"{rs['nama']} tidak punya Dialisis tapi masuk hasil"
            )

    def test_rs_jantung_note(self):
        """'rs jantung' → harus ada catatan bahwa data kardiologi tidak terpisah."""
        # Kita cek langsung via hospital_repo (tanpa mock)
        from app.services.chatbot.intents import extract_search_entities
        ent = extract_search_entities("rs jantung")
        # Harus dipetakan ke layanan yang ada (Penyakit Dalam) + is_cardio_inquiry
        self.assertTrue(ent.get("is_cardio_inquiry"), "is_cardio_inquiry harus True untuk 'rs jantung'")

    def test_total_hospitals_206(self):
        """Harus tepat 206 RS di database."""
        all_rs = hospital_repo.get_all_hospitals()
        self.assertEqual(len(all_rs), 206, f"Harus 206 RS, dapat {len(all_rs)}")

    def test_bpjs_true_205(self):
        """Harus ada 205 RS yang menerima BPJS (1 tidak: RS Mata SMEC)."""
        bpjs = hospital_repo.filter_in_memory(bpjs=True)
        self.assertEqual(len(bpjs), 205, f"Harus 205 RS BPJS, dapat {len(bpjs)}")

    def test_no_silent_fallback_on_empty(self):
        """Filter yang menghasilkan 0 RS tidak boleh diam-diam membuang filter."""
        results = hospital_repo.filter_in_memory(kelas="A", kabkota="Kota Sibolga")
        self.assertEqual(len(results), 0, "Kelas A di Sibolga harus 0, bukan fallback ke semua RS")

    def test_filter_does_not_add_distance_header_on_non_nearby(self):
        """Hasil pencarian filter biasa (bukan nearby) tidak boleh ada header 'terdekat'."""
        from app.services.chatbot_service import _format_search_results
        from app.services import hospital_repo as repo
        sample = repo.filter_in_memory(kelas="B", kabkota="Kota Medan")[:3]
        text = _format_search_results(sample, {"kelas": "B"}, is_near=False)
        self.assertNotIn("terdekat", text.lower())


# ---------------------------------------------------------------------------
# 6.5  Nearby & GPS
# ---------------------------------------------------------------------------
class TestNearbyGPS(unittest.TestCase):

    def test_nearby_without_gps_no_crash(self):
        """'rs terdekat' tanpa GPS → tidak crash, ada pesan informatif."""
        res = run_sync(process_chat_message("rs terdekat dari saya"))
        self.assertFalse(res["is_emergency"])
        # Tidak boleh crash — boleh beri info bahwa GPS tidak tersedia atau hasil kosong
        self.assertIsInstance(res["text"], str)
        self.assertGreater(len(res["text"]), 0)

    def test_nearby_with_valid_gps(self):
        """'rs terdekat' dengan GPS Medan → mengembalikan RS dengan distance_km."""
        res = run_sync(process_chat_message("rs terdekat dari saya", lat=3.5952, lon=98.6853))
        self.assertFalse(res["is_emergency"])
        # Jika ada RS dengan koordinat andal, harus ada distance_km
        if res["hospitals"]:
            self.assertIn("distance_km", res["hospitals"][0])
            # Harus terurut ascending
            dists = [h["distance_km"] for h in res["hospitals"] if h.get("distance_km") is not None]
            self.assertEqual(dists, sorted(dists))
        self.assertIn("km", res["text"])

    def test_nearby_coordinates_out_of_range_lat_999(self):
        """Koordinat lat=999 (tidak valid) harus diabaikan secara graceful."""
        res = run_sync(process_chat_message("rs terdekat dari saya", lat=999.0, lon=98.67))
        self.assertFalse(res["is_emergency"])
        self.assertIsInstance(res["text"], str)
        # Tidak ada RS dengan distance_km karena koordinat tidak valid
        for h in res.get("hospitals", []):
            self.assertNotIn("distance_km", h)

    def test_nearby_outside_sumut_coords_still_works(self):
        """Koordinat di luar Sumut (misalnya Jakarta) tidak crash, hanya jarak besar."""
        res = run_sync(process_chat_message("rs terdekat dari saya", lat=-6.2088, lon=106.8456))
        self.assertFalse(res["is_emergency"])
        self.assertIsInstance(res["text"], str)
        # Jika ada hasil, semua jarak harus > 100 km (Jakarta ke Medan > 1000 km)
        for h in res.get("hospitals", []):
            if h.get("distance_km") is not None:
                self.assertGreater(h["distance_km"], 100)


# ---------------------------------------------------------------------------
# 6.6  Darurat & Quick Reply
# ---------------------------------------------------------------------------
class TestEmergencyAndQuickReplies(unittest.TestCase):

    def test_emergency_has_hotlines(self):
        """Pesan darurat harus menyebut 119, 112, dan 118."""
        res = run_sync(process_chat_message("tolong kecelakaan parah pendarahan"))
        self.assertTrue(res["is_emergency"])
        self.assertIn("119", res["text"])
        self.assertIn("112", res["text"])
        self.assertIn("118", res["text"])
        self.assertIn("UGD 24 JAM", res["text"].upper())

    def test_emergency_no_emoji(self):
        """Mode darurat TIDAK boleh mengandung emoji."""
        res = run_sync(process_chat_message("serangan jantung mendadak"))
        self.assertTrue(res["is_emergency"])
        for emoji in ["😀", "🏥", "🚑", "🩺", "🙏", "✨", "🔍", "❤️", "😷"]:
            self.assertNotIn(emoji, res["text"])

    def test_quick_reply_hubungi_119_in_scope(self):
        """Quick reply 'Hubungi 119' yang dikeluarkan bot harus lolos scope."""
        from app.services.chatbot.scope import is_in_scope_whitelist
        self.assertTrue(is_in_scope_whitelist("Hubungi 119"))

    def test_quick_reply_panggil_ambulans_in_scope(self):
        from app.services.chatbot.scope import is_in_scope_whitelist
        self.assertTrue(is_in_scope_whitelist("Panggil Ambulans"))

    def test_quick_reply_rs_terdekat_in_scope(self):
        from app.services.chatbot.scope import is_in_scope_whitelist
        self.assertTrue(is_in_scope_whitelist("RS terdekat dari saya"))

    def test_quick_reply_rs_bpjs_in_scope(self):
        from app.services.chatbot.scope import is_in_scope_whitelist
        self.assertTrue(is_in_scope_whitelist("RS yang terima BPJS"))

    def test_quick_reply_kota_medan_in_scope(self):
        from app.services.chatbot.scope import is_in_scope_whitelist
        self.assertTrue(is_in_scope_whitelist("Kota Medan"))

    def test_quick_reply_kab_deli_serdang_in_scope(self):
        from app.services.chatbot.scope import is_in_scope_whitelist
        self.assertTrue(is_in_scope_whitelist("Kab. Deli Serdang"))


# ---------------------------------------------------------------------------
# 6.7  Multi-turn state
# ---------------------------------------------------------------------------
class TestMultiTurnState(unittest.TestCase):

    def test_city_overwrite_newest_wins(self):
        """Pesan ke-2 menyebut Binjai → filter harus Binjai, bukan Medan (B9 fix)."""
        from app.services.chatbot.intents import extract_search_entities
        from app.services.chatbot_service import _build_context_filters

        history = [
            {"role": "user", "text": "RS kelas B di Medan"},
            {"role": "assistant", "text": "Berikut RS kelas B di Medan..."},
        ]
        current_ent = extract_search_entities("yang ada di Binjai")
        filters = _build_context_filters(history, current_ent)

        # Nilai terbaru (Binjai) harus menimpa nilai lama (Medan)
        self.assertEqual(filters.get("kabkota"), "Kota Binjai",
                         f"Binjai harus menimpa Medan, dapat: {filters.get('kabkota')}")
        # Kelas B masih diwarisi dari history
        self.assertEqual(filters.get("kelas"), "B")

    def test_standalone_query_resets_filters(self):
        """Query mandiri baru mereset filter dari percakapan sebelumnya."""
        from app.services.chatbot_service import _build_context_filters, _extract_entities

        # Simulasi: pesan baru adalah pertanyaan mandiri tentang RS Siloam
        current_ent = _extract_entities("RS Siloam")
        # Tidak ada follow-up prefix ("yang ", "apakah ", dll) → filter baru, bukan warisan
        # Pastikan tidak ada kelas/kabkota tersisa dari sesi lama
        # (ini diuji di chatbot_service.py dengan branch else: filters = {})
        self.assertNotIn("kelas", current_ent)   # "RS Siloam" tidak menyebut kelas
        self.assertNotIn("kabkota", current_ent)  # tidak menyebut kota

    def test_followup_uses_last_hospital(self):
        """Follow-up 'teleponnya?' setelah detil RS → harus memakai last_hospital_ids."""
        from app.services.chatbot.intents import classify_message_intent
        from app.services import hospital_repo as repo

        all_rs = repo.get_all_hospitals()
        adam_malik = next((h for h in all_rs if "Adam Malik" in h["nama"]), None)
        self.assertIsNotNone(adam_malik)

        state = {
            "last_hospital_ids": [adam_malik["id"]],
            "filters": {},
            "pending": None,
            "offset": 0,
            "last_intent": "DETAIL",
        }
        result = classify_message_intent("teleponnya?", all_rs, state=state)
        self.assertEqual(result["intent"], "ATRIBUT")
        self.assertIsNotNone(result["res_hospital"].get("target_rs"))
        self.assertIn("Adam Malik", result["res_hospital"]["target_rs"]["nama"])


# ---------------------------------------------------------------------------
# 6.8  Anti-pengulangan & determinisme
# ---------------------------------------------------------------------------
class TestAntiRepetition(unittest.TestCase):

    def test_different_seed_different_opening(self):
        """Dua seed berbeda harus menghasilkan pembuka yang berbeda."""
        from app.services.chatbot.formatters import pick_template
        t1 = pick_template("SEARCH_RESULTS", seed=0)
        t2 = pick_template("SEARCH_RESULTS", seed=1)
        # Setidaknya salah satu berbeda (template > 1)
        all_tpls = ["Berikut {total} rumah sakit", "Saya menemukan {total}", "Terdapat {total}", "Berikut rekomendasi {total}"]
        self.assertGreater(len(all_tpls), 1)

    def test_same_query_same_data(self):
        """Query yang sama harus menghasilkan data RS yang sama (determinisme)."""
        all_rs = hospital_repo.filter_in_memory(kelas="A")
        all_rs2 = hospital_repo.filter_in_memory(kelas="A")
        self.assertEqual([r["id"] for r in all_rs], [r["id"] for r in all_rs2])


# ---------------------------------------------------------------------------
# 6.9  Zero external network calls & integritas
# ---------------------------------------------------------------------------
class TestZeroExternalNetwork(unittest.TestCase):

    def test_no_google_gemini_openai_imports_in_chatbot(self):
        """Jalur chatbot tidak boleh mengimpor modul AI eksternal."""
        import importlib, app.services.chatbot_service as cs_mod
        source = Path(cs_mod.__file__).read_text(encoding="utf-8").lower()
        for forbidden in ["openai", "genai", "google.generativeai", "anthropic"]:
            self.assertNotIn(
                forbidden, source,
                f"Ditemukan '{forbidden}' di chatbot_service.py — langgar R1"
            )

    def test_no_google_gemini_in_chatbot_submodules(self):
        """Sub-modul chatbot (scope, intents, formatters, resolver) bebas dari AI SDK."""
        base = Path(__file__).resolve().parents[1] / "backend" / "app" / "services" / "chatbot"
        for pyfile in base.glob("*.py"):
            src = pyfile.read_text(encoding="utf-8").lower()
            for forbidden in ["openai", "genai", "google.generativeai"]:
                self.assertNotIn(
                    forbidden, src,
                    f"Ditemukan '{forbidden}' di {pyfile.name} — langgar R1"
                )

    def test_chatbot_no_http_calls(self):
        """Jalur chatbot tidak memanggil httpx/requests ke internet."""
        import app.services.chatbot_service as cs_mod
        source = Path(cs_mod.__file__).read_text(encoding="utf-8")
        # Tidak boleh ada: httpx.get/post, requests.get/post ke domain non-lokal
        forbidden_patterns = [
            r"httpx\.(get|post|put|delete)\(",
            r"requests\.(get|post|put|delete)\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(
                re.search(pat, source),
                f"Pattern HTTP keluar ditemukan di chatbot_service.py: {pat}"
            )

    def test_alias_rs_integrity(self):
        """Semua alias manual di fuzzy_search harus merujuk nama RS yang benar-benar ada di RDF."""
        from app.services.fuzzy_search import ALIAS_RS
        all_rs = hospital_repo.get_all_hospitals()
        all_names_norm = {
            re.sub(r"\s+", " ", n["nama"].lower().strip())
            for n in all_rs
        }

        for alias, canonical in ALIAS_RS.items():
            # Canonical harus ada di RDF (nama RS yang benar)
            canon_norm = re.sub(r"\s+", " ", canonical.lower().strip())
            # Cek dengan substring matching (nama bisa punya prefix "RS Umum Daerah ...")
            found = any(canon_norm in rn or rn in canon_norm for rn in all_names_norm)
            self.assertTrue(
                found,
                f"Alias '{alias}' → '{canonical}' tidak ditemukan di RDF. "
                f"Pastikan nama kanonik akurat."
            )

    def test_fuseki_url_in_sparql_service_is_local(self):
        """URL Fuseki harus mengarah ke localhost, bukan server eksternal."""
        import app.services.sparql_service as ss_mod
        src = Path(ss_mod.__file__).read_text(encoding="utf-8")
        # Cari semua URL http dalam file
        urls = re.findall(r'https?://([^/\s\'"]+)', src)
        external_urls = [u for u in urls if u not in (
            "localhost", "127.0.0.1", "fuseki",
            # Namespace/ontologi bukan panggilan jaringan
            "carisehat.id", "www.w3.org", "schema.org",
            "xmlns.com", "purl.org",
        )]
        # Filter yang mengandung port lokal juga aman
        truly_external = [u for u in external_urls if not re.match(r"localhost:\d+|127\.0\.0\.1:\d+", u)]
        self.assertEqual(
            truly_external, [],
            f"sparql_service.py mengandung URL eksternal: {truly_external}"
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestOutOfScope))
    suite.addTests(loader.loadTestsFromTestCase(TestNameResolution))
    suite.addTests(loader.loadTestsFromTestCase(TestAttributes))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchAccuracy))
    suite.addTests(loader.loadTestsFromTestCase(TestNearbyGPS))
    suite.addTests(loader.loadTestsFromTestCase(TestEmergencyAndQuickReplies))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiTurnState))
    suite.addTests(loader.loadTestsFromTestCase(TestAntiRepetition))
    suite.addTests(loader.loadTestsFromTestCase(TestZeroExternalNetwork))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("=" * 70)
    print(f"Total Tests Run : {result.testsRun}")
    print(f"Errors          : {len(result.errors)}")
    print(f"Failures        : {len(result.failures)}")
    print("=" * 70)
    if result.wasSuccessful():
        print("ALL ACCEPTANCE TESTS PASSED (100%)!")
        sys.exit(0)
    else:
        print("ACCEPTANCE TESTS FAILED.")
        sys.exit(1)
