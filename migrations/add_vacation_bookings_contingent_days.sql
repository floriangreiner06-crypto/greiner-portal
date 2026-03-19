-- Teilzeit: Nicht-Arbeitstage sollen bei Urlaubsantrag nicht abgezogen werden (wie Wochenende).
-- contingent_days: 0 = Tag zählt nicht (Wochenende/Nicht-Arbeitstag), 1.0/0.5 = zählt zum Urlaubskonto.
-- Bestehende Buchungen (contingent_days NULL) werden wie bisher aus day_part berechnet.
ALTER TABLE vacation_bookings
    ADD COLUMN IF NOT EXISTS contingent_days NUMERIC DEFAULT NULL;

COMMENT ON COLUMN vacation_bookings.contingent_days IS 'Urlaubstage für diese Buchung (0 = nicht abziehen, 1.0/0.5 = abziehen). NULL = wie day_part.';
