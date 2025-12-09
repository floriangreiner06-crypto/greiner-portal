#!/bin/bash
# ============================================================================
# FAHRZEUGFINANZIERUNGEN - STATUS REPORT (KORRIGIERT)
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  🚗 FAHRZEUGFINANZIERUNGEN - KOMPLETTER STATUS                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

DB="/opt/greiner-portal/data/greiner_controlling.db"

# 1. GESAMTÜBERSICHT (wie im Screenshot)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "1️⃣  GESAMTÜBERSICHT"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on

SELECT 
    'Fahrzeuge gesamt' as Metrik,
    COUNT(*) as Wert
FROM fahrzeugfinanzierungen

UNION ALL

SELECT 
    'Aktueller Saldo (gesamt)',
    PRINTF('%.2f €', SUM(COALESCE(aktueller_saldo, 0)))
FROM fahrzeugfinanzierungen

UNION ALL

SELECT 
    'Original Finanzierung',
    PRINTF('%.2f €', SUM(COALESCE(original_betrag, 0)))
FROM fahrzeugfinanzierungen

UNION ALL

SELECT 
    'Abbezahlt (gesamt)',
    PRINTF('%.2f €', SUM(COALESCE(abbezahlt, original_betrag - aktueller_saldo, 0)))
FROM fahrzeugfinanzierungen

UNION ALL

SELECT 
    'Tilgungsquote',
    PRINTF('%.1f%%', 
        100.0 * SUM(COALESCE(original_betrag - aktueller_saldo, 0)) / 
        NULLIF(SUM(COALESCE(original_betrag, 0)), 0)
    )
FROM fahrzeugfinanzierungen;
SQL
echo ""
echo ""

# 2. NACH FINANZINSTITUT (wie im Screenshot)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "2️⃣  NACH FINANZINSTITUT (Hyundai, Santander, Stellantis)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 20 10 18 18 18 12

SELECT 
    COALESCE(finanzinstitut, 'Unbekannt') as Institut,
    COUNT(*) as Fahrzeuge,
    PRINTF('%.2f €', SUM(COALESCE(aktueller_saldo, 0))) as 'Aktueller Saldo',
    PRINTF('%.2f €', SUM(COALESCE(original_betrag, 0))) as 'Original',
    PRINTF('%.2f €', SUM(COALESCE(original_betrag - aktueller_saldo, 0))) as 'Abbezahlt',
    PRINTF('%.1f%%', 
        100.0 * SUM(COALESCE(original_betrag - aktueller_saldo, 0)) / 
        NULLIF(SUM(COALESCE(original_betrag, 0)), 0)
    ) as 'Tilgung'
FROM fahrzeugfinanzierungen
GROUP BY COALESCE(finanzinstitut, 'Unbekannt')
ORDER BY COUNT(*) DESC;
SQL
echo ""
echo ""

# 3. LETZTE UPDATES PRO INSTITUT
echo "═══════════════════════════════════════════════════════════════════════════"
echo "3️⃣  LETZTE UPDATES & IMPORT-STATUS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 20 20 10 12

SELECT 
    COALESCE(finanzinstitut, 'Unbekannt') as Institut,
    MAX(import_datum) as 'Letzter Import',
    COUNT(*) as Anzahl,
    CAST(julianday('now') - julianday(MAX(import_datum)) AS INTEGER) as 'Tage alt'
FROM fahrzeugfinanzierungen
GROUP BY COALESCE(finanzinstitut, 'Unbekannt')
ORDER BY MAX(import_datum) DESC;
SQL
echo ""
echo ""

# 4. STATUS-VERTEILUNG
echo "═══════════════════════════════════════════════════════════════════════════"
echo "4️⃣  STATUS-VERTEILUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on

SELECT 
    COALESCE(finanzierungsstatus, 'Unbekannt') as Status,
    COUNT(*) as Anzahl,
    PRINTF('%.2f €', SUM(COALESCE(aktueller_saldo, 0))) as 'Saldo gesamt'
FROM fahrzeugfinanzierungen
GROUP BY COALESCE(finanzierungsstatus, 'Unbekannt')
ORDER BY COUNT(*) DESC;
SQL
echo ""
echo ""

# 5. NEUESTE FAHRZEUGE (Top 10)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "5️⃣  NEUESTE FAHRZEUGE (Top 10)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 5 15 18 30 12 8 12

SELECT 
    id,
    finanzinstitut as Institut,
    vin as VIN,
    modell as Modell,
    vertragsbeginn as Vertrag,
    alter_tage as Tage,
    PRINTF('%.2f', aktueller_saldo) as Saldo
