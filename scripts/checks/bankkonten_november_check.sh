#!/bin/bash
# ============================================================================
# BANKKONTEN STATUS - NOVEMBER IMPORT CHECK
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  🏦 BANKKONTEN - NOVEMBER IMPORT STATUS                               ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

DB="/opt/greiner-portal/data/greiner_controlling.db"

# 1. ALLE KONTEN MIT AKTUELLEN SALDEN
echo "═══════════════════════════════════════════════════════════════════════════"
echo "1️⃣  ALLE BANKKONTEN (Girokonto & Kreditkarten)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 35 30 25 10 12 8

SELECT 
    k.id,
    k.kontoname,
    b.name as bank,
    k.iban,
    k.kontotyp,
    COUNT(t.id) as trans,
    MAX(t.buchungsdatum) as letzte_tx,
    CAST(julianday('now') - julianday(MAX(t.buchungsdatum)) AS INTEGER) as tage_alt
FROM konten k
LEFT JOIN banken b ON k.bank_id = b.id
LEFT JOIN transaktionen t ON k.id = t.konto_id
WHERE k.aktiv = 1 AND k.kontotyp IN ('Girokonto', 'Kreditkarte')
GROUP BY k.id
ORDER BY tage_alt ASC;
SQL
echo ""
echo ""

# 2. NOVEMBER 2025 - DETAILLIERT
echo "═══════════════════════════════════════════════════════════════════════════"
echo "2️⃣  NOVEMBER 2025 IMPORT - DETAILLIERT"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 35 30 10 12 12 8

SELECT 
    k.id,
    k.kontoname,
    b.name as bank,
    COUNT(t.id) as trans_nov,
    MIN(t.buchungsdatum) as von,
    MAX(t.buchungsdatum) as bis,
    CAST(julianday('now') - julianday(MAX(t.buchungsdatum)) AS INTEGER) as tage_alt
FROM konten k
LEFT JOIN banken b ON k.bank_id = b.id
LEFT JOIN transaktionen t ON k.id = t.konto_id 
    AND strftime('%Y-%m', t.buchungsdatum) = '2025-11'
WHERE k.aktiv = 1 AND k.kontotyp IN ('Girokonto', 'Kreditkarte')
GROUP BY k.id
ORDER BY trans_nov DESC, k.id;
SQL
echo ""
echo ""

# 3. WELCHE KONTEN BRAUCHEN NOVEMBER-IMPORT?
echo "═══════════════════════════════════════════════════════════════════════════"
echo "3️⃣  STATUS-AMPEL: WELCHE KONTEN BRAUCHEN IMPORT?"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 35 30 25 8

SELECT 
    k.id,
    k.kontoname,
    b.name as bank,
    MAX(t.buchungsdatum) as letzte_tx,
    CASE 
        WHEN MAX(t.buchungsdatum) >= date('now', '-3 days') THEN '🟢 Aktuell'
        WHEN MAX(t.buchungsdatum) >= date('now', '-7 days') THEN '🟡 Veraltet'
        ELSE '🔴 DRINGEND!'
    END as status
FROM konten k
LEFT JOIN banken b ON k.bank_id = b.id
LEFT JOIN transaktionen t ON k.id = t.konto_id
WHERE k.aktiv = 1 AND k.kontotyp IN ('Girokonto', 'Kreditkarte')
GROUP BY k.id
ORDER BY MAX(t.buchungsdatum) DESC;
SQL
echo ""
echo ""

# 4. PARSER-ZUORDNUNG
echo "═══════════════════════════════════════════════════════════════════════════"
echo "4️⃣  PARSER-ZUORDNUNG FÜR JEDES KONTO"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
.mode column
.headers on
.width 3 35 25 25

SELECT 
    k.id,
    k.kontoname,
    SUBSTR(k.iban, 1, 18) || '...' as iban_prefix,
    CASE 
        WHEN k.iban LIKE 'DE63741500%' THEN 'SparkasseParser'
        WHEN k.iban LIKE 'DE27741900%' OR k.iban LIKE 'DE64741900%' OR k.iban LIKE 'DE68741900%' THEN 'VRBankParser (Genobank)'
        WHEN k.iban LIKE 'DE22741200%' THEN 'HVB_Parser'
        WHEN k.iban LIKE 'DE76741910%' THEN 'VRBankParser (VR Landau)'
        ELSE '❓ Unbekannt / Check nötig'
    END as parser
FROM konten k
WHERE k.aktiv = 1 AND k.kontotyp IN ('Girokonto', 'Kreditkarte')
ORDER BY k.id;
SQL
echo ""
echo ""

# 5. VERFÜGBARE PDFs
echo "═══════════════════════════════════════════════════════════════════════════"
echo "5️⃣  VERFÜGBARE PDFs FÜR NOVEMBER 2025"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "--- Sparkasse Deggendorf ---"
find /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Sparkasse/ -name "*2025-11*" -type f 2>/dev/null | wc -l
echo "PDFs gefunden"

echo ""
echo "--- Genobank (alle Konten) ---"
find /mnt/buchhaltung/Buchhaltung/Kontoauszüge/ -path "*Genobank*" -name "*2025-11*" -type f 2>/dev/null | wc -l
echo "PDFs gefunden"

echo ""
echo "--- HypoVereinsbank ---"
find /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Hypovereinsbank/ -name "*2025-11*" -type f 2>/dev/null | wc -l
echo "PDFs gefunden"

echo ""
echo "--- VR Bank Landau ---"
find /mnt/buchhaltung/Buchhaltung/Kontoauszüge/ -path "*VR*Landau*" -name "*2025-11*" -type f 2>/dev/null | wc -l
echo "PDFs gefunden"

echo ""
echo ""

# 6. LETZTE IMPORT-LOGS
echo "═══════════════════════════════════════════════════════════════════════════"
echo "6️⃣  LETZTE IMPORT-AKTIVITÄT"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "--- November Import Log (letzte 10 Zeilen) ---"
if [ -f "/opt/greiner-portal/logs/imports/november_import_v2.log" ]; then
    tail -10 /opt/greiner-portal/logs/imports/november_import_v2.log
else
    echo "❌ Kein Log gefunden"
fi

echo ""
echo ""

# 7. ZUSAMMENFASSUNG
echo "═══════════════════════════════════════════════════════════════════════════"
echo "7️⃣  ZUSAMMENFASSUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sqlite3 "$DB" << 'SQL'
SELECT 
    'Konten aktiv (Giro/KK):' as Metrik,
    COUNT(*) as Wert
FROM konten WHERE aktiv = 1 AND kontotyp IN ('Girokonto', 'Kreditkarte')

UNION ALL

SELECT 
    'Transaktionen gesamt:',
    COUNT(*)
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
WHERE k.aktiv = 1 AND k.kontotyp IN ('Girokonto', 'Kreditkarte')

UNION ALL

SELECT 
    'Transaktionen November:',
    COUNT(*)
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
WHERE k.aktiv = 1 
  AND k.kontotyp IN ('Girokonto', 'Kreditkarte')
  AND strftime('%Y-%m', t.buchungsdatum) = '2025-11'

UNION ALL

SELECT 
    'Konten mit November-Daten:',
    COUNT(DISTINCT t.konto_id)
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
WHERE k.aktiv = 1 
  AND k.kontotyp IN ('Girokonto', 'Kreditkarte')
  AND strftime('%Y-%m', t.buchungsdatum) = '2025-11';
SQL

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ BANKKONTEN STATUS CHECK ABGESCHLOSSEN"
echo "═══════════════════════════════════════════════════════════════════════════"
