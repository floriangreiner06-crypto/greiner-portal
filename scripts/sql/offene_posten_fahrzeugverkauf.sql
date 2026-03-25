-- Offene Posten (OPOS) – wie Locosoft L362PR „Unausgeglichene Personenkonten“
-- Datenquelle: loco_journal_accountings (nur Forderungen: 140001, 150000-159999, 170000-199999; Kreditoren 160000-169999 ausgeschlossen), sales, employees, loco_customers_suppliers
-- posted_value in journal_accountings ist in CENT → / 100 für EUR
--
-- Zuordnung „Verkäufer/Ansprechpartner“:
--   • Fahrzeugverkauf: Verkäufer aus Ablieferung (sales) – Match Rechnungsnr+Datum oder Kunde+Datum.
--     (Bei Fz-Verkauf schreibt nicht der Verkäufer die Rechnung; die Info steht nur in der Verkaufs-Rechnung.)
--   • Sonstige Rechnungen (Werkstatt, Teile, …): „Mitarbeiter“ = Rechnungsersteller aus FIBU (employee_number).

WITH offene AS (
  SELECT
    j.customer_number,
    NULLIF(TRIM(j.invoice_number), '') AS invoice_number,
    j.invoice_date,
    SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 AS saldo_eur,
    MAX(j.employee_number) AS rechnungsersteller_nr
  FROM loco_journal_accountings j
  WHERE j.nominal_account_number BETWEEN 140000 AND 199999
    AND (j.nominal_account_number < 160000 OR j.nominal_account_number >= 170000)
    AND j.invoice_number IS NOT NULL
    AND TRIM(j.invoice_number) <> ''
    AND j.invoice_date IS NOT NULL
  GROUP BY j.customer_number, j.invoice_number, j.invoice_date
  HAVING SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) > 0
),
-- Fahrzeugverkauf: Verkäufer aus sales (ein Treffer pro offene Position)
sales_treffer AS (
  SELECT DISTINCT ON (o.customer_number, o.invoice_number, o.invoice_date)
    o.customer_number,
    o.invoice_number,
    o.invoice_date,
    o.saldo_eur,
    o.rechnungsersteller_nr,
    s.salesman_number AS verkaeufer_fahrzeugverkauf
  FROM offene o
  LEFT JOIN sales s
    ON s.out_invoice_date = o.invoice_date
   AND (s.out_invoice_number::text = o.invoice_number
        OR s.buyer_customer_no::text = o.customer_number::text)
  ORDER BY o.customer_number, o.invoice_number, o.invoice_date,
           (s.out_invoice_number::text = o.invoice_number) DESC NULLS LAST,
           s.salesman_number NULLS LAST
),
-- Final: Bei Fahrzeugverkauf Verkäufer aus sales, sonst Rechnungsersteller aus FIBU
mit_verkaeufer AS (
  SELECT
    customer_number,
    invoice_number,
    invoice_date,
    saldo_eur,
    COALESCE(verkaeufer_fahrzeugverkauf, rechnungsersteller_nr) AS verkaufer_nr,
    (verkaeufer_fahrzeugverkauf IS NOT NULL) AS ist_fahrzeugverkauf
  FROM sales_treffer
)
SELECT
  COALESCE(e.first_name || ' ' || e.last_name, 'Nr. ' || mv.verkaufer_nr::text, 'Ohne Zuordnung') AS verkaeufer_oder_ersteller,
  mv.verkaufer_nr,
  mv.ist_fahrzeugverkauf,
  cs.kunde,
  mv.invoice_date AS rechnung_datum,
  mv.invoice_number AS rechnung_nr,
  ROUND(mv.saldo_eur, 2) AS betrag_eur
FROM mit_verkaeufer mv
LEFT JOIN employees e ON e.locosoft_id = mv.verkaufer_nr
LEFT JOIN (
  SELECT customer_number,
         COALESCE(NULLIF(TRIM(MAX(COALESCE(family_name, '') || ', ' || COALESCE(first_name, ''))), ''), 'Kunde ' || customer_number) AS kunde
  FROM loco_customers_suppliers
  GROUP BY customer_number
) cs ON cs.customer_number = mv.customer_number
ORDER BY verkaeufer_oder_ersteller NULLS LAST, rechnung_datum, mv.customer_number;
