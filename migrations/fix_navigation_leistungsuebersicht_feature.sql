-- Leistungsübersicht (unter Werkstatt) mit eigenem Feature, damit Rolle "werkstatt"
-- den Punkt sehen kann, ohne ganzes "aftersales" zu haben.

UPDATE navigation_items
SET requires_feature = 'werkstatt_leistungsuebersicht'
WHERE id = 76 AND label = 'Leistungsübersicht';

-- Rolle werkstatt in DB explizit Zugriff geben (falls schon in Rechteverwaltung reduziert)
INSERT INTO feature_access (role_name, feature_name)
VALUES ('werkstatt', 'werkstatt_leistungsuebersicht')
ON CONFLICT (feature_name, role_name) DO NOTHING;
