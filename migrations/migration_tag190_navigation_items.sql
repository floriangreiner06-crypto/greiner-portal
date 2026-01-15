-- Migration TAG 190: Zentrales Navigations-Management
-- Erstellt: 2026-01-14
-- Zweck: DB-basierte Navigation mit Feature-Zuordnung

-- Tabelle für Navigation-Items
CREATE TABLE IF NOT EXISTS navigation_items (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES navigation_items(id) ON DELETE CASCADE,
    label VARCHAR(200) NOT NULL,
    url VARCHAR(255),
    icon VARCHAR(50),
    order_index INTEGER DEFAULT 0,
    requires_feature VARCHAR(100),  -- Optional: Feature-Zugriff erforderlich
    role_restriction VARCHAR(50),   -- Optional: Nur für bestimmte Rolle
    is_dropdown BOOLEAN DEFAULT false,
    is_header BOOLEAN DEFAULT false,  -- Für Dropdown-Header
    is_divider BOOLEAN DEFAULT false, -- Für Dropdown-Divider
    active BOOLEAN DEFAULT true,
    category VARCHAR(50) DEFAULT 'main',  -- 'main', 'dropdown', 'user_menu'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nav_parent ON navigation_items(parent_id);
CREATE INDEX IF NOT EXISTS idx_nav_active ON navigation_items(active);
CREATE INDEX IF NOT EXISTS idx_nav_category ON navigation_items(category);
CREATE INDEX IF NOT EXISTS idx_nav_order ON navigation_items(order_index);

-- Kommentare
COMMENT ON TABLE navigation_items IS 'Zentrale Navigation-Items mit Feature-Zuordnung (TAG 190)';
COMMENT ON COLUMN navigation_items.requires_feature IS 'Feature-Name aus feature_access Tabelle (optional)';
COMMENT ON COLUMN navigation_items.role_restriction IS 'Nur für bestimmte Rolle sichtbar (optional)';
COMMENT ON COLUMN navigation_items.is_header IS 'Dropdown-Header (z.B. "Übersichten")';
COMMENT ON COLUMN navigation_items.is_divider IS 'Dropdown-Divider (Trennlinie)';
