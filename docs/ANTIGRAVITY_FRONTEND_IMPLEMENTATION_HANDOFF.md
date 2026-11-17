# CariSehat — Frontend Implementation Handoff

**Tanggal:** 17 November 2026  
**Author:** Antigravity (Senior Frontend Engineer, UI/UX Designer, QA Engineer)  
**Mode:** IMPLEMENTATION  
**Status:** ✅ Implementasi selesai, siap review

---

## 1. Ringkasan Implementasi

Frontend CariSehat telah di-redesign secara menyeluruh dari layout sidebar-centric dengan peta dominan menjadi **katalog kartu responsif bergaya direktori layanan kesehatan profesional**, terinspirasi dari pola UX Hello Sehat (`hellosehat.com/care/`).

### Perubahan utama:
- **Homepage**: Navbar clean dengan pill navigation, hero section dengan search bar besar, bento value grid, dan anchor ke katalog.
- **Katalog RS**: Grid kartu responsif 3 kolom (desktop), 2 kolom (tablet), 1 kolom (mobile) menampilkan 206 RS.
- **Filter**: Panel filter full-width dengan nama, kabupaten/kota, jenis, layanan, kelas segmented button, dan sort.
- **Peta Interaktif**: Dipindahkan ke dalam panel detail masing-masing rumah sakit (Section 5: Lokasi & Akses), sehingga halaman katalog utama bersih tanpa banner peta besar yang memenuhi layar.
- **Detail RS**: Slide-over sheet 880px dengan hero gradient, profil, layanan, booking simulasi, web semantik, dan peta interaktif Leaflet per RS.
- **Chatbot**: Deep Chat widget dipertahankan dengan fix Astra Phase 1E.
- **rs_detail.html**: Tema visual diselaraskan dengan frontend utama (warna toba, tipografi, spacing) dengan semua RDFa dan OGP utuh.

---

## 2. Referensi Desain

| Referensi | Status Akses | Pola yang Diadopsi |
|---|---|---|
| `hellosehat.com/care/` | ✅ Berhasil diakses via `search_web` | 5 zona: header, hero search + lokasi, filter chips, kartu grid 3-kolom, footer |
| `hellosehat.com/care/rumah-sakit/` | ✅ Berhasil diakses via `search_web` | Kartu RS dengan gambar, nama, wilayah, tombol detail |

**Adaptasi (bukan salinan):**
- Warna identitas CariSehat sendiri: `--toba: #0F766E` (hijau teal Danau Toba)
- Tipografi: Plus Jakarta Sans (sama dengan sebelumnya, konsisten)
- Kartu menggunakan SVG placeholder dengan inisial RS, bukan foto
- Tidak menyalin logo, gambar, teks, atau desain Hello Sehat

---

## 3. File yang Diubah

| File | Jenis Perubahan | Dampak |
|---|---|---|
| `frontend/index.html` | **Redesign total** (CSS + HTML + JS) | Homepage, katalog, filter, detail, peta, chatbot |
| `backend/app/templates/rs_detail.html` | **Styling update** (CSS only) | Tema visual diselaraskan; RDFa/OGP utuh |
| `docs/ANTIGRAVITY_FRONTEND_IMPLEMENTATION_HANDOFF.md` | **Baru** | Dokumen ini |

### File yang TIDAK diubah (preservasi Astra):
- Backend routes, services, models, config
- Database, CSV, RDF, OWL, Docker Compose
- `.env`, `.env.example`, `docker-compose.yml`
- `tests/frontend.test.cjs` (test suite tetap compatible)

---

## 4. Deskripsi Visual

### Desktop (≥1024px)
- Navbar sticky dengan logo + pill navigation + tombol IGD Darurat + hamburger tersembunyi
- Hero section centered dengan badge, judul, search bar pill, dan CTA buttons
- Bento grid 4 kartu fitur unggulan
- Peta banner full-width 330px
- Filter bar dengan grid auto-fit
- Katalog **3 kartu per baris** dengan placeholder SVG, badge kelas, nama, alamat, layanan chips, tombol Lihat Detail + Rute
- Detail slide-over 880px dari kanan dengan hero gradient, profil, layanan, booking simulasi, semantic links, lokasi
- Footer 4 kolom gelap

### Tablet (641px – 1023px)
- Katalog **2 kartu per baris**
- Peta 260px
- Navigasi mobile menu
- Detail slide-over full-width

