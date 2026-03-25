-- P1-Zuordnung konfigurierbar machen (statt hardcoded II_testwagen)
-- NULL = keine Sonderbehandlung, sonst Zielkategorie für memo='P1' aus I_neuwagen.

BEGIN;

ALTER TABLE provision_config
  ADD COLUMN IF NOT EXISTS memo_p1_kategorie VARCHAR(40);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'chk_provision_memo_p1_kategorie'
  ) THEN
    ALTER TABLE provision_config
      ADD CONSTRAINT chk_provision_memo_p1_kategorie
      CHECK (memo_p1_kategorie IS NULL OR memo_p1_kategorie IN ('II_testwagen', 'III_gebrauchtwagen'));
  END IF;
END $$;

COMMENT ON COLUMN provision_config.memo_p1_kategorie IS
'Optionale Zuordnung für memo=P1 aus I_neuwagen: II_testwagen oder III_gebrauchtwagen. NULL = keine Sonderbehandlung.';

COMMIT;
