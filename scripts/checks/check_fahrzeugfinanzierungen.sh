#!/bin/bash
# ============================================================================
# FAHRZEUGFINANZIERUNGEN - DETAILLIERTER CHECK
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  🚗 FAHRZEUGFINANZIERUNGEN - DETAILLIERTER STATUS                     ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

DB="/opt/greiner-portal/data/greiner_controlling.db"

# 1. FAHRZEUGFINANZIERUNGEN SCHEMA
echo "═══════════════════════════════════════════════════════════════════════════"
echo "1️⃣  FAHRZEUGFINANZIERUNGEN TABELLE - STRUKTUR"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" "PRAGMA table_info(fahrzeugfinanzierungen);"
echo ""
echo ""

# 2. GESAMTÜBERSICHT
echo "═══════════════════════════════════════════════════════════════════════════"
echo "2️⃣  GESAMTÜBERSICHT (wie im Screenshot)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on

-- Versuche verschiedene mögliche Spaltennamen
SELECT 
    'Fahrzeuge gesamt' as Metrik,
    COUNT(*) as Wert
FROM fahrzeugfinanzierungen

UNION ALL

SELECT 
    'Aktueller Saldo (gesamt)',
    PRINTF('%.2f €', SUM(CASE 
        WHEN typeof(aktueller_saldo) = 'real' OR typeof(aktueller_saldo) = 'integer' 
        THEN aktueller_saldo 
        ELSE 0 
    END))
FROM fahrzeugfinanzierungen

UNION ALL

SELECT 
    'Original Finanzierung',
    PRINTF('%.2f €', SUM(CASE 
        WHEN typeof(original_betrag) = 'real' OR typeof(original_betrag) = 'integer'
        THEN original_betrag 
        WHEN typeof(finanzierungssumme) = 'real' OR typeof(finanzierungssumme) = 'integer'
        THEN finanzierungssumme
        ELSE 0 
    END))
FROM fahrzeugfinanzierungen;
SQL
echo ""
echo ""

# 3. NACH FINANZINSTITUT
echo "═══════════════════════════════════════════════════════════════════════════"
echo "3️⃣  GRUPPIERUNG NACH FINANZINSTITUT"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 20 10 15 15 15 8

SELECT 
    COALESCE(finanzinstitut, institut, bank, 'Unbekannt') as Institut,
    COUNT(*) as Fahrzeuge,
    PRINTF('%.2f', SUM(CASE 
        WHEN typeof(aktueller_saldo) = 'real' OR typeof(aktueller_saldo) = 'integer' 
        THEN aktueller_saldo 
        ELSE 0 
    END)) as 'Aktueller Saldo',
    PRINTF('%.2f', SUM(CASE 
        WHEN typeof(original_betrag) = 'real' OR typeof(original_betrag) = 'integer'
        THEN original_betrag 
        WHEN typeof(finanzierungssumme) = 'real' OR typeof(finanzierungssumme) = 'integer'
        THEN finanzierungssumme
        ELSE 0 
    END)) as 'Original',
    PRINTF('%.1f%%', 
        100.0 * SUM(CASE 
            WHEN typeof(original_betrag) = 'real' OR typeof(original_betrag) = 'integer'
            THEN original_betrag - aktueller_saldo
            WHEN typeof(finanzierungssumme) = 'real' OR typeof(finanzierungssumme) = 'integer'
            THEN finanzierungssumme - aktueller_saldo
            ELSE 0 
        END) / NULLIF(SUM(CASE 
            WHEN typeof(original_betrag) = 'real' OR typeof(original_betrag) = 'integer'
            THEN original_betrag 
            WHEN typeof(finanzierungssumme) = 'real' OR typeof(finanzierungssumme) = 'integer'
            THEN finanzierungssumme
            ELSE 0 
        END), 0)
    ) as 'Abbezahlt'
FROM fahrzeugfinanzierungen
GROUP BY COALESCE(finanzinstitut, institut, bank)
ORDER BY COUNT(*) DESC;
SQL
echo ""
echo ""

# 4. NEUESTE FAHRZEUGE (Top 10)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "4️⃣  NEUESTE FAHRZEUGE (Top 10)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 8 20 18 30 12 10 12

SELECT 
    id,
    COALESCE(finanzinstitut, institut, bank) as Institut,
    COALESCE(vin, fahrgestellnummer) as VIN,
    COALESCE(modell, fahrzeugmodell) as Modell,
    COALESCE(vertragsbeginn, startdatum) as Vertrag,
    CAST(julianday('now') - julianday(COALESCE(vertragsbeginn, startdatum)) AS INTEGER) as Tage,
    PRINTF('%.2f', COALESCE(aktueller_saldo, restwert, 0)) as Saldo
FROM fahrzeugfinanzierungen
ORDER BY COALESCE(vertragsbeginn, startdatum) DESC
LIMIT 10;
SQL
echo ""
echo ""

# 5. LETZTE UPDATES
echo "═══════════════════════════════════════════════════════════════════════════"
echo "5️⃣  LETZTE UPDATES PRO INSTITUT"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 20 12 20

SELECT 
    COALESCE(finanzinstitut, institut, bank) as Institut,
    MAX(COALESCE(aktualisiert_am, erstellt_am)) as 'Letztes Update',
    COUNT(*) as Anzahl
FROM fahrzeugfinanzierungen
GROUP BY COALESCE(finanzinstitut, institut, bank)
ORDER BY MAX(COALESCE(aktualisiert_am, erstellt_am)) DESC;
SQL
echo ""
echo ""

# 6. API-ENDPOINT TEST
echo "═══════════════════════════════════════════════════════════════════════════"
echo "6️⃣  API-ENDPOINT TEST"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Teste API-Endpoints..."
echo ""
echo "--- /api/bankenspiegel/fahrzeuge-mit-zinsen ---"
curl -s "http://localhost:5000/api/bankenspiegel/fahrzeuge-mit-zinsen" | python3 -m json.tool 2>/dev/null | head -50 || echo "❌ Endpoint nicht erreichbar"
echo ""
echo ""

# 7. ROUTE CHECK
echo "═══════════════════════════════════════════════════════════════════════════"
echo "7️⃣  FRONTEND-ROUTE CHECK"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Suche Route in Routes-Dateien..."
grep -n "fahrzeugfinanzierung" /opt/greiner-portal/routes/*.py 2>/dev/null || echo "Nicht in routes/ gefunden"
echo ""
echo "Suche Route in app.py..."
grep -n "fahrzeugfinanzierung" /opt/greiner-portal/app.py 2>/dev/null || echo "Nicht in app.py gefunden"
echo ""
echo ""

# 8. TEMPLATE CHECK
echo "═══════════════════════════════════════════════════════════════════════════"
echo "8️⃣  TEMPLATE CHECK"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
ls -lh /opt/greiner-portal/templates/*fahrzeug* 2>/dev/null || echo "Keine Fahrzeug-Templates"
echo ""

echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ FAHRZEUGFINANZIERUNGEN CHECK ABGESCHLOSSEN"
echo "═══════════════════════════════════════════════════════════════════════════"
