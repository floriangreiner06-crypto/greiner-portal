-- Provisionsabrechnung: J60/J61 für DB2 (GW aus Bestand) aus Excel Optionen übernehmen
-- Quelle: Provisionsabrechnung_V0.11.xlsm, Blatt Optionen J60=0,01, J61=175
-- Siehe PROVISION_ABGLEICH_PDF_EXCEL_STELLUNGNAHME.md

UPDATE provision_config
SET param_j60 = 0.01, param_j61 = 175
WHERE kategorie = 'IV_gw_bestand'
  AND gueltig_ab <= CURRENT_DATE
  AND (gueltig_bis IS NULL OR gueltig_bis >= CURRENT_DATE);
