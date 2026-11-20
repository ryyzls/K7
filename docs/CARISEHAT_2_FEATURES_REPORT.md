# CariSehat 2.0 — Laporan Implementasi 4 Fitur Utama

**Dokumen:** Laporan Resmi Implementasi, Pengujian, dan Verifikasi 4 Fitur Utama CariSehat 2.0  
**Tanggal:** 20 November 2026 (WIB)  
**Peran:** Senior Full-Stack Developer, Semantic Web Engineer, Data Engineer, dan QA Engineer  
**Repository:** `D:\TI 26\Tubes WS MSBD\K7`  
**Status Keseluruhan:** **100% DONE** (Semua 4 fitur berhasil diimplementasikan dan diverifikasi secara komprehensif tanpa regresi).

---

## 1. Status 4 Fitur Utama

| No | Fitur | Status | Keterangan Verifikasi |
|---|---|:---:|---|
| **1** | **Pencarian Spesialisasi & Kebutuhan** | **DONE** | 16 spesialisasi klinis inti Permenkes 3/2020 aktif, mapping sinonim awam deterministik (dokter jantung, dokter anak, dokter kandungan, dokter mata, dll.), query aman ke named graph SIRS, pemisahan status pencatatan vs operasional real-time. |
| **2** | **Perbandingan Rumah Sakit** | **DONE** | Membandingkan 2–3 RS secara faktual (nama, kode Kemenkes, kab/kota, kelas, jenis, kontak, website resmi terverifikasi, irisan layanan SIRS, fasilitas unverified). Disertai tombol "Bandingkan" pada kartu, floating dock responsif, dan modal matriks komparasi. |
| **3** | **Alternatif Rumah Sakit** | **DONE** | Menampilkan 3–5 faskes alternatif dengan prioritas deterministik: (1) kesamaan spesialisasi SIRS, (2) kesamaan wilayah administratif, (3) kesetaraan kelas faskes. Disertai narasi alasan rekomendasi yang dapat dijelaskan (*explainable*). |
| **4** | **Profil Rumah Sakit Lengkap** | **DONE** | Kode Kemenkes resmi (dari `cs:kodeRegistrasiKemenkes`), identitas lengkap, website resmi terverifikasi, kelompok spesialisasi SIRS, indikator UGD 24 jam, tautan provenance SIRS transparan, dan disclaimer operasional tanpa manipulasi ketersediaan bed/dokter. |

---

## 2. Rincian Perubahan File

Pekerjaan dilakukan dengan prinsip perubahan minimal, modular, dan memelihara seluruh pekerjaan anggota tim lain:

### Berkas Baru yang Dibuat
1. **`backend/app/services/specialty_service.py`**:
   - Modul kurasi 16 spesialisasi klinis aktif Permenkes 3/2020.
   - Kamus sinonim eksplisit (`SYNONYM_MAP`) mencakup istilah awam kedokteran umum.
   - Generator snippet SPARQL aman (`sirs_specialty_pattern`).
   - Loader data fallback lokal saat Fuseki offline (`load_all_sirs_observations`).
2. **`backend/app/services/comparison_service.py`**:
   - Logika matriks perbandingan rumah sakit (maksimal 3 RS).
   - Validasi batas input (HTTP 400 bila > 3 faskes atau kosong).
   - Ekstraksi atribut faktual, irisan layanan (*shared services*), dan layanan unik per faskes.
3. **`backend/app/services/alternatives_service.py`**:
   - Mesin pencari rumah sakit alternatif deterministik berbasis skor kesamaan layanan SIRS dan wilayah administratif.
   - Generator narasi alasan rekomendasi yang transparan (*explainable reasoning*).
4. **`tests/test_specialties.py`**:
   - Unit test mapping istilah sinonim, penolakan kata acak/bukan medis, dan pengujian injeksi SPARQL (5 test cases, PASS).
5. **`tests/test_carisehat2_features.py`**:
   - Test suite komprehensif untuk 4 fitur pada level integrasi data dan SPARQL named graph (10 test cases, PASS).
6. **`tests/test_carisehat2_frontend.cjs`**:
   - Pengujian antarmuka DOM, ketersediaan komponen compare dock, modal, selektor optgroup, dan kartu alternatif (5 test cases, PASS).
7. **`tests/test_carisehat2_live_http.py`**:
   - Pengujian HTTP live terhadap FastAPI server yang sedang berjalan (6 test cases, PASS).

