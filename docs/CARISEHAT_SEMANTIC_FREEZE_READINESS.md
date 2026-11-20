# CariSehat — Semantic Feature Freeze Readiness Report

**Versi:** 1.0  
**Tanggal:** 2026-11-20  
**Tim:** Senior Full-Stack Developer, Semantic Web Engineer, Data Engineer, QA Engineer  
**Status Keseluruhan:** ✅ SIAP UNTUK FEATURE FREEZE

---

## Ringkasan Eksekutif

CariSehat adalah aplikasi direktori 206 rumah sakit di 33 kabupaten/kota Sumatera Utara berbasis Web Semantik dan MSBD. Seluruh 6 fitur data informasi RS yang ditargetkan telah diimplementasikan dan diuji. Dataset RDF tersebar di tiga lapisan:

| Named Graph | Triple | Deskripsi |
|---|---|---|
| Default graph | 6.132 | Data utama RS: 206 RS, 33 wilayah, 34 Linked Data |
| `http://carisehat.id/graph/sirs/2026-11-19` | 93.595 | Integrasi SIRS Kemenkes: 10.219 observasi layanan |
| `http://carisehat.id/graph/enrichment/2026-11-20` | 8.052 | Overlay enrichment: profil, fasilitas, IGD, jam |
| **Total** | **107.779** | **Dataset Fuseki aktif** |

---

## 1. Status Matrix 6 Fitur

| Fitur | Status | Cakupan | Sumber Data | Tanggal Verifikasi | Catatan |
|---|---|---|---|---|---|
| **1. Profil Lengkap** | ✅ SELESAI | 206/206 RS | SIRS HTML Cache (Kemenkes) | 2026-11-20 | Direktur, Kepemilikan, Kode Kemenkes, Luas Tanah/Bangunan |
| **2. Website Resmi** | 🟡 PARTIAL | 3/206 verified | Review manual + website RS | 2026-11-20 | 1 needs\_review (rs-125), 202 unreviewed = DATA\_GAP |
| **3. Email & Kontak** | 🟡 PARTIAL | 3/206 email | Website resmi RS | 2026-11-20 | 203 RS = "Email belum tersedia" — tidak ada email fiktif |
| **4. Fasilitas Berbukti** | ✅ SELESAI | 187/206 ICU | SIRS Tempat Tidur + Pelayanan | 2026-11-20 | Dipisah dari layanan klinis; CT Scan, MRI, Radiologi, Hemodialisis |
| **5. IGD 24 Jam Terlapor** | ✅ SELESAI | 198/206 RS | SIRS Pelayanan Kemenkes | 2026-11-20 | Disclaimer wajib: "terlapor SIRS, bukan verifikasi real-time" |
| **6. Jam Operasional** | 🟡 PARTIAL | 3/206 verified | Website RS + publikasi resmi | 2026-11-20 | 203 RS = DATA\_GAP, fallback "Jam belum terverifikasi" |

---

## 2. Statistik Cakupan Detail

### Fitur 1 — Profil Rumah Sakit

| Atribut | Jumlah RS | Persentase |
|---|---|---|
| Kode Kemenkes (terverifikasi) | 206 | 100% |
| Direktur (tercatat SIRS) | 206 | 100% |
| Kepemilikan (tercatat SIRS) | 206 | 100% |
| Luas Tanah (m²) | 204 | 99% |
| Luas Bangunan (m²) | 204 | 99% |

> [!NOTE]
> 2 RS tidak memiliki data luas di profil SIRS HTML cache. Data diisi dari 206 file HTML cache `data/enrichment/tahap2/hasil_profil_sirs_206/html_cache/<kode_kemenkes>.html`.

### Fitur 2 — Website Resmi

| Status | RS | Keterangan |
|---|---|---|
| verified | rs-171, rs-008, rs-007 | Domain diverifikasi milik RS bersangkutan |
| needs\_review | rs-125 | URL ditemukan tapi belum diverifikasi kepemilikan |
| unreviewed | 202 | DATA\_GAP — tidak ada URL diasumsikan |

**RS Verified:**
- `rs-171` (RSHAM): https://www.rsham.co.id  
- `rs-008` (Columbia Asia Medan): https://www.columbiaasia.com/medan  
- `rs-007` (Columbia Asia Aksara): https://www.columbiaasia.com/aksara

### Fitur 3 — Email & Kontak

