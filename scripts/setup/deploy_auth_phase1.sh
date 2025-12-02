#!/bin/bash
#
# AUTH SYSTEM DEPLOYMENT - PHASE 1
# ==================================
#
# Deployed:
# - LDAP-Connector
# - Datenbank-Schema
# - Requirements
#
# Usage:
#   bash deploy_auth_phase1.sh
#

set -e

echo "========================================"
echo "🔐 AUTH SYSTEM DEPLOYMENT - PHASE 1"
echo "========================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# 1. Requirements installieren
# ============================================================================

echo "📦 Schritt 1/5: Python-Packages installieren..."

cd /opt/greiner-portal

if [ -f "requirements_auth.txt" ]; then
    /opt/greiner-portal/venv/bin/pip install -r requirements_auth.txt --break-system-packages
    echo -e "${GREEN}✅ Packages installiert${NC}"
else
    echo -e "${RED}❌ requirements_auth.txt nicht gefunden!${NC}"
    exit 1
fi

echo ""

# ============================================================================
# 2. Auth-Verzeichnis erstellen
# ============================================================================

echo "📁 Schritt 2/5: Verzeichnis-Struktur erstellen..."

mkdir -p auth
mkdir -p migrations/auth
mkdir -p logs

echo -e "${GREEN}✅ Verzeichnisse erstellt${NC}"
echo ""

# ============================================================================
# 3. LDAP-Connector deployen
# ============================================================================

echo "🔌 Schritt 3/5: LDAP-Connector deployen..."

if [ -f "ldap_connector.py" ]; then
    mv ldap_connector.py auth/ldap_connector.py
    echo -e "${GREEN}✅ LDAP-Connector deployed${NC}"
else
    echo -e "${YELLOW}⚠️  ldap_connector.py nicht gefunden${NC}"
fi

echo ""

# ============================================================================
# 4. Datenbank-Schema anwenden
# ============================================================================

echo "🗄️  Schritt 4/5: Datenbank-Schema erstellen..."

if [ -f "auth_system_schema.sql" ]; then
    mv auth_system_schema.sql migrations/auth/001_auth_system_schema.sql
    
    # Schema anwenden
    sqlite3 data/greiner_controlling.db < migrations/auth/001_auth_system_schema.sql
    
    echo -e "${GREEN}✅ Datenbank-Schema angewandt${NC}"
else
    echo -e "${RED}❌ auth_system_schema.sql nicht gefunden!${NC}"
    exit 1
fi

echo ""

# ============================================================================
# 5. LDAP-Connection testen
# ============================================================================

echo "🧪 Schritt 5/5: LDAP-Connection testen..."

python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/greiner-portal')

try:
    from auth.ldap_connector import LDAPConnector
    
    print("   Erstelle LDAP-Connector...")
    connector = LDAPConnector()
    
    print("   Teste Verbindung...")
    success, message = connector.test_connection()
    
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo ""

# ============================================================================
# Zusammenfassung
# ============================================================================

echo "========================================"
echo "📊 DEPLOYMENT ZUSAMMENFASSUNG"
echo "========================================"
echo ""

echo "Deployed:"
echo "  ✅ Python-Packages (ldap3, Flask-Login, etc.)"
echo "  ✅ auth/ldap_connector.py"
echo "  ✅ migrations/auth/001_auth_system_schema.sql"
echo "  ✅ Datenbank-Tabellen erstellt"
echo ""

echo "Datenbank-Tabellen:"
sqlite3 data/greiner_controlling.db "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%auth%' OR name IN ('users', 'roles', 'sessions')) ORDER BY name;" | while read table; do
    echo "  ✅ $table"
done

echo ""

echo "Standard-Rollen:"
sqlite3 data/greiner_controlling.db "SELECT '  ✅ ' || display_name || ' (' || name || ')' FROM roles WHERE is_system_role = 1;"

echo ""
echo "========================================"
echo ""

echo -e "${GREEN}✅ PHASE 1 DEPLOYMENT ERFOLGREICH!${NC}"
echo ""
echo "🧪 Nächste Schritte:"
echo "   1. Teste LDAP-Connector:"
echo "      python auth/ldap_connector.py"
echo ""
echo "   2. Prüfe Datenbank:"
echo "      sqlite3 data/greiner_controlling.db '.tables'"
echo ""
echo "   3. Warte auf Phase 2:"
echo "      - Auth-Manager"
echo "      - Login-Page"
echo "      - Route-Protection"
echo ""
