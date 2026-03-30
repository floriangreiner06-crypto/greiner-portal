-- migrations/add_provision_config_use_kumuliert.sql
-- Kumulierte Zielprämie: Gate ist kumuliertes Monatsziel (Jan bis aktueller Monat)
ALTER TABLE provision_config ADD COLUMN IF NOT EXISTS use_kumuliert BOOLEAN DEFAULT false;

-- Aktivierung für bestehende Zielerfüllung-Zeile (I_neuwagen)
UPDATE provision_config
SET use_kumuliert = true
WHERE kategorie = 'I_neuwagen'
  AND use_zielpraemie = true;
