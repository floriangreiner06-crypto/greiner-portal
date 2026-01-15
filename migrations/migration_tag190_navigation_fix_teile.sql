-- Fix: Teile-Items nach "Teile & Zubehör" verschieben
-- Erstellt: 2026-01-14

BEGIN;

DO $$
DECLARE
    teile_zubehoer_id INTEGER;
    teile_status_id INTEGER;
    renner_penner_id INTEGER;
    bestellungen_id INTEGER;
    preisradar_id INTEGER;
BEGIN
    -- Teile & Zubehör ID finden
    SELECT id INTO teile_zubehoer_id FROM navigation_items WHERE label = 'Teile & Zubehör' AND parent_id IS NULL;
    
    -- Teile-Items finden
    SELECT id INTO teile_status_id FROM navigation_items 
    WHERE (label = 'Teile-Status' OR url = '/werkstatt/teile-status') 
    AND parent_id IS NOT NULL;
    
    SELECT id INTO renner_penner_id FROM navigation_items 
    WHERE (label = 'Renner & Penner' OR url = '/werkstatt/renner-penner') 
    AND parent_id IS NOT NULL;
    
    SELECT id INTO bestellungen_id FROM navigation_items 
    WHERE (label = 'Teilebestellungen' OR url = '/aftersales/teile/bestellungen') 
    AND parent_id IS NOT NULL;
    
    SELECT id INTO preisradar_id FROM navigation_items 
    WHERE (label = 'Preisradar' OR url = '/aftersales/teile/preisradar') 
    AND parent_id IS NOT NULL;
    
    -- Items verschieben
    IF teile_zubehoer_id IS NOT NULL THEN
        IF teile_status_id IS NOT NULL THEN
            UPDATE navigation_items
            SET parent_id = teile_zubehoer_id,
                order_index = 1,
                category = 'dropdown',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = teile_status_id;
        END IF;
        
        IF renner_penner_id IS NOT NULL THEN
            UPDATE navigation_items
            SET parent_id = teile_zubehoer_id,
                order_index = 2,
                category = 'dropdown',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = renner_penner_id;
        END IF;
        
        IF bestellungen_id IS NOT NULL THEN
            UPDATE navigation_items
            SET parent_id = teile_zubehoer_id,
                order_index = 3,
                category = 'dropdown',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = bestellungen_id;
        END IF;
        
        IF preisradar_id IS NOT NULL THEN
            UPDATE navigation_items
            SET parent_id = teile_zubehoer_id,
                order_index = 4,
                category = 'dropdown',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = preisradar_id;
        END IF;
    END IF;
END $$;

COMMIT;

SELECT 'Teile-Items verschoben!' as status;
SELECT n1.label as top_level, n2.label as item, n2.url 
FROM navigation_items n1 
JOIN navigation_items n2 ON n2.parent_id = n1.id 
WHERE n1.label = 'Teile & Zubehör' 
ORDER BY n2.order_index;
