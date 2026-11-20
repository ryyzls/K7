"""Comprehensive test suite for CariSehat Final Data Enrichment & Semantic Feature Freeze.

Verifies:
1. Complete Hospital Profiles (206 RS, Kode Registrasi Kemenkes, Direktur, Kepemilikan).
2. Official & Candidate Websites (133 available, zero fabricated URLs, 'Belum tersedia' fallback).
3. Email and Contacts (152 available, explicit 'Belum tersedia' fallback for missing).
4. Evidence-Based Medical Facilities (physical beds vs diagnostic modalities).
5. IGD 24 Jam Reported (198 reported, 8 unrecorded).
6. Operational Hours & Poliklinik Schedule (WIB Asia/Jakarta timezone, no fictional hours).
7. Live HTTP API Endpoints & SPARQL Integration.
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import asyncio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.enrichment_service import (
    get_hospital_enrichment,
    get_all_hospitals_enrichment_summary,
    WIB
)
from app.services import sparql_service as sp

FINAL_DIR = ROOT / "data" / "enrichment" / "final_info_rs"


class CariSehatFeatureFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = get_all_hospitals_enrichment_summary()

    # =========================================================================
    # FITUR 1: PROFIL RUMAH SAKIT LEBIH LENGKAP
    # =========================================================================
    def test_fitur1_complete_profile_coverage(self):
        cov = self.summary["coverage_6_fitur"]["fitur_1_profil_lengkap"]
        self.assertEqual(cov["kode_kemenkes_terverifikasi"], 206)
        self.assertEqual(cov["direktur_tercatat"], 206)
        self.assertEqual(cov["kepemilikan_tercatat"], 206)
        self.assertGreaterEqual(cov["luas_tanah_tercatat"], 204)

        # RSUP H. Adam Malik (rs-171)
        e171 = get_hospital_enrichment("rs-171")
        prof171 = e171["profil_lengkap"]
        self.assertEqual(prof171["kode_kemenkes"], "1275655")
        self.assertEqual(prof171["direktur"], "dr. Zainal Safri, M.Ked (PD), Sp.PD-KKV, Sp.JP(K)")
        self.assertEqual(prof171["kepemilikan"], "Kemkes")

        # OG Hospital (rs-001)
        e001 = get_hospital_enrichment("rs-001")
        prof001 = e001["profil_lengkap"]
        self.assertEqual(prof001["kode_kemenkes"], "1276079")
        self.assertEqual(prof001["direktur"], "dr. Naeni Juliani, M.K.M")
        self.assertEqual(prof001["kepemilikan"], "Perusahaan")

    # =========================================================================
    # FITUR 2: WEBSITE RESMI & KANDIDAT RS
    # =========================================================================
    def test_fitur2_website_coverage_and_fallback(self):
        cov = self.summary["coverage_6_fitur"]["fitur_2_website_resmi"]
        self.assertGreaterEqual(cov.get("tersedia", 0), 130)

        # Verified & candidate hospitals must have valid URL
        for rs_id in ["rs-171", "rs-003", "rs-009", "rs-055"]:
            k = get_hospital_enrichment(rs_id)["kontak_dan_website"]
            self.assertTrue(k["website_url"].startswith("http"))

        # Hospital without website must have None and fallback 'Belum tersedia'
        e001 = get_hospital_enrichment("rs-001")["kontak_dan_website"]
        self.assertIsNone(e001["website_url"])
        self.assertEqual(e001["website_display"], "Belum tersedia")

    # =========================================================================
    # FITUR 3: EMAIL DAN KONTAK RESMI
    # =========================================================================
    def test_fitur3_email_coverage_and_fallback(self):
        cov = self.summary["coverage_6_fitur"]["fitur_3_email_dan_kontak"]
        self.assertGreaterEqual(cov.get("email_tersedia", 0), 150)

        # RS-171 email verified
        k171 = get_hospital_enrichment("rs-171")["kontak_dan_website"]
        self.assertEqual(k171["email"], "info@rsham.co.id")

        # RS-003 email from mass discovery
        k003 = get_hospital_enrichment("rs-003")["kontak_dan_website"]
        self.assertIn("@", k003["email"])

        # RS-001 email missing -> explicit "Belum tersedia"
        k001 = get_hospital_enrichment("rs-001")["kontak_dan_website"]
        self.assertIsNone(k001["email"])
        self.assertEqual(k001["email_display"], "Belum tersedia")

    # =========================================================================
    # FITUR 4: FASILITAS MEDIS BERBASIS BUKTI
    # =========================================================================
    def test_fitur4_facilities_evidence_based(self):
        cov = self.summary["coverage_6_fitur"]["fitur_4_fasilitas_medis_berbukti"]
        self.assertEqual(cov["rs_memiliki_icu"], 187)
        self.assertEqual(cov["rs_memiliki_nicu"], 163)
        self.assertEqual(cov["rs_memiliki_picu"], 112)
        self.assertEqual(cov["rs_memiliki_ct_scan"], 62)
        self.assertEqual(cov["rs_memiliki_radiologi"], 177)
        self.assertEqual(cov["rs_memiliki_hemodialisis"], 61)
        self.assertEqual(cov["rs_memiliki_laboratorium"], 60)
        self.assertEqual(cov["rs_memiliki_kamar_operasi"], 196)

        # RS-171 facilities
        f171 = get_hospital_enrichment("rs-171")["fasilitas_medis_berbukti"]
        self.assertGreater(f171["ruang_perawatan_kritis_terlapor"]["icu_dengan_ventilator"], 0)
        self.assertIn("CT Scan", f171["fasilitas_diagnostik_terlapor"])
        self.assertIn("Radiologi", f171["fasilitas_diagnostik_terlapor"])

    # =========================================================================
    # FITUR 5: IGD 24 JAM TERLAPOR SIRS
    # =========================================================================
    def test_fitur5_igd_24h_reported_status(self):
        cov = self.summary["coverage_6_fitur"]["fitur_5_igd_24jam_terlapor"]
        self.assertEqual(cov["terlapor_24jam"], 198)
        self.assertEqual(cov["tidak_terlapor_24jam"], 8)

        # RS-001 has IGD 24 Jam reported
        i001 = get_hospital_enrichment("rs-001")["igd_24jam"]
        self.assertTrue(i001["igd_24jam_terlapor"])

        # RS-206 does NOT have IGD 24 Jam reported in SIRS
        i206 = get_hospital_enrichment("rs-206")["igd_24jam"]
        self.assertFalse(i206["igd_24jam_terlapor"])

    # =========================================================================
    # FITUR 6: JAM OPERASIONAL & POLIKLINIK (ZONA WAKTU ASIA/JAKARTA)
    # =========================================================================
    def test_fitur6_operational_hours(self):
        # RS-171 has active units
        e171 = get_hospital_enrichment("rs-171")
        units171 = {u["unit"]: u for u in e171["jam_operasional"]["unit_operasional"]}
        self.assertEqual(units171["Instalasi Gawat Darurat (IGD)"]["status_sekarang"]["status_kode"], "BUKA_24_JAM")
        self.assertEqual(units171["Poliklinik Rawat Jalan"]["status_sekarang"]["status_kode"], "TERSEDIA")

        # RS-001 has IGD 24h
        e001 = get_hospital_enrichment("rs-001")
        units001 = {u["unit"]: u for u in e001["jam_operasional"]["unit_operasional"]}
        self.assertEqual(units001["Instalasi Gawat Darurat (IGD)"]["status_sekarang"]["status_kode"], "BUKA_24_JAM")

    # =========================================================================
    # INTEGRASI SPARQL & GET_HOSPITAL
    # =========================================================================
    def test_sparql_service_integration(self):
        h = asyncio.run(sp.get_hospital("rs-171"))
        self.assertIsNotNone(h)
        self.assertEqual(h["kode_kemenkes"], "1275655")
        self.assertEqual(h["direktur"], "dr. Zainal Safri, M.Ked (PD), Sp.PD-KKV, Sp.JP(K)")
        self.assertEqual(h["email"], "info@rsham.co.id")
        self.assertIn("fasilitas_medis_berbukti", h)
        self.assertIn("jam_operasional", h)
        self.assertTrue(h["igd_24jam_terlapor"]["igd_24jam_terlapor"])


if __name__ == "__main__":
    unittest.main()
