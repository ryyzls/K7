# Integrasi SIRS Kemenkes ke CariSehat

Tanggal: 20 November 2026 (Asia/Jakarta).

## Status

**PARTIAL untuk verifikasi menyeluruh. Integrasi layanan terkurasi sudah LIVE dan lulus pengujian.**
DBpedia masih mengembalikan `status: unavailable` (HTTP 200), sehingga pengambilan data eksternal belum dapat dinyatakan PASS. Modul DBpedia tidak diubah. Tidak ada klaim bahwa semua data klinis sudah direview atau bahwa layanan tersedia saat ini.

Keputusan pengguna dalam sesi ini: **tahan label klinis sampai direview**. Dengan demikian 239 label klinis tidak dipublikasikan sebagai filter/layanan rumah sakit. Ini keputusan cakupan, bukan kehilangan data.

## Baseline dan audit terarah

- Worktree sudah memiliki perubahan lokal pada frontend, ontologi, backend SPARQL/chatbot, template, dan tes. Perubahan itu dipertahankan; daftar Git keseluruhan bukan daftar pekerjaan integrasi ini.
- File staging yang benar bernama `carisehat_sirs_206_overlay_STAGING.ttl`, bukan nama dengan `.STAGING.ttl` pada deskripsi tugas.
- Generator `scripts/csv_ke_rdf.py` saat ini menurunkan beberapa layanan dari jenis rumah sakit khusus. Backend sebelumnya membaca `hf:menyediakanLayanan`; fallback `hospital_repo` juga membaca relasi tersebut.
- `rdf_loader.py` memuat berkas langsung dalam `semantic/rdf/` ke default graph. Artefak SIRS sengaja ditempatkan pada `semantic/sirs/`, sehingga tidak tercampur oleh loader ini.
- Default graph Fuseki sebelum dan sesudah migrasi: **6.132 triple**, identik secara RDF (`isomorphic`). Jumlah rumah sakit tetap **206**.
- Ontologi lama, generator, sumber CSV, dan TTL staging tidak diubah. Namespace observasi SIRS tetap `http://carisehat.id/ontology/sirs/`, berbeda dari relasi layanan lama.
- Container API ternyata aktif dengan `uvicorn --reload`, sehingga kode termuat otomatis. Tidak dilakukan restart/recreate container, perubahan port, migrasi SQL, reset volume, atau penggantian kredensial.

## Validasi dataset

Validasi executable: `scripts/integrate_sirs.py`; hasil mesin: `semantic/sirs/validation.json`, termasuk SHA-256 seluruh berkas Tahap 3.

| Pemeriksaan | Hasil |
|---|---:|
| ID internal unik dan sama dengan RDF master | 206 |
| Kode Kemenkes unik | 206 |
| Pencocokan nama/kota persis | 203 |
| Identitas dengan review manual pada master | 3 |
| Observasi unik rumah sakit × label | 10.219 |
| Label berbeda | 300 |
| Triple staging, parsing berhasil | 81.967 |
| Triple graph yang disiapkan, roundtrip berhasil | 93.595 |
| Observasi yang diizinkan untuk pencarian | 1.409 |
| Label yang diizinkan | 35 |
| Rumah sakit dengan layanan yang diizinkan | 200 |

Setiap baris layanan diperiksa terhadap URI rumah sakit, kode Kemenkes, record ID, label, kategori, URL profil, waktu pengambilan bertimezone, status publikasi, dan relasi balik observasi. Tidak dilakukan scraping atau verifikasi eksternal baru terhadap profil SIRS; sumber adalah artefak yang disediakan pengguna.

| Kategori kamus | Label | Penggunaan |
|---|---:|---|
| `diagnostik_pemeriksaan` | 34 | Pencarian; `RULE_REVIEWED`, tetap bukan verifikasi operasional |
| `gawat_darurat_terlapor` | 1 | Pencarian; `RULE_REVIEWED`, tetap bukan jaminan kesiapan saat ini |
| `pelayanan_klinis_terlapor` | 239 | Ditahan, `REVIEW_MANUAL`; 6.943 observasi |
| `operasional_pendukung` | 16 | Tidak dipakai sebagai rekomendasi medis; 1.664 observasi |
| `perlu_review` | 10 | Ditahan; 203 observasi |

