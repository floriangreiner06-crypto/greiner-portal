-- View: fahrzeuge_mit_zinsen
-- PostgreSQL-Version (TAG 172)
-- Erstellt die View für Zinsanalyse im Bankenspiegel

DROP VIEW IF EXISTS fahrzeuge_mit_zinsen;

CREATE VIEW fahrzeuge_mit_zinsen AS
SELECT
    f.id,
    f.finanzinstitut,
    f.rrdi,
    f.hersteller,
    f.vin,
    f.modell,
    f.produkt_kategorie,
    f.aktueller_saldo,
    f.original_betrag,
    f.zinsen_gesamt,
    f.zinsen_letzte_periode,
    f.zinsen_berechnet,
    f.vertragsbeginn,
    f.alter_tage,
    f.zinsfreiheit_tage,
    f.zins_startdatum,
    f.endfaelligkeit,
    f.aktiv,
    
    -- Zinsstatus ermitteln
    CASE
        WHEN f.zins_startdatum IS NOT NULL 
             AND f.zins_startdatum <= CURRENT_DATE THEN 'Zinsen laufen'
        WHEN f.zinsfreiheit_tage IS NOT NULL AND f.zinsfreiheit_tage < 0 THEN 'Zinsen laufen'
        WHEN f.zinsfreiheit_tage IS NOT NULL AND f.zinsfreiheit_tage <= 30 THEN 'Warnung (< 30 Tage)'
        WHEN f.zinsfreiheit_tage IS NOT NULL AND f.zinsfreiheit_tage <= 60 THEN 'Achtung (< 60 Tage)'
        WHEN f.zinsen_gesamt > 0 THEN 'Zinsen laufen'
        ELSE 'OK'
    END as zinsstatus,
    
    -- Tage seit Zinsstart
    CASE
        WHEN f.zins_startdatum IS NOT NULL THEN
            (CURRENT_DATE - f.zins_startdatum)::INTEGER
        WHEN f.zinsfreiheit_tage < 0 THEN ABS(f.zinsfreiheit_tage)
        ELSE 0
    END as tage_seit_zinsstart,
    
    -- Tage bis Endfälligkeit
    CASE
        WHEN f.endfaelligkeit IS NOT NULL THEN
            (f.endfaelligkeit - CURRENT_DATE)::INTEGER
        ELSE NULL
    END as tage_bis_endfaelligkeit,
    
    -- Tilgung in Prozent
    ROUND(((f.original_betrag - f.aktueller_saldo) / NULLIF(f.original_betrag, 0) * 100)::NUMERIC, 2) as tilgung_prozent,
    
    -- Monatliche Zinskosten (beste verfügbare Quelle)
    COALESCE(
        NULLIF(f.zinsen_letzte_periode, 0),
        CASE 
            WHEN f.aktueller_saldo > 0 AND f.finanzinstitut = 'Santander' THEN
                ROUND((f.aktueller_saldo * 0.09 * 30 / 365)::NUMERIC, 2)
            ELSE NULL
        END
    ) as zinsen_monatlich_geschaetzt

FROM fahrzeugfinanzierungen f
WHERE f.aktiv = true
  AND (
    -- Zinsen laufen bereits
    (f.zins_startdatum IS NOT NULL AND f.zins_startdatum <= CURRENT_DATE)
    -- Oder bald zinspflichtig (< 60 Tage Zinsfreiheit übrig)
    OR (f.zinsfreiheit_tage IS NOT NULL AND f.zinsfreiheit_tage <= 60)
    -- Oder hat bereits Zinsen
    OR f.zinsen_gesamt > 0
  )
ORDER BY
    -- Erst die mit laufenden Zinsen (höchste zuerst)
    CASE WHEN f.zinsen_gesamt > 0 THEN 0 ELSE 1 END,
    f.zinsen_gesamt DESC,
    f.zinsfreiheit_tage ASC NULLS LAST;
