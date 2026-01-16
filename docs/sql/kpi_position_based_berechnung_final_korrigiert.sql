-- KPI-Berechnung nach Locosoft-Logik (Position-basiert) - FINAL KORRIGIERT
-- Datum: 2026-01-16 (TAG 194)
-- 
-- WICHTIGE ERKENNTNISSE:
-- 1. Interne Positionen (labour_type = 'I') MÜSSEN berücksichtigt werden!
-- 2. Locosoft UI zeigt "Alle Auftragspositionen" - inkl. interne Positionen
-- 3. Anteilige Verteilung bei mehreren Positionen/Mechanikern

WITH
-- 1. Stempelungen MIT order_position (direkt zugeordnet)
stempelungen_roh AS (
    SELECT DISTINCT ON (t.employee_number, t.order_number, t.order_position, t.order_position_line, t.start_time, t.end_time)
        t.employee_number,
        t.order_number,
        t.order_position,
        t.order_position_line,
        t.start_time,
        t.end_time,
        EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60 as stempel_minuten
    FROM times t
    WHERE t.type = 2
        AND t.end_time IS NOT NULL
        AND t.order_number > 31
        AND t.order_position IS NOT NULL
        AND t.order_position_line IS NOT NULL
        AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
    ORDER BY t.employee_number, t.order_number, t.order_position, t.order_position_line, t.start_time, t.end_time
),
-- 2. Berechne anteilige Stempelzeit pro Position
--    WICHTIG: Wenn gleiche Start-/Endzeit auf mehrere Positionen → verteile basierend auf AW!
stempelungen_mit_anteil AS (
    SELECT
        sr.employee_number,
        sr.order_number,
        sr.order_position,
        sr.order_position_line,
        sr.start_time,
        sr.end_time,
        sr.stempel_minuten,
        l.time_units as aw_position,
        -- Gesamt-AW aller Positionen mit gleicher Start-/Endzeit
        SUM(l.time_units) OVER (
            PARTITION BY sr.employee_number, sr.order_number, sr.start_time, sr.end_time
        ) as gesamt_aw_stempelung
    FROM stempelungen_roh sr
    JOIN labours l ON sr.order_number = l.order_number
        AND sr.order_position = l.order_position
        AND sr.order_position_line = l.order_position_line
    WHERE l.time_units > 0
        -- WICHTIG: KEIN Filter auf labour_type != 'I' - interne Positionen werden berücksichtigt!
),
-- 3. Anteiliger Stempelanteil pro Position (AGGREGIERT - wie Excel)
stempelanteil_pro_position AS (
    SELECT
        employee_number,
        order_number,
        order_position,
        order_position_line,
        -- Anteilige Verteilung: Stempelzeit × (AW_Position / Gesamt_AW_Stempelung)
        SUM(stempel_minuten * (aw_position / NULLIF(gesamt_aw_stempelung, 0))) as stempelanteil_minuten
    FROM stempelungen_mit_anteil
    GROUP BY employee_number, order_number, order_position, order_position_line
),
-- 4. Gesamt-Stempelzeit pro Position (für anteilige AW-Verteilung bei mehreren Mechanikern)
gesamt_stempelzeit_pro_position AS (
    SELECT
        order_number,
        order_position,
        order_position_line,
        SUM(stempelanteil_minuten) as gesamt_stempel_minuten
    FROM stempelanteil_pro_position
    GROUP BY order_number, order_position, order_position_line
),
-- 5. AW-Anteil pro Mechaniker/Position (anteilige Verteilung bei mehreren Mechanikern)
aw_anteil_pro_position AS (
    SELECT
        sap.employee_number,
        sap.order_number,
        sap.order_position,
        sap.order_position_line,
        l.time_units * (sap.stempelanteil_minuten / NULLIF(gst.gesamt_stempel_minuten, 0)) as aw_anteil
    FROM stempelanteil_pro_position sap
    JOIN gesamt_stempelzeit_pro_position gst 
        ON sap.order_number = gst.order_number
        AND sap.order_position = gst.order_position
        AND sap.order_position_line = gst.order_position_line
    JOIN labours l 
        ON sap.order_number = l.order_number
        AND sap.order_position = l.order_position
        AND sap.order_position_line = l.order_position_line
    WHERE l.time_units > 0
        -- WICHTIG: KEIN Filter auf labour_type != 'I' - interne Positionen werden berücksichtigt!
),
-- 6. Stempelanteil pro Mechaniker (Summe über alle Positionen)
stempelanteil_mechaniker AS (
    SELECT
        employee_number,
        SUM(stempelanteil_minuten) as stempelanteil_minuten
    FROM stempelanteil_pro_position
    GROUP BY employee_number
),
-- 7. AW-Anteil pro Mechaniker (Summe über alle Positionen)
aw_anteil_mechaniker AS (
    SELECT
        employee_number,
        SUM(aw_anteil) as aw_anteil
    FROM aw_anteil_pro_position
    GROUP BY employee_number
),
-- 8. Leistungsgrad pro Mechaniker
leistungsgrad_mechaniker AS (
    SELECT
        sam.employee_number,
        sam.stempelanteil_minuten,
        aam.aw_anteil,
        CASE
            WHEN sam.stempelanteil_minuten > 0 AND aam.aw_anteil > 0
            THEN ROUND((aam.aw_anteil * 6 / sam.stempelanteil_minuten * 100)::numeric, 1)
            ELSE NULL
        END as leistungsgrad
    FROM stempelanteil_mechaniker sam
    JOIN aw_anteil_mechaniker aam ON sam.employee_number = aam.employee_number
)
SELECT
    lm.employee_number as mechaniker_nr,
    eh.name as name,
    eh.subsidiary as betrieb,
    ROUND(lm.stempelanteil_minuten::numeric, 0) as stempelanteil_minuten,
    ROUND(lm.aw_anteil::numeric, 1) as aw_anteil,
    lm.leistungsgrad
FROM leistungsgrad_mechaniker lm
JOIN employees_history eh ON lm.employee_number = eh.employee_number 
    AND eh.is_latest_record = true
WHERE lm.employee_number = %s
ORDER BY lm.employee_number;
