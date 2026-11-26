# CariSehat

Aplikasi pencarian rumah sakit se-Sumatera Utara (Tubes MSBD + Web Semantik).
Stack: FastAPI, SQLAlchemy, PostgreSQL, Apache Jena Fuseki, Leaflet + OpenStreetMap.

## Menjalankan
```bash
copy .env.example .env        # Windows (Linux/Mac: cp)
# edit .env, isi POSTGRES_PASSWORD
docker compose up --build
```
Build pertama mengunduh Fuseki (butuh internet). Dataset contoh dimuat otomatis ke Fuseki saat backend start.

| Alamat | Isi |
|---|---|
| http://localhost:8000 | UI pencarian + peta |
| http://localhost:8000/docs | Dokumentasi API (Swagger) |
| http://localhost:8000/api/health | Cek PostgreSQL dan Fuseki |
| http://localhost:8000/rs/rs-001 | Halaman RDFa + OGP (`.rdf` / `.ttl` untuk unduhan) |
| http://localhost:8000/sparql | SPARQL playground (YASGUI) |
| http://localhost:3030 | Fuseki (UI bawaan) |
| localhost:5433 | PostgreSQL (DBeaver) |
| localhost/admin | laman admin |

Muat ulang RDF setelah mengubah file: `docker compose exec backend python -m app.services.rdf_loader --force`
Ulang skema PostgreSQL dari nol: `docker compose down -v` lalu `docker compose up`.

## Data
Sumber: `data/rumah_sakit_sumut.csv` (206 RS Sumatera Utara: nama, alamat, telepon, pemilik, kelas, jenis).
CSV tidak memuat koordinat, layanan, dan fasilitas. Alurnya:
```bash
python scripts/geocode.py                                   # cari koordinat (Nominatim/OSM), hasil: data/koordinat.csv
python scripts/csv_ke_rdf.py --koordinat data/koordinat.csv # hasil: semantic/rdf/hospitals-sumut.ttl
docker compose exec backend python -m app.services.rdf_loader --force
```
`hospitals-sumut.ttl` dibuat otomatis: jangan diedit tangan, ubah CSV/skripnya. Kelas, properti, dan ontologi ada di `semantic/rdf/ontologi.ttl`.
Website resmi dan bukti verifikasinya disimpan dalam RDF tambahan. Lihat [panduan enrichment website RS](docs/WEBSITE_RESMI_RS.md) untuk memperbarui dan menyinkronkan hasil pemeriksaan.
Layanan hanya diturunkan dari jenis RS khusus (mis. RSIA -> Anak, Bersalin); layanan RS umum dan fasilitas belum ada datanya.
Koordinat bersumber `kabkota` adalah perkiraan kasar (titik pusat wilayah), bukan lokasi RS.

## Referensi dan atribusi
- Koordinat: (c) kontributor OpenStreetMap, lisensi ODbL, lewat Nominatim.
- Dataset RS: (isi sumber asli CSV: situs/instansi dan tanggal pengambilan).

## Struktur dan pemilik file
- `backend/app/services/sparql_service.py` (P4) query SPARQL; `rdf_loader.py` (P3/P4)
- `backend/app/routers/` (P5) API dan halaman RDFa/OGP
- `backend/app/database/`, `database/schema.sql` (P2)
- `semantic/rdf/` (P3) ontologi + dataset RDF; ganti `hospitals-sample.ttl`
- `frontend/index.html` (P6)
- `docker-compose.yml`, `fuseki/` (P1)

## Aturan
Satu fitur satu branch, PR kecil, jangan commit `.env`. Namespace ontologi dan pola URI v0 dibekukan Selasa 10 Nov.
