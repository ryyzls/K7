"""Suite Uji Chatbot Semantik CariSehat (14 Skenario Pengujian).
Memverifikasi fungsionalitas NLP lokal, SPARQL template, multi-turn, mode darurat, typo,
explainability, perbandingan, dan out-of-scope handler tanpa API eksternal.

Jalankan langsung: py C:\\K7\\tests\\test_chatbot_scenarios.py
"""
import sys
import unittest
from pathlib import Path

# Daftarkan backend ke path
backend_path = str(Path(__file__).resolve().parents[1] / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services import chatbot_service
from app.services.chatbot_service import process_chat_message, OUT_OF_SCOPE_TEXT

# --- Runner Sinkronus untuk Coroutine (Sandbox-Safe) ---
def run_sync(coro):
    """Menjalankan coroutine secara deterministik tanpa membuka socket Windows."""
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


class AsyncFuncMock:
    """Mock fungsi async tanpa ketergantungan pada ProactorEventLoop Windows."""
    def __init__(self, return_value=None, side_effect=None):
        self.return_value = return_value
        self.side_effect = side_effect
        self.calls = []
        self.call_args = None

    async def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        self.call_args = (args, kwargs)
        if self.side_effect:
            if callable(self.side_effect):
                res = self.side_effect(*args, **kwargs)
                if hasattr(res, "__await__") or hasattr(res, "send"):
                    return await res
                return res
            raise self.side_effect
        return self.return_value


# Mock Data Rumah Sakit
MOCK_HOSPITALS = [
    {
        "id": "rs-umum-pusat-h-adam-malik",
        "uri": "http://carisehat.id/rs/rs-umum-pusat-h-adam-malik",
        "nama": "RS Umum Pusat H. Adam Malik",
        "jenis": "Umum",
        "kelas": "A",
        "alamat": "Jl. Bunga Lau No.17, Medan Tuntungan",
        "kabkota": "Kota Medan",
        "telepon": "061-8360143",
        "website": "http://rsupham.co.id",
        "bpjs": True,
        "lat": 3.5186,
        "lon": 98.6083,
        "layanan": ["UGD 24 Jam", "Penyakit Dalam", "Bedah", "Kesehatan Anak", "Dialisis / Cuci Darah"],
        "fasilitas": ["ICU / ICCU / NICU", "Ambulans", "Kamar Operasi"],
        "foto": "https://example.com/adammalik.jpg",
    },
    {
        "id": "rs-umum-daerah-dr-pirngadi",
        "uri": "http://carisehat.id/rs/rs-umum-daerah-dr-pirngadi",
        "nama": "RS Umum Daerah Dr. Pirngadi",
        "jenis": "Umum",
        "kelas": "B",
        "alamat": "Jl. Prof. HM. Yamin SH No.47, Medan",
        "kabkota": "Kota Medan",
        "telepon": "061-4536022",
        "website": "http://rsudpirngadi.pemkomedan.go.id",
        "bpjs": True,
        "lat": 3.5952,
        "lon": 98.6853,
        "layanan": ["UGD 24 Jam", "Penyakit Dalam", "Bedah", "Kesehatan Anak", "Gigi dan Mulut"],
        "fasilitas": ["ICU", "Ambulans", "Kamar Operasi"],
        "foto": "https://example.com/pirngadi.jpg",
    },
    {
        "id": "rs-columbia-asia-medan",
        "uri": "http://carisehat.id/rs/rs-columbia-asia-medan",
        "nama": "RS Columbia Asia Medan",
        "jenis": "Umum",
        "kelas": "B",
        "alamat": "Jl. Listrik No.2A, Medan",
        "kabkota": "Kota Medan",
        "telepon": "061-4566368",
        "website": "http://columbiaasia.com",
        "bpjs": False,
        "lat": 3.5898,
        "lon": 98.6755,
        "layanan": ["UGD 24 Jam", "Penyakit Dalam", "Bedah", "Kesehatan Anak"],
        "fasilitas": ["ICU", "Ambulans", "Kamar Operasi"],
        "foto": "https://example.com/columbia.jpg",
    },
]


class ChatbotScenariosTest(unittest.TestCase):
    def setUp(self):
        # Simpan method asli
        self.orig_search_hospitals = chatbot_service.sp.search_hospitals
        self.orig_search_emergency = chatbot_service.sp.search_emergency_hospitals

    def tearDown(self):
        # Kembalikan method asli
        chatbot_service.sp.search_hospitals = self.orig_search_hospitals
        chatbot_service.sp.search_emergency_hospitals = self.orig_search_emergency

    # -----------------------------------------------------------------------
    # Skenario 1: Pencarian Spesifik (Kelas & Kota)
    # -----------------------------------------------------------------------
    def test_scenario_01_search_kelas_dan_kota(self):
        mock_search = AsyncFuncMock(return_value=[MOCK_HOSPITALS[1]])
        chatbot_service.sp.search_hospitals = mock_search

        res = run_sync(process_chat_message("RS kelas B di Medan"))

        self.assertFalse(res["is_emergency"])
        self.assertIn("Dr. Pirngadi", res["text"])
        self.assertEqual(len(res["hospitals"]), 1)
        self.assertIn("alasan", res["hospitals"][0])
        self.assertTrue(len(res["quick_replies"]) > 0)
        call_kwargs = mock_search.call_args[1]
        self.assertEqual(call_kwargs.get("kelas"), "B")
        self.assertEqual(call_kwargs.get("kabkota"), "Kota Medan")

    # -----------------------------------------------------------------------
    # Skenario 2: Konteks Percakapan Multi-turn (Pesan Lanjutan BPJS)
    # -----------------------------------------------------------------------
    def test_scenario_02_multiturn_followup_bpjs(self):
        history = [
            {"role": "user", "text": "RS kelas B di Medan"},
            {"role": "assistant", "text": "Berikut daftar RS kelas B di Medan..."},
        ]
        mock_search = AsyncFuncMock(return_value=[MOCK_HOSPITALS[1]])
        chatbot_service.sp.search_hospitals = mock_search

        res = run_sync(process_chat_message("yang terima BPJS?", history=history))

        self.assertFalse(res["is_emergency"])
        self.assertIn("Dr. Pirngadi", res["text"])
        call_kwargs = mock_search.call_args[1]
        # Konteks dari Turn 1 harus tetap terbawa
        self.assertEqual(call_kwargs.get("kelas"), "B")
        self.assertEqual(call_kwargs.get("kabkota"), "Kota Medan")
        self.assertTrue(call_kwargs.get("bpjs"))

    # -----------------------------------------------------------------------
    # Skenario 3: Pencarian Terdekat Berbasis Koordinat GPS
    # -----------------------------------------------------------------------
    def test_scenario_03_nearby_with_gps(self):
        mock_search = AsyncFuncMock(return_value=MOCK_HOSPITALS)
        chatbot_service.sp.search_hospitals = mock_search

        lat, lon = 3.5925, 98.6782
        res = run_sync(process_chat_message("RS terdekat dari saya", lat=lat, lon=lon))

        self.assertFalse(res["is_emergency"])
        self.assertTrue(len(res["hospitals"]) > 0)
        hosp = res["hospitals"]
        self.assertIn("distance_km", hosp[0])
        self.assertLessEqual(hosp[0]["distance_km"], hosp[-1]["distance_km"])
        self.assertIn("km", res["text"])

    # -----------------------------------------------------------------------
    # Skenario 4: Bahasa Informal & Keluhan Gejala Medis (Poli Anak)
    # -----------------------------------------------------------------------
    def test_scenario_04_symptom_layanan_extraction(self):
        mock_search = AsyncFuncMock(return_value=[MOCK_HOSPITALS[0]])
        chatbot_service.sp.search_hospitals = mock_search

        res = run_sync(process_chat_message("anak saya demam tinggi butuh dokter anak"))

        self.assertFalse(res["is_emergency"])
        call_kwargs = mock_search.call_args[1]
        self.assertEqual(call_kwargs.get("layanan"), "Kesehatan Anak")
        self.assertTrue(any(w in res["text"] for w in ["Semoga", "lekas", "tenang"]))

    # -----------------------------------------------------------------------
    # Skenario 5: Penanganan Typo & Singkatan Informal
    # -----------------------------------------------------------------------
    def test_scenario_05_typo_handling(self):
        mock_search = AsyncFuncMock(return_value=[MOCK_HOSPITALS[0]])
        chatbot_service.sp.search_hospitals = mock_search

        res = run_sync(process_chat_message("rmh skt kls a di mddan"))

        self.assertFalse(res["is_emergency"])
        call_kwargs = mock_search.call_args[1]
        self.assertEqual(call_kwargs.get("kelas"), "A")
        self.assertEqual(call_kwargs.get("kabkota"), "Kota Medan")

    # -----------------------------------------------------------------------
    # Skenario 6: Mode Darurat (Emergency Mode)
    # -----------------------------------------------------------------------
    def test_scenario_06_emergency_mode(self):
        mock_emergency = AsyncFuncMock(return_value=MOCK_HOSPITALS)
        chatbot_service.sp.search_emergency_hospitals = mock_emergency

        res = run_sync(process_chat_message("Tolong kecelakaan parah pendarahan"))

        self.assertTrue(res["is_emergency"])
        self.assertIn("119", res["text"])
        self.assertIn("112", res["text"])
        self.assertIn("118", res["text"])
        self.assertIn("UGD 24 JAM", res["text"])
        for emoji in ["😀", "🏥", "🚑", "🩺", "🙏", "✨", "🔍"]:
            self.assertNotIn(emoji, res["text"])

    # -----------------------------------------------------------------------
    # Skenario 7: Perbandingan Dua Rumah Sakit (Compare Table)
    # -----------------------------------------------------------------------
    def test_scenario_07_compare_hospitals(self):
        def side_effect(q="", **kwargs):
            if "adam malik" in q.lower():
                return [MOCK_HOSPITALS[0]]
            if "pirngadi" in q.lower():
                return [MOCK_HOSPITALS[1]]
            return []

        mock_search = AsyncFuncMock(side_effect=side_effect)
        chatbot_service.sp.search_hospitals = mock_search

        res = run_sync(process_chat_message("Bandingkan RS Adam Malik dan RS Pirngadi"))

        self.assertFalse(res["is_emergency"])
        self.assertIn("| Atribut |", res["text"])
        self.assertIn("RS Umum Pusat H. Adam Malik", res["text"])
        self.assertIn("RS Umum Daerah Dr. Pirngadi", res["text"])
        self.assertEqual(len(res["hospitals"]), 2)

    # -----------------------------------------------------------------------
    # Skenario 8: Klarifikasi Input Terlalu Singkat / Ambigu
    # -----------------------------------------------------------------------
    def test_scenario_08_clarification_ambiguous(self):
        res = run_sync(process_chat_message("Cari rumah sakit"))

        self.assertFalse(res["is_emergency"])
        self.assertEqual(len(res["hospitals"]), 0)
        self.assertTrue(any(w in res["text"] for w in ["wilayah", "kota", "kabupaten"]))
        self.assertIn("Kota Medan", res["quick_replies"])

    # -----------------------------------------------------------------------
    # Skenario 9: Hasil Pencarian Kosong (Empty Result Fallback)
    # -----------------------------------------------------------------------
    def test_scenario_09_empty_results(self):
        mock_search = AsyncFuncMock(return_value=[])
        chatbot_service.sp.search_hospitals = mock_search

        res = run_sync(process_chat_message("RS kelas A di Kota Sibolga"))

        self.assertFalse(res["is_emergency"])
        self.assertEqual(len(res["hospitals"]), 0)
        self.assertTrue(any(w in res["text"].lower() for w in ["belum menemukan", "belum ada", "tidak cocok", "tidak ada", "belum ditemukan"]))
        self.assertIn("Lihat semua RS di Medan", res["quick_replies"])

    # -----------------------------------------------------------------------
    # Skenario 10: Out of Scope 1 - Tiket Pesawat
    # -----------------------------------------------------------------------
    def test_scenario_10_out_of_scope_flight_ticket(self):
        res = run_sync(process_chat_message("Berapa harga tiket pesawat ke Jakarta?"))

        self.assertFalse(res["is_emergency"])
        self.assertEqual(len(res["hospitals"]), 0)
        self.assertEqual(res["text"], OUT_OF_SCOPE_TEXT)

    # -----------------------------------------------------------------------
    # Skenario 11: Out of Scope 2 - Pengetahuan Umum & Non-Hospital
    # -----------------------------------------------------------------------
    def test_scenario_11_out_of_scope_general_knowledge(self):
        res = run_sync(process_chat_message("Siapa presiden Indonesia?"))
        self.assertFalse(res["is_emergency"])
        self.assertEqual(len(res["hospitals"]), 0)
        self.assertEqual(res["text"], OUT_OF_SCOPE_TEXT)

        # Uji spesifik: "coba tebak namaku" baik dengan dan tanpa koordinat GPS
        res_tebak = run_sync(process_chat_message("coba tebak namaku"))
        self.assertEqual(res_tebak["text"], OUT_OF_SCOPE_TEXT)
        self.assertEqual(len(res_tebak["hospitals"]), 0)

        res_tebak_gps = run_sync(process_chat_message("coba tebak namaku", lat=2.33, lon=99.12))
        self.assertEqual(res_tebak_gps["text"], OUT_OF_SCOPE_TEXT)
        self.assertEqual(len(res_tebak_gps["hospitals"]), 0)

        # Uji spesifik non-medis lainnya
        for query in ["cuaca di Medan", "mobil terdekat", "rumah makan terdekat", "kucing saya sakit"]:
            res_non = run_sync(process_chat_message(query, lat=3.59, lon=98.67))
            self.assertEqual(res_non["text"], OUT_OF_SCOPE_TEXT, f"Query '{query}' harus OUT_OF_SCOPE")
            self.assertEqual(len(res_non["hospitals"]), 0)

    # -----------------------------------------------------------------------
    # Skenario 12: Pertanyaan Rating / Review RS (Kejujuran Data)
    # -----------------------------------------------------------------------
    def test_scenario_12_rating_inquiry(self):
        res = run_sync(process_chat_message("Apakah ada rating atau ulasan RS di Medan?"))

        self.assertFalse(res["is_emergency"])
        self.assertIn("belum memuat data penilaian/rating bintang", res["text"])
        self.assertIn("Kelas A & B", res["text"])

    # -----------------------------------------------------------------------
    # Skenario 13: Pertanyaan Jam Buka Operasional RS
    # -----------------------------------------------------------------------
    def test_scenario_13_jam_buka_inquiry(self):
        res = run_sync(process_chat_message("Jam buka RS jam berapa ya?"))

        self.assertFalse(res["is_emergency"])
        self.assertIn("24 Jam", res["text"])
        self.assertIn("Poliklinik", res["text"])

    # -----------------------------------------------------------------------
    # Skenario 14: Penanganan Error Triplestore / Database Down
    # -----------------------------------------------------------------------
    def test_scenario_14_database_down_error_handling(self):
        mock_search = AsyncFuncMock(side_effect=Exception("Connection refused to Fuseki triplestore"))
        chatbot_service.sp.search_hospitals = mock_search

        res = run_sync(process_chat_message("RS kelas B di Medan"))

        self.assertFalse(res["is_emergency"])
        self.assertEqual(len(res["hospitals"]), 0)
        self.assertTrue(any(w in res["text"].lower() for w in ["database", "kendala", "server"]))


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(ChatbotScenariosTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("=" * 60)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print("=" * 60)
    if result.wasSuccessful():
        print("ALL 14 TESTS PASSED (100% SUCCESS)!")
        sys.exit(0)
    else:
        print("TESTS FAILED.")
        sys.exit(1)
