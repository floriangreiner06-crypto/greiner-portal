-- Feature: AfA Verkaufsempfehlungen (nur GF / VKL)
-- Seite mit Verkaufsempfehlungen für VFW/Mietwagen inkl. verursachte Zinsen
-- Erstellt: 2026-03-02

INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
  ('afa_verkaufsempfehlungen', 'admin', 'migration', NOW()),
  ('afa_verkaufsempfehlungen', 'verkauf_leitung', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;
