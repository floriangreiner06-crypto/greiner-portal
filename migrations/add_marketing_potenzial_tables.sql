-- ============================================================================
-- Marketing Potenzial / Predictive Scoring (Verschleißreparatur Call-Agent)
-- ============================================================================
-- Tabellen in drive_portal (PostgreSQL). Daten aus Locosoft read-only;
-- Script schreibt km-Schätzungen und Reparatur-Scores hierher.
-- ============================================================================

-- Kategorien mit Intervall (km + Jahre) für Prioritäts-Score
CREATE TABLE IF NOT EXISTS repair_categories (
    category_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    interval_km INTEGER NOT NULL,
    interval_years INTEGER NOT NULL
);

INSERT INTO repair_categories (category_id, name, interval_km, interval_years)
VALUES
    ('bremsen_va', 'Bremsen Vorderachse', 50000, 4),
    ('bremsen_ha', 'Bremsen Hinterachse', 80000, 5),
    ('reifen', 'Reifen allgemein', 40000, 5),
    ('zahnriemen', 'Zahnriemen/Steuerkette', 90000, 6),
    ('batterie', 'Batterie/Starterbatterie', 999999, 5)
ON CONFLICT (category_id) DO NOTHING;

-- Keywords pro Kategorie (erweiterbar ohne Code; make_number 0 = alle Marken)
CREATE TABLE IF NOT EXISTS repair_category_keywords (
    id SERIAL PRIMARY KEY,
    category_id VARCHAR(50) NOT NULL REFERENCES repair_categories(category_id) ON DELETE CASCADE,
    keyword VARCHAR(100) NOT NULL,
    make_number INTEGER NOT NULL DEFAULT 0,
    UNIQUE(category_id, keyword, make_number)
);

-- Initial-Keywords aus Phase-1-Analyse (Locosoft text_line); make_number 0 = alle Marken
INSERT INTO repair_category_keywords (category_id, keyword, make_number)
VALUES
    ('bremsen_va', 'bremsscheib', 0),
    ('bremsen_va', 'bremsbelag', 0),
    ('bremsen_va', 'vorderbremse', 0),
    ('bremsen_va', 'vorn ersetzen', 0),
    ('bremsen_ha', 'bremsbelag', 0),
    ('bremsen_ha', 'hinterrad', 0),
    ('bremsen_ha', 'hinten ersetzen', 0),
    ('bremsen_ha', 'scheibe hinten', 0),
    ('batterie', 'batterie', 0),
    ('batterie', 'starterbatterie', 0),
    ('zahnriemen', 'zahnriemen', 0),
    ('zahnriemen', 'steuerkette', 0),
    ('zahnriemen', 'steuerzahnriemen', 0),
    ('reifen', 'reifen ersetzen', 0),
    ('reifen', 'reifen instandsetzen', 0)
ON CONFLICT (category_id, keyword, make_number) DO NOTHING;

-- Fahrzeug km-Schätzung (eine Zeile pro Fahrzeug; vehicle_number = Locosoft internal_number)
CREATE TABLE IF NOT EXISTS vehicle_km_estimates (
    vehicle_number INTEGER PRIMARY KEY,
    km_current_estimate INTEGER,
    km_per_year_estimate INTEGER,
    confidence VARCHAR(10) NOT NULL CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    last_known_km INTEGER,
    last_known_date DATE,
    measurement_count INTEGER DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reparatur-Scores pro Fahrzeug und Kategorie
CREATE TABLE IF NOT EXISTS vehicle_repair_scores (
    id SERIAL PRIMARY KEY,
    vehicle_number INTEGER NOT NULL,
    category_id VARCHAR(50) NOT NULL REFERENCES repair_categories(category_id) ON DELETE CASCADE,
    subsidiary INTEGER,
    last_service_date DATE,
    last_service_km INTEGER,
    estimated_current_km INTEGER,
    km_since_service INTEGER,
    years_since_service REAL,
    score_km REAL,
    score_years REAL,
    score_combined REAL,
    priority VARCHAR(10) NOT NULL CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    recommended_action VARCHAR(200),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(vehicle_number, category_id)
);

CREATE INDEX IF NOT EXISTS idx_vehicle_repair_scores_vehicle ON vehicle_repair_scores(vehicle_number);
CREATE INDEX IF NOT EXISTS idx_vehicle_repair_scores_category ON vehicle_repair_scores(category_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_repair_scores_subsidiary ON vehicle_repair_scores(subsidiary);
CREATE INDEX IF NOT EXISTS idx_vehicle_repair_scores_priority ON vehicle_repair_scores(priority);

COMMENT ON TABLE vehicle_km_estimates IS 'Geschätzter km-Stand pro Fahrzeug (Locosoft vehicle_number = internal_number); Quelle: orders.order_mileage';
COMMENT ON TABLE vehicle_repair_scores IS 'Verschleiß-Score pro Fahrzeug und Reparaturkategorie für Call-Agent / Catch-Export';
