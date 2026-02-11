-- Seed: Versicherungskunden-Whitelist aus loco_customers_suppliers
-- Mehrfach ausführbar: ON CONFLICT (customer_number, subsidiary) DO NOTHING
-- Datum: 2026-02-11

BEGIN;

INSERT INTO unfall_versicherung_kunden (customer_number, subsidiary, versicherung_name, ist_aktiv)
SELECT c.customer_number, c.subsidiary,
       COALESCE(NULLIF(TRIM(c.first_name || ' ' || c.family_name), ''), c.family_name, 'Unbekannt') AS versicherung_name,
       true
FROM loco_customers_suppliers c
WHERE (
    c.family_name ILIKE '%versicherung%'
    OR c.family_name ILIKE '%huk%'
    OR c.family_name ILIKE '%allianz%'
    OR c.family_name ILIKE '%devk%'
    OR c.family_name ILIKE '%adac%'
    OR c.family_name ILIKE '%lvm%'
    OR c.family_name ILIKE '%r+v%'
    OR c.family_name ILIKE '%agrippina%'
    OR c.family_name ILIKE '%arag%'
    OR c.family_name ILIKE '%gerling%'
    OR c.family_name ILIKE '%nordstern%'
    OR c.family_name ILIKE '%bayer%versicherung%'
    OR c.family_name ILIKE '%thuringia%versicherung%'
    OR c.family_name ILIKE '%vhv%'
    OR c.family_name ILIKE '%kravag%'
    OR c.family_name ILIKE '%car-garantie%'
    OR c.family_name ILIKE '%versicherungsmakler%'
)
ON CONFLICT (customer_number, subsidiary) DO NOTHING;

COMMIT;
