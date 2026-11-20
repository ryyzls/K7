# Laporan Akhir: Audit, Pengamanan, dan Verifikasi Endpoint SPARQL CariSehat

**Tanggal Audit:** 20 November 2026  
**Peran:** Senior Backend Engineer, Semantic Web Engineer, Security Reviewer  
**Status Evaluasi:** **PASS (Sistem Aman dan Siap Presentasi)**  
**Target Rilis/Presentasi:** 25 November 2026  

---

## 1. Temuan Keamanan Sebelum Perbaikan

Sebelum dilakukan pengamanan bertingkat (*defense-in-depth*), audit arsitektur menemukan potensi celah keamanan pada interaksi SPARQL:

| ID | Komponen / Endpoint | Temuan | Tingkat Risiko |
|:---|:---|:---|:---:|
| **SEC-01** | `/sparql/query` (Proxy) | Tanpa guard semantik, endpoint query menerima arbitrary query strings yang berisiko disusupi klausa SPARQL 1.1 Update (`INSERT DATA`, `DELETE WHERE`, `DROP GRAPH`, `CLEAR ALL`, `LOAD`). | **P0 (Critical)** |
| **SEC-02** | Federated SPARQL (`SERVICE`) | Celah Server-Side Request Forgery (SSRF) melalui klausa `SERVICE <uri>`. Penyerang dapat memicu Fuseki untuk memindai jaringan lokal internal (`localhost:3030`, `192.168.x.x`, `10.x.x.x`, `host.docker.internal`). | **P0 (Critical)** |
| **SEC-03** | DoS via Resource Exhaustion | Ketiadaan pembatasan ukuran payload request query dan ketiadaan pembatasan otomatis jumlah baris hasil (`LIMIT`) berpotensi membebani CPU dan memori Fuseki/FastAPI. | **P1 (High)** |
| **SEC-04** | Fuseki Direct Access | Port 3030 Fuseki terikat ke `127.0.0.1:3030` pada host laptop (bukan `0.0.0.0`), namun backend proxy `/sparql/query` terbuka untuk publik/browser. | **P1 (High)** |
| **SEC-05** | Multi-statement Query Injection | Injeksi multi-statement (`SELECT ... ; INSERT ...`) yang dapat mengelabui regex sederhana pencari kata awal jika tidak diuraikan dengan AST parser. | **P0 (Critical)** |

---

## 2. Tingkat Risiko dan Bukti Evaluasi

- **P0 - Mutasi Dataset Semantik:** Jika operasi `DROP` atau `DELETE WHERE` dapat dieksekusi, 206 data rumah sakit dan 5.833 tripel RDF W3C (pada dataset `hospitals-sumut.ttl`) dapat terhapus secara permanen dari triplestore TDB2 Fuseki.
- **P0 - SSRF Jaringan Internal:** Fuseki yang menjalankan `SERVICE <http://127.0.0.1:5432>` atau service internal lain dapat membocorkan informasi atau memetakan port internal container Docker.
- **P1 - DoS dan Memory Spike:** Permintaan query tanpa `LIMIT` atau query berukuran > 50 KB berisiko membuat thread worker FastAPI macet (*hung*) atau kehabisan memori.

---

## 3. File yang Diubah

1. **`backend/app/services/sparql_guard.py`** (Implementasi utama guard keamanan)
2. **`backend/app/routers/semantic.py`** (Integrasi proxy `/sparql/query`, payload guard, exception timeout 504/503)
3. **`backend/tests/test_sparql_guard.py`** (Suite pengujian komprehensif 22 skenario keamanan)

*(Catatan: Tidak ada perubahan pada dataset 206 RS, skema database PostgreSQL, Docker Compose, atau uncommitted work agent lain).*

---

## 4. Penjelasan Singkat Perubahan

### A. Dual-Layer Security Guard (Defense-in-Depth)
1. **Lapisan 1 - W3C SPARQL 1.1 AST Parser (`rdflib.plugins.sparql.parser`)**:
   - Query diuraikan ke dalam pohon sintaks abstrak (*Abstract Syntax Tree* / AST).
   - Validasi root node: hanya menerima `SelectQuery`, `AskQuery`, `ConstructQuery`, dan `DescribeQuery`.
   - Deteksi otomatis operasi mutasi: pemanggilan `parseUpdate()` mendeteksi perintah DDL/DML SPARQL 1.1 bahkan jika dikemas secara kompleks.
   - Deteksi klausa `SERVICE` pada tingkat AST (`ServiceGraphPattern`) untuk memblokir federated SPARQL secara presisi.
   - Kebal terhadap *false positive* komentar (`# INSERT`) dan string literal (`"This is not an INSERT"`).

