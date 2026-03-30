-- Migration: Ertragsvorschau-Modul (Umsatz- und Ertragsvorschau)
-- Erstellt: 2026-03-30 | Workstream: Controlling
-- Tabellen: fibu_guv_monatswerte, jahresabschluss_daten, ertragsvorschau_snapshots
-- Navigation: Ertragsvorschau unter Controlling
-- Feature: ertragsvorschau (geschaeftsleitung, admin)

-- ============================================================================
-- 1. FIBU GuV Monatswerte (täglicher Sync aus Locosoft)
-- ============================================================================
CREATE TABLE IF NOT EXISTS fibu_guv_monatswerte (
    id SERIAL PRIMARY KEY,
    geschaeftsjahr VARCHAR(10) NOT NULL,
    monat INT NOT NULL,
    bereich VARCHAR(50) NOT NULL,
    betrag_cent BIGINT NOT NULL DEFAULT 0,
    synced_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(geschaeftsjahr, monat, bereich)
);

CREATE INDEX IF NOT EXISTS idx_fibu_guv_gj ON fibu_guv_monatswerte(geschaeftsjahr);
CREATE INDEX IF NOT EXISTS idx_fibu_guv_gj_monat ON fibu_guv_monatswerte(geschaeftsjahr, monat);

-- ============================================================================
-- 2. Jahresabschluss-Daten (aus Steuerberater-PDF importiert)
-- ============================================================================
CREATE TABLE IF NOT EXISTS jahresabschluss_daten (
    id SERIAL PRIMARY KEY,
    geschaeftsjahr VARCHAR(10) NOT NULL UNIQUE,
    stichtag DATE NOT NULL,
    bilanzsumme NUMERIC(12,1),
    anlagevermoegen NUMERIC(12,1),
    umlaufvermoegen NUMERIC(12,1),
    eigenkapital NUMERIC(12,1),
    ek_quote NUMERIC(5,1),
    rueckstellungen NUMERIC(12,1),
    verbindlichkeiten NUMERIC(12,1),
    umsatz NUMERIC(12,1),
    rohertrag_pct NUMERIC(5,1),
    personalaufwand NUMERIC(12,1),
    abschreibungen NUMERIC(12,1),
    investitionen NUMERIC(12,1),
    zinsergebnis NUMERIC(12,1),
    betriebsergebnis NUMERIC(12,1),
    finanzergebnis NUMERIC(12,1),
    neutrales_ergebnis NUMERIC(12,1),
    jahresergebnis NUMERIC(12,1),
    cashflow_geschaeft NUMERIC(12,1),
    cashflow_invest NUMERIC(12,1),
    cashflow_finanz NUMERIC(12,1),
    finanzmittel_jahresende NUMERIC(12,1),
    quelldatei TEXT,
    importiert_am TIMESTAMP DEFAULT NOW(),
    importiert_von TEXT
);

-- ============================================================================
-- 3. Ertragsvorschau Snapshots (monatliche Sicherung)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ertragsvorschau_snapshots (
    id SERIAL PRIMARY KEY,
    stichtag DATE NOT NULL,
    geschaeftsjahr VARCHAR(10) NOT NULL,
    daten_json JSONB NOT NULL,
    erstellt_am TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ev_snapshots_gj ON ertragsvorschau_snapshots(geschaeftsjahr);

-- ============================================================================
-- 4. Feature-Zugriff
-- ============================================================================
INSERT INTO feature_access (feature_name, role_name)
SELECT 'ertragsvorschau', r.role_name
FROM (VALUES ('admin'), ('geschaeftsleitung')) AS r(role_name)
WHERE NOT EXISTS (
    SELECT 1 FROM feature_access fa
    WHERE fa.feature_name = 'ertragsvorschau' AND fa.role_name = r.role_name
);

-- ============================================================================
-- 5. Navigation: Ertragsvorschau unter Controlling
-- ============================================================================
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT c.id, 'Ertragsvorschau', '/controlling/ertragsvorschau', 'bi-graph-up-arrow', 25, 'ertragsvorschau', 'dropdown', true
FROM navigation_items c
WHERE c.label = 'Controlling' AND c.parent_id IS NULL
AND NOT EXISTS (SELECT 1 FROM navigation_items n WHERE n.parent_id = c.id AND n.label = 'Ertragsvorschau')
LIMIT 1;
