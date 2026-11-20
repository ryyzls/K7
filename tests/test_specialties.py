"""Unit test untuk mapping spesialisasi medis dan sinonim pencarian SIRS."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.specialty_service import (
    resolve_synonym,
    get_active_specialty_list,
    sirs_specialty_pattern,
    ACTIVE_CLINICAL_SPECIALTIES,
    SYNONYM_MAP,
    ALL_ACTIVE_SPECIALTIES,
)
from app.services import sirs


class SpecialtyMappingTests(unittest.TestCase):
    def test_required_synonym_mappings(self):
        # 4 contoh wajib dalam requirement task:
        self.assertEqual(resolve_synonym("dokter jantung"), "Jantung dan Pembuluh Darah")
        self.assertEqual(resolve_synonym("dokter anak"), "Kesehatan anak")
        self.assertEqual(resolve_synonym("dokter kandungan"), "Obstetri dan ginekologi")
        self.assertEqual(resolve_synonym("dokter mata"), "Mata")

    def test_additional_clinical_synonyms(self):
        self.assertEqual(resolve_synonym("spesialis jantung"), "Jantung dan Pembuluh Darah")
        self.assertEqual(resolve_synonym("kardiologi"), "Jantung dan Pembuluh Darah")
        self.assertEqual(resolve_synonym("pediatri"), "Kesehatan anak")
        self.assertEqual(resolve_synonym("obgyn"), "Obstetri dan ginekologi")
        self.assertEqual(resolve_synonym("spog"), "Obstetri dan ginekologi")
        self.assertEqual(resolve_synonym("oftalmologi"), "Mata")
        self.assertEqual(resolve_synonym("internis"), "Penyakit dalam")
        self.assertEqual(resolve_synonym("dokter bedah"), "Bedah")
        self.assertEqual(resolve_synonym("neurologi"), "Saraf")
        self.assertEqual(resolve_synonym("pulmonologi"), "Paru")
        self.assertEqual(resolve_synonym("dokter tht"), "Telinga Hidung Tenggorok Kepala Leher")
        self.assertEqual(resolve_synonym("dokter kulit"), "Kulit dan Kelamin")
        self.assertEqual(resolve_synonym("dokter tulang"), "Orthopedi")
        self.assertEqual(resolve_synonym("ortopedi"), "Orthopedi")
        self.assertEqual(resolve_synonym("urologi"), "Urologi")
        self.assertEqual(resolve_synonym("psikiater"), "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA")
        self.assertEqual(resolve_synonym("dokter gigi"), "Pelayanan medik gigi mulut")
        self.assertEqual(resolve_synonym("ugd"), sirs.EMERGENCY)
        self.assertEqual(resolve_synonym("igd"), sirs.EMERGENCY)
        self.assertEqual(resolve_synonym("radiologi"), "Radiologi")

    def test_unknown_or_ambiguous_term_returns_none(self):
        # Bukan tebakan LLM, istilah acak atau di luar domain harus None
        self.assertIsNone(resolve_synonym("penyakit misterius"))
        self.assertIsNone(resolve_synonym("obat pusing kepala"))
        self.assertIsNone(resolve_synonym("parkir gratis"))
        self.assertIsNone(resolve_synonym("wifi kencang"))

    def test_active_specialties_count_and_metadata(self):
        # 16 spesialisasi klinis standar Permenkes 3/2020
        self.assertEqual(len(ACTIVE_CLINICAL_SPECIALTIES), 16)
        # Total aktif termasuk darurat & diagnostik
        self.assertEqual(len(ALL_ACTIVE_SPECIALTIES), 19)

        active_list = get_active_specialty_list()
        self.assertEqual(len(active_list), 19)
        for item in active_list:
            self.assertIn("label_sirs", item)
            self.assertIn("display_name", item)
            self.assertIn("kategori", item)
            self.assertIn("frekuensi_rs", item)
            self.assertTrue(item["frekuensi_rs"] > 0)
            self.assertEqual(item["status_kebijakan"], "REVIEWED_ACTIVE")

    def test_sparql_pattern_escapes_injection(self):
        clean_pat = sirs_specialty_pattern("Mata")
        self.assertIn('?obs <http://carisehat.id/ontology/sirs/labelPelayanan> "Mata"', clean_pat)

        malicious_input = 'Mata" } ; DROP ALL ; #'
        safe_pat = sirs_specialty_pattern(malicious_input)
        # Kutip dua harus di-escape menjadi \" sehingga penyerang tidak dapat keluar dari literal string
        self.assertIn('\\"', safe_pat)
        self.assertTrue(safe_pat.startswith("GRAPH <http://carisehat.id/graph/sirs/2026-11-19>"))


if __name__ == "__main__":
    unittest.main()
