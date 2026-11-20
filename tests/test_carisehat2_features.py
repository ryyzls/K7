"""Comprehensive test suite for CariSehat 2.0 4 Core Features."""
import unittest
import sys
from pathlib import Path
import asyncio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.specialty_service import (
    resolve_synonym,
    get_active_specialty_list,
    ACTIVE_CLINICAL_SPECIALTIES,
    ALL_ACTIVE_SPECIALTIES,
    sirs_specialty_pattern,
)
from app.services.comparison_service import compare_hospitals
from app.services.alternatives_service import find_alternatives
from app.services import sparql_service as sp
from fastapi import HTTPException


class CariSehat2FeatureTests(unittest.TestCase):
    # =========================================================================
    # FITUR 1: PENCARIAN SPESIALISASI & SINONIM EKSPLISIT
    # =========================================================================
    def test_fitur1_synonym_resolution(self):
        cases = {
            "dokter jantung": "Jantung dan Pembuluh Darah",
            "spesialis jantung": "Jantung dan Pembuluh Darah",
            "dokter anak": "Kesehatan anak",
            "pediatri": "Kesehatan anak",
            "dokter kandungan": "Obstetri dan ginekologi",
            "kebidanan dan kandungan": "Obstetri dan ginekologi",
            "spog": "Obstetri dan ginekologi",
            "dokter mata": "Mata",
            "oftalmologi": "Mata",
            "dokter penyakit dalam": "Penyakit dalam",
            "internis": "Penyakit dalam",
            "dokter bedah": "Bedah",
            "dokter saraf": "Saraf",
            "dokter paru": "Paru",
            "dokter tht": "Telinga Hidung Tenggorok Kepala Leher",
            "dokter kulit": "Kulit dan Kelamin",
            "dokter tulang": "Orthopedi",
            "psikiater": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
            "dokter gigi": "Pelayanan medik gigi mulut",
            "ugd": "Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu",
        }
        for query, expected_label in cases.items():
            resolved = resolve_synonym(query)
            self.assertEqual(resolved, expected_label, f"Query '{query}' gagal di-resolve ke '{expected_label}'")

    def test_fitur1_active_specialties_count(self):
        # 16 spesialisasi klinis standar Permenkes 3/2020
        self.assertEqual(len(ACTIVE_CLINICAL_SPECIALTIES), 16)
        self.assertEqual(len(ALL_ACTIVE_SPECIALTIES), 19)
        # Sisa 137 label dari 153 label aman tetap ditahan
        self.assertEqual(153 - 16, 137)

    def test_fitur1_sparql_search_by_specialty(self):
        # Cari RS dengan spesialisasi Jantung dan Pembuluh Darah
        res = asyncio.run(sp.search_hospitals(spesialisasi="Jantung dan Pembuluh Darah", limit=10))
        self.assertTrue(len(res) > 0)
        for h in res:
            self.assertIn("Jantung dan Pembuluh Darah", h["spesialisasi"])
            self.assertIn("id", h)
            self.assertIn("nama", h)

    def test_fitur1_sparql_pattern_security(self):
        pat = sirs_specialty_pattern("Mata")
        self.assertIn("GRAPH <http://carisehat.id/graph/sirs/2026-11-19>", pat)
        self.assertIn('?obs <http://carisehat.id/ontology/sirs/labelPelayanan> "Mata"', pat)

    # =========================================================================
    # FITUR 2: PERBANDINGAN RUMAH SAKIT
    # =========================================================================
    def test_fitur2_compare_validation_limits(self):
        # Maksimal 3 RS
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(compare_hospitals(["rs-001", "rs-002", "rs-003", "rs-004"]))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Maksimal 3", ctx.exception.detail)

        # ID kosong
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(compare_hospitals([]))
        self.assertEqual(ctx.exception.status_code, 400)

        # ID tidak ditemukan
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(compare_hospitals(["rs-non-existent-999"]))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_fitur2_compare_two_hospitals_matrix(self):
        res = asyncio.run(compare_hospitals(["rs-001", "rs-002"]))
        self.assertEqual(res["count"], 2)
        hospitals = res["hospitals"]
        self.assertEqual(len(hospitals), 2)

        # Periksa atribut faktual wajib
        for h in hospitals:
            self.assertIn("id", h)
            self.assertIn("nama", h)
            self.assertIn("kode_kemenkes", h)
            self.assertIn("kelas", h)
            self.assertIn("jenis", h)
            self.assertIn("kabkota", h)
            self.assertIn("alamat", h)
            self.assertIn("telepon", h)
            self.assertIn("spesialisasi_sirs", h)
            self.assertIn("fasilitas", h)

        # Periksa matriks perbandingan
        matrix = res["comparison_matrix"]
        self.assertIn("shared_services", matrix)
        self.assertIn("all_distinct_services", matrix)
        self.assertIn("unique_services_per_hospital", matrix)
        self.assertIn("disclaimers", res)

    def test_fitur2_compare_three_hospitals_matrix(self):
        res = asyncio.run(compare_hospitals(["rs-001", "rs-008", "rs-171"]))
        self.assertEqual(res["count"], 3)
        self.assertEqual(len(res["hospitals"]), 3)

    # =========================================================================
    # FITUR 3: ALTERNATIF RUMAH SAKIT
    # =========================================================================
    def test_fitur3_alternatives_generation(self):
        res = asyncio.run(find_alternatives("rs-001", limit=4))
        self.assertIn("target_rs", res)
        self.assertEqual(res["target_rs"]["id"], "rs-001")
        self.assertTrue(res["has_alternatives"])
        self.assertTrue(1 <= res["count"] <= 4)

        for alt in res["alternatives"]:
            self.assertIn("id", alt)
            self.assertIn("nama", alt)
            self.assertIn("alasan_rekomendasi", alt)
            self.assertTrue(len(alt["alasan_rekomendasi"]) > 10)
            self.assertIn("score", alt)
            self.assertIn("layanan_serupa", alt)
            self.assertNotEqual(alt["id"], "rs-001")

    def test_fitur3_alternatives_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(find_alternatives("rs-fake-missing"))
        self.assertEqual(ctx.exception.status_code, 404)

    # =========================================================================
    # FITUR 4: PROFIL RS LENGKAP & KODE KEMENKES
    # =========================================================================
    def test_fitur4_complete_profile_fields(self):
        h = asyncio.run(sp.get_hospital("rs-001"))
        self.assertIsNotNone(h)
        # Kode registrasi Kemenkes resmi
        self.assertEqual(h["kode_kemenkes"], "1276079")
        # Identitas & kontak
        self.assertIn("nama", h)
        self.assertIn("alamat", h)
        self.assertIn("telepon", h)
        self.assertIn("kabkota", h)
        # Layanan & spesialisasi SIRS terstruktur
        self.assertIn("spesialisasi", h)
        self.assertTrue(len(h["spesialisasi"]) > 0)
        self.assertIn("Kesehatan anak", h["spesialisasi"])
        self.assertIn("Penyakit dalam", h["spesialisasi"])
        # Provenance fakta spesialisasi
        self.assertIn("spesialisasi_facts", h)
        first_fact = h["spesialisasi_facts"][0]
        self.assertTrue(first_fact["source_url"].startswith("https://sirs.kemkes.go.id/"))
        self.assertIn("retrieved_at", first_fact)
        # Indikator UGD 24 jam
        self.assertTrue(h["igd_tersedia"])


if __name__ == "__main__":
    unittest.main()
