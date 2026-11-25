# Stabilisasi CariSehat - Tahap 1

> Pembaruan terbaru: lihat bagian J (Tahap 1B). Bagian A?I adalah catatan historis Tahap 1; blocker Python/browser di sana telah ditindaklanjuti.

## A. Ringkasan eksekusi
Status: **PARTIAL**. Perubahan kecil diterapkan tanpa mengubah dataset, ontologi, skema SQL, volume, atau .env. Tidak ada commit/push. Git awal: main, frontend/index.html sudah dimodifikasi anggota (627 insertions/214 deletions), RDF revisi root untracked. Perubahan tersebut dipertahankan. Branch baru gagal dibuat karena cannot lock ref / cannot create directory. Git tersedia lewat C:/Program Files/Git/cmd/git.exe, bukan PATH.

## B. Bug yang diperbaiki
CODE berarti patch telah ditinjau, belum teruji runtime Python/browser. Delapan tes Node lulus; tidak berarti delapan fitur E2E lulus.

| ID | Masalah/penyebab | Perbaikan | File | Bukti | Status |
|---|---|---|---|---|---|
| F1 | Hero memanggil fungsi filter tidak ada | Panggil search sekali; batalkan debounce; keyword kosong juga disalin | frontend/index.html | 3 kasus Node VM | PASS unit |
| F2 | Wrapper menu hidden dan order pada anak salah | display:contents, order map-wrap, reset aria menu | frontend/index.html | Pemeriksaan source otomatis | CODE; browser pending |
| F3 | Data dalam inline JavaScript | Dataset attributes dan delegated listeners untuk graph/city/booking/cancel | frontend/index.html | Tes apostrof hero + larangan handler dinamis | CODE; DOM browser pending |
| F4 | Respons lama dapat menimpa hasil baru | Periksa identitas request sesudah JSON | frontend/index.html | Assertion guard | CODE; race browser pending |
| F5 | Filter gagal diam-diam | Toast yang dapat ditindaklanjuti | frontend/index.html | Review | CODE |
| F6 | Klaim terverifikasi/booking nyata | Label dataset inferensi dan simulasi; hapus klaim verifikasi | frontend/index.html, rs_detail.html | Review | CODE |
| F7 | Badge Gemini palsu/probe berbiaya | Hapus request __ping__ dan aktivasi badge otomatis | frontend/index.html | Review | CODE |
| B1 | Input booking tidak dibatasi | Panjang, whitespace, tanggal keluar | booking.py | 3 unit tests disiapkan | CODE |
| B2 | Collision/error transaksi | secrets, retry constraint kode, rollback dan 409/503 | booking.py, main.py | Mock failure test disiapkan | CODE |
| B3 | Data pasien dan pembatalan terbuka | Header operator, default deny | booking.py, config.py, Compose | Unit test akses disiapkan | CODE |
| B4 | Input chat Any | Model pesan strict dengan batas panjang | chat.py | Unit test disiapkan | CODE |
| B5 | Gemini menjawab saat Fuseki gagal/kosong | Return failure/empty sebelum Gemini pada alur pencarian | chatbot_service.py | Review | CODE |
| B6 | GEMINI_MODEL diabaikan | Model dari Settings | config.py, chatbot_service.py | Review | CODE |
| B7 | Label layanan/kota tidak cocok | Alias label sesuai RDF; q dibuang jika filter spesifik | chatbot_service.py | Review | CODE |
| D1 | Resource DBpedia diinterpolasi bebas | Validasi identifier; beberapa alias kota; binding kosong unavailable | dbpedia_service.py | Review | CODE |
| D2 | Port database/update di semua interface | Bind PostgreSQL/Fuseki/backend ke loopback | Compose | Diff review | CODE |
| B8 | Health gagal tetap 200 | 503 saat dependency gagal | api.py | Review | CODE |
| S1 | .env.example hilang | Template tanpa rahasia ditambahkan | .env.example | Review | CODE |

18 kelompok masalah mendapat patch; hanya F1 dibuktikan secara perilaku fungsi, sisanya memiliki bukti statis atau masih memerlukan runtime. Jangan menyebut 18 bug sudah lolos E2E.

## C. File yang berubah
- frontend/index.html: F1?F7 dan pesan akses booking.
- backend/app/templates/rs_detail.html: provenance yang terlihat pada halaman langsung.
- backend/app/config.py: model Gemini dan kunci operator.
- backend/app/main.py: respons aman kegagalan SQLAlchemy.
- backend/app/routers/api.py: health readiness HTTP.
- backend/app/routers/booking.py: validasi, rollback, collision, kontrol akses.
- backend/app/routers/chat.py: input bertipe jelas.
- backend/app/services/chatbot_service.py: konsistensi label/model dan kegagalan sumber.
- backend/app/services/dbpedia_service.py: identifier/mapping/binding.
- docker-compose.yml: binding loopback dan variabel operator.
- .env.example: template clean setup.
- tests/frontend.test.cjs: delapan pemeriksaan Node tanpa dependensi tambahan.
- tests/test_backend.py: tujuh unit tests Python, mock database; belum dijalankan.
- STABILIZATION_PHASE1_REPORT.md: laporan ini.

## D. Hasil pengujian
| Pengujian | Command | Hasil | Bukti/keterangan |
|---|---|---|---|
| Frontend | node --test tests/frontend.test.cjs | PASS | 8 pass, 0 fail |
| Diff whitespace | git diff --check (Git absolute path) | PASS | Exit 0 |
| Review backend/Compose | git diff -- backend/app docker-compose.yml | PASS inspeksi | Tidak ada data/kredensial di patch |
| Backend unit | python -m unittest discover -s tests -p 'test_*.py' | SKIPPED | Python tidak tersedia pada PATH; 7 kasus belum dieksekusi |
| Python syntax/import | Python AST/import validation | SKIPPED | Interpreter belum tersedia |
| Compose validation | docker compose config --quiet | SKIPPED | Docker belum tersedia pada PATH |
| RDF parser | RDFLib/Jena | SKIPPED | Runtime tidak tersedia; RDF tidak diubah |
| Integration isolated | FastAPI/PostgreSQL/Fuseki | SKIPPED | Tidak ada service test yang disiapkan |
| Browser E2E | 375/768/1440, GPS/rute mock | SKIPPED | Browser runner belum tersedia |
| External live | DBpedia/Gemini/tiles/routing | SKIPPED | Tidak dipaksakan |

Ringkasan runner: 8 PASS, 0 FAIL. Ada 7 kategori pemeriksaan dilewati (termasuk 7 kasus Python dalam satu kategori), bukan angka skip dari runner Node.

