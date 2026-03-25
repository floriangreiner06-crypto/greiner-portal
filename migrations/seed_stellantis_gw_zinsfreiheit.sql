-- Stellantis EK-GW (Gebrauchtwagen): 90 Tage Zinsfreiheit, Zinssatz 9,03 % p.a. (wie NW)
-- Quelle: gleiche Konditionen wie Neuwagen für GW.

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT va.id, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 1 LIMIT 1),
    'zinsfreiheit_tage', 'zinsfreiheit_tage', '90', 'Tage', 'Gebrauchtwagen',
    'Zinsfreiheit ab Vertragsbeginn; 90 Tage für Gebrauchtwagen (Stellantis EK-GW).',
    10, true
FROM kredit_vertragsart va
JOIN kredit_anbieter a ON va.anbieter_id = a.id
WHERE a.kuerzel = 'Stellantis' AND va.produkt_code = 'EK-GW'
  AND NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen ab WHERE ab.vertragsart_id = va.id AND ab.regel_key = 'zinsfreiheit_tage');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT va.id, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 1 LIMIT 1),
    'zinssatz_pct', 'zinssatz_pct', '9.03', 'Prozent', 'p.a. nach Zinsfreiheit (GW)',
    'Festzinssatz 9,03 % p.a. nach Ablauf der Zinsfreiheit (Stellantis EK-Gebrauchtwagen).',
    20, true
FROM kredit_vertragsart va
JOIN kredit_anbieter a ON va.anbieter_id = a.id
WHERE a.kuerzel = 'Stellantis' AND va.produkt_code = 'EK-GW'
  AND NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen ab WHERE ab.vertragsart_id = va.id AND ab.regel_key = 'zinssatz_pct');
