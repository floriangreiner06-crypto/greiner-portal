-- Optional: Ermöglicht Fuzzy-VIN-Suche im Dublettencheck (Fahrzeuganlage).
-- Wenn die OCR die VIN um 1–2 Zeichen falsch erkennt (z.B. C/S, G/Z), wird
-- trotzdem die Locosoft-Dublette gefunden (matched_by = vin_fuzzy).
-- Benötigt: PostgreSQL Extension fuzzystrmatch (Standard-Lieferumfang).
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
