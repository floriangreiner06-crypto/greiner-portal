-- Provisionsdeckel 300 € auch für I. Neuwagen (rg_netto 1%).
-- Ohne max_betrag wurde z.B. IONIQ 5 N mit 52.352 € × 1% = 523 € nicht gedeckelt.
-- Nach diesem Update wird calc_rg_netto_clamp(netto, cfg_i) auch für Kat. I den Deckel anwenden.

UPDATE provision_config
SET max_betrag = 300
WHERE kategorie = 'I_neuwagen'
  AND (gueltig_bis IS NULL OR gueltig_bis >= '2024-01-01')
  AND (bemessungsgrundlage IS NULL OR LOWER(TRIM(bemessungsgrundlage)) = 'rg_netto');
