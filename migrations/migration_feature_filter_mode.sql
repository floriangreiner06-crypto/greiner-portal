-- Filter-Modi für Seiten mit Verkäufer-/Listen-Filter (Auftragseingang, Auslieferungen, OPOS)
-- filter_mode: own_only = nur eigene, Filter nicht auflösbar | own_default = eigene, Filter auflösbar | all_filterable = alle, kann filtern

CREATE TABLE IF NOT EXISTS feature_filter_mode (
    id SERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    filter_mode VARCHAR(30) NOT NULL CHECK (filter_mode IN ('own_only', 'own_default', 'all_filterable')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(feature_name, role_name)
);

CREATE INDEX IF NOT EXISTS idx_feature_filter_mode_feature ON feature_filter_mode(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_filter_mode_role ON feature_filter_mode(role_name);

COMMENT ON TABLE feature_filter_mode IS 'Pro Feature und Rolle: Verhalten des Verkäufer-Filters (nur eigene / auflösbar / alle filterbar)';

-- Bestehendes Verhalten abbilden: Rolle verkauf = nur eigene (nicht auflösbar) für diese drei Features
INSERT INTO feature_filter_mode (feature_name, role_name, filter_mode)
VALUES
    ('auftragseingang', 'verkauf', 'own_only'),
    ('auslieferungen', 'verkauf', 'own_only'),
    ('opos', 'verkauf', 'own_only')
ON CONFLICT (feature_name, role_name) DO NOTHING;
