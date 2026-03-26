-- VKL-Verkaufsleiter-Dashboard: Rechte + Navi
-- URL /verkauf/dashboard, Feature verkauf_dashboard (nur admin, geschaeftsleitung, verkauf_leitung)
-- Einkaufsfinanzierung + AfA für VKL/GF ergänzt

-- Alte breite Zuordnung verkauf_dashboard entfernen (nur noch Führung)
DELETE FROM feature_access
WHERE feature_name = 'verkauf_dashboard'
  AND role_name IN ('verkauf', 'buchhaltung', 'disposition');

INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('verkauf_dashboard', 'geschaeftsleitung', 'migration_vkl_dash', NOW()),
  ('einkaufsfinanzierung', 'verkauf_leitung', 'migration_vkl_dash', NOW()),
  ('einkaufsfinanzierung', 'geschaeftsleitung', 'migration_vkl_dash', NOW()),
  ('afa_verkaufsempfehlungen', 'geschaeftsleitung', 'migration_vkl_dash', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;

INSERT INTO navigation_items (
    parent_id,
    label,
    url,
    icon,
    order_index,
    requires_feature,
    role_restriction,
    category,
    active
)
SELECT
    v.id,
    'Verkaufsleiter-Dashboard',
    '/verkauf/dashboard',
    'bi-speedometer2 text-primary',
    4,
    'verkauf_dashboard',
    'admin,geschaeftsleitung,verkauf_leitung',
    'dropdown',
    true
FROM navigation_items v
WHERE v.label = 'Verkauf' AND v.parent_id IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM navigation_items c
    WHERE c.parent_id = v.id AND c.url = '/verkauf/dashboard'
  )
LIMIT 1;
