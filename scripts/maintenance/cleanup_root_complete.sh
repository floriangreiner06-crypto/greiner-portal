#!/bin/bash
# Komplettes Root-Verzeichnis Cleanup
# Datum: 2025-11-14 TAG 42
# Erstellt von: Claude + User

set -e

echo "════════════════════════════════════════════════════════════"
echo "🧹 GREINER PORTAL - KOMPLETTES ROOT CLEANUP"
echo "════════════════════════════════════════════════════════════"
echo ""

# Backup erstellen
BACKUP_DIR="backups/cleanup_root_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 Backup: $BACKUP_DIR"

# Alle Dateien ins Backup kopieren (Sicherheit!)
echo "📦 Erstelle Komplett-Backup..."
cp *.md *.py *.sh *.txt "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Backup erstellt"
echo ""

# Verzeichnisse erstellen
echo "📁 Erstelle Verzeichnisstruktur..."
mkdir -p docs/claude
mkdir -p docs/sessions
mkdir -p docs/reports
mkdir -p scripts/checks
mkdir -p scripts/tests
mkdir -p scripts/setup
mkdir -p scripts/analysis
mkdir -p scripts/fixes
mkdir -p scripts/git
mkdir -p scripts/utils
mkdir -p scripts/sync/archive
mkdir -p scripts/archive
mkdir -p scripts/api/archive
echo "✅ Verzeichnisse erstellt"
echo ""

MOVED=0

# ═══════════════════════════════════════════════════════════════
# 1. SESSION-DOKUMENTATION → docs/sessions/
# ═══════════════════════════════════════════════════════════════

echo "📝 1. Session-Dokumentation..."

for file in SESSION_WRAP_UP_TAG*.md TODO_FOR_CLAUDE_SESSION_START*.md; do
    if [ -f "$file" ]; then
        # Prüfe ob bereits in docs/sessions existiert
        if [ -f "docs/sessions/$file" ]; then
            echo "  🗑️  $file (Duplikat, wird gelöscht)"
            rm "$file"
        else
            mv "$file" docs/sessions/
            echo "  ✅ $file → docs/sessions/"
        fi
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 2. CLAUDE-DOKUMENTATION → docs/claude/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "📖 2. Claude-Dokumentation..."

for file in README_FOR_CLAUDE.md \
            QUICK_START_NEW_CHAT.md \
            README_SESSION_START.md \
            PROJEKT_STRUKTUR.md \
            ACTION_ITEMS_TAG*.md \
            FEATURE_TEST_CHECKLIST.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/claude/
        echo "  ✅ $file → docs/claude/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 3. CHECK & DIAGNOSE SCRIPTS → scripts/checks/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "🔍 3. Check & Diagnose Scripts..."

for file in bankenspiegel_check_*.sh \
            bankkonten_*_check.sh \
            check_*.py \
            check_*.sh \
            cron_check_*.sh \
            diagnose_*.sh \
            fahrzeugfinanzierungen_*_report.sh \
            test_bankenspiegel_api.sh \
            validate_*.sh; do
    if [ -f "$file" ]; then
        mv "$file" scripts/checks/
        echo "  ✅ $file → scripts/checks/"
        ((MOVED++))
    fi
done

if [ -f "cron_check_report.txt" ]; then
    mv cron_check_report.txt docs/reports/
    echo "  ✅ cron_check_report.txt → docs/reports/"
    ((MOVED++))
fi

# ═══════════════════════════════════════════════════════════════
# 4. TEST SCRIPTS → scripts/tests/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "🧪 4. Test Scripts..."

for file in test_*.py; do
    if [ -f "$file" ]; then
        mv "$file" scripts/tests/
        echo "  ✅ $file → scripts/tests/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 5. SETUP & DEPLOY SCRIPTS → scripts/setup/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "⚙️  5. Setup & Deploy Scripts..."

for file in deploy_*.sh \
            install_*.sh \
            setup_*.py \
            setup_*.sh \
            phase1_*.sh; do
    if [ -f "$file" ]; then
        mv "$file" scripts/setup/
        echo "  ✅ $file → scripts/setup/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 6. ANALYSE SCRIPTS → scripts/analysis/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "📊 6. Analyse Scripts..."

for file in analyze_*.py \
            analyze_*.sh \
            find_*.py \
            show_*.py; do
    if [ -f "$file" ]; then
        mv "$file" scripts/analysis/
        echo "  ✅ $file → scripts/analysis/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 7. FIX & PATCH SCRIPTS → scripts/fixes/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "🔧 7. Fix & Patch Scripts..."

for file in fix_*.py \
            patch_*.py \
            final_fix_*.py; do
    if [ -f "$file" ]; then
        mv "$file" scripts/fixes/
        echo "  ✅ $file → scripts/fixes/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 8. GIT SCRIPTS → scripts/git/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "🔀 8. Git Scripts..."

