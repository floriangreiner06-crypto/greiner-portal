#!/bin/bash
# ========================================
# GREINER PORTAL - FEATURE ANALYSE SCRIPT
# ========================================
# Systematische Überprüfung aller Features
# und Erstellung eines Status-Reports

echo "🔍 GREINER PORTAL - FEATURE ANALYSE"
echo "===================================="
echo ""
echo "📅 Analyse-Datum: $(date '+%Y-%m-%d %H:%M:%S')"
echo "👤 User: $(whoami)"
echo "📂 Verzeichnis: $(pwd)"
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========================================
# 1. GIT STATUS
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 1. GIT STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git branch --show-current
git log --oneline -5
echo ""

# ========================================
# 2. VERZEICHNIS-STRUKTUR
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 2. VERZEICHNIS-STRUKTUR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Hauptverzeichnisse:"
ls -la | grep "^d" | awk '{print "  - " $9}' | grep -v "^\.$\|^\.\.$"
echo ""

# ========================================
# 3. PYTHON-DATEIEN ÜBERSICHT
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 3. PYTHON-DATEIEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "App-Struktur:"
find app -name "*.py" -type f 2>/dev/null | head -20 | sed 's/^/  /'
echo ""
echo "Root Python-Dateien:"
ls -1 *.py 2>/dev/null | sed 's/^/  /'
echo ""

# ========================================
# 4. ROUTEN-ANALYSE
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛣️  4. FLASK ROUTEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ -d "app/routes" ]; then
    echo "Route-Dateien:"
    ls -1 app/routes/*.py 2>/dev/null | sed 's/^/  /'
    echo ""
    echo "Definierte Routen (Auszug):"
    grep -rh "@.*\.route" app/routes/ 2>/dev/null | sed 's/^/  /' | head -20
else
    echo "  ⚠️  Verzeichnis app/routes nicht gefunden"
fi
echo ""

# ========================================
# 5. TEMPLATES
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 5. JINJA TEMPLATES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ -d "app/templates" ]; then
    echo "Template-Dateien:"
    find app/templates -name "*.html" 2>/dev/null | sed 's/^/  /'
else
    echo "  ⚠️  Verzeichnis app/templates nicht gefunden"
fi
echo ""

# ========================================
# 6. STATIC FILES
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 6. STATIC FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ -d "static" ]; then
    echo "CSS-Dateien:"
    find static -name "*.css" 2>/dev/null | sed 's/^/  /'
    echo ""
    echo "JS-Dateien:"
    find static -name "*.js" 2>/dev/null | sed 's/^/  /'
else
    echo "  ⚠️  Verzeichnis static nicht gefunden"
fi
echo ""

# ========================================
# 7. KONFIGURATION
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  7. KONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Config-Dateien:"
ls -1 config*.py .env* 2>/dev/null | sed 's/^/  /'
if [ -d "config" ]; then
    ls -1 config/* 2>/dev/null | sed 's/^/  /'
fi
echo ""

# ========================================
# 8. DATENBANK-PARSER
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏦 8. BANK-PARSER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Parser-Dateien:"
ls -1 *parser*.py 2>/dev/null | sed 's/^/  /'
echo ""

# ========================================
# 9. REQUIREMENTS
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 9. PYTHON PACKAGES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ -f "requirements.txt" ]; then
    echo "Installierte Packages (Auszug):"
    head -20 requirements.txt | sed 's/^/  /'
else
    echo "  ⚠️  requirements.txt nicht gefunden"
fi
echo ""

# ========================================
# 10. SYSTEMD SERVICE
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 10. SYSTEMD SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if systemctl list-units --type=service | grep -q greiner; then
    SERVICE_NAME=$(systemctl list-units --type=service | grep greiner | awk '{print $1}')
    echo "Service gefunden: $SERVICE_NAME"
    systemctl status $SERVICE_NAME --no-pager | head -10
else
    echo "  ⚠️  Kein greiner-Service gefunden"
fi
echo ""

# ========================================
# 11. LETZTE SESSIONS
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 11. LETZTE SESSIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ -d "docs/sessions" ]; then
    echo "Letzte 5 Session-Dateien:"
    ls -lt docs/sessions/*.md 2>/dev/null | head -5 | awk '{print "  " $9 " (" $6 " " $7 " " $8 ")"}'
else
    echo "  ⚠️  Verzeichnis docs/sessions nicht gefunden"
fi
echo ""

# ========================================
# ZUSAMMENFASSUNG
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ANALYSE ABGESCHLOSSEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Nächste Schritte:"
echo "  1. Obige Ausgabe prüfen"
echo "  2. Fehlende Komponenten identifizieren"
echo "  3. Features manuell testen"
echo "  4. PROJECT_STATUS.md aktualisieren"
echo ""
echo "💡 Tipp: Output in Datei speichern mit:"
echo "   ./analyze_system.sh > system_analyse_$(date +%Y%m%d_%H%M).txt"
echo ""
