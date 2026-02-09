#!/bin/bash
# Sichere Metabase Installation mit Rollback-Möglichkeit
# Führt automatisch Backup durch und ermöglicht einfachen Rollback

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/opt/greiner-portal"
BACKUP_SCRIPT="$SCRIPT_DIR/metabase_backup.sh"
INSTALL_SCRIPT="$SCRIPT_DIR/install_metabase_jar.sh"
ROLLBACK_SCRIPT="$SCRIPT_DIR/metabase_rollback.sh"

echo "=========================================="
echo "Metabase Installation (mit Rollback)"
echo "=========================================="
echo ""

# Prüfe ob bereits installiert
if systemctl is-active --quiet metabase 2>/dev/null; then
    echo "⚠️  Metabase läuft bereits!"
    echo ""
    read -p "Möchten Sie die Installation trotzdem fortsetzen? (ja/nein): " continue_install
    if [ "$continue_install" != "ja" ]; then
        echo "Installation abgebrochen"
        exit 0
    fi
fi

# Prüfe Port 3001 (Metabase wird auf 3001 installiert, Grafana nutzt 3000)
if netstat -tlnp 2>/dev/null | grep -q :3001; then
    echo "⚠️  Port 3001 ist bereits belegt!"
    netstat -tlnp 2>/dev/null | grep :3001
    echo ""
    read -p "Möchten Sie trotzdem fortfahren? (ja/nein): " continue_port
    if [ "$continue_port" != "ja" ]; then
        echo "Installation abgebrochen"
        exit 1
    fi
else
    echo "✅ Port 3001 ist frei (Grafana läuft auf Port 3000)"
fi

# Schritt 1: Backup
echo ""
echo "Schritt 1/3: Backup erstellen..."
bash "$BACKUP_SCRIPT"
BACKUP_DIR=$(ls -td /opt/greiner-portal/backups/metabase_* | head -1)
echo "✅ Backup erstellt: $BACKUP_DIR"
echo ""

# Schritt 2: Installation
echo "Schritt 2/3: Metabase installieren..."
echo "Hinweis: Benötigt sudo-Rechte für Java-Installation"
echo ""
read -p "Installation starten? (ja/nein): " start_install

if [ "$start_install" != "ja" ]; then
    echo "Installation abgebrochen"
    exit 0
fi

# Führe Installation aus
bash "$INSTALL_SCRIPT"
INSTALL_EXIT=$?

if [ $INSTALL_EXIT -ne 0 ]; then
    echo ""
    echo "❌ Installation fehlgeschlagen!"
    echo ""
    read -p "Möchten Sie einen Rollback durchführen? (ja/nein): " do_rollback
    if [ "$do_rollback" == "ja" ]; then
        echo ""
        echo "Führe Rollback durch..."
        sudo bash "$ROLLBACK_SCRIPT" "$BACKUP_DIR"
        echo "✅ Rollback abgeschlossen"
    else
        echo "Rollback übersprungen. Sie können später manuell ausführen:"
        echo "  sudo bash $ROLLBACK_SCRIPT $BACKUP_DIR"
    fi
    exit 1
fi

# Schritt 3: Verifikation
echo ""
echo "Schritt 3/3: Installation verifizieren..."
sleep 5

# Prüfe Service
if systemctl is-active --quiet metabase; then
    echo "✅ Metabase Service läuft"
else
    echo "⚠️  Metabase Service läuft nicht - prüfe Logs:"
    sudo systemctl status metabase --no-pager -l || true
fi

# Prüfe Port
if netstat -tlnp 2>/dev/null | grep -q :3000; then
    echo "✅ Port 3000 ist aktiv"
else
    echo "⚠️  Port 3000 ist nicht aktiv"
fi

# Prüfe Metabase-Verzeichnis
if [ -d "/opt/metabase" ]; then
    echo "✅ Metabase-Verzeichnis vorhanden"
    ls -lh /opt/metabase/metabase.jar 2>/dev/null && echo "✅ Metabase JAR vorhanden" || echo "⚠️  Metabase JAR nicht gefunden"
else
    echo "⚠️  Metabase-Verzeichnis nicht gefunden"
fi

echo ""
echo "=========================================="
echo "Installation abgeschlossen"
echo "=========================================="
echo ""
echo "Nächste Schritte:"
echo "1. Öffne http://10.80.80.20:3000 im Browser"
echo "2. Erstelle Admin-Account"
echo "3. Verbinde PostgreSQL-Datenbank"
echo ""
echo "Bei Problemen - Rollback durchführen:"
echo "  sudo bash $ROLLBACK_SCRIPT $BACKUP_DIR"
echo ""
echo "Service-Status:"
echo "  sudo systemctl status metabase"
echo "  sudo journalctl -u metabase -f"
