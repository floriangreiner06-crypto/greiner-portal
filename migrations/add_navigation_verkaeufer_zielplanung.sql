-- Verkäufer-Zielplanung in DB-Navigation (Verkauf → Planung)
-- Zweck: Navi-Punkt unter Verkauf sichtbar, wenn USE_DB_NAVIGATION=true.
-- Rolle: admin, geschaeftsleitung, verkauf_leitung (kommasep. in role_restriction;
--        navigation_utils prüft user_role in erlaubte Rollen).

INSERT INTO navigation_items (
    parent_id,
    label,
    url,
    icon,
    order_index,
    role_restriction,
    category,
    active
)
SELECT
    v.id,
    'Verkäufer-Zielplanung',
    '/verkauf/zielplanung',
    'bi-bullseye text-success',
    9,
    'admin,geschaeftsleitung,verkauf_leitung',
    'dropdown',
    true
FROM navigation_items v
WHERE v.label = 'Verkauf' AND v.parent_id IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM navigation_items c
    WHERE c.parent_id = v.id AND c.label = 'Verkäufer-Zielplanung'
  )
LIMIT 1;
