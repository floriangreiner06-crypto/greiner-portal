-- Migration 007: Zinsen-Tracking für Santander
-- Datum: 08.11.2025
-- Fügt fehlende Datumsspalten hinzu

-- Neue Spalten für Santander-Zinsdaten
ALTER TABLE fahrzeugfinanzierungen ADD COLUMN zins_startdatum DATE;
ALTER TABLE fahrzeugfinanzierungen ADD COLUMN endfaelligkeit DATE;

-- View mit intelligenter Zinsberechnung
DROP VIEW IF EXISTS fahrzeuge_mit_zinsen;

CREATE VIEW fahrzeuge_mit_zinsen AS
SELECT
    f.*,
    -- Zinsstatus ermitteln
    CASE
        WHEN f.zins_startdatum IS NOT NULL
             AND date(f.zins_startdatum) <= date('now') THEN 'Zinsen laufen'
        WHEN f.zinsfreiheit_tage < 0 THEN 'Zinsen laufen'
        WHEN f.zinsfreiheit_tage <= 30 THEN 'Warnung (< 30 Tage)'
        WHEN f.zinsfreiheit_tage <= 60 THEN 'Achtung (< 60 Tage)'
        ELSE 'OK'
    END as zinsstatus,

    -- Tage seit Zinsstart berechnen
    CASE
        WHEN f.zins_startdatum IS NOT NULL THEN
            CAST(julianday('now') - julianday(f.zins_startdatum) AS INTEGER)
        WHEN f.zinsfreiheit_tage < 0 THEN
            ABS(f.zinsfreiheit_tage)
        ELSE 0
    END as tage_seit_zinsstart,

    -- Tage bis Endfälligkeit (nur Santander)
    CASE
        WHEN f.endfaelligkeit IS NOT NULL THEN
            CAST(julianday(f.endfaelligkeit) - julianday('now') AS INTEGER)
        ELSE NULL
    END as tage_bis_endfaelligkeit,

    -- Tilgung in Prozent
    ROUND(((f.original_betrag - f.aktueller_saldo) / NULLIF(f.original_betrag, 0) * 100), 2) as tilgung_prozent,

    -- Geschätzte monatliche Zinskosten
    CASE
        WHEN f.zinsen_letzte_periode IS NOT NULL AND f.zinsen_letzte_periode > 0 THEN
            ROUND(f.zinsen_letzte_periode, 2)
        ELSE NULL
    END as zinsen_monatlich_geschaetzt

FROM fahrzeugfinanzierungen f
WHERE
    (f.zins_startdatum IS NOT NULL AND date(f.zins_startdatum) <= date('now'))
    OR f.zinsfreiheit_tage <= 60
ORDER BY
    CASE
        WHEN f.zinsen_gesamt IS NOT NULL THEN f.zinsen_gesamt
        WHEN f.zinsfreiheit_tage < 0 THEN f.zinsfreiheit_tage
        ELSE 999999
    END ASC;

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_zins_startdatum ON fahrzeugfinanzierungen(zins_startdatum)
    WHERE zins_startdatum IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_endfaelligkeit ON fahrzeugfinanzierungen(endfaelligkeit)
    WHERE endfaelligkeit IS NOT NULL;
