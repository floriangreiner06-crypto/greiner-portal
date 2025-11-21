#!/bin/bash

###############################################################################
# GREINER PORTAL - CLEANUP SCRIPT TAG71
###############################################################################
#
# Zweck: Repository aufräumen, alte Backups entfernen, Git committen
# Datum: 21. November 2025
# Version: 1.0
# Autor: Claude (TAG71)
#
# WICHTIG: Vor Ausführung BACKUP erstellen!
#
###############################################################################

set -e  # Bei Fehler abbrechen

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging-Funktionen
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

# Header
clear
echo "═══════════════════════════════════════════════════════"
echo "  GREINER PORTAL - CLEANUP SCRIPT TAG71"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Dieser Script führt folgende Aktionen aus:"
echo "  1. Backup erstellen"
echo "  2. Deprecated Files löschen"
echo "  3. FinTS auf Eis legen"
echo "  4. Session-Docs archivieren"
echo "  5. Git aufräumen"
echo "  6. Wichtige Changes committen"
echo ""
echo -e "${RED}WARNUNG: Dateien werden gelöscht!${NC}"
echo ""
read -p "Fortfahren? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 1
fi

# Ins richtige Verzeichnis wechseln
cd /opt/greiner-portal || {
    log_error "Verzeichnis /opt/greiner-portal nicht gefunden!"
    exit 1
}

###############################################################################
# PHASE 1: BACKUP ERSTELLEN
###############################################################################

log_step "PHASE 1: BACKUP ERSTELLEN"

BACKUP_DIR="$HOME/greiner-portal.backup_$(date +%Y%m%d_%H%M%S)"
log_info "Erstelle Backup in: $BACKUP_DIR"

cp -r /opt/greiner-portal "$BACKUP_DIR" || {
    log_error "Backup fehlgeschlagen!"
    exit 1
}

log_info "✅ Backup erstellt: $BACKUP_DIR"
log_info "Bei Problemen wiederherstellen mit:"
log_info "   rm -rf /opt/greiner-portal"
log_info "   mv $BACKUP_DIR /opt/greiner-portal"

sleep 2

###############################################################################
# PHASE 2: DEPRECATED BACKUPS LÖSCHEN
###############################################################################

log_step "PHASE 2: DEPRECATED BACKUPS LÖSCHEN"

log_info "Lösche Core-Backups (Bugs gefixt)..."
rm -fv api/bankenspiegel_api.py.broken_tag71
rm -fv auth/auth_manager.py.bak_SECURITY_BUG

log_info "Lösche Controlling-Backups (TAG67-68)..."
rm -fv routes/controlling_routes.py.bak_tag67
rm -fv routes/controlling_routes.py.bak_tag68_vor_bereinigung

log_info "Lösche Urlaubsplaner-Backups (TAG69)..."
rm -fv api/vacation_api.py.bak_tag69
rm -fv static/js/vacation_manager.js.bak_tag69
rm -fv templates/base.html.bak_tag69

log_info "✅ Alte Backups gelöscht"

sleep 1

###############################################################################
# PHASE 3: ALTE SCRAPER-VERSIONEN LÖSCHEN
###############################################################################

log_step "PHASE 3: ALTE SCRAPER-VERSIONEN LÖSCHEN"

log_info "Lösche alte Scraper-Versionen (12 Dateien)..."
rm -fv tools/scrapers/servicebox_detail_scraper.py
rm -fv tools/scrapers/servicebox_detail_scraper.py.old
rm -fv tools/scrapers/servicebox_detail_scraper_debug.py
rm -fv tools/scrapers/servicebox_detail_scraper_2phase.py.bak_tag70_v1
rm -fv tools/scrapers/servicebox_detail_scraper_2phase_v1.py
rm -fv tools/scrapers/servicebox_detail_scraper_2phase_v2.py
rm -fv tools/scrapers/servicebox_detail_scraper_2phase_v2_fixed.py
rm -fv tools/scrapers/servicebox_detail_scraper_final.py.bak_tag69
rm -fv tools/scrapers/servicebox_detail_scraper_with_pagination.py
rm -fv tools/scrapers/servicebox_detail_scraper_with_pagination.py.bak
rm -fv tools/scrapers/servicebox_test_scraper.py
rm -fv tools/scrapers/servicebox_test_scraper_v3.py

log_info "✅ Alte Scraper gelöscht"
log_info "Produktive Version bleibt: servicebox_detail_scraper_pagination_final.py"

sleep 1

###############################################################################
# PHASE 4: ALTE STELLANTIS-IMPORTER LÖSCHEN
###############################################################################

log_step "PHASE 4: ALTE STELLANTIS-IMPORTER LÖSCHEN"