## E. Status layanan
Frontend: syntax/unit terbatas PASS; render UNKNOWN. FastAPI, PostgreSQL, Fuseki, SPARQL: belum diuji live pada tahap ini. DBpedia, chatbot, peta, booking: CODE VERIFIED saja. Audit sebelumnya melaporkan ECONNREFUSED di localhost; itu bukan hasil probe ulang tahap ini.

## F. Masalah tersisa
- P1: clean setup, imports, backend tests, RDF parsing dan browser wajib diverifikasi di mesin ber-runtime.
- P1: mode darurat masih memakai hasil filter dan koordinat perkiraan. Peringatan bukan pengganti koreksi algoritme/provenance.
- P1: form publik cek/batal kini sengaja ditolak 403. Operator mengatur BOOKING_ACCESS_KEY di environment server dan mengirim X-Booking-Key lewat klien API tepercaya; jangan memasukkan key dalam HTML/localStorage. Belum ada identitas per pengguna atau audit operator. POST simulasi masih publik dan belum rate-limited.
- P1: booking belum memvalidasi identitas RS terhadap Fuseki; perlu test transaksi isolated.
- P1: semua handler SQLAlchemy runtime 503, tetapi startup create_all tetap bergantung DB tersedia. Tidak ada retry/migration startup baru.
- P1: SQL/ORM berbeda; loader graph parsial; query proxy bebas; URL website belum allowlist; DBpedia fallback belum canonical untuk semua wilayah.
- P1: sebagian sapaan/FAQ Gemini masih dapat melewati retrieval; grounding menyeluruh belum selesai.
- P2: race DBpedia/booking panel, mock peta/rute, aksesibilitas mobile dan pengetesan DOM masih diperlukan.
- P2: dependency lockfile, statistik hardcoded, graf sintetis dan generator ganda belum diperbaiki.

## G. Risiko regresi
Strict chat dapat menolak payload widget nonteks: perlu E2E Deep Chat. Format kode booking kini 20 karakter, tetap sesuai VARCHAR(20); kode lama tetap dapat dicari operator. Operator gate mengubah kontrak read/delete menjadi 403 tanpa key. Binding loopback menghentikan akses LAN yang sebelumnya terbuka. display:contents memerlukan verifikasi posisi menu pada browser. Tidak ada migrasi dijalankan.

Rencana migrasi aman: introspeksi pg_catalog pada salinan database, bandingkan CHECK/UNIQUE/index SQL dengan metadata ORM, identifikasi data pelanggar, backup, susun migrasi versioned non-destruktif, validasi constraint bertahap dan uji rollback. Jangan reset volume atau berharap create_all mengubah tabel existing.

## H. Rekomendasi Tahap 2
Selesaikan verifikasi/stabilisasi tersisa dahulu. Setelah itu cocokkan lima komponen MSBD dengan rubrik; satukan pipeline RDF dan ontologi canonical; gunakan ID stabil, provenance yang dapat ditelusuri, validasi koordinat, serta mapping linked data bersama. Pertahankan pencarian SPARQL dan booking ORM. Favorit, akun, pembayaran dan redesign tidak termasuk patch ini.

## I. Ringkasan untuk ChatGPT

CariSehat merupakan aplikasi direktori rumah sakit Sumatera Utara untuk tugas gabungan MSBD dan Web Semantik. Tahap stabilisasi pertama ini telah menghasilkan perubahan source code yang nyata, tetapi status keseluruhan masih PARTIAL. Alasannya bukan hanya layanan eksternal belum dicoba: interpreter Python, Docker, dan browser automation belum tersedia pada lingkungan kerja yang diperiksa. Delapan pemeriksaan frontend menggunakan Node berhasil dijalankan. Unit test Python telah ditulis tetapi belum dieksekusi, sehingga reviewer berikutnya tidak boleh menganggap backend sudah terbukti bebas error import atau runtime. Tidak ada dataset asli, ontologi, skema SQL, volume database, ataupun file .env yang diubah.

Sebelum perubahan, Git diperiksa melalui executable di Program Files karena perintah git tidak tersedia pada PATH. Working tree awal sudah mempunyai perubahan besar pada frontend/index.html dari anggota kelompok dan sebuah file RDF revisi yang belum tracked. Pekerjaan ini mempertahankan perubahan tersebut dan menambahkan patch berdasarkan anchor source yang aktual. Upaya membuat branch fix/stabilization-phase-1 gagal karena referensi Git tidak dapat ditulis. Tidak ada reset, commit, push, atau penghapusan file. Diff frontend terhadap HEAD mencakup pekerjaan anggota sebelumnya, sehingga statistik diff tidak boleh seluruhnya dianggap kontribusi stabilisasi.

Perbaikan perilaku yang paling jelas adalah pencarian hero. Fungsi goToExplorer sebelumnya memanggil filter yang tidak tersedia. Sekarang keyword hero disalin ke input explorer, debounce tertunda dibatalkan, lalu search dipanggil sekali. Keyword kosong juga diproses sehingga tidak mempertahankan teks lama secara tersembunyi. Pengujian Node menjalankan fungsi dengan stub DOM untuk teks biasa, teks kosong, serta nama RS O'Connor, dan memastikan satu pemanggilan pencarian. Tombol dan Enter menggunakan submit form yang sama. Ini merupakan bukti unit terisolasi, bukan pengujian visual browser.

Frontend juga memperoleh perbaikan CSS mobile. Wrapper navigasi tidak lagi disembunyikan, dan order peta diterapkan pada map-wrap yang benar-benar merupakan anak grid. Navigasi mengatur ulang aria-expanded saat ditutup atau ketika Escape digunakan. Handler dinamis untuk graf, informasi kota, submit booking, dan pembatalan tidak lagi menyisipkan data ke inline JavaScript. Nilai disimpan dalam data attributes yang tetap melalui escaping HTML, kemudian dibaca oleh event listener. Pengujian statis memastikan pola inline berisiko hilang. Namun render menu pada lebar 375, 768, dan 1440 piksel serta alur booking DOM masih harus diperiksa dengan browser.

Pada pencarian asynchronous, identitas request diperiksa lagi sesudah parsing JSON sehingga respons lama tidak menimpa hasil request terbaru. Kegagalan filter yang sebelumnya hanya dicatat ke console sekarang menampilkan toast. Permintaan chat __ping__ yang dapat memicu pencarian atau biaya AI dihapus bersama aktivasi badge Gemini yang tidak membuktikan provider aktif. Klaim rumah sakit terverifikasi diganti menjadi dataset, dan peringatan tentang inferensi layanan, fasilitas, BPJS, serta koordinat perkiraan muncul pada explorer dan halaman detail semantik. Pesan booking tidak lagi menjanjikan konfirmasi dari RS nyata. Semua perubahan tersebut mempertahankan struktur UI lama.