### Berkas yang Dimodifikasi Terarah
1. **`backend/app/services/sparql_service.py`**:
   - Menambahkan parameter `spesialisasi=""` pada `build_search_query()`.
   - Mengintegrasikan pengambilan `kodeKemenkes` dari named graph SIRS.
   - Memperkaya output `to_hospital()` dengan `kode_kemenkes`, `spesialisasi`, `spesialisasi_facts`, dan `igd_tersedia` tanpa mengubah kontrak `layanan` dan `layanan_facts` eksisting.
2. **`backend/app/routers/api.py`**:
   - Menambahkan endpoint `GET /api/specialties` untuk daftar spesialisasi terkurasi.
   - Menambahkan integrasi sinonim otomatis dan parameter `spesialisasi` pada `GET /api/search`.
   - Menambahkan endpoint `GET /api/compare` untuk membandingkan 2–3 RS.
   - Menambahkan endpoint `GET /api/hospitals/{rs_id}` dan `GET /api/hospitals/{rs_id}/alternatives`.
   - Memperbarui `GET /api/filters` dengan optgroup spesialisasi.
3. **`backend/app/routers/semantic.py`**:
   - Menyertakan data rekomendasi alternatif ke dalam render template `rs_detail.html`.
4. **`backend/app/templates/rs_detail.html`**:
   - Menampilkan Kode Registrasi Kemenkes resmi faskes.
   - Menampilkan indikator UGD 24 Jam Terlapor SIRS.
   - Menampilkan kelompok spesialisasi medis terlapor dan layanan diagnostik secara terpisah.
   - Menampilkan seksi "Rumah Sakit Alternatif Terdekat & Setara" lengkap dengan alasan kecocokan semantik.
5. **`frontend/index.html`**:
   - Menambahkan tombol "Bandingkan" pada kartu katalog faskes.
   - Menambahkan floating compare dock di bagian bawah layar.
   - Menambahkan dialog modal perbandingan responsif lengkap dengan tabel matriks komparasi.
   - Menambahkan seksi rekomendasi alternatif pada detail view dengan kartu interaktif.
   - Memperbarui dropdown filter `#lay` dengan optgroup "Spesialisasi Medis Terlapor (SIRS)".
   - Menambahkan styling CSS responsif untuk viewport 375px, 768px, dan 1440px.

---

## 3. Endpoint Baru dan Query SPARQL

### Daftar Endpoint API Baru

1. **`GET /api/specialties`**
   - Mengembalikan 16 spesialisasi klinis aktif dan 3 layanan diagnostik/darurat beserta sinonim populer dan jumlah rumah sakit penyedia di Sumatera Utara.
2. **`GET /api/search?q={query}&spesialisasi={label}`**
   - Jika `q` cocok dengan kamus sinonim (contoh: `q=dokter jantung`), secara otomatis memfilter RS dengan spesialisasi `Jantung dan Pembuluh Darah` di named graph SIRS dan mengembalikan `query_type: "specialty_synonym"`.
   - Jika `spesialisasi` diisi secara eksplisit, memfilter RS yang memiliki catatan spesialisasi tersebut.
3. **`GET /api/compare?ids={rs1,rs2,rs3}`**
   - Memvalidasi minimal 1 dan maksimal 3 faskes.
   - Mengembalikan profil lengkap, irisan layanan bersama (*shared services*), perbedaan layanan unik, dan disclaimer faktual.
4. **`GET /api/hospitals/{rs_id}`**
   - Mengembalikan detail lengkap rumah sakit termasuk kode Kemenkes resmi, spesialisasi terlapor, fakta provenance, dan status IGD.
5. **`GET /api/hospitals/{rs_id}/alternatives?limit={1-5}`**
   - Mengembalikan 3–5 rumah sakit alternatif berbasis kecocokan layanan SIRS dan wilayah administratif dengan narasi alasan yang dapat dijelaskan.

### Template Query SPARQL Baru

#### 1. Filter Spesialisasi Medis pada Named Graph SIRS:
```sparql
PREFIX cs: <http://carisehat.id/ontology/sirs/>
SELECT ?rs ?nama ?kabkota WHERE {
  ?rs a hf:RumahSakit ; schema:name ?nama ; hf:beradaDiKabupatenKota/rdfs:label ?kabkota .
  FILTER EXISTS {
    GRAPH <http://carisehat.id/graph/sirs/2026-11-19> {
      ?rs cs:catatanPelayanan ?obs .
      ?obs cs:labelPelayanan "Jantung dan Pembuluh Darah" .
    }
  }
}
```

