# CariSehat Chatbot — Actual Conversation Samples

## Multi-Turn Conversations (Skenario 1–4)

### Skenario 1: Filter bertahap

- **K1-T1** (`FAIL`, 177.16 ms) — **User:** `Carikan rumah sakit di Medan.`
  - *Issue:* hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"carikan medan"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fasilitas dan BPJS dari data lama belum terverifikasi. Sumber dan tanggal tersedia pa

- **K1-T2** (`PASS`, 124.39 ms) — **User:** `Yang kelas B aja.`
  - **Bot:** Berikut 14 rumah sakit yang sesuai dengan pencarian Anda:  1. **RS Bhayangkara Tingkat II Medan** • ✅ BPJS    📍 Kota Medan – Kelas B (Umum)    🏠 JL KH Wahid Hasyim No 1    📞 0821-7997-604    🩺 Layanan: CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping)    🔗 [Lihat Detail](/rumah-sakit/rs-003)  2. **RS Columbia Asia Aksara** • ✅ BPJS    📍 Kota Medan – Kelas B (Umum)    🏠 Jl. Letda Sujono, LK.X No. 90    📞 061-88806888    🩺 Layanan: Ekokardiografi, Elektromedik diagnostik

- **K1-T3** (`PASS`, 46.01 ms) — **User:** `Yang punya ICU.`
  - **Bot:** Berikut 11 rumah sakit yang sesuai dengan pencarian Anda:  1. **RS Bhayangkara Tingkat II Medan** • ✅ BPJS    📍 Kota Medan – Kelas B (Umum)    🏠 JL KH Wahid Hasyim No 1    📞 0821-7997-604    🩺 Layanan: CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping)    🔗 [Lihat Detail](/rumah-sakit/rs-003)  2. **RS Columbia Asia Aksara** • ✅ BPJS    📍 Kota Medan – Kelas B (Umum)    🏠 Jl. Letda Sujono, LK.X No. 90    📞 061-88806888    🩺 Layanan: Ekokardiografi, Elektromedik diagnostik

- **K1-T4** (`FAIL`, 231.23 ms) — **User:** `Ada yang punya layanan jantung?`
  - *Issue:* hospitals=0 < 1
  - **Bot:** Maaf, belum menemukan rumah sakit yang memenuhi kombinasi kriteria **wilayah Kota Medan, Kelas B, layanan Penyakit Dalam, fasilitas ICU** di database kami (tidak ada data yang cocok / belum ditemukan).  Silakan coba memperluas pencarian dengan menghilangkan salah satu filter atau mencari di wilayah terdekat.  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fasilitas dan BPJS dari data lama belum terverifikasi

- **K1-T5** (`PASS`, 87.96 ms) — **User:** `Tampilkan tiga saja.`
  - **Bot:** ### 🏥 RS Tiga Bersaudara **Kelas:** D | **Jenis:** Umum | **BPJS:** ✅ Menerima BPJS Kesehatan **Kepemilikan / Pengelola:** Perorangan **Wilayah:** Kab. Labuhan Batu Utara **Alamat:** Jl. Lintas Sumatera **Nomor Telepon:** 081260142618  🩺 **Layanan terlapor SIRS (3), belum diverifikasi operasional:** Laboratorium mikrobiologi, Patologi Klinik, Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu  🏢 **Fasilitas Penunjang (5):** Ambulans, Instalasi Farmasi, Instalasi Gawat Darurat, Laboratorium Da

### Skenario 2: Follow-up detail RS

- **K2-T1** (`FAIL`, 99.8 ms) — **User:** `Saya mau cari RS Hermina Medan.`
  - *Issue:* expected rs-125 not in []
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"saya mau hermina medan"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fasilitas dan BPJS dari data lama belum terverifikasi. Sumber dan tanggal te

- **K2-T2** (`FAIL`, 13.57 ms) — **User:** `Apa saja fasilitasnya?`
  - *Issue:* expected rs-125 not in []; missing any of ['fasilitas', 'icu']
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **K2-T3** (`FAIL`, 101.95 ms) — **User:** `Jam bukanya?`
  - *Issue:* expected rs-125 not in []; missing any of ['jam', 'buka', 'igd', '24']
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **K2-T4** (`FAIL`, 162.96 ms) — **User:** `Nomor teleponnya berapa?`
  - *Issue:* expected rs-125 not in []; missing any of ['telepon', '061']
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **K2-T5** (`FAIL`, 96.78 ms) — **User:** `Bisa tampilkan alternatifnya?`
  - *Issue:* missing any of ['alternatif', 'serupa', 'hermina']
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

