-- Migration TAG 190: Navigation-Struktur umbauen
-- Erstellt: 2026-01-14
-- Zweck: After Sales aufteilen, Urlaubsplaner umbenennen, Bankenspiegel verschieben, etc.

BEGIN;

-- 1. "After Sales" umbenennen in "Service"
UPDATE navigation_items 
SET label = 'Service', 
    order_index = 1,
    updated_at = CURRENT_TIMESTAMP
WHERE label = 'After Sales' AND parent_id IS NULL;

-- 2. "Teile" Sub-Dropdown aus "Service" entfernen und als Top-Level "Teile & Zubehör" erstellen
-- Zuerst: Teile-Items finden und parent_id merken
DO $$
DECLARE
    service_id INTEGER;
    teile_parent_id INTEGER;
    new_order_index INTEGER;
BEGIN
    -- Service-ID finden
    SELECT id INTO service_id FROM navigation_items WHERE label = 'Service' AND parent_id IS NULL;
    
    -- Teile-Dropdown-ID finden
    SELECT id INTO teile_parent_id FROM navigation_items WHERE label = 'Teile' AND parent_id = service_id;
    
    -- Neues Top-Level "Teile & Zubehör" erstellen
    INSERT INTO navigation_items (label, url, icon, order_index, requires_feature, is_dropdown, category, active)
    VALUES ('Teile & Zubehör', NULL, 'bi-box-seam', 2, 'teilebestellungen', true, 'main', true)
    RETURNING id INTO new_order_index;
    
    -- Alle Teile-Items auf neues Top-Level verschieben
    UPDATE navigation_items
    SET parent_id = new_order_index,
        category = 'dropdown',
        updated_at = CURRENT_TIMESTAMP
    WHERE parent_id = teile_parent_id;
    
    -- Alten "Teile" Header löschen
    DELETE FROM navigation_items WHERE id = teile_parent_id;
END $$;

-- 3. "Urlaubsplaner" umbenennen in "Team Greiner"
UPDATE navigation_items 
SET label = 'Team Greiner', 
    order_index = 5,
    updated_at = CURRENT_TIMESTAMP
WHERE label = 'Urlaubsplaner' AND parent_id IS NULL;

-- 4. Jahresprämie von Controlling/Analysen nach Team Greiner verschieben
DO $$
DECLARE
    team_greiner_id INTEGER;
    jahrespraemie_id INTEGER;
BEGIN
    -- Team Greiner ID finden
    SELECT id INTO team_greiner_id FROM navigation_items WHERE label = 'Team Greiner' AND parent_id IS NULL;
    
    -- Jahresprämie finden und verschieben
    SELECT id INTO jahrespraemie_id FROM navigation_items WHERE url = '/jahrespraemie/' AND label = 'Jahresprämie';
    
    IF jahrespraemie_id IS NOT NULL THEN
        UPDATE navigation_items
        SET parent_id = team_greiner_id,
            order_index = 3,
            category = 'dropdown',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = jahrespraemie_id;
    END IF;
END $$;

-- 5. Bankenspiegel-Items nach Controlling/Übersichten verschieben
DO $$
DECLARE
    controlling_id INTEGER;
    uebersichten_id INTEGER;
    bankenspiegel_dashboard_id INTEGER;
    bankenspiegel_konten_id INTEGER;
    bankenspiegel_transaktionen_id INTEGER;
