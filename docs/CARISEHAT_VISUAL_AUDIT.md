# CARISEHAT — FULL WEBSITE VISUAL AUDIT REPORT
**Role:** Principal Product Designer, Senior UI/UX Engineer, Frontend Specialist  
**Project:** CariSehat — Direktori Rumah Sakit Sumatera Utara  
**Target Repository:** `D:\TI 26\Tubes WS MSBD\K7`  
**Audit Date:** 24 November 2026  

---

## 1. Executive Summary

CariSehat telah melalui audit visual menyeluruh dan pembersihan pola desain generik (*anti-AI-slop redesign*) pada seluruh halaman, komponen, modal, dan elemen interaktif. Tujuannya adalah mengembalikan identitas produk sebagai direktori kesehatan profesional, tenang, berintegritas tinggi (*information-first*), dan berakar pada data master semantik (RDF/OWL, SIRS Kemenkes, OpenStreetMap, PostgreSQL).

Semua pola visual AI yang klise—seperti tombol kapsul neon tanpa batas hierarki, panah dekoratif `→` pada setiap CTA, centang hiasan tanpa nilai fungsional, teks promosi yang mengawang-awang, serta perulangan elemen berlebihan—telah diaudit dan diperbaiki secara langsung pada source code.

---

## 2. Inventarisasi Komponen & Audit Pola AI Slop

