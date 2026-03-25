-- Verkauf-Menü: Alle Punkte mit eigenem Feature für feine Steuerung in der Rechteverwaltung
-- Verkauf (Rolle) soll nur: Auftragseingang, Auslieferungen, Meine Provision, ggf. WhatsApp
-- Nicht: eAutoseller, GW-Standzeit, Planung/Budget/Lieferforecast, Verkäufer-Zielplanung, Leasys, Provisions-Dashboard (VKL)

-- Feature verkaeufer_zielplanung: VKL/GF/Admin (nicht Verkäufer)
INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('verkaeufer_zielplanung', 'admin', 'migration', NOW()),
  ('verkaeufer_zielplanung', 'geschaeftsleitung', 'migration', NOW()),
  ('verkaeufer_zielplanung', 'verkauf_leitung', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;

-- Feature planung: Budget, Lieferforecast (VKL/Admin)
INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('planung', 'admin', 'migration', NOW()),
  ('planung', 'geschaeftsleitung', 'migration', NOW()),
  ('planung', 'verkauf_leitung', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;

-- Feature provision: Meine Provision (alle Verkäufer + VKL)
INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('provision', 'admin', 'migration', NOW()),
  ('provision', 'geschaeftsleitung', 'migration', NOW()),
  ('provision', 'verkauf', 'migration', NOW()),
  ('provision', 'verkauf_leitung', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;

-- Feature provision_vkl: Provisions-Dashboard nur VKL/GF/Admin
INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('provision_vkl', 'admin', 'migration', NOW()),
  ('provision_vkl', 'geschaeftsleitung', 'migration', NOW()),
  ('provision_vkl', 'verkauf_leitung', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;

-- Feature leasys: Leasys Tools (nicht normaler Verkäufer)
INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('leasys', 'admin', 'migration', NOW()),
  ('leasys', 'disposition', 'migration', NOW()),
  ('leasys', 'verkauf_leitung', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;

-- Feature gw_standzeit: GW-Standzeit (wie Zielplanung, VKL)
INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('gw_standzeit', 'admin', 'migration', NOW()),
  ('gw_standzeit', 'geschaeftsleitung', 'migration', NOW()),
  ('gw_standzeit', 'verkauf_leitung', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;

-- Navigation: requires_feature setzen (label-basiert, unabhängig von IDs)
UPDATE navigation_items SET requires_feature = 'gw_standzeit'
WHERE active = true AND TRIM(label) = 'GW-Standzeit' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

UPDATE navigation_items SET requires_feature = 'planung', role_restriction = NULL
WHERE active = true AND TRIM(label) = 'Planung' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

UPDATE navigation_items SET requires_feature = 'planung', role_restriction = NULL
WHERE active = true AND TRIM(label) = 'Budget-Planung' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

UPDATE navigation_items SET requires_feature = 'planung', role_restriction = NULL
WHERE active = true AND TRIM(label) = 'Lieferforecast' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

UPDATE navigation_items SET requires_feature = 'verkaeufer_zielplanung', role_restriction = NULL
WHERE active = true AND TRIM(label) = 'Verkäufer-Zielplanung' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

UPDATE navigation_items SET requires_feature = 'leasys', role_restriction = NULL
WHERE active = true AND TRIM(label) = 'Leasys Programmfinder' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

UPDATE navigation_items SET requires_feature = 'leasys', role_restriction = NULL
WHERE active = true AND TRIM(label) = 'Leasys Kalkulator' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

UPDATE navigation_items SET requires_feature = 'provision', role_restriction = NULL
WHERE active = true AND TRIM(label) = 'Meine Provision' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

UPDATE navigation_items SET requires_feature = 'provision_vkl', role_restriction = NULL
WHERE active = true AND TRIM(label) = 'Provisions-Dashboard (VKL)' AND parent_id = (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1);

-- Tools (Header): bleibt auftragseingang, damit Verkäufer den Bereich sehen wenn sie Leasys/Provision nicht haben
-- oder auf leasys setzen wenn Tools nur für Leasys-Berechtigte sichtbar sein soll – hier lassen wir auftragseingang
