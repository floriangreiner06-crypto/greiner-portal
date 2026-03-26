-- Mitarbeiterverwaltung aus Admin-Navigation entfernen
-- Erreichbar über Rechteverwaltung → Tab "Mitarbeiterverwaltung"

UPDATE navigation_items
SET active = false
WHERE label = 'Mitarbeiterverwaltung'
  AND url = '/admin/mitarbeiterverwaltung';
