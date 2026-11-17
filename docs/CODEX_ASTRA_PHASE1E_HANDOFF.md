# CariSehat — Codex Astra Phase 1E Handoff

Tanggal: 17 November 2026 (Asia/Jakarta).

## 1. Executive summary
**PARTIAL untuk deployment produksi; perbaikan P0 terimplementasi dan teruji.** Idempotency PostgreSQL lolos concurrency, conflict, rollback, lost acknowledgement, dan replay lintas proses. Navigasi detail dan filter sesudah kembali lolos pada 375/768/1440. Restore drill PostgreSQL/Fuseki dan role runtime sintetis terbatas berhasil. Produksi tidak dimigrasi atau direstart; backend aktif masih versi proses sebelum 1E. Persetujuan eksplisit dibutuhkan untuk rollout backend/schema produksi.

## 2. Baseline sebelum perubahan
Git sudah dirty dari anggota dan Tahap 1 sebelumnya. Diff terhadap HEAD bukan kontribusi 1E saja. Handoff Antigravity menyebut audit/perencanaan read-only. Frontend berbeda dari snapshot 1D; edit ditahan sampai pengguna mengonfirmasi tidak sedang diedit agent lain dan memberi izin perbaikan navigasi.

Sumber yang dibaca: laporan K–L, rollout plan 1D, handoff UI/UX, migrasi 001 up/down, booking/model, tests dan bagian CSS/JS terkait. Port loopback/206 RS dari 1D dipertahankan. Database test carisehat_test_phase1d terpisah; migrasi 001 memiliki dua CHECK booking. Produksi memiliki satu booking. Backup PostgreSQL archive-list valid sebelum tindakan.

## 3. File yang diubah pada 1E
- backend/app/routers/booking.py: persistent idempotency, snapshot response sebelum commit, validasi tanggal untuk operasi baru.
- database/migrations/002_booking_idempotency.up.sql dan .down.sql: ledger PostgreSQL, tidak terdaftar pada Base.metadata sehingga startup create_all tidak diam-diam membuat ledger produksi.
- frontend/index.html: modal detail dipindah ke body saat inisialisasi; chat tertutup benar-benar display:none; klaim hero “terverifikasi” dikoreksi menjadi “dalam dataset”. Tidak redesign.
- tests/test_backend.py: mock failure mengikuti flush sebelum commit.
- tests/phase1e_postgres.py: runner PostgreSQL opt-in, bukan unittest discovery.
- tests/phase1e-browser.cjs: browser live, request tulis booking diblokir.
- docs/CODEX_ASTRA_PHASE1E_HANDOFF.md dan STABILIZATION_PHASE1_REPORT.md.

Model ORM dan migrasi 001 merupakan pekerjaan 1D, tidak diklaim sebagai perubahan baru 1E. Tidak mengubah CSV, RDF, OWL, generator, .env; tidak commit/push/reset/stash.

## 4. Perbaikan idempotency
Kontrak header opsional Idempotency-Key: 16–128 karakter ASCII alfanumerik, underscore atau hyphen. Anjurkan UUID acak baru per operasi, pertahankan key yang sama untuk retry. Request tanpa key tetap didukung, tetapi tidak dijamin idempotent.

Ledger menyimpan scope POST:/api/booking:v1, SHA-256 key, SHA-256 payload ternormalisasi dan booking_id FK. Primary key (scope,key_hash) menjamin satu operasi. Payload fingerprint dihitung sebelum nama RS diganti nama canonical Fuseki; perubahan nama client atau field bermakna lain tetap terdeteksi. Whitespace/default JSON dinormalisasi oleh model; bukan fingerprint byte HTTP mentah. Tidak menyimpan nama pasien, telepon, catatan atau response JSON pada ledger. Hash bukan enkripsi: akses DB tetap harus dibatasi.

