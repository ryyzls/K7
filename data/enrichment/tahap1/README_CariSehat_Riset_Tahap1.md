# CariSehat — Riset Dataset Tahap 1 (20 November 2026)

## Yang sudah dikerjakan

- Dibaca **206 baris** dari `K7(4).zip` (bukan data baru yang dikarang).
- Ditemukan **36 kandidat kode registrasi Kemenkes** dari nama/identitas yang tertera di sumber RS Online dan rekap resmi. Ini adalah **calon padanan**, bukan 36 rekam yang otomatis diverifikasi sepenuhnya.
- **14 profil** memiliki kolom nama/kelas/jenis/alamat/telepon yang ditranskripsi dari halaman SIRS yang dapat dibaca, dengan sumber per baris.
- **39 fakta layanan** untuk 5 RS dan **16 fakta jenis/kapasitas tempat tidur** untuk 6 RS disalin sebagai fakta yang *tercantum pada profil SIRS*, bukan jaminan layanan tersedia hari ini atau kamar kosong saat ini.
- **170 RS** masih tanpa padanan kode Kemenkes yang dapat disimpulkan aman dari penelusuran ini.
- File hasil **tidak mengubah** `rumah_sakit_sumut.csv`, `hospitals-sumut.ttl`, PostgreSQL, atau Fuseki.

## Cara membaca workbook

- `Ringkasan`: angka dan batasan riset.
- `Master_206`: semua baris asli; ID tetap. Kolom Kemenkes hanya diisi jika ada sumber yang cocok. Kolom `status_operasional_aktual`, `website_resmi_terverifikasi`, dan `email_resmi_terverifikasi` sengaja kosong tanpa bukti.
- `Layanan_Resmi`: layanan yang disebut di profil RS Online, bukan layanan yang sedang buka atau menerima pasien saat ini.
- `TT_Resmi_Sampel`: jumlah kapasitas kamar/bed yang tercatat di profil SIRS; BUKAN ketersediaan kamar real-time.
- `Sumber`: daftar sumber dan URL.
- `Panduan`: catatan audit dan penggunaan yang aman.

## Kendala yang ditemukan

Akses langsung ke endpoint publik `https://sirs.kemkes.go.id/fo/home/rekap_rs_all?id=0` dari lingkungan pengolah file ini tidak berhasil karena DNS/jaringan. Mesin pencarian web dapat membaca sebagian rekap dan profil resmi. Oleh karena itu **tidak jujur mengaku 206 RS sudah diverifikasi**. Juga belum ada bukti individual yang cukup untuk klaim BPJS, dokter beserta jadwal, koordinat bangunan yang tepat, atau status operasional hari ini.

## Cara mempercepat pencocokan lengkap (opsional)

File `CariSehat_sync_master_sirs_readonly.py` merupakan alat *staging* untuk mesin yang bisa mengakses endpoint Kemenkes. Script:

1. Mengunduh endpoint publik sekali, tanpa login atau mengakali pembatasan akses.
2. Memfilter Sumatera Utara dan memadankan nama RS **serta kabupaten/kota yang sama persis setelah normalisasi**.
3. Menulis file `sirs_sumut_snapshot.json`, `matches_exact.csv`, `perlu_review_manual.json`, `belum_cocok.json` ke folder output terpisah.
4. Tidak mengubah source code atau basis data CariSehat. Hasil tidak boleh di-*merge* otomatis tanpa review alamat/cabang/status.

Contoh via Docker (dari folder `K7` di Git Bash, setelah menyalin script dan CSV ke root folder proyek):

```bash
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace backend python CariSehat_sync_master_sirs_readonly.py --input CariSehat_Master_206_Tahap1.csv --out docs/dataset-research/sirs-stage2
```

Jika endpoint menolak permintaan, jangan ulangi agresif atau bypass. Unduh/export resmi melalui browser bila disediakan, lalu lakukan pencocokan lokal.

## Langkah setelah pencocokan

1. Cek hasil ID kandidat, nama, kabupaten, alamat, kelas dan telepon terhadap profil Kemenkes per RS.
2. Audit konflik/duplikat/RS berganti nama; jangan mengubah `rs-NNN` atau menghapus rumah sakit otomatis.
3. Ekstrak pelayanan/fasilitas dari profil resmi atau situs RS, dengan tanggal dan tautan, sebagai tabel relasi baru.
4. Publikasikan hanya yang memiliki bukti; dataset RDF yang lama boleh tetap ada untuk perbandingan namun jangan dianggap fakta klinis per RS.
5. Lakukan regresi 206 RS, SPARQL, RDFa, RDF/XML dan browser sebelum deploy.

### Sumber penting

- https://sirs.kemkes.go.id/fo/home/rekap_rs_all?id=0
- https://sirs.kemkes.go.id/fo/home/dashboard_rs
- https://sirs.kemkes.go.id/fo/home/profile_rs/1276079
- https://sirs.kemkes.go.id/fo/home/profile_rs/1275046
- https://sirs.kemkes.go.id/fo/home/profile_rs/1202029
- https://sirs.kemkes.go.id/fo/home/profile_rs/1273119
- https://satusehat.kemkes.go.id/platform/docs/id/master-data/master-sarana-index/rest-api-msi/
