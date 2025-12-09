#!/bin/bash
# ============================================
# STRUKTUR CLEANUP SCRIPT - TAG82
# ============================================
# Erstellt: 25.11.2025 von Claude
# Zweck: Projektstruktur aufräumen
# ============================================

set -e

echo "============================================"
echo "🏗️ GREINER PORTAL - STRUKTUR CLEANUP TAG82"
echo "============================================"
echo ""

cd /opt/greiner-portal

# 1. Doppelten Parser entfernen
echo "🔄 [1/7] Entferne doppelten Parser..."
if [ -f "scripts/imports/genobank_universal_parser.py" ]; then
    rm -f scripts/imports/genobank_universal_parser.py*
    echo "   ✅ Doppelter genobank_universal_parser entfernt"
else
    echo "   ℹ️  Bereits entfernt"
fi
echo ""

# 2. Logs aus Root verschieben
echo "🔄 [2/7] Verschiebe Logs aus Root..."
MOVED=0
for f in *.log; do
    if [ -f "$f" ]; then
        mv "$f" logs/
        MOVED=$((MOVED + 1))
    fi
done
echo "   ✅ $MOVED Log-Dateien verschoben"
echo ""

# 3. Session-Docs konsolidieren
echo "🔄 [3/7] Konsolidiere Session-Dokumentation..."
mkdir -p docs/sessions
MOVED=0

# Aus Root
for f in SESSION_WRAP_UP_TAG*.md; do
    if [ -f "$f" ]; then
        mv "$f" docs/sessions/
        MOVED=$((MOVED + 1))
    fi
done

# Aus docs/
for f in docs/SESSION_WRAP_UP_TAG*.md; do
    if [ -f "$f" ]; then
        mv "$f" docs/sessions/
        MOVED=$((MOVED + 1))
    fi
done
echo "   ✅ $MOVED Session-Wrap-Ups nach docs/sessions/ verschoben"
echo ""

# 4. TODOs verschieben
echo "🔄 [4/7] Verschiebe TODO-Dateien..."
MOVED=0
for f in TODO_FOR_CLAUDE_SESSION_START_TAG*.md; do
    if [ -f "$f" ]; then
        mv "$f" docs/
        MOVED=$((MOVED + 1))
    fi
done
echo "   ✅ $MOVED TODO-Dateien nach docs/ verschoben"
echo ""

# 5. Alte Scripts archivieren
echo "🔄 [5/7] Archiviere alte Root-Scripts..."
mkdir -p scripts/archive/root_cleanup_tag82
MOVED=0
for f in import_november_all_accounts_v2.py sync_fibu_buchungen_v2.3.py \
         fix_import_dynamic_scanning.py export_project_status.py \
         update_project_status.py cleanup_final.sh cleanup_root_scripts.sh \
         CLEANUP_COMMANDS_TAG71.sh; do
    if [ -f "$f" ]; then
        mv "$f" scripts/archive/root_cleanup_tag82/
        MOVED=$((MOVED + 1))
    fi
done
echo "   ✅ $MOVED Scripts archiviert"
echo ""

# 6. Cron-Backups verschieben
echo "🔄 [6/7] Verschiebe Cron-Backups..."
MOVED=0
for f in cron_backup_tag*.txt crontab_final_tag*.txt; do
    if [ -f "$f" ]; then
        mv "$f" backups/
        MOVED=$((MOVED + 1))
    fi
done
echo "   ✅ $MOVED Cron-Backups verschoben"
echo ""

# 7. Docs konsolidieren
echo "🔄 [7/7] Konsolidiere Dokumentation..."
mv GIT_WORKFLOW.md docs/ 2>/dev/null && echo "   ✅ GIT_WORKFLOW.md → docs/"
mv PROJECT_OVERVIEW.md docs/ 2>/dev/null && echo "   ✅ PROJECT_OVERVIEW.md → docs/"
mv PROJECT_STATUS.md docs/ 2>/dev/null && echo "   ✅ PROJECT_STATUS.md → docs/"
rm -f PROJEKT_STRUKTUR.md.backup_tag28 2>/dev/null && echo "   ✅ Altes Backup entfernt"
rm -f en 2>/dev/null && echo "   ✅ Datei 'en' entfernt"
echo ""

# Report
echo "============================================"
echo "✅ STRUKTUR-CLEANUP ABGESCHLOSSEN"
echo "============================================"
echo ""
echo "📁 Root-Verzeichnis (nur Dateien):"
ls -la | grep "^-" | awk '{print "   " $NF}'
echo ""
echo "📊 Erwartete Dateien im Root:"
echo "   - app.py"
echo "   - requirements.txt"
echo "   - requirements_auth.txt"
echo "   - README.md"
echo "   - .gitignore"
echo ""
echo "Falls weitere Dateien: Manuell prüfen!"
echo "============================================"
