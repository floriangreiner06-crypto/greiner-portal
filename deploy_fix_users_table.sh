#!/bin/bash

# ============================================================================
# FIX USERS-TABELLE - DEPLOYMENT SCRIPT
# ============================================================================

set -e  # Bei Fehler abbrechen

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================================================"
echo "🔧 FIX USERS-TABELLE - DEPLOYMENT"
echo "========================================================================"
echo ""

cd /opt/greiner-portal

# ============================================================================
# 1. PRE-CHECK
# ============================================================================

echo -e "${BLUE}1️⃣ Pre-Check...${NC}"

# Aktuelle Spalten-Anzahl:
CURRENT_COLS=$(sqlite3 data/greiner_controlling.db "PRAGMA table_info(users);" | wc -l)
echo "   Aktuelle Spalten: $CURRENT_COLS"

if [ "$CURRENT_COLS" -eq 17 ]; then
    echo -e "${GREEN}   ✅ Tabelle hat bereits 17 Spalten - nichts zu tun!${NC}"
    exit 0
fi

if [ "$CURRENT_COLS" -ne 4 ]; then
    echo -e "${RED}   ❌ Unerwartete Spalten-Anzahl: $CURRENT_COLS${NC}"
    echo "   Erwarte 4 (alt) oder 17 (neu)"
    exit 1
fi

echo -e "${GREEN}   ✅ Alte Tabelle erkannt (4 Spalten)${NC}"
echo ""

# ============================================================================
# 2. SERVICE STOPPEN
# ============================================================================

echo -e "${BLUE}2️⃣ Service stoppen...${NC}"
sudo systemctl stop greiner-portal
sudo pkill -9 -f gunicorn 2>/dev/null || true
sleep 3
echo -e "${GREEN}   ✅ Service gestoppt${NC}"
echo ""

# ============================================================================
# 3. BACKUP
# ============================================================================

echo -e "${BLUE}3️⃣ Datenbank-Backup erstellen...${NC}"
BACKUP_FILE="data/greiner_controlling.db.backup_$(date +%Y%m%d_%H%M%S)"
cp data/greiner_controlling.db "$BACKUP_FILE"
echo -e "${GREEN}   ✅ Backup: $BACKUP_FILE${NC}"
echo ""

# ============================================================================
# 4. SQL-SCRIPT AUSFÜHREN
# ============================================================================

echo -e "${BLUE}4️⃣ SQL-Script ausführen...${NC}"

# Check ob Script existiert:
if [ ! -f "fix_users_table.sql" ]; then
    echo -e "${RED}   ❌ fix_users_table.sql nicht gefunden!${NC}"
    echo "   Bitte Script erst hochladen!"
    exit 1
fi

# Script ausführen:
sqlite3 data/greiner_controlling.db < fix_users_table.sql

echo -e "${GREEN}   ✅ SQL-Script ausgeführt${NC}"
echo ""

# ============================================================================
# 5. VERIFIKATION
# ============================================================================

echo -e "${BLUE}5️⃣ Verifikation...${NC}"

# Neue Spalten-Anzahl:
NEW_COLS=$(sqlite3 data/greiner_controlling.db "PRAGMA table_info(users);" | wc -l)
echo "   Neue Spalten: $NEW_COLS"

if [ "$NEW_COLS" -ne 17 ]; then
    echo -e "${RED}   ❌ FEHLER: Tabelle hat $NEW_COLS Spalten (sollte 17 sein)${NC}"
    echo "   Restore Backup: cp $BACKUP_FILE data/greiner_controlling.db"
    exit 1
fi

# Check wichtige Spalten:
echo "   Prüfe wichtige Spalten..."
for col in display_name email ou ad_groups; do
    if sqlite3 data/greiner_controlling.db "PRAGMA table_info(users);" | grep -q "$col"; then
        echo -e "      ✅ $col"
    else
        echo -e "      ${RED}❌ $col fehlt!${NC}"
        exit 1
    fi
done

# Check Backup-Tabelle:
if sqlite3 data/greiner_controlling.db ".tables" | grep -q "users_old_backup"; then
    echo -e "   ✅ Backup-Tabelle erstellt"
else
    echo -e "   ${RED}❌ Backup-Tabelle fehlt!${NC}"
fi

echo -e "${GREEN}   ✅ Alle Checks bestanden!${NC}"
echo ""

# ============================================================================
# 6. SERVICE STARTEN
# ============================================================================

echo -e "${BLUE}6️⃣ Service starten...${NC}"
sudo systemctl start greiner-portal
sleep 3

# Status prüfen:
if systemctl is-active --quiet greiner-portal; then
    echo -e "${GREEN}   ✅ Service läuft${NC}"
else
    echo -e "${RED}   ❌ Service startet nicht!${NC}"
    sudo systemctl status greiner-portal
    exit 1
fi

echo ""

# ============================================================================
# 7. ERFOLGS-MELDUNG
# ============================================================================

echo "========================================================================"
echo -e "${GREEN}✅ FIX ERFOLGREICH ABGESCHLOSSEN!${NC}"
echo "========================================================================"
echo ""
echo "📊 Zusammenfassung:"
echo "   Alte Spalten: $CURRENT_COLS"
echo "   Neue Spalten: $NEW_COLS"
echo "   Backup: $BACKUP_FILE"
echo "   Alte Tabelle: users_old_backup_20251109_0148"
echo ""
echo "🧪 Nächster Schritt:"
echo "   1. Browser: http://10.80.80.20/login"
echo "   2. Login testen!"
echo "   3. Logs: sudo journalctl -u greiner-portal -f"
echo ""
echo "========================================================================"