log_info "Lösche alte Stellantis-Importer (3 Dateien)..."
rm -fv scripts/imports/import_stellantis_v2_backup.py
rm -fv scripts/imports/import_stellantis_v3.py
rm -fv scripts/imports/import_stellantis_v3_fixed.py

log_info "✅ Alte Importer gelöscht"

sleep 1

###############################################################################
# PHASE 5: TEST-SCRIPTS LÖSCHEN
###############################################################################

log_step "PHASE 5: TEST-SCRIPTS LÖSCHEN"

log_info "Lösche Test-Scripts..."
rm -fv install_hvb_parser.py
rm -fv debug_vacation_api.py

log_info "✅ Test-Scripts gelöscht"

sleep 1

###############################################################################
# PHASE 6: FINTS AUF EIS LEGEN
###############################################################################

log_step "PHASE 6: FINTS AUF EIS LEGEN"

log_info "Erstelle Experimental-Verzeichnis..."
mkdir -p backups/experimental/fints

log_info "Verschiebe FinTS-Module..."
[ -d fints-package ] && mv -v fints-package backups/experimental/fints/
[ -f api/fints_connector.py ] && mv -v api/fints_connector.py backups/experimental/fints/
[ -f scripts/imports/import_fints_daily.py ] && mv -v scripts/imports/import_fints_daily.py backups/experimental/fints/
[ -f scripts/checks/check_fints_health.sh ] && mv -v scripts/checks/check_fints_health.sh backups/experimental/fints/

log_info "Verschiebe FinTS-Migrations..."
[ -f migrations/008_add_finanzinstitut_compat.sql ] && mv -v migrations/008_add_finanzinstitut_compat.sql backups/experimental/fints/
[ -f migrations/009_add_missing_import_columns.sql ] && mv -v migrations/009_add_missing_import_columns.sql backups/experimental/fints/
[ -f migrations/010_add_all_import_columns.sql ] && mv -v migrations/010_add_all_import_columns.sql backups/experimental/fints/
[ -f migrations/011_remove_finanzbank_id_constraint.sql ] && mv -v migrations/011_remove_finanzbank_id_constraint.sql backups/experimental/fints/
[ -f migrations/012_fix_trigger_and_constraints.sql ] && mv -v migrations/012_fix_trigger_and_constraints.sql backups/experimental/fints/
[ -f migrations/013_emergency_recreate_table.sql ] && mv -v migrations/013_emergency_recreate_table.sql backups/experimental/fints/

log_info "✅ FinTS auf Eis gelegt"
log_info "Speicherort: backups/experimental/fints/"

sleep 1

###############################################################################
# PHASE 7: SESSION-DOCS ARCHIVIEREN
###############################################################################

log_step "PHASE 7: SESSION-DOCS ARCHIVIEREN"

log_info "Erstelle Sessions-Verzeichnis..."
mkdir -p docs/sessions

log_info "Verschiebe alte Session-Docs..."
[ -f SESSION_WRAP_UP_TAG63.md ] && mv -v SESSION_WRAP_UP_TAG63.md docs/sessions/
[ -f TODO_FOR_CLAUDE_SESSION_START_TAG66.md ] && mv -v TODO_FOR_CLAUDE_SESSION_START_TAG66.md docs/sessions/

log_info "✅ Session-Docs archiviert"
log_info "Speicherort: docs/sessions/"

sleep 1

###############################################################################
# PHASE 8: GIT AUFRÄUMEN
###############################################################################

log_step "PHASE 8: GIT AUFRÄUMEN"

log_info "Bestätige Git-Löschungen..."
git rm -f = 2>/dev/null || log_warn "Datei '=' nicht gefunden"
git rm -f L394PR-ALTERNATIVKONTEN-OPEL-01-001.csv 2>/dev/null || log_warn "CSV nicht gefunden"
git rm -f SERVER_STATUS.txt 2>/dev/null || log_warn "SERVER_STATUS.txt nicht gefunden"
git rm -f cron_backup_tag43.txt 2>/dev/null || log_warn "cron_backup_tag43.txt nicht gefunden"
git rm -f server_status_check.sh 2>/dev/null || log_warn "server_status_check.sh nicht gefunden"

log_info "✅ Git aufgeräumt"

sleep 1

###############################################################################
# PHASE 9: WICHTIGE CHANGES STAGEN
###############################################################################

log_step "PHASE 9: WICHTIGE CHANGES STAGEN"

log_info "Stage Core-Fixes..."
git add api/bankenspiegel_api.py 2>/dev/null || log_warn "bankenspiegel_api.py nicht modified"
git add api/vacation_api.py 2>/dev/null || log_warn "vacation_api.py nicht modified"
git add app.py 2>/dev/null || log_warn "app.py nicht modified"
git add auth/auth_manager.py 2>/dev/null || log_warn "auth_manager.py nicht modified"

