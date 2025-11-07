#!/bin/bash
################################################################################
# Bank-PDF Import Script - Greiner Portal
# ========================================
# Automatisierter Import neuer Bank-PDFs seit 31.10.2025 mit Validierung
#
# Usage: ./import_bank_pdfs_seit_31_10.sh
#
# Autor: Claude AI
# Datum: 07.11.2025
# Version: 1.0
################################################################################

set -e  # Exit bei Fehler
set -u  # Exit bei undefined variables

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Konfiguration
PORTAL_DIR="/opt/greiner-portal"
DB_PATH="${PORTAL_DIR}/data/greiner_controlling.db"
SHARE_PATH="/mnt/buchhaltung"
PDF_BASE_PATH="${SHARE_PATH}/Buchhaltung/Kontoauszüge"
MIN_DATE="2025-10-31"
VENV_PATH="${PORTAL_DIR}/venv"
LOG_FILE="${PORTAL_DIR}/import_$(date +%Y%m%d_%H%M%S).log"

# Funktionen
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${NC}  $1${NC}"
}

# Logging-Funktion
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fehlerbehandlung
error_exit() {
    print_error "FEHLER: $1"
    log "ERROR: $1"
    exit 1
}

################################################################################
# HAUPTPROGRAMM
################################################################################

clear
print_header "🏦 BANK-PDF IMPORT - GREINER PORTAL"
log "=== Import-Session gestartet ==="

# Schritt 1: Umgebung prüfen
print_step "Schritt 1/7: Umgebung prüfen"

# Verzeichnis wechseln
if [ ! -d "$PORTAL_DIR" ]; then
    error_exit "Portal-Verzeichnis nicht gefunden: $PORTAL_DIR"
fi
cd "$PORTAL_DIR" || error_exit "Kann nicht zu $PORTAL_DIR wechseln"
print_success "Portal-Verzeichnis: $PORTAL_DIR"
log "Working directory: $PORTAL_DIR"

# Datenbank prüfen
if [ ! -f "$DB_PATH" ]; then
    error_exit "Datenbank nicht gefunden: $DB_PATH"
fi
print_success "Datenbank gefunden: $DB_PATH"
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
print_info "Datenbank-Größe: $DB_SIZE"
log "Database size: $DB_SIZE"

# Virtual Environment prüfen
if [ ! -d "$VENV_PATH" ]; then
    error_exit "Virtual Environment nicht gefunden: $VENV_PATH"
fi
print_success "Virtual Environment gefunden"

# Share-Mount prüfen
print_step "Schritt 2/7: Share-Zugriff prüfen"
if ! mount | grep -q "srvrdb01"; then
    print_warning "Share nicht gemountet!"
    print_info "Bitte manuell mounten mit:"
    print_info "sudo mount -t cifs //srvrdb01/Allgemein /mnt/buchhaltung \\"
    print_info "  -o username=Administrator,domain=auto-greiner.de,vers=3.0"
    error_exit "Share muss gemountet sein"
fi
print_success "Share gemountet: $SHARE_PATH"
log "Share mount verified"

# PDF-Verzeichnis prüfen
if [ ! -d "$PDF_BASE_PATH" ]; then
    error_exit "PDF-Verzeichnis nicht gefunden: $PDF_BASE_PATH"
fi
print_success "PDF-Verzeichnis gefunden"

# Schritt 3: Neue PDFs finden
print_step "Schritt 3/7: Neue PDFs seit ${MIN_DATE} suchen"
print_info "Suche läuft (kann einige Sekunden dauern)..."

# PDFs zählen (ohne Stellantis)
NEW_PDF_COUNT=$(find "$PDF_BASE_PATH" \
    -name "*.pdf" \
    -newermt "$MIN_DATE" \
    -type f \
    2>/dev/null | grep -v Stellantis | wc -l)

if [ "$NEW_PDF_COUNT" -eq 0 ]; then
    print_warning "Keine neuen PDFs seit ${MIN_DATE} gefunden"
    print_info "Import wird übersprungen"
    log "No new PDFs found since $MIN_DATE"
    exit 0
fi

