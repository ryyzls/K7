# NARA 3 — Implementation Report

Tanggal: 25 November 2026. Status: implementasi fungsional Tahap 1 tersedia; penerimaan keseluruhan belum dinyatakan selesai.

## Ringkasan

NARA kini menggunakan mesin `hybrid_search` yang sama dengan search bar, bukan mesin pencarian rumah sakit kedua. Backend rule-based memvalidasi rencana Boolean, mengelola konteks, memanggil service yang sudah ada, dan mengembalikan response terstruktur. Tidak ada LLM, embedding, vector database, Redis, dependency baru, dataset rumah sakit baru, atau perubahan ID/URI.

Antarmuka baru menggunakan panel gelap transparan dengan blur, gradient, transisi, floating/expanded mode, command palette, kartu rumah sakit, perbandingan, peta, dan riwayat sementara. Logo CariSehat asli dipertahankan. Kode referensi `AnimatedAIChat` tidak terdapat dalam lampiran/repository yang diperiksa; kesetiaan terhadap kode referensi tersebut **belum dapat diverifikasi**. Desain mengikuti spesifikasi tertulis, bukan diklaim sebagai adaptasi persis kode yang tidak tersedia.

## Arsitektur sebelum dan sesudah

Sebelum: ChatWidget → `/api/chat` → classifier/resolver lama → repository/filter lama → Markdown. Search bar sudah mempunyai parser hybrid tersendiri. Intent layanan jantung pada jalur lama dapat diarahkan ke Penyakit Dalam.

Sesudah:

```text
React ChatWidget
  → validated FastAPI payload + bounded request limiter
  → emergency/input validation
  → rule-based intent, entity and context handling
  → Pydantic QueryPlan/Condition
  → bounded ToolRunner
  → existing hybrid_search / detail / comparison / alternatives / DBpedia
  → existing RDF + SIRS + enrichment sources
  → identity and mandatory-query verification
  → structured response and React components
```

`process_chat_message` tetap merupakan entry point kompatibel. Implementasi lama disimpan sebagai `process_chat_message_legacy` untuk penelusuran baseline, tidak dipanggil pada alur produksi.

## Fitur yang diimplementasikan

- Arahan darurat sebelum akses sumber data atau permintaan GPS, dengan penanganan negasi, konteks masa lalu, hipotetis, dan perbedaan pencarian IGD.
- Normalisasi bahasa percakapan, typo contoh tugas, alias, layanan SIRS, serta fuzzy/entity matching dari service yang ada.
- Query plan tervalidasi, AND/OR, pengelompokan kurung terbatas, pengecualian nama/kepemilikan, lokasi/kelas/layanan/fasilitas majemuk.
- Penambahan, penggantian, penghapusan filter; pemilihan hasil ordinal; batas hasil; pengurutan jarak/nama; pencarian baru yang memulai filter baru.
- `last_result_ids` dipisahkan dari rumah sakit terpilih agar referensi hasil sebelumnya tetap tersedia.
- Detail, kontak, website/email, direktur, jam per unit, pemeriksaan layanan/fasilitas, perbandingan maksimal tiga RS, dan alternatif yang disaring **sebelum** ranking.
- Workflow pencarian tiga RS terdekat dengan jantung + ICU → perbandingan → kontak, tanpa LLM.
- Geolocation hanya setelah tombol Lokasi dipilih; alternatif input wilayah manual; Haversine dinyatakan sebagai jarak garis lurus. Kandidat dengan sumber koordinat tidak memadai dikeluarkan dari ranking jarak.
- DBpedia hanya untuk permintaan eksplisit informasi wilayah, dengan fallback yang tidak menghalangi pencarian RS. Jalur kegagalan diuji; keberhasilan endpoint eksternal belum diverifikasi.
- Respons `kind`, hospitals, comparison, hours, regional_info, filters, total, retryable; frontend tidak menebak jenis komponen dari teks jawaban.
- Floating/expanded memakai sesi sama; minimize mempertahankan konteks; riwayat hingga 20 percakapan selama halaman terbuka; hapus dengan konfirmasi; new conversation; copy; retry; pengiriman ganda dicegah.
- Command palette dengan keyboard/mouse, Enter/Shift+Enter, textarea auto-resize, indikator request aktual, scroll yang menghormati posisi baca, loading/error, filter chips, peta dan navigasi.
- SVG fungsional lokal menghindari ketergantungan ikon NARA pada unduhan font. Tidak ada ikon robot/sparkle atau branding generative AI.

