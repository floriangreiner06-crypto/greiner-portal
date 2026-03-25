-- Modalitäten & Parameter im Admin-Bereich (neben Konten & Banken)
-- Zugriff: Admin → Modalitäten & Parameter; Änderungen quartalsweise.

BEGIN;

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT
    a.id,
    'Modalitäten & Parameter',
    '/admin/modalitaeten',
    'bi-sliders',
    2,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Modalitäten & Parameter'
);

COMMIT;
