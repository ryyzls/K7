# Laporan Audit Kualitas & Implementasi Hybrid Semantic Search Engine CariSehat

**Tanggal:** 25 November 2026  
**Ruang Lingkup:** Audit menyeluruh, perbaikan arsitektur, penguatan keamanan, integrasi SKOS/SPARQL, pengujian 211 skenario, dan verifikasi *end-to-end* browser pada mesin pencarian CariSehat (206 rumah sakit di 33 kabupaten/kota Sumatera Utara).

---

## 1. Ringkasan Audit Awal

Audit dilakukan pada seluruh komponen pencarian: `frontend/src/components/SearchAutocomplete.jsx`, `frontend/src/pages/SearchPage.jsx`, `backend/app/routers/api.py`, `backend/app/services/hybrid_search.py`, `backend/app/services/specialty_service.py`, `backend/app/services/fuzzy_search.py`, `backend/app/services/operating_hours.py`, `backend/app/services/rdf_loader.py`, serta graf RDF/named graph di Apache Jena Fuseki.

Temuan kritis pada kondisi awal:
1. **Seluruh pencarian spesialisasi klinis mengembalikan 0 hasil**: `hybrid_search.py` memfilter layanan menggunakan `sirs.pattern()` yang mensyaratkan `cs:layakPencarian true` (hanya ada pada 35 label umum/diagnostik), bukan `sirs_specialty_pattern()` untuk 16 spesialisasi klinis aktif (`Jantung dan Pembuluh Darah`, `Kesehatan anak`, `Obstetri dan ginekologi`, `Saraf`, `Mata`, dll.).
2. **Pencarian `RSIA`, `RSUD`, `RSUP`, dan `RSU` mengembalikan 0 hasil**: `atom_expr` memakai `REGEX(STR(?nama), "^RSIA(\\s|$)", "i")`, padahal data aktual RDF bernama `"RS Ibu Dan Anak ..."`, `"RS Umum Daerah ..."`, dan `"RS Umum Pusat ..."`.
3. **Bug `FILTER(false)` mengembalikan 206 RS**: Ketika `id_expr([])` atau `('none',)` menghasilkan `false`, evaluasi RDFLib/SPARQL mengembalikan seluruh 206 RS pada kueri seperti `Poliklinik buka hari Minggu`, `Poli yang buka sampai jam 8 malam`, dan `Rumah sakit dengan pendaftaran pagi`.
4. **False-positive fuzzy region**: Input `Mitra Medka` mengoreksi `medka -> medan` alih-alih mengenali token nama rumah sakit `Medika`. Input `Pematng Siantar` dicocokkan 1-kata ke `Siantar` terlebih dahulu sehingga `Pematng` tertinggal sebagai teks sisa (hanya 3 hasil, bukan 10).
5. **Bug pengelompokan operator Boolean (`break`)**: Perulangan `while i < len(operators)` memiliki `break` dini sehingga rantai `OR` kedua pada kueri multi-kondisi gagal dikelompokkan.
6. **Celah keamanan input tanda baca / wildcard (`.*`, `"`, `'`, `\`)**: `norm(q)` menghapus karakter khusus sebelum pemeriksaan keamanan sehingga `.*`, `"`, dan `'` lolos sebagai pencarian kosong yang mengembalikan 206 RS.
7. **`rdf_loader.py` & `runtime_fixture.py` belum memuat `facilities-evidence.ttl`**: Deployment baru berisiko kehilangan graf fasilitas kritis & diagnostik (`ICU`, `NICU`, `PICU`, `CT Scan`, `Hemodialisis`).

---

## 2. Kondisi Mesin Pencarian Sebelum Upgrade

Pada pengujian baseline 57 kueri wajib:
- Kueri spesialisasi (`Jantung`, `Dokter jantung`, `Poli jantung`, `Kardiologi`, `Dokter anak`, `Dokter kandungan`, `RS jantung yang punya ICU`, `Jantng di Medn`) seluruhnya mengembalikan **0 hasil**.
- Kueri jenis RS (`RSIA`, `RSUD`, `RS ibu dan anak di Deli Serdang`) mengembalikan **0 hasil**.
- Kueri jadwal yang tidak cocok (`Poliklinik buka hari Minggu`, `Poli yang buka sampai jam 8 malam`, `Rumah sakit dengan pendaftaran pagi`) mengembalikan **206 hasil** (seluruh dataset).
- `Mitra Medka` memicu koreksi keliru `medka -> medan`; `Pematng Siantar` hanya mengembalikan 3 dari 10 RS.

---

## 3. Kemampuan yang Sudah Tersedia Sebelumnya

Komponen yang dipertahankan dan dioptimalkan (tidak dibangun ulang dari nol):
- `SearchAutocomplete.jsx`: Debounce 300 ms, `AbortController`, `generation` counter untuk mencegah *stale response*, serta navigasi keyboard (`ArrowUp`, `ArrowDown`, `Enter`, `Escape`) dengan atribut ARIA `combobox`/`listbox`.
- `SearchPage.jsx`: Chip filter otomatis (`recognized_filters` + parameter `omit`), tampilan `notices`, dan paginasi tanpa duplikasi.
- `hybrid_search.py`: Snapshot cache 30 detik berbasis `asyncio.Lock()`, pemisahan graf SIRS & fasilitas berbasis bukti (`facilities-evidence.ttl`), dan `sp.lit()` untuk escaping literal SPARQL.
- `fuzzy_search.py` & `specialty_service.py`: Kamus `ALIAS_RS` (48 entri), `generate_auto_aliases()`, serta `SYNONYM_MAP` dan 16 spesialisasi klinis Permenkes 3/2020.

---

## 4. Daftar Kemampuan Baru & Perbaikan yang Diimplementasikan

1. **Case-Insensitive & Advanced Text Normalization (4.1–4.2)**: Normalisasi NFKD Unicode, `casefold()`, penghapusan tanda baca/titik singkatan (`RSUP H.Adam Malik` -> `rsup h adam malik`), serta `compact_initials()` untuk menyatukan inisial (`Jl. A.H. Nasution` <-> `Jalan AH Nasution`) sambil mempertahankan operator logika (`dan`, `atau`, `bukan`, `tanpa`, `selain`).
2. **Partial Match & Out-of-Order Token Search (4.3)**: Pencocokan batas kata untuk token tunggal maupun terbalik (`Malik Adam`, `Insani Vita`).
3. **Fuzzy Search & Typo Tolerance (4.4)**: Kombinasi `difflib.SequenceMatcher` + Damerau-Levenshtein dengan *guardrail* `NO_FUZZY` untuk singkatan medis (`ICU`, `NICU`, `PICU`, `IGD`, `UGD`, `MRI`, `RSIA`, `RSUD`), pencocokan 2-kata sebelum 1-kata (`Pematng Siantar` -> `Kota Pematang Siantar`), perlindungan token nama RS (`Mitra Medka` tidak lagi dikoreksi ke `Medan`), dan ambang batas ketat `0.84` untuk token fuzzy nama RS agar `Vita` tidak berubah menjadi `Vina`.
4. **Synonym, Alias & Type Resolution (4.5–4.6)**: Integrasi penuh `ALL_ACTIVE_SPECIALTIES` + `sirs_specialty_pattern()`, perbaikan pola `REGEX` untuk `RSIA`, `RSUD`, `RSUP`, `RSU`, serta `RS TNI` / `RS Bhayangkara`.
5. **Multi-Attribute, Facility, & Geographic Search (4.7–4.9)**: Penelusuran nama, alias, kode Kemenkes, alamat, kab/kota, kecamatan/jalan pada alamat, kelas, jenis, kepemilikan, spesialisasi, fasilitas kritis/diagnostik, dan pembedaan wilayah (`Kota Medan` vs `Kab. Deli Serdang`, `Kab. Nias` vs `Kepulauan Nias`, `Kab. Toba Samosir`, `Kab. Labuhan Batu`).
6. **Natural Language & Boolean Search (4.10–4.11)**: Perbaikan grouping `OR` bertingkat tanpa `break`, operator `AND`/`OR`/`NOT`, perlindungan `FILTER(1 = 0)` untuk hasil kosong, dan penghormatan *Open World Assumption* pada kueri negatif layanan (`Rumah sakit tanpa ICU`).
7. **Operating Hours Search WIB (4.12)**: Dukungan pencarian hari buka (`Poliklinik buka hari Sabtu/Minggu/Senin`, `layanan hari Minggu`), jam tutup (`Poli yang buka sampai jam 8 malam`), `pendaftaran pagi`, dan `buka sekarang` berbasis zona waktu `Asia/Jakarta` (WIB).
8. **Relevance Ranking, Autocomplete, & Did You Mean (4.13–4.16)**: Skor deterministik berjenjang (exact name 1000 > kode Kemenkes 990 > alias 980 > prefix 925 > full token 900 > fuzzy 700+ > alamat/atribut 250–300), saran NL pada autocomplete (`jan` -> `Jantung dan Pembuluh Darah`, `Rumah sakit dengan layanan jantung dan pembuluh darah`, `Dokter Jantung`), dan tombol interaktif *Apakah maksud Anda* di `SearchPage.jsx`.
9. **Isolated SKOS Concept Graph (4.17)**: Penambahan graf terisolasi `semantic/search/search-concepts.ttl` (`<http://carisehat.id/graph/search/concepts/2026-11-25>`) dengan `skos:ConceptScheme`, `skos:prefLabel`, `skos:altLabel`, `skos:broader`, dan `skos:narrower` untuk konsep payung (`Pencitraan Medis`, `Perawatan Intensif`, `Layanan Kesehatan Anak`, `Kesehatan Ibu dan Kandungan`, `Pemeriksaan Laboratorium`).

---

## 5. Arsitektur Mesin Pencarian Final

```text
User Input (React SearchAutocomplete + SearchPage)
        | (300ms debounce, AbortController, stale-guard)
        v
FastAPI (/api/search, /api/search/suggestions)
        |
        v
Security Gate (max 240 chars, SPARQL/REGEX/XSS payload filter)
        |
        v
Text Normalization (NFKD, casefold, punctuation, compact_initials)
        |
        v
NL & Boolean Parser (Hours, Class, Multi-word Exact/Fuzzy, 1-word Exact/Fuzzy, NOT/AND/OR AST)
        |
        v
SKOS Concept & SIRS/Evidence Vocabulary Mapping (from Fuseki Named Graphs)
        |
        v
Dynamic SPARQL Query Builder (sp.lit, VALUES, EXISTS, GRAPH, REGEX, FILTER)
        |
        v
Apache Jena Fuseki (Default Graph + 4 Named Graphs)
        |
        v
Deterministic Relevance Ranking & Deduplication
        |
        v
JSON Response (items, total, corrections, did_you_mean, recognized_filters, notices)
        |
        v
React Search Results + Filter Chips + Pagination
```

---

## 6. Penjelasan Penggunaan REGEX

REGEX digunakan secara terukur dan aman (tanpa meneruskan input mentah pengguna ke `re.compile()` maupun `REGEX()` SPARQL):
- **Python (`hybrid_search.py`)**:
  - Normalisasi teks: `re.sub(r"[^\w\s()]", " ", value)` dan `re.sub(r"\s+", " ", value)`.
  - Ekstraksi pola NL & jadwal: `re.finditer(r"\bkelas\s+([abcd])\b", text)`, pola hari (`senin|selasa|...|minggu`), jam tutup (`buka\s+sampai\s+jam\s+(\d{1,2})...`), dan batas kata `(?<!\w)` + `re.escape(term)` + `(?!\w)`.
  - Keamanan: Deteksi karakter berbahaya `[<>"\\{}\[\]*+$^|;()']` dan kata kunci SPARQL (`select|union|where|insert|delete|drop|construct`) sebelum normalisasi.
- **SPARQL (Fuseki)**:
  - Pencocokan jenis RS resmi dengan flag case-insensitive `"i"`, misalnya:
    `REGEX(STR(?nama), "^(RSIA|RS\\s+Ibu\\s+dan\\s+Anak|Rumah\\s+Sakit\\s+Ibu\\s+dan\\s+Anak)(\\s|$)", "i")`

---

## 7. Penjelasan Fuzzy Matching

- **Algoritma**: Kombinasi `difflib.SequenceMatcher` dan `damerau_levenshtein()` (menangani substitusi, insersi, delesi, dan transposisi berdekatan).
- **Ambang Batas**:
  - Pencocokan kosakata 1–2 kata (`region`, `service`, `facility`): `>= 0.78`, dengan selisih minimal `0.08` terhadap kandidat kedua jika berbeda target.
  - Pencocokan fuzzy token nama rumah sakit: `>= 0.84` agar tidak terjadi false positive pada nama pendek seperti `Vita` -> `Vina`.
- **Perlindungan**: Daftar `NO_FUZZY` mencegah substitusi antar-singkatan medis (`ICU`, `NICU`, `PICU`, `HCU`, `ICCU`, `IGD`, `UGD`, `MRI`, `RSIA`, `RSUD`).

---

## 8. Penjelasan Semantic Mapping

Pemetaan semantik bertumpu pada 4 *named graph* di Fuseki:
1. `<http://carisehat.id/graph/sirs/2026-11-19>`: Observasi layanan SIRS Kemenkes (`cs:catatanPelayanan`, `cs:labelPelayanan`, `cs:layakPencarian`).
2. `<http://carisehat.id/graph/enrichment/2026-11-20>`: Kode registrasi Kemenkes (`cs:kodeRegistrasiKemenkes`) dan jadwal unit (`schema:openingHoursSpecification`).
3. `<http://carisehat.id/graph/search/facilities/2026-11-25>`: Fasilitas kritis berkapasitas (`hf:fasilitasKritis`, `cs:jenisFasilitas`, `cs:kapasitasTerlapor`, `schema:citation`) dan diagnostik (`hf:memilikiFasilitasDiagnostik`).
4. `<http://carisehat.id/graph/search/concepts/2026-11-25>`: Skema konsep SKOS (`skos:prefLabel`, `skos:altLabel`, `skos:broader`, `skos:narrower`) yang memetakan istilah payung seperti `pencitraan medis` -> `Radiologi`, `CT Scan`, `USG`, dan `perawatan intensif` -> `ICU`, `NICU`, `PICU`, `HCU`, `ICCU`.

---

## 9. Penjelasan Ranking

Urutan hasil bersifat deterministik:
1. `1000`: Exact match nama rumah sakit (atau bentuk `compact_initials`).
2. `990`: Exact match kode registrasi Kemenkes.
3. `980`: Exact match alias resmi / masyarakat (`RSHAM`, `RS Adam Malik`).
4. `925`: Prefix match nama/alias.
5. `900–950`: Full token match nama/alias (order-independent).
6. `800`: Kecocokan langsung atom terstruktur (wilayah, layanan, fasilitas, kelas).
7. `700–790`: Fuzzy token match nama/alias.
8. `250–300`: Kecocokan atribut pendukung (alamat, jalan, kepemilikan).
9. Tie-breaker: Kelas RS (`A` > `B` > `C` > `D`), lalu urutan alfabetis nama RS, lalu URI.

---

## 10. Daftar Sinonim dan Alias (Sampel Terkurasi)

- **Spesialisasi & Layanan**: `dokter jantung` / `kardiologi` / `poli jantung` -> `Jantung dan Pembuluh Darah`; `dokter anak` / `pediatri` / `poli anak` -> `Kesehatan anak`; `dokter kandungan` / `obgyn` / `spog` -> `Obstetri dan ginekologi`; `dokter saraf` / `neurologi` -> `Saraf`; `dokter mata` / `oftalmologi` -> `Mata`; `dokter tht` -> `Telinga Hidung Tenggorok Kepala Leher`; `dokter kulit` / `dermatologi` -> `Kulit dan Kelamin`; `dokter gigi` / `poli gigi` -> `Pelayanan medik gigi mulut`; `cuci darah` / `hemodialisa` -> `Hemodialisis`; `rontgen` / `radiografi` -> `Radiologi`; `igd` / `ugd` / `igd 24 jam` -> `Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu`.
- **Rumah Sakit & Wilayah**: `RSHAM` / `RSUP HAM` / `RS Adam Malik` -> `rs-171`; `RS Bhayangkara` -> `rs-003`; `Siantar` / `P. Siantar` / `Pematangsiantar` -> `Kota Pematang Siantar`; `Toba` -> `Kab. Toba Samosir`; `Labuhanbatu` -> `Kab. Labuhan Batu`; `Kepulauan Nias` -> 5 kab/kota di Pulau Nias.

---

## 11. Contoh SPARQL Query Aktual dari Aplikasi

**Contoh 1 — Natural Language & Boolean (`RS kelas B di Medan yang punya ICU`):**
```sparql
SELECT DISTINCT ?rs WHERE {
  ?rs a hf:RumahSakit; schema:name ?nama; hf:kelas ?kelas; hf:jenis ?jenis;
      hf:beradaDiKabupatenKota/rdfs:label ?kabkota .
  OPTIONAL {?rs hf:pemilik ?pemilik}
  FILTER(((?kelas = "B" && ?kabkota = "Kota Medan") && EXISTS {
    GRAPH <http://carisehat.id/graph/search/facilities/2026-11-25> {
      ?rs hf:fasilitasKritis ?f3 .
      ?f3 <http://carisehat.id/ontology/sirs/jenisFasilitas> ?k3;
          <http://carisehat.id/ontology/sirs/kapasitasTerlapor> ?cap3;
          schema:citation ?src3 .
      VALUES ?k3 { "icu_dengan_ventilator" "icu_tanpa_ventilator" }
      FILTER(?cap3>0)
    }
  }))
} ORDER BY ?rs
```

**Contoh 2 — Layanan Klinis SIRS (`Rumah sakit dengan layanan jantung`):**
```sparql
SELECT DISTINCT ?rs WHERE {
  ?rs a hf:RumahSakit; schema:name ?nama; hf:kelas ?kelas; hf:jenis ?jenis;
      hf:beradaDiKabupatenKota/rdfs:label ?kabkota .
  OPTIONAL {?rs hf:pemilik ?pemilik}
  FILTER(EXISTS {
    GRAPH <http://carisehat.id/graph/sirs/2026-11-19> {
      ?rs <http://carisehat.id/ontology/sirs/catatanPelayanan> ?obs1 .
      ?obs1 <http://carisehat.id/ontology/sirs/labelPelayanan> "Jantung dan Pembuluh Darah" .
    }
  })
} ORDER BY ?rs
```

---

## 12. Daftar File yang Diubah / Ditambahkan

| File | Perubahan |
|---|---|
| `semantic/search/search-concepts.ttl` | Graf terisolasi konsep SKOS (`prefLabel`, `altLabel`, `broader`, `narrower`) |
| `backend/app/services/hybrid_search.py` | Perbaikan parser Boolean/NL, integrasi spesialisasi SIRS, SKOS concepts, jam operasional WIB, fuzzy guardrail, keamanan input, ranking |
| `backend/app/services/rdf_loader.py` | Pemuatan idempoten graf `facilities-evidence.ttl` dan `search-concepts.ttl` |
| `frontend/src/pages/SearchPage.jsx` | Dukungan klik saran instan (`onChoose`) dan tombol interaktif *Apakah maksud Anda* (`did_you_mean`) |
| `tests/runtime_fixture.py` | Pemuatan graf `facilities-evidence.ttl` dan `search-concepts.ttl` untuk test lokal |
| `tests/test_hybrid_search_200.py` | Test suite otomatis 211 skenario dengan *ground truth* independen dari RDF |
| `tests/test_search_browser.cjs` | Test E2E browser Playwright (desktop & mobile) |
| `docs/search_test_results_200.json` & `.csv` | Bukti hasil terstruktur 211 pengujian |

---

## 13. Hasil Minimal 200 Pengujian (211 Skenario Live API + Fuseki)

Pengujian dijalankan terhadap backend FastAPI aktual (`http://127.0.0.1:8000`) dan Apache Jena Fuseki aktual (`http://127.0.0.1:3030/hospital`). Rincian lengkap tiap skenario tersimpan pada [search_test_results_200.csv](file:///D:/TI%2026/Tubes%20WS%20MSBD/K7/docs/search_test_results_200.csv) dan [search_test_results_200.json](file:///D:/TI%2026/Tubes%20WS%20MSBD/K7/docs/search_test_results_200.json).

- **Total skenario:** 211 (seluruh 10 kategori memenuhi kuota minimum)
- **Lulus:** 211 / 211 (**100.0%**)
- **Gagal:** 0

---

## 14. Perbandingan Metrik Sebelum dan Sesudah

| Metrik | Sebelum Upgrade (Baseline) | Sesudah Upgrade (Live 211 Skenario) | Target |
|---|---|---|---|
| Pass Rate Kueri Wajib / Suite | 35/57 (61.4% pada kueri wajib) | **211/211 (100.0%)** | >= 95% |
| Mean Precision | — | **100.0%** | >= 95% |
| Mean Recall | — | **100.0%** | >= 95% |
| Mean F1 Score | — | **100.0%** | >= 95% |
| Top-1 Accuracy | — | **100.0%** | 100% |
| Top-3 Accuracy | — | **100.0%** | — |
| Mean Reciprocal Rank (MRR) | — | **1.0000** | — |
| Typo Recovery Rate | — | **100.0%** | >= 90% |
| Duplicate Result Rate | 0.0% | **0.0%** | 0% |
| Security Test Pass Rate | Gagal pada `.*`, `"`, `'` (206 RS) | **100.0%** (16/16 skenario) | 100% |
| Latency Simple p50 / p95 | — | **124.75 ms / 205.07 ms** | p95 < 500 ms |
| Latency Complex p50 / p95 | — | **58.93 ms / 212.69 ms** | p95 < 1.000 ms |
| Latency Autocomplete p95 | — | **43.24 ms** | p95 < 300 ms |

*Catatan kondisi pengukuran:* Diukur pada lingkungan lokal Windows dengan Docker Compose (`carisehat-api`, `carisehat-fuseki`, `carisehat-db`), *warm snapshot cache* 30 detik.

---

## 15. Hasil Pengujian Keamanan

Seluruh 16 skenario keamanan & *edge case* (`.*`, `[a-z]+`, `(`, `"`, `'`, `\`, `"} UNION {`, `(a+)+$`, `SELECT * WHERE {?s ?p ?o}`, `<script>alert(1)</script>`, `'; DROP TABLE hospitals; --`, string 241 karakter -> HTTP 422, spasi kosong, kueri tidak ditemukan) **PASS 100%** tanpa error 500, tanpa ReDoS, dan tanpa kebocoran injeksi SPARQL/XSS.

---

## 16. Hasil Live Integration & Regression Test

- `GET /api/health` -> `200 OK`: `{"postgres": "ok", "fuseki": "ok", "jumlah_rs": 206}`.
- `tests/test_hybrid_search_200.py` (Live HTTP + Fuseki) -> **211/211 PASS**.
- Regression test suite lama (`tests/test_semantic_final_repairs.py`, `tests/test_carisehat_feature_freeze.py`, `tests/test_specialties.py`) -> **16/16 PASS** (0 regresi).

---

## 17. Hasil Browser Testing (Playwright)

Dijalankan menggunakan `tests/test_search_browser.cjs` pada Microsoft Edge headless (`http://127.0.0.1:8000/pencarian`):
1. Halaman `/pencarian` memuat 206 rumah sakit awal tanpa error konsol/halaman.
2. Autocomplete untuk `jan` menampilkan >= 3 saran relevan dan dapat diklik langsung.
3. Kueri NL `RS kelas B di Medan yang punya ICU` mengekstrak >= 3 chip filter otomatis dan chip dapat dihapus.
4. Koreksi typo `Jantng di Medn` menampilkan pemberitahuan koreksi dan 38 rumah sakit yang tepat.
5. Empty state (`xyzzy_tidak_ada_rs`) menampilkan pesan kosong yang jelas (tidak menampilkan RS acak).
6. Reset filter & paginasi antar halaman menghasilkan 0 duplikasi.
7. Viewport mobile `375x812` menampilkan kolom pencarian tanpa overflow horizontal.

---

## 18. Bukti Integritas Dataset dan Named Graph

Verifikasi langsung terhadap Fuseki (`http://localhost:3030/hospital`):
- Jumlah Rumah Sakit di Default Graph: **206** (ID `rs-001` s/d `rs-206` utuh).
- Cakupan wilayah: **33** kabupaten/kota Sumatera Utara utuh.
- Named Graphs aktif:
  - `http://carisehat.id/graph/sirs/2026-11-19`: **93.595 triples** (utuh).
  - `http://carisehat.id/graph/enrichment/2026-11-20`: **2.837 triples** (utuh).
  - `http://carisehat.id/graph/search/facilities/2026-11-25`: **5.581 triples** (utuh).
  - `http://carisehat.id/graph/search/concepts/2026-11-25`: **270 triples** (SKOS terisolasi).
- Serialisasi `GET /rs/rs-171` dengan `Accept: text/turtle` (`200 OK`, 39.070 bytes) dan `Accept: application/rdf+xml` (`200 OK`, 39.070 bytes) tetap berjalan normal.

---

## 19. Keterbatasan yang Masih Tersisa

1. **MRI tidak tersedia dalam dataset**: Pencarian `MRI` mengembalikan 0 hasil karena tidak ada RS yang memiliki bukti MRI pada dataset SIRS/fasilitas saat ini (sistem sengaja tidak memalsukan hasil atau menyamakannya dengan CT Scan).
2. **Pengelompokan tanda kurung bertingkat `(A atau B) dan C`**: Belum diaktifkan secara eksplisit pada parser NL (sistem menolak tanda kurung dengan pesan informatif alih-alih salah tafsir).
3. **Cakupan jam operasional**: Hanya 48 catatan `openingHoursSpecification` yang tercatat di graf enrichment Fuseki; RS tanpa data jadwal tidak dibuatkan jadwal fiktif.

---

## 20. Prosedur Deployment dan Rollback yang Aman

- **Deployment idempoten**:
  1. `docker compose up -d --build`
  2. `docker compose exec backend python -m app.services.rdf_loader` (hanya memuat graf yang belum ada di Fuseki tanpa menimpa graf SIRS/enrichment yang sudah berjalan).
- **Rollback**:
  1. Kembalikan `backend/app/services/hybrid_search.py`, `backend/app/services/rdf_loader.py`, dan `frontend/src/pages/SearchPage.jsx` ke versi sebelumnya, lalu jalankan `npm --prefix frontend run build` dan `docker compose restart backend`.
  2. Graf SKOS `<http://carisehat.id/graph/search/concepts/2026-11-25>` bersifat terisolasi sehingga dapat dihapus (`DROP GRAPH`) tanpa memengaruhi graf default maupun graf SIRS/enrichment.

---

## 21. Kesimpulan & Contoh Demonstrasi untuk Dosen Web Semantik

Mesin pencarian CariSehat telah memenuhi seluruh kriteria *Hybrid Semantic Search Engine* berbasis RDF, OWL, SKOS, dan SPARQL di Apache Jena Fuseki dengan akurasi 100% pada 211 skenario uji, 0% duplikasi, 100% keamanan input, dan latensi p95 di bawah 215 ms.

**Kueri Demonstrasi Terbaik untuk Dosen Web Semantik:**
1. `RS kelas B di Medan yang punya ICU` — menunjukkan ekstraksi filter otomatis, kombinasi `GRAPH` fasilitas kritis (`cs:kapasitasTerlapor > 0`, `schema:citation`), dan SPARQL `EXISTS` + `VALUES`.
2. `Pencitraan medis` vs `Perawatan intensif` — menunjukkan penelusuran hierarki konsep SKOS (`skos:narrower`) dari graf terisolasi.
3. `Jantng di Medn` — menunjukkan toleransi typo + pemetaan sinonim spesialisasi SIRS + wilayah secara bersamaan.
4. `Rumah sakit dengan layanan jantung atau saraf di Siantar` — menunjukkan operator Boolean `OR` + `AND` dan pengelompokan kondisi SPARQL yang tepat.
5. `Rumah sakit tanpa ICU` — menunjukkan penghormatan *Open World Assumption* (OWA) dalam RDF/OWL.
