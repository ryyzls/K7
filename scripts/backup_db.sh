#!/usr/bin/env bash
# Backup & Recovery CariSehat (Materi 10).
# - Dump PostgreSQL (data booking, admin, kuota, jadwal, audit) -> .sql.gz bercap waktu
# - Arsip state RDF (semantic/rdf + named_graphs) -> .tar.gz
# - Verifikasi integritas gzip, lalu hapus backup lebih tua dari RETENTION_DAYS
# Pemakaian:  bash scripts/backup_db.sh        (jalankan dari mana saja)
# Jadwal harian (cron):  0 2 * * *  cd /path/K7 && bash scripts/backup_db.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

if [ -f "$ROOT/.env" ]; then
  set -a; . <(grep -E '^(POSTGRES_DB|POSTGRES_USER)=' "$ROOT/.env" | tr -d '\r'); set +a
fi
DB="${POSTGRES_DB:-carisehat}"
USER_DB="${POSTGRES_USER:-hospital_admin}"
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

SQL_FILE="$BACKUP_DIR/carisehat_${TS}.sql.gz"
RDF_FILE="$BACKUP_DIR/rdf_state_${TS}.tar.gz"

echo "[1/3] Dump PostgreSQL '$DB' -> $SQL_FILE"
docker compose -f "$ROOT/docker-compose.yml" exec -T postgres \
  pg_dump -U "$USER_DB" -d "$DB" --no-owner --clean --if-exists | gzip -9 > "$SQL_FILE"
gzip -t "$SQL_FILE"

echo "[2/3] Arsip state RDF -> $RDF_FILE"
tar -czf "$RDF_FILE" -C "$ROOT" semantic/rdf semantic/named_graphs 2>/dev/null || tar -czf "$RDF_FILE" -C "$ROOT" semantic/rdf
tar -tzf "$RDF_FILE" > /dev/null

echo "[3/3] Hapus backup > ${RETENTION_DAYS} hari"
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'carisehat_*.sql.gz' -o -name 'rdf_state_*.tar.gz' \) -mtime +"$RETENTION_DAYS" -print -delete || true

echo "SELESAI: $(du -h "$SQL_FILE" | cut -f1) SQL, $(du -h "$RDF_FILE" | cut -f1) RDF"
echo "Restore: bash scripts/restore_db.sh $SQL_FILE"
