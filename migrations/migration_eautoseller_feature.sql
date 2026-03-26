-- Eigenes Feature "eautoseller" für Menüpunkt eAutoseller Bestand
-- Rolle "Verkauf" soll eAutoseller Bestand nicht sehen; Verkaufsleitung/Admin/Disposition schon.

-- Feature-Zugriff: eautoseller für Admin, Verkaufsleitung, Disposition (nicht für verkauf)
INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('eautoseller', 'admin', 'migration', NOW()),
  ('eautoseller', 'verkauf_leitung', 'migration', NOW()),
  ('eautoseller', 'disposition', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;

-- Menüpunkt nutzt jetzt Feature "eautoseller" statt "auftragseingang"
UPDATE navigation_items
SET requires_feature = 'eautoseller'
WHERE active = true AND label = 'eAutoseller Bestand';
