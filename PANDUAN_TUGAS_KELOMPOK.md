# 📋 Panduan & Pembagian Peran Pengembang CariSehat
### Tugas Besar Web Semantik (Kelompok 6 Orang)

Panduan ini dibuat agar setiap anggota kelompok dapat langsung bekerja dan mengembangkan bagian masing-masing **tanpa risiko bentrok kode (*merge conflict*)**.

---

## 🏗️ Ringkasan Status Proyek Saat Ini
Pondasi sistem sudah terpasang dan siap dikembangkan:
- ✅ **Backend API & Semantic**: FastAPI + Apache Jena Fuseki + RDF Turtle.
- ✅ **Chatbot Widget**: Deep-Chat sudah terpasang di frontend dan terhubung ke `POST /api/chat`.
- ✅ **Maps Interaktif**: Leaflet dengan GPS User (`leaflet-locatecontrol`) & Rute Jalan (`leaflet-routing-machine`).
- ✅ **Layanan DBpedia**: Modul `dbpedia_service.py` siap melakukan federated query ke linked data eksternal.

---

## 👥 Checklist Tugas Spesifik Tiap Anggota (P1 - P6)

### 👤 Anggota 1 — Semantic Web & DBpedia Integration (P1)
> **Tanggung Jawab:** Menyempurnakan ontologi dan menghubungkan data lokal dengan linked data dunia (DBpedia/Wikidata).
* **File yang Dikerjakan:**
  * `semantic/rdf/ontologi.ttl`
  * `backend/app/services/dbpedia_service.py`
  * `backend/app/templates/rs_detail.html`
* **Checklist Tugas Pengembangan:**
  1. [ ] Tambahkan properti baru di `ontologi.ttl`: `hf:menerimaBPJS` (boolean) dan `hf:fasilitas` (string/Class).
  2. [ ] Tambahkan relasi `owl:sameAs` dari Kabupaten/Kota lokal ke DBpedia URI (misal: `kk:kota-medan owl:sameAs <http://dbpedia.org/resource/Medan>`).
  3. [ ] Di `rs_detail.html`, tambahkan badge/kartu informasi eksternal DBpedia (menampilkan deskripsi kota dan populasi dari DBpedia).
* **Kontribusi Paper Jurnal:** Tulis Bab **Metodologi (Pemodelan Ontologi OWL & Integrasi Linked Data Eksternal)**.

---

### 👤 Anggota 2 — Data Enrichment & Geocoding (P2)
> **Tanggung Jawab:** Memperbaiki dataset rumah sakit yang saat ini masih minim layanan dan koordinatnya menumpuk.
* **File yang Dikerjakan:**
  * `data/rumah_sakit_sumut.csv`
  * `data/koordinat.csv`
  * `scripts/csv_ke_rdf.py`
* **Checklist Tugas Pengembangan:**
  1. [ ] **Isi Layanan Dasar Otomatis:** Perbarui `scripts/csv_ke_rdf.py` agar Rumah Sakit Umum (RSU) otomatis memiliki layanan sesuai kelas:
     * *Kelas A & B:* IGD 24 Jam, ICU, Rawat Inap, Bedah, Radiologi, Laboratorium, Spesialis.
     * *Kelas C:* IGD 24 Jam, Rawat Inap, Bedah Umum, Laboratorium.
     * *Kelas D:* IGD 24 Jam, Rawat Inap Dasar.
  2. [ ] **Perbaiki Koordinat:** Cek 65 RS di `data/koordinat.csv` yang bertanda `kabkota`. Perbaiki koordinatnya agar tidak bertumpuk di titik tengah kota.
  3. [ ] Jalankan kembali:
     ```bash
     python scripts/csv_ke_rdf.py --koordinat data/koordinat.csv
     ```
* **Kontribusi Paper Jurnal:** Tulis Bab **Metodologi (Akuisisi, Pembersihan, dan Konversi Data CSV ke RDF)**.

---

### 👤 Anggota 3 — Core Backend & Database Relasional (P3)
> **Tanggung Jawab:** Optimasi endpoint pencarian, filter multi-kriteria, dan pemanfaatan PostgreSQL.
* **File yang Dikerjakan:**
  * `backend/app/routers/api.py`
  * `backend/app/services/sparql_service.py`
  * `backend/app/database/models.py`
  * `database/schema.sql`
* **Checklist Tugas Pengembangan:**
  1. [ ] **Fitur Favorit / Bookmark:** Buat tabel baru di PostgreSQL (`user_favorite_rs`) untuk menyimpan rumah sakit favorit pengguna.
  2. [ ] Buat endpoint `POST /api/favorites` dan `GET /api/favorites`.
  3. [ ] **Optimasi Query SPARQL:** Perbaiki fungsi `build_search_query` di `sparql_service.py` agar mendukung pengurutan (Sort by: Nama A-Z, Kelas).
