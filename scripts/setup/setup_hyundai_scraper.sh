#!/bin/bash
# Hyundai Finance Scraper - Installation und Setup
# Server: 10.80.80.20

set -e  # Bei Fehler abbrechen

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   HYUNDAI FINANCE SCRAPER - INSTALLATION                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verzeichnisse
PORTAL_DIR="/opt/greiner-portal"
TOOLS_DIR="$PORTAL_DIR/tools/scrapers"
VENV_DIR="$PORTAL_DIR/venv"

echo "📁 Verzeichnisse:"
echo "   Portal: $PORTAL_DIR"
echo "   Tools: $TOOLS_DIR"
echo "   VEnv: $VENV_DIR"
echo ""

# Schritt 1: Verzeichnisse erstellen
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 SCHRITT 1: Verzeichnisse erstellen"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p "$TOOLS_DIR"
touch "$TOOLS_DIR/__init__.py"

echo -e "${GREEN}✓${NC} Verzeichnisse erstellt"
echo ""

# Schritt 2: System-Pakete installieren
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 SCHRITT 2: System-Pakete installieren"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "⚠️  Benötigt sudo-Rechte!"
echo "   Installiere: chromium-browser, chromium-chromedriver"
echo ""

sudo apt-get update -qq
sudo apt-get install -y chromium-browser chromium-chromedriver

echo -e "${GREEN}✓${NC} System-Pakete installiert"
echo ""

# Schritt 3: Python-Dependencies installieren
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 SCHRITT 3: Python-Dependencies installieren"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PORTAL_DIR"

# Virtual Environment aktivieren
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✓${NC} Virtual Environment aktiviert"
else
    echo -e "${RED}✗${NC} Virtual Environment nicht gefunden!"
    exit 1
fi

# Selenium installieren
pip install selenium webdriver-manager --quiet

echo -e "${GREEN}✓${NC} Python-Dependencies installiert"
echo ""

# Schritt 4: Versions-Info
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ℹ️  VERSIONS-INFORMATIONEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Chrome/Chromium:"
chromium-browser --version 2>/dev/null || chromium --version 2>/dev/null || echo "  Nicht gefunden!"

echo ""
echo "ChromeDriver:"
chromedriver --version 2>/dev/null || echo "  Nicht gefunden!"

echo ""
echo "Python-Pakete:"
pip list | grep selenium

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ INSTALLATION ABGESCHLOSSEN!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 NÄCHSTE SCHRITTE:"
echo "   1. Tester-Script erstellen: nano tools/scrapers/hyundai_finance_tester.py"
echo "   2. Ausführbar machen: chmod +x tools/scrapers/hyundai_finance_tester.py"
echo "   3. Test ausführen: python3 tools/scrapers/hyundai_finance_tester.py"
echo ""
