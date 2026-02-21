-- Navigation: Werkstatt-Potenzial (Predictive Scoring / Call-Agent) unter Service
-- Erstellt: 2026-02-21 | Workstream: Marketing
-- requires_feature: marketing_potenzial

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT s.id, 'Werkstatt-Potenzial', '/marketing/potenzial', 'bi-telephone-outbound', 90, 'marketing_potenzial', 'dropdown', true
FROM navigation_items s
WHERE s.label = 'Service' AND s.parent_id IS NULL
AND NOT EXISTS (SELECT 1 FROM navigation_items n WHERE n.parent_id = s.id AND n.label = 'Werkstatt-Potenzial')
LIMIT 1;
