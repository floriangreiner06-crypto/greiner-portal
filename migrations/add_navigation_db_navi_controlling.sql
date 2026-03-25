-- Rollback: DB Navi war falsch. Stattdessen: Tagesumsatz unter Controlling.
-- Workstream: Controlling

-- Falls noch vorhanden: DB Navi entfernen
DELETE FROM navigation_items WHERE label = 'DB Navi';

-- Tagesumsatz unter Controlling (für alle mit Feature controlling)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT c.id, 'Tagesumsatz', '/controlling/tagesumsatz', 'bi-currency-euro', 29, 'controlling', 'dropdown', true
FROM navigation_items c
WHERE c.label = 'Controlling' AND c.parent_id IS NULL
  AND NOT EXISTS (SELECT 1 FROM navigation_items n WHERE n.parent_id = c.id AND n.label = 'Tagesumsatz')
LIMIT 1;