FROM fahrzeugfinanzierungen
WHERE finanzierungsstatus != 'Abgelöst'
ORDER BY vertragsbeginn DESC
LIMIT 10;
SQL
echo ""
echo ""

# 6. IMPORT-QUELLEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "6️⃣  IMPORT-QUELLEN (letzte Dateien)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on

SELECT 
    finanzinstitut as Institut,
    datei_quelle as 'Letzte Datei',
    MAX(import_datum) as Import,
    COUNT(*) as Einträge
FROM fahrzeugfinanzierungen
GROUP BY finanzinstitut, datei_quelle
HAVING MAX(import_datum) >= date('now', '-7 days')
ORDER BY finanzinstitut, MAX(import_datum) DESC
LIMIT 10;
SQL
echo ""
echo ""

# 7. VERZEICHNISSE & DATEIEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "7️⃣  IMPORT-VERZEICHNISSE & AKTUELLE DATEIEN"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "--- Stellantis (AddIn Stellantis) ---"
ls -lt "/mnt/buchhaltung/Buchhaltung/AddIn Stellantis/" 2>/dev/null | head -5 || echo "❌ Verzeichnis nicht gefunden"
echo ""

echo "--- Santander (suche CSV) ---"
find /mnt/buchhaltung/Buchhaltung/ -name "*santander*.csv" -o -name "*Santander*.csv" -o -name "*Bestandsliste*.csv" 2>/dev/null | head -5
echo ""

echo "--- Hyundai (SPARDEPOT HYUNDAI) ---"
ls -lt "/mnt/buchhaltung/Buchhaltung/SPARDEPOT HYUNDAI/" 2>/dev/null | head -5 || echo "❌ Verzeichnis nicht gefunden"
echo ""
echo ""

# 8. IMPORT-SCRIPTS STATUS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "8️⃣  IMPORT-SCRIPTS STATUS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "--- Stellantis Import-Script ---"
if [ -f "/opt/greiner-portal/scripts/imports/import_stellantis.py" ]; then
    echo "✅ Script existiert"
    ls -lh /opt/greiner-portal/scripts/imports/import_stellantis.py
    echo "Letzte Änderung: $(stat -c %y /opt/greiner-portal/scripts/imports/import_stellantis.py | cut -d' ' -f1)"
else
    echo "❌ Script nicht gefunden"
fi
echo ""

echo "--- Santander Import-Script ---"
if [ -f "/opt/greiner-portal/scripts/imports/import_santander_bestand.py" ]; then
    echo "✅ Script existiert"
    ls -lh /opt/greiner-portal/scripts/imports/import_santander_bestand.py
    echo "Letzte Änderung: $(stat -c %y /opt/greiner-portal/scripts/imports/import_santander_bestand.py | cut -d' ' -f1)"
else
    echo "❌ Script nicht gefunden"
fi
echo ""

echo "--- Hyundai Scraper ---"
if [ -f "/opt/greiner-portal/tools/scrapers/hyundai_finance_scraper.py" ]; then
    echo "✅ Scraper existiert"
    ls -lh /opt/greiner-portal/tools/scrapers/hyundai_finance_scraper.py
    echo "Letzte Änderung: $(stat -c %y /opt/greiner-portal/tools/scrapers/hyundai_finance_scraper.py | cut -d' ' -f1)"
else
    echo "❌ Scraper nicht gefunden"
fi
echo ""
echo ""

# 9. CRON-JOBS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "9️⃣  CRON-JOBS FÜR EINKAUFSFINANZIERUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Suche Cron-Jobs für Stellantis, Santander, Hyundai..."
crontab -l 2>/dev/null | grep -i "stellantis\|santander\|hyundai" || echo "❌ Keine Cron-Jobs gefunden"
echo ""

echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ FAHRZEUGFINANZIERUNGEN - KOMPLETTER STATUS ABGESCHLOSSEN"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 ZUSAMMENFASSUNG:"
echo ""
sqlite3 "$DB" << 'SQL'
SELECT 
    '   Fahrzeuge:          ' || COUNT(*) as Info
FROM fahrzeugfinanzierungen
UNION ALL
SELECT 
    '   Aktueller Saldo:    ' || PRINTF('%.2f €', SUM(COALESCE(aktueller_saldo, 0)))
FROM fahrzeugfinanzierungen
UNION ALL
SELECT 
    '   Institute:          ' || COUNT(DISTINCT finanzinstitut)
FROM fahrzeugfinanzierungen
UNION ALL
SELECT 
    '   Letzter Import:     ' || MAX(import_datum)
FROM fahrzeugfinanzierungen;
SQL
echo ""
