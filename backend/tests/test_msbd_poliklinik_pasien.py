import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestMsbdEndpoints(unittest.TestCase):
    def test_health_and_poliklinik_list(self):
        r_health = client.get("/health")
        self.assertEqual(r_health.status_code, 200)

        r_poli = client.get("/api/poliklinik/rs-001")
        self.assertEqual(r_poli.status_code, 200)
        body = r_poli.json()
        self.assertEqual(body["rs_id"], "rs-001")
        self.assertIsInstance(body["poliklinik"], list)

    def test_patient_login_and_dashboard(self):
        r_login = client.post("/api/auth/login", json={
            "username_or_email": "pasien_demo",
            "password": "Demo1234!",
        })
        self.assertEqual(r_login.status_code, 200, r_login.text)
        token = r_login.json()["access_token"]

        r_dash = client.get("/api/pasien/dashboard", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r_dash.status_code, 200, r_dash.text)
        dash = r_dash.json()
        self.assertEqual(dash["profil"]["username"], "pasien_demo")
        self.assertIn("statistik", dash)

    def test_hospital_rankings_and_reviews(self):
        r_rank = client.get("/api/rs-peringkat?min_ulasan=1&limit=10")
        self.assertEqual(r_rank.status_code, 200, r_rank.text)
        self.assertIn("peringkat", r_rank.json())

        r_rev = client.get("/api/rs/rs-001/ulasan")
        self.assertEqual(r_rev.status_code, 200, r_rev.text)
        self.assertIn("ulasan", r_rev.json())

    def test_admin_poliklinik_and_ulasan_views(self):
        r_adm_login = client.post("/api/admin/login", json={
            "username": "admin",
            "password": "admin12345",
        })
        self.assertEqual(r_adm_login.status_code, 200, r_adm_login.text)
        login_data = r_adm_login.json()
        adm_token = login_data.get("access_token") or login_data.get("token")
        hdr = {"Authorization": f"Bearer {adm_token}"} if adm_token else {}

        r_adm_poli = client.get("/api/admin/poliklinik", headers=hdr)
        self.assertEqual(r_adm_poli.status_code, 200, r_adm_poli.text)
        self.assertIn("items", r_adm_poli.json())

        r_adm_ulasan = client.get("/api/admin/ulasan", headers=hdr)
        self.assertEqual(r_adm_ulasan.status_code, 200, r_adm_ulasan.text)
        self.assertIn("items", r_adm_ulasan.json())


if __name__ == "__main__":
    unittest.main()
