#!/bin/bash
# =============================================================================
# CLEANUP SCRIPT - TAG 90
# =============================================================================
# Räumt alte Backup-Dateien und nicht mehr benötigte Scripts auf
# 
# WICHTIG: Vor Ausführung prüfen! Dieses Script LÖSCHT Dateien!
#
# Verwendung:
#   1. Erst mit --dry-run prüfen was gelöscht würde
#   2. Dann ohne Flag ausführen
#
# Beispiel:
#   ./cleanup_tag90.sh --dry-run   # Nur anzeigen
#   ./cleanup_tag90.sh             # Wirklich löschen
# =============================================================================

cd /opt/greiner-portal

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo "🔍 DRY-RUN MODUS - Nichts wird gelöscht!"
    echo ""
fi

# Zähler initialisieren
DELETED=0
SKIPPED=0

delete_file() {
    local file="$1"
    if [ -f "$file" ]; then
        if [ "$DRY_RUN" == "true" ]; then
            echo "  [WÜRDE LÖSCHEN] $file"
        else
            rm -f "$file"
            echo "  [GELÖSCHT] $file"
        fi
        DELETED=$((DELETED + 1))
    else
        SKIPPED=$((SKIPPED + 1))
    fi
}

move_to_archive() {
    local file="$1"
    local archive_dir="$2"
    if [ -f "$file" ]; then
        mkdir -p "$archive_dir"
        if [ "$DRY_RUN" == "true" ]; then
            echo "  [WÜRDE VERSCHIEBEN] $file → $archive_dir/"
        else
            mv "$file" "$archive_dir/"
            echo "  [VERSCHOBEN] $file → $archive_dir/"
        fi
        DELETED=$((DELETED + 1))
    fi
}

echo "================================================================="
echo "🧹 CLEANUP TAG 90 - Alte Backups und nicht benötigte Dateien"
echo "================================================================="
echo ""

# -----------------------------------------------------------------------------
# 1. PARSERS - Backup-Dateien löschen
# -----------------------------------------------------------------------------
echo "📁 PARSERS - Backup-Dateien:"

delete_file "parsers/genobank_universal_parser.py.backup_20251114_090425"
delete_file "parsers/genobank_universal_parser.py.backup_before_fix"
delete_file "parsers/genobank_universal_parser.py.backup_tag58_endsaldo"
delete_file "parsers/genobank_universal_parser.py.broken_dict_version"
delete_file "parsers/genobank_universal_parser.py.uncommitted_backup"
delete_file "parsers/hypovereinsbank_parser.py.backup_before_endsaldo"
delete_file "parsers/parser_factory.py.backup_20251113_165831"
delete_file "parsers/parser_factory.py.backup_20251113_170755"
delete_file "parsers/parser_factory.py.backup_20251117"
delete_file "parsers/parser_factory.py.backup_alt"
delete_file "parsers/parser_factory.py.backup_detection_20251113_170452"
delete_file "parsers/parser_factory.py.backup_fix_20251113_170952"
delete_file "parsers/parser_factory.py.backup_order_20251113_170141"
delete_file "parsers/parser_factory.py.backup_vor_iban_fix"
delete_file "parsers/parser_factory.py.uncommitted_backup"
delete_file "parsers/sparkasse_parser.py.backup_tag60_old_format"
delete_file "parsers/vrbank_landau_parser.py.backup"
delete_file "parsers/vrbank_landau_parser.py.backup_sed_fail"
delete_file "parsers/vrbank_landau_parser.py.backup_tag59"
delete_file "parsers/vrbank_parser.py.backup_before_endsaldo"
delete_file "parsers/iban_parser_factory.py.backup_v1_1"

echo ""

# -----------------------------------------------------------------------------
# 2. SCRIPTS/IMPORTS - Backup-Dateien löschen
# -----------------------------------------------------------------------------
echo "📁 SCRIPTS/IMPORTS - Backup-Dateien:"

