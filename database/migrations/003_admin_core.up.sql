-- ============================================================================
-- 003_admin_core.up.sql  (CariSehat - Tubes MSBD)
-- Migrasi IDEMPOTENT (aman dijalankan berulang) dan dijalankan otomatis saat
-- backend start (app/database/migrate.py). Menggantikan 001/002 yang manual:
-- semua efek 001 & 002 dibuat ulang di sini dengan IF NOT EXISTS.
--
-- Aturan Emas Polyglot: rs_id (rs-001..rs-206) adalah satu-satunya perekat ke
-- RDF. Atribut deskriptif RS (nama/alamat/fasilitas) TIDAK disimpan di SQL.
-- File ini dieksekusi sebagai SATU transaksi (rollback otomatis bila gagal).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- A. Baseline booking_kamar (setara 001 + 002, versi idempotent)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'booking_kamar_jenis_kamar_check') THEN
    ALTER TABLE booking_kamar ADD CONSTRAINT booking_kamar_jenis_kamar_check
      CHECK (jenis_kamar IN ('VIP','Kelas I','Kelas II','Kelas III','ICU')) NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'booking_kamar_status_check') THEN
    ALTER TABLE booking_kamar ADD CONSTRAINT booking_kamar_status_check
      CHECK (status IN ('menunggu','dikonfirmasi','dibatalkan')) NOT VALID;
  END IF;
END $$;

ALTER TABLE booking_kamar ALTER COLUMN status SET DEFAULT 'menunggu';
CREATE INDEX IF NOT EXISTS idx_booking_status ON booking_kamar (status);
CREATE INDEX IF NOT EXISTS idx_booking_tanggal ON booking_kamar (kode_rs, jenis_kamar, tanggal_masuk);

-- Polyglot: nama RS diambil dari RDF saat dibaca, tidak lagi wajib disimpan di SQL.
ALTER TABLE booking_kamar ALTER COLUMN nama_rs DROP NOT NULL;
ALTER TABLE booking_kamar ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Pencegah double booking: pasien yang sama, RS, kamar, tanggal, telepon sama
-- tidak boleh punya dua booking aktif.
DO $$
BEGIN
  CREATE UNIQUE INDEX IF NOT EXISTS uq_booking_pasien_aktif
    ON booking_kamar (kode_rs, jenis_kamar, lower(nama_pasien), no_telp, tanggal_masuk)
    WHERE status <> 'dibatalkan';
EXCEPTION WHEN unique_violation THEN
  RAISE NOTICE 'uq_booking_pasien_aktif dilewati: data lama berisi duplikat aktif. Bersihkan lalu jalankan ulang.';
END $$;

-- Ledger idempotency (Materi 09): kunci idempotency + hash payload.
CREATE TABLE IF NOT EXISTS booking_idempotency (
  scope        VARCHAR(32) NOT NULL,
  key_hash     CHAR(64)    NOT NULL,
  payload_hash CHAR(64)    NOT NULL,
  booking_id   INTEGER REFERENCES booking_kamar(id) ON DELETE RESTRICT,
  PRIMARY KEY (scope, key_hash)
);

-- ---------------------------------------------------------------------------
-- B. Manajemen hak akses (RBAC): roles, permissions, admin, sesi
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
  kode      VARCHAR(30) PRIMARY KEY,
  deskripsi TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS role_permissions (
  role_kode  VARCHAR(30) NOT NULL REFERENCES roles(kode) ON DELETE CASCADE,
  permission VARCHAR(50) NOT NULL,
  PRIMARY KEY (role_kode, permission)
);

