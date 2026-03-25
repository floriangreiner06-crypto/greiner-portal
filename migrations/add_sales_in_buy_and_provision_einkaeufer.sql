-- Ankaufender VK-Berater (Einkäufer) für Provision/Gw aus Bestand
-- sales.in_buy_salesman_number = Locosoft dealer_vehicles.in_buy_salesman_number
-- provision_positionen.einkaeufer_name = Anzeigename (aus employees oder "VKB <nr>")

-- 1. sales: Ankaufender VKB (wer hat das Fahrzeug angetauscht/zugekauft)
ALTER TABLE sales ADD COLUMN IF NOT EXISTS in_buy_salesman_number INTEGER;

-- 2. provision_positionen: Einkäufer-Name pro Position (für Kontrolle/Gw aus Bestand)
ALTER TABLE provision_positionen ADD COLUMN IF NOT EXISTS einkaeufer_name TEXT;

COMMENT ON COLUMN sales.in_buy_salesman_number IS 'Locosoft: Ankaufender VK-Berater (Einkäufer), aus dealer_vehicles.in_buy_salesman_number';
COMMENT ON COLUMN provision_positionen.einkaeufer_name IS 'Anzeigename des Ankaufenden VKB (Einkäufer), für Gw aus Bestand-Kontrolle';