#### 2. Pengambilan Kode Registrasi Kemenkes:
```sparql
OPTIONAL {
  GRAPH <http://carisehat.id/graph/sirs/2026-11-19> {
    ?rs <http://carisehat.id/ontology/sirs/kodeRegistrasiKemenkes> ?kodeKemenkes .
  }
}
```

---

## 4. Distribusi Label Spesialisasi (Aktif vs Ditahan)

Dari total **239 label** dalam kategori `pelayanan_klinis_terlapor` (dan 153 label yang dikelompokkan ke dalam `AMAN_SEBAGAI_PENCARIAN` pada tahap kurasi):

### 16 Spesialisasi Klinis Inti yang Diaktifkan (Permenkes 3/2020)

| No | Label Resmi SIRS | Nama Tampilan Pengguna | Kategori Spesialisasi | Frekuensi RS di Sumut |
|:---:|---|---|---|:---:|
| 1 | `Kesehatan anak` | Spesialis Anak (Pediatri) | Spesialisasi Klinis Standar | 190 RS |
| 2 | `Penyakit dalam` | Spesialis Penyakit Dalam (Internis) | Spesialisasi Klinis Standar | 188 RS |
| 3 | `Bedah` | Spesialis Bedah Umum | Spesialisasi Klinis Standar | 188 RS |
| 4 | `Obstetri dan ginekologi` | Spesialis Kebidanan & Kandungan (Obgyn) | Spesialisasi Klinis Standar | 186 RS |
| 5 | `Anestesi` | Spesialis Anestesiologi & Terapi Intensif | Spesialisasi Klinis Standar | 186 RS |
| 6 | `Paru` | Spesialis Paru (Pulmonologi) | Spesialisasi Klinis Standar | 164 RS |
| 7 | `Pelayanan medik gigi mulut` | Pelayanan Gigi & Mulut | Spesialisasi Klinis Standar | 142 RS |
| 8 | `Saraf` | Spesialis Saraf (Neurologi) | Spesialisasi Klinis Standar | 135 RS |
| 9 | `Telinga Hidung Tenggorok Kepala Leher` | Spesialis THT-KL | Spesialisasi Klinis Standar | 132 RS |
| 10 | `Mata` | Spesialis Mata (Oftalmologi) | Spesialisasi Klinis Standar | 116 RS |
| 11 | `Jantung dan Pembuluh Darah` | Spesialis Jantung & Pembuluh Darah | Spesialisasi Klinis Standar | 106 RS |
| 12 | `Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA` | Spesialis Kedokteran Jiwa (Psikiatri) | Spesialisasi Klinis Standar | 87 RS |
| 13 | `Kulit dan Kelamin` | Spesialis Kulit & Kelamin (Dermatologi) | Spesialisasi Klinis Standar | 87 RS |
| 14 | `Rehabilitasi Medik` | Kedokteran Fisik & Rehabilitasi | Spesialisasi Klinis Standar | 87 RS |
| 15 | `Orthopedi` | Spesialis Bedah Ortopedi & Traumatologi | Spesialisasi Klinis Standar | 62 RS |
| 16 | `Urologi` | Spesialis Urologi | Spesialisasi Klinis Standar | 47 RS |

*(Dilengkapi 3 layanan diagnostik & gawat darurat aktif: UGD 24 Jam [194 RS], Radiologi [184 RS], Patologi Klinik [169 RS]).*

### Label yang Masih Ditahan:
- **137 label** dari 153 label `AMAN_SEBAGAI_PENCARIAN` tetap berstatus **DITAHAN** (`cs:layakPencarian false`).
- **73 label** kategori `AMBIGU_PERLU_REVIEW` berstatus **DITAHAN / TIDAK DITAMPILKAN**.
- **13 label** kategori `BUKAN_LAYANAN_KLINIS` berstatus **DITAHAN / TIDAK DITAMPILKAN**.
- **Total:** **223 label klinis tetap ditahan** demi menjaga akurasi medis dan menghindari salah persepsi jadwal dokter di lapangan.

---

## 5. Hasil Pengujian Faktual (PASS/FAIL)

Semua pengujian dijalankan langsung pada repositori dengan status kelulusan 100%:

