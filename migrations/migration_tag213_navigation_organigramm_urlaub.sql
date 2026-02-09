-- Migration TAG 213: Organigramm + Urlaubsplaner Admin in DB-Navigation
-- Zweck: Fehlende Admin-Dropdown-Punkte aus Fallback-Navigation in navigation_items ergänzen

BEGIN;

-- Organigramm (nach Mitarbeiterverwaltung)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    a.id,
    'Organigramm',
    '/admin/organigramm',
    'bi-diagram-3',
    6,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Organigramm'
);

-- Urlaubsplaner Admin (nach Organigramm)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    a.id,
    'Urlaubsplaner Admin',
    '/urlaubsplaner/admin',
    'bi-calendar-check',
    7,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Urlaubsplaner Admin'
);

COMMIT;