INSERT ON CONFLICT DO NOTHING RETURNING menunggu transaksi pemilik key. Reservasi ledger, booking, dan pengisian FK terjadi dalam satu transaksi. Request sama membaca booking yang sudah committed; berbeda menghasilkan 409. Collision kode booking rollback seluruh reservasi lalu retry maksimal lima kali. Snapshot BookingResponse dibentuk setelah flush sebelum commit, sehingga tidak ada refresh sesudah commit yang memicu insert ulang. Jika commit acknowledgement hilang, retry keyed mengambil operasi committed. Booking yang dibatalkan tetap replay ke ID yang sama dengan status terkini, bukan membuat booking baru.

Tanggal lampau ditolak hanya untuk operasi baru setelah pengecekan replay, sehingga retry sah hari berikutnya tetap bekerja. Legacy tanpa key masih memiliki risiko duplicate bila client mengulang setelah respons hilang. Frontend lama belum mengirim key; integrasi client harus dilakukan bersama rollout backend agar tidak mengklaim UI sudah terlindungi otomatis.

Scope global endpoint sesuai API publik yang belum memiliki akun. Key harus tidak ditebak dan tidak dibagikan. Mengetahui key saja tidak cukup untuk replay: fingerprint payload harus cocok. Belum ada TTL/cleanup ledger atau idempotency retention policy; jangan menghapus ledger otomatis karena akan membuka duplicate operation. Replay masih melewati validasi input dan lookup Fuseki; outage sumber semantik dapat menghalangi replay sementara, tetapi tidak membuat booking kedua.

## 5. Perbaikan navigasi detail
Reproduksi live: tombol kembali y sekitar 14px; elementFromPoint menunjuk HEADER. Modal z-index 2500 terperangkap dalam aside z-index 100, sedangkan header z-index 1100. Perbaikan memindah node #detail ke document.body saat init; event delegation document tetap bekerja. Tidak force-click dan tidak sekadar menaikkan z-index child.

Expanded mobile test menemukan closed Deep Chat masih menangkap pointer walaupun bubble tidak open. Dibuktikan elementFromPoint di filter C mengembalikan deep-chat pada y sekitar 427px. Selector #chat-bubble:not(.open) #chat-container {display:none} menghapus hit target saat tertutup. Widget kembali bekerja ketika dibuka.

Suite akhir: back dan filter C=120 setelah kembali pada 375/768/1440 PASS; tanpa horizontal overflow. Tes akhir memakai reduced-motion dan scroll normal ke tengah, bukan force-click. Suite standar motion sebelumnya sudah lulus 11 checkpoint setelah perbaikan modal, sebelum expanded mobile menemukan closed-chat issue. Tidak mengklaim seluruh variasi motion/perangkat fisik sudah diuji.

## 6. Migrasi dan PostgreSQL tests
002 up/down/up benar-benar dijalankan pertama kali pada database test. Up: CREATE TABLE ledger + composite PK + FK RESTRICT. Down: DROP TABLE ledger saja, tanpa menghapus booking; kehilangan replay protection adalah dampak penting rollback. DDL memakai transaksi dan lock_timeout. Migrasi versioned file, belum migration ledger otomatis; jangan rerun up tanpa memeriksa objek. Runner ulang mempertahankan ledger existing dan mencatat migration drill SKIPPED, lalu tetap menguji transaksi dengan key acak baru.

Hasil PostgreSQL asli (session dependency test; tanpa menjalankan lifespan aplikasi produksi):
- 8 request bersamaan, key/payload sama: semua 201, satu ID canonical.
- Key sama payload berbeda: 409; dua payload berbeda bersamaan: tepat 201/409.
- Key terlalu pendek/panjang/karakter tidak valid: 422.
- Collision kode lalu retry: 201; lima collision: 409; key yang rollback dapat dipakai ulang sukses.
- Commit berhasil lalu synthetic OperationalError: 503; retry mengembalikan satu operasi committed.
- Replay sesudah pool dispose dan pada dua proses Python independen: ID sama.
- Replay hari berikutnya: 201 dengan ID sama; operasi baru bertanggal lampau: 422.
- Operator tanpa key: GET/DELETE 403; dummy authorized cancellation: 200; replay tidak membuat booking baru setelah cancel.
- Legacy tanpa idempotency header: 201.
- Produksi sebelum/sesudah runner: count=1, fingerprint row lengkap dalam memori sama. Fingerprint/nama pasien tidak dicetak. Pemeriksaan final: production booking_idempotency tidak ada.