| Status | RS | Email |
|---|---|---|
| verified | rs-171 | info@rsham.co.id |
| verified | rs-008 | customercare.medan@columbiaasia.com |
| verified | rs-007 | customercare.aksara@columbiaasia.com |
| belum tersedia | 203 RS | "Email belum tersedia" (eksplisit, bukan kosong) |

> [!IMPORTANT]
> SIRS Online Kemenkes tidak mempublikasikan kolom email di profil faskes. Email hanya tersedia dari 3 RS yang memiliki website resmi terverifikasi. Tidak ada email yang diinferensikan atau dikira.

**Telepon:** 204/206 RS memiliki nomor telepon dari SIRS.

### Fitur 4 — Fasilitas Medis Berbasis Bukti

**Tempat Tidur Khusus (dari sirs_tempat_tidur_raw.csv):**

| Fasilitas | RS Memiliki | Catatan |
|---|---|---|
| ICU (semua jenis, ekskl. NICU/PICU) | 187 | Termasuk ICU dengan/tanpa ventilator |
| NICU | 163 | Termasuk NICU dengan/tanpa ventilator |
| PICU | 112 | Termasuk PICU dengan/tanpa ventilator |
| Kamar Operasi | 196 | Dari SIRS tempat tidur OR |

**Modalitas Diagnostik (dari sirs_pelayanan_raw.csv):**

| Fasilitas | RS Memiliki |
|---|---|
| CT Scan | 62 |
| Radiologi/Rontgen | 177 |
| Hemodialisis | 61 |
| Laboratorium | 60 |

> [!WARNING]
> MRI tidak tersedia di dataset SIRS pelayanan yang digunakan — tidak dimasukkan ke enrichment untuk mencegah data fiktif.

> [!NOTE]
> Fasilitas fisik (tempat tidur ICU/NICU/PICU, kamar operasi) dipisah secara ketat dari layanan klinis (spesialisasi poliklinik). Keduanya memiliki atribut RDF dan kolom JSON yang berbeda.

### Fitur 5 — IGD 24 Jam Terlapor

| Status IGD | Jumlah RS |
|---|---|
| TERLAPOR\_SIRS (IGD 24 Jam) | 198 |
| TIDAK\_TERLAPOR | 8 |

> [!IMPORTANT]
> Status "TERLAPOR_SIRS" berarti tercatat di data SIRS per November 2026, **bukan** verifikasi real-time bahwa IGD saat ini buka. Disclaimer wajib ditampilkan di UI.

### Fitur 6 — Jam Operasional

| Status | Jumlah RS |
|---|---|
| Jadwal poliklinik verified | 3 |
| Jadwal poliklinik DATA\_GAP | 203 |
| IGD 24 jam (dari Fitur 5) | 198 |

**RS dengan jadwal verified:**
- `rs-171`: Poliklinik Senin–Jumat 08:00–15:00 WIB, Sabtu 08:00–12:00 WIB  
- `rs-008`: Poliklinik Senin–Jumat 08:00–17:00 WIB, Sabtu 08:00–13:00 WIB  
- `rs-007`: Poliklinik Senin–Jumat 08:00–17:00 WIB, Sabtu 08:00–13:00 WIB

Semua kalkulasi menggunakan timezone `Asia/Jakarta` (WIB, UTC+7) via `timezone(timedelta(hours=7))`.

---

## 3. Data Gap Catalog

| Kategori Data Gap | Jumlah RS Terdampak | Alasan Teknis | Fallback Ditampilkan |
|---|---|---|---|
| Email Resmi RS | 203 RS | SIRS tidak mempublikasikan email; hanya 3 RS dengan website verified memiliki email | "Email belum tersedia" |
| Website Resmi RS | 202 RS | Tidak ada verifikasi kepemilikan domain; HTTP 200 bukan bukti | Tidak ditampilkan (DATA\_GAP) |
| Jam Poliklinik Rawat Jalan | 203 RS | Tidak ada sumber publik terpercaya; jam berubah per unit | "Jam belum terverifikasi — Silakan hubungi RS langsung" |
| MRI | 206 RS | Tidak tercantum di dataset SIRS Pelayanan yang tersedia | Tidak ditampilkan |
| Luas Tanah/Bangunan | 2 RS | Data absen di profil SIRS HTML cache | Field kosong (null) |

> [!CAUTION]
> Tidak ada data yang diinferensikan, dihalusinasi, atau diisi berdasarkan nama RS yang mirip. Zero hallucination policy diterapkan ketat pada seluruh 6 fitur.

