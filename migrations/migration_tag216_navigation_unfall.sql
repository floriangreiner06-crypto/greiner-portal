-- Unfall-Rechnungsprüfung & Wissensdatenbank unter Service → Werkstatt
-- Damit die Links in der DB-Navigation erscheinen (Service/Werkstatt wie im Screenshot)
-- Erstellt: 2026-02-11

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, category, active)
SELECT
    w.id,
    'Unfall-Rechnungsprüfung',
    '/werkstatt/unfall-rechnungspruefung',
    'bi-file-earmark-check text-primary',
    20,
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Werkstatt' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Service' AND parent_id IS NULL LIMIT 1) LIMIT 1) w
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = w.id AND n.label = 'Unfall-Rechnungsprüfung'
);

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, category, active)
SELECT
    w.id,
    'Unfall-Wissensdatenbank',
    '/werkstatt/unfall-wissensdatenbank',
    'bi-journal-bookmark',
    21,
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Werkstatt' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Service' AND parent_id IS NULL LIMIT 1) LIMIT 1) w
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = w.id AND n.label = 'Unfall-Wissensdatenbank'
);
