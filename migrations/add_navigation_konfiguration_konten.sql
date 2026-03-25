-- Konfiguration-Hub und Konten & Banken im Admin-Dropdown (DB-Navigation)
-- Konfiguration: nur admin. Konten & Banken: admin + buchhaltung (Berechtigung pro Unterseite siehe Hub).

BEGIN;

-- Konfiguration & Verwaltung (Hub)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT
    a.id,
    'Konfiguration & Verwaltung',
    '/admin/konfiguration',
    'bi-gear-wide-connected',
    0,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Konfiguration & Verwaltung'
);

-- Konten & Banken (admin + buchhaltung)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT
    a.id,
    'Konten & Banken',
    '/admin/konten-verwaltung',
    'bi-wallet2',
    1,
    'admin,buchhaltung',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Konten & Banken'
);

COMMIT;
