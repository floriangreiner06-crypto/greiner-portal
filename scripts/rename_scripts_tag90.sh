#!/bin/bash
# =============================================================================
# SCRIPT RENAME - TAG 90 (SICHER)
# =============================================================================
# Benennt Scripts logisch um für bessere Übersicht im Job-Scheduler.
# 
# SICHERHEIT:
# - Originale werden NICHT gelöscht, nur kopiert
# - Rollback-Script wird erstellt
# - Erst nach erfolgreichem Test alte Dateien archivieren
#
# Verwendung:
#   1. ./rename_scripts_tag90.sh --dry-run    # Nur anzeigen
#   2. ./rename_scripts_tag90.sh              # Ausführen
#   3. Testen ob alles läuft
#   4. ./rename_scripts_tag90.sh --cleanup    # Alte Dateien archivieren
# =============================================================================

cd /opt/greiner-portal

DRY_RUN=false
CLEANUP=false

if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo "🔍 DRY-RUN MODUS - Nichts wird geändert!"
    echo ""
elif [ "$1" == "--cleanup" ]; then
    CLEANUP=true
    echo "🧹 CLEANUP MODUS - Archiviere alte Dateien"
    echo ""
fi

# Zähler
COPIED=0
ERRORS=0

# Backup-Verzeichnis
BACKUP_DIR="backups/pre_rename_tag90"
ARCHIVE_DIR="backups/archived_scripts_tag90"

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

copy_script() {
    local src="$1"
    local dst="$2"
    
    if [ ! -f "$src" ]; then
        echo "  ❌ FEHLER: Quelle nicht gefunden: $src"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
    
    # Zielverzeichnis erstellen falls nötig
    local dst_dir=$(dirname "$dst")
    
    if [ "$DRY_RUN" == "true" ]; then
        echo "  [WÜRDE KOPIEREN] $src → $dst"
        COPIED=$((COPIED + 1))
        return 0
    fi
    
    mkdir -p "$dst_dir"
    cp "$src" "$dst"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ $src → $dst"
        COPIED=$((COPIED + 1))
    else
        echo "  ❌ FEHLER beim Kopieren: $src"
        ERRORS=$((ERRORS + 1))
    fi
}

archive_old() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        return 0
    fi
    
    if [ "$DRY_RUN" == "true" ]; then
        echo "  [WÜRDE ARCHIVIEREN] $file"
        return 0
    fi
    
    mkdir -p "$ARCHIVE_DIR"
    mv "$file" "$ARCHIVE_DIR/"
    echo "  📦 Archiviert: $file"
}

# =============================================================================
# HAUPTLOGIK
# =============================================================================

if [ "$CLEANUP" == "true" ]; then
    echo "================================================================="
    echo "🧹 ARCHIVIERE ALTE SCRIPTS (nach erfolgreichem Test)"
    echo "================================================================="
    echo ""
    
    # Alte Dateien die jetzt neue Namen haben
    archive_old "scripts/imports/import_all_bank_pdfs.py"
    archive_old "scripts/analysis/umsatz_bereinigung_production.py"
    archive_old "scripts/imports/import_santander_bestand.py"
    archive_old "scripts/imports/import_hyundai_finance.py"
    archive_old "scripts/imports/import_servicebox_to_db.py"
    archive_old "scripts/imports/import_teile_lieferscheine.py"
    archive_old "scripts/imports/sync_teile_locosoft.py"
    archive_old "scripts/sync/sync_fahrzeug_stammdaten.py"
    archive_old "scripts/sync/import_stellantis.py"
    archive_old "tools/scrapers/hyundai_bestandsliste_scraper.py"
    archive_old "tools/scrapers/servicebox_detail_scraper_v3_kommentar.py"
    archive_old "tools/scrapers/servicebox_detail_scraper_v3_master.py"
    archive_old "tools/scrapers/servicebox_locosoft_matcher.py"
    
    echo ""
    echo "✅ Cleanup abgeschlossen!"
    echo "   Archiv: $ARCHIVE_DIR/"
    exit 0
fi

echo "================================================================="
echo "📝 SCRIPT RENAME - TAG 90"
echo "================================================================="
echo ""