Booking backend memperoleh batas panjang field sesuai kolom utama, pemangkasan whitespace, pembatasan catatan, dan validasi tanggal keluar tidak lebih awal daripada masuk. Kode booking memakai secrets dengan delapan karakter acak, tetap muat dalam kolom dua puluh karakter. Insert menangani IntegrityError: collision constraint kode diulang, pelanggaran lain menghasilkan 409, dan kegagalan SQLAlchemy menghasilkan rollback serta 503. Handler global juga mengubah error SQLAlchemy request menjadi respons aman tanpa detail internal. Tujuh unit tests Python mencakup request valid, tanggal, panjang field, input chat, query escaping, mock kegagalan database, dan penolakan akses booking. Seluruh test Python masih menunggu interpreter.

Perlindungan data pasien menggunakan pembatasan operator sederhana, tanpa sistem akun baru. Endpoint baca, daftar per RS, dan pembatalan memerlukan X-Booking-Key yang cocok dengan BOOKING_ACCESS_KEY pada server. Bila variabel kosong, akses ditolak secara default. Frontend tidak menerima atau menyimpan kunci tersebut. Akibatnya form status dan pembatalan publik kini mendapat 403; UI menjelaskan bahwa akses hanya untuk operator simulasi. Ini adalah perubahan kontrak yang disengaja untuk menutup pembacaan data pasien anonim, tetapi belum menyediakan otorisasi per pemilik booking, audit operator, ataupun pembatasan frekuensi. Pembuatan booking simulasi tetap publik. Identitas RS juga belum diverifikasi terhadap Fuseki.

Input chatbot kini memakai model pesan bertipe string ketat dengan batas panjang dan jumlah pesan. Alur pencarian tidak memanggil Gemini ketika Fuseki gagal atau hasil kosong. Konfigurasi GEMINI_MODEL sekarang benar-benar digunakan service. Label layanan lama dipetakan ke istilah dataset pengayaan dan beberapa nama wilayah diselaraskan. Query nama dibuang bila filter spesifik sudah dikenali untuk menghindari konflik ekstraksi. Masih ada keterbatasan: sapaan dan FAQ tertentu dapat menuju Gemini tanpa retrieval, sehingga grounding menyeluruh belum dapat dianggap selesai. Deep Chat perlu diuji terhadap model payload baru untuk menghindari regresi format pesan.

Service DBpedia menambahkan alias beberapa wilayah, memvalidasi resource identifier sebelum interpolasi, dan tidak lagi menyatakan binding kosong sebagai data tersedia. Konektivitas DBpedia tidak diuji live. Compose membatasi port PostgreSQL, Fuseki, dan backend ke loopback untuk development; komunikasi internal antarkontainer tetap memakai service names. Hal ini membatasi akses LAN, tetapi tidak menggantikan autentikasi Fuseki bagi proses lokal atau keamanan proxy query publik. Health endpoint kini menggunakan 503 bila dependency gagal. Template .env.example ditambahkan untuk memperbaiki instruksi clean setup, tanpa menyentuh kredensial existing.

Pekerjaan lanjutan harus dimulai dari verifikasi Python, Docker Compose, dataset parsing, backend isolated tests, dan browser E2E. Mode darurat masih memakai hasil filter aktif dan koordinat perkiraan; peringatan saja tidak menyelesaikan correctness tersebut. Skema ORM dan SQL masih perlu migrasi aman, loader perlu menangani graph parsial, dan mapping DBpedia serta label chatbot perlu pengujian lebih luas. Setelah stabilisasi benar-benar lulus, Tahap 2 dapat berfokus pada rubrik komponen MSBD, penyatuan generator RDF, ontologi canonical, provenance, serta ID rumah sakit stabil. Arsitektur pencarian tetap Fuseki/SPARQL dan transaksi tetap SQLAlchemy/PostgreSQL; tidak ada penggantian sumber semantik secara diam-diam.


## J. Tahap 1B ? verifikasi runtime dan regresi (17 November 2026)

### Keputusan
**PARTIAL**, dengan bukti runtime baru. Backend, query RDF dan browser berhasil pada fixture terisolasi; PostgreSQL/Fuseki dan Docker Compose live belum terbukti. Tidak ada perubahan dataset, ontologi atau skema. Dua bug aplikasi tambahan diperbaiki: identitas RS booking yang dipercaya dari client dan overflow mobile dari panel detail tersembunyi.

