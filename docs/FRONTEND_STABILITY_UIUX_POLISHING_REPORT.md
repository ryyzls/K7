# CariSehat — Frontend Stability, Smooth Interaction & UI/UX Polishing Report

## 1. Executive Summary
Audit menyeluruh dan perbaikan frontend CariSehat telah diselesaikan dengan fokus pada stabilitas interaksi pencarian, penghilangan kedipan (*flickering*) daftar rumah sakit saat mengetik atau mengubah filter, perbaikan responsivitas mobile, serta peningkatan kehalusan UI/UX tanpa mengubah algoritma *Hybrid Semantic Search* maupun identitas visual CariSehat.

Seluruh metrik stabilitas utama tercapai pada pengujian pasca-perbaikan menggunakan Playwright (`scratch/after_frontend_audit.cjs`):
- **Kedipan daftar hasil (`listDisappearedObservations`)**: turun dari **14** menjadi **0**.
- **Kemunculan `"0 rumah sakit ditemukan"` saat loading (`zeroCountObservations`)**: **0**.
- **Request saat mengetik `"Jantung"` (7 karakter)**: turun dari **8 request** menjadi **1 request** (debounce 300 ms + perbaikan bug referensi array `omit`).
- **Request duplikat saat load awal (`/pencarian`)**: turun dari **2** menjadi **1**.
- **Document reload saat mengetik**: **0**.
- **Cumulative Layout Shift (CLS)**: **0.016** (baik, di bawah ambang batas 0.1).
- **Responsivitas lintas viewport (360px, 390px, 768px, 1024px, 1280px, 1440px, 1920px)**: **100% OK** (0 overflow di `/`, `/pencarian`, `/rumah-sakit/rs-171`, dan `/peta`).
- **Regresi mesin pencari (`tests/test_hybrid_search_200.py`, `tests/test_search_browser.cjs`, unit test backend)**: **100% PASS** (211/211 skenario, 16/16 unit test, seluruh browser test lulus).

---

## 2. Metodologi & Ruang Lingkup Audit
Audit dilakukan langsung terhadap source code aktual pada `frontend/src/` serta pengujian runtime menggunakan Playwright (Microsoft Edge headless) terhadap aplikasi yang berjalan di `http://127.0.0.1:8000`:
- Komponen yang diaudit: `App.jsx`, `SearchPage.jsx`, `DetailPage.jsx`, `SearchAutocomplete.jsx`, `HospitalCard.jsx`, `SiteHeader.jsx`, `api.js`, dan `index.css`.
- Pengukuran meliputi: jumlah request `/api/search`, observasi hilangnya elemen `#list li` selama pengetikan, kemunculan teks `"0 rumah sakit ditemukan"`, fokus input pencarian, document reload, CLS, console error, serta horizontal overflow (`scrollWidth - innerWidth`) di 7 ukuran viewport.

---

## 3. Akar Masalah (Root Cause Analysis)

### 3.1. Daftar Rumah Sakit Berkedip / Menghilang Saat Mengetik
1. **Tidak ada pola `keepPreviousData` pada `SearchPage.jsx`**: setiap kali filter atau `debouncedQ` berubah, `setLoading(true)` langsung mengganti seluruh `#list` dengan spinner (`Memuat katalog rumah sakit...`), sehingga daftar rumah sakit menghilang di setiap pencarian.
2. **Bug referensi array `omit` memicu request di setiap ketikan**: `useEffect([q])` memanggil `setOmit([])` yang menghasilkan referensi array baru (`[] !== []`) pada setiap perubahan `q`. Karena `omit` menjadi dependency `useEffect` fetch pencarian, fetch langsung berjalan di setiap karakter sebelum debounce 300 ms selesai (menyebabkan 8 request untuk 7 huruf `"Jantung"`).
3. **Penghapusan state pada error**: blok `.catch()` langsung memanggil `setItems([])` dan `setSearchMeta({})`, menghapus hasil yang sebelumnya tampil.
4. **Status jumlah hasil disembunyikan saat loading**: `{!loading && !error && <p>{items.length} rumah sakit ditemukan</p>}` menghilang selama fetch dan memicu lompatan layout kecil.

### 3.2. Horizontal Overflow pada Mobile (360px & 390px)
- Pada halaman `/pencarian` dan `/rumah-sakit/:id`, header `.d-head-inner` menampilkan logo 190px, `.d-site-nav` dengan 4 tautan `white-space: nowrap`, dan tombol aksi dalam satu baris tanpa media query mobile, sehingga melebar melewati 360px–390px (`+122px` di `/pencarian`, `+105px` di `/rumah-sakit/rs-171`).
- Padding horizontal 1.5rem dan grid/card yang belum memiliki `min-width: 0` turut mempersempit ruang konten pada layar sempit.

---

## 4. Perbandingan Metrik Sebelum vs Sesudah Perbaikan