## Perubahan file

File aplikasi yang diubah pada tugas ini:

- `backend/app/routers/chat.py`: limiter dan integrasi request.
- `backend/app/services/chatbot_service.py`: entry point produksi ke engine baru; jalur lama tetap dapat ditelusuri.
- `backend/app/services/hybrid_search.py`: parameter internal planned_tree; parsing jadwal hari umum; menjaga specialty ketika kalimat jadwal mengandung nama layanan.
- `backend/app/services/alternatives_service.py`: optional allowed_ids agar filter wajib diterapkan sebelum pemeringkatan alternatif.
- `backend/app/services/chatbot/engine.py` (baru): orchestration, konteks, cache, verification, response.
- `backend/app/services/chatbot/planning.py` (baru): model, normalisasi, safety, komposisi/pruning Boolean, extension protocol.
- `frontend/src/api.js`: AbortSignal untuk request chat.
- `frontend/src/components/ChatWidget.jsx`: antarmuka fungsional baru.
- `frontend/src/components/NaraChat.css` (baru): styling scoped, mobile, reduced motion.
- `frontend/src/components/useNaraConversation.js` (baru): lifecycle request, session/history, command palette dan lokasi.
- `frontend/src/components/NaraRichResponse.jsx` (baru): tabel perbandingan, jadwal, peta, copy/retry dan pemilihan hasil.
- `frontend/src/components/NaraIcon.jsx` (baru): ikon SVG fungsional lokal.
- `frontend/dist/index.html` dan bundle hasil Vite.

Test baru: `tests/test_nara3.py`, `tests/benchmark_nara3.py`, `tests/test_nara3_heldout.py`, `tests/test_nara3_browser.cjs`, `tests/run_nara3_search_regression.py`.

Saat finalisasi, ChatWidget berubah lagi di workspace. Struktur visual terbaru dipertahankan, lalu fitur NARA disatukan lewat hook dan komponen rich response terpisah. Salinan sebelum rekonsiliasi tersedia di `scratch/nara_concurrent_widget.jsx`; perubahan tersebut tidak dihapus melalui git reset/checkout. Screenshot/test frontend diulang setelah rekonsiliasi.

Repository sudah berisi perubahan developer lain sebelum tugas ini. Daftar di atas tidak mengklaim perubahan pada file aplikasi lain sebagai hasil tugas ini. Tidak dilakukan reset/checkout massal. Tidak ada perubahan dependency atau Docker Compose.

## Integrasi semantik dan fakta

Parser/compiler yang sama dengan search bar mengeksekusi SPARQL read-only pada ontologi aktual, termasuk SIRS named graph, fasilitas evidence graph, SKOS konsep lebih luas, property path wilayah, dan jadwal enrichment. Contoh query hasil eksekusi disimpan di `NARA_3_QUERY_EXAMPLE.sparql`.

Fakta eksplisit: label/kontak RS, observasi layanan SIRS, kapasitas fasilitas terlapor, jadwal bersumber. Inferensi valid: pencocokan sinonim/alias dan perluasan konsep SKOS yang benar-benar mempunyai relasi. Tidak ada inferensi bahwa kelas RS membuktikan kepemilikan suatu fasilitas. ICU/NICU/PICU tetap kondisi terpisah.

Ketiadaan triple adalah **belum diketahui**, bukan bukti layanan tidak ada. Karena itu pencarian negatif layanan seperti “tanpa ICU” memberikan klarifikasi, bukan membentuk daftar yang menyesatkan. Pengecualian identitas/kepemilikan didukung.

## Konteks, verifikasi, keamanan, performa

State bersifat stateless di backend: client menyimpan plan dan ID publik; backend memvalidasi serta memuat ulang fakta dari sumber. Tidak ada tabel session, cookie autentikasi chat baru, atau riwayat medis/koordinat tersimpan permanen. Riwayat menghilang saat halaman dimuat ulang. Fitur pencarian bersifat publik; tidak memberi akses ke data booking/admin.

