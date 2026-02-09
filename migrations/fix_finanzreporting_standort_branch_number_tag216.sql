-- ============================================================================
-- Finanzreporting Cube: Standort = branch_number (3 Standorte inkl. Landau)
-- ============================================================================
-- TAG 216 (2026-02-09)
-- Problem: fact_bwa nutzte subsidiary_to_company_ref als standort_id →
--          Landau (branch_number=3) wurde mit Deggendorf Opel (subsidiary=1) zu 1 zusammengefasst.
-- Lösung: standort_id = branch_number (1=DEG, 2=HYU, 3=Landau) gemäß SSOT
--          (docs/STANDORT_LOGIK_SSOT.md, api/standort_utils.py)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- dim_standort: Standort = branch_number (physischer Ort)
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS fact_bwa CASCADE;
DROP MATERIALIZED VIEW IF EXISTS dim_standort CASCADE;

CREATE MATERIALIZED VIEW dim_standort AS
SELECT DISTINCT
    branch_number as standort_id,
    CASE branch_number
        WHEN 1 THEN 'DEG'
        WHEN 2 THEN 'HYU'
        WHEN 3 THEN 'LAN'
        ELSE 'UNKNOWN'
    END as standort_code,
    CASE branch_number
        WHEN 1 THEN 'Deggendorf Opel'
        WHEN 2 THEN 'Deggendorf Hyundai'
        WHEN 3 THEN 'Landau'
        ELSE 'Unbekannt'
    END as standort_name
FROM loco_journal_accountings
WHERE branch_number IS NOT NULL
ORDER BY branch_number;

CREATE UNIQUE INDEX idx_dim_standort_id ON dim_standort (standort_id);

-- ----------------------------------------------------------------------------
-- fact_bwa: standort_id = branch_number (nicht subsidiary_to_company_ref)
-- ----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW fact_bwa AS
SELECT
    lja.accounting_date as zeit_id,
    lja.branch_number as standort_id,
    CASE 
        WHEN lja.skr51_cost_center IS NOT NULL AND lja.skr51_cost_center != 0 
        THEN lja.skr51_cost_center
        WHEN LENGTH(CAST(lja.nominal_account_number AS TEXT)) >= 5 
        THEN CAST(substr(CAST(lja.nominal_account_number AS TEXT), 5, 1) AS INTEGER)
        ELSE NULL
    END as kst_id,
    lja.nominal_account_number as konto_id,
    CASE 
        WHEN lja.debit_or_credit = 'S' THEN lja.posted_value 
        ELSE -lja.posted_value 
    END / 100.0 as betrag,
    CASE 
        WHEN lja.debit_or_credit = 'S' THEN lja.posted_count 
        ELSE -lja.posted_count 
    END / 100.0 as menge,
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

CREATE INDEX idx_fact_bwa_zeit ON fact_bwa (zeit_id);
CREATE INDEX idx_fact_bwa_standort ON fact_bwa (standort_id);
CREATE INDEX idx_fact_bwa_kst ON fact_bwa (kst_id);
CREATE INDEX idx_fact_bwa_konto ON fact_bwa (konto_id);
CREATE INDEX idx_fact_bwa_zeit_standort ON fact_bwa (zeit_id, standort_id);
CREATE INDEX idx_fact_bwa_zeit_kst ON fact_bwa (zeit_id, kst_id);
CREATE INDEX idx_fact_bwa_zeit_konto ON fact_bwa (zeit_id, konto_id);

COMMENT ON MATERIALIZED VIEW dim_standort IS 'Standort-Dimension: standort_id = branch_number (1=DEG, 2=HYU, 3=Landau)';
COMMENT ON MATERIALIZED VIEW fact_bwa IS 'Fact-Table BWA; standort_id = branch_number (TAG 216)';
