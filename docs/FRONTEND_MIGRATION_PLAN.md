# FRONTEND_MIGRATION_PLAN — Migrasi Fitur Legacy → CariSehat React

## Konfirmasi Review (opencode — 2026-11-23)

Fitur rusak/dilipat sesuai form Review:

1. Semua fitur hilang (1-9) sekaligai
2. Compare + RS Alternatif (Recommended)
3. Halaman/offset Peta + Mode Darurat
4. Detail RS: Jam operasional + Fasilitas enriched
5. Rute: instruksi belok + batal booking + per-page + persist filter
6. Klarifikasi peta: Halaman peta RS terpisah (openHospitalMap)

## Daftar Fitur Hilang (Legacy → React) — 1 sampai 9

| # | Fitur | Legacy (ref) | Status React sebelumnya | Target React |
|---|-------|--------------|-------------------------|--------------|
| 1 | Fitur Perbandingan RS (Compare, max 3 RS): toggle compare di kartu RS + CompareDock (count & pills) + Modal "Perbandingan Rumah Sakit" dengan tabel atribut faktual | index.legacy.html:3265-3605, 3862-3907, 5231-5320, 4720-4725; services/comparison_service.py | None | CompareDock + CompareModal, data `GET /api/compare?ids=a,b,c` |
| 2 | RS Alternatif Terdekat & Setara + tombol "Bandingkan langsung" | index.legacy.html:5051-5056, 5191-5228; services/alternatives_service.py | None | `AlternativesSection` di DetailPage, data `GET /api/hospitals/:id/alternatives` |
| 3 | Jam Operasional & Poliklinik (tabel day, blok IGD "Instalasi Gawat Darurat") | index.legacy.html:4202-4258; `GET /api/hospitals/:id/operational-hours` | Sidebar badge belaka | Tabel Jam Operasional + IGD di DetailPage |
| 4 | Rute instruksi belok ("Belok kanan", "Belok kiri tajam", "Serong kanan/kiri", "Putar balik", "Di ujung jalan, belok {modifier}") | index.legacy.html:6093-6112 | Panel rute tanpa teks instruksi | Panel rute dengan teks instruksi lengkap |
| 5 | Batal Booking ("Batalkan Booking") → `DELETE /api/booking/:kode` + confirm dialog | index.legacy.html:5548, 5555-5573 | None | Tombol Batal Booking di BookingForm status |
| 6 | Per-page selector (default 20, sessionStorage) | index.legacy.html:3862-3866, 4360, 6647-6651 | Fixed 12/page (SearchPage) | Selector per-page di SearchPage |
| 7 | Persist filter state (sessionStorage `carisehat_filter_ctx`, q/kab/kelas/lay/jenis/sort/page/perPage) | index.legacy.html:5941-5994, 6683 | URL-only | sessionStorage filter context di SearchPage |
| 8 | Knowledge Graph (Vis.js modal: RS, wilayah, Permenkes 3/2020, BPJS, dbpedia) | index.legacy.html:5575+, KnowledgeGraphModal.jsx (unused) | Component tanpa entry point | Tombol entry + modal |
| 9 | Halaman peta RS terpisep (openHospitalMap — sidebar pencarian + list + canvas, Escape close, own pagination) | index.legacy.html:4768-4844 | Merged ke /peta | Route peta terpisah (openHospitalMap page) |

## Langkah Eksekusi (versi sampel)

1. **Audit & Gap-check (Langkah 1 — sedang dijalankan)** — perbandingan legacy vs React, verifikasi cakupan fitur 1–9 (cek tidak ada compare/alternatives/jam_operasional/rute teks/batal di frontend/src; cek endpoint backend lengkap).
2. **Fitur Compare + RS Alternatih** — CompareDock, CompareModal (tabel atribut faktual, disclaimer bukanrating/biaya), card compare toggle + a11y.
3. **Jam Operasional & IGD** — DetailPage sidebar lengkap + schedule table + IGD badge; buka `GET /api/hospitals/:id/operational-hours`.
4. **Per-page + Persist Filter** — select per-page (10/20/50), save/restore sessionStorage `carisehat_filter_ctx`.
5. **Batal Booking** — tombol di status BookingForm → `DELETE /api/booking/:kode`, confirm, toast.
6. **Rute Instruksi Belok** — panel rute di MapPage + petunjuk lengkap + entry dari DetailPage.
7. **Halaman Peta RS Terpisah (openHospitalMap)** — route terpisah dengan sidebar list + pencarian.
8. **Knowledge Graph Entry** — wire KnowledgeGraphModal + tombol trigger.
9. **Verifikasi & Build** — `npm run build`, node `tests/frontend.test.cjs`, kemudian review kolom (QA) dan stabilisasi.

## Jawaban: "Apakah ini semua fitur yang hilang?"

