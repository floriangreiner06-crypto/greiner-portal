-- KPI-Berechnung nach Locosoft-Logik (Position-basiert) - FINAL
-- Datum: 2026-01-16 (TAG 194)
-- 
-- WICHTIG: Excel aggregiert Stempelungen pro Position!
--          Eine Zeile in Excel = eine Position (nicht eine Stempelung)
--          Stempelanteil = Summe aller Stempelungen auf Position (aggregiert)

WITH
-- 1. Stempelungen MIT order_position (direkt zugeordnet)
--    WICHTIG: Aggregiere pro Position (wie Excel)
stempelungen_mit_position AS (
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
-- 2. Stempelanteil pro Position/Mechaniker (AGGREGIERT - wie Excel)
--    WICHTIG: Excel zeigt eine Zeile pro Position, nicht pro Stempelung!
stempelanteil_pro_position AS (
    SELECT
        employee_number,
        order_number,
        order_position,
        order_position_line,
        SUM(stempel_minuten) as stempelanteil_minuten
    FROM stempelungen_mit_position
    GROUP BY employee_number, order_number, order_position, order_position_line
),
-- 3. Gesamt-Stempelzeit pro Position (für anteilige AW-Verteilung)
gesamt_stempelzeit_pro_position AS (
    SELECT
        order_number,
        order_position,
        order_position_line,
        SUM(stempelanteil_minuten) as gesamt_stempel_minuten
    FROM stempelanteil_pro_position
    GROUP BY order_number, order_position, order_position_line
),
-- 4. AW-Anteil pro Mechaniker/Position (anteilige Verteilung)
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
        AND (l.labour_type IS NULL OR l.labour_type != 'I')
),
-- 5. Stempelanteil pro Mechaniker (Summe über alle Positionen)
stempelanteil_mechaniker AS (
    SELECT
        employee_number,
        SUM(stempelanteil_minuten) as stempelanteil_minuten
    FROM stempelanteil_pro_position
    GROUP BY employee_number
),
-- 6. AW-Anteil pro Mechaniker (Summe über alle Positionen)
aw_anteil_mechaniker AS (
    SELECT
        employee_number,
        SUM(aw_anteil) as aw_anteil
    FROM aw_anteil_pro_position
    GROUP BY employee_number
),
-- 7. Leistungsgrad pro Mechaniker
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
