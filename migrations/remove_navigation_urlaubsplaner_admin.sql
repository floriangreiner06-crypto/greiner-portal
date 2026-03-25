-- Urlaubsplaner Admin aus Admin-Navigation entfernen
-- Funktionalität liegt in Rechteverwaltung → Tab "Urlaubsverwaltung"

UPDATE navigation_items
SET active = false
WHERE label = 'Urlaubsplaner Admin'
  AND url = '/urlaubsplaner/admin';