for file in git_*.sh; do
    if [ -f "$file" ]; then
        mv "$file" scripts/git/
        echo "  ✅ $file → scripts/git/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 9. ALTE IMPORT SCRIPTS → scripts/archive/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "📦 9. Alte Import Scripts..."

for file in import_all_bank_pdfs.sh \
            import_moderne_genobank_pdfs.sh \
            update_import.sh \
            reorganize_*.sh; do
    if [ -f "$file" ]; then
        mv "$file" scripts/archive/
        echo "  ✅ $file → scripts/archive/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 10. SYNC BACKUPS → scripts/sync/archive/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "🔄 10. Sync Backups..."

for file in sync_*_backup*.py; do
    if [ -f "$file" ]; then
        mv "$file" scripts/sync/archive/
        echo "  ✅ $file → scripts/sync/archive/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 11. ALTE API FILES → scripts/api/archive/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "🔌 11. Alte API Files..."

# Nur verschieben wenn NICHT in api/ Verzeichnis genutzt
if [ -f "bankenspiegel_api.py" ] && [ -f "api/bankenspiegel_api.py" ]; then
    mv bankenspiegel_api.py scripts/api/archive/
    echo "  ✅ bankenspiegel_api.py → scripts/api/archive/ (Duplikat)"
    ((MOVED++))
fi

if [ -f "vacation_api_new.py" ]; then
    mv vacation_api_new.py scripts/api/archive/
    echo "  ✅ vacation_api_new.py → scripts/api/archive/"
    ((MOVED++))
fi

# ═══════════════════════════════════════════════════════════════
# 12. UTILITY SCRIPTS → scripts/utils/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "🛠️  12. Utility Scripts..."

for file in credentials_helper.py \
            register_*.py; do
    if [ -f "$file" ]; then
        mv "$file" scripts/utils/
        echo "  ✅ $file → scripts/utils/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 13. REPORTS & LOGS → docs/reports/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "📋 13. Reports & Logs..."

for file in salden_probleme.txt \
            duplikate_analyse_*.txt \
            *_report.txt; do
    if [ -f "$file" ]; then
        mv "$file" docs/reports/
        echo "  ✅ $file → docs/reports/"
        ((MOVED++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# 14. AUTH FILES PRÜFEN
# ═══════════════════════════════════════════════════════════════

echo ""
echo "🔐 14. Auth Files..."

if [ -f "ldap_connector.py" ] && [ -f "auth/ldap_connector.py" ]; then
    mv ldap_connector.py scripts/archive/
    echo "  ✅ ldap_connector.py → scripts/archive/ (Duplikat)"
    ((MOVED++))
elif [ -f "ldap_connector.py" ]; then
    echo "  ⚠️  ldap_connector.py (manuell prüfen!)"
fi

# ═══════════════════════════════════════════════════════════════
# 15. ALTE REQUIREMENTS → docs/archive/
# ═══════════════════════════════════════════════════════════════

echo ""
echo "📦 15. Alte Requirements..."

if [ -f "requirements_auth.txt" ]; then
    mv requirements_auth.txt docs/archive/
    echo "  ✅ requirements_auth.txt → docs/archive/"
    ((MOVED++))
fi

# ═══════════════════════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═══════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ CLEANUP ABGESCHLOSSEN"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 Statistik:"
echo "   Dateien verschoben: $MOVED"
echo ""
echo "📁 Verzeichnisse (Dateien):"
ls -1 docs/claude/ 2>/dev/null | wc -l | xargs echo "   docs/claude/:"
ls -1 docs/sessions/ 2>/dev/null | wc -l | xargs echo "   docs/sessions/:"
ls -1 docs/reports/ 2>/dev/null | wc -l | xargs echo "   docs/reports/:"
ls -1 scripts/checks/ 2>/dev/null | wc -l | xargs echo "   scripts/checks/:"
ls -1 scripts/tests/ 2>/dev/null | wc -l | xargs echo "   scripts/tests/:"
ls -1 scripts/setup/ 2>/dev/null | wc -l | xargs echo "   scripts/setup/:"
ls -1 scripts/analysis/ 2>/dev/null | wc -l | xargs echo "   scripts/analysis/:"
ls -1 scripts/fixes/ 2>/dev/null | wc -l | xargs echo "   scripts/fixes/:"
ls -1 scripts/git/ 2>/dev/null | wc -l | xargs echo "   scripts/git/:"
ls -1 scripts/archive/ 2>/dev/null | wc -l | xargs echo "   scripts/archive/:"
echo ""
echo "📦 Backup: $BACKUP_DIR"
echo ""
echo "⚠️  NÄCHSTE SCHRITTE:"
echo "   1. Root-Verzeichnis prüfen: ls -1 *.md *.py *.sh *.txt"
echo "   2. Git Status: git status"
echo "   3. Committen wenn OK"
echo ""