BEGIN
    -- Controlling ID finden
    SELECT id INTO controlling_id FROM navigation_items WHERE label = 'Controlling' AND parent_id IS NULL;
    
    -- Übersichten Sub-Dropdown finden
    SELECT id INTO uebersichten_id FROM navigation_items 
    WHERE label = 'Übersichten' AND parent_id = controlling_id AND is_dropdown = true;
    
    -- Bankenspiegel-Items finden (aus dem alten Bankenspiegel-Header)
    SELECT id INTO bankenspiegel_dashboard_id FROM navigation_items 
    WHERE url = '/bankenspiegel/dashboard' AND label = 'Dashboard';
    
    SELECT id INTO bankenspiegel_konten_id FROM navigation_items 
    WHERE url = '/bankenspiegel/konten' AND label = 'Kontenübersicht';
    
    SELECT id INTO bankenspiegel_transaktionen_id FROM navigation_items 
    WHERE url = '/bankenspiegel/transaktionen' AND label = 'Transaktionen';
    
    -- Items verschieben
    IF uebersichten_id IS NOT NULL THEN
        IF bankenspiegel_dashboard_id IS NOT NULL THEN
            UPDATE navigation_items
            SET parent_id = uebersichten_id,
                order_index = 5,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = bankenspiegel_dashboard_id;
        END IF;
        
        IF bankenspiegel_konten_id IS NOT NULL THEN
            UPDATE navigation_items
            SET parent_id = uebersichten_id,
                order_index = 6,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = bankenspiegel_konten_id;
        END IF;
        
        IF bankenspiegel_transaktionen_id IS NOT NULL THEN
            UPDATE navigation_items
            SET parent_id = uebersichten_id,
                order_index = 7,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = bankenspiegel_transaktionen_id;
        END IF;
    END IF;
END $$;

-- 6. Fahrzeugfinanzierungen nach Controlling/Analysen verschieben
DO $$
DECLARE
    controlling_id INTEGER;
    analysen_id INTEGER;
    fahrzeugfinanzierungen_id INTEGER;
BEGIN
    -- Controlling ID finden
    SELECT id INTO controlling_id FROM navigation_items WHERE label = 'Controlling' AND parent_id IS NULL;
    
    -- Analysen Sub-Dropdown finden
    SELECT id INTO analysen_id FROM navigation_items 
    WHERE label = 'Analysen' AND parent_id = controlling_id AND is_dropdown = true;
    
    -- Fahrzeugfinanzierungen finden
    SELECT id INTO fahrzeugfinanzierungen_id FROM navigation_items 
    WHERE url = '/bankenspiegel/fahrzeugfinanzierungen' AND label = 'Fahrzeugfinanzierungen';
    
    -- Verschieben
    IF analysen_id IS NOT NULL AND fahrzeugfinanzierungen_id IS NOT NULL THEN
        UPDATE navigation_items
        SET parent_id = analysen_id,
            order_index = 4,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = fahrzeugfinanzierungen_id;
    END IF;
END $$;

-- 7. Alten "Bankenspiegel" Header und Divider entfernen (falls noch vorhanden)
DELETE FROM navigation_items 
WHERE label = 'Bankenspiegel' AND is_header = true;

-- 8. Sortierung anpassen für alle Top-Level Items
UPDATE navigation_items SET order_index = 1 WHERE label = 'Service' AND parent_id IS NULL;
UPDATE navigation_items SET order_index = 2 WHERE label = 'Teile & Zubehör' AND parent_id IS NULL;
UPDATE navigation_items SET order_index = 3 WHERE label = 'Verkauf' AND parent_id IS NULL;
UPDATE navigation_items SET order_index = 4 WHERE label = 'Controlling' AND parent_id IS NULL;
UPDATE navigation_items SET order_index = 5 WHERE label = 'Team Greiner' AND parent_id IS NULL;
UPDATE navigation_items SET order_index = 6 WHERE label = 'Admin' AND parent_id IS NULL;

-- 9. "Teile & Zubehör" Items: order_index anpassen (flache Liste, keine Sub-Dropdowns)
UPDATE navigation_items
SET order_index = subquery.new_order
FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY order_index) as new_order
    FROM navigation_items
    WHERE parent_id = (SELECT id FROM navigation_items WHERE label = 'Teile & Zubehör' AND parent_id IS NULL)
) AS subquery
WHERE navigation_items.id = subquery.id;

COMMIT;

-- Zusammenfassung
SELECT 'Migration abgeschlossen!' as status;
SELECT label, order_index FROM navigation_items WHERE parent_id IS NULL ORDER BY order_index;