2. **Lapisan 2 - Lexical Skeleton & SSRF Protection**:
   - Deteksi dan penolakan multi-statement berpemisah titik koma (`;`).
   - Pemindaian IRI lokal/internal (`localhost`, `127.0.0.1`, `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`, `fuseki`, `carisehat`, `internal`, `host.docker.internal`).
   - Batas ketat ukuran query teks (maksimal 50 KB / `MAX_QUERY_BYTES`).

### B. Enforce Result Limit & Timeout
- **Auto-Enforce LIMIT:** Fungsi `enforce_result_limit` secara otomatis menambahkan `LIMIT 1000` jika query SELECT tidak mencantumkan batasan, atau memotong nilai LIMIT jika pengguna meminta > 1000 baris.
- **HTTP Payload Guard:** Memeriksa `Content-Length` request header (maksimal 100 KB) sebelum memuat body ke memori.
- **Strict Timeout:** Timeout proxy dibatasi maksimal 10 detik (`PROXY_TIMEOUT = 10`), dengan pemetaan status HTTP yang informatif:
  - `504 Gateway Timeout` jika Fuseki lambat/timeout.
  - `503 Service Unavailable` jika Fuseki sedang offline.

### C. Kompatibilitas SPARQL Studio / YASGUI
- Endpoint `/sparql/query` tetap mendukung metode `GET` dan `POST` dengan Content-Type `application/sparql-query`, `application/x-www-form-urlencoded`, dan `application/sparql-results+json`.
- Halaman playground `/sparql` (YASGUI) tetap berfungsi normal dan transparan.

---

## 5. Pengujian yang Dijalankan dan Hasil Aktual

Pengujian dijalankan langsung pada *environment* proyek menggunakan runner Python lokal:

### A. SPARQL Security Guard Suite (`backend/tests/test_sparql_guard.py`)
| Test Case | Deskripsi Skenario | Hasil Aktual |
|:---|:---|:---:|
| **TC01** | `SELECT` query valid | **PASS** |
| **TC02** | `ASK` query valid | **PASS** |
| **TC03** | `CONSTRUCT` query valid | **PASS** |
| **TC04** | `DESCRIBE` query valid | **PASS** |
| **TC05** | Mutasi `INSERT DATA {...}` | **PASS (BLOCKED)** |
| **TC06** | Mutasi `DELETE WHERE {...}` | **PASS (BLOCKED)** |
| **TC07** | `SERVICE <http://localhost:3030/>` (SSRF) | **PASS (BLOCKED)** |
| **TC08** | `SERVICE` eksternal (DBpedia/W3C) | **PASS (BLOCKED)** |
| **TC09** | Query melebihi batas ukuran (> 50 KB) | **PASS (BLOCKED)** |
| **TC10** | Query kosong | **PASS (BLOCKED)** |
| **TC11** | Query hanya spasi/whitespace | **PASS (BLOCKED)** |
| **TC12** | Operasi `LOAD <uri>` | **PASS (BLOCKED)** |
| **TC13** | Operasi `DROP GRAPH <uri>` | **PASS (BLOCKED)** |
| **TC14** | Operasi `CLEAR ALL` | **PASS (BLOCKED)** |
| **TC15** | Operasi `CREATE GRAPH <uri>` | **PASS (BLOCKED)** |
| **TC16** | Kata "INSERT" di dalam komentar `#` | **PASS (DIIZINKAN)** |
| **TC17** | Kata "INSERT" di dalam string literal `""` | **PASS (DIIZINKAN)** |
| **TC18** | Multi-statement `SELECT ... ; INSERT ...` | **PASS (BLOCKED)** |
| **TC19** | `enforce_result_limit` tanpa LIMIT awal | **PASS (LIMIT 1000)** |
| **TC20** | `enforce_result_limit` dengan LIMIT > 1000 | **PASS (Clamped ke 1000)** |
| **TC21** | `enforce_result_limit` dengan LIMIT wajar (10) | **PASS (Dipertahankan 10)** |
| **TC22** | `SERVICE` dengan IP privat internal (192.168.x.x) | **PASS (BLOCKED)** |
| **TOTAL** | **22 Skenario Pengujian Guard** | **22 PASS, 0 FAIL** |

