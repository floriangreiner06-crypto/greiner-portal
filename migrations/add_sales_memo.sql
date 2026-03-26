-- Memo-Feld aus Locosoft dealer_vehicles (Pr. 132 Reiter Verkauf, Zeile Memo).
-- Wenn bei NW "P1" eingetragen wird: Provision wie VFW/TW (1% Rg.Netto), nicht NW (DB/Zielprämie).
-- Sync sync_sales.py muss dv.memo lesen und hier schreiben.

ALTER TABLE sales ADD COLUMN IF NOT EXISTS memo VARCHAR(50);

COMMENT ON COLUMN sales.memo IS 'Aus Locosoft dealer_vehicles.memo (Pr. 132 Verkauf/Memo). P1 = NW als VFW/TW abrechnen (1% Rg.Netto).';
