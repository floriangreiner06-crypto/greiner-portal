#!/bin/bash
################################################################################
# Root-Scripts Cleanup - TAG 43
# Verschiebt sync_*.py und import_stellantis.py nach scripts/sync/
# Aktualisiert Crontab automatisch
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🧹 ROOT-SCRIPTS CLEANUP - TAG 43                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd /opt/greiner-portal

# 1. BACKUP CRONTAB
echo -e "${YELLOW}📋 Schritt 1: Crontab Backup${NC}"
crontab -l > cron_backup_tag43_$(date +%Y%m%d_%H%M%S).txt
echo -e "${GREEN}✓ Backup erstellt${NC}"
echo ""

# 2. SCRIPTS VERSCHIEBEN
echo -e "${YELLOW}📦 Schritt 2: Scripts verschieben${NC}"

if [ -f "sync_sales.py" ]; then
    mv sync_sales.py scripts/sync/
    echo -e "${GREEN}✓ sync_sales.py verschoben${NC}"
fi

if [ -f "sync_employees.py" ]; then
    mv sync_employees.py scripts/sync/
    echo -e "${GREEN}✓ sync_employees.py verschoben${NC}"
fi

if [ -f "import_stellantis.py" ]; then
    mv import_stellantis.py scripts/sync/
    echo -e "${GREEN}✓ import_stellantis.py verschoben${NC}"
fi

echo ""

# 3. NEUER CRONTAB
echo -e "${YELLOW}⏰ Schritt 3: Crontab aktualisieren${NC}"

cat > /tmp/new_crontab_tag43.txt << 'CRONEOF'
# ============================================================================
# GREINER PORTAL - CRON JOBS (TAG 43 - Aufgeräumt)
# ============================================================================

# Verkauf Sync - stündlich von 7-18 Uhr
0 7-18 * * * cd /opt/greiner-portal && venv/bin/python3 scripts/sync/sync_sales.py >> logs/sync_sales.log 2>&1

# Stellantis Import - stündlich von 7-18 Uhr
0 7-18 * * * cd /opt/greiner-portal && venv/bin/python3 scripts/sync/import_stellantis.py >> logs/stellantis_import.log 2>&1

# Employee Sync - täglich 6 Uhr
0 6 * * * cd /opt/greiner-portal && venv/bin/python3 scripts/sync/sync_employees.py --real >> logs/employee_sync.log 2>&1

# Bank-PDFs Import - täglich 8:30 Uhr
30 8 * * * cd /opt/greiner-portal && venv/bin/python3 scripts/imports/import_kontoauszuege.py >> logs/bank_import.log 2>&1

# Santander Import - täglich 8 Uhr
0 8 * * * cd /opt/greiner-portal && venv/bin/python3 scripts/imports/import_santander_bestand.py >> logs/santander_import.log 2>&1

# Hyundai Finance Import - täglich 9 Uhr
0 9 * * * cd /opt/greiner-portal && venv/bin/python3 scripts/imports/import_hyundai_finance.py >> logs/hyundai_import.log 2>&1

# DB Backup - stündlich
0 * * * * cd /opt/greiner-portal && cp data/greiner_controlling.db data/greiner_controlling.db.backup_auto_$(date +\%H00) 2>/dev/null

# Alte Backups löschen - täglich 2:30 Uhr
30 2 * * * find /opt/greiner-portal/data -name "*.backup_auto_*" -mtime +7 -delete 2>/dev/null
CRONEOF

crontab /tmp/new_crontab_tag43.txt
echo -e "${GREEN}✓ Crontab aktualisiert${NC}"
rm /tmp/new_crontab_tag43.txt
echo ""

# 4. VALIDIERUNG
echo -e "${YELLOW}✅ Schritt 4: Validierung${NC}"
echo ""
echo -e "${BLUE}Neue Verzeichnisstruktur:${NC}"
ls -lh scripts/sync/*.py | grep -E "(sync_sales|sync_employees|import_stellantis)"
echo ""

echo -e "${BLUE}Aktiver Crontab:${NC}"
crontab -l | grep -E "(sync_sales|sync_employees|import_stellantis)" | head -3
echo ""

# 5. TEST
echo -e "${YELLOW}🧪 Schritt 5: Quick-Test${NC}"
echo "Teste ob Scripts noch funktionieren..."

if python3 scripts/sync/sync_sales.py --help 2>&1 | grep -q "error"; then
    echo -e "${RED}⚠️  sync_sales.py könnte Probleme haben${NC}"
else
    echo -e "${GREEN}✓ sync_sales.py OK${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ CLEANUP ERFOLGREICH!                                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 Zusammenfassung:${NC}"
echo "  • Scripts verschoben nach scripts/sync/"
echo "  • Crontab aktualisiert"
echo "  • Backup erstellt: cron_backup_tag43_*.txt"
echo ""
echo -e "${YELLOW}💡 Nächster Cron-Run testet ob alles funktioniert!${NC}"
echo ""
