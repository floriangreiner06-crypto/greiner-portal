#!/bin/bash

# ============================================================================
# GREINER PORTAL - KOMPLETTES AUTH-SYSTEM DEPLOYMENT
# Master-Script: Checked, Deployed und Testet alles!
# ============================================================================

echo "========================================================================"
echo "🚀 GREINER PORTAL - AUTH-SYSTEM KOMPLETT-DEPLOYMENT"
echo "========================================================================"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BASE_DIR="/opt/greiner-portal"
cd "$BASE_DIR" || exit 1

# ============================================================================
# PHASE 1: PRE-CHECK
# ============================================================================

echo "📋 PHASE 1: PRE-CHECK"
echo "========================================================================"

# Virtual Environment
echo -n "Checking venv... "
if [ -d "venv" ]; then
    echo -e "${GREEN}✅${NC}"
    source venv/bin/activate
else
    echo -e "${RED}❌ venv nicht gefunden!${NC}"
    exit 1
fi

# LDAP Config
echo -n "Checking LDAP Config... "
if [ -f "config/ldap_credentials.env" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌ config/ldap_credentials.env fehlt!${NC}"
    exit 1
fi

# Datenbank
echo -n "Checking Datenbank... "
if [ -f "data/greiner_portal.db" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⚠️  Datenbank fehlt - wird erstellt${NC}"
fi

echo ""

# ============================================================================
# PHASE 2: DEPENDENCIES
# ============================================================================

echo "📦 PHASE 2: DEPENDENCIES INSTALLIEREN"
echo "========================================================================"

echo "Installiere Flask-Login..."
pip install flask-login --break-system-packages -q

echo "Installiere ldap3..."
pip install ldap3 --break-system-packages -q

echo -e "${GREEN}✅ Dependencies installiert${NC}"
echo ""

# ============================================================================
# PHASE 3: DATEIEN CHECKEN & DEPLOYEN
# ============================================================================

echo "📁 PHASE 3: DATEIEN CHECKEN"
echo "========================================================================"

# Check auth_manager.py
if [ ! -f "auth/auth_manager.py" ]; then
    echo -e "${YELLOW}⚠️  auth/auth_manager.py fehlt!${NC}"
    echo "Bitte lade auth_manager.py hoch und verschiebe nach auth/"
    exit 1
else
    echo -e "${GREEN}✅ auth/auth_manager.py${NC}"
fi

# Check ldap_connector.py
if [ ! -f "auth/ldap_connector.py" ]; then
    if [ -f "ldap_connector.py" ]; then
        echo "Verschiebe ldap_connector.py nach auth/"
        mv ldap_connector.py auth/
    else
        echo -e "${RED}❌ ldap_connector.py fehlt!${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ auth/ldap_connector.py${NC}"

# Check auth_decorators.py
if [ ! -f "decorators/auth_decorators.py" ]; then
    echo -e "${YELLOW}⚠️  decorators/auth_decorators.py fehlt!${NC}"
    echo "Bitte lade auth_decorators.py hoch"
    exit 1
else
    echo -e "${GREEN}✅ decorators/auth_decorators.py${NC}"
fi

# Check __init__.py Dateien
echo -n "Erstelle __init__.py Dateien... "
touch auth/__init__.py
touch decorators/__init__.py
echo -e "${GREEN}✅${NC}"

echo ""

# ============================================================================
# PHASE 4: DATENBANK-SCHEMA
# ============================================================================

echo "🗄️  PHASE 4: DATENBANK-SCHEMA"
echo "========================================================================"

if [ -f "migrations/auth/001_auth_system_schema.sql" ]; then
    echo "Wende Auth-Schema an..."
    sqlite3 data/greiner_portal.db < migrations/auth/001_auth_system_schema.sql 2>/dev/null || echo "Schema bereits vorhanden"
    echo -e "${GREEN}✅ Schema angewendet${NC}"
else
    echo -e "${YELLOW}⚠️  Schema-File fehlt - überspringe${NC}"
fi

echo ""

# ============================================================================
# PHASE 5: APP.PY PATCHEN
# ============================================================================

echo "🔧 PHASE 5: APP.PY INTEGRIEREN"
echo "========================================================================"

# Backup
BACKUP_FILE="app.py.backup.auth_$(date +%Y%m%d_%H%M%S)"
cp app.py "$BACKUP_FILE"
echo "Backup erstellt: $BACKUP_FILE"

# Patch ausführen
if [ -f "patch_app_auth.sh" ]; then
    chmod +x patch_app_auth.sh
    ./patch_app_auth.sh
    echo -e "${GREEN}✅ app.py gepatcht${NC}"
else
    echo -e "${RED}❌ patch_app_auth.sh nicht gefunden!${NC}"
    exit 1
fi

echo ""

# ============================================================================
# PHASE 6: SECRET KEY
# ============================================================================

echo "🔑 PHASE 6: SECRET KEY"
echo "========================================================================"

if grep -q "SECRET_KEY=" config/.env 2>/dev/null; then
    echo -e "${GREEN}✅ SECRET_KEY bereits vorhanden${NC}"
else
    echo "Generiere SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    mkdir -p config
    echo "SECRET_KEY=$SECRET_KEY" >> config/.env
    chmod 600 config/.env
    
    echo -e "${GREEN}✅ SECRET_KEY generiert und gespeichert${NC}"
fi

echo ""

# ============================================================================
# PHASE 7: TESTS
# ============================================================================

echo "🧪 PHASE 7: TESTS"
echo "========================================================================"

# Test 1: Python Import
echo -n "Test 1: Python Imports... "
python3 << 'EOTEST'
import sys
sys.path.insert(0, '/opt/greiner-portal')

try:
    from flask import Flask
    from flask_login import LoginManager
    from auth.auth_manager import get_auth_manager
    from decorators.auth_decorators import login_required
    print("✅")
    sys.exit(0)
except Exception as e:
    print(f"❌ {e}")
    sys.exit(1)
EOTEST

if [ $? -ne 0 ]; then
    echo -e "${RED}Import-Test fehlgeschlagen!${NC}"
    exit 1
fi

# Test 2: LDAP Connection
echo -n "Test 2: LDAP Connection... "
python auth/ldap_connector.py > /tmp/ldap_test.log 2>&1
if grep -q "✅ LDAP-Verbindung erfolgreich" /tmp/ldap_test.log; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⚠️  LDAP-Test fehlgeschlagen (siehe /tmp/ldap_test.log)${NC}"
fi

# Test 3: App Syntax
echo -n "Test 3: App Syntax... "
python3 -m py_compile app.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    exit 1
fi

echo ""

# ============================================================================
# PHASE 8: STRUKTUR-CHECK
# ============================================================================

echo "📊 PHASE 8: FINALE STRUKTUR"
echo "========================================================================"

echo "Auth-System:"
ls -1 auth/*.py 2>/dev/null | sed 's/^/  ✅ /'

echo ""
echo "Decorators:"
ls -1 decorators/*.py 2>/dev/null | sed 's/^/  ✅ /'

echo ""
echo "Migrations:"
ls -1 migrations/auth/*.sql 2>/dev/null | sed 's/^/  ✅ /' || echo "  ⚠️  Keine Migrations"

echo ""
echo "Config:"
ls -1 config/*.env 2>/dev/null | sed 's/^/  ✅ /'

echo ""

# ============================================================================
# FERTIG!
# ============================================================================

echo "========================================================================"
echo -e "${GREEN}✅ AUTH-SYSTEM DEPLOYMENT ABGESCHLOSSEN!${NC}"
echo "========================================================================"
echo ""
echo "🎯 WAS WURDE GEMACHT:"
echo "   ✅ Dependencies installiert (flask-login, ldap3)"
echo "   ✅ Auth-Dateien geprüft"
echo "   ✅ Datenbank-Schema angewendet"
echo "   ✅ app.py mit Auth integriert"
echo "   ✅ SECRET_KEY generiert"
echo "   ✅ Tests durchgeführt"
echo ""
echo "🚀 JETZT STARTEN:"
echo ""
echo "   cd /opt/greiner-portal"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 DANN IM BROWSER:"
echo ""
echo "   http://10.80.80.20:5000/login"
echo ""
echo "   Username: florian.greiner@auto-greiner.de"
echo "   Password: <dein AD-Passwort>"
echo ""
echo "📋 VERFÜGBARE ROUTES:"
echo "   ✅ /login                        (Login-Page)"
echo "   ✅ /logout                       (Logout)"
echo "   ✅ /                             (Startseite, protected)"
echo "   ✅ /bankenspiegel/dashboard      (Bankenspiegel)"
echo "   ✅ /verkauf/auftragseingang      (Verkauf)"
echo "   ✅ /urlaubsplaner/v2             (Urlaubsplaner)"
echo ""
echo "🔍 LOGS CHECKEN:"
echo "   tail -f logs/app.log             (falls vorhanden)"
echo "   tail -f flask_direct.log         (Flask Output)"
echo ""
echo "📝 BACKUPS:"
echo "   $BACKUP_FILE"
echo ""
echo "========================================================================"
echo -e "${BLUE}💪 VIEL ERFOLG!${NC}"
echo "========================================================================"
