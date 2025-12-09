#!/bin/bash
# ============================================
# CLEANUP SCRIPT TAG82
# ============================================
# Erstellt: 25.11.2025 von Claude
# Zweck: Aufräumen nach Qualitätscheck
# 
# ANLEITUNG:
# 1. Auf Server kopieren: scp cleanup_tag82.sh user@10.80.80.20:/opt/greiner-portal/
# 2. Ausführen: cd /opt/greiner-portal && bash cleanup_tag82.sh
# ============================================

set -e  # Bei Fehler abbrechen

cd /opt/greiner-portal

echo "============================================"
echo "GREINER PORTAL - CLEANUP TAG82"
echo "============================================"
echo ""

# Backup-Verzeichnis erstellen
BACKUP_DIR="backups/cleanup_tag82_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR/code_backups"
mkdir -p "$BACKUP_DIR/old_versions"
mkdir -p "$BACKUP_DIR/root_files"

echo "📁 Backup-Verzeichnis: $BACKUP_DIR"
echo ""

# Zähler
MOVED_FILES=0

# 1. Alle .backup Dateien verschieben
echo "🔄 [1/7] Verschiebe .backup Dateien..."
BACKUP_COUNT=$(find . -name "*.backup*" -not -path "./backups/*" -not -path "./venv/*" -not -path "./.git/*" 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 0 ]; then
    find . -name "*.backup*" -not -path "./backups/*" -not -path "./venv/*" -not -path "./.git/*" \
        -exec mv {} "$BACKUP_DIR/code_backups/" \; 2>/dev/null || true
    echo "   → $BACKUP_COUNT Dateien verschoben"
    MOVED_FILES=$((MOVED_FILES + BACKUP_COUNT))
else
    echo "   → Keine .backup Dateien gefunden"
fi

# 2. Alle .old/.OLD Dateien verschieben
echo "🔄 [2/7] Verschiebe .old Dateien..."
OLD_COUNT=$(find . \( -name "*.old" -o -name "*.OLD" \) -not -path "./backups/*" -not -path "./venv/*" -not -path "./.git/*" 2>/dev/null | wc -l)
if [ "$OLD_COUNT" -gt 0 ]; then
    find . \( -name "*.old" -o -name "*.OLD" \) -not -path "./backups/*" -not -path "./venv/*" -not -path "./.git/*" \
        -exec mv {} "$BACKUP_DIR/code_backups/" \; 2>/dev/null || true
    echo "   → $OLD_COUNT Dateien verschoben"
    MOVED_FILES=$((MOVED_FILES + OLD_COUNT))
else
    echo "   → Keine .old Dateien gefunden"
fi

# 3. Verwaiste Verzeichnisse verschieben
echo "🔄 [3/7] Verschiebe verwaiste Verzeichnisse..."
if [ -d "parsers_backup_tag59_end_20251118_163659" ]; then
    mv parsers_backup_tag59_end_20251118_163659 "$BACKUP_DIR/old_versions/"
    echo "   → parsers_backup_tag59_end verschoben"
fi
if [ -d "app.UNUSED_TAG24" ]; then
    mv app.UNUSED_TAG24 "$BACKUP_DIR/old_versions/"
    echo "   → app.UNUSED_TAG24 verschoben"
fi

# 4. Log-Dateien aus Root verschieben
echo "🔄 [4/7] Verschiebe Log-Dateien aus Root..."
for logfile in november_import_v2.log november_import_v3_final.log; do
    if [ -f "$logfile" ]; then
        mv "$logfile" logs/
        echo "   → $logfile → logs/"
        MOVED_FILES=$((MOVED_FILES + 1))
    fi
done

# 5. Session-Dokumentation verschieben
echo "🔄 [5/7] Verschiebe Session-Dokumentation..."
mkdir -p docs/sessions
SESSION_COUNT=$(ls SESSION_WRAP_UP_TAG*.md 2>/dev/null | wc -l)
if [ "$SESSION_COUNT" -gt 0 ]; then
    mv SESSION_WRAP_UP_TAG*.md docs/sessions/ 2>/dev/null || true
    echo "   → $SESSION_COUNT Session-Wrap-Ups verschoben"
    MOVED_FILES=$((MOVED_FILES + SESSION_COUNT))
fi

TODO_COUNT=$(ls TODO_FOR_CLAUDE_SESSION_START_TAG*.md 2>/dev/null | wc -l)
if [ "$TODO_COUNT" -gt 0 ]; then
    mv TODO_FOR_CLAUDE_SESSION_START_TAG*.md docs/ 2>/dev/null || true
    echo "   → $TODO_COUNT TODO-Dateien verschoben"
    MOVED_FILES=$((MOVED_FILES + TODO_COUNT))
fi

# 6. Alte Scripts aus Root verschieben
echo "🔄 [6/7] Verschiebe alte Scripts aus Root..."
for oldscript in import_november_all_accounts_v2.py sync_fibu_buchungen_v2.3.py fix_import_dynamic_scanning.py; do
    if [ -f "$oldscript" ]; then
        mv "$oldscript" "$BACKUP_DIR/old_versions/"
        echo "   → $oldscript verschoben"
        MOVED_FILES=$((MOVED_FILES + 1))
    fi
done

# Cron-Backups
for cronfile in cron_backup_tag43*.txt crontab_final_tag65.txt; do
    if [ -f "$cronfile" ]; then
        mv "$cronfile" "$BACKUP_DIR/root_files/" 2>/dev/null || true
        MOVED_FILES=$((MOVED_FILES + 1))
    fi
done

# 7. Cleanup-Scripts aus Root verschieben (außer diesem)
echo "🔄 [7/7] Verschiebe alte Cleanup-Scripts..."
for cleanupfile in cleanup_final.sh cleanup_root_scripts.sh CLEANUP_COMMANDS_TAG71.sh; do
    if [ -f "$cleanupfile" ]; then
        mv "$cleanupfile" "$BACKUP_DIR/root_files/"
        echo "   → $cleanupfile verschoben"
        MOVED_FILES=$((MOVED_FILES + 1))
    fi
done

# Report
echo ""
echo "============================================"
echo "✅ CLEANUP ABGESCHLOSSEN"
echo "============================================"
echo ""
echo "📊 Statistik:"
echo "   Verschobene Dateien: $MOVED_FILES"
echo "   Backup-Verzeichnis:  $BACKUP_DIR"
echo ""
echo "📦 Backup-Inhalt:"
find "$BACKUP_DIR" -type f 2>/dev/null | wc -l
echo " Dateien"
echo ""
echo "💾 Backup-Größe:"
du -sh "$BACKUP_DIR"
echo ""
echo "============================================"
echo "NÄCHSTE SCHRITTE:"
echo "============================================"
echo "1. Testen: systemctl restart greiner-portal"
echo "2. Prüfen: http://drive/admin/system-status"
echo "3. Git:    git add -A && git commit -m 'cleanup(TAG82): Aufräumen nach Qualitätscheck'"
echo ""
echo "Bei Problemen:"
echo "   Backup wiederherstellen aus: $BACKUP_DIR"
echo "============================================"
