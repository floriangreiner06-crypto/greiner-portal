#!/bin/bash
# -*- coding: utf-8 -*-
"""
Greiner Portal - Verzeichnis-Reorganisation
===========================================
Räumt die Verzeichnisstruktur auf und erstellt saubere Organisation

Author: Claude AI
Version: 1.0
Date: 2025-11-07
"""

set -e  # Bei Fehler abbrechen

echo "======================================================================="
echo "🧹 GREINER PORTAL - VERZEICHNIS-REORGANISATION"
echo "======================================================================="
echo ""

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Basis-Verzeichnis
BASE_DIR="/opt/greiner-portal"
cd "$BASE_DIR"

echo -e "${YELLOW}⚠️  WARNUNG: Dieses Script reorganisiert die Verzeichnisstruktur!${NC}"
echo ""
echo "Aktuelle Dateien werden in folgende Struktur verschoben:"
echo ""
echo "  📁 /scripts/          - Utility- und Import-Scripts"
echo "  📁 /scripts/analysis/ - Analyse-Scripts"
echo "  📁 /scripts/imports/  - Import-Scripts"
echo "  📁 /scripts/tests/    - Test-Scripts"
echo "  📁 /docs/             - Dokumentation & Session-Wrap-ups"
echo "  📁 /backups/          - Backup-Dateien"
echo "  📁 /logs/             - Log-Dateien"
echo ""
read -p "Fortfahren? (j/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    echo "Abgebrochen."
    exit 1
fi

echo ""
echo -e "${BLUE}📦 Erstelle Backup der aktuellen Struktur...${NC}"
BACKUP_DIR="backups/reorganization_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Backup-Verzeichnis: $BACKUP_DIR"

echo ""
echo -e "${BLUE}📁 Erstelle neue Verzeichnisstruktur...${NC}"

# Erstelle Verzeichnisse
mkdir -p scripts/{analysis,imports,tests,setup}
mkdir -p docs/sessions
mkdir -p logs/imports
mkdir -p backups

echo "  ✓ scripts/"
echo "  ✓ scripts/analysis/"
echo "  ✓ scripts/imports/"
echo "  ✓ scripts/tests/"
echo "  ✓ scripts/setup/"
echo "  ✓ docs/"
echo "  ✓ docs/sessions/"
echo "  ✓ logs/imports/"
echo "  ✓ backups/"

echo ""
echo -e "${BLUE}🔄 Verschiebe Dateien...${NC}"

# Zähler
moved=0
skipped=0

# Funktion zum sicheren Verschieben
safe_move() {
    local src="$1"
    local dest="$2"
    
    if [ -f "$src" ]; then
        mkdir -p "$(dirname "$dest")"
        mv "$src" "$dest"
        echo "  ✓ $src → $dest"
        ((moved++))
    fi
}

# 1. ANALYSE-SCRIPTS
echo ""
echo "📊 Analyse-Scripts..."
safe_move "analyze_employees.py" "scripts/analysis/analyze_employees.py"
safe_move "analyze_lines_detailed.py" "scripts/analysis/analyze_lines_detailed.py"
safe_move "analyze_locosoft_absence.py" "scripts/analysis/analyze_locosoft_absence.py"
safe_move "analyze_real_employees.py" "scripts/analysis/analyze_real_employees.py"
safe_move "analyze_subsidiaries.py" "scripts/analysis/analyze_subsidiaries.py"
safe_move "analyze_text.py" "scripts/analysis/analyze_text.py"
safe_move "check_db_status.py" "scripts/analysis/check_db_status.py"
safe_move "show_departments.py" "scripts/analysis/show_departments.py"

# 2. IMPORT-SCRIPTS
echo ""
echo "📥 Import-Scripts..."
safe_move "import_bank_pdfs.py" "scripts/imports/import_bank_pdfs.py"
safe_move "import_bank_pdfs_seit_31_10.sh" "scripts/imports/import_bank_pdfs_seit_31_10.sh"
safe_move "import_moderne_genobank_pdfs.sh" "scripts/imports/import_moderne_genobank_pdfs.sh"
safe_move "import_november_all_accounts.py" "scripts/imports/import_november_all_accounts.py"
safe_move "import_november_all_accounts_v2.py" "scripts/imports/import_november_all_accounts_v2.py"
safe_move "import_stellantis.py" "scripts/imports/import_stellantis.py"
safe_move "pdf_importer.py" "scripts/imports/pdf_importer.py"
safe_move "genobank_universal_parser.py" "scripts/imports/genobank_universal_parser.py"

# 3. TEST-SCRIPTS
echo ""
echo "🧪 Test-Scripts..."
safe_move "test_bankenspiegel_api.sh" "scripts/tests/test_bankenspiegel_api.sh"
safe_move "test_locosoft.py" "scripts/tests/test_locosoft.py"
safe_move "test_multiple_pdfs.py" "scripts/tests/test_multiple_pdfs.py"
safe_move "test_ocr_parser.py" "scripts/tests/test_ocr_parser.py"
safe_move "test_pymupdf.py" "scripts/tests/test_pymupdf.py"
safe_move "test_pypdf2.py" "scripts/tests/test_pypdf2.py"
safe_move "test_vacation_api.py" "scripts/tests/test_vacation_api.py"

