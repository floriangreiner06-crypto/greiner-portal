-- Arbeitstage Teilzeit: welche Wochentage (Mo–So) und ob halber Tag (2026-03)
-- work_weekdays: Kommagetrennt 0–6 (0=Mo, 6=So), z.B. '0,1,2,3,4' = Mo–Fr
-- half_weekdays: Kommagetrennt 0–6, an welchen Arbeitstagen nur halber Tag, z.B. '2,4' = Mi, Fr halber

ALTER TABLE employee_working_time_models
    ADD COLUMN IF NOT EXISTS work_weekdays TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS half_weekdays TEXT DEFAULT NULL;

COMMENT ON COLUMN employee_working_time_models.work_weekdays IS 'Kommagetrennt 0=Mo..6=So: an welchen Tagen gearbeitet wird (NULL = alle Werktage)';
COMMENT ON COLUMN employee_working_time_models.half_weekdays IS 'Kommagetrennt 0=Mo..6=So: an welchen Arbeitstagen nur halber Tag';
