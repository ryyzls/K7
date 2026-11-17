-- Roll back only objects introduced by 001 on the audited pre-migration schema.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
DROP INDEX idx_booking_status;
ALTER TABLE booking_kamar ALTER COLUMN status DROP DEFAULT;
ALTER TABLE booking_kamar DROP CONSTRAINT booking_kamar_status_check;
ALTER TABLE booking_kamar DROP CONSTRAINT booking_kamar_jenis_kamar_check;
COMMIT;