Pydantic memvalidasi bentuk kondisi, allowlist field, ID `rs-NNN`, maksimum 48 node, kedalaman 12, maksimal tiga ID target, batas hasil 1–20. Parser kurung dibatasi enam tingkat; bagian query maksimum 240 karakter. Pesan API maksimum 4000 karakter. Input query tidak digabungkan mentah ke SPARQL: compiler existing menggunakan literal escaping, allowlist predicate, dan URI whitelist.

ToolRunner membatasi delapan invocation per pesan, timeout service 15 detik, dan workflow 25 detik. Frontend mempunyai AbortController dan timeout 30 detik. Limiter per IP/per worker memiliki burst 40, refill 0,5 token/detik, dan maksimum 2048 bucket; tidak menyimpan teks/koordinat. Triage darurat murah tidak ditunda limiter pencarian.

Cache pencarian maksimum 64 entri/30 detik memakai kondisi kanonis (AND/OR diratakan dan diurutkan), intent, sorting, limit, exclusion, dan token snapshot dataset. Cache menyimpan evidence **sebelum** jarak dihitung, sehingga tidak menyimpan koordinat pengguna dan tidak berbagi hasil ranking lokasi. Pergantian snapshot mengubah key. Tidak ada Redis. Update sumber terlihat mengikuti TTL snapshot, bukan invalidasi push.

Verification produksi memastikan ID/URI berasal dari snapshot dan hasil telah melewati kondisi SPARQL wajib; alternatif dibatasi pada allowed IDs dari query yang sama. Jumlah hasil dihitung setelah verifikasi/penyaringan koordinat. Oracle pengujian menggunakan traversal RDF terpisah, tidak menggunakan query plan chatbot untuk menentukan expected IDs.

Self-correction terbatas pada normalisasi/alias, pemilihan entitas, dan koreksi filter eksplisit. Error sumber data dibedakan dari hasil kosong; tidak ada retry tanpa batas atau penghapusan filter otomatis. Ini belum merupakan self-correction umum untuk semua kalimat.

## Pengujian dan benchmark

Lihat `NARA_3_BENCHMARK_SUMMARY.json` untuk angka final dan `NARA_3_BENCHMARK_RESULTS.csv` untuk setiap skenario.

- Benchmark historis mentah: 75/138 (54,35%).
- Baseline arsip dengan validasi RDF lebih ketat: 73/138 (52,90%). Ini **re-evaluasi arsip**, bukan rerun baseline runtime penuh. Rerun engine lama dihentikan setelah eksekusi berkepanjangan; tidak diklaim selesai.
- Benchmark NARA final: 136/138 (98,55%). Dua kasus tetap gagal menurut oracle lama: typo “Hermna Medan” menghasilkan klarifikasi dua kandidat, dan Medan Johor tidak memiliki hasil dengan bukti alamat yang memadai. Expected result tidak diganti untuk menyembunyikan dua kegagalan itu.
- Unit/integrasi NARA: 22 test; hasil final di `NARA_3_UNIT_TESTS.txt`.
- Regresi mesin search bar: 211/211, oracle RDF independen; hasil di `NARA_3_SEARCH_REGRESSION_SUMMARY.json`.
- Frasa tambahan held-out pertama: 9/12; disimpan di `NARA_3_HELDOUT_INITIAL.json`. Setelah masalah diselesaikan: 12/12 pada regression rerun. Angka 12/12 tidak diklaim sebagai hasil blind held-out pertama.
- Browser Chromium/Edge: welcome, keyboard command palette, request RDF aktual, minimize, expand, filter bertahap, comparison, history/new conversation, location request, map, retry akibat network abort, clipboard, penghapusan filter chip, cancel/confirm hapus percakapan, dan viewport 390×844. Tidak ada JavaScript pageerror dalam suite. Runner browser selesai dengan exit code 0. Screenshot di `screenshots/nara3/`; capture akhir menggunakan reduced-motion agar tidak memotret transisi setengah jalan.
- Build Vite berhasil, tanpa dependency tambahan.
- Suite fitur CariSehat 2: 10/10; regresi jadwal: 4/4.
- `test_backend.py`: 6/7, satu error pada mock test rollback booking (Mock.get menghasilkan objek bukan BookingResponse). Kode booking tidak diubah. Ini dilaporkan, bukan diklaim seluruh regresi backend lulus.

