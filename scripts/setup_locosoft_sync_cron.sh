#!/bin/bash
# ============================================================================
# LOCOSOFT SYNC CRON SETUP - TAG 103
# ============================================================================
# Richtet automatischen Sync ein (täglich um 6:00 Uhr)
#
# Ausführung: sudo bash setup_locosoft_sync_cron.sh
# ============================================================================

SCRIPT_PATH="/opt/greiner-portal/scripts/sync_locosoft_employees.py"
VENV_PYTHON="/opt/greiner-portal/venv/bin/python3"
LOG_PATH="/opt/greiner-portal/logs"

echo "🔧 Locosoft Sync Cron Setup"
echo "================================"

# Log-Verzeichnis erstellen
mkdir -p $LOG_PATH
chown ag-admin:ag-admin $LOG_PATH

# Script ausführbar machen
chmod +x $SCRIPT_PATH

# Cron-Job hinzufügen (falls nicht vorhanden)
CRON_CMD="0 6 * * * $VENV_PYTHON $SCRIPT_PATH >> $LOG_PATH/locosoft_sync_cron.log 2>&1"

# Prüfe ob bereits vorhanden
if crontab -l 2>/dev/null | grep -q "sync_locosoft_employees"; then
    echo "⚠️  Cron-Job existiert bereits"
    crontab -l | grep "sync_locosoft"
else
    # Füge hinzu
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Cron-Job hinzugefügt:"
    echo "   $CRON_CMD"
fi

echo ""
echo "📋 Aktuelle Cron-Jobs:"
crontab -l | grep -E "(sync|greiner)" || echo "   (keine relevanten Jobs)"

echo ""
echo "🚀 Manueller Test:"
echo "   $VENV_PYTHON $SCRIPT_PATH"
echo ""
echo "📊 Nicht gemappte anzeigen:"
echo "   $VENV_PYTHON $SCRIPT_PATH --unmapped"
