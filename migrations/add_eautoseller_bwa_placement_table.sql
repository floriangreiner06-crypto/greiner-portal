-- eAutoSeller BWA-Platzierung cachen (mobile.de Platz, Treffer, Platz 1)
-- Celery-Task füllt die Tabelle; Verkaufsempfehlungen AfA lesen von hier (kein Live-API-Call im Request).
-- Ausführung: PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_eautoseller_bwa_placement_table.sql

CREATE TABLE IF NOT EXISTS eautoseller_bwa_placement (
    vin VARCHAR(17) PRIMARY KEY,
    mobile_platz INTEGER,
    total_hits INTEGER,
    platz_1_retail_gross NUMERIC(12,2),
    mobile_url TEXT,
    error_message TEXT,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE eautoseller_bwa_placement IS 'Gecachte eAutoSeller BWA-Bewerter-Daten (mobile.de Platz, Treffer, Platz 1); wird von Celery-Task aktualisiert.';

CREATE INDEX IF NOT EXISTS idx_eautoseller_bwa_placement_fetched_at ON eautoseller_bwa_placement(fetched_at);