# -----------------------------------------------------------------------------
# SCHRITT 1: Backup der job_definitions.py
# -----------------------------------------------------------------------------
echo "📦 SCHRITT 1: Backup erstellen..."

if [ "$DRY_RUN" == "false" ]; then
    mkdir -p "$BACKUP_DIR"
    cp scheduler/job_definitions.py "$BACKUP_DIR/job_definitions.py.backup"
    echo "  ✅ Backup: $BACKUP_DIR/job_definitions.py.backup"
fi

echo ""

# -----------------------------------------------------------------------------
# SCHRITT 2: Neues Verzeichnis scripts/scrapers/ erstellen
# -----------------------------------------------------------------------------
echo "📁 SCHRITT 2: Verzeichnis scripts/scrapers/ erstellen..."

if [ "$DRY_RUN" == "false" ]; then
    mkdir -p scripts/scrapers
    touch scripts/scrapers/__init__.py
    echo "  ✅ scripts/scrapers/ erstellt"
else
    echo "  [WÜRDE ERSTELLEN] scripts/scrapers/"
fi

echo ""

# -----------------------------------------------------------------------------
# SCHRITT 3: Scripts kopieren (mit neuen Namen)
# -----------------------------------------------------------------------------
echo "📋 SCHRITT 3: Scripts kopieren..."
echo ""

echo "--- IMPORTS ---"
copy_script "scripts/imports/import_all_bank_pdfs.py" "scripts/imports/import_hvb_pdf.py"
copy_script "scripts/imports/import_santander_bestand.py" "scripts/imports/import_santander.py"
copy_script "scripts/imports/import_hyundai_finance.py" "scripts/imports/import_hyundai.py"
copy_script "scripts/imports/import_servicebox_to_db.py" "scripts/imports/import_servicebox.py"
copy_script "scripts/imports/import_teile_lieferscheine.py" "scripts/imports/import_teile.py"
# Stellantis von sync nach imports verschieben
copy_script "scripts/sync/import_stellantis.py" "scripts/imports/import_stellantis.py"

echo ""
echo "--- SYNC ---"
copy_script "scripts/imports/sync_teile_locosoft.py" "scripts/sync/sync_teile.py"
copy_script "scripts/sync/sync_fahrzeug_stammdaten.py" "scripts/sync/sync_stammdaten.py"

echo ""
echo "--- ANALYSIS ---"
copy_script "scripts/analysis/umsatz_bereinigung_production.py" "scripts/analysis/umsatz_bereinigung.py"

echo ""
echo "--- SCRAPERS (neu aus tools/scrapers/) ---"
copy_script "tools/scrapers/hyundai_bestandsliste_scraper.py" "scripts/scrapers/scrape_hyundai.py"
copy_script "tools/scrapers/servicebox_detail_scraper_v3_kommentar.py" "scripts/scrapers/scrape_servicebox.py"
copy_script "tools/scrapers/servicebox_detail_scraper_v3_master.py" "scripts/scrapers/scrape_servicebox_full.py"
copy_script "tools/scrapers/servicebox_locosoft_matcher.py" "scripts/scrapers/match_servicebox.py"

echo ""

# -----------------------------------------------------------------------------
# SCHRITT 4: Zusammenfassung
# -----------------------------------------------------------------------------
echo "================================================================="
echo "📊 ZUSAMMENFASSUNG:"
echo "   Kopiert: $COPIED Scripts"
echo "   Fehler:  $ERRORS"
echo "================================================================="

if [ "$DRY_RUN" == "true" ]; then
    echo ""
    echo "⚠️  Dies war ein DRY-RUN - keine Dateien wurden geändert!"
    echo "    Führe das Script ohne --dry-run aus."
    exit 0
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "❌ Es gab Fehler! Bitte prüfen bevor du weitermachst."
    exit 1
fi

echo ""
echo "✅ Scripts kopiert!"
echo ""
echo "📋 NÄCHSTE SCHRITTE:"
echo "   1. job_definitions.py manuell updaten (Claude macht das)"
echo "   2. Scheduler neu starten: sudo systemctl restart greiner-scheduler"
echo "   3. Jobs testen"
echo "   4. Bei Erfolg: ./rename_scripts_tag90.sh --cleanup"
