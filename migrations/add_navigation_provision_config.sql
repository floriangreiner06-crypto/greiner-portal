-- Migration: Provisionsarten in DB-Navigation (Admin-Dropdown)
-- Zweck: Navi-Punkt "Provisionsarten" im Admin-Dropdown (wenn USE_DB_NAVIGATION=true)

BEGIN;

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    a.id,
    'Provisionsarten',
    '/admin/provision-config',
    'bi-percent',
    8,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Provisionsarten'
);

COMMIT;