### Skenario 3: Compare follow-up

- **K3-T1** (`FAIL`, 147.22 ms) — **User:** `Bandingkan Adam Malik dan Columbia Asia Medan.`
  - *Issue:* expected rs-171 not in []; expected rs-008 not in []
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **K3-T2** (`PASS`, 598.12 ms) — **User:** `Yang pertama punya CT Scan?`
  - **Bot:** Berikut 56 rumah sakit yang sesuai dengan pencarian Anda:  1. **RS AL Dr. Komang Makes Belawan** • ✅ BPJS    📍 Kota Medan – Kelas C (Umum)    🏠 Jl. Bengkalis No.1 Belawan    📞 061-6941741    🩺 Layanan: CT Scan, Patologi Klinik, Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu    🔗 [Lihat Detail](/rumah-sakit/rs-002)  2. **RS Bhayangkara Tingkat II Medan** • ✅ BPJS    📍 Kota Medan – Kelas B (Umum)    🏠 JL KH Wahid Hasyim No 1    📞 0821-7997-604    🩺 Layanan: CT Scan, Ekokardiografi, Elektrom

- **K3-T3** (`PASS`, 535.93 ms) — **User:** `Kalau yang kedua?`
  - **Bot:** Berikut 56 rumah sakit yang sesuai dengan pencarian Anda:  1. **RS AL Dr. Komang Makes Belawan** • ✅ BPJS    📍 Kota Medan – Kelas C (Umum)    🏠 Jl. Bengkalis No.1 Belawan    📞 061-6941741    🩺 Layanan: CT Scan, Patologi Klinik, Pelayanan Gawat Darurat Umum 24 jam & 7 hari seminggu    🔗 [Lihat Detail](/rumah-sakit/rs-002)  2. **RS Bhayangkara Tingkat II Medan** • ✅ BPJS    📍 Kota Medan – Kelas B (Umum)    🏠 JL KH Wahid Hasyim No 1    📞 0821-7997-604    🩺 Layanan: CT Scan, Ekokardiografi, Elektrom

- **K3-T4** (`PASS`, 1511.26 ms) — **User:** `Mana yang memiliki layanan jantung?`
  - **Bot:** Maaf, belum menemukan rumah sakit yang memenuhi kombinasi kriteria **layanan Penyakit Dalam** di database kami (tidak ada data yang cocok / belum ditemukan).  Silakan coba memperluas pencarian dengan menghilangkan salah satu filter atau mencari di wilayah terdekat.  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fasilitas dan BPJS dari data lama belum terverifikasi. Sumber dan tanggal tersedia pada halaman d

### Skenario 4: Koreksi konteks

- **K4-T1** (`FAIL`, 199.44 ms) — **User:** `Carikan rumah sakit di Medan.`
  - *Issue:* hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"carikan medan"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fasilitas dan BPJS dari data lama belum terverifikasi. Sumber dan tanggal tersedia pa

- **K4-T2** (`PASS`, 136.64 ms) — **User:** `Eh, maksud saya di Siantar.`
  - **Bot:** Berikut 10 rumah sakit yang sesuai dengan pencarian Anda:  1. **RS Efarina Etaham Pematang Siantar** • ✅ BPJS    📍 Kota Pematang Siantar – Kelas B (Umum)    🏠 Jalan Pdt J Wismar Saragih No 1    📞 085261163933    🩺 Layanan: CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping)    🔗 [Lihat Detail](/rumah-sakit/rs-011)  2. **RS Mata Siantar** • ✅ BPJS    📍 Kota Pematang Siantar – Kelas C (Khusus)    🏠 Jl. Kartini Nomor 18    📞 62225559    🩺 Layanan: Pelayanan Gawat Darurat Um

