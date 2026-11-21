# Backup PostgreSQL + state RDF di Windows PowerShell (padanan scripts/backup_db.sh).
# Pemakaian:  powershell -ExecutionPolicy Bypass -File scripts\backup_db.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $Root "backups"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$Db = "carisehat"; $UserDb = "hospital_admin"
$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
  foreach ($l in Get-Content $envFile) {
    if ($l -match '^POSTGRES_DB=(.+)$') { $Db = $Matches[1].Trim() }
    if ($l -match '^POSTGRES_USER=(.+)$') { $UserDb = $Matches[1].Trim() }
  }
}
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$sql = Join-Path $BackupDir "carisehat_$ts.sql"
Push-Location $Root
# Redirect biner PowerShell rawan merusak encoding; jalankan dump di dalam kontainer lalu salin keluar.
docker compose exec -T postgres sh -c "pg_dump -U $UserDb -d $Db --no-owner --clean --if-exists | gzip -9 > /tmp/dump.sql.gz"
$cid = (docker compose ps -q postgres)
docker cp "${cid}:/tmp/dump.sql.gz" "$sql.gz"
docker compose exec -T postgres rm -f /tmp/dump.sql.gz
Pop-Location
tar -czf (Join-Path $BackupDir "rdf_state_$ts.tar.gz") -C $Root semantic/rdf semantic/named_graphs
Get-ChildItem $BackupDir -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } | Remove-Item -Force
Write-Host "SELESAI: $sql.gz dan rdf_state_$ts.tar.gz di $BackupDir"
