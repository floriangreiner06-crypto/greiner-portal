#!/bin/bash
# Metabase Installation als JAR (ohne Docker)
# Einfacher für Server ohne Docker

set -e

echo "=== Metabase Installation (JAR) für DRIVE Portal ==="

METABASE_DIR="/opt/metabase"
METABASE_VERSION="v0.52.0"
METABASE_JAR="metabase.jar"

# Erstelle Verzeichnis
sudo mkdir -p $METABASE_DIR/data
sudo chown -R $USER:$USER $METABASE_DIR

# Prüfe Java
if ! command -v java &> /dev/null; then
    echo "Java wird installiert..."
    sudo apt update
    sudo apt install -y openjdk-17-jre-headless
fi

# Lade Metabase JAR herunter
if [ ! -f "$METABASE_DIR/$METABASE_JAR" ]; then
    echo "Lade Metabase herunter..."
    cd $METABASE_DIR
    wget -O $METABASE_JAR "https://downloads.metabase.com/$METABASE_VERSION/metabase.jar"
    echo "Metabase JAR heruntergeladen"
fi

# Port-Konfiguration (Grafana läuft bereits auf 3000)
# Metabase wird auf Port 3001 installiert
MB_PORT=3001
echo "Metabase wird auf Port $MB_PORT installiert (Grafana nutzt Port 3000)"

# Erstelle systemd Service
sudo tee /etc/systemd/system/metabase.service > /dev/null <<EOF
[Unit]
Description=Metabase Business Intelligence Tool
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$METABASE_DIR
ExecStart=/usr/bin/java -jar $METABASE_DIR/$METABASE_JAR
Restart=always
RestartSec=10
Environment="MB_DB_FILE=$METABASE_DIR/data/metabase.db"
Environment="MB_JETTY_PORT=$MB_PORT"
Environment="JAVA_OPTS=-Xmx2g -Xms1g"

[Install]
WantedBy=multi-user.target
EOF

# Starte Service
sudo systemctl daemon-reload
sudo systemctl enable metabase
sudo systemctl start metabase

echo ""
echo "=== Metabase Installation abgeschlossen ==="
echo ""
echo "Metabase läuft auf: http://10.80.80.20:$MB_PORT"
echo ""
echo "Status prüfen: sudo systemctl status metabase"
echo "Logs anzeigen: sudo journalctl -u metabase -f"
echo ""
echo "Nächste Schritte:"
echo "1. Warte 30-60 Sekunden bis Metabase gestartet ist"
echo "2. Öffne http://10.80.80.20:$MB_PORT im Browser"
echo "3. Erstelle einen Admin-Account"
echo "4. Verbinde PostgreSQL-Datenbank:"
echo "   - Host: localhost"
echo "   - Port: 5432"
echo "   - Database: drive_portal"
echo "   - User: drive_user"
echo "   - Password: [aus DB-Konfiguration]"
