-- Migration TAG 192: Bug-Übersicht zur Navigation hinzufügen (nur für Admin)
-- Erstellt: 2026-01-14
-- Zweck: Bug-Übersicht Link in Admin-Dropdown einfügen (QA Widget ist direkt auf Feature-Seiten)

BEGIN;

-- Bug-Übersicht als Admin-Dropdown-Item hinzufügen
WITH admin_id AS (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, role_restriction, category, active)
SELECT 
    (SELECT id FROM admin_id),
    'Bug-Übersicht',
    '/qa/bugs',
    'bi-bug',
    10,  -- Nach anderen Admin-Items
    'qa_dashboard',
    'admin',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM admin_id)
ON CONFLICT DO NOTHING;

COMMIT;