- **K4-T3** (`PASS`, 50.69 ms) — **User:** `Yang punya ICU.`
  - **Bot:** Berikut 7 rumah sakit yang sesuai dengan pencarian Anda:  1. **RS Efarina Etaham Pematang Siantar** • ✅ BPJS    📍 Kota Pematang Siantar – Kelas B (Umum)    🏠 Jalan Pdt J Wismar Saragih No 1    📞 085261163933    🩺 Layanan: CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping)    🔗 [Lihat Detail](/rumah-sakit/rs-011)  2. **RS Murni Teguh Horas Insani** • ✅ BPJS    📍 Kota Pematang Siantar – Kelas C (Umum)    🏠 Jl. Medan KM 2.5    📞 08116829705    🩺 Layanan: CT Scan, Ekokardio

- **K4-T4** (`FAIL`, 462.27 ms) — **User:** `Ganti jadi NICU.`
  - *Issue:* wrong kabkota ['Kota Medan', 'Kota Medan']
  - **Bot:** Berikut 2 rumah sakit yang sesuai dengan pencarian Anda:  1. **RS Umum Murni Teguh Memorial Hospital**    📍 Kota Medan – Kelas A (Umum)    🏠 Jalan Jawa Nomor 2    📞 061-80501888    🩺 Layanan: BERA (Brain Evoke Response Audimetri), CT Scan, Ekokardiografi    🔗 [Lihat Detail](/rumah-sakit/rs-157)  2. **RS Umum Pusat H. Adam Malik** • ✅ BPJS    📍 Kota Medan – Kelas A (Umum)    🏠 Jl Bunga Lau No. 17    📞 061-8363000    🩺 Layanan: CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Ma

## Selected Single-Turn Examples (Good & Failed)

- **A07 [A. Percakapan Dasar]** (`FAIL`, 181.19 ms) — **User:** `Sampai jumpa.`
  - *Issue:* intent=OUT_OF_SCOPE not in ['GREETING']
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **B01 [B. Nama RS]** (`PASS`, 89.8 ms) — **User:** `Cari RS Adam Malik.`
  - **Bot:** ### 🏥 RS Umum Pusat H. Adam Malik **Kelas:** A | **Jenis:** Umum | **BPJS:** ✅ Menerima BPJS Kesehatan **Kepemilikan / Pengelola:** Kemkes **Wilayah:** Kota Medan **Alamat:** Jl Bunga Lau No. 17 **Nomor Telepon:** 0618363000  🩺 **Layanan terlapor SIRS (19), belum diverifikasi operasional:** CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping), Laboratorium mikrobiologi, Mik

- **B03 [B. Nama RS]** (`FAIL`, 86.22 ms) — **User:** `Tampilkan RS Vita Insani.`
  - *Issue:* expected rs-200 not in ['rs-199']
  - **Bot:** ### 🏥 RS Umum Vita Insani **Kelas:** B | **Jenis:** Umum | **BPJS:** ✅ Menerima BPJS Kesehatan **Kepemilikan / Pengelola:** Perusahaan **Wilayah:** Kota Pematang Siantar **Alamat:** JL.MERDEKA NO 329 **Nomor Telepon:** 62811601125  🩺 **Layanan terlapor SIRS (31), belum diverifikasi operasional:** CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping), Faal Paru Klinik, Labora

- **B04 [B. Nama RS]** (`FAIL`, 96.07 ms) — **User:** `Saya mau cari rumah sakit Murni Teguh.`
  - *Issue:* intent=NOT_FOUND not in ['DETAIL']; expected rs-157 not in []
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"saya mau murni teguh"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang be

- **C01 [C. Typo & Informal]** (`FAIL`, 104.35 ms) — **User:** `Adam Malk.`
  - *Issue:* intent=OUT_OF_SCOPE not in ['DETAIL']; expected rs-171 not in []
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **C02 [C. Typo & Informal]** (`FAIL`, 176.28 ms) — **User:** `Jantng.`
  - *Issue:* intent=OUT_OF_SCOPE not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **C03 [C. Typo & Informal]** (`FAIL`, 91.95 ms) — **User:** `Medn.`
  - *Issue:* intent=OUT_OF_SCOPE not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **C08 [C. Typo & Informal]** (`PASS`, 165.78 ms) — **User:** `RSHAM.`
  - **Bot:** ### 🏥 RS Umum Pusat H. Adam Malik **Kelas:** A | **Jenis:** Umum | **BPJS:** ✅ Menerima BPJS Kesehatan **Kepemilikan / Pengelola:** Kemkes **Wilayah:** Kota Medan **Alamat:** Jl Bunga Lau No. 17 **Nomor Telepon:** 0618363000  🩺 **Layanan terlapor SIRS (19), belum diverifikasi operasional:** CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping), Laboratorium mikrobiologi, Mik

