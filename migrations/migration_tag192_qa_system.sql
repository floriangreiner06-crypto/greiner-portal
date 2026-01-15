-- Migration TAG 192: QA & Bug-Reporting-System (MVP)
-- Erstellt: 2026-01-14
-- Zweck: Tägliche Feature-Prüfung und Fehlermeldung durch Mitarbeiter

BEGIN;

-- =============================================================================
-- 1. FEATURE QA CHECKS (Tägliche Feature-Prüfungen)
-- =============================================================================

CREATE TABLE IF NOT EXISTS feature_qa_checks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    check_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('passed', 'failed', 'warning', 'not_checked')),
    notes TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, feature_name, check_date)
);

CREATE INDEX IF NOT EXISTS idx_qa_checks_user_date ON feature_qa_checks(user_id, check_date DESC);
CREATE INDEX IF NOT EXISTS idx_qa_checks_feature ON feature_qa_checks(feature_name);
CREATE INDEX IF NOT EXISTS idx_qa_checks_status ON feature_qa_checks(status);

COMMENT ON TABLE feature_qa_checks IS 'Tägliche Feature-Prüfungen pro Mitarbeiter (TAG 192)';
COMMENT ON COLUMN feature_qa_checks.status IS 'passed=Bestanden, failed=Fehler, warning=Warnung, not_checked=Nicht geprüft';

-- =============================================================================
-- 2. BUG REPORTS (Fehlermeldungen)
-- =============================================================================

CREATE TABLE IF NOT EXISTS bug_reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    feature_name VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    steps_to_reproduce TEXT,
    expected_behavior TEXT,
    actual_behavior TEXT,
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'analyzing', 'in_progress', 'fixed', 'closed', 'duplicate')),
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),  -- 1=highest, 5=lowest
    screenshot_urls TEXT[],  -- Array von URLs zu Screenshots
    browser_info TEXT,  -- JSON: {browser, version, os}
    url TEXT,  -- URL wo Bug auftrat
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_bug_reports_status ON bug_reports(status);
CREATE INDEX IF NOT EXISTS idx_bug_reports_feature ON bug_reports(feature_name);
CREATE INDEX IF NOT EXISTS idx_bug_reports_reporter ON bug_reports(reporter_id);
CREATE INDEX IF NOT EXISTS idx_bug_reports_created ON bug_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bug_reports_severity ON bug_reports(severity);

COMMENT ON TABLE bug_reports IS 'Fehlermeldungen mit vollständigem Kontext (TAG 192)';
COMMENT ON COLUMN bug_reports.severity IS 'low=kosmetisch, medium=beeinträchtigt Nutzung, high=Feature unbrauchbar, critical=System-Crash';
COMMENT ON COLUMN bug_reports.status IS 'open=Offen, analyzing=Claude analysiert, in_progress=In Bearbeitung, fixed=Behoben, closed=Geschlossen, duplicate=Duplikat';
COMMENT ON COLUMN bug_reports.priority IS '1=Höchste Priorität, 5=Niedrigste Priorität';

COMMIT;
