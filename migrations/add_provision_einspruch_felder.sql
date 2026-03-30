-- Einspruch/Ablehnung-Felder fuer Provision-Workflow
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_text TEXT;
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_von TEXT;
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_am TIMESTAMP;
