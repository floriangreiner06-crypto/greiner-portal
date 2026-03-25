-- Fahrzeuganlage unter Service → Werkstatt (DB-Navigation)

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT
    w.id,
    'Fahrzeuganlage',
    '/werkstatt/fahrzeuganlage',
    'bi-card-image',
    22,
    'fahrzeuganlage',
    'dropdown',
    true
FROM (
    SELECT id FROM navigation_items
    WHERE label = 'Werkstatt'
      AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Service' AND parent_id IS NULL LIMIT 1)
    LIMIT 1
) w
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = w.id AND n.label = 'Fahrzeuganlage'
);
