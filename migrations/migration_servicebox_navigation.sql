-- Migration: ServiceBox Zugang in DB-Navigation (Admin-Dropdown)
-- Zweck: Navi-Punkt "ServiceBox Zugang" aus base.html-Fallback in navigation_items überführen

BEGIN;

-- ServiceBox Zugang (nach Rechteverwaltung, order_index 5)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    a.id,
    'ServiceBox Zugang',
    '/admin/servicebox-zugang',
    'bi-key',
    5,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'ServiceBox Zugang'
);

-- Bestehende Admin-Items mit order_index >= 5 um 1 nach unten schieben (ServiceBox ausnehmen)
UPDATE navigation_items
SET order_index = order_index + 1
WHERE parent_id = (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1)
  AND order_index >= 5
  AND label != 'ServiceBox Zugang';

COMMIT;
