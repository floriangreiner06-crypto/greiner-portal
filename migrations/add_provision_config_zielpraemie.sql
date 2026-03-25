-- Migration: provision_config um Zielprämie (NW) erweitern
-- Stückprämie bei I_neuwagen = Zielprämie: Ziel aus Verkäufer-Zielplanung,
-- Prämie bei Zielerreichung (€) + Übererfüllung (€/Stück).

BEGIN;

ALTER TABLE provision_config
  ADD COLUMN IF NOT EXISTS use_zielpraemie BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS zielerreichung_betrag REAL;

COMMENT ON COLUMN provision_config.use_zielpraemie IS 'Bei true: NW-Prämie = Zielprämie (Ziel aus Verkäufer-Zielplanung, Zielerreichung + Übererfüllung)';
COMMENT ON COLUMN provision_config.zielerreichung_betrag IS 'Prämie in € bei Erreichen des Monatsziels (Zielerreichung). stueck_praemie = Übererfüllung €/Stück.';

-- I_neuwagen auf Zielprämie umstellen (100 € Zielerreichung, 50 € pro Übererfüllung)
UPDATE provision_config
SET use_zielpraemie = true,
    zielerreichung_betrag = 100.0,
    stueck_praemie = 50.0,
    stueck_max = NULL
WHERE kategorie = 'I_neuwagen'
  AND gueltig_ab = '2024-01-01';

COMMIT;
