-- Kategorisierung: Nur Zeilen, die der User per "Speichern" gesetzt hat, als "vom User gespeichert" markieren (grüne Hervorhebung).
-- kategorie_manuell = true nur bei PATCH (Speichern-Button), false bei Regeln anwenden / Regeln erneut anwenden.

ALTER TABLE transaktionen
ADD COLUMN IF NOT EXISTS kategorie_manuell BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN transaktionen.kategorie_manuell IS 'true = Kategorie vom User per Speichern gesetzt (grüne Markierung in Kategorisierung-UI)';
