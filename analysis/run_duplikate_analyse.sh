#!/bin/bash
# =====================================================
# DUPLIKATE-ANALYSE - SCHNELLSTART
# =====================================================

echo "🔍 Starte Duplikate-Analyse..."
echo ""

cd /opt/greiner-portal || exit 1

# Prüfe ob DB existiert
if [ ! -f "data/greiner_controlling.db" ]; then
    echo "❌ Datenbank nicht gefunden!"
    exit 1
fi

echo "✅ Datenbank gefunden"
echo "📊 Führe 5 Analyse-Queries aus..."
echo ""

# Führe die Analyse aus
sqlite3 data/greiner_controlling.db < /tmp/duplikate_analyse.sql

echo ""
echo "✅ Analyse komplett!"
echo ""
echo "💡 Nächste Schritte:"
echo "   1. Ergebnisse prüfen"
echo "   2. Falls Duplikate gefunden: Bereinigung planen"
echo "   3. Dashboard neu testen"
echo ""
