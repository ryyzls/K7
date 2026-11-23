-- ============================================================================
-- 004_poliklinik_pasien_ulasan.up.sql (CariSehat - Tubes MSBD)
-- Ekstensi fitur:
--   1. Akun Pasien (users, user_sessions)
--   2. Master Poliklinik (3NF) + Backfill dari jadwal_konsultasi
--   3. Nomor Antrean Atomik (SEQUENCE + Stored Function + Stored Procedure)
--   4. Favorit RS (Many-to-Many User <-> RS RDF)
--   5. Rating & Ulasan RS + Moderasi Admin
--   6. Analytical Views (CTE, GROUP BY, HAVING, RANK, DENSE_RANK)
-- ============================================================================

-- ---------------------------------------------------------------------------
-- A. Akun & Sesi Pengguna Publik (Pasien)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id            SERIAL PRIMARY KEY,
  username      VARCHAR(50)  NOT NULL UNIQUE CHECK (username ~ '^[A-Za-z0-9_.-]{3,50}$'),
  email         VARCHAR(120) NOT NULL UNIQUE CHECK (position('@' IN email) > 1),
  password_hash TEXT         NOT NULL,
  nama_lengkap  VARCHAR(100) NOT NULL,
  no_telp       VARCHAR(20),
  aktif         BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_sessions (
  token_hash CHAR(64)    PRIMARY KEY,
  user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions (user_id);

-- ---------------------------------------------------------------------------
-- B. Master Poliklinik (Normalisasi 3NF dari jadwal_konsultasi)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS poliklinik (
  id              SERIAL PRIMARY KEY,
  rs_id           VARCHAR(20)  NOT NULL, -- Kunci federasi ke Apache Jena Fuseki (RDF)
  kode_poli       VARCHAR(24)  NOT NULL,
  nama_poli       VARCHAR(100) NOT NULL,
  spesialisasi    VARCHAR(80)  NOT NULL,
  lokasi_ruangan  VARCHAR(100),
  jam_operasional VARCHAR(60)  DEFAULT 'Senin-Sabtu, 08:00-15:00 WIB',
  kuota_harian    INTEGER      NOT NULL DEFAULT 30 CHECK (kuota_harian BETWEEN 0 AND 1000),
  aktif           BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  UNIQUE (rs_id, kode_poli),
  UNIQUE (rs_id, spesialisasi)
);

-- Partial index untuk pencarian poliklinik aktif pada RS tertentu
CREATE INDEX IF NOT EXISTS idx_poliklinik_rs_aktif
  ON poliklinik (rs_id, spesialisasi) WHERE aktif = TRUE;

-- Hubungkan jadwal_konsultasi ke master poliklinik
ALTER TABLE jadwal_konsultasi
  ADD COLUMN IF NOT EXISTS poliklinik_id INTEGER REFERENCES poliklinik(id) ON DELETE RESTRICT;

-- Backfill otomatis: bentuk unit poliklinik dari kombinasi (rs_id, spesialisasi) yang sudah ada
INSERT INTO poliklinik (rs_id, kode_poli, nama_poli, spesialisasi)
SELECT DISTINCT
  j.rs_id,
  'POL-' || upper(substr(md5(j.spesialisasi), 1, 6)),
  'Poliklinik ' || j.spesialisasi,
  j.spesialisasi
FROM jadwal_konsultasi j
WHERE j.spesialisasi IS NOT NULL
ON CONFLICT (rs_id, spesialisasi) DO NOTHING;

UPDATE jadwal_konsultasi j
SET poliklinik_id = p.id
FROM poliklinik p
WHERE j.rs_id = p.rs_id
  AND lower(trim(j.spesialisasi)) = lower(trim(p.spesialisasi))
  AND j.poliklinik_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_jadwal_poliklinik ON jadwal_konsultasi (poliklinik_id, hari);

-- ---------------------------------------------------------------------------
-- C. Integrasi Akun & Nomor Antrean pada Transaksi Booking/Reservasi
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_tiket_poliklinik START WITH 1001 INCREMENT BY 1;

ALTER TABLE booking_kamar
  ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_booking_user ON booking_kamar (user_id, created_at DESC);

ALTER TABLE reservasi_konsultasi
  ADD COLUMN IF NOT EXISTS user_id       INTEGER REFERENCES users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS nomor_antrean INTEGER,
  ADD COLUMN IF NOT EXISTS kode_tiket    VARCHAR(32) UNIQUE;

CREATE INDEX IF NOT EXISTS idx_reservasi_user ON reservasi_konsultasi (user_id, tanggal DESC);
CREATE INDEX IF NOT EXISTS idx_reservasi_jadwal_tgl_status
  ON reservasi_konsultasi (jadwal_id, tanggal, status);

-- Constraint anti-nomor antrean ganda pada sesi dokter & tanggal yang sama
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_reservasi_nomor_antrean') THEN
    ALTER TABLE reservasi_konsultasi
      ADD CONSTRAINT uq_reservasi_nomor_antrean UNIQUE (jadwal_id, tanggal, nomor_antrean);
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- D. Favorit RS & Ulasan/Rating RS (Terkait Akun Pengguna)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS favorit_rs (
  user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  rs_id      VARCHAR(20) NOT NULL,
  catatan    VARCHAR(200),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, rs_id)
);
CREATE INDEX IF NOT EXISTS idx_favorit_rs_id ON favorit_rs (rs_id);

