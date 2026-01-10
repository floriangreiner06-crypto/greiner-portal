-- ============================================================================
-- Finanzreporting Cube - Materialized Views
-- ============================================================================
-- Erstellt: TAG 178 (2026-01-10)
-- Zweck: Vorgeaggregierte Daten für schnelle BWA-Analysen
-- 
-- Architektur:
-- 1. Dimensionstabellen (dim_zeit, dim_standort, dim_kostenstelle, dim_konto)
-- 2. Fact-Table (fact_bwa)
-- 3. Indizes für Performance
-- ============================================================================

-- ============================================================================
-- PHASE 1: DIMENSIONSTABELLEN
-- ============================================================================

-- ----------------------------------------------------------------------------
-- dim_zeit: Zeit-Dimension (Jahr, Monat, Tag)
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS dim_zeit CASCADE;

CREATE MATERIALIZED VIEW dim_zeit AS
SELECT DISTINCT
    accounting_date as datum,
    EXTRACT(YEAR FROM accounting_date)::INTEGER as jahr,
    EXTRACT(MONTH FROM accounting_date)::INTEGER as monat,
    EXTRACT(DAY FROM accounting_date)::INTEGER as tag,
    EXTRACT(QUARTER FROM accounting_date)::INTEGER as quartal,
    EXTRACT(WEEK FROM accounting_date)::INTEGER as woche,
    EXTRACT(DOW FROM accounting_date)::INTEGER as wochentag, -- 0=Sonntag, 6=Samstag
    TO_CHAR(accounting_date, 'YYYY-MM') as jahr_monat,
    TO_CHAR(accounting_date, 'YYYY-Q') as jahr_quartal,
    TO_CHAR(accounting_date, 'YYYY') as jahr_text,
    TO_CHAR(accounting_date, 'Month') as monat_name,
    TO_CHAR(accounting_date, 'Day') as wochentag_name
FROM loco_journal_accountings
WHERE accounting_date IS NOT NULL
ORDER BY accounting_date;

-- Indizes für dim_zeit
CREATE UNIQUE INDEX idx_dim_zeit_datum ON dim_zeit (datum);
CREATE INDEX idx_dim_zeit_jahr_monat ON dim_zeit (jahr, monat);
CREATE INDEX idx_dim_zeit_jahr_quartal ON dim_zeit (jahr, quartal);

-- ----------------------------------------------------------------------------
-- dim_standort: Standort-Dimension
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS dim_standort CASCADE;

CREATE MATERIALIZED VIEW dim_standort AS
SELECT DISTINCT
    subsidiary_to_company_ref as standort_id,
    CASE subsidiary_to_company_ref
        WHEN 1 THEN 'DEG'  -- Deggendorf Opel
        WHEN 2 THEN 'HYU'  -- Deggendorf Hyundai
        WHEN 3 THEN 'LAN'  -- Landau
        ELSE 'UNKNOWN'
    END as standort_code,
    CASE subsidiary_to_company_ref
        WHEN 1 THEN 'Deggendorf Opel'
        WHEN 2 THEN 'Deggendorf Hyundai'
        WHEN 3 THEN 'Landau'
        ELSE 'Unbekannt'
    END as standort_name
FROM loco_journal_accountings
WHERE subsidiary_to_company_ref IS NOT NULL
ORDER BY subsidiary_to_company_ref;

-- Indizes für dim_standort
CREATE UNIQUE INDEX idx_dim_standort_id ON dim_standort (standort_id);

-- ----------------------------------------------------------------------------
-- dim_kostenstelle: Kostenstellen-Dimension
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS dim_kostenstelle CASCADE;

CREATE MATERIALIZED VIEW dim_kostenstelle AS
SELECT DISTINCT
    -- KST-ID: skr51_cost_center oder Fallback auf 5. Stelle
    COALESCE(
        NULLIF(skr51_cost_center, 0),
        CAST(substr(CAST(nominal_account_number AS TEXT), 5, 1) AS INTEGER)
    ) as kst_id,
    skr51_cost_center as skr51_cost_center_original,
    CAST(substr(CAST(nominal_account_number AS TEXT), 5, 1) AS INTEGER) as kst_5_stelle,
    -- KST-Name aus accounts_characteristics (falls vorhanden)
    NULL::TEXT as kst_name  -- Wird später über JOIN ergänzt
