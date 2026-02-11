-- Migration: Whitelist Versicherungskunden für M1 Unfall-Rechnungsprüfung
-- Tabelle: unfall_versicherung_kunden (Mapping Locosoft-Kunden → Versicherung)
-- Datum: 2026-02-11

BEGIN;

CREATE TABLE IF NOT EXISTS unfall_versicherung_kunden (
    id SERIAL PRIMARY KEY,
    customer_number INTEGER NOT NULL,
    subsidiary INTEGER NOT NULL,
    versicherung_name VARCHAR(200) NOT NULL,
    ist_aktiv BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_number, subsidiary)
);

CREATE INDEX IF NOT EXISTS idx_unfall_vers_kunden_cust_sub ON unfall_versicherung_kunden(customer_number, subsidiary);
CREATE INDEX IF NOT EXISTS idx_unfall_vers_kunden_aktiv ON unfall_versicherung_kunden(ist_aktiv);

COMMENT ON TABLE unfall_versicherung_kunden IS 'Whitelist: Locosoft-Kunden die Versicherungen sind (für M1 Versicherungsaufträge)';

COMMIT;
