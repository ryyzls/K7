-- Skema awal (starter). P2 (Database Engineer) memperluas: layanan, fasilitas, relasi, ulasan,
-- favorit, log_pencarian, audit_log, staging_rs, serta index/view/function/procedure/trigger.
CREATE TABLE provinsi (
  id SERIAL PRIMARY KEY,
  nama VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE kabupaten_kota (
  id SERIAL PRIMARY KEY,
  id_provinsi INT NOT NULL REFERENCES provinsi(id),
  nama VARCHAR(100) NOT NULL,
  jenis VARCHAR(10) NOT NULL CHECK (jenis IN ('Kabupaten','Kota')),
  UNIQUE (id_provinsi, nama)
);
CREATE TABLE rumah_sakit (
  id SERIAL PRIMARY KEY,
  kode_rs VARCHAR(20) NOT NULL UNIQUE,
  id_kabkota INT NOT NULL REFERENCES kabupaten_kota(id),
  nama VARCHAR(200) NOT NULL,
  jenis VARCHAR(20) NOT NULL CHECK (jenis IN ('Umum','Khusus')),
  kelas CHAR(1) CHECK (kelas IN ('A','B','C','D')),
  alamat TEXT,
  telepon VARCHAR(30),
  website VARCHAR(255),
  latitude NUMERIC(10,7) CHECK (latitude BETWEEN -90 AND 90),
  longitude NUMERIC(10,7) CHECK (longitude BETWEEN -180 AND 180),
  status VARCHAR(10) NOT NULL DEFAULT 'aktif'
);
INSERT INTO provinsi (nama) VALUES ('Sumatera Utara');

-- Tabel booking kamar rawat inap (simulasi untuk Tugas Besar)
CREATE TABLE IF NOT EXISTS booking_kamar (
  id SERIAL PRIMARY KEY,
  kode_booking VARCHAR(20) NOT NULL UNIQUE,
  kode_rs VARCHAR(20) NOT NULL,
  nama_rs VARCHAR(200) NOT NULL,
  nama_pasien VARCHAR(100) NOT NULL,
  no_telp VARCHAR(20) NOT NULL,
  tanggal_masuk DATE NOT NULL,
  tanggal_keluar DATE,
  jenis_kamar VARCHAR(30) NOT NULL CHECK (jenis_kamar IN ('VIP','Kelas I','Kelas II','Kelas III','ICU')),
  catatan TEXT,
  status VARCHAR(15) NOT NULL DEFAULT 'menunggu' CHECK (status IN ('menunggu','dikonfirmasi','dibatalkan')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_booking_kode_rs ON booking_kamar(kode_rs);
CREATE INDEX IF NOT EXISTS idx_booking_status ON booking_kamar(status);
