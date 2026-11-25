# CARISEHAT — UI BEFORE & AFTER REDESIGN DOCUMENTATION
**Project:** CariSehat — Direktori Rumah Sakit Sumatera Utara  
**Repository:** `D:\TI 26\Tubes WS MSBD\K7`  
**Date:** 24 November 2026  

---

## 1. Ringkasan Transformasi Visual

Redesign ini mengubah antarmuka CariSehat dari tampilan prototipe AI generik yang dipenuhi pill button kapsul, ornamen panah redundan, dan teks promosi yang bising menjadi produk direktori medis modern yang tenang, fungsional, dan berbasis data ilmiah (*evidence-based UI*).

---

## 2. Perbandingan Spesifik Komponen & Halaman

### A. Komponen Perbandingan Rumah Sakit (`CompareModal.jsx`)
- **Sebelum:**
  - Menampilkan blok teks bertumpuk di atas tabel: `"Layanan Terlapor yang Sama-Sama Dimiliki (22): Anestesi Bedah CT Scan..."` yang sangat panjang, memakan tinggi layar, dan mengulang informasi yang ada di tabel matriks di bawahnya.
  - Membingungkan pengguna karena harus menggulir jauh ke bawah sebelum melihat perbandingan per rumah sakit.
- **Sesudah:**
  - Blok ringkasan teks panjang dihapus total.
  - Pengguna langsung disajikan tabel matriks perbandingan komparatif (Kelas, Jenis, Wilayah, Alamat, Hotline, BPJS, Layanan, Fasilitas Medis) secara jelas berdampingan.
  - Interaksi lebih cepat dan bersih.

---

### B. Jam Operasional & Layanan IGD (`DetailPage.jsx` - `#sec-jam`)
- **Sebelum:**
  - Jam poliklinik dan IGD sempat dibuat dalam 2 kolom card-in-card dengan badge hijau besar bertuliskan "Buka 24 Jam" dan deskripsi naratif panjang.
  - Jarak antara hari ("Senin") dan jam ("08:00 - 16:00") sempat tidak seimbang (terlalu rapat atau terdorong ke ujung).
- **Sesudah:**
  - Mengadopsi struktur vertikal Dennis yang bersih dan proporsional (`max-width: 700px`).
  - Baris atas menyajikan status Instalasi Gawat Darurat (IGD) yang jelas.
  - Baris bawah menampilkan jadwal harian poliklinik dalam grid 2 kolom dengan teks hari di kiri dan rentang jam di kanan rata (align-right) dengan indikator status merah kalem `Tutup` pada akhir pekan bila libur.

---

### C. Link Website Resmi Rumah Sakit (`DetailPage.jsx`)
- **Sebelum:**
  - Link website menampilkan URL mentah panjang hingga lebih dari 70 karakter (contoh: `https://columbiaasia.co.id/rs-columbia-asia-aksara/informasi-umum-aksara/`) yang membungkus ke 3 baris teks dan merusak kerapian kartu profil.
- **Sesudah:**
  - Diterapkan fungsi pembantu `formatWebsiteLabel(url)` yang memotong URL menjadi nama domain bersih dan rapi (contoh: `columbiaasia.co.id ↗`).
  - Dilengkapi ikon eksternal halus `fa-arrow-up-right-from-square` dan atribut keamanan `rel="noopener noreferrer"`.
  - Jika website belum terdaftar di dataset, ditampilkan status jujur `"Belum tersedia"` dengan warna netral.

---

### D. Petunjuk Arah Belokan & Navigasi Peta (`MapPage.jsx` & `LeafletMap.jsx`)
- **Sebelum:**
  - Petunjuk arah di sidebar belokan hanya menggunakan badge angka lingkaran mentah (`1`, `2`, `3`, `4`, `5`). Pengemudi tidak tahu apakah harus belok kiri atau kanan tanpa membaca seluruh kalimat teks.
  - Titik keberangkatan berlabel kaku `"Lokasi Anda (GPS / Otomatis)"`.
  - Map tiles sempat mengalami kanvas putih akibat intervensi Tailwind CSS preflight (`img { max-width: 100% }`).
