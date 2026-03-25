-- Controlling-Untermenüs nur für Rollen mit Feature "controlling" anzeigen
-- (z. B. Verkäufer mit nur OPOS sehen dann nicht mehr Übersichten, Planung, Analysen)

UPDATE navigation_items
SET requires_feature = 'controlling'
WHERE active = true
  AND (TRIM(label) = 'Übersichten' OR TRIM(label) = 'Planung' OR TRIM(label) = 'Analysen')
  AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Controlling' AND parent_id IS NULL LIMIT 1);