### Environment yang benar-benar diperiksa
- Python 3.12.13 ditemukan di `C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, bukan PATH. Pencarian juga meliputi Program Files, C:/Python*, Local/Programs/Python, Local/Python, WindowsApps dan registry uninstall.
- Dengan izin eksplisit pengguna, dibuat `.venv` dan diinstal `backend/requirements.txt`. Unduhan pertama gagal WinError 10013; percobaan dengan akses jaringan yang diizinkan berhasil. PATH sistem dan .env tidak diubah.
- Dependency terpasang antara lain FastAPI 0.163.1, SQLAlchemy 2.1.9, RDFLib 7.6.0, Pydantic 2.14.3, Uvicorn 0.54.0. `pip check` lulus. Requirements asli tidak diubah; versi dipilih resolver dari batas bawah yang sudah ada. Ada warning deprecation Starlette/httpx pada test client, bukan error.
- Node v24.13.1 dan npm 11.8.0 di C:/Program Files/nodejs; Git 2.53.0.windows.1 di C:/Program Files/Git/cmd/git.exe. Working tree tetap memuat perubahan anggota dan patch tahap sebelumnya, tanpa commit/push.
- Chromium cache ada di Local/ms-playwright. Playwright ditemukan melalui file .links, di `C:/Users/User/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright`. Akses cache memerlukan eksekusi di luar sandbox; browser berhasil berjalan headless. Chrome dan Edge juga ditemukan, tetapi tes menggunakan Chromium Playwright.
- Docker executable/service/process tidak ditemukan di lokasi umum C:/Program Files/Docker, Local/Programs, Local/DockerDesktop, D:/Program Files maupun daftar service/process. Ada folder sisa Local/Docker berisi log, tetapi itu bukan bukti Engine aktif. Jangan menyimpulkan tidak ada instalasi di seluruh disk. Probe TCP 8000/3030/5433 dari lingkungan ini timeout; bukan bukti layanan mati secara global.

### Lingkup fixture dan reproduksi
`tests/runtime_fixture.py` menjalankan FastAPI asli, tetapi mengganti akses SELECT/CONSTRUCT service semantik dengan eksekusi query RDFLib atas TTL asli dan mengganti dependency session booking dengan SQLite memory. Gemini dinonaktifkan dan operator key hanya nilai dummy fixture. Tidak ada data pasien nyata. Seluruh booking hilang saat proses uji dihentikan. CONSTRUCT fixture lebih sederhana daripada service Fuseki; hasil ini tidak mengesahkan transport HTTP atau implementasi CONSTRUCT production.

Perintah yang dijalankan:
```powershell
node --test tests/frontend.test.cjs
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_*.py'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -B tests/runtime_fixture.py
$env:PLAYWRIGHT_MODULE='C:\Users\User\AppData\Local\npm-cache\_npx\e41f203b7505f1fb\node_modules\playwright'
node tests/browser-runtime.cjs
```
Jalankan server fixture pada terminal terpisah untuk browser. Variabel PLAYWRIGHT_MODULE hanya berlaku pada proses shell tersebut; tidak mengubah PATH. Sesuaikan lokasi package jika berbeda. Jangan memakai fixture sebagai konfigurasi produksi.

### Hasil akhir dan riwayat kegagalan
| Pemeriksaan | Hasil akhir | Bukti dan batas |
|---|---|---|
| Node frontend | 8 PASS | Hero normal/kosong/apostrof, syntax, wiring dan guard |
| Python unit lama | 7 PASS | Booking validation, chat invalid, query, rollback mock, operator denial |
| Integrasi FastAPI isolated | 5 PASS | Health 206, pencarian/filter/HTML/RDF, chat widget-shaped, booking/operator, Fuseki failure mock |
| Chromium browser | 13 PASS | Homepage; hero; detail panel; booking sintetis; UX 403; halaman semantik; filter C=120; delayed search race; 375/768/1440; widget Deep Chat nyata; tanpa pageerror |
| AST Python | PASS | Backend, scripts dan tests diparse tanpa bytecode |
| RDFLib parse | 3 PASS | Dataset 5564 triple; ontologi 73; RDF revisi root 381 |
| Dependency consistency | PASS | pip check: No broken requirements found |
| YAML Compose | PASS terbatas | YAML parse dan tiga service ditemukan, bukan docker compose config |
| Git diff --check | PASS | Tidak ada whitespace error |
| Docker Compose/Engine | SKIPPED | Executable/engine belum ditemukan |
| PostgreSQL live | SKIPPED | Tidak ada runtime terverifikasi |
| Fuseki HTTP/TDB2 live | SKIPPED | Digantikan RDFLib hanya pada fixture |
| DBpedia/Gemini live | SKIPPED | Tidak diuji; Gemini dimatikan |
| GPS/rute end-to-end | SKIPPED | Peta dimuat, tetapi navigasi/GPS tidak disimulasikan |

Jumlah utama: **33 assertion/case PASS, 0 FAIL final**, terdiri dari 8 Node + 12 Python + 13 checkpoint browser. Tambahan 7 pemeriksaan statis PASS (AST, tiga RDF, pip, YAML, diff) dicatat terpisah. **5 kategori SKIPPED** di tabel. Jumlah ini bukan 33 fitur production yang sudah lulus.

Riwayat: percobaan Python sebelum instalasi gagal import FastAPI; setelah instalasi 1 dari 12 tes gagal karena konfigurasi singleton sudah terimport sebelum fixture mengatur operator key. Fixture diperbaiki untuk menetapkan Settings secara eksplisit. Browser awal gagal mengklik reset saat panel detail terbuka; skenario diperbaiki dengan tombol kembali, tanpa memaksa click. Browser berikutnya menemukan overflow mobile asli. Setelah patch, 13 checkpoint lulus. Pengujian Node sempat gagal dua assertion karena CRLF hasil penulisan Windows; reader tes kini menormalisasi CRLF, file patch mengikuti LF. Semua riwayat ini tidak disembunyikan oleh angka final.

### Bug terverifikasi dan perubahan tambahan
1. **Identitas booking**: sebelum perbaikan, POST dengan kode RS valid dan nama sintetis diterima apa adanya. Dependency async `verified_booking` pada booking.py kini mengambil RS dari SPARQL; ID hilang menghasilkan 404 dan nama client diganti nama canonical RDF. Unit integrasi membuktikan nama palsu tidak disimpan dan ID tidak ada ditolak. Fuseki gagal tetap menghasilkan 502 melalui handler HTTPX, tanpa insert. Ini tidak memverifikasi kapasitas kamar; booking tetap simulasi.
2. **Overflow mobile**: setelah membuka/menutup detail lalu mencari hasil kosong, panel off-screen memperbesar scrollWidth di 375px. Ukuran DOM menunjukkan section detail di luar viewport. `aside` kini memiliki overflow:hidden dan min-width:0, menjaga panel bergeser tetap di dalam sidebar. Skenario race/empty dilanjutkan pengukuran mobile/tablet/desktop lulus.
3. **Test isolation**: DATABASE_URL tes unit ditetapkan eksplisit ke SQLite, bukan setdefault yang dapat mewarisi koneksi luar. Fixture mengatur API key AI kosong dan operator dummy sebelum layanan. Tidak ada rahasia disalin ke laporan.

File baru Tahap 1B: tests/runtime_fixture.py, tests/test_runtime.py, tests/browser-runtime.cjs. File diubah: tests/test_backend.py (isolasi), tests/frontend.test.cjs (CRLF), backend/app/routers/booking.py (canonical RS), frontend/index.html (overflow), dan laporan ini. Tidak ada dependency aplikasi atau ontologi yang diubah.

### Schema ORM dan risiko tersisa
Introspeksi metadata SQLAlchemy benar-benar dijalankan: keempat model memiliki nol CHECK; kabupaten_kota tidak memiliki UNIQUE gabungan, dan hanya index ix_booking_kamar_kode_rs ditemukan untuk booking. SQL file memiliki CHECK, UNIQUE gabungan serta index status tambahan. Ketidaksetaraan sudah terbukti pada metadata/source, bukan introspeksi PostgreSQL live. Tidak dilakukan migrasi; rencana aman bagian G tetap berlaku.

Deep Chat nyata mengirim payload yang diterima API 200. Tes hanya membuktikan request widget dan ketiadaan pageerror, belum menilai seluruh formatting jawaban atau semua console/network warning. Browser menggunakan CDN aktual; tidak ada klaim layanan DBpedia atau rute ikut teruji. Public booking read/cancel 403 tampil dengan pesan operator; akses operator diuji lewat API terisolasi, bukan memasukkan key di browser. Belum ada rate limit, akun individual, pagination booking, atau audit akses. Mode darurat, loader graph parsial, DBpedia canonical lengkap dan proxy query masih menjadi risiko dari laporan awal.

### Tindakan pengguna untuk verifikasi live
Tidak ada Docker yang diinstal otomatis. Jika Docker Desktop terpasang di lokasi lain, sediakan lokasi executable atau buka Docker Desktop hingga Engine siap. Jika belum terpasang, instal Docker Desktop sesuai konfigurasi Windows/virtualisasi perangkat, lalu jalankan:
```powershell
docker version
docker compose version
docker compose config --quiet
docker compose up -d --build
docker compose ps
```
Perintah up memakai konfigurasi proyek existing dan dapat menjalankan loader startup sebagaimana desain aplikasi. Jangan gunakan down -v/reset. Setelah Engine siap, ulangi health, query Fuseki, PostgreSQL dan booking pada database uji terpisah sebelum menyatakan Tahap 1 COMPLETED.

## K. Tahap 1C - Live integration verification (17 November 2026)

### Keputusan dan batas pelaksanaan
Status Tahap 1 tetap **PARTIAL**. Transport HTTP FastAPI/PostgreSQL/Fuseki kini terbukti live. Transaksi booking PostgreSQL dan browser live belum terbukti. Tidak ada insert/update/delete booking, migrasi, restart/recreate container, perubahan environment, dataset, ontologi, volume, commit atau push. Perubahan Tahap 1C hanya laporan ini. Satu booking existing ditemukan melalui COUNT saja; data pasien tidak ditampilkan.

### Kode aktif dan environment
- Git awal masih memuat perubahan anggota/tahap sebelumnya pada backend, frontend, Compose, tests dan laporan. Tidak ditimpa.
- Docker Engine 29.7.2; `docker compose config --quiet` berhasil exit 0. API running tanpa --reload, restart count 0; database healthy. Startup baru tidak dipicu karena startup menjalankan create_all dan loader RDF.
- Container API mulai 2026-11-17 04:29:42 UTC (11:29:42 WIB). Mount /code/app berasal dari backend/app workspace; /frontend dan /semantic read-only.
- SHA-256 21 file Python/HTML/TTL container dibandingkan dengan workspace: seluruhnya sama setelah koreksi pemetaan path pada skrip audit. Percobaan awal salah mengganti substring /semantic pada routers/semantic.py sehingga melaporkan mismatch palsu; bukan perubahan aplikasi.
- Kesamaan file disk bukan pemeriksaan bytecode proses Uvicorn. Bukti perilaku HTTP tambahan mengonfirmasi health, booking default-deny, validasi payload chat dan pencarian. Dependency canonical booking diuji langsung dalam proses Python terpisah di container, bukan POST booking valid.
- Konfigurasi diperiksa sebagai boolean saja: booking operator key belum dikonfigurasi; Gemini tidak aktif; auto-load RDF aktif. Tidak ada nilai rahasia ditampilkan. Chat live menggunakan fallback tanpa pemanggilan Gemini berbayar.

### Hasil HTTP live
Semua respons berikut benar-benar diterima melalui localhost menuju container aktif. Hitungan filter dibandingkan dengan CSV; kelas D mencakup D PRATAMA.

| Pengujian | HTTP | Isi/bukti | Status |
|---|---:|---|---|
| /api/health | 200 | postgres=ok, fuseki=ok, jumlah_rs=206 | PASS |
| /api/search?limit=500 | 200 | 206 item, 206 ID unik | PASS |
| Pencarian Adam Malik | 200 | 1 RS | PASS |
| Kelas A/B/C/D | 200 masing-masing | 3/29/120/54 RS | PASS |
| Jenis Umum/Khusus | 200 masing-masing | 183/23 RS | PASS |
| Wilayah Kota Medan/Kab. Karo | 200 masing-masing | 66/5 RS | PASS |
| Gabungan C + Umum + Kota Medan | 200 | 30 RS | PASS |
| Literal menyerupai SPARQL injection dan O'Connor | 200 masing-masing | 0 hasil; tidak memperluas hasil | PASS terbatas |
| Limit 501 / offset -1 | 422 masing-masing | Ditolak validasi | PASS |
| /api/filters | 200 | 33 wilayah, 25 layanan | PASS |
| /rs/rs-001 | 200 | Og Hospital; RDFa; 7 properti Open Graph | PASS |
| /rs/rs-NOTEXIST | 404 | RS tidak ditemukan | PASS |
| /rs/rs-001.ttl | 200 | text/turtle; RDFLib parse 45 triple | PASS |
| /rs/rs-001.rdf | 200 | application/rdf+xml; 45 triple | PASS |
| /data/hospitals.rdf | 200 | RDF/XML; 5637 triple | PASS |
| GET Fuseki /hospital/query | 200 | COUNT DISTINCT RumahSakit=206 | PASS |
| GET /sparql/query dengan SELECT yang sama | 200 | COUNT=206 | PASS |
| /sparql/query tanpa query | 400 | Parameter kosong ditolak | PASS |
| GET booking kode dummy tanpa key | 403 | Pesan operator; tidak ada data pasien | PASS |
| GET daftar booking rs-001 tanpa key | 403 | Ditolak | PASS |
| GET booking kode dummy dengan key salah | 403 | Ditolak | PASS |
| POST /api/booking dengan {} | 422 | 6 validation errors; tidak ada payload valid/insert | PASS |
| POST /api/chat teks kosong | 200 | Sapaan deterministik | PASS |
| POST /api/chat payload messages: RS kelas A di Medan | 200 | Jawaban fallback berisi RS kelas A di Medan | PASS |
| POST /api/chat text berupa object | 422 | 1 validation error | PASS |

Total **32 kasus HTTP unik PASS**, bukan 32 fitur E2E. Runner awal berhenti karena encoding terminal cp1252 saat mencetak emoji jawaban chat, bukan kegagalan endpoint. Tiga pemeriksaan terakhir kemudian dijalankan/dicatat ulang dengan JSON ASCII-safe. Tidak ada klaim runner awal selesai normal.

### Audit PostgreSQL read-only dan SQL/ORM
Introspeksi melalui engine aplikasi menggunakan `SET TRANSACTION READ ONLY`, `SHOW transaction_read_only` menghasilkan on, statement_timeout 5 detik, lalu rollback. Pemeriksaan meliputi pg_database, pg_roles, columns, PK, UNIQUE, CHECK, FK dan indexes. Tidak membaca isi identitas pasien.

Database non-template yang tersedia hanya postgres dan carisehat. Tidak ada database pengujian terpisah yang terbukti. Database postgres bukan otomatis database test. Tidak ada transaksi sintetis ditulis.

| Bagian | PostgreSQL live | Perbandingan |
|---|---|---|
| provinsi | PK dan UNIQUE nama | Sesuai SQL/ORM pokok |
| kabupaten_kota | CHECK jenis, UNIQUE(id_provinsi,nama), FK provinsi | Sesuai SQL; CHECK dan UNIQUE gabungan tidak ada pada ORM |
| rumah_sakit | 4 CHECK: jenis, kelas, latitude, longitude; FK kabkota; UNIQUE kode_rs | Sesuai SQL; ORM tidak memiliki CHECK |
| rumah_sakit kelas/alamat | CHAR(1), TEXT | ORM VARCHAR(1), VARCHAR tanpa panjang |
| rumah_sakit status | Server DEFAULT aktif | ORM hanya client default |
| booking_kamar | PK, UNIQUE kode_booking, index ix_booking_kamar_kode_rs | Cocok metadata ORM; nama index berbeda dari SQL |
| booking CHECK jenis/status | Tidak ada | SQL mendefinisikan dua CHECK; ORM tidak |
| booking index status | Tidak ada | SQL mendefinisikan idx_booking_status |
| booking status | NOT NULL, tanpa server default | SQL DEFAULT menunggu; ORM client default menunggu |
| booking catatan | VARCHAR tanpa panjang | SQL TEXT |
| booking created_at | NOT NULL, default now() | SQL membolehkan NULL; ORM NOT NULL |
| booking FK kode_rs | Tidak ada | Tidak ada juga pada SQL/ORM; validasi aplikasi memakai Fuseki |

Agregat booking: total=1, tanggal_keluar sebelum masuk=0, identitas kosong=0. Ini snapshot sebelum pemeriksaan HTTP; tidak ada penghitungan akhir yang diklaim. Role koneksi aplikasi memiliki rolsuper, rolcreatedb, rolcreaterole=true: privilege terlalu luas untuk akun aplikasi.

Alur transaksi ditinjau: add -> commit -> refresh; IntegrityError rollback dan retry khusus nama constraint kode_booking hingga lima kali, selain itu 409; SQLAlchemyError rollback dan 503. UNIQUE live bernama booking_kamar_kode_booking_key cocok dengan deteksi retry. Collision, commit, rollback, cancellation dan konkurensi belum diuji pada PostgreSQL. Risiko commit berhasil tetapi refresh gagal dapat menghasilkan 503 setelah insert sudah tersimpan; belum ada idempotency. Validasi kapasitas kamar tidak ada karena simulasi.

Dependency verified_booking diuji langsung terhadap Fuseki live tanpa memanggil fungsi insert: nama client sintetis untuk rs-001 menjadi Og Hospital (PASS); ID tidak ada menghasilkan HTTPException 404 (PASS dependency, bukan respons HTTP endpoint). Ini tambahan dua pemeriksaan di luar 32 kasus HTTP.

### Temuan keamanan dan bug tersisa
1. **FAIL deployment port isolation:** Compose workspace menetapkan loopback untuk semua service, tetapi docker ps menunjukkan PostgreSQL 5433 dan Fuseki 3030 masih bind 0.0.0.0 serta IPv6 semua interface. Backend 8000 sudah 127.0.0.1. Belum menguji keterjangkauan dari LAN/firewall. Container tidak direcreate.
2. **FAIL schema parity:** booking live belum memiliki CHECK dan index status dari schema.sql; create_all tidak menyelaraskan tabel existing. Tidak dilakukan migrasi.
3. **Risiko privilege:** koneksi aplikasi memakai role superuser PostgreSQL. Perlu role runtime terbatas dalam perubahan terencana.
4. **Operator authorization:** default-deny live PASS; konfigurasi key kosong membuat semua operasi operator tertutup. Jalur operator valid dan pembatalan SKIPPED, tidak mengambil data pasien existing.
5. **Public booking:** POST tetap publik, belum ada rate limit, autentikasi per pasien, audit operator atau idempotency. Tidak dilakukan stress/load test.
6. **Injection:** filter SPARQL memakai escaping literal dan ID regex; satu payload injection read-only tidak memperluas hasil. Booking query memakai SQLAlchemy parameter binding. SQL injection terhadap PostgreSQL melalui operator valid belum diuji. Tidak menjalankan payload UPDATE/DELETE atau exploit SERVICE.
7. **Proxy SPARQL:** endpoint /query tidak sama dengan sandbox query; query pengguna masih dapat berat atau menggunakan federasi SERVICE. Tidak menguji SSRF atau write endpoint Fuseki. Bind loopback tidak menggantikan autentikasi.
8. **Error handling:** 400/403/404/422 teramati. Handler dependency outage 502/503 hanya review kode/historis fixture; service tidak dihentikan untuk fault injection.
9. **Frontend:** file disk patch hero/race/mobile sama dengan workspace, tetapi browser live belum dieksekusi. Bukti browser Tahap 1B tetap fixture, tidak dinaikkan menjadi live.
10. Risiko dataset koordinat perkiraan/inferensi layanan dan BPJS, mode darurat, loader graph parsial, serta grounding sapaan/FAQ belum selesai. Health 206 bukan bukti kualitas seluruh fakta.

### SKIPPED dan rencana pengujian aman
- Browser desktop/mobile live: automatic approval review gagal karena batas penggunaan akun sebelum Chromium dijalankan. Ini kegagalan review, bukan penetapan tindakan tidak aman. Tidak mencoba melewati approval. Rencana browser memblokir semua write booking dan menguji hero, filter, race, detail, 375/768/1440 serta Deep Chat.
- Booking insert/cancel/collision/rollback PostgreSQL: tidak tersedia database test terpisah. Siapkan database testing bernama khusus dengan role terbatas dan tanpa data pasien; pastikan DATABASE_URL proses test menunjuk ke database tersebut, auto-load RDF dimatikan, AI dimatikan, lalu uji canonical identity, UNIQUE collision, CHECK, rollback, authorization dan konkurensi. Jangan menjalankan test fixture lama langsung pada database utama.
- Restart startup, dependency outage, LAN penetration/load, DBpedia eksternal, AI berbayar, GPS/routing: tidak dijalankan.

### Patch dan tindak lanjut
Tidak ada patch kode aplikasi pada Tahap 1C; temuan utama memerlukan perubahan deployment/schema yang sengaja tidak dilakukan saat audit. Hanya laporan diperbarui. Tahap 1 **belum COMPLETED** sampai transaksi PostgreSQL terisolasi, browser live, perbedaan skema dan eksposur port ditindaklanjuti. Hasil live pencarian dan semantik sudah PASS, tidak lagi hanya fixture SQLite/RDFLib.

## L. Tahap 1D - baseline regresi dan rencana rollout (17 November 2026)

Status **BLOCKED untuk integrasi live; Tahap 1 tetap PARTIAL**. Docker CLI tersedia tetapi koneksi Engine gagal: pipe dockerDesktopLinuxEngine tidak ditemukan. Ini berbeda dari snapshot live Tahap 1C; hasil lama tidak diklaim sebagai hasil saat ini. Tidak otomatis menyalakan/recreate service atau mengubah konfigurasi aktif.

| Pemeriksaan | Hasil | Bukti |
|---|---|---|
| Git status | PASS inspeksi | Perubahan sebelumnya dipertahankan; docs/ sudah ada dan tidak ditimpa |
| Docker Engine | BLOCKED | failed to connect; named pipe tidak ditemukan |
| docker compose config --quiet | PASS | Tidak ada error validasi; bukan bukti Engine aktif |
| Node frontend regression | PASS | 8 tests, 0 fail |
| Python regression | PASS isolated | 12 tests, 27.919 detik, OK; SQLite/RDFLib, bukan PostgreSQL/Fuseki |
| Backup database/Fuseki | BLOCKED | Engine tidak tersedia; belum ada backup yang dibuat/diklaim valid |
| Port container aktual dan perbaikannya | BLOCKED | Tidak dapat diinspeksi/recreate; konfigurasi loopback existing dipertahankan |
| Migrasi dan PostgreSQL test terpisah | BLOCKED / NOT TESTED | Belum dibuat/diterapkan; tidak menulis ke carisehat |
| Booking idempotency PostgreSQL | NOT TESTED | Tidak diimplementasikan atau diklaim selesai |
| Browser live, HTTP live, Fuseki live | NOT TESTED | Engine unavailable; bukti 1C tetap historis |

Perintah regresi: `node --test tests/frontend.test.cjs` dan `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_*.py'`. Fixture menetapkan SQLite memory, AI nonaktif dan RDF lokal. Warning deprecation Starlette/httpx tidak menggagalkan tes; pesan SPARQL error: test offline berasal dari skenario failure mock.