FROM loco_journal_accountings
WHERE nominal_account_number BETWEEN 400000 AND 499999
  AND (
    skr51_cost_center IS NOT NULL 
    OR substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('0','1','2','3','4','5','6','7','8','9')
  )
ORDER BY kst_id;

-- Indizes für dim_kostenstelle
CREATE UNIQUE INDEX idx_dim_kostenstelle_id ON dim_kostenstelle (kst_id);

-- ----------------------------------------------------------------------------
-- dim_konto: Konten-Dimension (mit Hierarchie)
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS dim_konto CASCADE;

CREATE MATERIALIZED VIEW dim_konto AS
SELECT DISTINCT
    nominal_account_number as konto_id,
    -- Hierarchie-Ebenen (6-stellige Kontonummer)
    CASE 
        WHEN LENGTH(CAST(nominal_account_number AS TEXT)) >= 1 
        THEN CAST(substr(CAST(nominal_account_number AS TEXT), 1, 1) AS INTEGER)
        ELSE NULL
    END as ebene1,  -- 1. Stelle (z.B. 4 = Kosten)
    CASE 
        WHEN LENGTH(CAST(nominal_account_number AS TEXT)) >= 2 
        THEN CAST(substr(CAST(nominal_account_number AS TEXT), 1, 2) AS INTEGER)
        ELSE NULL
    END as ebene2,  -- 1-2. Stelle (z.B. 40 = Kosten)
    CASE 
        WHEN LENGTH(CAST(nominal_account_number AS TEXT)) >= 3 
        THEN CAST(substr(CAST(nominal_account_number AS TEXT), 1, 3) AS INTEGER)
        ELSE NULL
    END as ebene3,  -- 1-3. Stelle (z.B. 400 = Kosten)
    CASE 
        WHEN LENGTH(CAST(nominal_account_number AS TEXT)) >= 4 
        THEN CAST(substr(CAST(nominal_account_number AS TEXT), 1, 4) AS INTEGER)
        ELSE NULL
    END as ebene4,  -- 1-4. Stelle (z.B. 4000 = Kosten)
    CASE 
        WHEN LENGTH(CAST(nominal_account_number AS TEXT)) >= 5 
        THEN CAST(substr(CAST(nominal_account_number AS TEXT), 1, 5) AS INTEGER)
        ELSE NULL
    END as ebene5,  -- 1-5. Stelle (z.B. 40000 = Kosten)
    CASE 
        WHEN LENGTH(CAST(nominal_account_number AS TEXT)) >= 5 
        THEN CAST(substr(CAST(nominal_account_number AS TEXT), 5, 1) AS INTEGER)
        ELSE NULL
    END as kst_stelle,  -- 5. Stelle (KST)
    -- Konto-Name (wird später über JOIN mit nominal_accounts ergänzt)
    NULL::TEXT as konto_name,
    -- Konto-Typ
    CASE 
        WHEN nominal_account_number BETWEEN 400000 AND 499999 THEN 'Kosten'
        WHEN nominal_account_number BETWEEN 700000 AND 799999 THEN 'Einsatz'
        WHEN nominal_account_number BETWEEN 800000 AND 899999 THEN 'Umsatz'
        ELSE 'Sonstiges'
    END as konto_typ
FROM loco_journal_accountings
WHERE nominal_account_number IS NOT NULL
ORDER BY nominal_account_number;

-- Indizes für dim_konto
CREATE UNIQUE INDEX idx_dim_konto_id ON dim_konto (konto_id);
CREATE INDEX idx_dim_konto_ebene3 ON dim_konto (ebene3);
CREATE INDEX idx_dim_konto_ebene4 ON dim_konto (ebene4);
CREATE INDEX idx_dim_konto_typ ON dim_konto (konto_typ);