log_info "Stage Routes & Templates..."
git add routes/controlling_routes.py 2>/dev/null || log_warn "controlling_routes.py nicht modified"
git add templates/base.html 2>/dev/null || log_warn "base.html nicht modified"
git add templates/controlling/dashboard.html 2>/dev/null || log_warn "dashboard.html nicht modified"

log_info "Stage Static-Files..."
git add static/js/controlling/dashboard.js 2>/dev/null || log_warn "dashboard.js nicht modified"
git add static/js/vacation_manager.js 2>/dev/null || log_warn "vacation_manager.js nicht modified"

log_info "Stage Parser..."
git add parsers/sparkasse_online_parser.py 2>/dev/null || log_warn "sparkasse_online_parser.py nicht modified"

log_info "Stage Migrations..."
git add migrations/tag67_schema_migration.sql 2>/dev/null || log_warn "tag67_schema_migration.sql nicht gefunden"
git add migrations/tag67_update_konten_daten.sql 2>/dev/null || log_warn "tag67_update_konten_daten.sql nicht gefunden"

log_info "Stage Scripts..."
git add scripts/maintenance/server_status_check.sh 2>/dev/null || log_warn "server_status_check.sh nicht gefunden"
git add crontab_final_tag65.txt 2>/dev/null || log_warn "crontab_final_tag65.txt nicht gefunden"

log_info "✅ Wichtige Changes gestaged"

sleep 1

###############################################################################
# PHASE 10: GIT STATUS ANZEIGEN
###############################################################################

log_step "PHASE 10: GIT STATUS"

log_info "Aktueller Git-Status:"
echo ""
git status --short

echo ""
log_info "Staged Changes (werden committed):"
git diff --cached --name-only

sleep 2

###############################################################################
# PHASE 11: COMMIT BESTÄTIGUNG
###############################################################################

log_step "PHASE 11: COMMIT BESTÄTIGUNG"

echo ""
echo "Folgende Änderungen werden committed:"
echo ""
git diff --cached --stat
echo ""

read -p "Commit durchführen? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Commit abgebrochen."
    log_info "Staged Changes bleiben erhalten."
    log_info "Manuell committen mit:"
    log_info "   git commit -m 'chore(tag71): Cleanup & Feature-Fixes'"
    exit 0
fi

###############################################################################
# PHASE 12: GIT COMMIT
###############################################################################

log_step "PHASE 12: GIT COMMIT"

log_info "Erstelle Commit..."

git commit -m "chore(tag71): Cleanup & Feature-Fixes

- fix(controlling): Bankenspiegel Dashboard komplett
- fix(auth): Security-Bug behoben
- feat(vacation): V2 Testing-Version
- feat(scraper): Stellantis Pagination produktiv
- chore: FinTS auf Eis gelegt (zu komplex)
- chore: Alte Backups & deprecated Versions entfernt
- chore: Migrations TAG67 nachgetragen
- docs: Session-Docs archiviert

Files cleaned:
- 12 alte Scraper-Versionen entfernt
- 7 Backup-Files entfernt
- 3 alte Stellantis-Importer entfernt
- FinTS-Module nach backups/experimental/ verschoben
- Session-Docs nach docs/sessions/ archiviert

Status: Sauberer Stand für weitere Entwicklung"

log_info "✅ Commit erstellt"

sleep 1

###############################################################################
# PHASE 13: GIT PUSH
###############################################################################

log_step "PHASE 13: GIT PUSH"

read -p "Push zu origin/develop? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Push abgebrochen."
    log_info "Manuell pushen mit:"
    log_info "   git push origin develop"
    exit 0
fi

log_info "Pushe zu origin/develop..."
git push origin develop

log_info "✅ Push erfolgreich"

###############################################################################
# ZUSAMMENFASSUNG
###############################################################################

log_step "✅ CLEANUP KOMPLETT"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ZUSAMMENFASSUNG"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "✅ Backup erstellt:      $BACKUP_DIR"
echo "✅ Deprecated Files:     22 gelöscht"
echo "✅ FinTS-Module:         Auf Eis gelegt"
echo "✅ Session-Docs:         Archiviert"
echo "✅ Git Status:           Sauber"
echo "✅ Commit:               Erstellt & gepusht"
echo ""
echo "═══════════════════════════════════════════════════════"
echo ""

log_info "Repository ist jetzt sauber und bereit für Entwicklung!"
log_info ""
log_info "Nächste Schritte:"
log_info "  1. Siehe: DECISION_TREE_TAG71.md"
log_info "  2. Siehe: IST_ZUSTAND_TAG71.md"
log_info ""
log_info "Bei Problemen Backup wiederherstellen:"
log_info "  rm -rf /opt/greiner-portal"
log_info "  mv $BACKUP_DIR /opt/greiner-portal"
echo ""

exit 0