Reproduksi runner: baca kedua SQL 002 di host, prepend variabel Python MIGRATION_UP dan MIGRATION_DOWN menggunakan repr, lalu kirim tests/phase1e_postgres.py melalui `docker exec -i carisehat-api python -B -`. Guard current_database() harus tepat carisehat_test_phase1d sebelum DDL/DML. Jangan menjalankan terhadap carisehat. Supplemental tests lintas proses/conflicting concurrency/next-day dijalankan melalui stdin, belum dipaketkan ke runner utama.

## 7. Backup/restore verification
Pengguna menyetujui restore drill terisolasi dan mempertahankan resource sampai cleanup disetujui.
- PostgreSQL backup: /var/lib/postgresql/data/phase1d-backups/before-phase1d.dump. pg_restore --list PASS. Restore --exit-on-error ke carisehat_restore_phase1e PASS: 4 tabel, 1 booking. CONNECT database dicabut dari PUBLIC. Database ini mengandung salinan backup pasien, **bukan fixture sintetis**; jangan dipakai untuk test tulis/menampilkan identitas.
- Fuseki archive: C:/Users/User/AppData/Local/CariSehat-private-backups/20261117T094320Z/fuseki-data.tar. Dipulihkan ke volume baru carisehat_phase1e_restore, container carisehat-fuseki-restore-phase1e, image ID sama dengan Fuseki aktif, network=none dan tanpa port host. Query via curl dari dalam container: 206 RS PASS.
- Produksi tidak menjadi target restore, tidak downtime, tidak mengganti kredensial. Resource restore tetap ada. Backup PostgreSQL masih pada volume produksi yang sama; salinan backup independen/off-host tetap rekomendasi terpisah.

## 8. Least privilege
Dibuat role sintetis NOLOGIN phase1e_test_runtime (cluster role, hanya diberi grants di database test): NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOINHERIT. USAGE schema public; SELECT/INSERT/UPDATE booking_kamar dan booking_idempotency; USAGE/SELECT sequence booking_kamar_id_seq. Tidak DELETE/DDL/grants tabel lain. SET LOCAL ROLE per transaksi membuktikan effective role dan CREATE pada schema public ditolak via privilege check. Insert/replay/cancel PASS.

Role migrasi tetap terpisah dari runtime. Produksi masih memakai role superuser existing, belum diganti. Rencana rollout: role LOGIN runtime dengan secret baru dikelola privat, grants tabel/sequence minimum; proses migrasi memakai role owner terpisah. Jangan mengeksekusi startup create_all sebagai mekanisme migrasi runtime; pastikan seluruh tabel sudah tersedia terlebih dahulu. Full startup memakai LOGIN runtime dan konfigurasi credential baru belum diuji; SET ROLE membuktikan izin SQL, bukan authentication deployment.

