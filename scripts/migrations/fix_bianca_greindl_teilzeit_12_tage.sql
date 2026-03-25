-- Bianca Greindl: Teilzeit → 12 Tage Gesamtanspruch (nicht 27 Vollzeit)
-- Ausführung: PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f scripts/migrations/fix_bianca_greindl_teilzeit_12_tage.sql

-- employee_id 18 = Bianca Greindl (Callcenter)
-- 2026: aktuell total_days=27, carried_over=14 → Anspruch 41; Korrektur auf 12 Tage
UPDATE vacation_entitlements
SET total_days = 12, carried_over = 0, updated_at = CURRENT_TIMESTAMP
WHERE employee_id = 18 AND year = 2026;

-- Optional: 2025 und 2027 ebenfalls auf 12 (falls bereits Einträge existieren)
UPDATE vacation_entitlements
SET total_days = 12, updated_at = CURRENT_TIMESTAMP
WHERE employee_id = 18 AND year = 2025;

UPDATE vacation_entitlements
SET total_days = 12, updated_at = CURRENT_TIMESTAMP
WHERE employee_id = 18 AND year = 2027;