CREATE TABLE IF NOT EXISTS admin_users (
  id              SERIAL PRIMARY KEY,
  username        VARCHAR(50)  NOT NULL UNIQUE CHECK (username ~ '^[A-Za-z0-9_.-]{3,50}$'),
  password_hash   TEXT         NOT NULL,
  nama_lengkap    VARCHAR(100) NOT NULL,
  role_kode       VARCHAR(30)  NOT NULL REFERENCES roles(kode),
  aktif           BOOLEAN      NOT NULL DEFAULT TRUE,
  failed_attempts INTEGER      NOT NULL DEFAULT 0,
  locked_until    TIMESTAMPTZ,
  last_login      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_sessions (
  token_hash CHAR(64)    PRIMARY KEY,
  user_id    INTEGER     NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_user ON admin_sessions (user_id);

INSERT INTO roles (kode, deskripsi) VALUES
  ('superadmin', 'Akses penuh termasuk manajemen pengguna, penghapusan data, dan audit log'),
  ('operator',   'Mengelola booking, kuota kamar, jadwal & reservasi konsultasi'),
  ('viewer',     'Hanya melihat dashboard dan data (read-only)')
ON CONFLICT (kode) DO NOTHING;

INSERT INTO role_permissions (role_kode, permission) VALUES
  ('superadmin','dashboard.view'),('superadmin','booking.read'),('superadmin','booking.write'),('superadmin','booking.delete'),
  ('superadmin','kuota.read'),('superadmin','kuota.write'),('superadmin','jadwal.read'),('superadmin','jadwal.write'),
  ('superadmin','reservasi.read'),('superadmin','reservasi.write'),('superadmin','user.manage'),('superadmin','audit.read'),
  ('operator','dashboard.view'),('operator','booking.read'),('operator','booking.write'),
  ('operator','kuota.read'),('operator','kuota.write'),('operator','jadwal.read'),('operator','jadwal.write'),
  ('operator','reservasi.read'),('operator','reservasi.write'),
  ('viewer','dashboard.view'),('viewer','booking.read'),('viewer','kuota.read'),
  ('viewer','jadwal.read'),('viewer','reservasi.read')
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- C. Kuota kamar & konsultasi (data dinamis; deskripsi RS tetap di RDF)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kuota_kamar (
  rs_id       VARCHAR(20) NOT NULL,
  jenis_kamar VARCHAR(30) NOT NULL CHECK (jenis_kamar IN ('VIP','Kelas I','Kelas II','Kelas III','ICU')),
  kapasitas   INTEGER     NOT NULL CHECK (kapasitas BETWEEN 0 AND 1000),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (rs_id, jenis_kamar)
);

CREATE TABLE IF NOT EXISTS jadwal_konsultasi (
  id             SERIAL PRIMARY KEY,
  rs_id          VARCHAR(20)  NOT NULL,
  nama_dokter    VARCHAR(120) NOT NULL,
  spesialisasi   VARCHAR(80)  NOT NULL,
  hari           SMALLINT     NOT NULL CHECK (hari BETWEEN 1 AND 7),   -- ISO: 1=Senin ... 7=Minggu
  jam_mulai      TIME         NOT NULL,
  jam_selesai    TIME         NOT NULL,
  kuota_per_sesi INTEGER      NOT NULL DEFAULT 10 CHECK (kuota_per_sesi BETWEEN 1 AND 500),
  aktif          BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  CHECK (jam_selesai > jam_mulai)
);
CREATE INDEX IF NOT EXISTS idx_jadwal_rs_hari ON jadwal_konsultasi (rs_id, hari);

CREATE TABLE IF NOT EXISTS reservasi_konsultasi (
  id              SERIAL PRIMARY KEY,
  kode_reservasi  VARCHAR(24)  NOT NULL UNIQUE,
  jadwal_id       INTEGER      NOT NULL REFERENCES jadwal_konsultasi(id) ON DELETE RESTRICT,
  rs_id           VARCHAR(20)  NOT NULL,
  nama_pasien     VARCHAR(100) NOT NULL,
  no_telp         VARCHAR(20)  NOT NULL,
  tanggal         DATE         NOT NULL,
  keluhan         TEXT,
  status          VARCHAR(15)  NOT NULL DEFAULT 'menunggu'
                  CHECK (status IN ('menunggu','dikonfirmasi','selesai','dibatalkan')),
  idempotency_key VARCHAR(64)  UNIQUE,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_reservasi_jadwal ON reservasi_konsultasi (jadwal_id, tanggal);
CREATE UNIQUE INDEX IF NOT EXISTS uq_reservasi_pasien_aktif
  ON reservasi_konsultasi (jadwal_id, tanggal, no_telp) WHERE status <> 'dibatalkan';

-- ---------------------------------------------------------------------------
-- D. Audit log
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
  id        BIGSERIAL PRIMARY KEY,
  waktu     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  aktor     VARCHAR(50),
  aksi      VARCHAR(10) NOT NULL,
  tabel     VARCHAR(50) NOT NULL,
  record_id TEXT,
  data_lama JSONB,
  data_baru JSONB
);
CREATE INDEX IF NOT EXISTS idx_audit_waktu ON audit_log (waktu DESC);
CREATE INDEX IF NOT EXISTS idx_audit_tabel ON audit_log (tabel, waktu DESC);

-- ---------------------------------------------------------------------------
-- E. Functions & stored procedures
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_hari_ini_wib() RETURNS date
LANGUAGE sql STABLE AS $$ SELECT (now() AT TIME ZONE 'Asia/Jakarta')::date $$;

-- Kapasitas kamar per RS & jenis. Bila belum diatur admin, default 5 kamar.
CREATE OR REPLACE FUNCTION fn_kapasitas_kamar(p_rs text, p_jenis text) RETURNS integer
LANGUAGE sql STABLE AS $$
  SELECT COALESCE((SELECT kapasitas FROM kuota_kamar WHERE rs_id = p_rs AND jenis_kamar = p_jenis), 5)
$$;

-- Okupansi puncak (jumlah kamar terpakai terbanyak pada satu hari) di periode tertentu.
CREATE OR REPLACE FUNCTION fn_terisi_kamar(p_rs text, p_jenis text, p_masuk date, p_keluar date, p_exclude integer DEFAULT NULL)
RETURNS integer LANGUAGE sql STABLE AS $$
  SELECT COALESCE(MAX(t.c), 0)::integer FROM (
    SELECT g.d::date AS hari, COUNT(b.id) AS c
    FROM generate_series(p_masuk::timestamp,
                         LEAST(COALESCE(p_keluar, p_masuk), p_masuk + 365)::timestamp,
                         interval '1 day') AS g(d)
    LEFT JOIN booking_kamar b
      ON b.kode_rs = p_rs AND b.jenis_kamar = p_jenis AND b.status <> 'dibatalkan'
     AND (p_exclude IS NULL OR b.id <> p_exclude)
     AND g.d::date BETWEEN b.tanggal_masuk AND COALESCE(b.tanggal_keluar, b.tanggal_masuk)
    GROUP BY g.d
  ) t
$$;

CREATE OR REPLACE FUNCTION fn_sisa_kamar(p_rs text, p_jenis text, p_masuk date, p_keluar date, p_exclude integer DEFAULT NULL)
RETURNS integer LANGUAGE sql STABLE AS $$
  SELECT GREATEST(fn_kapasitas_kamar(p_rs, p_jenis) - fn_terisi_kamar(p_rs, p_jenis, p_masuk, p_keluar, p_exclude), 0)
$$;

-- Stored procedure booking ATOMIK: kunci advisory per (RS, jenis kamar) agar dua
-- request bersamaan tidak bisa sama-sama mengambil kamar terakhir (race condition).
CREATE OR REPLACE FUNCTION sp_buat_booking(
  p_kode text, p_rs text, p_pasien text, p_telp text,
  p_masuk date, p_keluar date, p_jenis text, p_catatan text
) RETURNS integer LANGUAGE plpgsql AS $$
DECLARE v_id integer;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('booking:' || p_rs || ':' || p_jenis, 0));
  IF fn_sisa_kamar(p_rs, p_jenis, p_masuk, p_keluar, NULL) <= 0 THEN
    RAISE EXCEPTION 'Kamar % penuh pada periode yang dipilih', p_jenis USING ERRCODE = 'CS409';
  END IF;
  INSERT INTO booking_kamar (kode_booking, kode_rs, nama_pasien, no_telp, tanggal_masuk, tanggal_keluar, jenis_kamar, catatan)
  VALUES (p_kode, p_rs, p_pasien, p_telp, p_masuk, p_keluar, p_jenis, p_catatan)
  RETURNING id INTO v_id;
  RETURN v_id;
END $$;

-- Sisa kuota satu sesi konsultasi pada tanggal tertentu.
CREATE OR REPLACE FUNCTION fn_sisa_kuota_konsultasi(p_jadwal integer, p_tanggal date) RETURNS integer
LANGUAGE sql STABLE AS $$
  SELECT GREATEST(j.kuota_per_sesi - (
           SELECT COUNT(*) FROM reservasi_konsultasi r
           WHERE r.jadwal_id = j.id AND r.tanggal = p_tanggal AND r.status <> 'dibatalkan'
         )::integer, 0)
  FROM jadwal_konsultasi j WHERE j.id = p_jadwal
$$;

-- Reservasi konsultasi ATOMIK dengan validasi hari praktik, sesi, dan kuota.
CREATE OR REPLACE FUNCTION sp_buat_reservasi_konsultasi(
  p_kode text, p_jadwal integer, p_pasien text, p_telp text,
  p_tanggal date, p_keluhan text, p_idem text
) RETURNS integer LANGUAGE plpgsql AS $$
DECLARE
  j jadwal_konsultasi%ROWTYPE;
  v_id integer;
  v_sekarang timestamp := (now() AT TIME ZONE 'Asia/Jakarta');
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('konsultasi:' || p_jadwal || ':' || p_tanggal, 0));
  SELECT * INTO j FROM jadwal_konsultasi WHERE id = p_jadwal AND aktif;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Jadwal konsultasi tidak ditemukan atau tidak aktif' USING ERRCODE = 'CS404';
  END IF;
  IF EXTRACT(ISODOW FROM p_tanggal)::integer <> j.hari THEN
    RAISE EXCEPTION 'Tanggal tidak sesuai hari praktik dokter' USING ERRCODE = 'CS422';
  END IF;
  IF p_tanggal < v_sekarang::date OR (p_tanggal = v_sekarang::date AND v_sekarang::time >= j.jam_selesai) THEN
    RAISE EXCEPTION 'Sesi konsultasi sudah berakhir atau tanggal sudah lewat' USING ERRCODE = 'CS422';
  END IF;
  IF fn_sisa_kuota_konsultasi(p_jadwal, p_tanggal) <= 0 THEN
    RAISE EXCEPTION 'Kuota sesi konsultasi pada tanggal tersebut sudah penuh' USING ERRCODE = 'CS409';
  END IF;
  INSERT INTO reservasi_konsultasi (kode_reservasi, jadwal_id, rs_id, nama_pasien, no_telp, tanggal, keluhan, idempotency_key)
  VALUES (p_kode, j.id, j.rs_id, p_pasien, p_telp, p_tanggal, p_keluhan, p_idem)
  RETURNING id INTO v_id;
  RETURN v_id;
