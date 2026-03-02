-- Filter-Verhalten: Leistungsübersicht Werkstatt – Rolle werkstatt = nur eigene Leistung (wie bei Verkäufer-Listen)
INSERT INTO feature_filter_mode (feature_name, role_name, filter_mode)
VALUES ('werkstatt_leistungsuebersicht', 'werkstatt', 'own_only')
ON CONFLICT (feature_name, role_name) DO NOTHING;