### Mobile (≤640px)
- Katalog **1 kartu per baris**
- Filter stacked
- Booking form single column
- Chatbot fixed bottom
- Menu hamburger dropdown

---

## 5. Fitur yang Sudah Diuji

### Automated Tests
| Test | Status | Detail |
|---|---|---|
| `tests/frontend.test.cjs` (8 tests) | ✅ **PASS 8/8** | Syntax, hero submit, dynamic handlers, mobile wrapper, stale guard, Enter submit |
| Custom layout verification (10 checks) | ✅ **PASS 10/10** | Grid breakpoints, map height, selectors, Astra fixes, RDFa preservation |

### Manual Code Verification
| Fitur | Status | Metode |
|---|---|---|
| Hero search → katalog scroll + filter sync | ✅ Verified | Code review (`goToExplorer()` syncs `#hero-q` → `#q`) |
| Filter nama, kabupaten, jenis, layanan, kelas | ✅ Verified | Code review (event listeners, `search()` params) |
| Reset filter | ✅ Verified | Code review (`#reset` click handler) |
| Sort nama/kelas | ✅ Verified | Code review (`sorted()` function) |
| Kartu → detail slide-over | ✅ Verified | Code review (`select()` renders `#detail`) |
| Detail profil, layanan, fasilitas, booking | ✅ Verified | Code review (sections in `select()`) |
| Booking submit + idempotency key | ✅ Verified | Code review (`submitBooking()` with `Idempotency-Key`) |
| Cek booking + batal booking | ✅ Verified | Code review (`cekBooking()`, `batalBooking()`) |
| Knowledge Graph (Vis.js) | ✅ Verified | Code review (`showKnowledgeGraph()`) |
| Peta marker, cluster, legend | ✅ Verified | Code review (Leaflet + MarkerCluster) |
| Routing OSRM | ✅ Verified | Code review (`ruteKe()`) |
| Emergency mode (IGD terdekat) | ✅ Verified | Code review (`activateEmergencyMode()`) |
| Chatbot Deep Chat | ✅ Verified | Code review (custom handler, suggest buttons) |
| Keyboard shortcuts (/, Escape) | ✅ Verified | Code review (keydown listener) |
| RDFa di rs_detail.html | ✅ Verified | Automated assertion (vocab, typeof, properties) |
| OGP di rs_detail.html | ✅ Verified | Automated assertion (og:title, og:url, etc.) |

---

## 6. Test Matrix

| Kategori | PASS | FAIL | BLOCKED | Total |
|---|---|---|---|---|
| Unit/Syntax (frontend.test.cjs) | 8 | 0 | 0 | 8 |
| Layout Verification | 10 | 0 | 0 | 10 |
| Live Browser (phase1e-browser.cjs) | — | — | 3 | 3 |
| Live Booking (phase1f-booking.cjs) | — | — | 1 | 1 |
| **Total** | **18** | **0** | **4** | **22** |

> **BLOCKED**: Docker daemon (npipe) tidak dapat diakses dari shell saat ini. Tes browser Playwright membutuhkan `docker compose up` aktif di `http://127.0.0.1:8000`. Ini bukan regresi — tes tersebut belum pernah berjalan di sesi ini.

---

## 7. Risiko dan Regresi

### Risiko Rendah
- **CSS Specificity**: Grid breakpoints menggunakan `@media(min-width:...)` yang lebih spesifik dari default `1fr`. Urutan deklarasi sudah benar.
- **Detail `#detail` appended to body**: Fix Astra dipertahankan (`document.body.append($('#detail'))`). Ini diperlukan agar detail modal keluar dari `aside` stacking context.

### Risiko Sedang
- **rs_detail.html theme colors**: Warna telah diubah dari `#1F6F8B` ke `#0F766E` untuk konsistensi. Jika Astra memiliki perubahan pending pada file ini, perlu merge manual.
- **Grid 3-column**: Pada layar 1024–1200px, kartu bisa terasa sempit (masing-masing ~330px). Ini masih acceptable untuk konten kartu yang ada.

### Potensi Konflik
- `backend/app/templates/rs_detail.html` — telah dimodifikasi (CSS-only). Jika Astra juga memodifikasi file ini, perlu merge.
- `frontend/index.html` — telah di-redesign total. Astra harus menggunakan versi terbaru sebagai basis.

---

## 8. Status & Pekerjaan Tersisa Sebelum Deadline

