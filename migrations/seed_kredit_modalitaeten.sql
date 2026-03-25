-- Seed: Stammdaten Kredit-Modalitäten (Anbieter, Vertragsarten, erste Regeln)
-- Erstellt: 2026-03 | Idempotent: Anbieter/Dokumente nur wenn fehlend

-- Anbieter (idempotent: ON CONFLICT (id))
INSERT INTO kredit_anbieter (id, name, kuerzel, aktiv)
VALUES
    (1, 'Stellantis', 'Stellantis', true),
    (2, 'Santander', 'Santander', true),
    (3, 'Hyundai Finance', 'Hyundai', true),
    (4, 'Genobank', 'Genobank', true)
ON CONFLICT (id) DO NOTHING;

SELECT setval(pg_get_serial_sequence('kredit_anbieter', 'id'), (SELECT COALESCE(MAX(id), 1) FROM kredit_anbieter));

-- Vertragsarten (nur wenn noch keine vorhanden)
INSERT INTO kredit_vertragsart (anbieter_id, bezeichnung, produkt_code, aktiv)
SELECT 1, 'EK-Finanzierung Neuwagen', 'EK-NW', true WHERE NOT EXISTS (SELECT 1 FROM kredit_vertragsart WHERE anbieter_id = 1 AND produkt_code = 'EK-NW');
INSERT INTO kredit_vertragsart (anbieter_id, bezeichnung, produkt_code, aktiv)
SELECT 1, 'EK-Finanzierung Gebrauchtwagen', 'EK-GW', true WHERE NOT EXISTS (SELECT 1 FROM kredit_vertragsart WHERE anbieter_id = 1 AND produkt_code = 'EK-GW');
INSERT INTO kredit_vertragsart (anbieter_id, bezeichnung, produkt_code, aktiv)
SELECT 2, 'EK-Finanzierung', 'EK', true WHERE NOT EXISTS (SELECT 1 FROM kredit_vertragsart WHERE anbieter_id = 2 LIMIT 1);
INSERT INTO kredit_vertragsart (anbieter_id, bezeichnung, produkt_code, aktiv)
SELECT 3, 'EK-Finanzierung', 'EK', true WHERE NOT EXISTS (SELECT 1 FROM kredit_vertragsart WHERE anbieter_id = 3 LIMIT 1);
INSERT INTO kredit_vertragsart (anbieter_id, bezeichnung, produkt_code, aktiv)
SELECT 4, 'EK-Finanzierung', 'EK', true WHERE NOT EXISTS (SELECT 1 FROM kredit_vertragsart WHERE anbieter_id = 4 LIMIT 1);

-- Dokumente (nur wenn noch keins für Anbieter 1)
INSERT INTO kredit_dokumente (anbieter_id, titel, dokument_typ, bemerkung)
SELECT 1, 'Stellantis Ausführungsbestimmungen EK-Finanzierung (Referenz)', 'Ausführungsbestimmung', 'Regelwerte aus Excel-Import-Logik / Doku; PDF bei Bedarf nachtragen'
WHERE NOT EXISTS (SELECT 1 FROM kredit_dokumente WHERE anbieter_id = 1 LIMIT 1);

-- Stellantis: Zinsfreiheit und Zinssatz (nur wenn noch keine Regel für EK-NW)
INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT va.id, d.id, 'zinsfreiheit_tage', 'zinsfreiheit_tage', '90', 'Tage', 'Neuwagen',
    'Zinsfreiheit ab Vertragsbeginn; Dauer aus Excel-Spalte „Zinsfreiheit (Tage)“ pro Fahrzeug. Typisch 90 Tage für Neuwagen (Ausführungsbestimmungen).',
    10, true
FROM kredit_vertragsart va
JOIN kredit_anbieter a ON va.anbieter_id = a.id
CROSS JOIN (SELECT id FROM kredit_dokumente WHERE anbieter_id = 1 LIMIT 1) d
WHERE a.kuerzel = 'Stellantis' AND va.produkt_code = 'EK-NW'
  AND NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen ab JOIN kredit_vertragsart v ON ab.vertragsart_id = v.id WHERE v.produkt_code = 'EK-NW' AND ab.regel_key = 'zinsfreiheit_tage')
LIMIT 1;

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT va.id, d.id, 'zinssatz_pct', 'zinssatz_pct', '9.03', 'Prozent', 'p.a. nach Zinsfreiheit',
    'Festzinssatz 9,03 % p.a. nach Ablauf der Zinsfreiheit (Import berechnet Zinsen so).',
    20, true
FROM kredit_vertragsart va
JOIN kredit_anbieter a ON va.anbieter_id = a.id
CROSS JOIN (SELECT id FROM kredit_dokumente WHERE anbieter_id = 1 LIMIT 1) d
WHERE a.kuerzel = 'Stellantis' AND va.produkt_code = 'EK-NW'
  AND NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen ab JOIN kredit_vertragsart v ON ab.vertragsart_id = v.id WHERE v.produkt_code = 'EK-NW' AND ab.regel_key = 'zinssatz_pct')
LIMIT 1;

-- Santander Platzhalter-Dokument
INSERT INTO kredit_dokumente (anbieter_id, titel, dokument_typ, bemerkung)
SELECT 2, 'Santander Modalitäten (Platzhalter)', 'Modalität', 'Santander-Modalitäten nach Lieferung einpflegen.'
WHERE NOT EXISTS (SELECT 1 FROM kredit_dokumente WHERE anbieter_id = 2 LIMIT 1);
