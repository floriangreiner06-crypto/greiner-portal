-- ============================================
-- TAG 67: Konten-Daten Update
-- Datum: 2025-11-19
-- Zweck: Kontoinhaber, Verwendungszweck und Kategorien eintragen
-- ============================================

-- Autohaus Greiner GmbH & Co. KG - Euribor Festgeld ist auf Auszug der IBAN ersichtlich
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'Euribor Festgeld ist auf Auszug der IBAN ersichtlich',
    ist_operativ = 0,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE22741200710006407420', 'DE22 7412 0071 0006 4074 20');

-- Autohaus Greiner GmbH & Co. KG - Kontokorrent
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'Kontokorrent',
    ist_operativ = 1,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE22741200710006407420', 'DE22 7412 0071 0006 4074 20');

-- Peter Greiner Darlehen (kein IBAN)
UPDATE konten SET
    kontoinhaber = 'Peter Greiner',
    verwendungszweck = 'Darlehen (quartalsweise Tilgung)',
    ist_operativ = 0,
    anzeige_gruppe = 'info'
WHERE kontoname LIKE '%Peter%Greiner%Darlehen%';

-- Autohaus Greiner GmbH & Co. KG - kontokorrent
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'kontokorrent',
    ist_operativ = 1,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE63741500000760036467', 'DE63 7415 0000 0760 0364 67');

-- Autohaus Greiner GmbH & Co. KG - Festgeld / KK
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'Festgeld / KK',
    ist_operativ = 1,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE96741900001700057908', 'DE96 7419 0000 1700 0579 08');

-- Autohaus Greiner GmbH & Co. KG - Festgeld / KK
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'Festgeld / KK',
    ist_operativ = 1,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE06741900003700057908', 'DE06 7419 0000 3700 0579 08');

-- Autohaus Greiner GmbH & Co. KG - Kontokorrent mit Kfz Brief zu besichern
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'Kontokorrent mit Kfz Brief zu besichern; max 24 Monate für ein Fahrzeug',
    ist_operativ = 1,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE58741900004700057908', 'DE58 7419 0000 4700 0579 08');

-- Autohaus Greiner GmbH & Co. KG - Darlehen wird moantlich getilgt
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'Darlehen wird moantlich getilgt',
    ist_operativ = 0,
    anzeige_gruppe = 'info'
WHERE iban IN ('DE94741900000020057908', 'DE94 7419 0000 0020 0579 08');

-- Greiner Immob.verw.GmbH & Co.KG - Girokonto / Sonderkonto Peter Greiner
UPDATE konten SET
    kontoinhaber = 'Greiner Immob.verw.GmbH & Co.KG',
    verwendungszweck = 'Girokonto / Sonderkonto Peter Greiner',
    ist_operativ = 0,
    anzeige_gruppe = 'gesellschafter'
WHERE iban IN ('DE64741900000000022225', 'DE64 7419 0000 0000 0222 25');

-- Autohaus Greiner GmbH & Co. KG - KFW Darlehen; Tilgung quartalsweise
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'KFW Darlehen; Tilgung quartalsweise',
    ist_operativ = 0,
    anzeige_gruppe = 'info'
WHERE iban IN ('DE41741900000120057908', 'DE41 7419 0000 0120 0579 08');

-- Auto Greiner GmbH & Co. KG - Kontokorrent
UPDATE konten SET
    kontoinhaber = 'Auto Greiner GmbH & Co. KG ',
    verwendungszweck = 'Kontokorrent',
    ist_operativ = 1,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE68741900000001501500', 'DE68 7419 0000 0001 5015 00');

-- Autohaus Greiner GmbH & Co. KG - Kontokorrent
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'Kontokorrent',
    ist_operativ = 1,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE27741900000000057908', 'DE27 7419 0000 0000 0579 08');

-- Autohaus Greiner GmbH & Co. KG - Kontokorrent
UPDATE konten SET
    kontoinhaber = 'Autohaus Greiner GmbH & Co. KG',
    verwendungszweck = 'Kontokorrent',
    ist_operativ = 1,
    anzeige_gruppe = 'autohaus'
WHERE iban IN ('DE76741910000000303585', 'DE76 7419 1000 0000 3035 85');

-- ============================================
-- Validierung:
-- ============================================

-- Anzahl Konten pro Gruppe:
SELECT anzeige_gruppe, COUNT(*) as anzahl
FROM konten
WHERE aktiv = 1
GROUP BY anzeige_gruppe;

-- Operative vs. Nicht-operative:
SELECT 
    CASE ist_operativ WHEN 1 THEN 'Operativ' ELSE 'Nicht-operativ' END as typ,
    COUNT(*) as anzahl
FROM konten
WHERE aktiv = 1
GROUP BY ist_operativ;

-- Detail-Übersicht:
SELECT 
    kontoname,
    kontoinhaber,
    verwendungszweck,
    CASE ist_operativ WHEN 1 THEN 'JA' ELSE 'NEIN' END as operativ,
    anzeige_gruppe,
    ROUND(saldo, 2) as saldo
FROM v_aktuelle_kontostaende
ORDER BY anzeige_gruppe, ist_operativ DESC, kontoname;

-- ============================================
-- Fertig! Nächster Schritt: API erweitern
-- ============================================
