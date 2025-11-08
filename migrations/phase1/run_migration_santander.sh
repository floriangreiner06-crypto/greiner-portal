#!/bin/bash
# Migration-Script für Santander-Support
# Datum: 2025-11-08
# Verzeichnis: /opt/greiner-portal/migrations/phase1/

set -e  # Bei Fehler abbrechen

DB_PATH="/opt/greiner-portal/data/greiner_controlling.db"
BACKUP_PATH="${DB_PATH}.backup_santander_$(date +%Y%m%d_%H%M%S)"
MIGRATION_SQL="/opt/greiner-portal/migrations/phase1/006_add_santander_support.sql"

echo "=================================="
echo "SANTANDER MIGRATION - SCHRITT 1"
echo "=================================="
echo ""

# 1. Backup erstellen
echo "📦 Erstelle Backup..."
cp "$DB_PATH" "$BACKUP_PATH"
echo "✅ Backup erstellt: $BACKUP_PATH"
echo ""

# 2. Migration ausführen
echo "🔧 Führe Migration 006 aus..."
sqlite3 "$DB_PATH" < "$MIGRATION_SQL"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration erfolgreich!"
    echo ""
    echo "📊 Aktuelle Statistik:"
    sqlite3 "$DB_PATH" << 'EOF'
SELECT 
    COALESCE(finanzinstitut, 'NULL') as institut,
    COUNT(*) as anzahl,
    printf('%.2f', SUM(aktueller_saldo)) as gesamt_saldo
FROM fahrzeugfinanzierungen
GROUP BY finanzinstitut;
EOF
    echo ""
    echo "✅ Datenbank bereit für Santander-Import!"
else
    echo ""
    echo "❌ Fehler bei Migration!"
    echo "Restore Backup mit:"
    echo "cp $BACKUP_PATH $DB_PATH"
    exit 1
fi
