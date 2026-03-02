-- Liquiditätsvorschau unter Controlling (Phase 1 Cashflow)
-- Workstream: Controlling | 2026-03-02
-- Sichtbar für alle mit Feature 'controlling' (wie Parent)

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT c.id, 'Liquiditätsvorschau', '/controlling/liquiditaet', 'bi-graph-up', 26, 'controlling', 'dropdown', true
FROM navigation_items c
WHERE c.label = 'Controlling' AND c.parent_id IS NULL
  AND NOT EXISTS (SELECT 1 FROM navigation_items n WHERE n.parent_id = c.id AND n.label = 'Liquiditätsvorschau');