Koreksi oracle dibuktikan dengan RDF: Vita Insani adalah rs-199, bukan rs-200; MRI tidak memiliki evidence afirmatif sehingga hasil kosong adalah benar. Label layanan dibandingkan tanpa membedakan kapitalisasi. Gratitude/farewell merupakan intent eksplisit yang diminta. “Murni Teguh” cocok beberapa entitas aktual sehingga klarifikasi diterima. Criteria layanan/fasilitas/kepemilikan/jadwal dan multi-turn divalidasi terpisah; nonempty saja tidak cukup.

Lingkungan: ASGI/FastAPI + RDFLib atas RDF/named graphs yang sudah ada, serta SQLite test fixture. Ini **bukan** pembuktian live Fuseki/PostgreSQL. Fixture menampilkan warning migrasi PostgreSQL tidak kompatibel SQLite; fitur admin/kuota tidak dinilai lewat fixture ini. Uji bersamaan sempat mencapai timeout; rerun berurutan digunakan untuk hasil fungsional final, bukan klaim load testing.

## Keterbatasan dan pekerjaan yang belum selesai

1. Kode referensi AnimatedAIChat belum tersedia; kesetiaan desain persis belum terverifikasi.
2. Docker CLI dan service Fuseki/PostgreSQL nyata tidak tersedia/terdeteksi pada lingkungan uji ini. Docker Compose tidak diubah, tetapi runtime/deployment Compose belum diuji.
3. Dua kegagalan benchmark di atas tetap dilaporkan; pemahaman bebas tidak universal. Penolakan terkontrol lebih baik daripada informasi rumah sakit tanpa bukti.
4. Confidence masih menggunakan aturan, skor/margin resolver dan hybrid matcher existing; belum ada enam confidence subsystem terkalibrasi dan konfigurasi threshold terpadu seperti spesifikasi penuh.
5. Belum ada general preference-ranking planner atau self-correction otomatis menyeluruh. Negasi layanan tidak tersedia jika tidak ada bukti negatif eksplisit.
6. Riwayat hanya dalam memori halaman; tidak ada penyimpanan lintas perangkat/reload. Ini sengaja menjaga privasi, bukan fitur riwayat persisten yang diklaim selesai.
7. Performa multi-worker, stress/flood deployment, GPS perangkat fisik, keyboard virtual nyata, screen-reader UAT, dan DBpedia live success belum diuji. Limiter hanya per worker; bukan limiter terdistribusi.
8. UAT visual dilakukan pada implementasi lokal, bukan persetujuan pengguna terhadap referensi yang belum diberikan. Font eksternal di bagian website lain dapat tidak termuat pada lingkungan jaringan terbatas; ikon NARA tidak bergantung pada font tersebut.

## Kesiapan Tahap 2

`QueryPlan`, `Condition`, ToolRunner dan `OptionalProvider` memisahkan rencana/evidence dari rendering. Protocol dapat diperluas untuk embedding, retrieval, reranking, LLM dan generative response. Tidak ada provider Tahap 2 yang diinstal, dipanggil, atau diklaim sudah berfungsi. Sebelum mengaktifkannya, pertahankan verification, privacy, dan oracle faktual yang sama.

## Menjalankan dan menguji

Dari root repository, PowerShell:

```powershell
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe tests/test_nara3.py
.\.venv\Scripts\python.exe tests/benchmark_nara3.py archive
.\.venv\Scripts\python.exe tests/benchmark_nara3.py after
.\.venv\Scripts\python.exe tests/test_nara3_heldout.py
.\.venv\Scripts\python.exe tests/run_nara3_search_regression.py
```

Jalankan berurutan. Untuk browser lokal, jalankan fixture di terminal terpisah:

```powershell
.\.venv\Scripts\python.exe tests/runtime_fixture.py
# Terminal lain:
node tests/test_nara3_browser.cjs
```

Buka `http://127.0.0.1:8765` untuk fixture RDF. Untuk deployment aktual gunakan konfigurasi `.env` dan `docker compose up --build` sesuai README, ketika Docker tersedia. Perintah deployment tersebut belum dijalankan dalam tugas ini.