File Tahap 1D: docs/PHASE1D_ROLLOUT_PLAN.md (baru) dan laporan ini. Rencana mencakup backup privat, uji restore, konsistensi backup TDB2, recreate service terarah, guard database test, preflight migrasi dan rollback. Tidak ada kode anggota, .env, dataset, ontologi, database atau volume diubah. Tidak ada commit/push.

Belum ada blocker live yang diperbaiki. Risiko port, schema drift, superuser aplikasi, public booking/rate limit dan idempotency dari 1C masih terbuka. Tahap 2 belum siap sebagai kelanjutan dari Tahap 1 yang selesai. Langkah berikut: aktifkan Docker Desktop hingga Linux Engine siap; lanjutkan backup dan database test sintetis sesuai rencana sebelum perubahan aktif.

### Pembaruan Tahap 1D setelah Docker aktif

Status terbaru: **PARTIAL**, menggantikan blocker Engine pada awal bagian L. Engine dapat dihubungi kembali. Dengan izin eksplisit pengguna, hanya container PostgreSQL direcreate memakai volume k7_pgdata yang sama. Port aktual kini 127.0.0.1:5433; API tetap 127.0.0.1:8000. Health setelah recreate HTTP 200 (postgres/fuseki ok, 206 RS); search limit=500 HTTP 200 count=206.

