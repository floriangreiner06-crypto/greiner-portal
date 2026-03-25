-- Migration: Offene Posten (OPOS) unter Controlling
-- Erstellt: 2026-02-19 | Workstream: Controlling
-- requires_feature: opos (admin, buchhaltung, verkauf_leitung, verkauf)

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT c.id, 'Offene Posten (OPOS)', '/controlling/opos', 'bi-receipt-cutoff', 24, 'opos', 'dropdown', true
FROM navigation_items c
WHERE c.label = 'Controlling' AND c.parent_id IS NULL
AND NOT EXISTS (SELECT 1 FROM navigation_items n WHERE n.parent_id = c.id AND n.label = 'Offene Posten (OPOS)')
LIMIT 1;
