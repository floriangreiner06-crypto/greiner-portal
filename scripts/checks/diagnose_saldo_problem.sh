#!/bin/bash
# ============================================================================
# SALDO-PROBLEM DIAGNOSE
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  💰 SALDO-PROBLEM DIAGNOSE                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

DB="/opt/greiner-portal/data/greiner_controlling.db"

# 1. AKTUELLER SALDO IN DB
echo "═══════════════════════════════════════════════════════════════════════════"
echo "1️⃣  AKTUELLER SALDO IN DB (Konto 1501500 HYU KK)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
SELECT 
    id,
    kontoname,
    iban,
    '❌ FEHLT!' as aktueller_saldo_spalte
FROM konten 
WHERE id = 15 OR kontoname LIKE '%1501500%';
SQL
echo ""
echo "PRÜFE: Gibt es eine Spalte für Saldo?"
sqlite3 "$DB" "PRAGMA table_info(konten);" | grep -i "saldo"
echo ""
echo ""

# 2. BERECHNETER SALDO AUS TRANSAKTIONEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "2️⃣  BERECHNETER SALDO AUS TRANSAKTIONEN"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on

SELECT 
    k.id,
    k.kontoname,
    COUNT(t.id) as transaktionen,
    PRINTF('%.2f €', SUM(t.betrag)) as summe_betrag,
    MAX(t.buchungsdatum) as letzte_tx,
    MAX(t.saldo_nach_buchung) as letzter_saldo
FROM konten k
LEFT JOIN transaktionen t ON k.id = t.konto_id
WHERE k.id = 15
GROUP BY k.id;
SQL
echo ""
echo ""

# 3. NOVEMBER TRANSAKTIONEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "3️⃣  NOVEMBER TRANSAKTIONEN (Konto 15)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
SELECT 
    'November 2025:' as Info,
    COUNT(*) as Anzahl,
    PRINTF('%.2f €', SUM(betrag)) as Summe
FROM transaktionen
WHERE konto_id = 15
  AND strftime('%Y-%m', buchungsdatum) = '2025-11';
SQL
echo ""
echo ""

# 4. LETZTE 5 TRANSAKTIONEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "4️⃣  LETZTE 5 TRANSAKTIONEN (Konto 15)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 12 12 40 12 12

SELECT 
    buchungsdatum,
    PRINTF('%.2f', betrag) as betrag,
    LEFT(verwendungszweck, 40) as zweck,
    PRINTF('%.2f', saldo_nach_buchung) as saldo_nach,
    id
FROM transaktionen
WHERE konto_id = 15
ORDER BY buchungsdatum DESC, id DESC
LIMIT 5;
SQL
echo ""
echo ""

# 5. DAILY_BALANCES TABELLE
echo "═══════════════════════════════════════════════════════════════════════════"
echo "5️⃣  DAILY_BALANCES (falls vorhanden)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
if sqlite3 "$DB" ".tables" | grep -q "daily_balances"; then
    echo "✅ Tabelle existiert"
    sqlite3 "$DB" << 'SQL'
.mode column
.headers on

SELECT 
    datum,
    PRINTF('%.2f €', saldo) as saldo
FROM daily_balances
WHERE konto_id = 15
ORDER BY datum DESC
LIMIT 10;
SQL
else
    echo "❌ Tabelle daily_balances existiert nicht"
fi
echo ""
echo ""

# 6. IMPORT-SCRIPT CHECKEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "6️⃣  IMPORT-SCRIPT: SALDO-UPDATE LOGIK"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Suche nach Saldo-Update im Import-Script..."
grep -n "saldo\|balance\|UPDATE konten" /opt/greiner-portal/scripts/imports/import_november_all_accounts_v2.py 2>/dev/null | head -20 || echo "❌ Nicht gefunden"
echo ""
echo ""

# 7. PARSER FACTORY CHECKEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "7️⃣  PARSER FACTORY: SALDO-PARSING"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Suche nach Saldo-Parsing in Parser Factory..."
grep -n "saldo\|balance\|endsaldo" /opt/greiner-portal/parsers/parser_factory.py 2>/dev/null | head -20 || echo "❌ Nicht gefunden"
echo ""
echo ""

# 8. VR BANK PARSER CHECKEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "8️⃣  VR BANK PARSER: SALDO-PARSING"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Suche nach Endsaldo-Parsing..."
grep -n "Endsaldo\|saldo_nach_buchung" /opt/greiner-portal/parsers/vrbank_parser.py 2>/dev/null | head -20 || echo "❌ Nicht gefunden"
echo ""
echo ""

# 9. ZUSAMMENFASSUNG
echo "═══════════════════════════════════════════════════════════════════════════"
echo "9️⃣  PROBLEM-ZUSAMMENFASSUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
cat << 'SUMMARY'
ERWARTETER SALDO:  +329.881 € (laut PDF)
ANGEZEIGTER SALDO: 140.122,61 € (Frontend)
DIFFERENZ:         ~190.000 € FEHLEN!

MÖGLICHE URSACHEN:
1. Saldo wird aus PDF nicht geparst
2. Saldo wird nicht in DB geschrieben
3. konten-Tabelle hat keine Saldo-Spalte
4. daily_balances wird nicht aktualisiert
5. Frontend berechnet Saldo falsch

NÄCHSTE SCHRITTE:
→ Parser-Code prüfen (parst Endsaldo?)
→ Import-Script prüfen (updated Saldo?)
→ DB-Schema prüfen (Spalte vorhanden?)
→ Frontend-Code prüfen (wo kommt Saldo her?)
SUMMARY

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ DIAGNOSE ABGESCHLOSSEN"
echo "═══════════════════════════════════════════════════════════════════════════"
