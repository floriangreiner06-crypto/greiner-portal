#!/bin/bash
# =============================================================================
# ROLLBACK: Zurück zu SQLite
# =============================================================================
# Setzt DRIVE Portal zurück auf SQLite-Datenbank
#
# Verwendung:
#   sudo ./rollback_to_sqlite.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}ROLLBACK: Zurück zu SQLite${NC}"
echo -e "${YELLOW}========================================${NC}"

ENV_FILE="/opt/greiner-portal/config/.env"

# Prüfe ob .env existiert
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}.env nicht gefunden: $ENV_FILE${NC}"
    exit 1
fi

# Aktuellen Status anzeigen
echo -e "\nAktueller DB_TYPE:"
grep "DB_TYPE" $ENV_FILE || echo "  (nicht gesetzt = sqlite)"

# Backup der .env
cp $ENV_FILE "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# DB_TYPE auf sqlite setzen
if grep -q "^DB_TYPE=" $ENV_FILE; then
    sed -i 's/^DB_TYPE=.*/DB_TYPE=sqlite/' $ENV_FILE
else
    echo "DB_TYPE=sqlite" >> $ENV_FILE
fi

echo -e "\n${GREEN}✓ .env aktualisiert: DB_TYPE=sqlite${NC}"

# Service neustarten
echo -e "\nStarte greiner-portal neu..."
systemctl restart greiner-portal

sleep 2

if systemctl is-active --quiet greiner-portal; then
    echo -e "${GREEN}✓ Service läuft${NC}"
else
    echo -e "${RED}✗ Service nicht gestartet!${NC}"
    echo "Prüfe Logs: journalctl -u greiner-portal -f"
    exit 1
fi

# Verifizieren
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}ROLLBACK ERFOLGREICH${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "DRIVE Portal verwendet jetzt SQLite."
echo "PostgreSQL-Daten bleiben erhalten für späteren Wechsel."
echo ""
echo "Zurück zu PostgreSQL:"
echo "  1. In .env: DB_TYPE=postgresql"
echo "  2. sudo systemctl restart greiner-portal"