| Test Suite | File Runner | Kasus Uji | Hasil | Status |
|---|---|:---:|:---:|:---:|
| **Mapping Sinonim & Spesialisasi** | `tests/test_specialties.py` | 5 | 5 PASS / 0 FAIL | **PASS** |
| **CariSehat 2.0 4 Fitur Integrasi** | `tests/test_carisehat2_features.py` | 10 | 10 PASS / 0 FAIL | **PASS** |
| **Live HTTP Endpoints Backend** | `tests/test_carisehat2_live_http.py` | 6 | 6 PASS / 0 FAIL | **PASS** |
| **DOM, Modal & CSS Frontend** | `tests/test_carisehat2_frontend.cjs` | 5 | 5 PASS / 0 FAIL | **PASS** |
| **Regression Frontend Eksisting** | `tests/frontend.test.cjs` | 8 | 8 PASS / 0 FAIL | **PASS** |
| **Regression Keamanan SPARQL Guard** | `backend/tests/test_sparql_guard.py` | 22 | 22 PASS / 0 FAIL | **PASS** |
| **Regression Backend Core** | `tests/test_backend.py` | 7 | 7 PASS / 0 FAIL | **PASS** |
| **Regression Skenario Chatbot** | `tests/test_chatbot_scenarios.py` | 14 | 14 PASS / 0 FAIL | **PASS** |
| **Regression Kebijakan Named Graph SIRS**| `tests/test_sirs_integration.py` | 8 | 8 PASS / 0 FAIL | **PASS** |
| **TOTAL** | — | **85** | **85 PASS / 0 FAIL** | **100% PASS** |

---

## 6. Verifikasi Responsif Browser (375px, 768px, 1440px)

Tampilan telah diverifikasi secara visual dan semantik pada 3 breakpoint utama:
1. **Mobile (375px):**
   - Floating compare dock menyesuaikan lebar layar (`max-width: 96vw`) dengan tombol aksi terpadu.
   - Tabel perbandingan rumah sakit otomatis mengaktifkan horizontal scroll (`.compare-table-wrap` dengan `overflow-x: auto`), kolom atribut sticky, dan lebar minimum per kolom faskes 220px.
   - Kartu alternatif rumah sakit tersusun vertikal (1 kolom) dengan narasi alasan yang mudah dibaca.
2. **Tablet (768px):**
   - Dialog perbandingan menampilkan 2–3 kolom faskes secara nyaman tanpa teks terpotong.
   - Kartu alternatif faskes tersusun dalam grid 2 kolom.
3. **Desktop (1440px):**
   - Modal dialog perbandingan berdimensi maksimal 1100px di tengah layar dengan background backdrop blur.
   - Semua fakta komparasi (kode Kemenkes, kontak, website resmi verified, spesialisasi, fasilitas) tertata rapi dalam matriks komparasi tabular.

---

## 7. Penanganan Risiko & Prosedur Rollback

### Aspek Keamanan & Arsitektur yang Dijaga:
- **SPARQL Guard Utuh:** Tidak ada query berisiko `INSERT`, `DELETE`, `DROP`, atau `SERVICE` yang diizinkan; seluruh input parameter di-escape menggunakan `lit()` dan sanitasi ketat.
- **Isolasi Graf Semantik:** Named graph `http://carisehat.id/graph/sirs/2026-11-19` dan default graph (206 RS) tidak dimutasi atau di-overwrite.
- **Integritas Data Relasional:** Database PostgreSQL tidak mengalami perubahan skema ataupun reset data pemesanan.
- **Pemisahan Klaim Medis:** Seluruh antarmuka secara eksplisit menampilkan disclaimer bahwa data spesialisasi merupakan data laporan administratif SIRS Kemenkes, bukan jadwal praktik dokter real-time.

### Instruksi Rollback (Bila Diperlukan):
Jika tim memutuskan untuk menonaktifkan fitur CariSehat 2.0 ini:
1. **Rollback Kode:**
   Revert berkas baru pada git:
   ```powershell
   git checkout HEAD -- backend/app/routers/api.py backend/app/routers/semantic.py backend/app/services/sparql_service.py backend/app/templates/rs_detail.html frontend/index.html
   ```
2. **Pembersihan Modul Layanan Baru:**
   Hapus berkas layanan mandiri:
   - `backend/app/services/specialty_service.py`
   - `backend/app/services/comparison_service.py`
   - `backend/app/services/alternatives_service.py`
3. Tidak ada rollback database Fuseki ataupun PostgreSQL yang diperlukan karena tidak ada perubahan pada isi database.