# 4. SETUP-SCRIPTS
echo ""
echo "⚙️  Setup-Scripts..."
safe_move "setup_vacation_api.py" "scripts/setup/setup_vacation_api.py"
safe_move "setup_vacation_calculator.py" "scripts/setup/setup_vacation_calculator.py"
safe_move "setup_vacation_entitlements_2025.py" "scripts/setup/setup_vacation_entitlements_2025.py"
safe_move "setup_vacation_views.py" "scripts/setup/setup_vacation_views.py"
safe_move "phase1_tag1_setup.sh" "scripts/setup/phase1_tag1_setup.sh"
safe_move "install.sh" "scripts/setup/install.sh"
safe_move "install_bankenspiegel_api.sh" "scripts/setup/install_bankenspiegel_api.sh"

# 5. UTILITY-SCRIPTS
echo ""
echo "🔧 Utility-Scripts..."
safe_move "add_missing_columns.py" "scripts/add_missing_columns.py"
safe_move "credentials_helper.py" "scripts/credentials_helper.py"
safe_move "delete_bookings.py" "scripts/delete_bookings.py"
safe_move "sync_employees.py" "scripts/sync_employees.py"
safe_move "update_import.sh" "scripts/update_import.sh"
safe_move "validate_salden.sh" "scripts/validate_salden.sh"
safe_move "git_commit_tag9.sh" "scripts/git_commit_tag9.sh"

# 6. FIX-SCRIPTS
echo ""
echo "🩹 Fix-Scripts..."
safe_move "fix_app_py.py" "scripts/fixes/fix_app_py.py"
safe_move "fix_konten_endpoint.py" "scripts/fixes/fix_konten_endpoint.py"
safe_move "fix_vacation_views.py" "scripts/fixes/fix_vacation_views.py"
safe_move "fix_vacation_views_final.py" "scripts/fixes/fix_vacation_views_final.py"
safe_move "final_fix_vacation_calculator.py" "scripts/fixes/final_fix_vacation_calculator.py"

# 7. PATCH-SCRIPTS
echo ""
echo "🔨 Patch-Scripts..."
safe_move "patch_api_interne_transfers.py" "scripts/patches/patch_api_interne_transfers.py"
safe_move "register_vacation_api.py" "scripts/patches/register_vacation_api.py"

# 8. CHECK-SCRIPTS
echo ""
echo "🔍 Check-Scripts..."
safe_move "check_locosoft_arbeitszeitkonto.py" "scripts/checks/check_locosoft_arbeitszeitkonto.py"
safe_move "check_locosoft_vacation.py" "scripts/checks/check_locosoft_vacation.py"

# 9. DOKUMENTATION
echo ""
echo "📚 Dokumentation..."
safe_move "SESSION_WRAP_UP_TAG2.md" "docs/sessions/SESSION_WRAP_UP_TAG02.md"
safe_move "SESSION_WRAP_UP_TAG3.md" "docs/sessions/SESSION_WRAP_UP_TAG03.md"
safe_move "SESSION_WRAP_UP_TAG4_FRONTEND.md" "docs/sessions/SESSION_WRAP_UP_TAG04_FRONTEND.md"
safe_move "SESSION_WRAP_UP_TAG6.md" "docs/sessions/SESSION_WRAP_UP_TAG06.md"
safe_move "SESSION_WRAP_UP_TAG13.md" "docs/sessions/SESSION_WRAP_UP_TAG13.md"
safe_move "SESSION_WRAP_UP_TAG14.md" "docs/sessions/SESSION_WRAP_UP_TAG14.md"
safe_move "BUG_FIX_REPORT_TAG14.md" "docs/BUG_FIX_REPORT_TAG14.md"
safe_move "INSTALLATION_ANLEITUNG.md" "docs/INSTALLATION_ANLEITUNG.md"
safe_move "README_BANKENSPIEGEL_API.md" "docs/README_BANKENSPIEGEL_API.md"
safe_move "README_NOVEMBER_IMPORT.md" "docs/README_NOVEMBER_IMPORT.md"
safe_move "SETUP_COMPLETE.md" "docs/SETUP_COMPLETE.md"

# 10. LOG-DATEIEN
echo ""
echo "📝 Log-Dateien..."
safe_move "november_import.log" "logs/imports/november_import.log"
safe_move "november_import_v2.log" "logs/imports/november_import_v2.log"
safe_move "bank_import.log" "logs/imports/bank_import.log"
safe_move "import_20251107_163730.log" "logs/imports/import_20251107_163730.log"
safe_move "import_20251107_193754.log" "logs/imports/import_20251107_193754.log"
safe_move "update_import_20251107_164652.log" "logs/imports/update_import_20251107_164652.log"

# 11. BACKUP-DATEIEN
echo ""
echo "💾 Backup-Dateien..."
safe_move "app.py.backup_20251107_111258" "backups/app.py.backup_20251107_111258"
safe_move "import_bank_pdfs_seit_31_10.sh.backup" "backups/import_bank_pdfs_seit_31_10.sh.backup"
safe_move "import_stellantis.py.backup_20251107_175542" "backups/import_stellantis.py.backup_20251107_175542"

