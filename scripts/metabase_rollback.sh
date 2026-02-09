#!/bin/bash
# Rollback-Skript für Metabase-Installation
# Stellt den Zustand vor der Installation wieder her

set -e

if [ -z "$1" ]; then
    echo "Fehler: Backup-Verzeichnis nicht angegeben"
    echo "Usage: sudo bash metabase_rollback.sh <BACKUP_DIR>"
    echo ""
    echo "Verfügbare Backups:"
    ls -d /opt/greiner-portal/backups/metabase_* 2>/dev/null | tail -5
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Fehler: Backup-Verzeichnis nicht gefunden: $BACKUP_DIR"
    exit 1
fi

echo "=== Metabase Rollback ==="
echo "Backup-Verzeichnis: $BACKUP_DIR"
echo ""
read -p "Möchten Sie wirklich zurücksetzen? (ja/nein): " confirm

if [ "$confirm" != "ja" ]; then
    echo "Rollback abgebrochen"
    exit 0
fi

# Stoppe Metabase Service
echo "Stoppe Metabase..."
sudo systemctl stop metabase 2>/dev/null || true
sudo systemctl disable metabase 2>/dev/null || true

# Entferne Service
if [ -f "/etc/systemd/system/metabase.service" ]; then
    echo "Entferne Metabase Service..."
    sudo rm /etc/systemd/system/metabase.service
    sudo systemctl daemon-reload
fi

# Stelle Metabase-Verzeichnis wieder her (falls Backup vorhanden)
if [ -f "$BACKUP_DIR/metabase_data.tar.gz" ]; then
    echo "Stelle Metabase-Daten wieder her..."
    sudo rm -rf /opt/metabase
    sudo tar -xzf "$BACKUP_DIR/metabase_data.tar.gz" -C /opt
else
    echo "Entferne Metabase-Verzeichnis..."
    sudo rm -rf /opt/metabase
fi

# Stelle Service wieder her (falls Backup vorhanden)
if [ -f "$BACKUP_DIR/metabase.service.bak" ]; then
    echo "Stelle Metabase Service wieder her..."
    sudo cp "$BACKUP_DIR/metabase.service.bak" /etc/systemd/system/metabase.service
    sudo systemctl daemon-reload
    sudo systemctl enable metabase
    sudo systemctl start metabase
fi

# Prüfe Docker Container (falls Docker-Version)
if docker ps -a | grep -q metabase; then
    echo "Entferne Metabase Docker Container..."
    docker stop metabase 2>/dev/null || true
    docker rm metabase 2>/dev/null || true
fi

echo ""
echo "=== Rollback abgeschlossen ==="
echo "Metabase wurde vollständig entfernt/wiederhergestellt"
echo ""
echo "Prüfe Status:"
echo "  - Service: systemctl status metabase"
echo "  - Port 3000: netstat -tlnp | grep 3000"
echo "  - Docker: docker ps -a | grep metabase"