END $$;

-- ---------------------------------------------------------------------------
-- F. Triggers
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN NEW.updated_at := NOW(); RETURN NEW; END $$;

CREATE OR REPLACE FUNCTION fn_audit() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_old jsonb; v_new jsonb; v_actor text;
BEGIN
  v_actor := COALESCE(NULLIF(current_setting('app.aktor', true), ''), 'system');
  IF TG_OP IN ('UPDATE', 'DELETE') THEN v_old := to_jsonb(OLD) - 'password_hash'; END IF;
  IF TG_OP IN ('INSERT', 'UPDATE') THEN v_new := to_jsonb(NEW) - 'password_hash'; END IF;
  INSERT INTO audit_log (aktor, aksi, tabel, record_id, data_lama, data_baru)
  VALUES (v_actor, TG_OP, TG_TABLE_NAME, COALESCE(v_new, v_old) ->> TG_ARGV[0], v_old, v_new);
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION fn_booking_validasi() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.tanggal_keluar IS NOT NULL AND NEW.tanggal_keluar < NEW.tanggal_masuk THEN
    RAISE EXCEPTION 'tanggal_keluar tidak boleh sebelum tanggal_masuk' USING ERRCODE = 'CS422';
  END IF;
  IF TG_OP = 'UPDATE' AND OLD.status = 'dibatalkan' AND NEW.status <> 'dibatalkan' THEN
    RAISE EXCEPTION 'Booking yang sudah dibatalkan tidak dapat diaktifkan kembali' USING ERRCODE = 'CS422';
  END IF;
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION fn_jadwal_validasi() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.aktif AND EXISTS (
    SELECT 1 FROM jadwal_konsultasi o
    WHERE o.rs_id = NEW.rs_id AND o.nama_dokter = NEW.nama_dokter AND o.hari = NEW.hari AND o.aktif
      AND o.id IS DISTINCT FROM NEW.id
      AND o.jam_mulai < NEW.jam_selesai AND NEW.jam_mulai < o.jam_selesai
  ) THEN
    RAISE EXCEPTION 'Jadwal dokter bentrok dengan jadwal lain di hari yang sama' USING ERRCODE = 'CS409';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_booking_validasi ON booking_kamar;