Backup PostgreSQL: pg_dump format custom di /var/lib/postgresql/data/phase1d-backups/before-phase1d.dump, dibuat dengan umask 077; pg_restore --list berhasil. Backup masih dalam volume yang sama, bukan salinan disaster recovery independen dan belum restore-tested. Tidak ada data pasien dicetak/disalin ke fixture. Fuseki: NetworkSettings.Ports menunjukkan 3030/tcp=[] (tidak ada publikasi efektif), tetapi HostConfig.PortBindings masih HostIp kosong, HostPort 3030. Jangan menyatakan konfigurasi Fuseki sudah aman/persisten sebelum recreate dan pemeriksaan ulang. Izin jeda Fuseki untuk backup konsisten/recreate sudah ditanyakan, belum ada jawaban pada pembaruan ini; belum dihentikan.

Database carisehat_test_phase1d dibuat terpisah dengan dump schema-only dari produksi. Baseline booking=0 dibuktikan lewat current_database() dan COUNT. Fixture tidak menyalin data pasien. Tes memakai role koneksi existing (superuser), sehingga pembuktian least-privilege belum selesai.

Migrasi versioned baru: database/migrations/001_booking_constraints.up.sql dan .down.sql. Up menambah dua CHECK booking dengan NOT VALID lalu VALIDATE, default status menunggu, index status. Transaksi dibatasi lock_timeout 5s dan statement_timeout 30s. Down menghapus hanya objek tersebut untuk mengembalikan baseline audit. Up/down/up benar-benar lulus pada database test. Migrasi belum diterapkan ke produksi, belum memiliki version ledger/rerun guard, dan tidak boleh dijalankan berulang sembarangan. Belum ada tes data pelanggar atau restore backup.

