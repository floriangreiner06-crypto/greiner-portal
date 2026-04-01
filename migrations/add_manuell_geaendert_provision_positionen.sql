-- Migration: manuell_geaendert Flag auf provision_positionen
-- Zweck: Explizites Flag für manuell bearbeitete Positionen,
--         damit aktualisiere_vorlauf diese nicht überschreibt.
-- Setzt auch bestehende manuell geänderte Positionen (provision_final != provision_berechnet) auf true.

ALTER TABLE provision_positionen
    ADD COLUMN IF NOT EXISTS manuell_geaendert BOOLEAN NOT NULL DEFAULT false;

-- Bestehende manuell geänderte Positionen markieren
UPDATE provision_positionen
SET manuell_geaendert = true
WHERE provision_final IS NOT NULL
  AND provision_berechnet IS NOT NULL
  AND ROUND(provision_final::numeric, 2) != ROUND(provision_berechnet::numeric, 2);
