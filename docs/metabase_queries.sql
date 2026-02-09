-- Metabase SQL-Queries für DRIVE Portal
-- Diese Queries können direkt in Metabase verwendet werden

-- ============================================================================
-- TEK QUERIES
-- ============================================================================

-- TEK Gesamt - Monat kumuliert nach Bereichen
SELECT 
    b.name as "Bereich",
    COALESCE(SUM(cd.erloes), 0) as "Erlös (€)",
    COALESCE(SUM(cd.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(cd.db1), 0) as "DB1 (€)",
    CASE 
        WHEN SUM(cd.erloes) > 0 
        THEN ROUND(SUM(cd.db1) / SUM(cd.erloes) * 100, 2)
        ELSE 0 
    END as "DB1 (%)",
    COALESCE(SUM(cd.stueck), 0) as "Menge (Stück)"
FROM (
    SELECT 
        bereich_id,
        standort_id,
        jahr,
        monat,
        SUM(erloes) as erloes,
        SUM(einsatz) as einsatz,
        SUM(db1) as db1,
        SUM(stueck) as stueck
    FROM controlling_data
    WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
      AND monat <= EXTRACT(MONTH FROM CURRENT_DATE)
    GROUP BY bereich_id, standort_id, jahr, monat
) cd
JOIN bereiche b ON cd.bereich_id = b.id
GROUP BY b.name, b.sort_order
ORDER BY b.sort_order;

-- TEK nach Standort und Bereich (aktueller Monat)
SELECT 
    s.name as "Standort",
    b.name as "Bereich",
    COALESCE(SUM(cd.erloes), 0) as "Erlös (€)",
    COALESCE(SUM(cd.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(cd.db1), 0) as "DB1 (€)",
    CASE 
        WHEN SUM(cd.erloes) > 0 
        THEN ROUND(SUM(cd.db1) / SUM(cd.erloes) * 100, 2)
        ELSE 0 
    END as "DB1 (%)",
    COALESCE(SUM(cd.stueck), 0) as "Menge (Stück)"
FROM (
    SELECT 
        bereich_id,
        standort_id,
        jahr,
        monat,
        SUM(erloes) as erloes,
        SUM(einsatz) as einsatz,
        SUM(db1) as db1,
        SUM(stueck) as stueck
    FROM controlling_data
    WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
      AND monat = EXTRACT(MONTH FROM CURRENT_DATE)
    GROUP BY bereich_id, standort_id, jahr, monat
) cd
JOIN standorte s ON cd.standort_id = s.id
JOIN bereiche b ON cd.bereich_id = b.id
GROUP BY s.name, b.name, s.sort_order, b.sort_order
ORDER BY s.sort_order, b.sort_order;

-- TEK Verlauf (letzte 12 Monate)
SELECT 
    TO_CHAR(TO_DATE(jahr || '-' || LPAD(monat::text, 2, '0') || '-01'), 'YYYY-MM') as "Monat",
    COALESCE(SUM(erloes), 0) as "Erlös (€)",
    COALESCE(SUM(einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(db1), 0) as "DB1 (€)",
    CASE 
        WHEN SUM(erloes) > 0 
        THEN ROUND(SUM(db1) / SUM(erloes) * 100, 2)
        ELSE 0 
    END as "DB1 (%)"
FROM controlling_data
WHERE jahr >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
  AND (jahr < EXTRACT(YEAR FROM CURRENT_DATE) 
       OR (jahr = EXTRACT(YEAR FROM CURRENT_DATE) 
           AND monat <= EXTRACT(MONTH FROM CURRENT_DATE)))
GROUP BY jahr, monat
ORDER BY jahr, monat;

-- TEK Drill-Down: NW/GW nach Absatzweg
SELECT 
    b.name as "Bereich",
    aw.name as "Absatzweg",
    COALESCE(SUM(cd.erloes), 0) as "Erlös (€)",
    COALESCE(SUM(cd.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(cd.db1), 0) as "DB1 (€)",
    COALESCE(SUM(cd.stueck), 0) as "Menge (Stück)",
    CASE 
        WHEN SUM(cd.stueck) > 0 
        THEN ROUND(SUM(cd.db1) / SUM(cd.stueck), 2)
        ELSE 0 
    END as "DB/Stück (€)"
FROM (
    SELECT 
        bereich_id,
        absatzweg_id,
        jahr,
        monat,
        SUM(erloes) as erloes,
        SUM(einsatz) as einsatz,
        SUM(db1) as db1,
        SUM(stueck) as stueck
    FROM controlling_data
    WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
      AND monat = EXTRACT(MONTH FROM CURRENT_DATE)
      AND bereich_id IN (1, 2)  -- Nur NW und GW
    GROUP BY bereich_id, absatzweg_id, jahr, monat
) cd
JOIN bereiche b ON cd.bereich_id = b.id
LEFT JOIN absatzwege aw ON cd.absatzweg_id = aw.id
GROUP BY b.name, aw.name, b.sort_order, aw.sort_order
ORDER BY b.sort_order, aw.sort_order;

-- ============================================================================
-- BWA QUERIES
-- ============================================================================

-- BWA Monatswerte (aktueller Monat)
SELECT 
    position as "Position",
    betrag as "Betrag (€)",
    jahr as "Jahr",
    monat as "Monat"
FROM bwa_monatswerte
WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
  AND monat = EXTRACT(MONTH FROM CURRENT_DATE)
ORDER BY 
    CASE position
        WHEN 'umsatz' THEN 1
        WHEN 'einsatz' THEN 2
        WHEN 'db1' THEN 3
        WHEN 'variable' THEN 4
        WHEN 'db2' THEN 5
        WHEN 'direkte' THEN 6
        WHEN 'db3' THEN 7
        WHEN 'indirekte' THEN 8
        WHEN 'betriebsergebnis' THEN 9
        WHEN 'neutral' THEN 10
        WHEN 'unternehmensergebnis' THEN 11
        ELSE 99
    END;

-- BWA Verlauf (letzte 12 Monate)
SELECT 
    TO_CHAR(TO_DATE(jahr || '-' || LPAD(monat::text, 2, '0') || '-01'), 'YYYY-MM') as "Monat",
    MAX(CASE WHEN position = 'umsatz' THEN betrag END) as "Umsatz (€)",
    MAX(CASE WHEN position = 'einsatz' THEN betrag END) as "Einsatz (€)",
    MAX(CASE WHEN position = 'db1' THEN betrag END) as "DB1 (€)",
    MAX(CASE WHEN position = 'db2' THEN betrag END) as "DB2 (€)",
    MAX(CASE WHEN position = 'db3' THEN betrag END) as "DB3 (€)",
    MAX(CASE WHEN position = 'betriebsergebnis' THEN betrag END) as "Betriebsergebnis (€)",
    MAX(CASE WHEN position = 'unternehmensergebnis' THEN betrag END) as "Unternehmensergebnis (€)"
FROM bwa_monatswerte
WHERE jahr >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
  AND (jahr < EXTRACT(YEAR FROM CURRENT_DATE) 
       OR (jahr = EXTRACT(YEAR FROM CURRENT_DATE) 
           AND monat <= EXTRACT(MONTH FROM CURRENT_DATE)))
GROUP BY jahr, monat
ORDER BY jahr, monat;

-- BWA Drill-Down: Umsatz nach Konten (aktueller Monat)
SELECT 
    nominal_account_number as "Konto",
    COALESCE(na.account_name, 'Unbekannt') as "Kontobezeichnung",
    SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as "Umsatz (€)"
FROM loco_journal_accountings lja
LEFT JOIN loco_nominal_accounts na ON lja.nominal_account_number = na.account_number
WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
  AND nominal_account_number BETWEEN 800000 AND 899999
  AND NOT (firma = '0' AND journal_entry_number LIKE 'GV%')  -- G&V-Abschluss ausschließen
GROUP BY nominal_account_number, na.account_name
HAVING SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END) != 0
ORDER BY "Umsatz (€)" DESC
LIMIT 50;

-- BWA Drill-Down: Variable Kosten nach Konten
SELECT 
    nominal_account_number as "Konto",
    COALESCE(na.account_name, 'Unbekannt') as "Kontobezeichnung",
    SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as "Kosten (€)"
FROM loco_journal_accountings lja
LEFT JOIN loco_nominal_accounts na ON lja.nominal_account_number = na.account_number
WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
  AND (
    (nominal_account_number BETWEEN 415100 AND 415199)
    OR (nominal_account_number BETWEEN 435500 AND 435599)
    OR (nominal_account_number BETWEEN 455000 AND 456999 AND cost_center != 0)
    OR (nominal_account_number BETWEEN 487000 AND 487099 AND cost_center != 0)
    OR (nominal_account_number BETWEEN 491000 AND 497899)
    OR (nominal_account_number BETWEEN 891000 AND 891099)
  )
  AND NOT (firma = '0' AND journal_entry_number LIKE 'GV%')
GROUP BY nominal_account_number, na.account_name
HAVING SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) != 0
ORDER BY "Kosten (€)" DESC
LIMIT 50;

-- BWA Vergleich: Aktuell vs. Vorjahr
SELECT 
    position as "Position",
    MAX(CASE WHEN jahr = EXTRACT(YEAR FROM CURRENT_DATE) 
             AND monat = EXTRACT(MONTH FROM CURRENT_DATE) 
        THEN betrag END) as "Aktuell (€)",
    MAX(CASE WHEN jahr = EXTRACT(YEAR FROM CURRENT_DATE) - 1 
             AND monat = EXTRACT(MONTH FROM CURRENT_DATE) 
        THEN betrag END) as "Vorjahr (€)",
    MAX(CASE WHEN jahr = EXTRACT(YEAR FROM CURRENT_DATE) 
             AND monat = EXTRACT(MONTH FROM CURRENT_DATE) 
        THEN betrag END) - 
    MAX(CASE WHEN jahr = EXTRACT(YEAR FROM CURRENT_DATE) - 1 
             AND monat = EXTRACT(MONTH FROM CURRENT_DATE) 
        THEN betrag END) as "Differenz (€)",
    CASE 
        WHEN MAX(CASE WHEN jahr = EXTRACT(YEAR FROM CURRENT_DATE) - 1 
                      AND monat = EXTRACT(MONTH FROM CURRENT_DATE) 
                 THEN betrag END) != 0
        THEN ROUND(
            (MAX(CASE WHEN jahr = EXTRACT(YEAR FROM CURRENT_DATE) 
                      AND monat = EXTRACT(MONTH FROM CURRENT_DATE) 
                 THEN betrag END) - 
             MAX(CASE WHEN jahr = EXTRACT(YEAR FROM CURRENT_DATE) - 1 
                      AND monat = EXTRACT(MONTH FROM CURRENT_DATE) 
                 THEN betrag END)) / 
            ABS(MAX(CASE WHEN jahr = EXTRACT(YEAR FROM CURRENT_DATE) - 1 
                        AND monat = EXTRACT(MONTH FROM CURRENT_DATE) 
                   THEN betrag END)) * 100, 
            1
        )
        ELSE NULL
    END as "Änderung (%)"
FROM bwa_monatswerte
WHERE (jahr = EXTRACT(YEAR FROM CURRENT_DATE) 
       OR jahr = EXTRACT(YEAR FROM CURRENT_DATE) - 1)
  AND monat = EXTRACT(MONTH FROM CURRENT_DATE)
GROUP BY position
ORDER BY 
    CASE position
        WHEN 'umsatz' THEN 1
        WHEN 'einsatz' THEN 2
        WHEN 'db1' THEN 3
        WHEN 'variable' THEN 4
        WHEN 'db2' THEN 5
        WHEN 'direkte' THEN 6
        WHEN 'db3' THEN 7
        WHEN 'indirekte' THEN 8
        WHEN 'betriebsergebnis' THEN 9
        WHEN 'neutral' THEN 10
        WHEN 'unternehmensergebnis' THEN 11
        ELSE 99
    END;