Rumah sakit tanpa layanan yang lolos kebijakan tetap muncul dalam katalog: `rs-016`, `rs-024`, `rs-026`, `rs-031`, `rs-034`, `rs-206`. Tidak adanya layanan terkurasi **bukan** bukti rumah sakit tidak menyediakan layanan.

Kapasitas tempat tidur **3.466 baris** dan SDM **9.362 baris** diperiksa identitas, URL, tanggal, dan statusnya. Keduanya tidak dimasukkan ke perhitungan tempat tidur kosong, jadwal dokter, booking, atau availability. Sebanyak **537 baris SDM** tidak memiliki grup.

## Implementasi

- Named graph: `http://carisehat.id/graph/sirs/2026-11-19`.
- Semua observasi staging dipertahankan; metadata `cs:statusKurasi` ditambahkan pada artefak turunan. Hanya observasi yang lolos kebijakan mendapat `cs:layakPencarian true`.
- `cs:statusPublikasi STAGING_TIDAK_REALTIME` tetap dipertahankan sebagai status sumber, bukan diam-diam diganti menjadi verified.
- Pencarian, dropdown layanan, dan pencarian darurat memakai observasi eligible di named graph melalui SPARQL. Tidak ada fallback ke relasi layanan inferensi ketika graph tidak ada.
- Fallback lokal chatbot membaca artefak kurasi yang sama, sehingga kegagalan Fuseki tidak menghidupkan kembali layanan hasil asumsi.
- API mengembalikan `layanan_facts` berisi URI observasi, label, kategori, URL sumber, waktu pengambilan, status sumber, status kurasi, dan `reported_not_operationally_verified`.
- Detail frontend menampilkan sumber/tanggal dan disclaimer. RDFa memakai `cs:PelayananTercatat`, bukan menyebut laporan SIRS sebagai `MedicalProcedure` yang tersedia.
- Ekspor per-rumah-sakit menyertakan observasi eligible beserta provenance. Relasi layanan inferensi lama tidak ikut ekspor publik tersebut; data aslinya tetap tersimpan di default graph.
- Metadata OGP, identitas rumah sakit, peta, RDFa Hospital, website resmi, dan SPARQL Studio tetap berfungsi.
- Fasilitas dan BPJS tetap data lama, ditandai belum terverifikasi; integrasi layanan SIRS tidak menjadi bukti verifikasi BPJS.
- Tidak memodifikasi SPARQL Guard atau menambahkan endpoint UPDATE publik.

Contoh live `rs-001`, kode `1276079`: Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping), Laboratorium mikrobiologi, Patologi Klinik, Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu, Radiologi. Sumber: `https://sirs.kemkes.go.id/fo/home/profile_rs/1276079`; waktu pengambilan `2026-11-19T19:17:23.235106+00:00`.

Contoh query read-only:

```sparql
PREFIX cs: <http://carisehat.id/ontology/sirs/>
SELECT ?label ?source ?date ?status WHERE {
  GRAPH <http://carisehat.id/graph/sirs/2026-11-19> {
    <http://localhost:8000/rs/rs-001> cs:catatanPelayanan ?observation .
    ?observation cs:layakPencarian true;
      cs:labelPelayanan ?label; cs:sumberProfil ?source;
      cs:tanggalPengambilan ?date; cs:statusPublikasi ?status .
  }
} ORDER BY ?label
```

## Migrasi, backup, dan rollback

Migrasi dijalankan hanya setelah target named graph dipastikan belum ada. Script menolak overwrite graph yang sudah ada. Backup default graph diparse ulang sebelum penulisan; hasil named graph dibandingkan secara isomorfik dengan artefak dan default graph dibandingkan sebelum/sesudah.

