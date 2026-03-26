-- Erstzulassung in sales für Regel "T = NW nur im ersten Jahr ab Ez"
-- Verkaufsleitung: T (Tageszulassung) bis 1 Jahr ab Erstzulassung = NW, älter = GW
ALTER TABLE sales ADD COLUMN IF NOT EXISTS first_registration_date DATE;
COMMENT ON COLUMN sales.first_registration_date IS 'Erstzulassung (Locosoft vehicles); für T: NW wenn (Vertragsdatum - Ez) <= 1 Jahr, sonst GW';
