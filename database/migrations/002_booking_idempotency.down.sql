-- Removing this ledger loses replay protection. Explicit maintenance approval required.
BEGIN;
SET LOCAL lock_timeout = '5s';
DROP TABLE booking_idempotency;
COMMIT;