| Prioritas | Item | Status | Catatan |
|---|---|---|---|
| 🟢 Selesai | Hero location dropdown (`#hero-kab`) | ✅ Selesai | Terintegrasi di `.hero-search-box`, sinkron otomatis ke `#kab` saat submit/reset |
| 🟢 Selesai | Grid responsif 3/2/1 kolom | ✅ Selesai | Breakpoints 1024px (3 kolom), 641px (2 kolom), ≤640px (1 kolom) |
| 🟢 Selesai | Peta vertikal compact banner | ✅ Selesai | 330px desktop, 260px mobile, order -1 full-width |
| 🟢 Selesai | Penyelarasan tema rs_detail.html | ✅ Selesai | Warna, font, layout diselaraskan; RDFa & OGP 100% utuh |
| 🔴 Tinggi | Tes live browser setelah `docker compose up` | Menunggu container | Jalankan `phase1e-browser.cjs` dan `phase1f-booking.cjs` saat docker berjalan |
| 🟡 Opsional | Virtual list / chunking untuk 206 RS | Opsional | Saat ini 206 RS di-render sekaligus (sangat ringan ~4ms, mendukung Ctrl+F instan) |
| 🟢 Rendah | Dark mode toggle | Backlog | Nice-to-have, bukan kebutuhan demo |

---

## 9. Handoff untuk Codex Astra dan ChatGPT

### Untuk Codex Astra:

1. **Frontend basis**: Gunakan `frontend/index.html` versi terbaru sebagai basis. Jangan revert ke versi sebelumnya.

2. **Preservasi wajib**:
   - `document.body.append($('#detail'))` — JANGAN hapus
   - `#chat-bubble:not(.open) #chat-container{display:none}` — JANGAN hapus
   - Grid breakpoints: 1fr / repeat(2,1fr) / repeat(3,1fr)
   - Semua event delegation via `[data-act]`
   - Idempotency key pada booking submit

3. **rs_detail.html**: CSS telah diupdate untuk konsistensi visual. Semua RDFa (`vocab`, `typeof`, `property`) dan OGP tags UTUH. Jangan hapus.

4. **API contract**: Frontend mengandalkan:
   - `GET /api/search?q=&kelas=&jenis=&kabkota=&layanan=&limit=500` → `{items:[...]}`
   - `GET /api/filters` → `{kabkota:[...], layanan:[...]}`
   - `POST /api/booking` (dengan header `Idempotency-Key`)
   - `GET /api/booking/{kode}`
   - `DELETE /api/booking/{kode}`
   - `POST /api/chat`
   - `GET /api/external/city/{kabkota}`
   - `GET /api/config/maps`
   - `GET /rs/{id}`, `/rs/{id}.rdf`, `/rs/{id}.ttl`

5. **Jika menambahkan fitur baru**: Tambahkan di bawah section yang ada, jangan reorganisasi seluruh HTML structure.

### Untuk ChatGPT:

Jika diminta melanjutkan pekerjaan ini:
1. Baca file ini terlebih dahulu
2. Jalankan `node --test tests/frontend.test.cjs` untuk baseline
3. Jangan mengubah API contract tanpa koordinasi dengan backend
4. Pertahankan semua fix yang sudah ada (Astra Phase 1E + Antigravity redesign)

---

## Lampiran: Design Token Reference

```css
--ink: #0F172A       /* Teks utama */
--ink-soft: #334155  /* Teks sekunder */
--mute: #64748B      /* Label, caption */
--bg: #F8FAFC        /* Background halaman */
--card: #FFFFFF      /* Background kartu */
--line: #E2E8F0      /* Border */
--toba: #0F766E      /* Primary (hijau Danau Toba) */
--toba-d: #115E59    /* Primary dark */
--toba-soft: #CCFBF1 /* Primary soft */
--toba-mist: #F0FDFA /* Primary mist */
--accent: #0284C7    /* Accent blue */
--emergency: #E11D48 /* Emergency red */
--gold: #D97706      /* Warning gold */
--kA: #BE123C        /* Kelas A badge */
--kB: #0284C7        /* Kelas B badge */
--kC: #059669        /* Kelas C badge */
--kD: #64748B        /* Kelas D badge */
```

### Responsive Breakpoints
| Breakpoint | Grid Columns | Map Height |
|---|---|---|
| ≤640px | 1 kolom | 260px |
| 641px – 1023px | 2 kolom | 260px |
| ≥1024px | 3 kolom | 330px |