- **Sesudah:**
  - Setiap langkah belokan dilengkapi inline SVG icon arah berstandar navigasi:
    - Belok Kanan 90°
    - Belok Kiri 90°
    - Putar Balik (U-Turn Loop)
    - Serong Kanan / Kiri
    - Lurus
    - Bundaran (Roundabout)
    - Titik Tujuan (Destination Pin)
  - Lokasi GPS otomatis di-reverse geocode melalui Photon API untuk menampilkan alamat jalan nyata (misal: `"Jalan Pipa, Pangkalan Mansyur, Kota Medan"`).
  - Leaflet Map dilengkapi CSS override khusus `.leaflet-container img { max-width: none !important; }` sehingga peta raster OSM, Google Maps Road, dan CARTO Voyager tampil tajam tanpa distorsi atau tile putih.

---

### E. Daftar Spesialisasi & Fasilitas Medis (`DetailPage.jsx`)
- **Sebelum:**
  - Komponen menggunakan badge berbentuk pill warna-warni yang bertumpuk (*tag soup* / AI slop), menyulitkan pengguna membaca nama spesialisasi medis yang panjang.
- **Sesudah:**
  - Menggunakan daftar butir terstruktur (`.clean-bullet-list`) dalam grid 2 kolom yang tenang dengan tipografi Plus Jakarta Sans, kontras tinggi, dan jarak vertikal proporsional.

---

### F. Hero Section & Tombol Navigasi (`HomePage.jsx`, `SiteHeader.jsx`)
- **Sebelum:**
  - Form pencarian utama hero berbentuk kapsul oval `rounded-full` dengan tombol "Cari sekarang →" yang menggunakan panah ornamen generik.
  - Tautan "Jelajahi →", "Lihat semua →", dan "Mulai pencarian →" dipenuhi ornamen panah.
  - Floating button chat memiliki badge hijau "AI" norak.
- **Sesudah:**
  - Form hero berbentuk rounded elegan `rounded-2xl` dengan input terstruktur `rounded-xl`.
  - Tombol aksi utama bertuliskan "Cari Rumah Sakit" yang tegas tanpa panah dekoratif.
  - Tombol-tombol CTA sekunder dinormalisasi menjadi `rounded-lg` dengan label fungsional ("Lihat Semua Layanan", "Buka Peta", "Tanya Asisten").
  - Badge "AI" pada tombol chat mengambang dihapus; ikon chat robot bersih dan tenang.

---

### G. Rekomendasi Rumah Sakit Alternatif (`DetailPage.jsx`)
- **Sebelum:**
  - Alternatif rumah sakit tidak dibatasi, berpotensi memanjang ke bawah tanpa hierarki visual.
- **Sesudah:**
  - Dibatasi secara presisi maksimal 3 rekomendasi rumah sakit terdekat dan setara kelas.
  - Disajikan dalam grid 3 kartu (`d-alternatives-grid`) dengan foto mini, badge kelas terverifikasi, jarak kab/kota, tombol "Lihat Detail", dan tombol "Bandingkan" instan.

---

## 3. Matriks Komponen UI

| Komponen | Status Sebelum | Status Sesudah | Manfaat Pengguna |
| :--- | :--- | :--- | :--- |
| **Bandingkan RS Modal** | Ada blok redundan teks panjang | Langsung ke tabel matriks | Mempercepat pengambilan keputusan rujukan |
| **Jam Operasional** | Layout 2 kolom renggang | Layout vertikal proporsional 700px | Mudah dipindai di ponsel dan desktop |
| **Tautan Web** | URL mentah hingga 80 karakter | Domain ringkas `domain.com ↗` | Tampilan bersih, tipografi tidak patah |
| **Petunjuk Belokan** | Angka 1, 2, 3 tanpa tanda arah | SVG Icon manuver resmi (Kanan, Kiri, U-turn) | Navigasi intuitif setara Google Maps / Apple Maps |
| **Nama Titik GPS** | Teks generik "Lokasi Anda" | Nama jalan nyata (Reverse Geocoded) | Konfirmasi titik awal yang akurat |
| **Peta Leaflet** | Rawan canvas putih (Tailwind bug) | Peta tile stabil & multi-layer provider | Navigasi visual lancar dan andal |
| **Spesialisasi** | Pill badges bertumpuk | Clean bullet list 2-kolom | Mudah dibaca oleh pasien dan dokter perujuk |
| **Tombol & Bentuk** | Kapsul `rounded-full` berlebihan | Standar `rounded-lg` / `rounded-xl` | Tampilan produk profesional non-AI slop |
| **Panah Dekoratif** | Panah di semua tombol aksi | Dihapus dari tombol CTA | Fokus ke label tindakan yang jelas |
