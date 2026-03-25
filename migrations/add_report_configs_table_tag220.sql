-- TAG 220: Report-spezifische Konfigurationen (z. B. Alarm-Parameter)
CREATE TABLE IF NOT EXISTS report_configs (
    report_type TEXT PRIMARY KEY,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_report_configs_updated_at
    ON report_configs(updated_at DESC);