CREATE TRIGGER trg_booking_validasi BEFORE INSERT OR UPDATE ON booking_kamar
  FOR EACH ROW EXECUTE FUNCTION fn_booking_validasi();

DROP TRIGGER IF EXISTS trg_jadwal_validasi ON jadwal_konsultasi;
CREATE TRIGGER trg_jadwal_validasi BEFORE INSERT OR UPDATE ON jadwal_konsultasi
  FOR EACH ROW EXECUTE FUNCTION fn_jadwal_validasi();

DROP TRIGGER IF EXISTS trg_updated_booking ON booking_kamar;
CREATE TRIGGER trg_updated_booking BEFORE UPDATE ON booking_kamar
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
DROP TRIGGER IF EXISTS trg_updated_kuota ON kuota_kamar;
CREATE TRIGGER trg_updated_kuota BEFORE UPDATE ON kuota_kamar
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
DROP TRIGGER IF EXISTS trg_updated_jadwal ON jadwal_konsultasi;
CREATE TRIGGER trg_updated_jadwal BEFORE UPDATE ON jadwal_konsultasi
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
DROP TRIGGER IF EXISTS trg_updated_reservasi ON reservasi_konsultasi;
CREATE TRIGGER trg_updated_reservasi BEFORE UPDATE ON reservasi_konsultasi
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
DROP TRIGGER IF EXISTS trg_updated_admin ON admin_users;
CREATE TRIGGER trg_updated_admin BEFORE UPDATE ON admin_users
  FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_audit_booking ON booking_kamar;
