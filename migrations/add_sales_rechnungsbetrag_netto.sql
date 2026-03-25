-- Rechnungsbetrag netto aus Locosoft invoices.total_net (SSOT für Provisionsbasis Kat. II/III).
-- Bisher: netto_vk_preis = out_sale_price - mwst (kann von Rechnung abweichen).
-- Korrekte Abrechnung nutzt Rechnungsbetrag netto → 1% darauf; mit total_net stimmen Beträge (z.B. Friesl 284,53 €).

ALTER TABLE sales ADD COLUMN IF NOT EXISTS rechnungsbetrag_netto DOUBLE PRECISION;

COMMENT ON COLUMN sales.rechnungsbetrag_netto IS 'Aus Locosoft invoices.total_net; Basis für Provisionsberechnung (1% Rg.Netto) wenn vorhanden, sonst netto_vk_preis.';
