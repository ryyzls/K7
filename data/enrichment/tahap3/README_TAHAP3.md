# CariSehat: hasil olah data SIRS 206 RS — Tahap 3

## Hasil nyata
- 206 kode RS dipasangkan dan diuji konsisten terhadap master.
- 10,257 baris pelayanan asli; 10,219 kombinasi unik RS × label layanan (selisih 38 baris). Data mentah tetap utuh dalam ZIP sumber.
- 300 label layanan berbeda diklasifikasi konservatif; status per label tercantum pada `kamus_300_layanan.csv`.
- 3,466 baris kapasitas TT (1,594 bernilai nol); 9,362 baris SDM (537 tanpa grup). **Tidak ada perhitungan TT kosong atau penjumlahan SDM.**
- RDF overlay dibuat dan diuji roundtrip: **81,967 triples**.

## Keputusan keamanan data
- Semua data tetap **staging**, bukan klaim ketersediaan layanan saat ini.
- Label tertentu diklasifikasi sebagai `perlu_review`; label lainnya yang dikelompokkan otomatis juga tetap memerlukan review medis/editorial sebelum publikasi sebagai kategori resmi.
- Relasi RDF yang dibuat: `cs:catatanPelayanan` dan entitas `cs:PelayananTercatat`. **Bukan** `hf:menyediakanLayanan`. Dengan demikian ia tidak bercampur secara semantik dengan tautan layanan hasil perkiraan generator terdahulu.
- Jangan mengimpor TTL ke default graph produksi, menghapus layanan lama, menimpa `hospitals-sumut.ttl`, atau menampilkan fasilitas/SDM/TT sebagai real-time.
- `sirs_tempat_tidur_raw.csv` merekam **kapasitas kategori** sebagaimana dilaporkan, bukan ketersediaan. SDM bukan daftar dokter.
- Data sumber Kemenkes diperlakukan sebagai laporan rumah sakit, tidak menyatakan izin atau jadwal pelayanan terbaru.

## Integrasi aman yang bisa dilakukan setelah review
1. Simpan file hasil di `data/enrichment/tahap3/`.
2. Lakukan review kamus kategori (terutama `REVIEW_MANUAL`) dan kasus prioritas TINGGI.
3. Backup Fuseki dan lakukan staging ke **named graph terpisah** hanya jika kode backend sudah diuji.
4. Query demonstrasi di bawah mengambil data SIRS secara eksplisit, tidak menggabungkan ke predicate layanan hasil inferensi.

```sparql
PREFIX cs: <http://carisehat.id/ontology/sirs/>
PREFIX rs: <http://localhost:8000/rs/>
SELECT ?label ?kategori ?sumber WHERE {
  rs:rs-001 cs:catatanPelayanan ?obs .
  ?obs cs:labelPelayanan ?label ; cs:kategoriKurasi ?kategori ; cs:sumberProfil ?sumber .
} ORDER BY ?label LIMIT 50
```

## Bukti dan batasan
Input dari `hasil_profil_sirs_206.zip` yang diunggah user dan `CariSehat_Master_206_Rekonsiliasi_SIRS.csv`. Tidak melakukan scraping baru. Audit ini adalah pemeriksaan struktur, identitas dan normalisasi label; **bukan verifikasi klinis per RS di lapangan**.
