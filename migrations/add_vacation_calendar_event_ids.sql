-- Migration: Graph-Kalender-Event-IDs für Urlaubsbuchungen
-- Zweck: Bei Genehmigung werden Einträge in drive@ und im Mitarbeiter-Kalender erstellt.
--        Die Event-IDs werden gespeichert, damit bei Storno beide Einträge gelöscht werden können.
-- Datum: 2026-02

BEGIN;

ALTER TABLE vacation_bookings ADD COLUMN IF NOT EXISTS calendar_event_id_employee TEXT;
ALTER TABLE vacation_bookings ADD COLUMN IF NOT EXISTS calendar_event_id_drive TEXT;

COMMIT;
