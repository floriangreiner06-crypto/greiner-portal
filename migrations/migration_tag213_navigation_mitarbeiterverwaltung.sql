-- Migration TAG 213: Mitarbeiterverwaltung in Navigation (DB-Navigation)
-- Zweck: Navi-Punkt "Mitarbeiterverwaltung" im Admin-Dropdown (wenn Navigation aus DB geladen wird)

BEGIN;

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    a.id,
    'Mitarbeiterverwaltung',
    '/admin/mitarbeiterverwaltung',
    'bi-people',
    5,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Mitarbeiterverwaltung'
);

COMMIT;