| Metrik Pengujian | Baseline (Sebelum) | Sesudah Perbaikan | Status |
|---|---:|---:|---|
| `initialSearchRequests` (`/pencarian`) | 2 | 1 | Membaik |
| `requestsDuringTyping` (`"Jantung"`) | 8 | 1 | Membaik |
| `listDisappearedObservations` | 14 | 0 | Lulus |
| `zeroCountObservations` | - | 0 | Lulus |
| `inputFocusedAfterSearch` | - | `true` | Lulus |
| `docReloads` | 0 | 0 | Lulus |
| `cls` (Cumulative Layout Shift) | 0.0146 | 0.016 | Baik (< 0.1) |
| Console Errors | 0 | 0 | Lulus |
| Overflow 360px (`/pencarian`) | `OVERFLOW(+122px)` | `OK` | Lulus |
| Overflow 390px (`/pencarian`) | `OVERFLOW(+92px)` | `OK` | Lulus |
| Overflow 360px (`/rumah-sakit/rs-171`) | `OVERFLOW(+105px)` | `OK` | Lulus |
| Overflow 390px (`/rumah-sakit/rs-171`) | `OVERFLOW(+75px)` | `OK` | Lulus |
| Overflow 768px–1920px (semua halaman) | `OK` | `OK` | Lulus |

---

## 5. Ringkasan Perubahan Kode

1. **`frontend/src/pages/SearchPage.jsx`**
   - Memisahkan `loading` (load awal sebelum data pertama hadir) dan `isUpdating` (fetch lanjutan dengan `keepPreviousData`).
   - Mempertahankan `items` dan `searchMeta` sebelumnya selama `isUpdating` maupun saat terjadi error jaringan sementara (disertai banner error ringan + tombol `Coba Lagi` berbasis `retryTick`).
   - Mengganti dependency `omit` menjadi `omitKey = omit.join('|')` dan hanya mereset `omit` ketika `prev.length > 0` agar debounce 300 ms bekerja efektif (1 request per jeda ketik).
   - Menambahkan skeleton loader saat initial load (`loading && items.length === 0`) dan transisi opasitas halus (`.is-updating`) saat pembaruan hasil.
   - Menjaga tampilan jumlah hasil (`{items.length} rumah sakit ditemukan`) dengan indikator `(memperbarui...)` saat fetch berlangsung.
   - Menambahkan penyimpanan dan pemulihan posisi scroll (`sessionStorage` key `carisehat_search_scroll`).
   - Menyelaraskan container status/chip (`.search-meta-bar`) dengan `.filters` dan `.hospital-grid`.

2. **`frontend/src/api.js`**
   - Menambahkan cache hasil pencarian in-memory (`TTL 30 detik`, maksimum 60 entri) pada `searchHospitals` untuk mempercepat navigasi bolak-balik dan query berulang.

3. **`frontend/src/App.jsx`**
   - Menyesuaikan `ScrollToTop` agar tidak memaksa scroll ke atas saat kembali ke `/pencarian` ketika `carisehat_search_scroll` tersimpan.

4. **`frontend/src/components/HospitalCard.jsx`**
   - Membungkus komponen dengan `React.memo` untuk mencegah re-render kartu yang tidak berubah dan menambahkan `decoding="async"` pada gambar kartu.

5. **`frontend/src/index.css`**
   - Menambahkan styling `.search-meta-bar`, `.hospital-grid.is-updating`, `contain: layout style`, dan animasi `.skeleton-card`.
   - Menambahkan media query `@media (max-width: 768px)` dan `@media (max-width: 640px)` untuk `.d-head-inner`, `.d-site-nav`, `.brand-image`, `.d-body-inner`, `.d-quicknav`, `.d-card`, `.info-grid`, `.explorer-header`, `.filters`, `.hospital-grid`, `.card-btn-group`, dan `.d-alternatives-grid` guna menghilangkan overflow mobile.
   - Menambahkan `@media (prefers-reduced-motion: reduce)` untuk aksesibilitas.

---

## 6. Hasil Pengujian Build & Regresi Pasca-Perubahan

1. **Production Build (`npm --prefix frontend run build`)**:
   - Berhasil tanpa error (`vite v6.4.6`, selesai dalam `5.88s`).
2. **Playwright Frontend Stability & Responsive Audit (`node scratch/after_frontend_audit.cjs`)**:
   - `listDisappearedObservations: 0`, `requestsDuringTyping: 1`, `docReloads: 0`, `cls: 0.016`, `consoleErrors: []`, seluruh viewport 360px–1920px `OK`.
3. **Browser E2E Search Tests (`node tests/test_search_browser.cjs`)**:
   - `ALL BROWSER TESTS PASSED!` (autocomplete, NL query + filter chips, typo correction, empty state, reset filter & pagination, mobile viewport).
4. **Backend Unit Regression (`python -m unittest tests/test_semantic_final_repairs.py tests/test_carisehat_feature_freeze.py tests/test_specialties.py`)**:
   - `Ran 16 tests in 5.614s — OK`.
5. **Hybrid Semantic Search 211-Scenario Suite (`python -u tests/test_hybrid_search_200.py`)**:
   - `211/211 passed` (`pass_rate: 100.0%`, `mean_precision: 100.0%`, `mean_recall: 100.0%`, `mrr: 1.0`, `security_pass_rate: 100.0%`, `duplicate_rate: 0.0%`).

---

## 7. Artefak Screenshot
- Sebelum perbaikan: `docs/screenshots/before_search_desktop.png`, `docs/screenshots/before_search_mobile.png`, `docs/screenshots/before_home_desktop.png`, `docs/screenshots/before_detail_desktop.png`, `docs/screenshots/before_map_desktop.png`
- Sesudah perbaikan: `docs/screenshots/after_search_desktop.png`, `docs/screenshots/after_search_mobile.png`, `docs/screenshots/after_home_desktop.png`, `docs/screenshots/after_detail_desktop.png`, `docs/screenshots/after_map_desktop.png`