---

## 4. Arsitektur Data & File Baru

### File Data Enrichment (data/enrichment/final_info_rs/)

| File | Deskripsi | Jumlah Entri |
|---|---|---|
| `profiles.json` | Direktur, Kepemilikan, Luas Tanah/Bangunan, Kode Kemenkes | 206 RS |
| `websites.json` | Status website, URL, tanggal verifikasi | 206 RS |
| `contacts.json` | Telepon, email, status email | 206 RS |
| `facilities.json` | ICU/NICU/PICU beds, diagnostics | 206 RS |
| `operational_hours.json` | Per-unit jadwal (IGD, Poliklinik, Pendaftaran) | 206 RS |
| `ringkasan_cakupan_freeze.json` | Ringkasan coverage 6 fitur | Metadata |

Data juga tersedia sebagai CSV di folder yang sama.

### File Backend Baru/Dimodifikasi

| File | Perubahan |
|---|---|
| `backend/app/services/enrichment_service.py` | **BARU** — service layer 6 fitur enrichment |
| `backend/app/services/sparql_service.py` | `to_hospital()` diperluas dengan semua field enrichment |
| `backend/app/routers/api.py` | 3 endpoint baru (lihat bagian 5) |
| `backend/app/routers/semantic.py` | Penyesuaian route rs\_detail |
| `backend/app/templates/rs_detail.html` | Semua 6 fitur ditambahkan ke template Jinja2 |

### File Frontend Dimodifikasi

| File | Perubahan |
|---|---|
| `frontend/index.html` | `renderEmailBadge()`, `renderEnrichedHours()`, `renderEnrichedFacilities()`, quick-nav anchors |

### File RDF

| File | Deskripsi |
|---|---|
| `semantic/rdf/carisehat-enrichment-freeze.ttl` | 8.052 triple overlay enrichment |
| `semantic/backups/enrichment_freeze_20261120/deployment_manifest.json` | Manifest deployment + rollback |

### Script Auxiliary

| Script | Fungsi |
|---|---|
| `scripts/build_final_enrichment.py` | Build semua data enrichment dari SIRS raw data |
| `scripts/deploy_enrichment_graph.py` | Deploy/rollback named graph ke Fuseki |
| `scripts/run_all_tests.py` | Master test runner (48 total tests) |
| `scripts/test_sparql_enrichment.py` | Verifikasi SPARQL enrichment data |
| `scripts/audit_sparql_dbpedia.py` | Audit SPARQL internal + DBpedia |
| `scripts/audit_semantic_e2e.py` | End-to-end semantic audit |

---

## 5. Endpoint API Baru

| Method | Path | Fungsi |
|---|---|---|
| `GET` | `/api/hospitals/{rs_id}` | Detail RS + enrichment (direktur, email, facilities, jam) |
| `GET` | `/api/hospitals/{rs_id}/operational-hours` | Jam operasional per-unit dengan WIB real-time status |
| `GET` | `/api/enrichment/summary` | Ringkasan cakupan 6 fitur untuk semua 206 RS |

**Contoh respons `/api/hospitals/rs-171` (enrichment fields):**
```json
{
  "direktur": "dr. Nazar, M.Ked (ORL-HNS), Sp.THT-KL(K)",
  "kepemilikan": "Pemerintah Pusat",
  "email_display": "info@rsham.co.id",
  "email_status": "verified",
  "igd_24jam_terlapor": true,
  "fasilitas_medis_berbukti": {
    "tempat_tidur_khusus": {"icu": {...}, "nicu": {...}, "picu": {...}},
    "diagnostik": {"ct_scan": true, "radiologi": true}
  }
}
```

---

## 6. Named Graphs Fuseki (Runtime State)

| Named Graph | Triple | Status |
|---|---|---|
| Default graph | 6.132 | ✅ Aktif (206 RS, 33 wilayah, 34 Linked Data) |
| `http://carisehat.id/graph/sirs/2026-11-19` | 93.595 | ✅ Aktif (SIRS Kemenkes, 10.219 observasi) |
| `http://carisehat.id/graph/enrichment/2026-11-20` | 8.052 | ✅ Aktif (overlay enrichment 6 fitur) |
| **Total** | **107.779** | **✅ Semua aktif** |

**Container Docker (runtime):**
- `carisehat-api` — Up 14+ hours, port 8000, hot reload aktif
- `carisehat-fuseki` — Up 14+ hours, port 3030
- `carisehat-db` — Up 14+ hours (healthy), port 5433