| Area / Komponen | File / Selector | Masalah Awal (AI Slop / Tropes) | Tindakan & Perbaikan Nyata |
| :--- | :--- | :--- | :--- |
| **Site Header / Navbar** | `SiteHeader.jsx`<br>`.d-head`, `.d-site-nav` | Nav button dan tombol auth menggunakan radius kapsul `rounded-full` berlebihan yang terasa generik. | Diubah ke radius terukur `rounded-md` / `rounded-lg`, mempertahankan hierarki visual tenang dan kontras tinggi. |
| **Hero Section** | `HomePage.jsx`<br>`form`, `h1`, `p` | Form pencarian kapsul `rounded-full`, tombol CTA utama bertuliskan "Cari sekarang →" dengan ikon panah dekoratif, teks deskripsi marketing. | Bentuk diubah ke radius struktur `rounded-2xl` & `rounded-xl`, teks diperjelas menjadi "Cari Rumah Sakit", panah dekoratif dihapus. |
| **Quick Filter Chips** | `HomePage.jsx`<br>`hero quick-links` | Chips filter cepat berbentuk kapsul `rounded-full` berdesain SaaS AI generik. | Diganti dengan rounded-lg border halus dengan kontras teks tajam `text-white/85`. |
| **Layanan Medis Grid** | `HomePage.jsx`<br>`SpecialtyCard` | Tombol/link "Jelajahi →" menggunakan panah `arrow_forward` dekoratif di setiap kartu. | Panah dihilangkan, menyisakan teks label "Jelajahi" yang ringkas dan fungsional. |
| **Editorial Sections** | `HomePage.jsx`<br>`section.py-16` | Tombol aksi sekunder menggunakan kapsul `rounded-full` tidak konsisten. | Dinormalisasi menggunakan tombol solid dan outline dengan radius sistem standar `rounded-lg`. |
| **Katalog Rumah Sakit** | `SearchPage.jsx`<br>`#explorer`, `#sort` | Teks opsi pengurutan mengandung `Kelas (A &rarr; D)` bergaya kode mentah. | Disederhanakan menjadi `Kelas (A ke D)` yang natural dan mudah dipahami. |
| **Hospital Cards** | `HospitalCard.jsx`<br>`.card`, `.btn-primary` | Sebelumnya tombol "Lihat Detail" rawan ditambahi panah ornamen. | Menggunakan Dennis Design System: `.btn.btn-primary` dengan teks murni "Lihat Detail", tombol perbandingan `.btn-compare` dengan status "Dipilih" yang jelas. |
| **Compare Modal** | `CompareModal.jsx`<br>`#compare-modal` | Memiliki blok ringkasan redundan "Layanan Terlapor yang Sama-Sama Dimiliki (22)" yang membuang ruang vertikal dan mengulang data tabel. | Dihapus sepenuhnya sesuai permintaan pengguna. Modal kini langsung menampilkan tabel matriks perbandingan komparatif yang rapi. |
| **Website Links** | `DetailPage.jsx`<br>`.rs-website`, `.info-item` | Link website rumah sakit menampilkan URL mentah hingga 80 karakter (misal `https://columbiaasia.co.id/rs-columbia-asia-aksara/informasi-umum-aksara/`) yang merusak tipografi. | Diterapkan formatter `formatWebsiteLabel(url)` sehingga hanya menampilkan domain bersih (`columbiaasia.co.id ↗`) dengan atribut keamanan `noopener noreferrer`. |
| **Jam Operasional & IGD** | `DetailPage.jsx`<br>`#sec-jam` | Penataan jadwal dan status IGD sempat tidak seimbang dengan jarak hari dan jam terlalu rapat atau terlalu renggang. | Direstrukturisasi dengan Dennis vertical layout: IGD 24 Jam di atas, disusul tabel jam poliklinik dengan lebar proporsional (`max-width: 700px`) dan perataan kanan waktu operasional. |
| **Spesialisasi & Fasilitas** | `DetailPage.jsx`<br>`#sec-spesialisasi`, `#sec-fasilitas` | Penggunaan badge warna-warni yang bertumpuk menyerupai tag cloud AI slop. | Diganti dengan list berbutir standar (`.clean-bullet-list`) 2 kolom grid yang elegan, kontras tinggi, dan nyaman dipindai mata. |
| **Foto & Galeri Carousel** | `DetailPage.jsx`<br>`.hospital-carousel` | Gambar galeri memiliki rasio dan tinggi yang tidak terkontrol sehingga mendorong layout konten ke bawah. | Dikunci pada tinggi proporsional `260px` dengan `object-fit: cover` dan navigasi slide `&#10094;` / `&#10095;`. |
| **Alternatif Rumah Sakit** | `DetailPage.jsx`<br>`#sec-alternatif` | Daftar alternatif RS sebelumnya tidak dibatasi sehingga berpotensi memenuhi halaman. | Dibatasi secara presisi maksimal 3 rumah sakit terdekat dan setara kelas dalam grid 3-kolom rapi. |
| **Petunjuk Arah Rute Peta** | `MapPage.jsx`<br>`LeafletMap.jsx`, `RouteSidebar.jsx` | 1. Langkah navigasi hanya memakai badge angka mentah (1, 2, 3).<br>2. Titik keberangkatan berlabel generic "Lokasi Anda (GPS / Otomatis)".<br>3. Peta sempat mengalami canvas putih. | 1. Diimplementasikan inline SVG icon resmi untuk setiap manuver (Belok Kanan, Belok Kiri, Putar Balik loop U-turn, Serong, Bundaran, Tujuan).<br>2. Reverse geocoding terintegrasi via Photon API sehingga menampilkan nama jalan dan wilayah nyata.<br>3. Masalah tiles putih diselesaikan via CSS preflight override `.leaflet-container img { max-width: none !important; }`. |
| **Asisten Chatbot** | `ChatWidget.jsx`<br>`floating trigger`, `MessageBubble` | 1. Floating button memiliki badge "AI" hijau norak.<br>2. Setiap kartu rekomendasi RS memiliki chevron panah dekoratif. | 1. Badge "AI" dekoratif dihapus total.<br>2. Chevron dekoratif dihilangkan; link rumah sakit kini fokus pada nama, kelas, dan kab/kota. |
| **Graf Pengetahuan** | `KnowledgeGraphModal.jsx`<br>`modal footer` | Link keluar footer bertuliskan "Buka halaman semantik RDF →" dengan panah ornamen. | Diubah menjadi teks tautan bersih "Buka halaman semantik RDF". |
| **Booking Form Simulasi** | `BookingForm.jsx`<br>`form inputs` | Form simulasi rawat inap berpotensi membingungkan pengguna mengenai status riil faskes. | Diberi penegasan visual berulang "SIMULASI AKADEMIK" dan badge basis data lokal PostgreSQL untuk kepatuhan etika direktori medis. |

