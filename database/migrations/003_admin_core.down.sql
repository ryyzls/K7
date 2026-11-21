-- Rollback 003: hanya membuang objek yang DIBUAT 003 (tabel admin/kuota/jadwal/audit,
-- function, trigger, view). Tabel booking_kamar dan booking_idempotency TIDAK dihapus.
-- PERINGATAN: menghapus akun admin, kuota, jadwal, reservasi konsultasi, dan audit log.
BEGIN;
SET LOCAL lock_timeout = '5s';

DROP VIEW IF EXISTS v_statistik_dashboard, v_okupansi_kamar, v_ringkasan_booking_per_rs;

DROP TRIGGER IF EXISTS trg_audit_booking ON booking_kamar;
DROP TRIGGER IF EXISTS trg_updated_booking ON booking_kamar;
DROP TRIGGER IF EXISTS trg_booking_validasi ON booking_kamar;

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS reservasi_konsultasi;
DROP TABLE IF EXISTS jadwal_konsultasi;
DROP TABLE IF EXISTS kuota_kamar;
DROP TABLE IF EXISTS admin_sessions;
DROP TABLE IF EXISTS admin_users;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS roles;

DROP FUNCTION IF EXISTS sp_buat_reservasi_konsultasi(text, integer, text, text, date, text, text);
DROP FUNCTION IF EXISTS sp_buat_booking(text, text, text, text, date, date, text, text);
DROP FUNCTION IF EXISTS fn_sisa_kuota_konsultasi(integer, date);
DROP FUNCTION IF EXISTS fn_sisa_kamar(text, text, date, date, integer);
DROP FUNCTION IF EXISTS fn_terisi_kamar(text, text, date, date, integer);
DROP FUNCTION IF EXISTS fn_kapasitas_kamar(text, text);
DROP FUNCTION IF EXISTS fn_hari_ini_wib();
DROP FUNCTION IF EXISTS fn_jadwal_validasi();
DROP FUNCTION IF EXISTS fn_booking_validasi();
DROP FUNCTION IF EXISTS fn_audit();
DROP FUNCTION IF EXISTS fn_set_updated_at();

DROP INDEX IF EXISTS uq_booking_pasien_aktif;
DELETE FROM schema_migrations WHERE version = '003_admin_core';
COMMIT;
