-- Phase 1D: additive migration; does not modify patient rows.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
ALTER TABLE booking_kamar ADD CONSTRAINT booking_kamar_jenis_kamar_check
  CHECK (jenis_kamar IN ('VIP','Kelas I','Kelas II','Kelas III','ICU')) NOT VALID;
ALTER TABLE booking_kamar ADD CONSTRAINT booking_kamar_status_check
  CHECK (status IN ('menunggu','dikonfirmasi','dibatalkan')) NOT VALID;
ALTER TABLE booking_kamar VALIDATE CONSTRAINT booking_kamar_jenis_kamar_check;
ALTER TABLE booking_kamar VALIDATE CONSTRAINT booking_kamar_status_check;
ALTER TABLE booking_kamar ALTER COLUMN status SET DEFAULT 'menunggu';
CREATE INDEX idx_booking_status ON booking_kamar(status);
COMMIT;
