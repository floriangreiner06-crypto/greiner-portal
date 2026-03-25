-- Zielprämie-Basis für NW konfigurieren:
-- auslieferung (Rechnungsdatum) oder auftragseingang (Vertragsdatum)

BEGIN;

ALTER TABLE provision_config
  ADD COLUMN IF NOT EXISTS zielpraemie_basis VARCHAR(30) DEFAULT 'auslieferung';

UPDATE provision_config
SET zielpraemie_basis = 'auslieferung'
WHERE zielpraemie_basis IS NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'chk_provision_zielpraemie_basis'
  ) THEN
    ALTER TABLE provision_config
      ADD CONSTRAINT chk_provision_zielpraemie_basis
      CHECK (zielpraemie_basis IN ('auslieferung', 'auftragseingang'));
  END IF;
END $$;

COMMENT ON COLUMN provision_config.zielpraemie_basis IS
'Basis für NW-Zielprämie: auslieferung (Rechnungsdatum) oder auftragseingang (Vertragsdatum).';

COMMIT;