delete_file "scripts/imports/genobank_universal_parser.py.backup_20251112_085150"
delete_file "scripts/imports/genobank_universal_parser.py.before_startsaldo_fix"
delete_file "scripts/imports/import_bank_pdfs.py.backup"
delete_file "scripts/imports/import_hyundai_finance.py.backup"
delete_file "scripts/imports/import_kontoauszuege.py.backup2"
delete_file "scripts/imports/import_kontoauszuege.py.backup3"
delete_file "scripts/imports/import_kontoauszuege.py.backup_20251115_235938"
delete_file "scripts/imports/import_kontoauszuege.py.backup_before_complete_fix"
delete_file "scripts/imports/import_kontoauszuege.py.backup_before_dict_fix"
delete_file "scripts/imports/import_kontoauszuege.py.backup_before_dynamic_scan"
delete_file "scripts/imports/import_kontoauszuege.py.backup_before_factory_fix"
delete_file "scripts/imports/import_kontoauszuege.py.backup_final"
delete_file "scripts/imports/import_kontoauszuege.py.backup_tag40_2"
delete_file "scripts/imports/import_kontoauszuege.py.backup_tag40_final"
delete_file "scripts/imports/import_kontoauszuege.py.backup_vor_fix_20251115_234910"
delete_file "scripts/imports/import_kontoauszuege.py.broken"
delete_file "scripts/imports/import_mt940.py.backup_20251124_091320"
delete_file "scripts/imports/import_mt940.py.backup_20251124_091435"
delete_file "scripts/imports/import_mt940.py.backup_20251124_091510"
delete_file "scripts/imports/import_november_all_accounts_v2.py.backup"
delete_file "scripts/imports/import_november_all_accounts_v2.py.backup_20251114_084234"
delete_file "scripts/imports/import_santander_bestand.py.backup_20251201_142247"
delete_file "scripts/imports/import_santander_bestand.py.backup_vor_zinsen"
delete_file "scripts/imports/import_sparkasse_online.py.backup"
delete_file "scripts/imports/import_stellantis.py.backup_20251124_153550"
delete_file "scripts/imports/import_stellantis.py.backup_20251201_141127"
delete_file "scripts/imports/import_stellantis.py.backup_fix2_20251124_154008"
delete_file "scripts/imports/import_stellantis.py.backup_fix2_20251124_154102"

echo ""

# -----------------------------------------------------------------------------
# 3. DEPRECATED SCRIPTS - In Archiv verschieben
# -----------------------------------------------------------------------------
echo "📁 DEPRECATED SCRIPTS - Werden archiviert:"

mkdir -p backups/deprecated_scripts_tag90

# Alte November/Oktober Import Scripts (nicht mehr benötigt)
move_to_archive "scripts/imports/import_november_all_accounts_v2.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_november_all_tag15.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_november_fix.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_november_SIMPLE.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_oktober_november_2025.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_sparkasse_november.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_hypovereinsbank_november.py" "backups/deprecated_scripts_tag90"

# Alte 2025 Import Scripts (ersetzt durch import_mt940.py)
move_to_archive "scripts/imports/import_2025_clean.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_2025_v2_with_genobank.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_complete_2025.py" "backups/deprecated_scripts_tag90"

# Fix-Scripts (einmalig verwendet)
move_to_archive "scripts/imports/fix_import_script.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/fix_salden.py" "backups/deprecated_scripts_tag90"
move_to_archive "scripts/imports/import_sparkasse_online_fix.py" "backups/deprecated_scripts_tag90"

echo ""

# -----------------------------------------------------------------------------
# ZUSAMMENFASSUNG
# -----------------------------------------------------------------------------
echo "================================================================="
echo "📊 ZUSAMMENFASSUNG:"
echo "   Gelöscht/Verschoben: $DELETED Dateien"
echo "   Übersprungen (nicht gefunden): $SKIPPED Dateien"
echo "================================================================="

if [ "$DRY_RUN" == "true" ]; then
    echo ""
    echo "⚠️  Dies war ein DRY-RUN - keine Dateien wurden geändert!"
    echo "    Führe das Script ohne --dry-run aus um die Änderungen anzuwenden."
fi