* **Kontribusi Paper Jurnal:** Tulis Bab **Arsitektur Sistem & Perancangan Endpoint SPARQL**.

---

### 👤 Anggota 4 — Chatbot Intelligence & NL-to-SPARQL (P4)
> **Tanggung Jawab:** Mengembangkan kecerdasan asisten chatbot agar bisa menjawab pertanyaan pengguna yang lebih bervariasi.
* **File yang Dikerjakan:**
  * `backend/app/routers/chat.py`
  * `backend/app/services/chatbot_service.py`
* **Checklist Tugas Pengembangan:**
  1. [ ] Tambahkan pengenalan kata kunci baru pada `chatbot_service.py`:
     * Deteksi pertanyaan BPJS (*"RS mana yang terima BPJS?"*).
     * Deteksi fasilitas darurat (*"RS yang punya ambulans / ICU"*).
     * Pertanyaan rumah sakit terdekat.
  2. [ ] Percantik format teks respons chat dengan Markdown list dan link langsung ke halaman semantik `/rs/{id}`.
  3. [ ] (Opsional jika ingin nilai plus maksimal): Hubungkan endpoint `/api/chat` ke Google Gemini API / OpenAI untuk natural conversation.
* **Kontribusi Paper Jurnal:** Tulis Bab **Hasil dan Pembahasan (Implementasi Chatbot Berbasis Knowledge Graph)**.

---

### 👤 Anggota 5 — Frontend UI/UX & Peta Interaktif (P5)
> **Tanggung Jawab:** Menyempurnakan tampilan antarmuka web, kartu rumah sakit, dan kontrol peta.
* **File yang Dikerjakan:**
  * `frontend/index.html`
* **Checklist Tugas Pengembangan:**
  1. [ ] **Tampilan Kartu RS:** Tambahkan tombol cepat *"Detail Semantik"* dan badge fasilitas di setiap item list sebelah kiri.
  2. [ ] **Kustomisasi Rute Peta:** Sesuaikan tampilan garis rute jalan dari `Leaflet Routing Machine` agar lebih kontras dan petunjuk arahnya dalam bahasa Indonesia.
  3. [ ] **UI Feedback:** Berikan indikator loading (spinner) saat proses pencarian atau rute sedang dihitung.
* **Kontribusi Paper Jurnal:** Tulis Bab **Hasil dan Pembahasan (Perancangan Antarmuka Web & Visualisasi Spasial)**.

---

### 👤 Anggota 6 — Lead Dokumentasi Paper Jurnal & Demo (P6)
> **Tanggung Jawab:** Mengoordinasikan penulisan Paper Jurnal ilmiah (bobot 30%) dan slide presentasi (bobot 20%).
* **File/Dokumen yang Dikerjakan:**
  * Dokumen Paper Jurnal (format template jurnal USU / IEEE)
  * Slide Deck Presentasi (PPT / Canva)
* **Checklist Tugas:**
  1. [ ] Buat kerangka paper sesuai pedoman slide 16:
     * *Abstrak*
     * *Pendahuluan*
     * *Tinjauan Pustaka & Penelitian Terdahulu*
     * *Metodologi (menggabungkan tulisan P1, P2, P3)*
     * *Hasil dan Pembahasan (menggabungkan tulisan P4, P5)*
     * *Kesimpulan & Daftar Pustaka*
  2. [ ] Ambil tangkapan layar (screenshot) fitur-fitur utama aplikasi untuk dijadikan gambar ilustrasi di paper dan slide.
  3. [ ] Susun skenario presentasi dan demo aplikasi durasi 1-3 menit sesuai ketentuan dosen.

---

## 🛠️ Panduan Git Anti-Bentrok untuk Anggota

Agar tidak terjadi tabrakan kode saat bekerja bersamaan:
1. Sebelum mulai koding, selalu tarik perubahan terbaru:
   ```bash
   git pull origin main
   ```
2. Buat branch fitur sendiri (sesuai peran):
   ```bash
   # Contoh Anggota 4:
   git checkout -b feat/chatbot-enhancement
   ```
3. Setelah selesai koding, commit dan push:
   ```bash
   git add .
   git commit -m "feat(chatbot): tambah intent bpjs dan fasilitas"
   git push origin feat/chatbot-enhancement
   ```
4. Buka Pull Request (PR) di GitHub ke branch `main`.
