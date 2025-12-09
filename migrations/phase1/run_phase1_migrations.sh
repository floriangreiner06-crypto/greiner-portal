#!/bin/bash
# ============================================================================
# PHASE 1 MIGRATION - MASTER SCRIPT
# ============================================================================
# Beschreibung: Führt alle Phase 1 Migrationen nacheinander aus
# Verwendung: ./run_phase1_migrations.sh
# ============================================================================

set -e  # Beende bei Fehler

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DB_PATH="/opt/greiner-portal/data/greiner_controlling.db"

echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}PHASE 1 MIGRATION - BANKENSPIEGEL 3.0${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

# Prüfe ob Datenbank existiert
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}❌ ERROR: Datenbank nicht gefunden: $DB_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Datenbank gefunden: $DB_PATH${NC}"
echo ""

# Backup erstellen
BACKUP_PATH="$DB_PATH.backup_phase1_$(date +%Y%m%d_%H%M%S)"
echo -e "${YELLOW}📦 Erstelle Backup: $BACKUP_PATH${NC}"
cp "$DB_PATH" "$BACKUP_PATH"
echo -e "${GREEN}✅ Backup erstellt${NC}"
echo ""

# Migration 001: Kontostand-Historie
echo -e "${YELLOW}🔄 Migration 001: kontostand_historie${NC}"
sqlite3 "$DB_PATH" < 001_add_kontostand_historie.sql
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration 001 erfolgreich${NC}"
else
    echo -e "${RED}❌ Migration 001 fehlgeschlagen${NC}"
    exit 1
fi
echo ""

# Migration 002: Kreditlinien
echo -e "${YELLOW}🔄 Migration 002: kreditlinien${NC}"
sqlite3 "$DB_PATH" < 002_add_kreditlinien.sql
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration 002 erfolgreich${NC}"
else
    echo -e "${RED}❌ Migration 002 fehlgeschlagen${NC}"
    exit 1
fi
echo ""

# Migration 003: Kategorien
echo -e "${YELLOW}🔄 Migration 003: kategorien${NC}"
sqlite3 "$DB_PATH" < 003_add_kategorien.sql
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration 003 erfolgreich${NC}"
else
    echo -e "${RED}❌ Migration 003 fehlgeschlagen${NC}"
    exit 1
fi
echo ""

# Migration 004: PDF-Imports
echo -e "${YELLOW}🔄 Migration 004: pdf_imports${NC}"
sqlite3 "$DB_PATH" < 004_add_pdf_imports.sql
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration 004 erfolgreich${NC}"
else
    echo -e "${RED}❌ Migration 004 fehlgeschlagen${NC}"
    exit 1
fi
echo ""

# Migration 005: Views
echo -e "${YELLOW}🔄 Migration 005: reporting_views${NC}"
sqlite3 "$DB_PATH" < 005_add_views.sql
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration 005 erfolgreich${NC}"
else
    echo -e "${RED}❌ Migration 005 fehlgeschlagen${NC}"
    exit 1
fi
echo ""

# Finale Validierung
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}VALIDIERUNG${NC}"
echo -e "${YELLOW}============================================================================${NC}"

sqlite3 "$DB_PATH" << EOF
.mode column
.headers on

SELECT 'TABELLEN-ÜBERSICHT' as Kategorie;
SELECT name as Tabelle FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;

SELECT '';
SELECT 'VIEWS-ÜBERSICHT' as Kategorie;
SELECT name as View FROM sqlite_master WHERE type='view' ORDER BY name;

SELECT '';
SELECT 'DATEN-STATISTIK' as Kategorie;
SELECT 
    (SELECT COUNT(*) FROM banken) as Banken,
    (SELECT COUNT(*) FROM konten) as Konten,
    (SELECT COUNT(*) FROM transaktionen) as Transaktionen,
    (SELECT COUNT(*) FROM kontostand_historie) as Kontostände,
    (SELECT COUNT(*) FROM kreditlinien) as Kreditlinien,
    (SELECT COUNT(*) FROM kategorien) as Kategorien,
    (SELECT COUNT(*) FROM pdf_imports) as PDF_Imports;
EOF

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}🎉 PHASE 1 MIGRATION ERFOLGREICH ABGESCHLOSSEN!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "Backup verfügbar unter: ${YELLOW}$BACKUP_PATH${NC}"
echo ""
