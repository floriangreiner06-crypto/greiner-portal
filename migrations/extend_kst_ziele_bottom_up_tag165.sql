-- ============================================================================
-- KST-ZIELE ERWEITERN (TAG 165)
-- ============================================================================
-- Erstellt: TAG 165
-- Zweck: Basis-Planung (Bottom-Up) + Aufhol-Beitrag (Top-Down) getrennt speichern
-- ============================================================================

-- Neue Spalten für Bottom-Up Planung
ALTER TABLE kst_ziele 
ADD COLUMN IF NOT EXISTS umsatz_basis NUMERIC(15,2),
ADD COLUMN IF NOT EXISTS db1_basis NUMERIC(15,2),
ADD COLUMN IF NOT EXISTS aufhol_umsatz NUMERIC(15,2),
ADD COLUMN IF NOT EXISTS aufhol_db1 NUMERIC(15,2),
ADD COLUMN IF NOT EXISTS planungs_quelle TEXT DEFAULT 'manual';

-- Kommentare
COMMENT ON COLUMN kst_ziele.umsatz_basis IS 'Basis-Umsatz-Ziel (Bottom-Up Planung)';
COMMENT ON COLUMN kst_ziele.db1_basis IS 'Basis-DB1-Ziel (Bottom-Up Planung)';
COMMENT ON COLUMN kst_ziele.aufhol_umsatz IS 'Aufhol-Beitrag Umsatz (Top-Down aus Gap-Analyse)';
COMMENT ON COLUMN kst_ziele.aufhol_db1 IS 'Aufhol-Beitrag DB1 (Top-Down aus Gap-Analyse)';
COMMENT ON COLUMN kst_ziele.planungs_quelle IS 'Quelle der Planung: bottom-up, top-down, manual, hybrid';

-- Logik: Gesamtziel = Basis + Aufhol
-- Aktualisiere bestehende Einträge: umsatz_ziel → umsatz_basis (als Basis ansehen)
UPDATE kst_ziele 
SET umsatz_basis = umsatz_ziel,
    db1_basis = db1_ziel,
    aufhol_umsatz = 0,
    aufhol_db1 = 0,
    planungs_quelle = 'manual'
WHERE umsatz_basis IS NULL 
  AND umsatz_ziel IS NOT NULL;

-- ============================================================================

