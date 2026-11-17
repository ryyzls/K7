-- Apply explicitly, before deploying keyed booking support. No patient rows copied.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
CREATE TABLE booking_idempotency (
  scope VARCHAR(32) NOT NULL,
  key_hash CHAR(64) NOT NULL,
  payload_hash CHAR(64) NOT NULL,
  booking_id INTEGER REFERENCES booking_kamar(id) ON DELETE RESTRICT,
  PRIMARY KEY (scope, key_hash)
);
COMMIT;
