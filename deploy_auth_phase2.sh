#!/bin/bash

# ============================================================================
# GREINER PORTAL - AUTH-SYSTEM PHASE 2 DEPLOYMENT
# Deployt komplettes Login-System mit Flask-Login Integration
# ============================================================================

echo "========================================================================"
echo "🚀 GREINER PORTAL - AUTH-SYSTEM PHASE 2 DEPLOYMENT"
echo "========================================================================"
echo ""

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Basis-Verzeichnis
BASE_DIR="/opt/greiner-portal"
cd "$BASE_DIR" || exit 1

echo -e "${BLUE}📁 Working Directory: $BASE_DIR${NC}"
echo ""

# ============================================================================
# 1. VIRTUELLE UMGEBUNG AKTIVIEREN
# ============================================================================

echo "1️⃣ Aktiviere virtuelle Umgebung..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ venv aktiviert${NC}"
else
    echo -e "${RED}❌ venv nicht gefunden! Bitte erst erstellen.${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 2. FLASK-LOGIN INSTALLIEREN
# ============================================================================

echo "2️⃣ Installiere Flask-Login..."
pip install flask-login --break-system-packages
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Flask-Login installiert${NC}"
else
    echo -e "${RED}❌ Installation fehlgeschlagen${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 3. VERZEICHNISSTRUKTUR ERSTELLEN
# ============================================================================

echo "3️⃣ Erstelle Verzeichnisstruktur..."

# Auth-Verzeichnis
mkdir -p auth
mkdir -p templates
mkdir -p decorators

echo -e "${GREEN}✅ Verzeichnisse erstellt${NC}"
echo ""

# ============================================================================
# 4. AUTH-DATEIEN VERSCHIEBEN
# ============================================================================

echo "4️⃣ Verschiebe Auth-Dateien..."

# Auth-Manager
if [ -f "auth_manager.py" ]; then
    mv auth_manager.py auth/
    echo -e "${GREEN}✅ auth_manager.py → auth/${NC}"
fi

# Decorators
if [ -f "auth_decorators.py" ]; then
    mv auth_decorators.py decorators/
    echo -e "${GREEN}✅ auth_decorators.py → decorators/${NC}"
fi

# Login Template
if [ -f "login.html" ]; then
    mv login.html templates/
    echo -e "${GREEN}✅ login.html → templates/${NC}"
fi

echo ""

# ============================================================================
# 5. __init__.py DATEIEN ERSTELLEN
# ============================================================================

echo "5️⃣ Erstelle __init__.py Dateien..."

# auth/__init__.py
cat > auth/__init__.py << 'EOF'
"""Auth Package für Greiner Portal"""
from .ldap_connector import LDAPConnector
from .auth_manager import AuthManager, get_auth_manager, User

__all__ = ['LDAPConnector', 'AuthManager', 'get_auth_manager', 'User']
EOF

# decorators/__init__.py
cat > decorators/__init__.py << 'EOF'
"""Decorators Package für Greiner Portal"""
from .auth_decorators import (
    login_required, 
    role_required, 
    permission_required,
    module_required,
    admin_required,
    ajax_login_required,
    api_key_required
)

__all__ = [
    'login_required',
    'role_required', 
    'permission_required',
    'module_required',
    'admin_required',
    'ajax_login_required',
    'api_key_required'
]
EOF

echo -e "${GREEN}✅ __init__.py Dateien erstellt${NC}"
echo ""

# ============================================================================
# 6. SECRET KEY GENERIEREN
# ============================================================================

echo "6️⃣ Generiere SECRET_KEY..."

# Python-Script zum Generieren eines sicheren Secret Keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# In .env Datei speichern
if [ ! -f "config/.env" ]; then
    mkdir -p config
    touch config/.env
fi

# Prüfe ob SECRET_KEY schon existiert
if grep -q "SECRET_KEY=" config/.env; then
    echo -e "${YELLOW}⚠️  SECRET_KEY existiert bereits${NC}"
else
    echo "SECRET_KEY=$SECRET_KEY" >> config/.env
    echo -e "${GREEN}✅ SECRET_KEY generiert und gespeichert${NC}"
fi

# Permissions setzen
chmod 600 config/.env

echo ""

# ============================================================================
# 7. APP.PY BACKUP ERSTELLEN
# ============================================================================

echo "7️⃣ Erstelle Backup von app.py..."

if [ -f "app.py" ]; then
    cp app.py "app.py.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅ Backup erstellt: app.py.backup.*${NC}"
else
    echo -e "${YELLOW}⚠️  app.py nicht gefunden - wird beim ersten Start erstellt${NC}"
fi

echo ""

# ============================================================================
# 8. BERECHTIGUNGEN SETZEN
# ============================================================================

echo "8️⃣ Setze Berechtigungen..."

# Owner setzen
chown -R ag-admin:ag-admin "$BASE_DIR"

# Executable für Scripts
chmod +x deploy_auth_phase2.sh

echo -e "${GREEN}✅ Berechtigungen gesetzt${NC}"
echo ""

# ============================================================================
# 9. STRUKTUR ANZEIGEN
# ============================================================================

echo "9️⃣ Finale Struktur:"
echo ""
tree -L 2 -I 'venv|__pycache__|*.pyc|data' "$BASE_DIR" 2>/dev/null || ls -la
echo ""

# ============================================================================
# 10. ZUSAMMENFASSUNG
# ============================================================================

echo "========================================================================"
echo -e "${GREEN}✅ PHASE 2 DEPLOYMENT ABGESCHLOSSEN!${NC}"
echo "========================================================================"
echo ""
echo "📦 Installiert:"
echo "   ✅ Flask-Login"
echo "   ✅ Auth-Manager (OU-basierte Rollen)"
echo "   ✅ Auth-Decorators (Route-Protection)"
echo "   ✅ Login-Page (moderne UI)"
echo "   ✅ SECRET_KEY generiert"
echo ""
echo "📁 Dateien verschoben:"
echo "   ✅ auth/auth_manager.py"
echo "   ✅ auth/ldap_connector.py"
echo "   ✅ decorators/auth_decorators.py"
echo "   ✅ templates/login.html"
echo ""
echo "🔧 NÄCHSTE SCHRITTE:"
echo ""
echo "1️⃣ App.py integrieren:"
echo "   Öffne: app_integration.py"
echo "   Kopiere die Code-Snippets in deine app.py"
echo ""
echo "2️⃣ Portal Home Template erstellen:"
echo "   Warte auf Phase 3 oder erstelle eigenes Template"
echo ""
echo "3️⃣ App starten:"
echo "   python app.py"
echo ""
echo "4️⃣ Login testen:"
echo "   http://10.80.80.20:5000/login"
echo "   Username: florian.greiner@auto-greiner.de"
echo "   Password: <dein AD-Passwort>"
echo ""
echo "========================================================================"
echo -e "${BLUE}💡 TIPP: Schaue in AUTH_PHASE2_README.md für Details!${NC}"
echo "========================================================================"
