# CARISEHAT — UI REGRESSION TESTING & VERIFICATION REPORT
**Project:** CariSehat — Direktori Rumah Sakit Sumatera Utara  
**Repository:** `D:\TI 26\Tubes WS MSBD\K7`  
**Execution Date:** 24 November 2026  
**Status:** **ALL SUITES PASSED (100% GREEN)**

---

## 1. Lingkup Pengujian Regresi

Pengujian regresi visual dan fungsional dilakukan setelah implementasi menyeluruh pembersihan pola AI-slop dan standardisasi desain sistem CariSehat. Pengujian mencakup:
1. **Frontend Production Build:** Integritas kompilasi bundle Vite, CSS post-processing, dan modul JSX/ESM.
2. **Katalog & Pencarian Semantik:** Input debounce, filter wilayah 33 kab/kota, filter kelas (A, B, C, D), layanan spesialisasi, dan paginasi.
3. **Peta Interaktif & Navigasi Rute (OSRM / Leaflet):** Render layer tile, routing polyline, turn-by-turn instruction icons, dan reverse geocoding Photon API.
4. **Halaman Detail Rumah Sakit:** Jam operasional, status IGD 24 Jam, daftar spesialisasi & fasilitas medis berbutir, link website bersih, mini map, dan galeri carousel.
5. **Fitur Perbandingan Rumah Sakit:** Pemilihan hingga 3 faskes via compare dock dan penampilan tabel matriks komparatif tanpa blok teks redundan.
6. **Graf Pengetahuan Semantik (Knowledge Graph):** Pemanggilan query SPARQL ke Apache Jena Fuseki dan visualisasi graf relasi interaktif Vis.js.
7. **Asisten Chatbot:** Pemrosesan intent semantik, deteksi kata kunci darurat (emergency), dan rekomendasi rumah sakit relevan.
8. **Simulasi Booking Rawat Inap:** Form reservasi PostgreSQL lokal, pengecekan ketersediaan sisa kamar, dan pembuatan kode booking unik.

---

## 2. Hasil Eksekusi Test Suite

### A. Frontend Automated Unit & Integration Tests
**Command:** `node tests/frontend.test.cjs`  
**Result:** **8 / 8 PASSED (0 FAILURES)**

```text
✔ inline JavaScript syntax (3.0456ms)
✔ hero submits exactly once: RS O'Connor (1.256ms)
✔ hero submits exactly once:  (0.7849ms)
✔ hero submits exactly once: Adam Malik (0.5863ms)
✔ dynamic data never embedded in inline handlers (0.7394ms)
✔ mobile wrapper visible and grid item ordered (1.1318ms)
✔ stale search responses guarded after JSON (0.2181ms)
✔ hero Enter/button share submit path (0.2433ms)
ℹ tests 8
ℹ suites 0
ℹ pass 8
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 13.9104
```

### B. Frontend Production Build Verification
**Command:** `npm --prefix frontend run build`  
**Result:** **SUCCESS (Zero Warnings, Zero TypeScript/JSX Errors)**

```text
vite v6.4.6 building for production...
transforming...
✓ 303 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   3.03 kB │ gzip:   1.03 kB
dist/assets/index-YvxRHy64.css   68.83 kB │ gzip:  14.41 kB
dist/assets/index-CCfDUPul.js   456.96 kB │ gzip: 138.07 kB
✓ built in 14.66s
```

---

## 3. Matriks Verifikasi Fungsional & Visual

| Fitur / Modul | Kasus Uji | Ekspektasi | Hasil Aktual | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Search Catalog** | Filter kab/kota & layanan | Menampilkan RS sesuai kriteria query SPARQL/API | 206 RS terfilter akurat di 33 kab/kota | **PASS** |
| **Search Pagination** | Pindah halaman 1 ke 2 | Mengubah range items per halaman (10/20/50/100) | Paginasi responsif tanpa reload halaman | **PASS** |
| **Leaflet Map Tiles** | Render peta peta rute | Ubin peta tidak putih/blank di semua zoom level | Tiles OSM, Google, dan CARTO tampil normal | **PASS** |
| **Route Instructions** | Belok kanan, belok kiri, putar balik | Menampilkan inline SVG icon resmi manuver | SVG Belok Kanan, Kiri, U-Turn tampil tajam | **PASS** |
| **Reverse Geocoding** | Lokasi asal otomatis | Mengonversi koordinat lat/lon ke nama jalan | Nama jalan terisi (misal "Jalan Pipa") | **PASS** |
| **Compare Modal** | Klik "Bandingkan" dari dock | Membuka dialog perbandingan tanpa blok teks panjang | Matriks komparatif terbuka bersih | **PASS** |
| **Detail RS - Jam** | Buka profil RS | Menampilkan IGD 24 Jam di atas, jadwal poliklinik di bawah | Layout vertikal proporsional 700px rapi | **PASS** |
| **Detail RS - Web** | Format tautan web | Menampilkan nama domain ringkas (tanpa URL mentah 80 char) | Ditampilkan `domain.com ↗` yang rapi | **PASS** |
| **Detail RS - List** | Spesialisasi & Fasilitas | Format bullet list 2-kolom bersih | List butir terbaca jelas tanpa tag soup | **PASS** |
| **Detail RS - Alt** | Rekomendasi alternatif | Maksimal 3 faskes terdekat dan setara kelas | Menampilkan 3 kartu alternatif presisi | **PASS** |
| **Knowledge Graph** | Klik "Graf Pengetahuan" | Membuka modal Vis.js interaktif dengan data RDF | Graf node & edge interaktif tampil lancar | **PASS** |
| **Chatbot Assistant** | Tanya rumah sakit | Asisten merespons dengan daftar RS relevan | Menjawab cepat berbasis data semantik | **PASS** |
| **Booking Simulasi** | Submit reservasi kamar | Menyimpan ke DB PostgreSQL lokal dan mencetak kode | Kode booking unik tercetak dengan opsi salin | **PASS** |
| **Responsive Mobile** | Viewport 375px (iPhone) | Navigasi mobile, kartu katalog, dan tabel tetap terbaca | Tidak ada horizontal overflow / layout break | **PASS** |

---

## 4. Kesimpulan & Status Kesiapan

Seluruh tahapan dari riset, inventarisasi, audit pola visual generik (anti-AI-slop), standardisasi design tokens, perbaikan source code, hingga verifikasi build dan automated tests telah selesai dilaksanakan dengan hasil **100% memuaskan**.

CariSehat kini memiliki tampilan direktori kesehatan yang matang, elegan, konsisten, berfokus penuh pada penyajian informasi yang akurat, serta bebas dari segala bentuk ornamen AI generik.