Model backend/app/database/models.py diselaraskan pada CHECK/UNIQUE wilayah, CHECK RS, CHAR kelas, TEXT alamat/catatan, server defaults status dan CHECK/index booking. Ini perubahan metadata; tidak mengubah tabel existing secara otomatis. Perbedaan nullable created_at dan VARCHAR/TEXT booking live belum dimigrasi. API tanpa reload belum direstart, sehingga metadata proses aktif tidak diklaim telah diperbarui. Regresi Python sesudah perubahan: 12 tests PASS (3.741s), tetap isolated SQLite/RDFLib.

Tes PostgreSQL asli menggunakan FastAPI TestClient di proses terpisah dalam container, dependency session diarahkan ke database test, tanpa lifespan production. Fuseki tetap live untuk identitas RS; key operator hanya dummy dalam proses test. Hasil:
- PASS insert HTTP 201 dan nama canonical Og Hospital.
- PASS akses tanpa key 403, operator dummy 200, cancel 200.
- PASS collision UNIQUE pertama lalu retry berhasil 201.
- PASS lima collision berturut-turut menghasilkan 409; COUNT tetap 2 sebelum pengujian idempotency.
- **FAIL idempotency**: dua POST dengan Idempotency-Key sama membuat dua booking sintetis berbeda; header belum ditangani. Belum diperbaiki.
- COUNT produksi setelah tes tetap 1. Tidak ada transaksi tulis ke produksi.