## 9. Test matrix
| Pemeriksaan | Status | Bukti |
|---|---|---|
| Node frontend | PASS | 8 tests |
| Python unit/integration isolated | PASS | 12 tests; 22.767s; SQLite/RDFLib |
| PostgreSQL idempotency/concurrency/recovery | PASS | Skenario bagian 6; runner final exit 0 |
| Migrasi 002 | PASS test-only | Up/down/up awal; rerun tidak menjatuhkan ledger |
| Migrasi 001 | PASS evidence/check | Bukti 1D up/down/up; dua CHECK masih ada |
| Live browser final | PASS functionality | 11 counted checkpoints + 3 back/filter assertions |
| Browser console/network bersih | FAIL cleanliness | Deep Chat request deprecated; tile ERR_ABORTED; pencarian dibatalkan saat race |
| Backup PostgreSQL restore | PASS | 4 tabel, count booking 1 pada database restore privat |
| Backup Fuseki restore | PASS | 206 RS dalam network-isolated restore container |
| Synthetic least-privilege | PASS | Flags false, limited-role booking success |
| Production least-privilege LOGIN rollout | NOT TESTED | Tidak mengganti role/kredensial |
| Live health/search | PASS | HTTP 200, dependencies ok, count 206 |
| Direct SPARQL | PASS | HTTP 200, COUNT DISTINCT 206 |
| Live RDF detail | PASS | HTTP 200, Turtle 45 triple |
| Local RDF parse | PASS | Dataset 5564; ontologi 73; OWL revisi 381 |
| Public operator gate | PASS | Live GET kode dummy 403 |
| Compose validation / diff check | PASS | config --quiet; diff --check |
| Production migrations/restart/new idempotency HTTP | NOT TESTED | Menunggu persetujuan eksplisit |

Riwayat kegagalan browser tidak disembunyikan: sebelum fix modal, header menutup back; expanded test kemudian gagal karena closed chat intercept. Setelah perbaikan closed chat, seluruh assertion final PASS. ERR_ABORTED pencarian pada race sesuai abort request lama; tile aborts bukan bukti seluruh akses peta sehat. Tidak ada uncaught pageerror pada suite final; bukan berarti tidak ada console error.

## 10. Risiko tersisa
- Backend aktif belum memuat patch 1E; produksi belum memiliki ledger. Jangan menjanjikan idempotency production sebelum migrasi dan restart yang disetujui.
- Tidak ada akun, rate limit, idempotency client frontend, retention ledger, audit operator atau login runtime produksi.
- Keyless requests tetap bisa duplicate; jangan mengklaim backward compatibility berarti semua request idempotent.
- Dependency CDN/Deep Chat deprecation, peta/routing/GPS dan semua variasi motion belum seluruhnya diuji.
- Schema parity 1D masih menyisakan perbedaan text/nullability; 002 tidak mengubah pasien existing.
- Qualitas koordinat/inferensi layanan/BPJS dan proxy SPARQL tetap risiko sebelumnya; tidak memperluas scope ke dataset/desain baru.

## 11. Perubahan memerlukan persetujuan
1. Terapkan 001 jika objek belum ada dan 002 ke produksi setelah backup terbaru/preflight; jangan rerun 001/002 membabi buta.
2. Restart hanya API untuk memuat patch setelah schema siap; rencanakan jeda singkat. Tidak menjalankan ini dalam 1E.
3. Ganti role/kredensial runtime produksi hanya setelah secret dan rencana rollback disetujui.
4. Cleanup database restore berisi backup pasien dan volume/container restore; belum ada penghapusan.

Rollback 002 memerlukan penghentian request keyed/deployment kode lama terlebih dahulu; kehilangan ledger berarti replay lama tidak lagi terlindungi. Booking asli tidak dihapus. Jangan deploy backend keyed lalu drop ledger ketika request masih aktif.

## 12. Handoff koordinasi
ChatGPT: bedakan implementation/test PASS dengan production rollout pending; status keseluruhan PARTIAL secara konservatif. Antigravity: pertahankan modal #detail sebagai anak body dan display:none chat tertutup; jangan kembalikan klaim semua RS terverifikasi. OpenCode: fokus reproducibility supplemental PostgreSQL tests, deployment checklist dan observability; jangan menulis ke carisehat atau memakai database restore sebagai fixture. Jangan menimpa perubahan anggota; Git diff keseluruhan mencakup pekerjaan terdahulu.