Backup independen dari volume produksi:

- `scratch/sirs-backup-20261120/default-before.ttl`
- `scratch/sirs-backup-20261120/deployed.ttl`
- `scratch/sirs-backup-20261120/migration.json` (`VERIFIED`)
- SHA-256 backup default: `9b07ed8b5640cc92068ba227607784046fee82d3155ef4e53002166c687e4c25`.

Perintah persiapan dan deployment yang digunakan:

```powershell
.venv/Scripts/python.exe scripts/integrate_sirs.py
.venv/Scripts/python.exe scripts/deploy_sirs_graph.py --backup-dir scratch/sirs-backup-20261120
```

Untuk instalasi baru, named graph ini harus dimigrasikan secara eksplisit setelah default graph tersedia. Loader startup lama tidak memuat `semantic/sirs/` otomatis. Jangan memakai `rdf_loader --force` untuk integrasi ini.

Rollback data, **hanya bila diminta**, menggunakan:

```powershell
.venv/Scripts/python.exe scripts/deploy_sirs_graph.py --backup-dir scratch/sirs-backup-20261120 --rollback
```

Rollback hanya menghapus named graph yang baru dibuat setelah memastikan graph tidak berubah sejak deployment. Default graph tidak dihapus/ditimpa. Uji rollback dan penolakan graph yang berubah lulus melalui HTTP mock terisolasi; rollback aktual produksi tidak dijalankan.

Rollback data saja menyebabkan layanan pada API live kosong, tetapi fallback lokal masih memiliki artefak kurasi. Untuk menarik layanan sepenuhnya, lakukan maintenance dan tarik artefak `semantic/sirs/services-reviewed.ttl`, lalu muat ulang backend agar cache lokal hilang. Untuk rollback kode ke perilaku lama, revert **hanya hunk integrasi ini**, bukan `git checkout/reset` seluruh berkas karena ada perubahan anggota lain. Perilaku lama akan kembali memakai inferensi dan memerlukan keputusan tersendiri.

## Pengujian

| Suite | Hasil akhir |
|---|---|
| Validator CSV/RDF/identitas/provenance/roundtrip | PASS |
| `tests/test_sirs_integration.py` | PASS, 8 tes |
| `tests/test_sirs_migration.py` | PASS, 1 tes, deploy/rollback/drift guard mock |
| `tests/test_backend.py` | PASS, 7 tes |
| `tests/test_runtime.py` | PASS, 5 tes, SQLite/RDFLib terisolasi |
| `tests/test_chatbot_rdf_local.py` | PASS, 49 tes |
| `tests/test_chatbot_scenarios.py` | PASS, 14 tes |
| Node frontend/chat/website suites | PASS, 10 tes |
| `backend/tests/test_sparql_guard.py` | PASS, 22 tes dijalankan langsung |
| `scripts/verify_sirs_live.py` | PASS, 6 kelompok pemeriksaan; semua 35 filter tepat |
| `scripts/audit_semantic_e2e.py` | PASS, 13 pemeriksaan HTTP/RDF/metadata |
| `tests/audit_browser_semantic.cjs` | PASS, 11 pemeriksaan; 375/768/1440 px, YASGUI |
| `tests/sirs-browser.cjs` | PASS, 5 pemeriksaan SIRS/provenance/peta/chatbot/JS |
| DBpedia data eksternal | BLOCKED/UNAVAILABLE, HTTP 200 tetapi status unavailable |
| Rollback aktual produksi / restore volume | NOT TESTED, tidak diperlukan untuk rollout non-destruktif ini |

Bukti JSON: `docs/sirs-tests/live.json`, `semantic-e2e.json`, `browser.json`, serta `docs/semantic-audit-output/patch06/browser_semantic_report.json`. Screenshot responsive berada di direktori patch06 tersebut. Tidak ada booking produksi yang dibuat/dihapus; tes booking hanya memakai SQLite memory pada runtime fixture.