CREATE TABLE IF NOT EXISTS ulasan_rs (
  id              SERIAL PRIMARY KEY,
  user_id         INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  rs_id           VARCHAR(20) NOT NULL,
  rating          SMALLINT    NOT NULL CHECK (rating BETWEEN 1 AND 5),
  komentar        TEXT        NOT NULL CHECK (char_length(trim(komentar)) >= 5),
  status_moderasi VARCHAR(20) NOT NULL DEFAULT 'disetujui'
                  CHECK (status_moderasi IN ('menunggu', 'disetujui', 'ditolak')),
  dimoderasi_oleh VARCHAR(50),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, rs_id)
);
CREATE INDEX IF NOT EXISTS idx_ulasan_rs_moderasi ON ulasan_rs (rs_id, status_moderasi, created_at DESC);

-- ---------------------------------------------------------------------------
-- E. Penambahan Permission RBAC Admin
-- ---------------------------------------------------------------------------
INSERT INTO role_permissions (role_kode, permission) VALUES
  ('superadmin', 'poliklinik.read'), ('superadmin', 'poliklinik.write'), ('superadmin', 'ulasan.moderate'),
  ('operator',   'poliklinik.read'), ('operator',   'poliklinik.write'), ('operator',   'ulasan.moderate'),
  ('viewer',     'poliklinik.read')
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- F. Stored Function & Stored Procedure (ACID + Concurrency + Nomor Antrean)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_buat_reservasi_poliklinik(
  p_kode    text,
  p_jadwal  integer,
  p_user_id integer,
  p_pasien  text,
  p_telp    text,
  p_tanggal date,
  p_keluhan text,
  p_idem    text
) RETURNS TABLE(reservasi_id integer, nomor_antrean integer, kode_tiket text)
LANGUAGE plpgsql AS $$
DECLARE
  j           jadwal_konsultasi%ROWTYPE;
  p           poliklinik%ROWTYPE;
  v_id        integer;
  v_antrean   integer;
  v_tiket     text;
  v_terisi_h  integer;
  v_sekarang  timestamp := (now() AT TIME ZONE 'Asia/Jakarta');
