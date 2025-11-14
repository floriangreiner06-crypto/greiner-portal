#!/bin/bash
# ============================================================================
# CRON-JOBS CHECK - BANKENSPIEGEL IMPORTS
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  ⏰ CRON-JOBS CHECK - IMPORT AUTOMATISIERUNG                          ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# 1. ALLE AKTIVEN CRON-JOBS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "1️⃣  ALLE AKTIVEN CRON-JOBS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "User: $(whoami)"
echo ""
crontab -l 2>/dev/null || echo "❌ Keine Cron-Jobs für $(whoami)"
echo ""
echo ""

# 2. CRON-SERVICE STATUS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "2️⃣  CRON-SERVICE STATUS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
systemctl status cron 2>/dev/null || systemctl status crond 2>/dev/null || echo "⚠️  Cron-Service-Status nicht prüfbar"
echo ""
echo ""

# 3. CRON-LOGS (letzte 50 Zeilen)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "3️⃣  CRON-LOGS (letzte 50 Zeilen, gefiltert nach greiner)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "=== System Cron Log ==="
grep -i "greiner\|stellantis\|santander\|hyundai\|import" /var/log/syslog 2>/dev/null | tail -50 || \
    journalctl -u cron 2>/dev/null | grep -i "greiner\|import" | tail -50 || \
    echo "⚠️  Keine System-Logs gefunden"
echo ""
echo ""

# 4. IMPORT-SCRIPT LOGS (DETAILLIERT)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "4️⃣  IMPORT-SCRIPT LOGS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "=== Stellantis Log (letzte 30 Zeilen) ==="
if [ -f "/opt/greiner-portal/logs/stellantis_import.log" ]; then
    echo "Datei: $(ls -lh /opt/greiner-portal/logs/stellantis_import.log)"
    echo ""
    tail -30 /opt/greiner-portal/logs/stellantis_import.log
else
    echo "❌ Kein Log gefunden"
fi
echo ""
echo ""

echo "=== Santander Log (letzte 30 Zeilen) ==="
if [ -f "/opt/greiner-portal/logs/santander_import.log" ]; then
    echo "Datei: $(ls -lh /opt/greiner-portal/logs/santander_import.log)"
    echo ""
    tail -30 /opt/greiner-portal/logs/santander_import.log
else
    echo "❌ Kein Log gefunden"
fi
echo ""
echo ""

echo "=== Hyundai Log (letzte 30 Zeilen) ==="
if [ -f "/opt/greiner-portal/logs/hyundai_import.log" ]; then
    echo "Datei: $(ls -lh /opt/greiner-portal/logs/hyundai_import.log)"
    echo ""
    tail -30 /opt/greiner-portal/logs/hyundai_import.log
else
    echo "❌ Kein Log gefunden"
fi
echo ""
echo ""

echo "=== November Import Log (letzte 30 Zeilen) ==="
if [ -f "/opt/greiner-portal/logs/imports/november_import_v2.log" ]; then
    echo "Datei: $(ls -lh /opt/greiner-portal/logs/imports/november_import_v2.log)"
    echo ""
    tail -30 /opt/greiner-portal/logs/imports/november_import_v2.log
else
    echo "❌ Kein Log gefunden"
fi
echo ""
echo ""

# 5. PROZESS-CHECK (läuft gerade ein Import?)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "5️⃣  LAUFENDE IMPORT-PROZESSE"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
ps aux | grep -i "import.*\(stellantis\|santander\|hyundai\|november\)" | grep -v grep || echo "✅ Keine Import-Prozesse laufen gerade"
echo ""
echo ""

# 6. SCRIPT-PFADE & AUSFÜHRBARKEIT
echo "═══════════════════════════════════════════════════════════════════════════"
echo "6️⃣  IMPORT-SCRIPTS - PFADE & RECHTE"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "=== Stellantis ==="
if [ -f "/opt/greiner-portal/import_stellantis.py" ]; then
    ls -lh /opt/greiner-portal/import_stellantis.py
else
    echo "⚠️  /opt/greiner-portal/import_stellantis.py nicht gefunden"
fi
if [ -f "/opt/greiner-portal/scripts/imports/import_stellantis.py" ]; then
    ls -lh /opt/greiner-portal/scripts/imports/import_stellantis.py
else
    echo "⚠️  scripts/imports/import_stellantis.py nicht gefunden"
fi
echo ""

echo "=== Santander ==="
if [ -f "/opt/greiner-portal/scripts/imports/import_santander_bestand.py" ]; then
    ls -lh /opt/greiner-portal/scripts/imports/import_santander_bestand.py