### B. Live HTTP Security & Proxy Tests (`scratch/test_live_http_sparql.py`)
Pengujian HTTP aktual langsung ke container Docker yang sedang berjalan (`http://127.0.0.1:8000/sparql/query`):
1. **Live Backend Health & 206 RS:** `200 OK` (Fuseki=ok, Postgres=ok, jumlah_rs=206) -> **PASS**
2. **HTTP SELECT Valid:** `200 OK` (JSON bindings terstruktur) -> **PASS**
3. **HTTP ASK Valid:** `200 OK` (`boolean=True`) -> **PASS**
4. **HTTP CONSTRUCT Valid:** `200 OK` (text/turtle) -> **PASS**
5. **HTTP DESCRIBE Valid:** `200 OK` (text/turtle) -> **PASS**
6. **HTTP REJECT INSERT DATA:** `400 Bad Request` -> **PASS (BLOCKED)**
7. **HTTP REJECT DELETE WHERE:** `400 Bad Request` -> **PASS (BLOCKED)**
8. **HTTP REJECT DROP GRAPH:** `400 Bad Request` -> **PASS (BLOCKED)**
9. **HTTP REJECT CLEAR ALL:** `400 Bad Request` -> **PASS (BLOCKED)**
10. **HTTP REJECT SERVICE Localhost SSRF:** `400 Bad Request` -> **PASS (BLOCKED)**
11. **HTTP REJECT SERVICE External:** `400 Bad Request` -> **PASS (BLOCKED)**
12. **HTTP REJECT Multi-Statement Injection:** `400 Bad Request` -> **PASS (BLOCKED)**
13. **HTTP REJECT Query > 50KB:** `400 Bad Request` -> **PASS (BLOCKED)**
14. **HTTP REJECT Payload > 100KB (dengan Content-Length):** `413 Payload Too Large` -> **PASS (BLOCKED)**
15. **HTTP REJECT Payload > 100KB (TANPA Content-Length / Streamed):** `413 Payload Too Large` -> **PASS (BLOCKED)**
16. **HTTP Enforce Result Limit on SELECT:** `200 OK` (206 baris, terpotong otomatis <= 1000) -> **PASS**
**Hasil: 16 PASS, 0 FAIL**

### C. Eksekusi Skrip Audit Semantik & Browser Smoke Tests
1. **Audit SPARQL & DBpedia (`scripts/audit_sparql_dbpedia.py` - Patch 04):**
   - Internal Fuseki: **PASS** (hospital_count: 206, cities_count: 33, linked_regions: 34)
   - DBpedia External SPARQL Endpoint: **PASS**
2. **Semantic E2E Integration Tests (`scripts/audit_semantic_e2e.py` - Patch 05):**
   - **13 PASS, 0 FAIL, 0 BLOCKED**
   - Health check: Fuseki=ok, PG=ok, RS=206
   - RDFa markup, Open Graph tags, TTL & RDF/XML equivalence: PASS
   - SPARQL Studio HTTP & proxy select: PASS
3. **Browser E2E Smoke Tests (`tests/audit_browser_semantic.cjs` - Patch 06C):**
   - **11 PASS, 0 FAIL**
   - Homepage 206 RS, Hero Search, Filter Kelas C, Responsive 375/768/1440, YASGUI Browser render: PASS

### D. Regresi Unit Test Lainnya
- **Frontend Test Suite (`tests/frontend.test.cjs`):** 8/8 PASS
- **Chatbot Local Rule-Based Scenarios (`tests/run_tests.py`):** 14/14 PASS
- **Backend Search, Filters & Booking (`tests/test_backend.py`):** 7/7 PASS
- **Official Hospital Website Metadata (`tests/test_websites.py`):** 4/4 PASS

---

## 6. Risiko yang Masih Tersisa

1. **Port Fuseki Langsung (3030) pada Host Laptop:**
   - Di `docker-compose.yml`, port `3030` dipetakan ke `127.0.0.1:3030`. Siapapun yang memiliki akses shell ke laptop developer dapat memanggil endpoint `/hospital/update` secara langsung tanpa melalui backend FastAPI.
   - *Mitigasi:* Port hanya terikat ke loopback (`127.0.0.1`), bukan interface publik (`0.0.0.0`). Untuk demo Tugas Besar, konfigurasi ini sudah sesuai standar keamanan lokal.
2. **Ketergantungan Eksternal DBpedia:**
   - Fitur info kota DBpedia bergantung pada ketersediaan `https://dbpedia.org/sparql`. Jika jaringan publik down, service telah dilengkapi fallback lokal terisolasi (`unavailable`) sehingga website tidak crash.

---

## 7. Status Kesiapan Presentasi (25 November 2026)

**STATUS: SIAP PRESENTASI (READY FOR DEMO)**

1. Akses SPARQL publik melalui `/sparql/query` dan YASGUI Studio terbukti aman dari serangan manipulasi data RDF.
2. Pengujian akademis (SELECT, ASK, CONSTRUCT, DESCRIBE) berjalan lancar dan menghasilkan data valid 206 RS Sumatera Utara.
3. Seluruh suite pengujian otomatis proyek (Guard, Chatbot, Backend, Frontend) berstatus **100% HIJAU (PASS)**.

---

## 8. Rekomendasi Langkah Lanjutan (Opsional Pasca-Demo)

- Jika aplikasi dideploy ke server produksi publik berbasis cloud:
  - Lepas port `3030` dari bagian `ports:` di `docker-compose.yml` agar Fuseki hanya bisa diakses melalui jaringan internal Docker oleh service `backend`.
  - Pasang Apache Jena Fuseki Shiro authentication untuk administrasi triplestore.