- **C09 [C. Typo & Informal]** (`FAIL`, 101.26 ms) — **User:** `Ada rs yg punya dokter jantung ga?`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"yg dokter jantung ga"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang be

- **C10 [C. Typo & Informal]** (`FAIL`, 177.92 ms) — **User:** `Carikan rs yg ada fasilitas cuci darah dong.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"carikan yg cuci darah"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang b

- **C11 [C. Typo & Informal]** (`FAIL`, 184.97 ms) — **User:** `Rs di siantar yg buka hari sabtu apa aja?`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"siantar yg buka hari sabtu aja"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klin

- **D04 [D. Lokasi]** (`FAIL`, 172.95 ms) — **User:** `Rumah sakit di Medan Johor.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"medan johor"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direv

- **E01 [E. Layanan]** (`FAIL`, 1465.89 ms) — **User:** `Rumah sakit dengan layanan jantung.`
  - *Issue:* hospitals=0 < 1
  - **Bot:** Semoga lekas pulih dan sehat kembali.  Maaf, belum menemukan rumah sakit yang memenuhi kombinasi kriteria **layanan Penyakit Dalam** di database kami (tidak ada data yang cocok / belum ditemukan).  Silakan coba memperluas pencarian dengan menghilangkan salah satu filter atau mencari di wilayah terdekat.  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. 

- **E03 [E. Layanan]** (`FAIL`, 172.13 ms) — **User:** `Rumah sakit untuk pemeriksaan mata.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"untuk pemeriksaan mata"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang 

- **E04 [E. Layanan]** (`FAIL`, 133.02 ms) — **User:** `Rumah sakit dengan layanan kesehatan anak.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"kesehatan anak"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum di

- **E05 [E. Layanan]** (`FAIL`, 1432.35 ms) — **User:** `Rumah sakit dengan poli kandungan.`
  - *Issue:* hospitals=0 < 1
  - **Bot:** Semoga lekas pulih dan sehat kembali.  Maaf, belum menemukan rumah sakit yang memenuhi kombinasi kriteria **layanan Kebidanan dan Kandungan** di database kami (tidak ada data yang cocok / belum ditemukan).  Silakan coba memperluas pencarian dengan menghilangkan salah satu filter atau mencari di wilayah terdekat.  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan s

- **E06 [E. Layanan]** (`FAIL`, 119.44 ms) — **User:** `Rumah sakit yang menyediakan hemodialisis.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"menyediakan hemodialisis"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yan

- **E07 [E. Layanan]** (`FAIL`, 91.22 ms) — **User:** `Rumah sakit yang bisa cuci darah.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"bisa cuci darah"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum d

- **E08 [E. Layanan]** (`FAIL`, 121.63 ms) — **User:** `Rumah sakit dengan layanan pencitraan medis.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"pencitraan medis"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum 

- **E09 [E. Layanan]** (`FAIL`, 131.27 ms) — **User:** `Rumah sakit dengan layanan ortopedi.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"ortopedi"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview

- **F01 [F. Fasilitas]** (`FAIL`, 130.16 ms) — **User:** `Rumah sakit yang memiliki ICU.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"memiliki"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview

- **F02 [F. Fasilitas]** (`FAIL`, 140.33 ms) — **User:** `Rumah sakit yang memiliki NICU.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"memiliki nicu"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum dir

- **F03 [F. Fasilitas]** (`FAIL`, 134.25 ms) — **User:** `Rumah sakit yang memiliki PICU.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"memiliki picu"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum dir

- **F07 [F. Fasilitas]** (`FAIL`, 1407.51 ms) — **User:** `Rumah sakit yang punya laboratorium.`
  - *Issue:* hospitals=0 < 1
  - **Bot:** Semoga lekas pulih dan sehat kembali.  Maaf, belum menemukan rumah sakit yang memenuhi kombinasi kriteria **layanan Laboratorium, fasilitas Laboratorium** di database kami (tidak ada data yang cocok / belum ditemukan).  Silakan coba memperluas pencarian dengan menghilangkan salah satu filter atau mencari di wilayah terdekat.  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau k

- **F08 [F. Fasilitas]** (`FAIL`, 94.15 ms) — **User:** `Rumah sakit dengan ICU dan ventilator.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"dan ventilator"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum di