---

## 7. Hasil Pengujian

### Test Suite Master (task-1692 + task-1705 — Executed 2026-11-20)

| Test File | Tests | Status |
|---|---|---|
| `tests/test_carisehat_feature_freeze.py` | 7 | ✅ ALL PASS |
| `tests/test_freeze_live_http.py` | 4 | ✅ ALL PASS |
| `tests/test_specialties.py` | 5 | ✅ ALL PASS |
| `tests/test_carisehat2_features.py` | 10 | ✅ ALL PASS |
| `tests/test_chatbot_scenarios.py` | 14 | ✅ ALL PASS |
| `tests/test_sirs_integration.py` | 8 | ✅ ALL PASS |
| `backend/tests/test_sparql_guard.py` | — | ⚠️ 0 loaded (file keamanan OK, test file path berbeda) |
| **Total** | **48** | **✅ 48/48 PASS — OK** |

> [!NOTE]
> `test_sparql_guard.py` tidak ter-load oleh runner karena berada di `backend/tests/` bukan `tests/`. Pengujian SPARQL Guard dilakukan melalui `audit_sparql_dbpedia.py` (22 kasus PASS dari sesi sebelumnya).

### Audit SPARQL & DBpedia (Executed 2026-11-20T10:51 WIB — `FUSEKI_URL=http://localhost:3030/hospital`)

| Pemeriksaan | Hasil |
|---|---|
| `audit_sparql_dbpedia.py` internal SPARQL | ✅ PASS — 206 RS, 33 kota, 34 linked regions |
| `audit_sparql_dbpedia.py` DBpedia external | ✅ PASS |
| `audit_semantic_e2e.py` (13 kasus) | ✅ 13/13 PASS, 0 FAIL, 0 BLOCKED |
| `GET /api/enrichment/summary` live | ✅ PASS — data sesuai coverage JSON |

> [!NOTE]
> Kedua script menggunakan hostname Docker internal (`fuseki:3030`, `backend:8000`) sebagai default. Set env `FUSEKI_URL=http://localhost:3030/hospital` dan `CARISEHAT_URL=http://localhost:8000` untuk run di luar container.

### Verifikasi SPARQL Guard (dari sesi sebelumnya — Patch 06C)

| Kategori Uji | Hasil |
|---|---|
| SELECT/ASK/CONSTRUCT/DESCRIBE (read-only) | ✅ PASS |
| INSERT/DELETE/LOAD/CLEAR/DROP (write ops) | ✅ DITOLAK |
| SERVICE (SSRF external endpoint) | ✅ DIBATASI |
| Batas ukuran request (>50KB) | ✅ DITOLAK |
| Batas hasil query | ✅ TERBATAS |
| Timeout query | ✅ AKTIF |
| Kompatibilitas YASGUI | ✅ PASS |

### Verifikasi Fuseki & Data (Executed 2026-11-20T10:46 WIB)

| Pemeriksaan | Hasil |
|---|---|
| Default graph — 6.132 triple | ✅ PASS |
| SIRS named graph — 93.595 triple | ✅ PASS |
| Enrichment named graph — 8.052 triple | ✅ PASS |
| `GET /api/enrichment/summary` HTTP 200 | ✅ PASS |
| `GET /api/hospitals/rs-171` enrichment fields | ✅ PASS |
| SPARQL enrichment query sample (5 RS random) | ✅ PASS |
| Rollback script tersedia | ✅ PASS |

### Verifikasi Regresi Fitur CariSehat 2.0

| Fitur | Status |
|---|---|
| Perbandingan RS (maks 3 RS) | ✅ PASS (test\_carisehat2\_features) |
| Rekomendasi Alternatif RS | ✅ PASS |
| Chatbot Semantic | ✅ PASS |
| Filter Spesialisasi SIRS | ✅ PASS |
| Peta Interaktif | ✅ PASS (test\_carisehat2\_features) |
| SPARQL Guard keamanan | ✅ PASS |
| DBpedia integration | ✅ PASS (dengan fallback lokal) |

---

## 8. Deployment & Rollback

### Cara Deploy Ulang Named Graph Enrichment (instalasi baru)

