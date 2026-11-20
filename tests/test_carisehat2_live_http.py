"""Live HTTP tests against running CariSehat FastAPI server for 4 core features."""
import unittest
import httpx
import os

BASE_URL = os.environ.get("CARISEHAT_URL", "http://127.0.0.1:8000")


class LiveHTTPFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
            r = client.get("/api/health")
            if r.status_code != 200:
                raise unittest.SkipTest(f"CariSehat backend not healthy at {BASE_URL}")

    def test_live_specialties_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
            r = client.get("/api/specialties")
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertIn("items", data)
            self.assertEqual(data["count"], 19)
            labels = [x["label_sirs"] for x in data["items"]]
            self.assertIn("Jantung dan Pembuluh Darah", labels)
            self.assertIn("Kesehatan anak", labels)
            self.assertIn("Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu", labels)

    def test_live_search_by_specialty_synonym(self):
        with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
            # Cari dokter jantung
            r = client.get("/api/search", params={"q": "dokter jantung"})
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data.get("matched_specialty"), "Jantung dan Pembuluh Darah")
            self.assertEqual(data.get("query_type"), "specialty_synonym")
            self.assertTrue(data["count"] > 0)
            first_rs = data["items"][0]
            self.assertIn("Jantung dan Pembuluh Darah", first_rs["spesialisasi"])

    def test_live_search_by_explicit_specialty(self):
        with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
            r = client.get("/api/search", params={"spesialisasi": "Mata", "limit": 5})
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertTrue(data["count"] > 0)
            for h in data["items"]:
                self.assertIn("Mata", h["spesialisasi"])

    def test_live_compare_endpoint_two_and_three(self):
        with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
            # 2 RS
            r2 = client.get("/api/compare", params={"ids": "rs-001,rs-002"})
            self.assertEqual(r2.status_code, 200)
            d2 = r2.json()
            self.assertEqual(d2["count"], 2)
            self.assertIn("comparison_matrix", d2)
            self.assertEqual(d2["hospitals"][0]["kode_kemenkes"], "1276079")

            # 3 RS
            r3 = client.get("/api/compare", params={"ids": "rs-001,rs-008,rs-171"})
            self.assertEqual(r3.status_code, 200)
            d3 = r3.json()
            self.assertEqual(d3["count"], 3)

            # Limit > 3 should fail 400
            r4 = client.get("/api/compare", params={"ids": "rs-001,rs-002,rs-003,rs-004"})
            self.assertEqual(r4.status_code, 400)

    def test_live_hospital_alternatives_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
            r = client.get("/api/hospitals/rs-001/alternatives", params={"limit": 4})
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data["target_rs"]["id"], "rs-001")
            self.assertTrue(data["has_alternatives"])
            self.assertTrue(len(data["alternatives"]) <= 4)
            for alt in data["alternatives"]:
                self.assertIn("alasan_rekomendasi", alt)
                self.assertTrue(len(alt["alasan_rekomendasi"]) > 10)

    def test_live_hospital_detail_and_html(self):
        with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
            # API detail
            r = client.get("/api/hospitals/rs-001")
            self.assertEqual(r.status_code, 200)
            h = r.json()
            self.assertEqual(h["kode_kemenkes"], "1276079")
            self.assertTrue(h["igd_tersedia"])

            # HTML detail
            r_html = client.get("/rs/rs-001")
            self.assertEqual(r_html.status_code, 200)
            self.assertIn("1276079", r_html.text)
            self.assertIn("Kode Registrasi Kemenkes", r_html.text)
            self.assertIn("Rumah Sakit Alternatif Rekomendasi", r_html.text)


if __name__ == "__main__":
    unittest.main()