- **G01 [G. Kompleks]** (`PASS`, 59.37 ms) — **User:** `Rumah sakit kelas B di Medan yang punya ICU.`
  - **Bot:** Semoga lekas pulih dan sehat kembali.  Berikut 11 rumah sakit yang sesuai dengan pencarian Anda:  1. **RS Bhayangkara Tingkat II Medan** • ✅ BPJS    📍 Kota Medan – Kelas B (Umum)    🏠 JL KH Wahid Hasyim No 1    📞 0821-7997-604    🩺 Layanan: CT Scan, Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain Mapping)    🔗 [Lihat Detail](/rumah-sakit/rs-003)  2. **RS Columbia Asia Aksara** • ✅ BPJS 

- **G02 [G. Kompleks]** (`FAIL`, 194.47 ms) — **User:** `Rumah sakit swasta di Siantar yang memiliki layanan jantung.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"swasta siantar memiliki jantung"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label kli

- **G03 [G. Kompleks]** (`FAIL`, 132.57 ms) — **User:** `Rumah sakit pemerintah di Medan dengan IGD 24 jam.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"pemerintah medan igd 24 jam"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis 

- **G04 [G. Kompleks]** (`FAIL`, 95.47 ms) — **User:** `Rumah sakit yang punya ICU dan NICU.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"dan nicu"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview

- **G05 [G. Kompleks]** (`FAIL`, 176.39 ms) — **User:** `Rumah sakit dengan layanan jantung atau saraf di Medan.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"jantung atau saraf medan"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yan

- **G06 [G. Kompleks]** (`FAIL`, 96.59 ms) — **User:** `Rumah sakit kelas A atau B yang memiliki CT Scan.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"a atau b memiliki ct scan"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis ya

- **G07 [G. Kompleks]** (`FAIL`, 181.13 ms) — **User:** `Rumah sakit di Medan selain Adam Malik.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"medan selain adam malik"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang

- **G08 [G. Kompleks]** (`FAIL`, 175.46 ms) — **User:** `Rumah sakit di Medan yang punya ICU, CT Scan, dan layanan jantung.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"medan ct scan dan jantung"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis ya

- **G09 [G. Kompleks]** (`FAIL`, 188.61 ms) — **User:** `Rumah sakit di Siantar yang memiliki poli anak dan buka hari Sabtu.`
  - *Issue:* intent=NOT_FOUND not in ['SEARCH_FILTER']; hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"siantar memiliki anak dan buka hari sabtu"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini.

- **H02 [H. Detail Atribut]** (`FAIL`, 180.19 ms) — **User:** `Berapa nomor telepon RS Adam Malik?`
  - *Issue:* intent=NOT_FOUND not in ['ATRIBUT']; expected rs-171 not in []; missing any of ['telepon', '061']
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"berapa adam malik"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum

- **H03 [H. Detail Atribut]** (`FAIL`, 169.8 ms) — **User:** `Apa website resmi RS Vita Insani?`
  - *Issue:* intent=NOT_FOUND not in ['ATRIBUT', 'DETAIL']; expected rs-200 not in []
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"website resmi vita insani"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis ya

- **H04 [H. Detail Atribut]** (`FAIL`, 174.69 ms) — **User:** `Apa email RS Hermina Medan?`
  - *Issue:* intent=NOT_FOUND not in ['ATRIBUT', 'DETAIL']; expected rs-125 not in []; missing any of ['@']
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"email hermina medan"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang bel

- **H06 [H. Detail Atribut]** (`FAIL`, 116.67 ms) — **User:** `Apa saja spesialisasi RS Vita Insani?`
  - *Issue:* intent=NOT_FOUND not in ['ATRIBUT']; expected rs-200 not in []
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"spesialisasi vita insani"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yan

- **H07 [H. Detail Atribut]** (`FAIL`, 180.16 ms) — **User:** `Siapa direktur RS Adam Malik?`
  - *Issue:* intent=NOT_FOUND not in ['ATRIBUT', 'DETAIL']; expected rs-171 not in []
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"siapa direktur adam malik"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis ya

- **H09 [H. Detail Atribut]** (`FAIL`, 88.67 ms) — **User:** `Apakah RS Vita Insani punya ICU?`
  - *Issue:* expected rs-200 not in ['rs-199']
  - **Bot:** ✅ Ya, **RS Umum Vita Insani** memiliki fasilitas perawatan intensif: **ICU / ICCU**.  Untuk profil lengkap faskes ini, Anda dapat membuka [Detail RS Umum Vita Insani](/rumah-sakit/rs-199).  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fasilitas dan BPJS dari data lama belum terverifikasi. Sumber dan tanggal 

- **H10 [H. Detail Atribut]** (`FAIL`, 99.17 ms) — **User:** `Jam berapa poliklinik RS Vita Insani buka?`
  - *Issue:* intent=NOT_FOUND not in ['ATRIBUT']; expected rs-200 not in []
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"jam berapa poliklinik vita insani buka"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. La

- **I02 [I. Jam Operasional]** (`FAIL`, 86.26 ms) — **User:** `Rumah sakit dengan IGD 24 jam.`
  - *Issue:* hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"igd 24 jam"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direvi

- **I05 [I. Jam Operasional]** (`FAIL`, 96.47 ms) — **User:** `Apakah RS Adam Malik buka sekarang?`
  - *Issue:* expected rs-171 not in []
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"adam malik buka sekarang"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yan

- **I06 [I. Jam Operasional]** (`FAIL`, 99.83 ms) — **User:** `Jam berapa pendaftaran pasien ditutup?`
  - *Issue:* missing any of ['pendaftaran', 'jadwal', 'jam', 'belum tersedia']
  - **Bot:** Tentu, saya siap membantu menemukan rumah sakit yang sesuai! 🏥  Agar pencarian lebih akurat, bisakah Anda menyebutkan: - **Wilayah/kota** yang diinginkan? (mis: Kota Medan, Kab. Deli Serdang) - **Kelas RS** (A/B/C/D) atau jenis layanan tertentu? - Atau gunakan opsi cepat di bawah ini:  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang b

- **J01 [J. Rekomendasi & Compare]** (`FAIL`, 115.54 ms) — **User:** `Rekomendasikan rumah sakit dengan layanan jantung di Medan.`
  - *Issue:* hospitals=0 < 1
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"rekomendasikan jantung medan"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis

- **J03 [J. Rekomendasi & Compare]** (`PASS`, 427.86 ms) — **User:** `Bandingkan RS Hermina Medan dengan Columbia Asia Medan.`
  - **Bot:** ### 📊 Perbandingan Rumah Sakit  | Atribut | RS Umum Hermina Medan | RS Columbia Asia Medan | |---|---|---| | Nama Rumah Sakit | RS Umum Hermina Medan | RS Columbia Asia Medan | | Kelas Perizinan | C | B | | Jenis Rumah Sakit | Umum | Umum | | Wilayah (Kab/Kota) | Kota Medan | Kota Medan | | Menerima BPJS | Ya ✅ | Ya ✅ | | Layanan Unggulan | CT Scan, Elektromedik diagnostik (EKG/EEG/EEG Brain Mappi

- **J06 [J. Rekomendasi & Compare]** (`FAIL`, 192.44 ms) — **User:** `Carikan rumah sakit yang sesuai dengan kebutuhan saya.`
  - *Issue:* intent=NOT_FOUND not in ['KLARIFIKASI']
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"carikan sesuai kebutuhan saya"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klini

- **L01 [L. Ambigu]** (`FAIL`, 183.28 ms) — **User:** `Carikan rumah sakit yang bagus.`
  - *Issue:* intent=NOT_FOUND not in ['RATING_INQUIRY', 'KLARIFIKASI']
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"carikan bagus"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum dir

- **L04 [L. Ambigu]** (`FAIL`, 158.82 ms) — **User:** `Rumah sakit yang murah.`
  - *Issue:* intent=NOT_FOUND not in ['KLARIFIKASI', 'RATING_INQUIRY']
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"murah"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **RS Umum Mitra Sehat** (Kab. Deli Serdang) 2. **Og Hospital** (Kota Binjai) 3. **RS AL Dr. Komang Makes Belawan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan

- **L05 [L. Ambigu]** (`FAIL`, 160.2 ms) — **User:** `Rumah sakit terbaik.`
  - *Issue:* intent=NOT_FOUND not in ['RATING_INQUIRY', 'KLARIFIKASI']
  - **Bot:** Mohon maaf, rumah sakit dengan nama **"terbaik"** tidak ditemukan di database kami.  Apakah maksud Anda salah satu rumah sakit berikut? 1. **Og Hospital** (Kota Binjai) 2. **RS AL Dr. Komang Makes Belawan** (Kota Medan) 3. **RS Bhayangkara Tingkat II Medan** (Kota Medan)  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview 

- **L07 [L. Ambigu]** (`FAIL`, 87.66 ms) — **User:** `Rumah sakit yang buka.`
  - *Issue:* intent=ATRIBUT not in ['KLARIFIKASI', 'JAM_BUKA_INQUIRY']
  - **Bot:** Semoga lekas pulih dan sehat kembali.  Jadwal poliklinik **RS Umum Mitra Guray Petumbukan** belum tersedia. Hubungi rumah sakit untuk konfirmasi.  Untuk profil lengkap faskes ini, Anda dapat membuka [Detail RS Umum Mitra Guray Petumbukan](/rumah-sakit/rs-149).  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fa

- **L08 [L. Ambigu]** (`FAIL`, 103.18 ms) — **User:** `Saya mau ke Hermina.`
  - *Issue:* intent=OUT_OF_SCOPE not in ['DETAIL', 'DISAMBIGUASI']; missing any of ['hermina']
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **M01 [M. Kesehatan & Keselamatan]** (`FAIL`, 119.32 ms) — **User:** `Saya sakit kepala, harus ke mana?`
  - *Issue:* missing any of ['dokter', 'rumah sakit', 'saraf', 'wilayah', 'medis']
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **M02 [M. Kesehatan & Keselamatan]** (`FAIL`, 101.51 ms) — **User:** `Saya batuk dan demam.`
  - *Issue:* missing any of ['dokter', 'rumah sakit', 'paru', 'penyakit dalam', 'wilayah', 'medis']
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.

- **M03 [M. Kesehatan & Keselamatan]** (`FAIL`, 1525.95 ms) — **User:** `Saya mengalami nyeri dada dan sesak napas.`
  - *Issue:* is_emergency=False != True; missing any of ['119', 'ugd', 'igd', 'darurat']
  - **Bot:** Semoga lekas pulih dan sehat kembali.  Maaf, belum menemukan rumah sakit yang memenuhi kombinasi kriteria **layanan Pulmonologi dan Kedokteran Respirasi** di database kami (tidak ada data yang cocok / belum ditemukan).  Silakan coba memperluas pencarian dengan menghilangkan salah satu filter atau mencari di wilayah terdekat.  Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau k

- **N01 [N. Out-of-Scope & Fallback]** (`FAIL`, 166.52 ms) — **User:** `Rumah sakit di Jakarta.`
  - *Issue:* missing any of ['sumatera utara', 'maaf', 'hanya', 'tidak']
  - **Bot:** Semoga lekas pulih dan sehat kembali.  ### 🏥 RS Columbia Asia Aksara **Kelas:** B | **Jenis:** Umum | **BPJS:** ✅ Menerima BPJS Kesehatan **Kepemilikan / Pengelola:** Perusahaan **Wilayah:** Kota Medan **Alamat:** Jl. Letda Sujono, LK.X No. 90 **Nomor Telepon:** 06188806888  🩺 **Layanan terlapor SIRS (12), belum diverifikasi operasional:** Ekokardiografi, Elektromedik diagnostik (EKG/EEG/EEG Brain

- **N07 [N. Out-of-Scope & Fallback]** (`PASS`, 189.53 ms) — **User:** `Berapa harga Bitcoin?`
  - **Bot:** Mohon maaf, saat ini saya hanya dapat membantu memberikan informasi yang berkaitan dengan layanan website ini.
