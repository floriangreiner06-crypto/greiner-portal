-- Fix: Controlling-Struktur mit Sub-Dropdowns korrigieren
-- Erstellt: 2026-01-14

BEGIN;

DO $$
DECLARE
    controlling_id INTEGER;
    uebersichten_id INTEGER;
    planung_id INTEGER;
    analysen_id INTEGER;
BEGIN
    -- Controlling ID finden
    SELECT id INTO controlling_id FROM navigation_items WHERE label = 'Controlling' AND parent_id IS NULL;
    
    -- Alte Header/Items löschen, die nicht mehr benötigt werden
    DELETE FROM navigation_items 
    WHERE parent_id = controlling_id 
    AND (is_header = true OR label = 'Archiv' OR url = '/controlling/tek/archiv');
    
    -- Übersichten Sub-Dropdown erstellen (falls nicht vorhanden)
    SELECT id INTO uebersichten_id FROM navigation_items 
    WHERE label = 'Übersichten' AND parent_id = controlling_id AND is_dropdown = true;
    
    IF uebersichten_id IS NULL THEN
        INSERT INTO navigation_items (parent_id, label, url, icon, order_index, is_dropdown, category, active)
        VALUES (controlling_id, 'Übersichten', NULL, 'bi-speedometer2', 1, true, 'dropdown', true)
        RETURNING id INTO uebersichten_id;
    END IF;
    
    -- Bestehende Items nach Übersichten verschieben
    UPDATE navigation_items
    SET parent_id = uebersichten_id,
        order_index = CASE 
            WHEN url = '/controlling/dashboard' THEN 1
            WHEN url = '/controlling/bwa' THEN 2
            WHEN url = '/controlling/tek' THEN 3
            WHEN url = '/controlling/kontenmapping' THEN 4
            WHEN url = '/bankenspiegel/dashboard' THEN 5
            WHEN url = '/bankenspiegel/konten' THEN 6
            WHEN url = '/bankenspiegel/transaktionen' THEN 7
            ELSE order_index
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE parent_id = controlling_id 
    AND url IN ('/controlling/dashboard', '/controlling/bwa', '/controlling/tek', '/controlling/kontenmapping', '/bankenspiegel/dashboard', '/bankenspiegel/konten', '/bankenspiegel/transaktionen');
    
    -- Planung Sub-Dropdown erstellen (falls nicht vorhanden)
    SELECT id INTO planung_id FROM navigation_items 
    WHERE label = 'Planung' AND parent_id = controlling_id AND is_dropdown = true;
    
    IF planung_id IS NULL THEN
        INSERT INTO navigation_items (parent_id, label, url, icon, order_index, is_dropdown, category, active)
        VALUES (controlling_id, 'Planung', NULL, 'bi-bullseye', 2, true, 'dropdown', true)
        RETURNING id INTO planung_id;
    END IF;
    
    -- Planung-Items verschieben
    UPDATE navigation_items
    SET parent_id = planung_id,
        order_index = CASE 
            WHEN url = '/planung/abteilungsleiter' THEN 1
            WHEN url = '/controlling/unternehmensplan' THEN 2
            WHEN url = '/controlling/kst-ziele' THEN 3
            ELSE order_index
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE parent_id = controlling_id 
    AND url IN ('/planung/abteilungsleiter', '/controlling/unternehmensplan', '/controlling/kst-ziele');
    
    -- Analysen Sub-Dropdown erstellen (falls nicht vorhanden)
    SELECT id INTO analysen_id FROM navigation_items 
    WHERE label = 'Analysen' AND parent_id = controlling_id AND is_dropdown = true;
    
    IF analysen_id IS NULL THEN
        INSERT INTO navigation_items (parent_id, label, url, icon, order_index, is_dropdown, category, active)
        VALUES (controlling_id, 'Analysen', NULL, 'bi-graph-up-arrow', 3, true, 'dropdown', true)
        RETURNING id INTO analysen_id;
    END IF;
    
    -- Analysen-Items verschieben
    UPDATE navigation_items
    SET parent_id = analysen_id,
        order_index = CASE 
            WHEN url = '/bankenspiegel/zinsen-analyse' THEN 1
            WHEN url = '/bankenspiegel/einkaufsfinanzierung' THEN 2
            WHEN url = '/bankenspiegel/fahrzeugfinanzierungen' THEN 3
            ELSE order_index
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE parent_id = controlling_id 
    AND url IN ('/bankenspiegel/zinsen-analyse', '/bankenspiegel/einkaufsfinanzierung', '/bankenspiegel/fahrzeugfinanzierungen');
    
END $$;

COMMIT;

SELECT 'Controlling-Struktur korrigiert!' as status;
SELECT n1.label as top, n2.label as sub, n3.label as item, n3.url
FROM navigation_items n1
JOIN navigation_items n2 ON n2.parent_id = n1.id AND n2.is_dropdown = true
LEFT JOIN navigation_items n3 ON n3.parent_id = n2.id
WHERE n1.label = 'Controlling'
ORDER BY n2.order_index, n3.order_index
LIMIT 25;
