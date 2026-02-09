#!/bin/bash
# Backup-Skript für Metabase-Installation
# Erstellt Backup des aktuellen Zustands vor Installation

set -e

BACKUP_DIR="/opt/greiner-portal/backups/metabase_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=== Metabase Backup erstellen ==="
echo "Backup-Verzeichnis: $BACKUP_DIR"

# Backup systemd Services
if [ -f "/etc/systemd/system/metabase.service" ]; then
    echo "Sichere Metabase Service..."
    sudo cp /etc/systemd/system/metabase.service "$BACKUP_DIR/metabase.service.bak"
fi

# Backup Metabase-Verzeichnis (falls vorhanden)
if [ -d "/opt/metabase" ]; then
    echo "Sichere Metabase-Verzeichnis..."
    sudo tar -czf "$BACKUP_DIR/metabase_data.tar.gz" -C /opt metabase 2>/dev/null || true
fi

# Prüfe ob Metabase läuft
if systemctl is-active --quiet metabase 2>/dev/null; then
    echo "Metabase läuft - Status wird gesichert..."
    sudo systemctl status metabase > "$BACKUP_DIR/metabase_status.txt" 2>&1 || true
fi

# Prüfe Port 3000
echo "Prüfe Port 3000..."
netstat -tlnp 2>/dev/null | grep :3000 > "$BACKUP_DIR/port_3000_status.txt" || echo "Port 3000 frei" > "$BACKUP_DIR/port_3000_status.txt"

# Backup-Info speichern
cat > "$BACKUP_DIR/backup_info.txt" <<EOF
Backup erstellt: $(date)
Zweck: Metabase Installation
Backup-Verzeichnis: $BACKUP_DIR
EOF

echo ""
echo "=== Backup abgeschlossen ==="
echo "Backup-Verzeichnis: $BACKUP_DIR"
echo ""
echo "Für Rollback: sudo bash /opt/greiner-portal/scripts/metabase_rollback.sh $BACKUP_DIR"
