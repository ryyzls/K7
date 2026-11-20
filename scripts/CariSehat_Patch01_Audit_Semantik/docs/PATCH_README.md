# CariSehat — Patch 01: Audit kualitas semantik (aman, non-destruktif)

## Mengapa ini dulu?
Dataset saat ini memiliki relasi layanan/fasilitas/BPJS hasil generator berbasis kelas RS, yang tidak sama dengan verifikasi individual. Audit ini menginventarisasi masalah per RS sebelum perubahan RDF/ontologi yang berisiko. Tidak ada klaim verifikasi otomatis.

## Cara memasang
1. **Jangan menimpa file Codex yang sedang diedit.** Salin hanya `scripts/audit_semantic_quality.py` ke folder `scripts/` pada proyek `K7`.
2. Buka terminal VS Code pada root `K7`.
3. Jika `rdflib` belum tersedia pada Python host, jalankan `python -m pip install rdflib` di environment proyek (atau jalankan dari container yang sudah memilikinya).
4. Jalankan `python scripts/audit_semantic_quality.py`.
5. Baca `docs/semantic-audit-output/summary.json` dan `hospital_quality_review.csv`.

## Apa yang dilakukan
- Membaca RDF utama, koordinat CSV, dan graph website yang sudah ada.
- Menghitung jumlah RS/triple, status website, dan sumber koordinat.
- Menandai layanan/fasilitas/BPJS yang dihasilkan generator sebagai **perlu verifikasi**, bukan menghapus atau mengklaim salah.
- Menghasilkan CSV per RS yang dapat dipakai sebagai daftar kerja untuk pengayaan berikutnya.

## Yang TIDAK dilakukan
- Tidak mengubah RDF/ontologi/website, SQL, frontend, Docker, maupun database.
- Tidak mengakses internet dan tidak scraping.
- Tidak menjalankan loader Fuseki, migrasi, atau `docker compose down`.
- Tidak mengklaim website/email/layanan sebagai verified tanpa bukti.

## Pengujian dan rollback
- Hapus hanya `scripts/audit_semantic_quality.py` dan `docs/semantic-audit-output/` jika ingin membatalkan patch.
- Jalankan ulang setelah Codex menyelesaikan website untuk memperoleh laporan terbaru.