Kegagalan awal yang sudah ditangani:

- Browser sandbox tidak dapat mengambil CDN (`ERR_NETWORK_ACCESS_DENIED`, `L is not defined`); pengujian diulang dengan akses jaringan dan lulus.
- Tes website lama memakai regex CSS yang tidak menerima whitespace; diperbaiki tanpa mengurangi pemeriksaan `overflow-wrap:anywhere`.
- Tes runtime lama mengharapkan chatbot error saat Fuseki mati; disesuaikan untuk fallback lokal yang memang sudah tersedia, sekaligus menguji SIRS dan penahanan label klinis.
- Tes gate booking awal memakai URL yang bukan route operator (404); diperbaiki ke `/api/booking/rs/rs-001`, hasil 403 tanpa key.
- `pytest` tidak terpasang dan unittest tidak menemukan fungsi tes guard. Suite tersebut memiliki runner sendiri; dijalankan langsung dan seluruh 22 kasus lulus, tanpa instalasi dependency.
- Dua iterasi tes RDFLib yang lambat dihentikan untuk memperbaiki query pengujian; suite final lulus, hasil yang dihentikan tidak dihitung PASS.

## File yang disentuh oleh integrasi ini

Baru:

- `backend/app/services/sirs.py`
- `scripts/integrate_sirs.py`
- `scripts/deploy_sirs_graph.py`
- `scripts/verify_sirs_live.py`
- `semantic/sirs/services-reviewed.ttl`
- `semantic/sirs/validation.json`
- `tests/test_sirs_integration.py`
- `tests/test_sirs_migration.py`
- `tests/sirs-browser.cjs`
- Laporan ini dan bukti `docs/sirs-tests/`.

Modifikasi terarah, mempertahankan perubahan lokal sebelumnya:

- `backend/app/services/sparql_service.py`
- `backend/app/services/hospital_repo.py`
- `backend/app/services/chatbot/formatters.py`
- `backend/app/services/chatbot/models.py`
- `backend/app/templates/rs_detail.html`
- `frontend/index.html`
- `tests/runtime_fixture.py`
- `tests/test_runtime.py`
- `tests/test_websites_frontend.cjs`
- Artefak hasil browser di `docs/semantic-audit-output/patch06/` diperbarui oleh runner yang sudah tersedia.

## Risiko dan review berikutnya

1. Review klinis/editorial 239 label sebelum memperluas publication gate. `RULE_REVIEWED` hanya validasi pengelompokan, bukan survei layanan di lapangan.
2. Identitas administratif sudah dipasangkan, tetapi atribut master masih perlu review: `rs-017` telepon; `rs-048`, `rs-066`, `rs-120`, `rs-153` alamat. Alias nama: `rs-037`, `rs-069`, `rs-114`. Nama/alamat master tidak ditimpa.
3. 38 kelebihan baris duplikat layanan mentah dinormalisasi menjadi 10.219 pasangan unik menurut staging; file review duplikat tetap disimpan.
4. Enam rumah sakit tanpa layanan eligible tidak boleh ditafsirkan tidak memiliki layanan. Sediakan review lanjutan, jangan isi dengan kelas/kepemilikan.
5. Deployment berikutnya harus membawa artefak lokal dan named graph dengan versi yang sama. Tidak ada sinkronisasi edit langsung dari Fuseki ke artefak fallback.
6. Backup ada di luar volume, tetapi belum disalin ke perangkat independen. Jangan hapus direktori backup sampai rollout diterima.
7. DBpedia belum terbukti dapat mengambil data saat pengujian ini. Dependensi CDN tetap membutuhkan koneksi internet.
8. `--reload` adalah konfigurasi aktif yang sudah ada, bukan perubahan integrasi ini; perubahan Python berikutnya akan langsung dimuat.
9. Belum ada commit/push; jangan stage semua perubahan Git karena worktree juga berisi pekerjaan anggota lain.