CREATE TRIGGER trg_audit_booking AFTER INSERT OR UPDATE OR DELETE ON booking_kamar
  FOR EACH ROW EXECUTE FUNCTION fn_audit('kode_booking');
DROP TRIGGER IF EXISTS trg_audit_kuota ON kuota_kamar;
CREATE TRIGGER trg_audit_kuota AFTER INSERT OR UPDATE OR DELETE ON kuota_kamar
  FOR EACH ROW EXECUTE FUNCTION fn_audit('rs_id');
DROP TRIGGER IF EXISTS trg_audit_jadwal ON jadwal_konsultasi;
CREATE TRIGGER trg_audit_jadwal AFTER INSERT OR UPDATE OR DELETE ON jadwal_konsultasi
  FOR EACH ROW EXECUTE FUNCTION fn_audit('id');
DROP TRIGGER IF EXISTS trg_audit_reservasi ON reservasi_konsultasi;
CREATE TRIGGER trg_audit_reservasi AFTER INSERT OR UPDATE OR DELETE ON reservasi_konsultasi
  FOR EACH ROW EXECUTE FUNCTION fn_audit('kode_reservasi');
DROP TRIGGER IF EXISTS trg_audit_admin ON admin_users;
CREATE TRIGGER trg_audit_admin AFTER INSERT OR UPDATE OR DELETE ON admin_users
  FOR EACH ROW EXECUTE FUNCTION fn_audit('username');

-- ---------------------------------------------------------------------------
-- G. Views
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_ringkasan_booking_per_rs AS
SELECT kode_rs AS rs_id,
       COUNT(*)                                          AS total,
       COUNT(*) FILTER (WHERE status = 'menunggu')       AS menunggu,
       COUNT(*) FILTER (WHERE status = 'dikonfirmasi')   AS dikonfirmasi,
       COUNT(*) FILTER (WHERE status = 'dibatalkan')     AS dibatalkan
FROM booking_kamar GROUP BY kode_rs;

CREATE OR REPLACE VIEW v_okupansi_kamar AS
SELECT k.rs_id, k.jenis_kamar, k.kapasitas,
       fn_terisi_kamar(k.rs_id, k.jenis_kamar, fn_hari_ini_wib(), NULL) AS terisi_hari_ini,
       GREATEST(k.kapasitas - fn_terisi_kamar(k.rs_id, k.jenis_kamar, fn_hari_ini_wib(), NULL), 0) AS sisa_hari_ini
FROM kuota_kamar k;

CREATE OR REPLACE VIEW v_statistik_dashboard AS
SELECT
  (SELECT COUNT(*) FROM booking_kamar)                                       AS total_booking,
  (SELECT COUNT(*) FROM booking_kamar WHERE status = 'menunggu')             AS booking_menunggu,
  (SELECT COUNT(*) FROM booking_kamar WHERE status = 'dikonfirmasi')         AS booking_dikonfirmasi,
  (SELECT COUNT(*) FROM booking_kamar WHERE status = 'dibatalkan')           AS booking_dibatalkan,
  (SELECT COUNT(*) FROM booking_kamar WHERE created_at >= date_trunc('day', now())) AS booking_hari_ini,
  (SELECT COUNT(*) FROM jadwal_konsultasi WHERE aktif)                       AS jadwal_aktif,
  (SELECT COUNT(*) FROM reservasi_konsultasi WHERE status IN ('menunggu','dikonfirmasi')) AS reservasi_aktif,
  (SELECT COUNT(*) FROM kuota_kamar)                                         AS kuota_diatur,
  (SELECT COUNT(*) FROM admin_users WHERE aktif)                             AS admin_aktif;

-- ---------------------------------------------------------------------------
-- H. Hak akses level database (Materi 11): role read-only untuk pelaporan
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'carisehat_viewer') THEN
    CREATE ROLE carisehat_viewer NOLOGIN;
  END IF;
  GRANT SELECT ON v_ringkasan_booking_per_rs, v_okupansi_kamar, v_statistik_dashboard TO carisehat_viewer;
EXCEPTION WHEN insufficient_privilege THEN
  RAISE NOTICE 'Role carisehat_viewer dilewati: user database tidak punya hak CREATEROLE.';
END $$;
