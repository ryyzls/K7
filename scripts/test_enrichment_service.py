import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.enrichment_service import get_hospital_enrichment

WIB = timezone(timedelta(hours=7))

# Test Monday at 10:00 WIB
dt_monday_morning = datetime(2026, 11, 23, 10, 0, tzinfo=WIB)
# Test Sunday at 10:00 WIB
dt_sunday_morning = datetime(2026, 11, 22, 10, 0, tzinfo=WIB)

print("=== RS-171 (Adam Malik) Monday 10:00 WIB ===")
e171 = get_hospital_enrichment("rs-171", current_dt_wib=dt_monday_morning)
print(json.dumps(e171["jam_operasional"], indent=2))
print("Email:", e171["kontak_dan_website"]["email_display"])
print("Website:", e171["kontak_dan_website"]["website_url"])
print("Direktur:", e171["profil_lengkap"]["direktur"])
print("ICU vent:", e171["fasilitas_medis_berbukti"]["ruang_perawatan_kritis_terlapor"]["icu_dengan_ventilator"])
print("CT Scan in diagnostik:", "CT Scan" in e171["fasilitas_medis_berbukti"]["fasilitas_diagnostik_terlapor"])

print("\n=== RS-171 (Adam Malik) Sunday 10:00 WIB ===")
e171_sun = get_hospital_enrichment("rs-171", current_dt_wib=dt_sunday_morning)
print(json.dumps(e171_sun["jam_operasional"]["unit_operasional"][1]["status_sekarang"], indent=2))

print("\n=== RS-001 (OG Hospital - Unverified Clinic Hours) ===")
e001 = get_hospital_enrichment("rs-001", current_dt_wib=dt_monday_morning)
print(json.dumps(e001["jam_operasional"], indent=2))
print("Email:", e001["kontak_dan_website"]["email_display"])
print("Website status:", e001["kontak_dan_website"]["website_status"])
