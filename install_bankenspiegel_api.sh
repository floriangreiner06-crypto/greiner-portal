#!/bin/bash
# ============================================================================
# BANKENSPIEGEL API - INSTALLATION
# ============================================================================
# Beschreibung: Integriert Bankenspiegel API in bestehendes Flask-Portal
# Verwendung: ./install_bankenspiegel_api.sh
# ============================================================================

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}BANKENSPIEGEL API - INSTALLATION${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

# Pfade
PORTAL_DIR="/opt/greiner-portal"
API_DIR="$PORTAL_DIR/api"
APP_FILE="$PORTAL_DIR/app.py"

# 1. API-Verzeichnis erstellen
echo -e "${YELLOW}📁 Erstelle API-Verzeichnis...${NC}"
mkdir -p "$API_DIR"
echo -e "${GREEN}✅ API-Verzeichnis erstellt: $API_DIR${NC}"
echo ""

# 2. API-Datei kopieren
echo -e "${YELLOW}📄 Kopiere bankenspiegel_api.py...${NC}"
if [ -f "bankenspiegel_api.py" ]; then
    cp bankenspiegel_api.py "$API_DIR/"
    echo -e "${GREEN}✅ API-Datei kopiert${NC}"
else
    echo -e "${RED}❌ ERROR: bankenspiegel_api.py nicht gefunden!${NC}"
    exit 1
fi
echo ""

# 3. __init__.py erstellen (falls nicht vorhanden)
echo -e "${YELLOW}📄 Erstelle api/__init__.py...${NC}"
cat > "$API_DIR/__init__.py" << 'EOF'
"""
API Package für Greiner Portal
"""
EOF
echo -e "${GREEN}✅ __init__.py erstellt${NC}"
echo ""

# 4. Backup von app.py erstellen
echo -e "${YELLOW}💾 Erstelle Backup von app.py...${NC}"
BACKUP_FILE="$APP_FILE.backup_$(date +%Y%m%d_%H%M%S)"
cp "$APP_FILE" "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup erstellt: $BACKUP_FILE${NC}"
echo ""

# 5. Prüfen ob Blueprint bereits registriert ist
echo -e "${YELLOW}🔍 Prüfe ob API bereits registriert ist...${NC}"
if grep -q "bankenspiegel_api" "$APP_FILE"; then
    echo -e "${YELLOW}⚠️  Bankenspiegel API bereits in app.py gefunden - wird übersprungen${NC}"
else
    echo -e "${YELLOW}➕ Füge Bankenspiegel API zu app.py hinzu...${NC}"
    
    # API-Import und Registrierung am Ende einfügen (vor app.run() falls vorhanden)
    cat >> "$APP_FILE" << 'EOF'

# ============================================================================
# BANKENSPIEGEL REST API
# ============================================================================
from api.bankenspiegel_api import bankenspiegel_api
app.register_blueprint(bankenspiegel_api)
print("✅ Bankenspiegel API registriert: /api/bankenspiegel/")

EOF
    
    echo -e "${GREEN}✅ Bankenspiegel API zu app.py hinzugefügt${NC}"
fi
echo ""

# 6. Flask neu starten
echo -e "${YELLOW}🔄 Starte Flask-Server neu...${NC}"

# Flask-Prozess finden und beenden
FLASK_PID=$(ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}')
if [ -n "$FLASK_PID" ]; then
    echo -e "${YELLOW}   Stoppe Flask (PID: $FLASK_PID)...${NC}"
    kill $FLASK_PID
    sleep 2
fi

# Flask im Hintergrund starten
cd "$PORTAL_DIR"
source venv/bin/activate
nohup python3 app.py > logs/flask.log 2>&1 &
NEW_PID=$!
echo -e "${GREEN}✅ Flask gestartet (PID: $NEW_PID)${NC}"
echo ""

# 7. Warten auf Flask-Start
echo -e "${YELLOW}⏳ Warte auf Flask-Start (5 Sekunden)...${NC}"
sleep 5
echo ""

# 8. Health Check
echo -e "${YELLOW}🏥 Teste API Health-Endpoint...${NC}"
HEALTH_CHECK=$(curl -s http://localhost:5000/api/bankenspiegel/health)

if echo "$HEALTH_CHECK" | grep -q '"success": true'; then
    echo -e "${GREEN}✅ API ist erreichbar und funktionsfähig!${NC}"
    echo ""
    echo "$HEALTH_CHECK" | python3 -m json.tool
else
    echo -e "${RED}❌ API antwortet nicht korrekt${NC}"
    echo "$HEALTH_CHECK"
fi
echo ""

# 9. Zusammenfassung
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}🎉 INSTALLATION ERFOLGREICH!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${YELLOW}📍 API-ENDPOINTS:${NC}"
echo ""
echo "  Dashboard:      http://localhost:5000/api/bankenspiegel/dashboard"
echo "  Konten:         http://localhost:5000/api/bankenspiegel/konten"
echo "  Transaktionen:  http://localhost:5000/api/bankenspiegel/transaktionen"
echo "  Health:         http://localhost:5000/api/bankenspiegel/health"
echo ""
echo -e "${YELLOW}📍 VIA NGINX (öffentlich):${NC}"
echo ""
echo "  http://10.80.80.20/api/bankenspiegel/dashboard"
echo "  http://10.80.80.20/api/bankenspiegel/konten"
echo "  http://10.80.80.20/api/bankenspiegel/transaktionen"
echo ""
echo -e "${YELLOW}📝 LOGS:${NC}"
echo "  tail -f $PORTAL_DIR/logs/flask.log"
echo ""
echo -e "${YELLOW}💾 BACKUP:${NC}"
echo "  $BACKUP_FILE"
echo ""
