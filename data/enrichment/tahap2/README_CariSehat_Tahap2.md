# CariSehat — Pengayaan SIRS Tahap 2 (STAGING, 20 November 2026)

## Isi paket
- `CariSehat_Tahap2_Staging_20Nov2026.xlsx`: workbook review, terdiri atas Ringkasan, Profil_206, Layanan_Staging, TT_Staging.
- `CariSehat_Tahap2_Profil_206_Staging.csv`: 206 identitas RS dengan kode dan URL profil **kandidat** (tidak berarti URL tiap RS telah diperiksa).
- `CariSehat_Tahap2_Layanan_Staging.csv`: 85 catatan layanan dari 7 RS (39 lama + 46 hasil pembacaan manual **pilihan**, bukan daftar lengkap).
- `CariSehat_Tahap2_Kapasitas_TT_Staging.csv`: 37 catatan kapasitas terlapor, **bukan ketersediaan real-time**.
- `CariSehat_scrape_profiles_sirs_staging.py`: script baca profil SIRS, hanya menghasilkan file baru di staging; tidak menyentuh Fuseki, PostgreSQL atau CSV asli.

## Asal data
- Identitas RS: rekap Kemenkes (snapshot dari pengguna, 19 November 2026 18:45 UTC), direkonsiliasi pada Tahap 1.
- Sampel layanan/TT tahap 1: CSV `CariSehat_Layanan_Resmi_Tahap1.csv` dan `CariSehat_TT_Resmi_Sampel_Tahap1.csv`.
- Tambahan tahap 2: `https://sirs.kemkes.go.id/fo/home/profile_rs/1278013` (RS Metta Medika, Kota Gunungsitoli) dan `https://sirs.kemkes.go.id/fo/home/profile_rs/1275890` (RSU Bunda Thamrin, Kota Medan). Data disalin dari bagian tabel **Data Pelayanan** dan **Data Tempat Tidur**, hanya contoh terpilih. Tanggal cek riset: 2026-11-20.

## Simpan ke K7
- Salin tiga CSV + Excel ke `K7/data/enrichment/tahap2/` (buat folder jika belum ada).
- Salin `CariSehat_scrape_profiles_sirs_staging.py` ke `K7/scripts/`.
- Simpan README bersama CSV tahap2.

## Uji tiga profil dulu (Git Bash di folder K7)

```bash
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace backend python scripts/CariSehat_scrape_profiles_sirs_staging.py --input data/enrichment/tahap1/CariSehat_Master_206_Rekonsiliasi_SIRS.csv --out data/enrichment/tahap2/hasil_profil_sirs --limit 3
```

Jika mengeluarkan `EXTRACTED`, periksa `profile_fetch_status.csv`, `sirs_pelayanan_raw.csv`, `sirs_tempat_tidur_raw.csv`, `sirs_sdm_raw.csv`. **Jangan langsung menjalankan seluruh 206** jika hasil pertama `PARSE_REVIEW` atau `FETCH_ERROR`. Ini harus diperbaiki sebelum lanjut.

Jika tiga profil pertama sukses dan datanya masuk akal, uji 15 profil berikutnya dengan perintah yang sama kecuali `--limit 15`. Script menyimpan HTML yang sudah diunduh untuk dipakai lagi, dan hanya menambahkan permintaan baru untuk yang belum di-cache. Setelah itu baru `--limit 206`. Diperkirakan perlu setidaknya beberapa menit untuk 206 permintaan; hindari beban berlebihan pada server dan patuhi kebijakan akses Kemenkes. Jika muncul rate limiting/403, berhenti. Jangan bypass pembatasan.

## Interpretasi data
- `EXTRACTED` hanya menandai script dapat membaca halaman dan struktur tabel dengan kecocokan nama memadai. Tidak otomatis memverifikasi status operasional, layanan klinis real-time, atau tahun pembaruan datanya.
- `IDENTITY_REVIEW`: nama profil berbeda signifikan dari master, sehingga harus direview.
- `PARSE_REVIEW`: tabel tidak terbaca atau format situs berubah. **Jangan anggap kolom kosong artinya RS tidak memiliki layanan.**
- `FETCH_ERROR`: tidak bisa mengambil HTML, tidak boleh mengklaim telah diteliti.
- `Data SDM` adalah jumlah profesi/tenaga terlapor, **bukan nama atau jadwal dokter**.
- Pembedaan fasilitas dari layanan memerlukan mapping konsep yang ditinjau manual; misalnya `CT Scan` di tabel pelayanan tidak membuktikan scanner sedang tersedia/operasional.
- Jangan memasukkan data yang belum di-review ke rekomendasi pasien atau SPARQL publik.

## Output laporan yang dikirim kembali ke ChatGPT
Upload `manifest.json`, `profile_fetch_status.csv`, dan **beberapa baris sampel** dari tiga CSV hasilnya, untuk memeriksa ekstraksi. Bila terbatas, upload keempat CSV dan `manifest.json`. Jangan upload seluruh `html_cache` jika tidak dibutuhkan.
