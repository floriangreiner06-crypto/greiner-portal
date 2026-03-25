-- Fallback-Ziel für Zielprämie (Test ohne Zielplanung/Freigabe)
-- Wenn gesetzt und Zielplanung liefert 0: dieses Ziel als Monatsziel verwenden.

BEGIN;

ALTER TABLE provision_config
  ADD COLUMN IF NOT EXISTS zielpraemie_fallback_ziel INTEGER;

COMMENT ON COLUMN provision_config.zielpraemie_fallback_ziel IS 'Optional: Ziel (Stück) für Zielprämie, wenn Verkäufer-Zielplanung 0 liefert (z.B. 1 zum Testen ohne Freigabe).';

COMMIT;
