BEGIN;
SET LOCAL lock_timeout = '5s';

DROP VIEW IF EXISTS v_ringkasan_aktivitas_user, v_peringkat_rs, v_okupansi_poliklinik;

DROP TRIGGER IF EXISTS trg_audit_ulasan ON ulasan_rs;
DROP TRIGGER IF EXISTS trg_audit_poliklinik ON poliklinik;
DROP TRIGGER IF EXISTS trg_updated_ulasan ON ulasan_rs;
DROP TRIGGER IF EXISTS trg_updated_poliklinik ON poliklinik;
DROP TRIGGER IF EXISTS trg_updated_users ON users;

DROP PROCEDURE IF EXISTS prc_tutup_antrean_kedaluwarsa(date);
DROP FUNCTION IF EXISTS sp_buat_reservasi_poliklinik(text, integer, integer, text, text, date, text, text);

DROP TABLE IF EXISTS ulasan_rs;
DROP TABLE IF EXISTS favorit_rs;

ALTER TABLE reservasi_konsultasi
  DROP CONSTRAINT IF EXISTS uq_reservasi_nomor_antrean,
  DROP COLUMN IF EXISTS kode_tiket,
  DROP COLUMN IF EXISTS nomor_antrean,
  DROP COLUMN IF EXISTS user_id;

ALTER TABLE booking_kamar DROP COLUMN IF EXISTS user_id;
ALTER TABLE jadwal_konsultasi DROP COLUMN IF EXISTS poliklinik_id;

DROP SEQUENCE IF EXISTS seq_tiket_poliklinik;
DROP TABLE IF EXISTS poliklinik;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS users;

DELETE FROM role_permissions WHERE permission IN ('poliklinik.read', 'poliklinik.write', 'ulasan.moderate');
DELETE FROM schema_migrations WHERE version = '004_poliklinik_pasien_ulasan';
COMMIT;