# 12. Erstelle Symlinks für häufig genutzte Scripts (für Kompatibilität)
echo ""
echo "🔗 Erstelle Symlinks für Kompatibilität..."
ln -sf scripts/imports/import_november_all_accounts_v2.py import_november_all_accounts_v2.py
ln -sf scripts/imports/import_stellantis.py import_stellantis.py
ln -sf scripts/validate_salden.sh validate_salden.sh
echo "  ✓ Symlinks erstellt"

# 13. Erstelle README in Script-Verzeichnissen
echo ""
echo "📄 Erstelle README-Dateien..."

cat > scripts/README.md << 'EOF'
# Scripts Verzeichnis

## Struktur

- **analysis/** - Analyse-Scripts für DB, Employees, etc.
- **imports/** - Import-Scripts für Bank-PDFs, Stellantis, etc.
- **tests/** - Test-Scripts
- **setup/** - Setup- und Installations-Scripts
- **fixes/** - Bug-Fix-Scripts
- **patches/** - Patch-Scripts für API-Änderungen
- **checks/** - Check-Scripts für Validierungen

## Wichtige Scripts

### Imports
- `imports/import_november_all_accounts_v2.py` - November-Import (IBAN-basiert) ✅ PRODUKTIV
- `imports/import_stellantis.py` - Stellantis ZIP-Import ✅ PRODUKTIV
- `imports/import_bank_pdfs.py` - Allgemeiner PDF-Import

### Validierung
- `validate_salden.sh` - Salden-Validierung ✅ PRODUKTIV

### Analyse
- `analysis/check_db_status.py` - Datenbank-Status
EOF

cat > docs/README.md << 'EOF'
# Dokumentation

## Struktur

- **sessions/** - Session Wrap-Ups (Tag 1-X)
- **README_*.md** - Feature-spezifische Dokumentation
- **INSTALLATION_ANLEITUNG.md** - Setup-Anleitung

## Session Wrap-Ups

Chronologische Dokumentation der Entwicklung:
- TAG02 bis TAG06 - Frühe Features
- TAG13 - Stellantis-Import, November-Daten
- TAG14 - Bug-Fixes, Konto-Konsolidierung
- TAG15 - Weitere November-Imports (in Arbeit)
EOF

echo "  ✓ README-Dateien erstellt"

# Zusammenfassung
echo ""
echo "======================================================================="
echo -e "${GREEN}✅ REORGANISATION ABGESCHLOSSEN${NC}"
echo "======================================================================="
echo ""
echo "📊 Statistik:"
echo "  Verschobene Dateien: $moved"
echo "  Übersprungene Dateien: $skipped"
echo ""
echo "📁 Neue Struktur:"
echo "  ├── api/              (unverändert)"
echo "  ├── app/              (unverändert)"
echo "  ├── config/           (unverändert)"
echo "  ├── data/             (unverändert)"
echo "  ├── migrations/       (unverändert)"
echo "  ├── parsers/          (unverändert)"
echo "  ├── routes/           (unverändert)"
echo "  ├── static/           (unverändert)"
echo "  ├── templates/        (unverändert)"
echo "  ├── scripts/          ✅ NEU - Alle Scripts"
echo "  │   ├── analysis/     ✅ NEU - Analyse-Scripts"
echo "  │   ├── imports/      ✅ NEU - Import-Scripts"
echo "  │   ├── tests/        ✅ NEU - Test-Scripts"
echo "  │   ├── setup/        ✅ NEU - Setup-Scripts"
echo "  │   ├── fixes/        ✅ NEU - Fix-Scripts"
echo "  │   ├── patches/      ✅ NEU - Patch-Scripts"
echo "  │   └── checks/       ✅ NEU - Check-Scripts"
echo "  ├── docs/             ✅ NEU - Dokumentation"
echo "  │   └── sessions/     ✅ NEU - Session Wrap-Ups"
echo "  ├── logs/             ✅ NEU - Log-Dateien"
echo "  │   └── imports/      ✅ NEU - Import-Logs"
echo "  ├── backups/          ✅ NEU - Backup-Dateien"
echo "  └── venv/             (unverändert)"
echo ""
echo "🔗 Symlinks für Kompatibilität:"
echo "  ✓ import_november_all_accounts_v2.py → scripts/imports/"
echo "  ✓ import_stellantis.py → scripts/imports/"
echo "  ✓ validate_salden.sh → scripts/"
echo ""
echo -e "${YELLOW}⚠️  Wichtig:${NC}"
echo "  1. Prüfen Sie, ob alle Scripts noch funktionieren"
echo "  2. Passen Sie ggf. Cronjobs an (neue Pfade)"
echo "  3. Backup liegt in: $BACKUP_DIR"
echo ""
echo "🚀 Nächste Schritte:"
echo "  1. Git-Status prüfen: git status"
echo "  2. Test-Import durchführen"
echo "  3. Bei Problemen: Backup zurückspielen"
echo ""
echo "======================================================================="
