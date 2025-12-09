#!/bin/bash
# Minimale Reorganisation - nur wichtigste Dateien
# Version: 1.0 - Quick & Simple

set -e
cd /opt/greiner-portal

echo "🧹 MINIMALE REORGANISATION - Wichtigste Dateien"
echo "================================================"
echo ""

# Zähler
moved=0

# Funktion zum sicheren Verschieben
move_if_exists() {
    local src="$1"
    local dest="$2"
    
    if [ -f "$src" ]; then
        mkdir -p "$(dirname "$dest")"
        mv "$src" "$dest"
        echo "  ✓ $src → $dest"
        ((moved++))
    fi
}

# WICHTIGSTE IMPORT-SCRIPTS
echo "📥 Import-Scripts..."
move_if_exists "import_bank_pdfs.py" "scripts/imports/import_bank_pdfs.py"
move_if_exists "import_november_all_accounts_v2.py" "scripts/imports/import_november_all_accounts_v2.py"
move_if_exists "import_stellantis.py" "scripts/imports/import_stellantis.py"
move_if_exists "pdf_importer.py" "scripts/imports/pdf_importer.py"
move_if_exists "genobank_universal_parser.py" "scripts/imports/genobank_universal_parser.py"
move_if_exists "import_bank_pdfs_seit_31_10.sh" "scripts/imports/import_bank_pdfs_seit_31_10.sh"
move_if_exists "import_moderne_genobank_pdfs.sh" "scripts/imports/import_moderne_genobank_pdfs.sh"

# TRANSACTION MANAGER
echo ""
echo "💾 Core-Dateien..."
move_if_exists "transaction_manager.py" "scripts/transaction_manager.py"

# WICHTIGSTE DOCS
echo ""
echo "📚 Dokumentation..."
move_if_exists "SESSION_WRAP_UP_TAG13.md" "docs/sessions/SESSION_WRAP_UP_TAG13.md"
move_if_exists "SESSION_WRAP_UP_TAG14.md" "docs/sessions/SESSION_WRAP_UP_TAG14.md"
move_if_exists "BUG_FIX_REPORT_TAG14.md" "docs/BUG_FIX_REPORT_TAG14.md"

# WICHTIGSTE LOGS
echo ""
echo "📝 Logs..."
move_if_exists "november_import.log" "logs/imports/november_import.log"
move_if_exists "november_import_v2.log" "logs/imports/november_import_v2.log"
move_if_exists "bank_import.log" "logs/imports/bank_import.log"

# BACKUPS
echo ""
echo "💾 Backups..."
move_if_exists "import_bank_pdfs_seit_31_10.sh.backup" "backups/import_bank_pdfs_seit_31_10.sh.backup"
move_if_exists "import_stellantis.py.backup_20251107_175542" "backups/import_stellantis.py.backup_20251107_175542"

# UTILITY-SCRIPTS
echo ""
echo "🔧 Utilities..."
move_if_exists "validate_salden.sh" "scripts/validate_salden.sh"

# SYMLINKS
echo ""
echo "🔗 Erstelle Symlinks..."
ln -sf scripts/imports/import_november_all_accounts_v2.py import_november_all_accounts_v2.py
ln -sf scripts/imports/import_stellantis.py import_stellantis.py
ln -sf scripts/validate_salden.sh validate_salden.sh
echo "  ✓ Symlinks erstellt"

# Zusammenfassung
echo ""
echo "================================================"
echo "✅ FERTIG - $moved Dateien verschoben"
echo "================================================"
echo ""
echo "📊 Wichtigste Scripts:"
ls -1 scripts/imports/ | grep -v "^$" || true
echo ""
echo "🔗 Symlinks (für Kompatibilität):"
ls -la | grep "^l" | awk '{print "  " $9 " -> " $11}'
echo ""
echo "⚠️  Hinweis: Weitere Dateien im Root können später aufgeräumt werden"
echo "🚀 Nächster Schritt: git add -A && git commit"