BEGIN
  -- Kunci transaksi per (jadwal, tanggal) agar nomor antrean & kuota 100% atomik
  PERFORM pg_advisory_xact_lock(hashtextextended('poli_antrean:' || p_jadwal || ':' || p_tanggal, 0));

  SELECT * INTO j FROM jadwal_konsultasi WHERE id = p_jadwal AND aktif;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Jadwal dokter tidak ditemukan atau sedang nonaktif' USING ERRCODE = 'CS404';
  END IF;

  IF j.poliklinik_id IS NOT NULL THEN
    SELECT * INTO p FROM poliklinik WHERE id = j.poliklinik_id;
    IF FOUND AND NOT p.aktif THEN
      RAISE EXCEPTION 'Unit poliklinik sedang ditutup sementara' USING ERRCODE = 'CS422';
    END IF;
  END IF;

  IF EXTRACT(ISODOW FROM p_tanggal)::integer <> j.hari THEN
    RAISE EXCEPTION 'Tanggal kunjungan tidak sesuai hari praktik dokter' USING ERRCODE = 'CS422';
  END IF;

  IF p_tanggal < v_sekarang::date OR (p_tanggal = v_sekarang::date AND v_sekarang::time >= j.jam_selesai) THEN
    RAISE EXCEPTION 'Sesi praktik sudah berakhir atau tanggal sudah lewat' USING ERRCODE = 'CS422';
  END IF;

  -- Cek kuota sesi dokter
  IF fn_sisa_kuota_konsultasi(p_jadwal, p_tanggal) <= 0 THEN
    RAISE EXCEPTION 'Kuota sesi dokter pada tanggal tersebut sudah penuh' USING ERRCODE = 'CS409';
  END IF;

  -- Cek kuota harian unit poliklinik (jika terhubung ke master poliklinik)
  IF p.id IS NOT NULL THEN
    SELECT COUNT(*)::integer INTO v_terisi_h
    FROM reservasi_konsultasi r
    JOIN jadwal_konsultasi jk ON jk.id = r.jadwal_id
    WHERE jk.poliklinik_id = p.id
      AND r.tanggal = p_tanggal
      AND r.status <> 'dibatalkan';

    IF v_terisi_h >= p.kuota_harian THEN
      RAISE EXCEPTION 'Kuota harian % sudah penuh', p.nama_poli USING ERRCODE = 'CS409';
    END IF;
  END IF;

  -- Hitung nomor antrean berikutnya secara atomik
  SELECT COALESCE(MAX(r.nomor_antrean), 0) + 1 INTO v_antrean
  FROM reservasi_konsultasi r
  WHERE r.jadwal_id = p_jadwal AND r.tanggal = p_tanggal;

  v_tiket := 'TKT-' || to_char(p_tanggal, 'YYYYMMDD') || '-' || nextval('seq_tiket_poliklinik');

  INSERT INTO reservasi_konsultasi (
    kode_reservasi, jadwal_id, rs_id, user_id, nama_pasien, no_telp,
    tanggal, keluhan, idempotency_key, nomor_antrean, kode_tiket
  )
  VALUES (
    p_kode, j.id, j.rs_id, p_user_id, p_pasien, p_telp,
    p_tanggal, p_keluhan, p_idem, v_antrean, v_tiket
  )
  RETURNING id INTO v_id;

  RETURN QUERY SELECT v_id, v_antrean, v_tiket;
END $$;

-- Stored Procedure operasional: menutup antrean kedaluwarsa yang belum hadir
CREATE OR REPLACE PROCEDURE prc_tutup_antrean_kedaluwarsa(p_batas_tanggal date DEFAULT fn_hari_ini_wib())
LANGUAGE plpgsql AS $$
DECLARE
  v_jumlah integer;
BEGIN
  UPDATE reservasi_konsultasi
  SET status = 'dibatalkan',
      keluhan = COALESCE(keluhan, '') || ' [Ditutup otomatis: melewati tanggal kunjungan]'
  WHERE tanggal < p_batas_tanggal
    AND status = 'menunggu';

  GET DIAGNOSTICS v_jumlah = ROW_COUNT;

  INSERT INTO audit_log (aktor, aksi, tabel, record_id, data_baru)
  VALUES (
    'system_scheduler',
    'PROC',
    'reservasi_konsultasi',
    p_batas_tanggal::text,
    jsonb_build_object('jumlah_ditutup', v_jumlah, 'batas_tanggal', p_batas_tanggal)
  );
END $$;

-- ---------------------------------------------------------------------------
-- G. Triggers (Memanfaatkan fn_set_updated_at & fn_audit dari migrasi 003)
-- ---------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_updated_users ON users;
CREATE TRIGGER trg_updated_users BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_updated_poliklinik ON poliklinik;
CREATE TRIGGER trg_updated_poliklinik BEFORE UPDATE ON poliklinik
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_updated_ulasan ON ulasan_rs;
CREATE TRIGGER trg_updated_ulasan BEFORE UPDATE ON ulasan_rs
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_audit_poliklinik ON poliklinik;
CREATE TRIGGER trg_audit_poliklinik AFTER INSERT OR UPDATE OR DELETE ON poliklinik
  FOR EACH ROW EXECUTE FUNCTION fn_audit('id');

