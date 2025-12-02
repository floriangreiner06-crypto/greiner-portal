#!/bin/bash
# DB Backup Script
# Erstellt: TAG82

BACKUP_DIR="/opt/greiner-portal/backups"
DB_PATH="/opt/greiner-portal/data/greiner_controlling.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/greiner_controlling_${DATE}.db"

echo "=== DB Backup Start: $(date) ==="

# Backup-Verzeichnis erstellen falls nötig
mkdir -p "$BACKUP_DIR"

# SQLite Backup (mit .backup für Konsistenz)
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

if [ $? -eq 0 ]; then
    # Komprimieren
    gzip "$BACKUP_FILE"
    SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "✅ Backup erstellt: ${BACKUP_FILE}.gz ($SIZE)"
    
    # In system_jobs Status schreiben
    sqlite3 "$DB_PATH" "UPDATE system_jobs SET last_status='success', last_run='$(date -Iseconds)', updated_at='$(date -Iseconds)' WHERE job_name='db_backup';"
else
    echo "❌ Backup fehlgeschlagen!"
    sqlite3 "$DB_PATH" "UPDATE system_jobs SET last_status='error', last_run='$(date -Iseconds)', updated_at='$(date -Iseconds)' WHERE job_name='db_backup';"
    exit 1
fi

echo "=== DB Backup Ende: $(date) ==="