Browser live (Chromium, booking submission dihapus dari skenario): homepage, hero Adam Malik, detail form, dan HTML semantik PASS. Skenario berhenti FAIL pada tombol #d-back: header intercepts pointer events hingga timeout 30s. Dua percobaan scroll-margin/scroll-padding tidak memperbaikinya dan dibatalkan; tidak meninggalkan patch CSS yang gagal. Console mencatat deprecation Deep Chat request/connect; request tile OSM beberapa ERR_ABORTED. Ini tidak sama dengan crash aplikasi, tetapi tidak boleh dicatat sebagai console/network bersih.

Tes browser independen: HTTP 200 pada viewport 375/768/1440, tidak ada horizontal overflow; Deep Chat nyata HTTP 200 dengan jawaban Kelas A. Tes ini dilakukan saat percobaan scroll-padding masih ada, sehingga belum mengesahkan layout final sesudah percobaan dibatalkan. Filter/race lanjutan dalam suite penuh belum dijalankan karena gagal lebih awal. Node frontend 8 PASS; git diff --check PASS pada pemeriksaan sebelum catatan ini.

File tambahan/perubahan terbaru: models.py; dua SQL migrasi; laporan ini. Dataset, ontologi, .env, booking produksi, dan volume tidak dihapus/diubah isinya oleh migrasi. PostgreSQL backup dan database sintetis tetap disimpan. Belum siap menyatakan Tahap 1 selesai atau masuk Tahap 2: idempotency, detail navigation, backup restore, least-privilege, migrasi produksi, dan konfigurasi Fuseki masih perlu dituntaskan.

### Fuseki: maintenance disetujui dan selesai (17 November 2026)
Pengguna menyetujui jeda backup/recreate Fuseki. Sebelum stop, mount dipastikan volume k7_fusekidata. Fuseki dihentikan dengan grace period 30s; TDB2 dicadangkan saat container berhenti melalui docker cp stream tar ke direktori profil pengguna di luar Git. Arsip: C:/Users/User/AppData/Local/CariSehat-private-backups/20261117T094320Z/fuseki-data.tar, 201395200 byte, 45 anggota. Semua isi file arsip berhasil dibaca; SHA-256 8503b35b3c15a06daa5c6d1c235f16d31dca328b6882b956a27931e9031699fa. Metadata rollback image ID, volume, command dan port disimpan berdampingan, tanpa environment/kredensial. Validasi arsip bukan restore drill; restore ke volume terpisah belum diuji. Tidak menghapus volume atau menimpa data TDB2.

`docker compose up -d --no-deps fuseki` berhasil. Mount setelah recreate tetap k7_fusekidata. NetworkSettings.Ports dan docker ps mengonfirmasi **127.0.0.1:3030**. PostgreSQL **127.0.0.1:5433**, API **127.0.0.1:8000**. Container prak-postgres milik proyek lain tidak disentuh.

Verifikasi setelah recreate:
- PASS /api/health HTTP 200: postgres=ok, fuseki=ok, jumlah_rs=206.
- PASS /api/search?limit=500 HTTP 200: count=206.
- PASS direct Fuseki /hospital/query HTTP 200: COUNT DISTINCT RS=206.
- PASS /rs/rs-001.ttl HTTP 200: RDFLib parse 45 triple.

Blocker eksposur port tiga service CariSehat kini terselesaikan pada binding aktual. Autentikasi Fuseki/least-privilege, idempotency booking, migrasi produksi dan detail navigation tetap belum selesai; status keseluruhan PARTIAL. Jika rollback diperlukan, hentikan hanya Fuseki, gunakan image ID tercatat dan volume yang sama terlebih dahulu; restore arsip harus diuji di volume baru dan memerlukan keputusan eksplisit sebelum mengganti data aktif. Jangan mengembalikan eksposur semua interface secara otomatis.

## M. Tahap 1E — persistent idempotency, navigasi dan restore drill
Status **PARTIAL untuk deployment produksi**; implementasi P0 dan pengujian PostgreSQL/browser berhasil. Tidak ada migrasi produksi/restart API atau penggantian kredensial dilakukan.

Idempotency memakai ledger PostgreSQL baru (migrasi 002 up/down), PK scope+hash key, fingerprint payload dan FK booking; tidak menyimpan pasien mentah pada ledger. Transaksi atomik, replay identik, 409 payload berbeda, response dibentuk sebelum commit. PostgreSQL test membuktikan 8 concurrent requests menghasilkan satu ID, conflicting concurrency 201/409, collision/retry/rollback, lost commit acknowledgement recovery, restart proses dan next-day replay. Request tanpa key tetap kompatibel tetapi tidak dijamin idempotent. Produksi count=1 dan private row fingerprint tetap sama; ledger produksi belum ada.

Navigasi detail: modal terperangkap stacking context aside (100) di bawah header (1100); dipindahkan ke body. Closed Deep Chat ternyata masih menangkap pointer di mobile; ditutup dengan display:none. Back + filter sesudahnya PASS di 375/768/1440 tanpa force-click. Final browser 11 counted checkpoints + 3 back/filter assertions PASS, zero pageerror; console deprecation Deep Chat dan beberapa ERR_ABORTED tetap dicatat. Tes expanded akhir reduced-motion; tidak mengklaim semua motion/perangkat diuji.

Regresi: Node 8 PASS; Python 12 PASS isolated; live health/search HTTP 200 count 206; SPARQL langsung HTTP 200 count 206; RDF detail 45 triple; local RDF 5564/73/381 triple; Compose config dan diff check PASS. Migasi 002 up/down/up hanya di carisehat_test_phase1d. Ledger existing dipertahankan saat runner diulang.

Dengan persetujuan eksplisit pengguna, restore backup PostgreSQL ke carisehat_restore_phase1e berhasil (4 tabel, 1 booking), CONNECT PUBLIC dicabut. Database restore privat mengandung backup pasien, BUKAN fixture sintetis. Fuseki dipulihkan ke volume carisehat_phase1e_restore/container carisehat-fuseki-restore-phase1e, network none, tanpa port host: 206 RS PASS. Resource dipertahankan, cleanup belum disetujui. Role NOLOGIN sintetis phase1e_test_runtime dengan flags superuser/createdb/createrole false dan grants minimum berhasil insert/replay/cancel via SET ROLE di database test; role produksi tidak diganti.

File 1E: booking.py; migrasi 002 up/down; frontend/index.html (perubahan minimal dan koreksi klaim terverifikasi); tests/test_backend.py; tests/phase1e_postgres.py; tests/phase1e-browser.cjs; handoff baru dan laporan ini. Dataset, ontologi, generator dan .env tidak diubah. Tidak commit/push/reset/stash. Perbaikan produksi baru memerlukan persetujuan migrasi dan restart API; rate limit, runtime credentials, client idempotency dan kebijakan retention masih terbuka. Lihat handoff sebelum masuk Tahap 2.
