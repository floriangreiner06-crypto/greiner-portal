-- Fix: Service-Struktur mit Sub-Dropdowns korrigieren
-- Erstellt: 2026-01-14

BEGIN;

DO $$
DECLARE
    service_id INTEGER;
    werkstatt_id INTEGER;
    garantie_id INTEGER;
    serviceberater_id INTEGER;
    drive_id INTEGER;
    werkstatt_cockpit_id INTEGER;
    werkstatt_kapazitaet_id INTEGER;
    werkstatt_anwesenheit_id INTEGER;
    werkstatt_auftraege_id INTEGER;
    garantie_auftraege_id INTEGER;
    serviceberater_uebersicht_id INTEGER;
    serviceberater_controlling_id INTEGER;
    drive_briefing_id INTEGER;
    drive_kulanz_id INTEGER;
    drive_kapazitaet_id INTEGER;
BEGIN
    -- Service ID finden
    SELECT id INTO service_id FROM navigation_items WHERE label = 'Service' AND parent_id IS NULL;
    
    -- Alte Items löschen/verschieben
    DELETE FROM navigation_items WHERE parent_id = service_id AND (label = 'Controlling' OR label = '' OR is_divider = true);
    
    -- Werkstatt Sub-Dropdown erstellen
    INSERT INTO navigation_items (parent_id, label, url, icon, order_index, is_dropdown, category, active)
    VALUES (service_id, 'Werkstatt', NULL, 'bi-speedometer2', 1, true, 'dropdown', true)
    RETURNING id INTO werkstatt_id;
    
    -- Werkstatt-Items verschieben/erstellen
    INSERT INTO navigation_items (parent_id, label, url, icon, order_index, category, active)
    VALUES 
        (werkstatt_id, 'Cockpit', '/werkstatt/cockpit', 'bi-speedometer2', 1, 'dropdown', true),
        (werkstatt_id, 'Kapazitätsplanung', '/aftersales/kapazitaet', 'bi-calendar-range', 2, 'dropdown', true),
        (werkstatt_id, 'Anwesenheit', '/werkstatt/anwesenheit', 'bi-person-check', 3, 'dropdown', true),
        (werkstatt_id, 'Aufträge & Prognose', '/werkstatt/auftraege', 'bi-list-check', 4, 'dropdown', true)
    ON CONFLICT DO NOTHING;
    
    -- Garantie Sub-Dropdown erstellen
    INSERT INTO navigation_items (parent_id, label, url, icon, order_index, is_dropdown, category, active)
    VALUES (service_id, 'Garantie', NULL, 'bi-shield-check', 2, true, 'dropdown', true)
    RETURNING id INTO garantie_id;
    
    -- Garantie-Item verschieben
    UPDATE navigation_items
    SET parent_id = garantie_id,
        order_index = 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE url = '/aftersales/garantie/auftraege' AND label = 'Garantieaufträge';
    
    -- Serviceberater Sub-Dropdown erstellen
    INSERT INTO navigation_items (parent_id, label, url, icon, order_index, is_dropdown, category, active)
    VALUES (service_id, 'Serviceberater', NULL, 'bi-people', 3, true, 'dropdown', true)
    RETURNING id INTO serviceberater_id;
    
    -- Serviceberater-Items verschieben
    UPDATE navigation_items
    SET parent_id = serviceberater_id,
        order_index = 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE url = '/aftersales/serviceberater/uebersicht' AND label = 'Serviceberater Übersicht';
    
    UPDATE navigation_items
    SET parent_id = serviceberater_id,
        order_index = 2,
        updated_at = CURRENT_TIMESTAMP
    WHERE url = '/aftersales/serviceberater/' AND label = 'Serviceberater Controlling';
    
    -- DRIVE Sub-Dropdown erstellen
    INSERT INTO navigation_items (parent_id, label, url, icon, order_index, is_dropdown, category, active)
    VALUES (service_id, 'DRIVE', NULL, 'bi-robot', 4, true, 'dropdown', true)
    RETURNING id INTO drive_id;
    
    -- DRIVE-Items erstellen
    INSERT INTO navigation_items (parent_id, label, url, icon, order_index, category, active)
    VALUES 
        (drive_id, 'Morgen-Briefing', '/werkstatt/drive/briefing', 'bi-sunrise', 1, 'dropdown', true),
        (drive_id, 'Kulanz-Monitor', '/werkstatt/drive/kulanz', 'bi-cash-coin', 2, 'dropdown', true),
        (drive_id, 'ML-Kapazität', '/werkstatt/drive/kapazitaet', 'bi-robot', 3, 'dropdown', true)
    ON CONFLICT DO NOTHING;
    
END $$;

COMMIT;

SELECT 'Service-Struktur korrigiert!' as status;
SELECT n1.label as top_level, n2.label as sub_dropdown, n3.label as item, n3.url
FROM navigation_items n1
JOIN navigation_items n2 ON n2.parent_id = n1.id AND n2.is_dropdown = true
LEFT JOIN navigation_items n3 ON n3.parent_id = n2.id
WHERE n1.label = 'Service'
ORDER BY n2.order_index, n3.order_index
LIMIT 20;
