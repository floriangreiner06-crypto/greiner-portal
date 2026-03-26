-- Verkaufsempfehlungen AfA unter Controlling (nur GF/VKL, Feature afa_verkaufsempfehlungen)
-- Workstream: Controlling | 2026-03-02

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT c.id, 'Verkaufsempfehlungen AfA', '/controlling/afa/verkaufsempfehlungen', 'bi-graph-up-arrow', 28, 'afa_verkaufsempfehlungen', 'dropdown', true
FROM navigation_items c
WHERE c.label = 'Controlling' AND c.parent_id IS NULL
  AND NOT EXISTS (SELECT 1 FROM navigation_items n WHERE n.parent_id = c.id AND n.label = 'Verkaufsempfehlungen AfA');
