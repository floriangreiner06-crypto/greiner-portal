#!/bin/bash
# Metabase Installation Script für DRIVE Portal
# Installiert Metabase als Docker-Container

set -e

echo "=== Metabase Installation für DRIVE Portal ==="

# Prüfe ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo "Docker wird installiert..."
    sudo apt update
    sudo apt install -y docker.io
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo "Docker installiert. Bitte neu einloggen oder 'newgrp docker' ausführen."
fi

# Erstelle Metabase-Verzeichnis
METABASE_DIR="/opt/metabase"
sudo mkdir -p $METABASE_DIR/data
sudo chown -R $USER:$USER $METABASE_DIR

# Hole DB-Credentials aus .env oder verwende Defaults
if [ -f "/opt/greiner-portal/.env" ]; then
    source /opt/greiner-portal/.env
fi

DB_HOST=${DB_HOST:-localhost}
DB_NAME=${DB_NAME:-drive_portal}
DB_USER=${DB_USER:-drive_user}
DB_PASSWORD=${DB_PASSWORD:-""}

echo "Verwende DB: $DB_NAME auf $DB_HOST"

# Starte Metabase Container
echo "Starte Metabase Container..."
docker run -d \
  --name metabase \
  --restart unless-stopped \
  -p 3000:3000 \
  -v $METABASE_DIR/data:/metabase-data \
  -e "MB_DB_FILE=/metabase-data/metabase.db" \
  metabase/metabase:latest

echo ""
echo "=== Metabase Installation abgeschlossen ==="
echo ""
echo "Metabase läuft auf: http://10.80.80.20:3000"
echo ""
echo "Nächste Schritte:"
echo "1. Öffne http://10.80.80.20:3000 im Browser"
echo "2. Erstelle einen Admin-Account"
echo "3. Verbinde PostgreSQL-Datenbank:"
echo "   - Host: $DB_HOST"
echo "   - Port: 5432"
echo "   - Database: $DB_NAME"
echo "   - User: $DB_USER"
echo "   - Password: [aus .env]"
echo ""
echo "Container-Status prüfen: docker ps | grep metabase"
echo "Logs anzeigen: docker logs metabase"