---

## 3. Evaluasi Terhadap 6 Pilar Anti-AI-Slop

### A. Ikon Centang (Checkmarks)
- **Status:** **TERVALIDASI BERSIH**.
- **Aturan:** Centang hanya boleh muncul pada indikator sukses fungsional (misal: "Reservasi berhasil dicatat" saat form booking simulasi berhasil disimpan ke DB) dan status filter aktif.
- **Tindakan:** Tidak ada fitur atau kartu keunggulan yang memakai centang dekoratif `✓` atau `✅`.

### B. Ikon Tanda Panah (Arrows)
- **Status:** **TERVALIDASI BERSIH**.
- **Aturan:** Panah dekoratif seperti `Lihat Detail →`, `Jelajahi Sekarang →`, `Cari sekarang →` telah dihapus.
- **Pengecualian Fungsional:** Panah hanya dipertahankan untuk:
  - Navigasi rute berkendara (turn-by-turn navigation SVG icons: Belok Kanan, Belok Kiri, U-Turn).
  - Kontrol navigasi carousel galeri foto (`&#10094;`, `&#10095;`).
  - Pagination katalog (`&larr;`, `&rarr;`).
  - Indikator tautan eksternal (`↗` / `fa-arrow-up-right-from-square`).

### C. Sistem Warna & Tombol
- **Status:** **KONSISTEN & TENANG**.
- **Palet Utama:**
  - Primary Brand: Deep Toba Teal (`#0F766E` / `--toba`) dan Navy (`#021F42` / `var(--brand-navy)`).
  - Accent / Rujukan: Royal Blue (`#0284C7`).
  - Neutral Background: Off-white (`#FAFAF9` / `#F8FAFC`).
  - Surface Borders: Slate Neutral (`#E2E8F0` / `--line`).
  - Emergency / IGD: Rose Crimson (`#E11D48` / `--emergency`).
- **Gaya Tombol:** Dihilangkan gradien neon, glow shadow berwarna, dan pill button berlebih. Semua tombol aksi memiliki kontras WCAG AA, padding proporsional, dan radius struktur 8px (`rounded-lg` / `var(--r-sm)`).

### D. Kartu dan Layout
- **Status:** **TERSTRUKTUR & RINGKAS**.
- Hilangkan nesting kartu di dalam kartu yang berlebihan.
- Modal perbandingan langsung ke pokok data tanpa kartu ringkasan teks panjang.
- Lebar container dibatasi secara tepat (`max-w-[1360px]` untuk desktop lebar, `max-w-[700px]` untuk tabel jadwal operasional).

### E. Copywriting & Tipografi
- **Status:** **NATURAL BAHASA INDONESIA**.
- Menghapus jargon AI seperti *"Platform kesehatan paling cerdas dan revolusioner"*.
- Menggunakan copywriting ringkas dan informatif: *"Direktori semantik 206 rumah sakit di 33 kabupaten/kota Sumatera Utara. Cari berdasarkan kelas, layanan, wilayah, lalu hubungkan data RDF dengan peta dan asisten pintar."*
- Menggunakan font Plus Jakarta Sans dan Serif Editorial dengan perbandingan skala tipografi yang jelas antara heading, body, dan caption.

### F. Integritas Data & Keamanan
- Tidak ada data fiktif atau rating bintang palsu.
- Status data yang belum tercatat di Kemenkes/SIRS selalu diberi fallback jujur: `"Belum tersedia"`.
- Setiap endpoint SPARQL dilindungi read-only guard.
