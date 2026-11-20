# Website resmi RS

## Audit dan arsitektur

Audit 19 November 2026: 206 RS; CSV asli tidak punya kolom website dan RDF awal
tidak mempunyai URL website. API telah membaca `schema:url`, tetapi UI sebelumnya
menampilkannya tanpa status verifikasi. PostgreSQL tetap dipakai untuk booking,
bukan sebagai sumber website tambahan. Tidak ditemukan AGENTS.md di checkout.

Sumber runtime tetap RDF:

1. `data/website_reviews.json`: catatan hasil pemeriksaan manual untuk impor, bukan
   database yang dibaca pada setiap request. ID `rs-NNN`, nama dan alamat RDF
   wajib cocok. Jangan membuat ID baru dari urutan hasil pencarian.
2. `scripts/enrich_websites.py`: validasi dan impor batch.
3. `semantic/rdf/hospital-websites.ttl`: tambahan RDF terpisah agar regenerasi
   `hospitals-sumut.ttl` tidak menghapus hasil pemeriksaan.
4. Fuseki/SPARQL dan fallback `hospital_repo` membaca metadata yang sama.
5. `website.py` mengizinkan URL publik hanya ketika status `verified` disertai
   bukti dan waktu pemeriksaan. Kandidat berada di `hf:websiteCandidate`, tidak
   dalam field API `website`.

Metadata: `schema:url`, `hf:websiteStatus`, `hf:websiteEvidence`,
`hf:websiteCheckedAt`, `hf:websiteScope`, `hf:websiteNotes`.
Status: `unreviewed`, `verified`, `needs_review`, `not_found`. `not_found` berarti
pencarian belum menemukan website, bukan pernyataan bahwa RS tidak memilikinya.
Cakupan URL: `hospital`, `branch`, atau `network` (UI memberi label jaringan).

## Menambah hasil pemeriksaan

Cari nama RS + kabupaten/kota + Sumatera Utara; buka sumber resmi dan halaman
kandidat. Cocokkan cabang, alamat, telepon dan pengelola. Catat bukti dan perbedaan
data pada `notes`. Jangan menyetujui berdasarkan nama domain, snippet, HTTP 200,
direktori komersial, Google Maps, berita, atau media sosial saja. Jangan melewati
login/CAPTCHA/pembatasan akses. Jika tidak cukup bukti, gunakan `needs_review`.

Salin struktur record yang ada; `checked_at` harus waktu pemeriksaan sebenarnya
dengan zona waktu. `nama` dan `alamat` harus persis nilai RDF yang diperiksa.
Simpan URL kandidat dalam `url` dengan status non-verified: importer otomatis
menyimpannya sebagai kandidat, tidak mempublikasikannya.

```powershell
.venv/Scripts/python.exe scripts/enrich_websites.py --input data/website_reviews.json --batch-size 10 --offset 0
# Setelah review, sinkronkan hanya properti website ke dataset Fuseki terkonfigurasi:
.venv/Scripts/python.exe scripts/enrich_websites.py --input data/website_reviews.json --batch-size 10 --offset 0 --publish
```

Batch 1–100 record, satu proses pada satu waktu. File diganti secara atomik setelah
seluruh batch valid; impor ulang menghasilkan graph yang sama. Status lebih lemah
atau pemeriksaan lebih lama tidak menggantikan hasil verified. Output CLI memuat
jumlah status dan antrean review. Jalankan ulang untuk retry; tidak ada crawler
kandidat di aplikasi maupun CLI, sehingga tidak ada request/redirect ke URL input,
API key, atau pencarian saat halaman dibuka. Penelusuran kandidat dilakukan secara
manual memakai browser/search. Satu-satunya request CLI opsional adalah ke Fuseki
terkonfigurasi: timeout 15 detik, maksimal 2 percobaan, tanpa redirect, concurrency 1.

Loader RDF yang sudah ada otomatis membaca file tambahan pada dataset kosong.
Untuk dataset aktif gunakan `--publish` agar tidak menghapus data lain. Setelah
mengubah RDF, restart backend bila cache chatbot lokal sudah dimuat. UI detail
membaca Fuseki secara langsung. Jangan jalankan dua importer bersamaan.

## Batch awal dan bukti

| ID | Hasil | Bukti identitas |
|---|---|---|
| rs-171 | verified | [Kontak Adam Malik](https://rsham.go.id/profil/hubungi-kami), nama dan Bunga Lau 17 Medan cocok; [direktori Kemenkes](https://rs.kemkes.go.id/hospitals/all/rs-h-adam-malik) menunjuk domain yang sama. Nomor telepon situs berbeda, data telepon lama tidak diubah. |
| rs-007 | verified, branch | [Columbia Asia Aksara](https://columbiaasia.co.id/rs-columbia-asia-aksara/informasi-umum-aksara/), Letda Sujono LK X 90 Medan dan 06188806888 cocok. |
| rs-008 | verified, branch | [Cabang Medan](https://columbiaasia.co.id/rs-columbia-asia-medan/) dan [kontak jaringan](https://columbiaasia.co.id/hubungi-kami/), Listrik 2A Medan dan 0614566368 cocok; bukan cabang Aksara. |
| rs-125 | needs_review | [Kandidat Hermina Medan](https://herminahospitals.com/id/branch/hermina-medan) terbuka tetapi isi identitas tidak terbaca oleh alat penelusuran (iframe). Tidak dipublikasikan. |

Cakupan: **4 diperiksa; 3 verified; 1 needs_review; 0 not_found; 202 unreviewed**.
Ke-202 RS tersebut belum ditelusuri, bukan dianggap tidak memiliki website.
Pemeriksaan lanjutan harus dilakukan sebelum menambah tautan publik.

## Pengujian

```powershell
.venv/Scripts/python.exe tests/test_websites.py
node tests/test_websites_frontend.cjs
```

Mencakup URL/status gates, ID/cabang, impor berulang dan perlindungan downgrade,
penempatan tautan, atribut tab aman, parsing JavaScript, CSS focus dan overflow.
Empat template query SPARQL juga diperiksa sintaksnya. Uji CSS/markup ini tidak
menggantikan uji visual atau interaksi browser. API aktif telah diuji: 206 RS,
3 URL publik; halaman RDFa rs-171, rs-007, rs-008, rs-125, dan rs-001 lulus
pemeriksaan tautan/status serta atribut keamanan. Uji tersebut tidak
menggantikan uji visual atau interaksi browser. Pemeriksaan desktop/mobile,
tab keyboard, klik rute dan hotline secara langsung masih perlu dilakukan;
Playwright dan alat browser tidak tersedia pada sesi implementasi.
