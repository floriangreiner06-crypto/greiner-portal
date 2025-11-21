-- ============================================================================
-- BANKENSPIEGEL V2 - STAMMDATEN
-- ============================================================================
-- Datum: 2025-11-19
-- Beschreibung: Banken und Konten für Greiner Portal
-- ============================================================================

BEGIN TRANSACTION;

-- ============================================================================
-- 1. BANKEN EINTRAGEN
-- ============================================================================

-- Sparkasse Deggendorf
INSERT INTO banken (id, bank_name, bank_typ, bic, blz, aktiv)
VALUES (1, 'Sparkasse Deggendorf', 'Sparkasse', 'BYLADEM1DEG', '74150000', 1);

-- Genobank (VR-Bank) - Mehrere Konten
INSERT INTO banken (id, bank_name, bank_typ, bic, blz, aktiv)
VALUES (2, 'Genobank Autohaus Greiner', 'Genossenschaftsbank', 'GENODEF1DEG', '74190000', 1);

-- Genobank Immobilien
INSERT INTO banken (id, bank_name, bank_typ, bic, blz, aktiv)
VALUES (3, 'Genobank Greiner Immobilien Verwaltung', 'Genossenschaftsbank', 'GENODEF1DEG', '74190000', 1);

-- Genobank Auto Greiner (Hyundai)
INSERT INTO banken (id, bank_name, bank_typ, bic, blz, aktiv)
VALUES (4, 'Genobank Auto Greiner', 'Genossenschaftsbank', 'GENODEF1DEG', '74190000', 1);

-- Hypovereinsbank
INSERT INTO banken (id, bank_name, bank_typ, bic, blz, aktiv)
VALUES (5, 'Hypovereinsbank', 'Sonstige', 'HYVEDEMM421', '74120071', 1);

-- VR Bank Landau
INSERT INTO banken (id, bank_name, bank_typ, bic, blz, aktiv)
VALUES (6, 'VR Bank Landau', 'Genossenschaftsbank', 'GENODEF1LA1', '74191000', 1);

-- ============================================================================
-- 2. KONTEN EINTRAGEN
-- ============================================================================

-- Konto 1: Sparkasse KK
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    1, 
    1, 
    '0760036467', 
    'DE63741500000760036467',
    'BYLADEM1DEG',
    'Sparkasse KK',
    'Kontokorrent',
    'EUR',
    1,
    'Autohaus Greiner GmbH & Co. KG',
    0
);

-- Konto 5: 57908 KK (Hauptkonto Autohaus)
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    5,
    2,
    '0000057908',
    'DE27741900000000057908',
    'GENODEF1DEG',
    '57908 KK',
    'Kontokorrent',
    'EUR',
    1,
    'Autohaus Greiner GmbH & Co. KG',
    0
);

-- Konto 6: 22225 Immo KK
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    6,
    3,
    '0000022225',
    'DE64741900000000022225',
    'GENODEF1DEG',
    '22225 Immo KK',
    'Girokonto',
    'EUR',
    1,
    'Greiner Immobilien Verwaltungs GmbH',
    0
);

-- Konto 7: 20057908 Darlehen
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    7,
    2,
    '0020057908',
    'DE94741900000020057908',
    'GENODEF1DEG',
    '20057908 Darlehen',
    'Darlehen',
    'EUR',
    1,
    'Autohaus Greiner GmbH & Co. KG',
    0
);

-- Konto 8: 1700057908 Festgeld
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    8,
    2,
    '1700057908',
    'DE96741900001700057908',
    'GENODEF1DEG',
    '1700057908 Festgeld',
    'Festgeld',
    'EUR',
    1,
    'Autohaus Greiner GmbH & Co. KG',
    0
);

-- Konto 9: Hypovereinsbank KK
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    9,
    5,
    '0006407420',
    'DE22741200710006407420',
    'HYVEDEMM421',
    'Hypovereinsbank KK',
    'Kontokorrent',
    'EUR',
    1,
    'Autohaus Greiner GmbH & Co. KG',
    0
);

-- Konto 14: 303585 VR Landau KK
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    14,
    6,
    '0000303585',
    'DE76741910000000303585',
    'GENODEF1LA1',
    '303585 VR Landau KK',
    'Kontokorrent',
    'EUR',
    1,
    'Autohaus Greiner GmbH & Co. KG',
    0
);

-- Konto 15: 1501500 HYU KK (Hyundai)
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    15,
    4,
    '0001501500',
    'DE68741900000001501500',
    'GENODEF1DEG',
    '1501500 HYU KK',
    'Kontokorrent',
    'EUR',
    1,
    'Auto Greiner GmbH & Co. KG',
    0
);

-- Konto 17: 4700057908 Darlehen (Kontokorrent KFZ - Hauptfinanzierung)
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    17,
    2,
    '4700057908',
    'DE58741900004700057908',
    'GENODEF1DEG',
    '4700057908 Darlehen',
    'Kontokorrent',
    'EUR',
    1,
    'Autohaus Greiner GmbH & Co. KG',
    1000000  -- 1 Mio € Kreditlinie
);

-- Konto 20: KfW 120057908
INSERT INTO konten (id, bank_id, kontonummer, iban, bic, kontoname, kontotyp, waehrung, aktiv, inhaber, kreditlinie)
VALUES (
    20,
    2,
    '0120057908',
    'DE41741900000120057908',
    'GENODEF1DEG',
    'KfW 120057908',
    'Darlehen',
    'EUR',
    1,
    'Autohaus Greiner GmbH & Co. KG',
    0
);

-- ============================================================================
-- 3. FINANZIERUNGSBANKEN (für Fahrzeugfinanzierungen)
-- ============================================================================

-- Santander Consumer Bank
INSERT INTO finanzierungsbanken (id, bank_name, bank_typ, import_format, aktiv)
VALUES (1, 'Santander Consumer Bank', 'Santander', 'CSV', 1);

-- Hyundai Finance
INSERT INTO finanzierungsbanken (id, bank_name, bank_typ, import_format, aktiv)
VALUES (2, 'Hyundai Capital Bank Europe', 'Hyundai', 'CSV', 1);

-- Stellantis Bank (Opel/Peugeot/Citroën/etc.)
INSERT INTO finanzierungsbanken (id, bank_name, bank_typ, import_format, aktiv)
VALUES (3, 'Stellantis Bank S.A.', 'Stellantis', 'Excel', 1);

COMMIT;

-- ============================================================================
-- 4. VERIFIKATION
-- ============================================================================

SELECT '=== BANKEN ===' as info;
SELECT id, bank_name, bank_typ, aktiv FROM banken ORDER BY id;

SELECT '=== KONTEN ===' as info;
SELECT 
    k.id,
    k.kontoname,
    k.kontonummer,
    k.iban,
    b.bank_name,
    k.kontotyp,
    k.aktiv
FROM konten k
JOIN banken b ON k.bank_id = b.id
ORDER BY k.id;

SELECT '=== FINANZIERUNGSBANKEN ===' as info;
SELECT id, bank_name, bank_typ, import_format, aktiv FROM finanzierungsbanken ORDER BY id;

-- ============================================================================
-- FERTIG!
-- ============================================================================
