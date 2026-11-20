"""Live HTTP API endpoint verification for CariSehat Final Feature Freeze."""
import unittest
import httpx

API_BASE = "http://localhost:8000/api"


class TestFreezeLiveHTTP(unittest.TestCase):
    def test_hospital_detail_enriched(self):
        r = httpx.get(f"{API_BASE}/hospitals/rs-171", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["id"], "rs-171")
        self.assertEqual(data["nama"], "RS Umum Pusat H. Adam Malik")
        self.assertEqual(data["kode_kemenkes"], "1275655")
        self.assertEqual(data["direktur"], "dr. Zainal Safri, M.Ked (PD), Sp.PD-KKV, Sp.JP(K)")
        self.assertEqual(data["email"], "info@rsham.co.id")
        self.assertTrue("VERIF" in data["email_status"])
        self.assertIn("fasilitas_medis_berbukti", data)
        self.assertIn("jam_operasional", data)
        self.assertTrue(data["igd_24jam_terlapor"]["igd_24jam_terlapor"])

    def test_hospital_operational_hours_endpoint(self):
        r = httpx.get(f"{API_BASE}/hospitals/rs-171/operational-hours", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["id_carisehat"], "rs-171")
        self.assertIn("jam_operasional", data)
        jam = data["jam_operasional"]
        self.assertTrue("JADWAL_" in jam["status_jam_operasional"] or "JAM_" in jam["status_jam_operasional"])
        self.assertIn("unit_operasional", jam)
        self.assertTrue(len(jam["unit_operasional"]) >= 2)

    def test_enrichment_summary_endpoint(self):
        r = httpx.get(f"{API_BASE}/enrichment/summary", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["metadata"]["total_rumah_sakit"], 206)
        self.assertEqual(data["coverage_6_fitur"]["fitur_1_profil_lengkap"]["kode_kemenkes_terverifikasi"], 206)
        self.assertEqual(data["coverage_6_fitur"]["fitur_5_igd_24jam_terlapor"]["terlapor_24jam"], 198)

    def test_unverified_hospital_integrity(self):
        r = httpx.get(f"{API_BASE}/hospitals/rs-001", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIsNone(data["email"])
        self.assertIn("Belum tersedia", data["email_display"])


if __name__ == "__main__":
    unittest.main()