else
    echo "❌ Script nicht gefunden"
fi
echo ""

echo "=== Hyundai ==="
if [ -f "/opt/greiner-portal/scripts/imports/import_hyundai_finance.py" ]; then
    ls -lh /opt/greiner-portal/scripts/imports/import_hyundai_finance.py
else
    echo "⚠️  import_hyundai_finance.py nicht gefunden"
fi
if [ -f "/opt/greiner-portal/tools/scrapers/hyundai_finance_scraper.py" ]; then
    ls -lh /opt/greiner-portal/tools/scrapers/hyundai_finance_scraper.py
else
    echo "❌ Scraper nicht gefunden"
fi
echo ""

echo "=== November Import ==="
ls -lh /opt/greiner-portal/scripts/imports/*november* 2>/dev/null || echo "❌ Keine November-Scripts gefunden"
echo ""
echo ""

# 7. VENV-CHECK
echo "═══════════════════════════════════════════════════════════════════════════"
echo "7️⃣  PYTHON VENV CHECK"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "VEnv-Pfad in Cron: /opt/greiner-portal/venv/bin/python3"
echo ""
if [ -f "/opt/greiner-portal/venv/bin/python3" ]; then
    echo "✅ VEnv existiert"
    /opt/greiner-portal/venv/bin/python3 --version
else
    echo "❌ VEnv nicht gefunden!"
fi
echo ""
echo ""

# 8. LETZTES ERFOLGREICHES IMPORT-DATUM
echo "═══════════════════════════════════════════════════════════════════════════"
echo "8️⃣  LETZTES ERFOLGREICHES IMPORT-DATUM (aus Logs)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "=== Stellantis ==="
grep -i "success\|erfolgreich\|abgeschlossen" /opt/greiner-portal/logs/stellantis_import.log 2>/dev/null | tail -5 || echo "Keine Erfolgs-Meldungen"
echo ""

echo "=== Santander ==="
grep -i "success\|erfolgreich\|abgeschlossen" /opt/greiner-portal/logs/santander_import.log 2>/dev/null | tail -5 || echo "Keine Erfolgs-Meldungen"
echo ""

echo "=== Hyundai ==="
grep -i "success\|erfolgreich\|abgeschlossen" /opt/greiner-portal/logs/hyundai_import.log 2>/dev/null | tail -5 || echo "Keine Erfolgs-Meldungen"
echo ""
echo ""

# 9. FEHLER IN LOGS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "9️⃣  FEHLER IN LOGS (letzte 10)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "=== Stellantis Fehler ==="
grep -i "error\|fehler\|exception\|traceback" /opt/greiner-portal/logs/stellantis_import.log 2>/dev/null | tail -10 || echo "Keine Fehler"
echo ""

echo "=== Santander Fehler ==="
grep -i "error\|fehler\|exception\|traceback" /opt/greiner-portal/logs/santander_import.log 2>/dev/null | tail -10 || echo "Keine Fehler"
echo ""

echo "=== Hyundai Fehler ==="
grep -i "error\|fehler\|exception\|traceback" /opt/greiner-portal/logs/hyundai_import.log 2>/dev/null | tail -10 || echo "Keine Fehler"
echo ""
echo ""

# 10. ZUSAMMENFASSUNG
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🔟  ZUSAMMENFASSUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

cat << 'SUMMARY'
PRÜFPUNKTE:
-----------
1. Cron-Jobs aktiv?          → Siehe Abschnitt 1
2. Cron-Service läuft?       → Siehe Abschnitt 2
3. Scripts existieren?       → Siehe Abschnitt 6
4. VEnv funktioniert?        → Siehe Abschnitt 7
5. Letzte Erfolge?           → Siehe Abschnitt 8
6. Fehler in Logs?           → Siehe Abschnitt 9
7. Laufende Prozesse?        → Siehe Abschnitt 5

MÖGLICHE PROBLEME:
------------------
❌ Cron-Pfade falsch         → Scripts in falschem Verzeichnis
❌ VEnv-Pfad falsch          → Python kann Module nicht finden
❌ Berechtigungen fehlen     → Scripts nicht ausführbar
❌ Überschneidungen          → Imports blockieren sich gegenseitig
❌ Cron-Service gestoppt     → Keine automatischen Imports
❌ Verzeichnis nicht mounted → PDFs nicht erreichbar

SUMMARY

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ CRON-CHECK ABGESCHLOSSEN"
echo "═══════════════════════════════════════════════════════════════════════════"
