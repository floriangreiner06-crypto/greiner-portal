#!/bin/bash
# ============================================================================
# EINKAUFSFINANZIERUNG CHECK
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  🔍 EINKAUFSFINANZIERUNG - DATEN-CHECK                                ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

DB="/opt/greiner-portal/data/greiner_controlling.db"

# 1. KONTEN-SCHEMA
echo "═══════════════════════════════════════════════════════════════════════════"
echo "1️⃣  KONTEN-TABELLE SCHEMA"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" ".schema konten"
echo ""
echo ""

# 2. ALLE KONTEN (KORRIGIERT)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "2️⃣  ALLE KONTEN (ohne 'bank' Feld)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 35 30 15 6 12 6 12 8

SELECT 
    k.id,
    k.kontoname,
    k.iban,
    k.kontotyp,
    k.aktiv,
    PRINTF('%.2f', COALESCE(k.aktueller_saldo, 0)) as saldo,
    COUNT(t.id) as trans,
    MAX(t.buchungsdatum) as letzte_tx,
    CAST(julianday('now') - julianday(MAX(t.buchungsdatum)) AS INTEGER) as tage_alt
FROM konten k
LEFT JOIN transaktionen t ON k.id = t.konto_id
GROUP BY k.id
ORDER BY k.kontotyp, k.id;
SQL
echo ""
echo ""

# 3. WELCHE KONTOTYPEN GIBT ES?
echo "═══════════════════════════════════════════════════════════════════════════"
echo "3️⃣  WELCHE KONTOTYPEN EXISTIEREN?"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
SELECT 
    kontotyp,
    COUNT(*) as anzahl,
    SUM(CASE WHEN aktiv = 1 THEN 1 ELSE 0 END) as aktiv
FROM konten
GROUP BY kontotyp
ORDER BY anzahl DESC;
SQL
echo ""
echo ""

# 4. GIBT ES TABELLEN FÜR EINKAUFSFINANZIERUNG?
echo "═══════════════════════════════════════════════════════════════════════════"
echo "4️⃣  TABELLEN FÜR EINKAUFSFINANZIERUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.tables
SQL
echo ""
echo "Suche nach Einkaufsfinanzierung-Tabellen:"
sqlite3 "$DB" ".tables" | grep -i "finanz\|fahrzeug\|santander\|stellantis\|hyundai" || echo "❌ Keine gefunden"
echo ""
echo ""

# 5. FAHRZEUGFINANZIERUNGEN TABELLE
echo "═══════════════════════════════════════════════════════════════════════════"
echo "5️⃣  FAHRZEUGFINANZIERUNGEN TABELLE"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
SELECT COUNT(*) as anzahl_finanzierungen FROM fahrzeugfinanzierungen;
SQL
echo ""

sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 5 15 15 20 12 12 8

SELECT 
    id,
    finanzierungsart,
    finanzinstitut,
    fahrzeug_id,
    PRINTF('%.2f', betrag) as betrag,
    status,
    CAST(julianday('now') - julianday(startdatum) AS INTEGER) as tage_alt
FROM fahrzeugfinanzierungen
LIMIT 20;
SQL
echo ""
echo ""

# 6. FINANZINSTITUTE IN DER DB
echo "═══════════════════════════════════════════════════════════════════════════"
echo "6️⃣  WELCHE FINANZINSTITUTE?"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
SELECT 
    finanzinstitut,
    COUNT(*) as anzahl,
    COUNT(DISTINCT fahrzeug_id) as fahrzeuge
FROM fahrzeugfinanzierungen
GROUP BY finanzinstitut
ORDER BY anzahl DESC;
SQL
echo ""
echo ""

# 7. IMPORT-SCRIPTS FINDEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "7️⃣  IMPORT-SCRIPTS FÜR EINKAUFSFINANZIERUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Suche Scripts für Stellantis, Santander, Hyundai..."
echo ""
find /opt/greiner-portal -name "*stellantis*" -type f 2>/dev/null | head -10
find /opt/greiner-portal -name "*santander*" -type f 2>/dev/null | head -10
find /opt/greiner-portal -name "*hyundai*" -type f 2>/dev/null | grep -v node_modules | head -10
echo ""
echo ""

# 8. VERZEICHNISSE FÜR IMPORTS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "8️⃣  IMPORT-VERZEICHNISSE"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Suche nach typischen Import-Verzeichnissen..."
echo ""
ls -la /mnt/buchhaltung/Buchhaltung/ 2>/dev/null | grep -i "finanz\|stellantis\|santander\|hyundai" || echo "Im /mnt/buchhaltung nicht gefunden"
echo ""
ls -la /opt/greiner-portal/data/ 2>/dev/null | grep -i "finanz\|stellantis\|santander\|hyundai" || echo "Im data/ nicht gefunden"
echo ""

echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ EINKAUFSFINANZIERUNG CHECK ABGESCHLOSSEN"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
