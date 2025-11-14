#!/bin/bash
# ============================================================================
# BANKENSPIEGEL CHECK - PHASE 1: KONTEN-INVENTUR
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  📊 BANKENSPIEGEL - PHASE 1: KONTEN-INVENTUR                          ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

DB="/opt/greiner-portal/data/greiner_controlling.db"

# 1. ALLE KONTEN MIT STATUS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "1️⃣  ALLE KONTEN (inkl. Einkaufsfinanzierung)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 30 30 25 12 6 12 6 12 8

SELECT 
    k.id,
    k.kontoname,
    k.bank,
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

# 2. NOVEMBER 2025 IMPORT-STATUS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "2️⃣  NOVEMBER 2025 IMPORT-STATUS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 30 10 12 12

SELECT 
    k.id,
    k.kontoname,
    COUNT(t.id) as trans_nov,
    MIN(t.buchungsdatum) as von,
    MAX(t.buchungsdatum) as bis
FROM konten k
LEFT JOIN transaktionen t ON k.id = t.konto_id 
    AND strftime('%Y-%m', t.buchungsdatum) = '2025-11'
WHERE k.aktiv = 1
GROUP BY k.id
ORDER BY trans_nov DESC, k.id;
SQL

echo ""
echo ""

# 3. EINKAUFSFINANZIERUNG SEPARAT
echo "═══════════════════════════════════════════════════════════════════════════"
echo "3️⃣  EINKAUFSFINANZIERUNG-KONTEN (Santander, Stellantis, Hyundai)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 30 30 10 12 12 8

SELECT 
    k.id,
    k.kontoname,
    k.bank,
    COUNT(t.id) as trans,
    MAX(t.buchungsdatum) as letzte_tx,
    PRINTF('%.2f', COALESCE(k.aktueller_saldo, 0)) as saldo,
    CAST(julianday('now') - julianday(MAX(t.buchungsdatum)) AS INTEGER) as tage_alt
FROM konten k
LEFT JOIN transaktionen t ON k.id = t.konto_id
WHERE k.kontotyp = 'Einkaufsfinanzierung'
GROUP BY k.id
ORDER BY k.id;
SQL

echo ""
echo ""

# 4. PARSER-ZUORDNUNG
echo "═══════════════════════════════════════════════════════════════════════════"
echo "4️⃣  PARSER-ZUORDNUNG (welcher Parser für welches Konto)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

cat << 'PARSER'
IBAN-Prefix → Parser:
├─ DE20 7415 0000 → Sparkasse Deggendorf (SparkasseParser)
├─ DE06 7419 0000 → Genobank (VRBankParser)
├─ DE51 7002 0270 → HypoVereinsbank (Hypovereinsbank_Parser)
├─ DE68 5483 0002 → VR Bank Landau (VRBankParser)
├─ DE89 5001 0517 → Santander (SantanderParser)
├─ DE23 5123 xxxx → Stellantis (SantanderParser oder eigener?)
└─ DE43 7619 xxxx → Hyundai Finance (SantanderParser oder eigener?)
PARSER

echo ""

sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 30 25 8

SELECT 
    k.id,
    k.kontoname,
    SUBSTR(k.iban, 1, 14) || '...' as iban_prefix,
    CASE 
        WHEN k.iban LIKE 'DE20741500%' THEN 'SparkasseParser'
        WHEN k.iban LIKE 'DE06741900%' THEN 'VRBankParser'
        WHEN k.iban LIKE 'DE51700202%' THEN 'HVB_Parser'
        WHEN k.iban LIKE 'DE68548300%' THEN 'VRBankParser'
        WHEN k.iban LIKE 'DE89500105%' THEN 'SantanderParser'
        WHEN k.iban LIKE 'DE23%' THEN 'Santander/Eigener?'
        WHEN k.iban LIKE 'DE43%' THEN 'Santander/Eigener?'
        ELSE '❓ Unbekannt'
    END as parser
FROM konten k
WHERE k.aktiv = 1
ORDER BY k.kontotyp, k.id;
SQL

echo ""
echo ""

# 5. ZUSAMMENFASSUNG
echo "═══════════════════════════════════════════════════════════════════════════"
echo "5️⃣  ZUSAMMENFASSUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

sqlite3 "$DB" << 'SQL'
SELECT 
    'Konten gesamt:' as metric,
    COUNT(*) as wert
FROM konten
UNION ALL
SELECT 
    'Konten aktiv:',
    COUNT(*) 
FROM konten WHERE aktiv = 1
UNION ALL
SELECT 
    'Einkaufsfinanzierung:',
    COUNT(*) 
FROM konten WHERE kontotyp = 'Einkaufsfinanzierung' AND aktiv = 1
UNION ALL
SELECT 
    'Transaktionen gesamt:',
    COUNT(*) 
FROM transaktionen
UNION ALL
SELECT 
    'November 2025 Transaktionen:',
    COUNT(*) 
FROM transaktionen 
WHERE strftime('%Y-%m', buchungsdatum) = '2025-11';
SQL

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ PHASE 1 ABGESCHLOSSEN"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
