#!/bin/bash
# Direkte Metabase Installation (nicht-interaktiv)
# Führt alle Schritte automatisch aus

set -e

echo "=========================================="
echo "Metabase Installation - Direkt"
echo "=========================================="
echo ""

METABASE_DIR="/opt/metabase"
METABASE_VERSION="v0.52.0"
METABASE_JAR="metabase.jar"
MB_PORT=3001

# Schritt 1: Java installieren
echo "Schritt 1/5: Java prüfen/installieren..."
if ! command -v java &> /dev/null; then
    echo "Java wird installiert..."
    apt update
    apt install -y openjdk-17-jre-headless
    echo "✅ Java installiert"
else
    echo "✅ Java bereits installiert: $(java -version 2>&1 | head -1)"
fi

# Schritt 2: Verzeichnis erstellen
echo ""
echo "Schritt 2/5: Verzeichnis erstellen..."
mkdir -p $METABASE_DIR/data
chown -R $SUDO_USER:$SUDO_USER $METABASE_DIR
echo "✅ Verzeichnis erstellt: $METABASE_DIR"

# Schritt 3: Metabase JAR herunterladen
echo ""
echo "Schritt 3/5: Metabase JAR herunterladen..."
if [ ! -f "$METABASE_DIR/$METABASE_JAR" ]; then
    cd $METABASE_DIR
    echo "Lade Metabase $METABASE_VERSION herunter..."
    wget -q --show-progress -O $METABASE_JAR "https://downloads.metabase.com/$METABASE_VERSION/metabase.jar"
    chown $SUDO_USER:$SUDO_USER $METABASE_JAR
    echo "✅ Metabase JAR heruntergeladen"
else
    echo "✅ Metabase JAR bereits vorhanden"
fi

# Schritt 4: systemd Service erstellen
echo ""
echo "Schritt 4/5: systemd Service erstellen..."
tee /etc/systemd/system/metabase.service > /dev/null <<EOF
[Unit]
Description=Metabase Business Intelligence Tool
After=network.target postgresql.service

[Service]
Type=simple
User=$SUDO_USER
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

systemctl daemon-reload
systemctl enable metabase
echo "✅ systemd Service erstellt und aktiviert"

# Schritt 5: Metabase starten
echo ""
echo "Schritt 5/5: Metabase starten..."
systemctl start metabase
echo "✅ Metabase Service gestartet"

# Warte kurz und prüfe Status
echo ""
echo "Warte 5 Sekunden auf Start..."
sleep 5

echo ""
echo "=========================================="
echo "Installation abgeschlossen!"
echo "=========================================="
echo ""
echo "Metabase läuft auf: http://10.80.80.20:$MB_PORT"
echo ""
echo "Status prüfen:"
echo "  sudo systemctl status metabase"
echo ""
echo "Logs anzeigen:"
echo "  sudo journalctl -u metabase -f"
echo ""
echo "Nächste Schritte:"
echo "1. Warte 30-60 Sekunden bis Metabase vollständig gestartet ist"
echo "2. Öffne http://10.80.80.20:$MB_PORT im Browser"
echo "3. Erstelle einen Admin-Account"
echo "4. Verbinde PostgreSQL-Datenbank:"
echo "   - Host: localhost"
echo "   - Port: 5432"
echo "   - Database: drive_portal"
echo "   - User: drive_user"
echo "   - Password: [aus DB-Konfiguration]"
