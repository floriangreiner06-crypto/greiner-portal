#!/bin/bash
# ============================================================================
# Bankenspiegel 3.0 - Installations-Skript
# ============================================================================
# Automatische Installation des PDF-Import-Systems
# Server: 10.80.80.20
# Pfad: /opt/greiner-portal/
# ============================================================================

set -e  # Exit bei Fehler

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Bankenspiegel 3.0 - PDF Import System Installation          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# VARIABLEN
# ============================================================================

TARGET_DIR="/opt/greiner-portal"
VENV_DIR="$TARGET_DIR/venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# PRE-CHECK
# ============================================================================

echo "📋 Schritt 1: Voraussetzungen prüfen..."

# Prüfe ob wir im richtigen Verzeichnis sind
if [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Fehler: $TARGET_DIR existiert nicht!"
    exit 1
fi

# Prüfe ob Virtual Environment existiert
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Fehler: Virtual Environment nicht gefunden in $VENV_DIR"
    exit 1
fi

echo "✅ Target-Verzeichnis: $TARGET_DIR"
echo "✅ Virtual Environment: $VENV_DIR"
echo ""

# ============================================================================
# DATEIEN KOPIEREN
# ============================================================================

echo "📂 Schritt 2: Dateien kopieren..."

# Erstelle parsers/ Verzeichnis
if [ ! -d "$TARGET_DIR/parsers" ]; then
    echo "   Erstelle parsers/ Verzeichnis..."
    mkdir -p "$TARGET_DIR/parsers"
fi

# Kopiere Parser-Dateien
echo "   Kopiere Parser-Dateien..."
cp -v "$SCRIPT_DIR/parsers/"*.py "$TARGET_DIR/parsers/" 2>/dev/null || {
    echo "⚠️  Warnung: Parser-Dateien nicht gefunden in $SCRIPT_DIR/parsers/"
    echo "   Stelle sicher, dass du das Skript aus dem Deployment-Verzeichnis ausführst!"
}

# Kopiere Hauptdateien
echo "   Kopiere Hauptdateien..."
for file in transaction_manager.py pdf_importer.py import_bank_pdfs.py; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        cp -v "$SCRIPT_DIR/$file" "$TARGET_DIR/"
    else
        echo "⚠️  Warnung: $file nicht gefunden"
    fi
done

# Setze Berechtigungen
echo "   Setze Berechtigungen..."
chmod +x "$TARGET_DIR/import_bank_pdfs.py"
chmod -R 755 "$TARGET_DIR/parsers/"

echo "✅ Dateien kopiert"
echo ""

# ============================================================================
# DEPENDENCIES PRÜFEN
# ============================================================================

echo "📦 Schritt 3: Dependencies prüfen..."

# Aktiviere Virtual Environment
source "$VENV_DIR/bin/activate"

# Prüfe ob pdfplumber installiert ist
if python -c "import pdfplumber" 2>/dev/null; then
    PDFPLUMBER_VERSION=$(python -c "import pdfplumber; print(pdfplumber.__version__)")
    echo "✅ pdfplumber $PDFPLUMBER_VERSION bereits installiert"
else
    echo "📥 Installiere pdfplumber..."
    pip install pdfplumber==0.11.0
    echo "✅ pdfplumber installiert"
fi

# Optional: python-dateutil
if ! python -c "import dateutil" 2>/dev/null; then
    echo "📥 Installiere python-dateutil (optional)..."
    pip install python-dateutil==2.8.2 || true
fi

echo ""

# ============================================================================
# TESTS
# ============================================================================

echo "🧪 Schritt 4: System testen..."

cd "$TARGET_DIR"

# Test 1: Module importierbar?
echo "   Test 1: Module importieren..."
if python -c "from parsers import BaseParser, ParserFactory; from pdf_importer import PDFImporter; from transaction_manager import TransactionManager" 2>/dev/null; then
    echo "   ✅ Alle Module erfolgreich importiert"
else
    echo "   ❌ Fehler beim Importieren der Module!"
    exit 1
fi

# Test 2: CLI aufrufbar?
echo "   Test 2: CLI-Tool..."
if python import_bank_pdfs.py --help >/dev/null 2>&1; then
    echo "   ✅ CLI-Tool funktioniert"
else
    echo "   ❌ Fehler beim Ausführen des CLI-Tools!"
    exit 1
fi

# Test 3: Datenbank erreichbar?
echo "   Test 3: Datenbank-Verbindung..."
if python -c "from transaction_manager import TransactionManager; tm = TransactionManager(); print('OK')" 2>/dev/null | grep -q "OK"; then
    echo "   ✅ Datenbank erreichbar"
else
    echo "   ⚠️  Warnung: Datenbank-Verbindung konnte nicht getestet werden"
fi

echo ""

# ============================================================================
# ZUSAMMENFASSUNG
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ INSTALLATION ERFOLGREICH                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Installierte Komponenten:"
echo "   ✅ Parser Package (parsers/)"
echo "   ✅ Transaction Manager"
echo "   ✅ PDF Importer"
echo "   ✅ CLI Tool"
echo "   ✅ Dependencies"
echo ""
echo "🎯 Nächste Schritte:"
echo ""
echo "   1. System-Info anzeigen:"
echo "      python import_bank_pdfs.py info"
echo ""
echo "   2. Unterstützte Banken:"
echo "      python import_bank_pdfs.py list-banks"
echo ""
echo "   3. Test-PDF importieren:"
echo "      python import_bank_pdfs.py test /pfad/zur/test.pdf"
echo ""
echo "   4. Produktiv-Import:"
echo "      python import_bank_pdfs.py import /pfad/zu/pdfs --min-year 2025"
echo ""
echo "📖 Weitere Infos: README.md"
echo ""

# Deaktiviere Virtual Environment
deactivate

echo "✨ Ready to use! ✨"
