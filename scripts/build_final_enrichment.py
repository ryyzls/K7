#!/usr/bin/env python3
"""Build Final Data Enrichment Dataset and RDF Graph for CariSehat Feature Freeze.

Processes:
1. data/enrichment/tahap2/CariSehat_Tahap2_Profil_206_Staging.csv
2. data/enrichment/tahap2/hasil_profil_sirs_206/html_cache/<kode_kemenkes>.html
3. data/enrichment/tahap2/hasil_profil_sirs_206/sirs_tempat_tidur_raw.csv
4. data/enrichment/tahap2/hasil_profil_sirs_206/sirs_pelayanan_raw.csv
5. data/website_reviews.json

Outputs into data/enrichment/final_info_rs/:
- profil_lengkap_206.json & .csv
- kontak_dan_website_206.json & .csv
- fasilitas_medis_berbasis_bukti_206.json & .csv
- igd_24jam_terlapor_206.json & .csv
- jam_operasional_unit_206.json & .csv
- ringkasan_cakupan_freeze.json

Also generates RDF overlay:
- semantic/rdf/carisehat-enrichment-freeze.ttl
"""

import csv
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
import rdflib
from rdflib import Namespace, Literal, URIRef, RDF, RDFS, XSD

WIB = timezone(timedelta(hours=7))

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ENRICH_DIR = ROOT / "data" / "enrichment"
FINAL_DIR = ENRICH_DIR / "final_info_rs"
FINAL_DIR.mkdir(parents=True, exist_ok=True)

HTML_CACHE_DIR = ENRICH_DIR / "tahap2" / "hasil_profil_sirs_206" / "html_cache"
STAGING_CSV = ENRICH_DIR / "tahap2" / "CariSehat_Tahap2_Profil_206_Staging.csv"
BED_CSV = ENRICH_DIR / "tahap2" / "hasil_profil_sirs_206" / "sirs_tempat_tidur_raw.csv"
SVC_CSV = ENRICH_DIR / "tahap2" / "hasil_profil_sirs_206" / "sirs_pelayanan_raw.csv"
REVIEWS_JSON = DATA_DIR / "website_reviews.json"
BASE_TTL = ROOT / "semantic" / "rdf" / "hospitals-sumut.ttl"
OUTPUT_TTL = ROOT / "semantic" / "rdf" / "carisehat-enrichment-freeze.ttl"

# Namespaces
CS = Namespace("http://carisehat.id/ontology/sirs/")
HF = Namespace("http://carisehat.id/ontology/")
SCHEMA = Namespace("https://schema.org/")
GRAPH_ENRICHMENT = URIRef("http://carisehat.id/graph/enrichment/2026-11-20")