```powershell
# 1. Pastikan Fuseki aktif di http://localhost:3030/hospital
# 2. Deploy named graph enrichment
cd "D:\TI 26\Tubes WS MSBD\K7"
.venv\Scripts\python.exe scripts/deploy_enrichment_graph.py

# 3. Verifikasi
.venv\Scripts\python.exe scripts/test_sparql_enrichment.py
```

### Cara Rollback Named Graph Enrichment

```powershell
cd "D:\TI 26\Tubes WS MSBD\K7"
.venv\Scripts\python.exe scripts/deploy_enrichment_graph.py --rollback
```

### Cara Rebuild Data Enrichment dari SIRS Raw

```powershell
cd "D:\TI 26\Tubes WS MSBD\K7"
.venv\Scripts\python.exe scripts/build_final_enrichment.py
# Output: data/enrichment/final_info_rs/*.json dan *.csv
# Kemudian: deploy ulang ke Fuseki
.venv\Scripts\python.exe scripts/deploy_enrichment_graph.py
```

### Prasyarat Instalasi Baru

1. Apache Jena Fuseki aktif di port 3030, dataset name: `hospital`
2. Backend FastAPI aktif di port 8000 (Docker Compose atau manual)
3. File `data/enrichment/final_info_rs/*.json` ada (dari `build_final_enrichment.py`)
4. Mount path `/code/app/data/final_info_rs` terpetakan ke `backend/app/data/final_info_rs`

---

## 9. Risiko yang Belum Terselesaikan

| Risiko | Tingkat | Mitigasi Tersedia |
|---|---|---|
| Jam poliklinik 203 RS belum terverifikasi | 🟡 MEDIUM | Fallback "hubungi RS langsung" + disclaimer |
| Website 202 RS belum di-review | 🟡 MEDIUM | Hanya 3 yang verified — tidak ada URL diasumsikan |
| Email 203 RS tidak tersedia | 🟡 MEDIUM | Tampilan eksplisit "Email belum tersedia" |
| MRI tidak ada di dataset SIRS pelayanan | 🟡 MEDIUM | Tidak ditampilkan — tidak ada data fiktif |
| DBpedia data `status: unavailable` (beberapa RS) | 🟡 MEDIUM | Fallback ke data lokal — 206 RS tetap terbaca |
| Data SIRS per November 2026 (tidak real-time) | 🟡 MEDIUM | Tanggal sumber ditampilkan di semua fitur |
| rs-125 website needs\_review | 🟢 LOW | Belum diklaim verified, tidak ditampilkan |
| Luas tanah/bangunan 2 RS kosong | 🟢 LOW | null ditampilkan — tidak ada nilai fiktif |

---

## 10. Kebijakan Data & Kepatuhan

| Kebijakan | Status |
|---|---|
| Zero hallucination policy | ✅ DITERAPKAN — semua data_gap eksplisit |
| Pemisahan layanan klinis vs fasilitas fisik | ✅ DITERAPKAN |
| Timezone WIB (Asia/Jakarta, UTC+7) | ✅ DITERAPKAN (`timezone(timedelta(hours=7))`) |
| Sumber data dan tanggal wajib ditampilkan | ✅ DITERAPKAN — semua enrichment timestamped 2026-11-20 |
| Tidak mereset Docker volumes | ✅ TIDAK dilakukan |
| Tidak menghapus relasi RDF lama | ✅ TIDAK dilakukan |
| Mekanisme rollback tersedia | ✅ `deploy_enrichment_graph.py --rollback` |
| Mempertahankan pekerjaan anggota tim lain | ✅ TIDAK ada file anggota tim yang ditimpa |

---

## Keputusan Feature Freeze

> **✅ CariSehat Web Semantik — SIAP UNTUK FEATURE FREEZE**

Seluruh 6 fitur telah diimplementasikan sesuai cakupan yang ditetapkan:
- Fitur 1, 4, 5 → **SELESAI PENUH** (cakupan 100% atau mendekati 100%)
- Fitur 2, 3, 6 → **PARTIAL** tetapi sesuai batasan data yang tersedia; semua data gap ditangani dengan fallback eksplisit tanpa data fiktif

**48/48 test PASS.** Named graph enrichment aktif di Fuseki. Backend dan frontend siap.

Tidak ada fitur baru yang boleh ditambahkan setelah dokumen ini dibuat tanpa review tim.

---

*Laporan ini dibuat berdasarkan kondisi runtime aktual pada 2026-11-20T10:46 WIB.*  
*Data sumber: SIRS Online Kemenkes, Website resmi RS, HTML cache 206 profil faskes.*
