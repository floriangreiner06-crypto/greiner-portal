-- Service-Untermenüs nur für User mit passendem Feature anzeigen
-- Roland (Rolle verkauf) soll z. B. Service nicht mit Werkstatt/Garantie/Serviceberater/DRIVE sehen.
-- Vorher: Werkstatt, Garantie, Serviceberater, DRIVE hatten kein requires_feature → für alle sichtbar.

UPDATE navigation_items
SET requires_feature = 'aftersales'
WHERE parent_id = (SELECT id FROM navigation_items WHERE label = 'Service' AND parent_id IS NULL LIMIT 1)
  AND label IN ('Werkstatt', 'Garantie', 'Serviceberater')
  AND category = 'dropdown';

-- DRIVE (Werkstatt-Live/ML) nur mit werkstatt_live oder aftersales
UPDATE navigation_items
SET requires_feature = 'werkstatt_live'
WHERE parent_id = (SELECT id FROM navigation_items WHERE label = 'Service' AND parent_id IS NULL LIMIT 1)
  AND label = 'DRIVE'
  AND category = 'dropdown';
