#!/bin/bash
# Backup Cleanup Script - Löscht alte Backups
# Erstellt: TAG82

BACKUP_DIR="/opt/greiner-portal/backups"
DB_PATH="/opt/greiner-portal/data/greiner_controlling.db"
KEEP_DAYS=7

echo "=== Backup Cleanup Start: $(date) ==="
echo "Verzeichnis: $BACKUP_DIR"
echo "Behalte Backups der letzten $KEEP_DAYS Tage"

# Zähle Backups vor dem Löschen
BEFORE=$(find "$BACKUP_DIR" -name "*.gz" -type f 2>/dev/null | wc -l)

# Lösche Backups älter als KEEP_DAYS
DELETED=$(find "$BACKUP_DIR" -name "greiner_controlling_*.db.gz" -type f -mtime +$KEEP_DAYS -delete -print | wc -l)

# Zähle Backups nach dem Löschen
AFTER=$(find "$BACKUP_DIR" -name "*.gz" -type f 2>/dev/null | wc -l)

echo "Backups vorher: $BEFORE"
echo "Gelöscht: $DELETED"
echo "Backups nachher: $AFTER"

# Status in DB schreiben
sqlite3 "$DB_PATH" "UPDATE system_jobs SET last_status='success', last_run='$(date -Iseconds)', updated_at='$(date -Iseconds)' WHERE job_name='backup_cleanup';"

echo "=== Backup Cleanup Ende: $(date) ==="