print_success "Neue PDFs gefunden: $NEW_PDF_COUNT"
log "Found $NEW_PDF_COUNT new PDFs"

# Erste 10 PDFs anzeigen
print_info "\nBeispiel-PDFs (erste 10):"
find "$PDF_BASE_PATH" \
    -name "*.pdf" \
    -newermt "$MIN_DATE" \
    -type f \
    2>/dev/null | grep -v Stellantis | head -10 | while read -r pdf; do
    basename=$(basename "$pdf")
    print_info "  • $basename"
done

# Schritt 4: Backup erstellen
print_step "Schritt 4/7: Datenbank-Backup erstellen"

BACKUP_FILE="${DB_PATH}.backup_import_$(date +%Y%m%d_%H%M%S)"
cp "$DB_PATH" "$BACKUP_FILE" || error_exit "Backup fehlgeschlagen"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
print_success "Backup erstellt: $(basename $BACKUP_FILE)"
print_info "Backup-Größe: $BACKUP_SIZE"
log "Backup created: $BACKUP_FILE"

# Transaktionen VOR Import zählen
TRANS_BEFORE=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM transaktionen')
print(c.fetchone()[0])
conn.close()
" 2>/dev/null)

print_info "Transaktionen vor Import: $(printf "%'d" $TRANS_BEFORE)"
log "Transactions before import: $TRANS_BEFORE"

# Schritt 5: Virtual Environment aktivieren und Import starten
print_step "Schritt 5/7: PDF-Import starten"

source "$VENV_PATH/bin/activate" || error_exit "Kann venv nicht aktivieren"
print_success "Virtual Environment aktiviert"

# Import-Script prüfen
if [ ! -f "${PORTAL_DIR}/import_bank_pdfs.py" ]; then
    error_exit "Import-Script nicht gefunden: import_bank_pdfs.py"
fi
print_success "Import-Script gefunden"

print_info "\n${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
print_info "${YELLOW}Import läuft... (Dies kann einige Minuten dauern)${NC}"
print_info "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}\n"

# Import ausführen mit Fehlerbehandlung
if python3 import_bank_pdfs.py import "$PDF_BASE_PATH" --min-year 2024 2>&1 | tee -a "$LOG_FILE"; then
    print_success "Import erfolgreich abgeschlossen"
    log "Import completed successfully"
else
    IMPORT_EXIT_CODE=$?
    print_warning "Import mit Warnungen beendet (Exit Code: $IMPORT_EXIT_CODE)"
    print_info "Prüfe bank_import.log für Details"
    log "Import finished with warnings (exit code: $IMPORT_EXIT_CODE)"
fi

# Schritt 6: Import-Ergebnis prüfen
print_step "Schritt 6/7: Import-Ergebnis analysieren"

# Transaktionen NACH Import
TRANS_AFTER=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM transaktionen')
print(c.fetchone()[0])
conn.close()
" 2>/dev/null)

TRANS_NEW=$((TRANS_AFTER - TRANS_BEFORE))

print_success "Transaktionen nach Import: $(printf "%'d" $TRANS_AFTER)"
print_info "Neue Transaktionen importiert: $(printf "%'d" $TRANS_NEW)"
log "Transactions after import: $TRANS_AFTER (new: $TRANS_NEW)"

# Neue Transaktionen nach Datum
print_info "\nNeue Transaktionen nach Datum (Top 10):"
python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
c = conn.cursor()
c.execute("""
    SELECT buchungsdatum, COUNT(*), SUM(ABS(betrag))
    FROM transaktionen
    WHERE buchungsdatum >= '2024-10-31'
    GROUP BY buchungsdatum
    ORDER BY buchungsdatum DESC
    LIMIT 10
""")
print("\n  Datum        | Anzahl | Betrag (€)")
print("  " + "-" * 45)
for datum, cnt, summe in c.fetchall():
    print(f"  {datum} | {cnt:6d} | {summe:12,.2f}")
conn.close()
PYEOF

# Schritt 7: Salden validieren
print_step "Schritt 7/7: Salden validieren"

python3 << 'PYEOF'
import sqlite3

conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
c = conn.cursor()

print("\n" + "="*80)
print("🎯 AKTUELLE SALDEN-VALIDIERUNG")
print("="*80 + "\n")

# Bank-Konten
print("📊 BANK-KONTEN:\n")
c.execute("""
    SELECT 
        k.id,
        b.bank_name,
        k.kontoname,
        (SELECT saldo_nach_buchung 
         FROM transaktionen 
         WHERE konto_id = k.id 
         ORDER BY buchungsdatum DESC, id DESC 
         LIMIT 1) as saldo,
        (SELECT buchungsdatum 
         FROM transaktionen 
         WHERE konto_id = k.id 
         ORDER BY buchungsdatum DESC, id DESC 
         LIMIT 1) as datum
    FROM konten k
    JOIN banken b ON k.bank_id = b.id
    WHERE k.aktiv = 1
    ORDER BY b.bank_name, k.kontoname
""")

bank_total = 0
for kid, bank, kname, saldo, datum in c.fetchall():
    bank_total += (saldo or 0)
    print(f"[{kid:2d}] {bank:<25} {kname:<30} {(saldo or 0):>15,.2f} € ({datum})")

print(f"\n{'─'*80}")
print(f"{'Bank-Konten GESAMT:':<60} {bank_total:>15,.2f} €")

# Fahrzeugfinanzierungen
c.execute("SELECT COUNT(*), SUM(aktueller_saldo) FROM fahrzeugfinanzierungen")
fz_count, fz_saldo = c.fetchone()
print(f"{'Fahrzeugfinanzierungen:':<60} {fz_saldo:>15,.2f} €")
print(f"{'─'*80}")

# Gesamtvermögen
gesamt = bank_total + (fz_saldo or 0)
print(f"{'💰 GESAMT-VERMÖGEN:':<60} {gesamt:>15,.2f} €\n")

# Statistiken
c.execute("SELECT COUNT(*) FROM transaktionen")
trans_count = c.fetchone()[0]
c.execute("SELECT MIN(buchungsdatum), MAX(buchungsdatum) FROM transaktionen")
min_date, max_date = c.fetchone()
c.execute("SELECT COUNT(*) FROM konten WHERE aktiv=1")
konto_count = c.fetchone()[0]

print("📈 DATENBANK-STATISTIK:")
print(f"  • Transaktionen gesamt: {trans_count:,}")
print(f"  • Zeitraum: {min_date} bis {max_date}")
print(f"  • Fahrzeuge (Stellantis): {fz_count}")
print(f"  • Bank-Konten aktiv: {konto_count}")

conn.close()
print("\n" + "="*80 + "\n")
PYEOF

# Zusammenfassung
print_header "✅ IMPORT ABGESCHLOSSEN"

echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}ZUSAMMENFASSUNG:${NC}"
echo -e "${GREEN}───────────────────────────────────────────────────────────────────${NC}"
echo -e "${GREEN}  • PDFs gefunden:          $NEW_PDF_COUNT${NC}"
echo -e "${GREEN}  • Transaktionen importiert: $(printf "%'d" $TRANS_NEW)${NC}"
echo -e "${GREEN}  • Transaktionen gesamt:    $(printf "%'d" $TRANS_AFTER)${NC}"
echo -e "${GREEN}  • Backup erstellt:        $(basename $BACKUP_FILE)${NC}"
echo -e "${GREEN}  • Log-Datei:              $(basename $LOG_FILE)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}\n"

log "=== Import-Session erfolgreich beendet ==="

# Logs anzeigen
print_info "Weitere Details in:"
print_info "  • Import-Log: $LOG_FILE"
print_info "  • Parser-Log: ${PORTAL_DIR}/bank_import.log"

# Nächste Schritte
print_info "\n📋 NÄCHSTE SCHRITTE:"
print_info "  1. Salden mit Excel-Bankenspiegel vergleichen"
print_info "  2. Plausibilitätsprüfung durchführen"
print_info "  3. Bei Problemen: Backup zurückspielen mit:"
print_info "     cp $(basename $BACKUP_FILE) greiner_controlling.db"

exit 0
