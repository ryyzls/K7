# NARA 3 — UAT Checklist

Tanggal: 25 November 2026. PASS berarti diuji pada fixture lokal dengan RDF aktual, bukan deployment Fuseki/PostgreSQL. `PENDING` belum diverifikasi.

| Area | Kriteria | Status / evidence |
|---|---|---|
| Welcome | Identitas/logo lama, panel gelap, enam quick actions | PASS; screenshots/nara3/welcome-floating.png |
| Floating/expanded | Sesi tetap sama setelah minimize/expand | PASS; browser suite |
| Command palette | Arrow navigation dan Tab memilih command; Enter mengirim | PASS; browser suite |
| Input | Textarea bertambah tinggi, Enter/Shift+Enter, batas pesan | Implemented; interaksi Enter diuji, UAT keyboard fisik/mobile lanjutan PENDING |
| Search | Medan, layanan, kelas, fasilitas sesuai RDF | PASS; unit + benchmark |
| Boolean | AND/OR/grouped conditions/exclusion | PASS; unit dan shared search regression |
| Context | Medan → kelas B → ICU → CT Scan → Siantar → hapus CT Scan | PASS; unit |
| New query | Pencarian baru tidak memakai target RS lama | PASS; unit |
| Selection | Hasil pertama/kedua dan kontak follow-up | PASS; unit |
| Comparison | Maksimum tiga RS, tabel dan kontak dari service aktual | PASS; unit + browser |
| Alternatives | Kandidat disaring filter wajib sebelum ranking | PASS; unit |
| Location | Tanpa GPS meminta lokasi; ranking geografis mengabaikan koordinat tidak memadai | PASS; unit |
| GPS device | Browser permission granted/denied pada perangkat fisik | PENDING; handler dan manual-region fallback tersedia |
| Map | Peta hasil memakai koordinat sumber, link navigasi | PASS; browser + map.png |
| Hours | Jadwal per unit, bukan klaim buka real-time; filter anak tetap ada bersama Sabtu | PASS; unit + benchmark |
| Safety | Triage sebelum query/GPS; negasi, hipotetis, masa lalu | PASS pada suite yang ditetapkan; bukan validasi klinis universal |
| Security | Injeksi, ID/payload invalid, limiter, isolasi konteks | PASS pada suite lokal |
| Error/retry | Network abort menampilkan retry yang mengirim request aktual | PASS; browser |
| History | Sesi baru/riwayat sementara | PASS; browser |
| Delete/copy | Konfirmasi hapus dan Clipboard API | PASS; browser menguji clipboard serta cancel/confirm penghapusan |
| Responsive | Panel/input berada dalam viewport 390×844 | PASS; mobile.png |
| Reduced motion | Animasi dinonaktifkan melalui media preference | PASS; screenshot/browser run terakhir |
| Accessibility | Label tombol dan keyboard command palette | PASS terbatas; screen-reader UAT PENDING |
| Regression | Search bar 211 skenario | PASS 211/211 |
| Other features | Fitur CariSehat 2 + jadwal | PASS 10/10 + 4/4 |
| Booking test | Mock rollback test lama | FAIL 1/7 backend suite; kode booking tidak diubah |
| DBpedia | Kegagalan regional tidak menghalangi pencarian RS | PASS; unit. Live success PENDING |
| Exact reference | Kesetiaan terhadap kode AnimatedAIChat | PENDING; kode referensi belum tersedia |
| Docker | Compose dengan Fuseki/PostgreSQL aktual | PENDING; tidak tersedia pada lingkungan ini |
| Performance | Stress concurrency dan multi-worker | PENDING; jangan gunakan hasil fungsional sebagai load-test |

## Skenario manual penerimaan pengguna

1. Buka NARA, cari `RS di Medan dengan ICU`, lalu expand dan minimize. Pastikan pesan tetap ada.
2. Ketik `/`, gunakan Arrow Down dan Tab, lengkapi command, kirim.
3. Ikuti rangkaian filter pada tabel konteks; akhir harus Siantar + kelas B + jantung + ICU, tanpa CT Scan.
4. Pilih dua/tiga RS, bandingkan, buka detail, kembali ke chat.
5. Aktifkan lokasi dengan izin browser; periksa label jarak garis lurus, peta, dan navigasi. Ulangi dengan izin ditolak dan ketik wilayah manual.
6. Periksa jadwal satu RS: jadwal dokter yang tidak tercatat tidak boleh dibuat-buat.
7. Putuskan jaringan sementara, kirim, sambungkan kembali, tekan Coba lagi.
8. Hapus percakapan dengan cancel lalu confirm; uji copy response.
9. Ulangi pada perangkat mobile dengan keyboard virtual dan screen reader.

Persetujuan pengguna dan deployment production belum diberikan/dilakukan; checklist ini bukan klaim sign-off final.
