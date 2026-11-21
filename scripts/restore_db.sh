#!/usr/bin/env bash
# Restore PostgreSQL dari file .sql.gz hasil backup_db.sh.
# Pemakaian:  bash scripts/restore_db.sh backups/carisehat_YYYYMMDD_HHMMSS.sql.gz
# Dump dibuat dengan --clean --if-exists sehingga tabel lama otomatis diganti.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="${1:?Beri path file backup .sql.gz}"
[ -f "$FILE" ] || { echo "File tidak ditemukan: $FILE"; exit 1; }
gzip -t "$FILE"

if [ -f "$ROOT/.env" ]; then
  set -a; . <(grep -E '^(POSTGRES_DB|POSTGRES_USER)=' "$ROOT/.env" | tr -d '\r'); set +a
fi
DB="${POSTGRES_DB:-carisehat}"
USER_DB="${POSTGRES_USER:-hospital_admin}"

echo "Restore $FILE -> database '$DB' (data saat ini akan ditimpa)"
gunzip -c "$FILE" | docker compose -f "$ROOT/docker-compose.yml" exec -T postgres \
  psql -U "$USER_DB" -d "$DB" -v ON_ERROR_STOP=1 -q
echo "SELESAI. Restart backend bila perlu: docker compose restart backend"
