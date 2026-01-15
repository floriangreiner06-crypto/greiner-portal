-- Migration TAG 190: Individuelle Startseite
-- Erstellt: 2026-01-14
-- Zweck: User können ihre persönliche Startseite konfigurieren

-- Tabelle für verfügbare Dashboards
CREATE TABLE IF NOT EXISTS available_dashboards (
    id SERIAL PRIMARY KEY,
    dashboard_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    url VARCHAR(255) NOT NULL,
    icon VARCHAR(50),
    category VARCHAR(50),
    requires_feature VARCHAR(100),
    role_restriction VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dashboards_category ON available_dashboards(category);
CREATE INDEX IF NOT EXISTS idx_dashboards_active ON available_dashboards(active);

-- Tabelle für User-Dashboard-Konfiguration
CREATE TABLE IF NOT EXISTS user_dashboard_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dashboard_type VARCHAR(50) NOT NULL DEFAULT 'redirect',
    target_url VARCHAR(255),
    widget_config JSONB,
    layout_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_dashboard_user ON user_dashboard_config(user_id);

-- Initial-Dashboards einfügen
INSERT INTO available_dashboards (dashboard_key, name, description, url, icon, category, display_order) VALUES
    ('dashboard', 'Allgemeines Dashboard', 'Übersicht über alle Bereiche', '/dashboard', 'bi-speedometer2', 'general', 1),
    ('verkauf_auftragseingang', 'Auftragseingang', 'Verkaufsaufträge verwalten', '/verkauf/auftragseingang', 'bi-cart', 'verkauf', 2),
    ('werkstatt_dashboard', 'Werkstatt Dashboard', 'Werkstatt-Übersicht', '/werkstatt/dashboard', 'bi-tools', 'werkstatt', 3),
    ('controlling', 'Controlling', 'Finanz-Controlling', '/controlling', 'bi-graph-up', 'controlling', 4),
    ('bankenspiegel', 'Bankenspiegel', 'Bankkonten-Übersicht', '/bankenspiegel', 'bi-bank', 'finanzen', 5),
    ('mein_bereich', 'Mein Bereich', 'Persönlicher Bereich für Serviceberater', '/mein-bereich', 'bi-person', 'personal', 6),
    ('aftersales_serviceberater', 'Serviceberater Controlling', 'Serviceberater-Übersicht', '/aftersales/serviceberater/', 'bi-people', 'aftersales', 7),
    ('aftersales_garantie', 'Garantieaufträge', 'Garantieaufträge-Übersicht', '/aftersales/garantie/auftraege', 'bi-shield-check', 'aftersales', 8),
    ('werkstatt_live', 'Werkstatt Live', 'Live-Übersicht Werkstatt', '/werkstatt/live', 'bi-lightning-charge', 'werkstatt', 9),
    ('urlaubsplaner', 'Urlaubsplaner', 'Urlaubsverwaltung', '/urlaubsplaner', 'bi-calendar', 'hr', 10)
ON CONFLICT (dashboard_key) DO NOTHING;

-- Kommentare hinzufügen
COMMENT ON TABLE available_dashboards IS 'Verfügbare Dashboards für individuelle Startseiten-Konfiguration (TAG 190)';
COMMENT ON TABLE user_dashboard_config IS 'Individuelle Startseiten-Konfiguration pro User (TAG 190)';
COMMENT ON COLUMN user_dashboard_config.dashboard_type IS 'Typ: redirect (URL-Weiterleitung) oder custom (Widgets)';
COMMENT ON COLUMN user_dashboard_config.target_url IS 'Ziel-URL für redirect-Typ';