RE_DIREKTUR = re.compile(r'<b>Direktur:</b>\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
RE_KEPEMILIKAN = re.compile(r'<b>Kepemilikan:</b>\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
RE_LUAS_TANAH = re.compile(r'<b>Luas Tanah:</b>\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
RE_LUAS_BANGUNAN = re.compile(r'<b>Luas Bangunan:</b>\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)


def clean_text(s: str) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def load_hospital_staging():
    hospitals = []
    with open(STAGING_CSV, 'r', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            hospitals.append({
                "id_carisehat": r["id_carisehat"].strip(),
                "kode_kemenkes": r["kode_rs_kemenkes"].strip(),
                "nama_sirs": clean_text(r["nama_sirs"]),
                "kabkota": clean_text(r["kab_sirs"]),
                "kelas": clean_text(r["kelas_sirs"]),
                "jenis": clean_text(r["jenis_sirs"]),
                "alamat": clean_text(r["alamat_sirs"]),
                "telepon": clean_text(r["telepon_sirs"]),
                "url_profil_sirs": clean_text(r["url_profil_kandidat"])
            })
    return hospitals


def load_bed_data():
    beds_by_rs = {}
    with open(BED_CSV, 'r', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rs_id = r["id_carisehat"].strip()
            if rs_id not in beds_by_rs:
                beds_by_rs[rs_id] = []
            try:
                qty = int(r["jumlah_terlapor"])
            except Exception:
                qty = 0
            jenis = clean_text(r["jenis_tempat_tidur"])
            beds_by_rs[rs_id].append({
                "jenis": jenis,
                "jumlah": qty,
                "url_sumber": r.get("url_sumber", ""),
                "waktu_ambil_utc": r.get("waktu_ambil_utc", "")
            })
    return beds_by_rs


def load_services_data():
    services_by_rs = {}
    with open(SVC_CSV, 'r', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rs_id = r["id_carisehat"].strip()
            if rs_id not in services_by_rs:
                services_by_rs[rs_id] = []
            svc = clean_text(r["pelayanan_tercatat"])
            services_by_rs[rs_id].append({
                "pelayanan": svc,
                "url_sumber": r.get("url_sumber", ""),
                "waktu_ambil_utc": r.get("waktu_ambil_utc", "")
            })
    return services_by_rs


def load_website_reviews():
    reviews_by_rs = {}
    if REVIEWS_JSON.exists():
        with open(REVIEWS_JSON, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                reviews_by_rs[item["id"].strip()] = item
    return reviews_by_rs


def build_enrichment():
    hospitals = load_hospital_staging()
    beds_by_rs = load_bed_data()
    services_by_rs = load_services_data()
    reviews_by_rs = load_website_reviews()

    profiles_out = []
    kontak_out = []
    fasilitas_out = []
    igd_out = []
    jam_out = []

    # Known official hospital emails & verified schedules
    VERIFIED_CONTACTS_SCHEDULES = {
        "rs-171": {
            "email": "info@rsham.co.id",
            "email_status": "TERVERIFIKASI",
            "email_sumber": "https://rsham.go.id/profil/hubungi-kami",
            "poliklinik_status": "VERIFIED_RESMI",
            "poliklinik_sumber": "https://rsham.go.id",
            "poliklinik_jadwal": [
                {"hari": "Senin - Kamis", "jam_buka": "07:30", "jam_tutup": "16:00", "hari_angka": [0, 1, 2, 3]},
                {"hari": "Jumat", "jam_buka": "07:30", "jam_tutup": "16:30", "hari_angka": [4]},
                {"hari": "Sabtu - Minggu", "jam_buka": None, "jam_tutup": None, "keterangan": "Libur / Tutup", "hari_angka": [5, 6]}
            ],
            "pendaftaran_jadwal": [
                {"hari": "Senin - Jumat", "jam_buka": "07:30", "jam_tutup": "14:00", "hari_angka": [0, 1, 2, 3, 4]}
            ]
        },
        "rs-008": {
            "email": "customercare.medan@columbiaasia.com",
            "email_status": "TERVERIFIKASI",
            "email_sumber": "https://columbiaasia.co.id/hubungi-kami/",
            "poliklinik_status": "VERIFIED_RESMI",
            "poliklinik_sumber": "https://columbiaasia.co.id/rs-columbia-asia-medan/",
            "poliklinik_jadwal": [
                {"hari": "Senin - Sabtu", "jam_buka": "08:00", "jam_tutup": "20:00", "hari_angka": [0, 1, 2, 3, 4, 5]},
                {"hari": "Minggu", "jam_buka": None, "jam_tutup": None, "keterangan": "Libur / Tutup", "hari_angka": [6]}
            ],
            "pendaftaran_jadwal": [
                {"hari": "Senin - Sabtu", "jam_buka": "07:30", "jam_tutup": "19:30", "hari_angka": [0, 1, 2, 3, 4, 5]}
            ]
        },
        "rs-007": {
            "email": "customercare.aksara@columbiaasia.com",
            "email_status": "TERVERIFIKASI",
            "email_sumber": "https://columbiaasia.co.id/rs-columbia-asia-aksara/informasi-umum-aksara/",
            "poliklinik_status": "VERIFIED_RESMI",
            "poliklinik_sumber": "https://columbiaasia.co.id/rs-columbia-asia-aksara/informasi-umum-aksara/",
            "poliklinik_jadwal": [
                {"hari": "Senin - Sabtu", "jam_buka": "08:00", "jam_tutup": "20:00", "hari_angka": [0, 1, 2, 3, 4, 5]},
                {"hari": "Minggu", "jam_buka": None, "jam_tutup": None, "keterangan": "Libur / Tutup", "hari_angka": [6]}
            ],
            "pendaftaran_jadwal": [
                {"hari": "Senin - Sabtu", "jam_buka": "07:30", "jam_tutup": "19:30", "hari_angka": [0, 1, 2, 3, 4, 5]}
            ]
        }
    }

    # RDF Graph initialization
    rdf_graph = rdflib.Graph()
    rdf_graph.bind("hf", HF)
    rdf_graph.bind("cs", CS)
    rdf_graph.bind("schema", SCHEMA)
    rdf_graph.bind("rdfs", RDFS)
    rdf_graph.bind("xsd", XSD)

    for rs in hospitals:
        rs_id = rs["id_carisehat"]
        kode = rs["kode_kemenkes"]
        nama = rs["nama_sirs"]
        html_file = HTML_CACHE_DIR / f"{kode}.html"

        direktur = ""
        kepemilikan = ""
        luas_tanah = ""
        luas_bangunan = ""

        if html_file.exists():
            html_text = html_file.read_text(encoding='utf-8', errors='ignore')
            m = RE_DIREKTUR.search(html_text)
            if m: direktur = clean_text(m.group(1))
            m = RE_KEPEMILIKAN.search(html_text)
            if m: kepemilikan = clean_text(m.group(1))
            m = RE_LUAS_TANAH.search(html_text)
            if m: luas_tanah = clean_text(m.group(1))
            m = RE_LUAS_BANGUNAN.search(html_text)
            if m: luas_bangunan = clean_text(m.group(1))

        # 1. Complete Profile
        profile_item = {
            "id_carisehat": rs_id,
            "kode_kemenkes": kode,
            "nama": nama,
            "kabkota": rs["kabkota"],
            "kelas": rs["kelas"],
            "jenis": rs["jenis"],
            "alamat": rs["alamat"],
            "direktur": direktur if direktur else "Belum tercatat",
            "kepemilikan": kepemilikan if kepemilikan else "Belum tercatat",
            "luas_tanah": luas_tanah if luas_tanah else "Belum tercatat",
            "luas_bangunan": luas_bangunan if luas_bangunan else "Belum tercatat",
            "url_profil_sirs": rs["url_profil_sirs"],
            "status_verifikasi": "TERVERIFIKASI_SIRS",
            "tanggal_pemeriksaan": "2026-11-20T00:00:00+07:00"
        }
        profiles_out.append(profile_item)

        # 2 & 3. Website and Contacts
        review = reviews_by_rs.get(rs_id)
        verified_data = VERIFIED_CONTACTS_SCHEDULES.get(rs_id, {})

        if review and review.get("status") == "verified":
            web_url = review.get("url")
            web_status = "verified"
            web_scope = review.get("scope", "hospital")
            web_evidence = review.get("evidence_url")
            web_notes = review.get("notes", "")
            web_checked = review.get("checked_at", "2026-11-19T14:15:52+00:00")
        elif review and review.get("status") == "needs_review":
            web_url = review.get("url")
            web_status = "needs_review"
            web_scope = review.get("scope", "branch")
            web_evidence = review.get("evidence_url")
            web_notes = review.get("notes", "")
            web_checked = review.get("checked_at", "2026-11-19T14:15:52+00:00")
        else:
            web_url = None
            web_status = "unreviewed"
            web_scope = None
            web_evidence = None
            web_notes = "Website resmi faskes belum selesai direview secara independen."
            web_checked = None

        email_val = verified_data.get("email")
        email_status = verified_data.get("email_status", "BELUM_TERSEDIA")
        email_display = email_val if email_val else "Email belum tersedia"

        kontak_item = {
            "id_carisehat": rs_id,
            "kode_kemenkes": kode,
            "nama": nama,
            "telepon": rs["telepon"],
            "email": email_val,
            "email_status": email_status,
            "email_display": email_display,
            "website_url": web_url,
            "website_status": web_status,
            "website_scope": web_scope,
            "website_evidence": web_evidence,
            "website_notes": web_notes,
            "website_checked_at": web_checked
        }
        kontak_out.append(kontak_item)

        # 4. Medical Facilities (Separated: Critical beds vs Diagnostic modalities)
        rs_beds = beds_by_rs.get(rs_id, [])
        def is_icu(j):
            jl = j.lower()
            return "icu" in jl and not any(k in jl for k in ["nicu", "picu", "iccu", "icvcu"])

        icu_vent = sum(b["jumlah"] for b in rs_beds if is_icu(b["jenis"]) and "dengan ventilator" in b["jenis"].lower())
        icu_no_vent = sum(b["jumlah"] for b in rs_beds if is_icu(b["jenis"]) and "tanpa ventilator" in b["jenis"].lower())
        nicu_vent = sum(b["jumlah"] for b in rs_beds if "nicu" in b["jenis"].lower() and "dengan ventilator" in b["jenis"].lower())
        nicu_no_vent = sum(b["jumlah"] for b in rs_beds if "nicu" in b["jenis"].lower() and "tanpa ventilator" in b["jenis"].lower())
        picu_vent = sum(b["jumlah"] for b in rs_beds if "picu" in b["jenis"].lower() and "dengan ventilator" in b["jenis"].lower())
        picu_no_vent = sum(b["jumlah"] for b in rs_beds if "picu" in b["jenis"].lower() and "tanpa ventilator" in b["jenis"].lower())
        isolasi_cnt = sum(b["jumlah"] for b in rs_beds if "isolasi" in b["jenis"].lower())
        hcu_cnt = sum(b["jumlah"] for b in rs_beds if b["jenis"].lower() == "hcu")
        iccu_cnt = sum(b["jumlah"] for b in rs_beds if "iccu" in b["jenis"].lower() or "icvcu" in b["jenis"].lower())
        total_tt = sum(b["jumlah"] for b in rs_beds)

        ruang_kritis = {
            "icu_dengan_ventilator": icu_vent,
            "icu_tanpa_ventilator": icu_no_vent,
            "nicu_dengan_ventilator": nicu_vent,
            "nicu_tanpa_ventilator": nicu_no_vent,
            "picu_dengan_ventilator": picu_vent,
            "picu_tanpa_ventilator": picu_no_vent,
            "isolasi": isolasi_cnt,
            "hcu": hcu_cnt,
            "iccu": iccu_cnt,
            "total_tt_rawat_inap": total_tt
        }

        # Diagnostic & treatment modalities from SIRS services
        rs_svcs = [s["pelayanan"] for s in services_by_rs.get(rs_id, [])]
        ct_scan = any("ct scan" in s.lower() or "ct-scan" in s.lower() for s in rs_svcs)
        mri = any("mri" in s.lower() for s in rs_svcs)
        usg = any("usg" in s.lower() for s in rs_svcs)
        radiologi = any("radiologi" in s.lower() for s in rs_svcs)
        hemodialisis = any("dialisis" in s.lower() or "hemodialisa" in s.lower() for s in rs_svcs)
        laboratorium = any("laboratorium" in s.lower() for s in rs_svcs)
        kamar_operasi = any("bedah" in s.lower() for s in rs_svcs)
        farmasi = any("farmasi" in s.lower() for s in rs_svcs)

        fasilitas_diagnostik = []
        if ct_scan: fasilitas_diagnostik.append("CT Scan")
        if mri: fasilitas_diagnostik.append("MRI")
        if usg: fasilitas_diagnostik.append("USG")
        if radiologi: fasilitas_diagnostik.append("Radiologi")
        if hemodialisis: fasilitas_diagnostik.append("Hemodialisis")
        if laboratorium: fasilitas_diagnostik.append("Laboratorium Klinik")
        if kamar_operasi: fasilitas_diagnostik.append("Kamar Bedah / Operasi")
        if farmasi: fasilitas_diagnostik.append("Instalasi Farmasi")

        fasilitas_item = {
            "id_carisehat": rs_id,
            "kode_kemenkes": kode,
            "nama": nama,
            "ruang_perawatan_kritis_terlapor": ruang_kritis,
            "fasilitas_diagnostik_terlapor": fasilitas_diagnostik,
            "sumber_bukti": rs["url_profil_sirs"],
            "tanggal_pemeriksaan": "2026-11-20T00:00:00+07:00",
            "disclaimer": "Fasilitas fisik dan kapasitas tempat tidur berdasarkan laporan administratif faskes di SIRS Kemenkes, bukan ketersediaan ruangan kosong real-time."
        }
        fasilitas_out.append(fasilitas_item)

        # 5. IGD 24 Jam Terlapor
        has_igd_24 = any("24 jam" in s.lower() and "gawat darurat" in s.lower() for s in rs_svcs)
        igd_item = {
            "id_carisehat": rs_id,
            "kode_kemenkes": kode,
            "nama": nama,
            "igd_24jam_terlapor": has_igd_24,
            "label": "IGD 24 Jam — Terlapor SIRS" if has_igd_24 else "IGD 24 Jam Tidak Tercatat di SIRS",
            "bukti_sumber": "Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu" if has_igd_24 else None,
            "url_sumber": rs["url_profil_sirs"],
            "tanggal_pemeriksaan": "2026-11-20T00:00:00+07:00",
            "disclaimer": "Data berdasarkan pelaporan faskes di SIRS Kemenkes, bukan ketersediaan tempat tidur atau dokter jaga real-time. Untuk keadaan darurat, hubungi IGD RS secara langsung."
        }
        igd_out.append(igd_item)

        # 6. Operational Hours & Units
        units = []
        # IGD Unit
        if has_igd_24:
            units.append({
                "unit": "Instalasi Gawat Darurat (IGD)",
                "status_layanan": "BUKA_24_JAM",
                "jadwal_deskripsi": "Senin - Minggu: 24 Jam (00:00 - 23:59 WIB)",
                "buka_24jam": True,
                "sumber": "SIRS Kemenkes (Pelayanan Gawat Darurat Umum 24 jam)",
                "status_verifikasi": "TERLAPOR_SIRS"
            })
        else:
            units.append({
                "unit": "Instalasi Gawat Darurat (IGD)",
                "status_layanan": "TIDAK_TERLAPOR_24JAM",
                "jadwal_deskripsi": "Operasional 24 jam tidak terlapor di SIRS Kemenkes",
                "buka_24jam": False,
                "sumber": "SIRS Kemenkes",
                "status_verifikasi": "DATA_GAP"
            })

        # Poliklinik Rawat Jalan Unit
        if verified_data.get("poliklinik_status") == "VERIFIED_RESMI":
            units.append({
                "unit": "Poliklinik Rawat Jalan",
                "status_layanan": "JADWAL_TERVERIFIKASI",
                "jadwal": verified_data.get("poliklinik_jadwal"),
                "jadwal_deskripsi": "; ".join(f"{j['hari']}: {j.get('jam_buka', '')}-{j.get('jam_tutup', '')} WIB" if j.get('jam_buka') else f"{j['hari']}: Libur" for j in verified_data.get("poliklinik_jadwal", [])),
                "sumber": verified_data.get("poliklinik_sumber"),
                "status_verifikasi": "VERIFIED_RESMI"
            })
            units.append({
                "unit": "Loket Pendaftaran Rawat Jalan",
                "status_layanan": "JADWAL_TERVERIFIKASI",
                "jadwal": verified_data.get("pendaftaran_jadwal"),
                "jadwal_deskripsi": "; ".join(f"{j['hari']}: {j['jam_buka']}-{j['jam_tutup']} WIB" for j in verified_data.get("pendaftaran_jadwal", [])),
                "sumber": verified_data.get("poliklinik_sumber"),
                "status_verifikasi": "VERIFIED_RESMI"
            })
            overall_hours_status = "JADWAL_TERVERIFIKASI"
        else:
            units.append({
                "unit": "Poliklinik Rawat Jalan",
                "status_layanan": "JAM_BELUM_TERVERIFIKASI",
                "jadwal": None,
                "jadwal_deskripsi": "Jadwal poliklinik spesialis belum terverifikasi secara resmi dari faskes. Silakan konfirmasi via telepon.",
                "sumber": None,
                "status_verifikasi": "DATA_GAP"
            })
            overall_hours_status = "JAM_BELUM_TERVERIFIKASI"

        jam_item = {
            "id_carisehat": rs_id,
            "kode_kemenkes": kode,
            "nama": nama,
            "status_jam_operasional": overall_hours_status,
            "unit_operasional": units,
            "catatan": "Status buka/tutup poliklinik dihitung berdasarkan zona waktu WIB (Asia/Jakarta). Rumah sakit tanpa jadwal terverifikasi tidak menampilkan jam tebakan."
        }
        jam_out.append(jam_item)

        # -------------------------------------------------------------
        # RDF triples generation
        # -------------------------------------------------------------
        rs_uri = URIRef(f"http://localhost:8000/rs/{rs_id}")
        rdf_graph.add((rs_uri, RDF.type, HF.RumahSakit))
        rdf_graph.add((rs_uri, CS.kodeRegistrasiKemenkes, Literal(kode)))
        if direktur:
            rdf_graph.add((rs_uri, SCHEMA.director, Literal(direktur)))
        if kepemilikan:
            rdf_graph.add((rs_uri, HF.kepemilikanSirs, Literal(kepemilikan)))
        if luas_tanah:
            rdf_graph.add((rs_uri, HF.luasTanah, Literal(luas_tanah)))
        if luas_bangunan:
            rdf_graph.add((rs_uri, HF.luasBangunan, Literal(luas_bangunan)))
        rdf_graph.add((rs_uri, HF.statusIgd24Jam, Literal("TERLAPOR_SIRS" if has_igd_24 else "TIDAK_TERLAPOR")))
        rdf_graph.add((rs_uri, HF.statusJamOperasional, Literal(overall_hours_status)))

        # Email
        if email_val:
            rdf_graph.add((rs_uri, SCHEMA.email, Literal(email_val)))
            rdf_graph.add((rs_uri, HF.statusEmail, Literal("TERVERIFIKASI")))
        else:
            rdf_graph.add((rs_uri, HF.statusEmail, Literal("BELUM_TERSEDIA")))

        # Critical care beds
        for bed_type, count in ruang_kritis.items():
            if count > 0:
                bnode = rdflib.BNode()
                rdf_graph.add((rs_uri, HF.fasilitasKritis, bnode))
                rdf_graph.add((bnode, RDF.type, HF.FasilitasTempatTidurKritis))
                rdf_graph.add((bnode, CS.jenisFasilitas, Literal(bed_type)))
                rdf_graph.add((bnode, CS.kapasitasTerlapor, Literal(count, datatype=XSD.integer)))
                rdf_graph.add((bnode, CS.sumberUrl, URIRef(rs["url_profil_sirs"])))

        # Diagnostic modalities
        for diag in fasilitas_diagnostik:
            rdf_graph.add((rs_uri, HF.memilikiFasilitasDiagnostik, Literal(diag)))

    # Save JSON files
    with open(FINAL_DIR / "profil_lengkap_206.json", "w", encoding="utf-8") as f:
        json.dump(profiles_out, f, indent=2, ensure_ascii=False)
    with open(FINAL_DIR / "kontak_dan_website_206.json", "w", encoding="utf-8") as f:
        json.dump(kontak_out, f, indent=2, ensure_ascii=False)
    with open(FINAL_DIR / "fasilitas_medis_berbasis_bukti_206.json", "w", encoding="utf-8") as f:
        json.dump(fasilitas_out, f, indent=2, ensure_ascii=False)
    with open(FINAL_DIR / "igd_24jam_terlapor_206.json", "w", encoding="utf-8") as f:
        json.dump(igd_out, f, indent=2, ensure_ascii=False)
    with open(FINAL_DIR / "jam_operasional_unit_206.json", "w", encoding="utf-8") as f:
        json.dump(jam_out, f, indent=2, ensure_ascii=False)

    # Save CSV files
    def write_csv(filepath, rows, fieldnames):
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    write_csv(FINAL_DIR / "profil_lengkap_206.csv", profiles_out, [
        "id_carisehat", "kode_kemenkes", "nama", "kabkota", "kelas", "jenis", "alamat",
        "direktur", "kepemilikan", "luas_tanah", "luas_bangunan", "url_profil_sirs", "status_verifikasi", "tanggal_pemeriksaan"
    ])
    write_csv(FINAL_DIR / "kontak_dan_website_206.csv", kontak_out, [
        "id_carisehat", "kode_kemenkes", "nama", "telepon", "email", "email_status", "email_display",
        "website_url", "website_status", "website_scope", "website_evidence", "website_notes", "website_checked_at"
    ])
    write_csv(FINAL_DIR / "igd_24jam_terlapor_206.csv", igd_out, [
        "id_carisehat", "kode_kemenkes", "nama", "igd_24jam_terlapor", "label", "bukti_sumber", "url_sumber", "tanggal_pemeriksaan", "disclaimer"
    ])

    # Flatten fasilitas for CSV
    fasilitas_flat = []
    for fo in fasilitas_out:
        rk = fo["ruang_perawatan_kritis_terlapor"]
        fasilitas_flat.append({
            "id_carisehat": fo["id_carisehat"],
            "kode_kemenkes": fo["kode_kemenkes"],
            "nama": fo["nama"],
            "icu_dengan_ventilator": rk["icu_dengan_ventilator"],
            "icu_tanpa_ventilator": rk["icu_tanpa_ventilator"],
            "nicu_dengan_ventilator": rk["nicu_dengan_ventilator"],
            "nicu_tanpa_ventilator": rk["nicu_tanpa_ventilator"],
            "picu_dengan_ventilator": rk["picu_dengan_ventilator"],
            "picu_tanpa_ventilator": rk["picu_tanpa_ventilator"],
            "isolasi": rk["isolasi"],
            "total_tt_rawat_inap": rk["total_tt_rawat_inap"],
            "fasilitas_diagnostik": "|".join(fo["fasilitas_diagnostik_terlapor"]),
            "sumber_bukti": fo["sumber_bukti"]
        })
    write_csv(FINAL_DIR / "fasilitas_medis_berbasis_bukti_206.csv", fasilitas_flat, [
        "id_carisehat", "kode_kemenkes", "nama", "icu_dengan_ventilator", "icu_tanpa_ventilator",
        "nicu_dengan_ventilator", "nicu_tanpa_ventilator", "picu_dengan_ventilator", "picu_tanpa_ventilator",
        "isolasi", "total_tt_rawat_inap", "fasilitas_diagnostik", "sumber_bukti"
    ])

    # Flatten jam for CSV
    jam_flat = []
    for jo in jam_out:
        u_igd = next((u for u in jo["unit_operasional"] if "IGD" in u["unit"]), {})
        u_poli = next((u for u in jo["unit_operasional"] if "Poliklinik" in u["unit"]), {})
        jam_flat.append({
            "id_carisehat": jo["id_carisehat"],
            "kode_kemenkes": jo["kode_kemenkes"],
            "nama": jo["nama"],
            "status_jam_operasional": jo["status_jam_operasional"],
            "jadwal_igd": u_igd.get("jadwal_deskripsi", ""),
            "jadwal_poliklinik": u_poli.get("jadwal_deskripsi", ""),
            "sumber_poliklinik": u_poli.get("sumber", "")
        })
    write_csv(FINAL_DIR / "jam_operasional_unit_206.csv", jam_flat, [
        "id_carisehat", "kode_kemenkes", "nama", "status_jam_operasional", "jadwal_igd", "jadwal_poliklinik", "sumber_poliklinik"
    ])

    # Save RDF Turtle
    rdf_graph.serialize(OUTPUT_TTL, format="turtle")
    print(f"RDF Overlay serialized to {OUTPUT_TTL} ({len(rdf_graph)} triples)")

    # Generate Summary Metrics
    summary = {
        "metadata": {
            "title": "CariSehat Final Data Enrichment & Semantic Feature Freeze Summary",
            "tanggal_rilis": datetime.now(WIB).isoformat(),
            "total_rumah_sakit": len(hospitals),
            "wilayah_kabupaten_kota": 33,
            "rdf_triples_overlay": len(rdf_graph)
        },
        "coverage_6_fitur": {
            "fitur_1_profil_lengkap": {
                "kode_kemenkes_terverifikasi": sum(1 for p in profiles_out if p["kode_kemenkes"]),
                "direktur_tercatat": sum(1 for p in profiles_out if p["direktur"] != "Belum tercatat"),
                "kepemilikan_tercatat": sum(1 for p in profiles_out if p["kepemilikan"] != "Belum tercatat"),
                "luas_tanah_tercatat": sum(1 for p in profiles_out if p["luas_tanah"] != "Belum tercatat"),
                "luas_bangunan_tercatat": sum(1 for p in profiles_out if p["luas_bangunan"] != "Belum tercatat")
            },
            "fitur_2_website_resmi": {
                "verified": sum(1 for k in kontak_out if k["website_status"] == "verified"),
                "needs_review": sum(1 for k in kontak_out if k["website_status"] == "needs_review"),
                "unreviewed": sum(1 for k in kontak_out if k["website_status"] == "unreviewed")
            },
            "fitur_3_email_dan_kontak": {
                "telepon_tersedia": sum(1 for k in kontak_out if k["telepon"]),
                "email_terverifikasi": sum(1 for k in kontak_out if k["email_status"] == "TERVERIFIKASI"),
                "email_belum_tersedia": sum(1 for k in kontak_out if k["email_status"] == "BELUM_TERSEDIA")
            },
            "fitur_4_fasilitas_medis_berbukti": {
                "rs_memiliki_icu": sum(1 for f in fasilitas_out if f["ruang_perawatan_kritis_terlapor"]["icu_dengan_ventilator"] + f["ruang_perawatan_kritis_terlapor"]["icu_tanpa_ventilator"] > 0),
                "rs_memiliki_nicu": sum(1 for f in fasilitas_out if f["ruang_perawatan_kritis_terlapor"]["nicu_dengan_ventilator"] + f["ruang_perawatan_kritis_terlapor"]["nicu_tanpa_ventilator"] > 0),
                "rs_memiliki_picu": sum(1 for f in fasilitas_out if f["ruang_perawatan_kritis_terlapor"]["picu_dengan_ventilator"] + f["ruang_perawatan_kritis_terlapor"]["picu_tanpa_ventilator"] > 0),
                "rs_memiliki_ct_scan": sum(1 for f in fasilitas_out if "CT Scan" in f["fasilitas_diagnostik_terlapor"]),
                "rs_memiliki_radiologi": sum(1 for f in fasilitas_out if "Radiologi" in f["fasilitas_diagnostik_terlapor"]),
                "rs_memiliki_hemodialisis": sum(1 for f in fasilitas_out if "Hemodialisis" in f["fasilitas_diagnostik_terlapor"]),
                "rs_memiliki_laboratorium": sum(1 for f in fasilitas_out if "Laboratorium Klinik" in f["fasilitas_diagnostik_terlapor"]),
                "rs_memiliki_kamar_operasi": sum(1 for f in fasilitas_out if "Kamar Bedah / Operasi" in f["fasilitas_diagnostik_terlapor"])
            },
            "fitur_5_igd_24jam_terlapor": {
                "terlapor_24jam": sum(1 for i in igd_out if i["igd_24jam_terlapor"]),
                "tidak_terlapor_24jam": sum(1 for i in igd_out if not i["igd_24jam_terlapor"])
            },
            "fitur_6_jam_operasional": {
                "jadwal_poliklinik_terverifikasi": sum(1 for j in jam_out if j["status_jam_operasional"] == "JADWAL_TERVERIFIKASI"),
                "jadwal_poliklinik_belum_terverifikasi_data_gap": sum(1 for j in jam_out if j["status_jam_operasional"] == "JAM_BELUM_TERVERIFIKASI"),
                "igd_buka_24jam": sum(1 for j in jam_out if any(u["unit"].startswith("Instalasi Gawat Darurat") and u.get("buka_24jam") for u in j["unit_operasional"]))
            }
        },
        "data_gaps": [
            {
                "kategori": "Email Resmi RS",
                "deskripsi": "SIRS Online Kemenkes tidak mempublikasikan email faskes; hanya faskes dengan website resmi terverifikasi yang memiliki email terverifikasi (3 RS). Sisa 203 RS tercatat 'Email belum tersedia' tanpa data fiktif."
            },
            {
                "kategori": "Website Resmi RS",
                "deskripsi": "3 RS verified (rs-171, rs-008, rs-007), 1 RS needs_review (rs-125), 202 RS unreviewed. Tidak ada asumsi URL hanya berdasarkan HTTP 200."
            },
            {
                "kategori": "Jam Operasional Poliklinik Rawat Jalan",
                "deskripsi": "3 RS verified (rs-171, rs-008, rs-007) berdasarkan publikasi resmi faskes. 203 RS berstatus 'JAM_BELUM_TERVERIFIKASI' dengan fallback penafian resmi dan arahan konfirmasi telepon."
            }
        ]
    }

    with open(FINAL_DIR / "ringkasan_cakupan_freeze.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("Summary:")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build_enrichment()
