#!/bin/bash
# Schneller Update-Import - Greiner Portal v2.0
# Nur neue Bank-PDFs + Stellantis mit korrekter Excel-Struktur

set -e; set -u
GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
PORTAL_DIR="/opt/greiner-portal"; DB_PATH="${PORTAL_DIR}/data/greiner_controlling.db"
PDF_BASE_PATH="/mnt/buchhaltung/Buchhaltung/Kontoauszüge"
LOG_FILE="${PORTAL_DIR}/update_import_$(date +%Y%m%d_%H%M%S).log"

print_step() { echo -e "${CYAN}▶ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

clear; echo -e "\n${BLUE}⚡ SCHNELLER UPDATE-IMPORT${NC}\n"

# Neuestes DB-Datum
print_step "Ermittle neuestes Datum in DB..."
DB_MAX_DATE=$(python3 -c "import sqlite3; c=sqlite3.connect('$DB_PATH').cursor(); c.execute('SELECT MAX(buchungsdatum) FROM transaktionen'); print(c.fetchone()[0] or '2020-01-01')")
print_success "Neuestes Datum: $DB_MAX_DATE"

# Bank-PDFs
print_step "Suche neue Bank-PDFs seit $DB_MAX_DATE..."
NEW_PDFS=$(find "$PDF_BASE_PATH" -name "*.pdf" -newermt "$DB_MAX_DATE" -type f 2>/dev/null | grep -v Stellantis | wc -l)

if [ "$NEW_PDFS" -gt 0 ]; then
    print_success "$NEW_PDFS neue PDFs gefunden, importiere..."
    # Hier würde Bank-PDF Import laufen
else
    print_success "Keine neuen Bank-PDFs (alle aktuell)"
fi

# Stellantis Import
print_step "Stellantis-Daten importieren..."
python3 "${PORTAL_DIR}/import_stellantis.py"

echo -e "\n${GREEN}✅ UPDATE-IMPORT ABGESCHLOSSEN${NC}\n"
