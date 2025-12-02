#!/bin/bash
# Vereinfachtes Cleanup - ohne set -e, zeigt alle Fehler
# TAG 42 - 2025-11-14

echo "════════════════════════════════════════════════════════════"
echo "🧹 GREINER PORTAL - CLEANUP START"
echo "════════════════════════════════════════════════════════════"

# Backup
BACKUP="backups/cleanup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP"
echo "📦 Backup: $BACKUP"

# Verzeichnisse erstellen (ohne Fehler wenn existiert)
mkdir -p docs/claude docs/sessions docs/reports
mkdir -p scripts/checks scripts/tests scripts/setup scripts/analysis
mkdir -p scripts/fixes scripts/git scripts/sync/archive scripts/archive

MOVED=0

# Session Docs
echo ""
echo "1. Session-Docs..."
mv SESSION_WRAP_UP_TAG*.md docs/sessions/ 2>/dev/null && echo "  ✅ Session Wrap-Ups" && ((MOVED+=3))
mv TODO_FOR_CLAUDE*.md docs/sessions/ 2>/dev/null && echo "  ✅ TODOs" && ((MOVED+=1))

# Claude Docs
echo "2. Claude-Docs..."
mv README_FOR_CLAUDE.md README_SESSION_START.md QUICK_START_NEW_CHAT.md docs/claude/ 2>/dev/null && ((MOVED+=3))
mv ACTION_ITEMS_*.md FEATURE_TEST_CHECKLIST.md PROJEKT_STRUKTUR.md docs/claude/ 2>/dev/null && ((MOVED+=3))

# Check Scripts
echo "3. Check Scripts..."
mv bankenspiegel_check*.sh bankkonten_*check*.sh check_*.sh check_*.py scripts/checks/ 2>/dev/null && ((MOVED+=10))
mv diagnose_*.sh cron_check*.sh *_report.sh validate_*.sh scripts/checks/ 2>/dev/null && ((MOVED+=5))

# Reports
mv cron_check_report.txt salden_probleme.txt duplikate_*.txt docs/reports/ 2>/dev/null && ((MOVED+=3))

# Test Scripts
echo "4. Test Scripts..."
mv test_*.py scripts/tests/ 2>/dev/null && ((MOVED+=15))

# Setup/Deploy
echo "5. Setup Scripts..."
mv deploy_*.sh install_*.sh setup_*.sh setup_*.py phase1_*.sh scripts/setup/ 2>/dev/null && ((MOVED+=20))

# Analyse
echo "6. Analyse Scripts..."
mv analyze_*.py analyze_*.sh find_*.py show_*.py scripts/analysis/ 2>/dev/null && ((MOVED+=8))

# Fixes
echo "7. Fix Scripts..."
mv fix_*.py patch_*.py final_fix_*.py scripts/fixes/ 2>/dev/null && ((MOVED+=5))

# Git
echo "8. Git Scripts..."
mv git_*.sh scripts/git/ 2>/dev/null && ((MOVED+=4))

# Archive
echo "9. Alte Scripts..."
mv import_all_*.sh import_moderne_*.sh update_import.sh reorganize_*.sh scripts/archive/ 2>/dev/null && ((MOVED+=4))

# Sync Backups
echo "10. Sync Backups..."
mv sync_*_backup*.py scripts/sync/archive/ 2>/dev/null && ((MOVED+=3))

# API Duplikate
echo "11. API Duplikate..."
if [ -f "bankenspiegel_api.py" ] && [ -f "api/bankenspiegel_api.py" ]; then
    mv bankenspiegel_api.py scripts/archive/bankenspiegel_api_root.py
    echo "  ✅ bankenspiegel_api.py (Duplikat)"
    ((MOVED+=1))
fi
mv vacation_api_new.py scripts/archive/ 2>/dev/null && ((MOVED+=1))

# Utils
echo "12. Utils..."
mv credentials_helper.py register_*.py app_integration.py scripts/archive/ 2>/dev/null && ((MOVED+=3))

# Alte Auth
if [ -f "ldap_connector.py" ] && [ -f "auth/ldap_connector.py" ]; then
    mv ldap_connector.py scripts/archive/ldap_connector_root.py
    echo "  ✅ ldap_connector.py (Duplikat)"
    ((MOVED+=1))
fi

# Alte Requirements
mv requirements_auth.txt docs/archive/ 2>/dev/null && ((MOVED+=1))

# Merkwürdige Dateien löschen
echo "13. Merkwürdige Dateien..."
rm -f "View fehlt, erstelle sie:" "er-Cache leeren (WICHTIG!)" "tiert (WICHTIG!):" 2>/dev/null && echo "  ✅ Merkwürdige Dateien entfernt"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ CLEANUP FERTIG"
echo "════════════════════════════════════════════════════════════"
echo "Dateien verschoben/gelöscht: ~$MOVED"
echo "Backup: $BACKUP"
echo ""
echo "CHECK:"
ls -1 *.md *.py *.sh *.txt 2>/dev/null | wc -l | xargs echo "Dateien im Root:"