-- ============================================================================
-- PHASE 2: FACT-TABLE
-- ============================================================================

-- ----------------------------------------------------------------------------
-- fact_bwa: Fact-Table für BWA-Daten
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS fact_bwa CASCADE;

CREATE MATERIALIZED VIEW fact_bwa AS
SELECT
    -- Dimensionen
    lja.accounting_date as zeit_id,
    lja.subsidiary_to_company_ref as standort_id,
    CASE 
        WHEN lja.skr51_cost_center IS NOT NULL AND lja.skr51_cost_center != 0 
        THEN lja.skr51_cost_center
        WHEN LENGTH(CAST(lja.nominal_account_number AS TEXT)) >= 5 
        THEN CAST(substr(CAST(lja.nominal_account_number AS TEXT), 5, 1) AS INTEGER)
        ELSE NULL
    END as kst_id,
    lja.nominal_account_number as konto_id,
    
    -- Measures
    CASE 
        WHEN lja.debit_or_credit = 'S' THEN lja.posted_value 
        ELSE -lja.posted_value 
    END / 100.0 as betrag,
    
    CASE 
        WHEN lja.debit_or_credit = 'S' THEN lja.posted_count 
        ELSE -lja.posted_count 
    END / 100.0 as menge,
    
    -- Metadaten
    lja.debit_or_credit,
    lja.posting_text,
    lja.document_number,
    lja.skr51_branch,
    lja.skr51_make,
    lja.skr51_cost_center as skr51_cost_center_original,
    lja.skr51_sales_channel,
    lja.skr51_cost_unit
    
FROM loco_journal_accountings lja
WHERE lja.accounting_date IS NOT NULL
  AND lja.nominal_account_number IS NOT NULL
  AND (lja.posting_text IS NULL OR lja.posting_text NOT LIKE '%G&V-Abschluss%')
ORDER BY lja.accounting_date, lja.nominal_account_number;

-- Indizes für fact_bwa
CREATE INDEX idx_fact_bwa_zeit ON fact_bwa (zeit_id);
CREATE INDEX idx_fact_bwa_standort ON fact_bwa (standort_id);
CREATE INDEX idx_fact_bwa_kst ON fact_bwa (kst_id);
CREATE INDEX idx_fact_bwa_konto ON fact_bwa (konto_id);
CREATE INDEX idx_fact_bwa_zeit_standort ON fact_bwa (zeit_id, standort_id);
CREATE INDEX idx_fact_bwa_zeit_kst ON fact_bwa (zeit_id, kst_id);
CREATE INDEX idx_fact_bwa_zeit_konto ON fact_bwa (zeit_id, konto_id);

-- ============================================================================
-- REFRESH-FUNKTIONEN
-- ============================================================================

-- Funktion zum Aktualisieren aller Materialized Views
CREATE OR REPLACE FUNCTION refresh_finanzreporting_cube()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dim_zeit;
    REFRESH MATERIALIZED VIEW CONCURRENTLY dim_standort;
    REFRESH MATERIALIZED VIEW CONCURRENTLY dim_kostenstelle;
    REFRESH MATERIALIZED VIEW CONCURRENTLY dim_konto;
    REFRESH MATERIALIZED VIEW CONCURRENTLY fact_bwa;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- KOMMENTARE
-- ============================================================================

COMMENT ON MATERIALIZED VIEW dim_zeit IS 'Zeit-Dimension für Finanzreporting Cube';
COMMENT ON MATERIALIZED VIEW dim_standort IS 'Standort-Dimension für Finanzreporting Cube';
COMMENT ON MATERIALIZED VIEW dim_kostenstelle IS 'Kostenstellen-Dimension für Finanzreporting Cube';
COMMENT ON MATERIALIZED VIEW dim_konto IS 'Konten-Dimension für Finanzreporting Cube';
COMMENT ON MATERIALIZED VIEW fact_bwa IS 'Fact-Table für BWA-Daten (vorgeaggregiert)';
COMMENT ON FUNCTION refresh_finanzreporting_cube() IS 'Aktualisiert alle Materialized Views des Finanzreporting Cubes';
