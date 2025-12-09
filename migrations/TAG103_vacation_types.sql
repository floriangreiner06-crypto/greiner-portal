-- ============================================================================
-- TAG 103: Erweiterte Abwesenheitsarten
-- ============================================================================

-- Prüfe vorhandene Typen
SELECT * FROM vacation_types;

-- Erweitere vacation_types mit needs_approval Flag
ALTER TABLE vacation_types ADD COLUMN IF NOT EXISTS needs_approval INTEGER DEFAULT 1;
ALTER TABLE vacation_types ADD COLUMN IF NOT EXISTS icon TEXT;
ALTER TABLE vacation_types ADD COLUMN IF NOT EXISTS loco_reason TEXT;

-- Aktualisiere/Füge alle Abwesenheitsarten ein
INSERT OR REPLACE INTO vacation_types (id, name, needs_approval, icon, loco_reason, description) VALUES
    (1, 'Urlaub', 1, '🏖️', 'Url', 'Bezahlter Jahresurlaub'),
    (2, 'Sonderurlaub', 1, '👶', 'Snd', 'Sonderurlaub (Hochzeit, Geburt, etc.)'),
    (3, 'Krankheit', 0, '🤒', 'Krn', 'Krankmeldung'),
    (4, 'Unbezahlter Urlaub', 1, '💰', 'Url', 'Unbezahlter Urlaub'),
    (5, 'Schulung/Seminar', 1, '📚', 'Sem', 'Fortbildung, Schulung, Seminar'),
    (6, 'Zeitausgleich', 1, '⏰', 'ZA.', 'Überstundenabbau'),
    (7, 'Arzttermin', 0, '🏥', NULL, 'Arzttermin (Info an TL)'),
    (8, 'Sonstiges', 0, '📋', NULL, 'Sonstige Abwesenheit');

-- Verifizieren
SELECT id, name, needs_approval, icon, loco_reason FROM vacation_types ORDER BY id;