**Ya, menurut audit Langkah 1: 9 fitur hilang (daftar 1–9 di atas) + kelemahan terdegradasi:**
- Jam Operasional: `DetailPage` punya badge belaka; rincian tabel + blok IGD hilang.
- Rute instruksi belok: panel ada (mode & jarak/durasi) tapi teks belok ("Belok kanan", …) hilang.
- openHospitalMap: sebagai halaman terpisah hilang (dilacak g Parking tercampur ke /peta).
Selain itu prioritas user: "Semua fitur hilang (1-9) sekaligai" = tabel fitur 1–9 adalah daftar lengkap.

## Langkah 2 — Fitur Compare + RS Alternatih (eksekusi sedang berlangsung)

Target eksekusi:
1. `api.js`: `compareHospitals(ids)` → `GET /api/compare?ids=a,b,c`; `getHospitalAlternatives(rsId, limit=4)` → `GET /api/hospitals/:id/alternatives`.
2. `CompareDock.jsx`: floating bar di SearchPage (count + pills), toggle max 3, aria-pressed; pesan maks 3 RS.
3. `CompareModal.jsx`: modal "Perbandingan Rumah Sakit" — tabel atribut faktual dari `comparison_matrix.shared_services`/per-RS dengan mapping label fakta (kode kemenkes, kabkota, kelas, alamat, telepon, website_resmi, spesialisasi_sirs, layanan_terkurasi, fasilitas) + disclaimer bukan rating/biaya/mengarang.
4. `HospitalCard.jsx`: tombol "Bandingkan" (toggle, aria-pressed, stopPropagation) — di SearchPage.
5. `DetailPage.jsx`: `AlternativesSection` — fetch `getHospitalAlternatives`, grid (foto, nama, kelas, kabkota, skor, alasan_rekomendasi), tombol "Lihat Detail" + "Bandingkan langsung" (navigate `/pencarian?compare=targetId`).
6. SearchPage: konsolidasi state compare (dari card toggle + param URL `?compare=`), render `<CompareDock>` + `<CompareModal>`; `detail` page tidak perlu dock.
7. Validasi: `npm run build`, `node tests/frontend.test.cjs`, lint-ish grep di frontend/src menunjukkan ada compare-dock/modal.

## Langkah 2 — Hasil (dieksekusi sekarang)

- `api.js`: + `compareHospitals(ids)` → `GET /api/compare?ids=a,b,c`; `getHospitalAlternatives(rsId, limit=4)` → `GET /api/hospitals/:id/alternatives`.
- `frontend/src/components/CompareDock.jsx`: floating bar bawah: "N terpilih — kombo:" + pills nama RS ×;"><i>"Bersihkan"</i>.
- `frontend/src/components/CompareModal.jsx`: modal "Perbandingan Rumah Sakit", tabel atribut faktual: Kode Registrasi Kemenches, Wilayah Kabupaten/Kota, Kelas, Jenis, Alamat, Telepon, Website Resmi, Spesialisasi SIRS, Layanan Terkurasi SIRS, Fasilitas (data katalog); disclaimer "Maksimal 3 rumah sakit" + disclaimer bukan rating/biaya.
- `frontend/src/components/HospitalCard.jsx`: + tombol "Band" toggle `aria-pressed`, di kartu RS.
- `frontend/src/pages/SearchPage.jsx`: + `compareIds` state (toggle kartu, max 3), `compareData` via `compareHospoons` (baca `compare` URL param), render `CompareDock` + `CompareModal`.
- `frontend/src/pages/DetailPage.jsx`: + `AlternativesSection` (RS alternatif: foto, nama, kelas, kabkota, jumlah layanan sama, alasan rekomendasi; tombol Lihat Detail + Band ke `/pencarian?compare=<targetId>`).
- Validasi: `npm install` (7s) → `npm run build` ✓ 302 modules transformed → `node tests/frontend.test.cjs` ✓ 8/8 pass.

## Langkah 1 — Audit & Gap-check (hasil)

Langkah 1 dijalankan:

- Backend: `GET /api/compare?ids=` (returns `{count,hospitals[],comparison_matrix,disclaimers}`), `GET /api/hospitals/:id/alternatives` (returns `{target_rs,count,has_alternatives,message,alternatives[],disclaimer}`), `GET /api/hospitals/:id/operational-hours` (returns jam per-unit), `DELETE /api/booking/:kode` — semua ada, cukup dipanggil dari React.
- Legacy referensi: comparison_service.py (matrix + disclaimer), alternatives_service.py (target_rs/alasan_rekomendasi), legacy HTML: renderEnrichedHours (4202-4258), route texts (6093-6112), batalBooking (5555-5573), openHospitalMap (4768-4844), per-page (3862-3866, default 20), filter ctx (5941-5994).
- React sekarang: tidak mengandung compare/alternatives/jam_operasional; batal booking belum; openHospitalMap belum ada sebagai halaman sendiri.
- **Langkah 1 selesai.** Siap eksekusi **Langkah 2** (Fitur Compare + RS Alternatih) atau navigasi ke step lain?
