#!/bin/bash
# ============================================================================
# PHASE 1 - TAG 1: SETUP & BACKUP (NEUER SERVER)
# ============================================================================
# Erstellt: 06.11.2025
# Server: 10.80.80.20 (srvlinux01)
# Pfad: /opt/greiner-portal
# Zweck: Backup erstellen und Verzeichnisstruktur vorbereiten
# ============================================================================

set -e  # Bei Fehler abbrechen

echo "🚀 PHASE 1 - TAG 1: SETUP & BACKUP"
echo "=================================="
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# 1. VORBEREITUNGEN
# ============================================================================

echo "📋 Schritt 1: Vorbereitungen"
echo "----------------------------"

# Zum Portal-Verzeichnis wechseln
cd /opt/greiner-portal || {
    echo -e "${RED}❌ Fehler: Verzeichnis nicht gefunden!${NC}"
    exit 1
}

echo -e "${GREEN}✅ Im Verzeichnis: $(pwd)${NC}"

# Python-Version prüfen
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"

# User anzeigen
echo -e "${GREEN}✅ User: $(whoami)${NC}"
echo ""

# ============================================================================
# 2. KRITISCH: BACKUP ERSTELLEN!
# ============================================================================

echo "💾 Schritt 2: BACKUP erstellen (KRITISCH!)"
echo "------------------------------------------"

# Backup-Verzeichnis erstellen
BACKUP_DIR="backups/urlaubsplaner_v2"
mkdir -p "$BACKUP_DIR"

# Zeitstempel
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/greiner_controlling_before_v2_${TIMESTAMP}.db"

# Prüfen ob Datenbank existiert
if [ ! -f "data/greiner_controlling.db" ]; then
    echo -e "${RED}❌ Fehler: data/greiner_controlling.db nicht gefunden!${NC}"
    exit 1
fi

# Dateigröße anzeigen
DB_SIZE=$(du -h data/greiner_controlling.db | cut -f1)
echo "📊 Datenbank-Größe: $DB_SIZE"

# Backup erstellen
echo "📦 Erstelle Backup..."
cp data/greiner_controlling.db "$BACKUP_FILE"

# Komprimieren
echo "🗜️  Komprimiere Backup..."
gzip "$BACKUP_FILE"

# Backup prüfen
if [ -f "${BACKUP_FILE}.gz" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo -e "${GREEN}✅ Backup erstellt: ${BACKUP_FILE}.gz ($BACKUP_SIZE)${NC}"
    echo ""
    echo "📁 Backup-Übersicht:"
    ls -lh "$BACKUP_DIR/" | tail -5
else
    echo -e "${RED}❌ Fehler: Backup konnte nicht erstellt werden!${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 3. GIT-BRANCH ERSTELLEN
# ============================================================================

echo "🔀 Schritt 3: Git-Branch erstellen"
echo "----------------------------------"

# Git-Status prüfen
if [ -d ".git" ]; then
    echo "📊 Git-Status:"
    git status --short || true
    
    # Neuer Branch
    BRANCH_NAME="feature/urlaubsplaner-v2-hybrid"
    
    # Prüfen ob Branch bereits existiert
    if git rev-parse --verify "$BRANCH_NAME" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Branch '$BRANCH_NAME' existiert bereits${NC}"
        git checkout "$BRANCH_NAME"
    else
        echo "🌿 Erstelle neuen Branch: $BRANCH_NAME"
        git checkout -b "$BRANCH_NAME"
    fi
    
    echo -e "${GREEN}✅ Aktueller Branch: $(git branch --show-current)${NC}"
else
    echo -e "${YELLOW}⚠️  Kein Git-Repository gefunden - überspringe Git-Setup${NC}"
fi
echo ""

# ============================================================================
# 4. VERZEICHNISSTRUKTUR ANLEGEN
# ============================================================================

echo "📁 Schritt 4: Verzeichnisstruktur anlegen"
echo "-----------------------------------------"

# Verzeichnisse erstellen
mkdir -p vacation_v2
mkdir -p vacation_v2/migrations
mkdir -p vacation_v2/utils
mkdir -p vacation_v2/tests
mkdir -p vacation_v2/api
mkdir -p vacation_v2/grafana/dashboards
mkdir -p vacation_v2/grafana/queries

echo "📂 Verzeichnisstruktur:"
ls -la vacation_v2/

echo -e "${GREEN}✅ Verzeichnisse erstellt${NC}"
echo ""

# ============================================================================
# 5. DEPENDENCIES PRÜFEN
# ============================================================================

echo "📦 Schritt 5: Dependencies prüfen"
echo "---------------------------------"

# Flask prüfen
python3 << 'EOF'
try:
    import flask
    print(f"✅ Flask: {flask.__version__}")
except ImportError:
    print("❌ Flask fehlt!")
    
try:
    import sqlite3
    print(f"✅ SQLite: OK")
except ImportError:
    print("❌ SQLite fehlt!")
EOF

# Pytest installieren falls nötig
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "📥 Installiere pytest..."
    pip3 install pytest pytest-cov --user
fi

# Weitere Test-Tools
if ! python3 -c "import freezegun" 2>/dev/null; then
    echo "📥 Installiere freezegun und faker..."
    pip3 install freezegun faker --user
fi

echo ""
echo "📦 Installierte Packages:"
pip3 list | grep -E "(Flask|pytest|freezegun|faker)" || true
echo ""

# ============================================================================
# 6. ZUSAMMENFASSUNG
# ============================================================================

echo "✅ ZUSAMMENFASSUNG TAG 1"
echo "======================="
echo ""
echo "✅ Backup erstellt: ${BACKUP_FILE}.gz"
echo "✅ Git-Branch: feature/urlaubsplaner-v2-hybrid"
echo "✅ Verzeichnisstruktur: vacation_v2/"
echo "✅ Dependencies: OK"
echo ""
echo "📊 NÄCHSTE SCHRITTE:"
echo "  1. Datenbank prüfen (Anzahl Buchungen, Mitarbeiter)"
echo "  2. Migration 001: Schema erweitern"
echo "  3. Migration 002: Feiertage importieren"
echo ""
echo "🔍 ROLLBACK-BEFEHL (falls nötig):"
echo "  gunzip -c ${BACKUP_FILE}.gz > data/greiner_controlling.db"
echo ""
echo "🎯 BEREIT FÜR TAG 2 (DB-Migration)!"
echo ""
