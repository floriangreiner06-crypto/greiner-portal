-- Query: Welche Fahrzeuge haben noch Garantie?
-- Basierend auf Erstzulassungsdatum + Garantiedauer
-- 
-- Verwendung:
--   psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -f query_fahrzeuge_mit_garantie.sql
--
-- Oder in Python:
--   from api.db_utils import locosoft_session
--   with locosoft_session() as conn:
--       cursor = conn.cursor()
--       cursor.execute(open('scripts/query_fahrzeuge_mit_garantie.sql').read())

-- Standard-Garantiedauer (kann angepasst werden)
-- Opel/Stellantis: 2 Jahre
-- Hyundai: 5 Jahre
-- Andere: 2 Jahre Standard

WITH garantie_dauer AS (
    SELECT 
        v.internal_number,
        v.dealer_vehicle_number,
        v.dealer_vehicle_type,
        v.first_registration_date as erstzulassung,
        v.vin,
        v.license_plate as kennzeichen,
        m.description as marke,
        COALESCE(
            NULLIF(TRIM(v.free_form_model_text), ''),
            NULLIF(TRIM(mo.description), ''),
            'Unbekannt'
        ) as modell,
        v.mileage_km as km_stand,
        -- Garantiedauer je nach Marke
        CASE 
            WHEN UPPER(m.description) LIKE '%HYUNDAI%' THEN 5  -- Hyundai: 5 Jahre
            WHEN UPPER(m.description) LIKE '%OPEL%' THEN 2     -- Opel: 2 Jahre
            WHEN UPPER(m.description) LIKE '%CITROEN%' THEN 2  -- Citroën: 2 Jahre
            WHEN UPPER(m.description) LIKE '%PEUGEOT%' THEN 2 -- Peugeot: 2 Jahre
            ELSE 2  -- Standard: 2 Jahre
        END as garantie_jahre,
        -- Garantie-Ablaufdatum berechnen
        CASE 
            WHEN v.first_registration_date IS NOT NULL THEN
                v.first_registration_date + INTERVAL '1 year' * 
                CASE 
                    WHEN UPPER(m.description) LIKE '%HYUNDAI%' THEN 5
                    WHEN UPPER(m.description) LIKE '%OPEL%' THEN 2
                    WHEN UPPER(m.description) LIKE '%CITROEN%' THEN 2
                    WHEN UPPER(m.description) LIKE '%PEUGEOT%' THEN 2
                    ELSE 2
                END
            ELSE NULL
        END as garantie_ablauf,
        -- Prüfe ob Garantie noch aktiv ist
        CASE 
            WHEN v.first_registration_date IS NOT NULL THEN
                CURRENT_DATE <= (
                    v.first_registration_date + INTERVAL '1 year' * 
                    CASE 
                        WHEN UPPER(m.description) LIKE '%HYUNDAI%' THEN 5
                        WHEN UPPER(m.description) LIKE '%OPEL%' THEN 2
                        WHEN UPPER(m.description) LIKE '%CITROEN%' THEN 2
                        WHEN UPPER(m.description) LIKE '%PEUGEOT%' THEN 2
                        ELSE 2
                    END
                )
            ELSE false
        END as hat_garantie,
        -- Restliche Garantie in Tagen
        CASE 
            WHEN v.first_registration_date IS NOT NULL THEN
                (v.first_registration_date + INTERVAL '1 year' * 
                 CASE 
                     WHEN UPPER(m.description) LIKE '%HYUNDAI%' THEN 5
                     WHEN UPPER(m.description) LIKE '%OPEL%' THEN 2
                     WHEN UPPER(m.description) LIKE '%CITROEN%' THEN 2
                     WHEN UPPER(m.description) LIKE '%PEUGEOT%' THEN 2
                     ELSE 2
                 END)::date - CURRENT_DATE
            ELSE NULL
        END as garantie_rest_tage,
        -- Fahrzeug-Alter in Jahren
        CASE 
            WHEN v.first_registration_date IS NOT NULL THEN
                EXTRACT(YEAR FROM AGE(CURRENT_DATE, v.first_registration_date))
            ELSE NULL
        END as fahrzeug_alter_jahre,
        -- Kunde (falls verkauft)
        cs.family_name || COALESCE(', ' || cs.first_name, '') as kunde,
        dv.out_sales_contract_date as verkauft_am
    FROM vehicles v
    LEFT JOIN makes m ON v.make_number = m.make_number
    LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
    LEFT JOIN dealer_vehicles dv 
        ON v.dealer_vehicle_number = dv.dealer_vehicle_number
        AND v.dealer_vehicle_type = dv.dealer_vehicle_type
    LEFT JOIN customers_suppliers cs ON dv.buyer_customer_no = cs.customer_number
    WHERE v.first_registration_date IS NOT NULL
)
SELECT 
    internal_number,
    dealer_vehicle_number,
    dealer_vehicle_type,
    vin,
    kennzeichen,
    marke,
    modell,
    erstzulassung,
    fahrzeug_alter_jahre,
    km_stand,
    garantie_jahre,
    garantie_ablauf,
    garantie_rest_tage,
    hat_garantie,
    kunde,
    verkauft_am,
    -- Warnung wenn Garantie bald abläuft (< 30 Tage)
    CASE 
        WHEN garantie_rest_tage IS NOT NULL AND garantie_rest_tage < 30 AND garantie_rest_tage > 0 THEN true
        ELSE false
    END as garantie_laeuft_bald_ab
FROM garantie_dauer
WHERE hat_garantie = true  -- Nur Fahrzeuge mit noch aktiver Garantie
ORDER BY 
    garantie_rest_tage ASC,  -- Zuerst die, deren Garantie bald abläuft
    marke,
    modell;

-- Alternative: Alle Fahrzeuge (auch ohne Garantie) anzeigen
-- WHERE hat_garantie = true  -- Diese Zeile entfernen für alle Fahrzeuge

-- Alternative: Nur Fahrzeuge deren Garantie bald abläuft (< 30 Tage)
-- WHERE hat_garantie = true AND garantie_rest_tage < 30 AND garantie_rest_tage > 0
