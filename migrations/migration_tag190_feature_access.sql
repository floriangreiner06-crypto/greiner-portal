-- Migration TAG 190: Feature-Zugriffsverwaltung
-- Erstellt: 2026-01-14
-- Zweck: DB-basierte Feature-Zugriffsverwaltung mit Fallback auf roles_config.py

-- Tabelle für Feature-Zugriff erstellen
CREATE TABLE IF NOT EXISTS feature_access (
    id SERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    UNIQUE(feature_name, role_name)
);

CREATE INDEX IF NOT EXISTS idx_feature_access_feature ON feature_access(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_access_role ON feature_access(role_name);

-- Initial-Daten aus FEATURE_ACCESS (roles_config.py) migrieren
-- Diese Daten werden als Fallback verwendet, wenn DB leer ist
INSERT INTO feature_access (feature_name, role_name, created_by)
VALUES
    -- Controlling / Finanzen
    ('bankenspiegel', 'admin', 'system_migration'),
    ('bankenspiegel', 'buchhaltung', 'system_migration'),
    ('controlling', 'admin', 'system_migration'),
    ('controlling', 'buchhaltung', 'system_migration'),
    ('zinsen', 'admin', 'system_migration'),
    ('zinsen', 'buchhaltung', 'system_migration'),
    ('zinsen', 'verkauf_leitung', 'system_migration'),
    ('zinsen', 'disposition', 'system_migration'),
    
    -- Einkaufsfinanzierung
    ('einkaufsfinanzierung', 'admin', 'system_migration'),
    ('einkaufsfinanzierung', 'buchhaltung', 'system_migration'),
    ('einkaufsfinanzierung', 'disposition', 'system_migration'),
    ('fahrzeugfinanzierungen', 'admin', 'system_migration'),
    ('fahrzeugfinanzierungen', 'buchhaltung', 'system_migration'),
    ('fahrzeugfinanzierungen', 'disposition', 'system_migration'),
    
    -- Verkauf
    ('auftragseingang', 'admin', 'system_migration'),
    ('auftragseingang', 'buchhaltung', 'system_migration'),
    ('auftragseingang', 'verkauf_leitung', 'system_migration'),
    ('auftragseingang', 'verkauf', 'system_migration'),
    ('auftragseingang', 'disposition', 'system_migration'),
    ('auslieferungen', 'admin', 'system_migration'),
    ('auslieferungen', 'buchhaltung', 'system_migration'),
    ('auslieferungen', 'verkauf_leitung', 'system_migration'),
    ('auslieferungen', 'verkauf', 'system_migration'),
    ('auslieferungen', 'disposition', 'system_migration'),
    ('verkauf_dashboard', 'admin', 'system_migration'),
    ('verkauf_dashboard', 'buchhaltung', 'system_migration'),
    ('verkauf_dashboard', 'verkauf_leitung', 'system_migration'),
    ('verkauf_dashboard', 'verkauf', 'system_migration'),
    ('verkauf_dashboard', 'disposition', 'system_migration'),
    
    -- Fahrzeuge / Bestand
    ('fahrzeuge', 'admin', 'system_migration'),
    ('fahrzeuge', 'buchhaltung', 'system_migration'),
    ('fahrzeuge', 'verkauf_leitung', 'system_migration'),
    ('fahrzeuge', 'verkauf', 'system_migration'),
    ('fahrzeuge', 'disposition', 'system_migration'),
    ('stellantis_bestand', 'admin', 'system_migration'),
    ('stellantis_bestand', 'buchhaltung', 'system_migration'),
    ('stellantis_bestand', 'verkauf_leitung', 'system_migration'),
    ('stellantis_bestand', 'verkauf', 'system_migration'),
    ('stellantis_bestand', 'disposition', 'system_migration'),
    
    -- Urlaubsplaner (alle)
    ('urlaubsplaner', '*', 'system_migration'),
    
    -- After Sales / Teile
    ('teilebestellungen', 'admin', 'system_migration'),
    ('teilebestellungen', 'buchhaltung', 'system_migration'),
    ('teilebestellungen', 'lager', 'system_migration'),
    ('teilebestellungen', 'werkstatt', 'system_migration'),
    ('teilebestellungen', 'werkstatt_leitung', 'system_migration'),
    ('teilebestellungen', 'service', 'system_migration'),
    ('teilebestellungen', 'service_leitung', 'system_migration'),
    ('teilebestellungen', 'serviceberater', 'system_migration'),
    ('teilebestellungen', 'disposition', 'system_migration'),
    ('aftersales', 'admin', 'system_migration'),
    ('aftersales', 'buchhaltung', 'system_migration'),
    ('aftersales', 'werkstatt', 'system_migration'),
    ('aftersales', 'werkstatt_leitung', 'system_migration'),
    ('aftersales', 'service', 'system_migration'),
    ('aftersales', 'service_leitung', 'system_migration'),
    ('aftersales', 'serviceberater', 'system_migration'),
    
    -- SB-Controlling
    ('sb_dashboard', 'admin', 'system_migration'),
    ('sb_dashboard', 'buchhaltung', 'system_migration'),
    ('sb_dashboard', 'service_leitung', 'system_migration'),
    ('sb_dashboard', 'serviceberater', 'system_migration'),
    ('sb_ranking', 'admin', 'system_migration'),
    ('sb_ranking', 'buchhaltung', 'system_migration'),
    ('sb_ranking', 'service_leitung', 'system_migration'),
    ('sb_ranking', 'serviceberater', 'system_migration'),
    ('werkstatt_live', 'admin', 'system_migration'),
    ('werkstatt_live', 'buchhaltung', 'system_migration'),
    ('werkstatt_live', 'werkstatt_leitung', 'system_migration'),
    ('werkstatt_live', 'service_leitung', 'system_migration'),
    ('werkstatt_live', 'serviceberater', 'system_migration'),
    
    -- Team-Genehmigungen
    ('urlaub_genehmigen', 'admin', 'system_migration'),
    ('urlaub_genehmigen', 'buchhaltung', 'system_migration'),
    ('urlaub_genehmigen', 'verkauf_leitung', 'system_migration'),
    ('urlaub_genehmigen', 'werkstatt_leitung', 'system_migration'),
    ('urlaub_genehmigen', 'service_leitung', 'system_migration')
ON CONFLICT (feature_name, role_name) DO NOTHING;

-- Kommentar hinzufügen
COMMENT ON TABLE feature_access IS 'Feature-Zugriffsverwaltung - DB-basiert mit Fallback auf roles_config.py (TAG 190)';
COMMENT ON COLUMN feature_access.feature_name IS 'Name des Features (z.B. bankenspiegel, controlling)';
COMMENT ON COLUMN feature_access.role_name IS 'Rolle die Zugriff hat (oder * für alle)';
COMMENT ON COLUMN feature_access.created_by IS 'User der die Zuordnung erstellt hat';