DROP TRIGGER IF EXISTS trg_audit_ulasan ON ulasan_rs;
CREATE TRIGGER trg_audit_ulasan AFTER INSERT OR UPDATE OR DELETE ON ulasan_rs
  FOR EACH ROW EXECUTE FUNCTION fn_audit('id');

-- ---------------------------------------------------------------------------
-- H. Analytical Views (CTE, GROUP BY, HAVING, Window Function RANK/DENSE_RANK)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_okupansi_poliklinik AS
SELECT
  p.id AS poliklinik_id,
  p.rs_id,
  p.kode_poli,
  p.nama_poli,
  p.spesialisasi,
  p.lokasi_ruangan,
  p.kuota_harian,
  p.aktif,
  COUNT(DISTINCT j.id) FILTER (WHERE j.aktif) AS jumlah_dokter_aktif,
  COUNT(r.id) FILTER (WHERE r.tanggal = fn_hari_ini_wib() AND r.status <> 'dibatalkan') AS terisi_hari_ini,
  GREATEST(
    p.kuota_harian - COUNT(r.id) FILTER (WHERE r.tanggal = fn_hari_ini_wib() AND r.status <> 'dibatalkan'),
    0
  )::integer AS sisa_hari_ini
FROM poliklinik p
LEFT JOIN jadwal_konsultasi j ON j.poliklinik_id = p.id
LEFT JOIN reservasi_konsultasi r ON r.jadwal_id = j.id
GROUP BY p.id;

-- View Peringkat RS (menggunakan CTE, agregasi AVG/COUNT, HAVING, dan Window Functions)
CREATE OR REPLACE VIEW v_peringkat_rs AS
WITH agregat_ulasan AS (
  SELECT
    rs_id,
    ROUND(AVG(rating)::numeric, 2) AS rata_rating,
    COUNT(*)::integer              AS total_ulasan,
    COUNT(*) FILTER (WHERE rating = 5)::integer AS jumlah_bintang_5
  FROM ulasan_rs
  WHERE status_moderasi = 'disetujui'
  GROUP BY rs_id
  HAVING COUNT(*) >= 1
),
agregat_favorit AS (
  SELECT rs_id, COUNT(*)::integer AS total_favorit
  FROM favorit_rs
  GROUP BY rs_id
)
SELECT
  u.rs_id,
  u.rata_rating,
  u.total_ulasan,
  u.jumlah_bintang_5,
  COALESCE(f.total_favorit, 0) AS total_favorit,
  RANK() OVER (ORDER BY u.rata_rating DESC, u.total_ulasan DESC)       AS peringkat_rating,
  DENSE_RANK() OVER (ORDER BY u.total_ulasan DESC, u.rata_rating DESC) AS peringkat_terpopuler
FROM agregat_ulasan u
LEFT JOIN agregat_favorit f ON f.rs_id = u.rs_id;

-- View Ringkasan Aktivitas per Pengguna (untuk Dashboard Pasien)
CREATE OR REPLACE VIEW v_ringkasan_aktivitas_user AS
SELECT
  u.id AS user_id,
  u.username,
  u.nama_lengkap,
  (SELECT COUNT(*)::integer FROM favorit_rs f WHERE f.user_id = u.id) AS total_favorit,
  (SELECT COUNT(*)::integer FROM ulasan_rs ul WHERE ul.user_id = u.id) AS total_ulasan,
  (SELECT COUNT(*)::integer FROM reservasi_konsultasi rk WHERE rk.user_id = u.id) AS total_reservasi_poli,
  (SELECT COUNT(*)::integer FROM reservasi_konsultasi rk
    WHERE rk.user_id = u.id AND rk.status IN ('menunggu', 'dikonfirmasi')) AS antrean_poli_aktif,
  (SELECT COUNT(*)::integer FROM booking_kamar bk WHERE bk.user_id = u.id) AS total_booking_kamar
FROM users u;

-- Berikan hak SELECT pada view analitik ke role read-only carisehat_viewer
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'carisehat_viewer') THEN
    GRANT SELECT ON v_okupansi_poliklinik, v_peringkat_rs, v_ringkasan_aktivitas_user TO carisehat_viewer;
  END IF;
END $$;