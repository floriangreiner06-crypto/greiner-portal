-- Seed: Santander-Dokumente und Modalitäten aus den drei PDFs (Liquiditaet-Ordner)
-- Quelle: Kreditrahmenvereinbarung_P@rtnerPlus_bestätigt.pdf, Allgemeine Bedingungen, Gebührenverzeichnis
-- Siehe: docs/workstreams/controlling/Liquiditaet/SANTANDER_PDF_INHALT.md

-- 1) Dokumente (Santander anbieter_id = 2), nur wenn noch nicht vorhanden
INSERT INTO kredit_dokumente (anbieter_id, titel, dokument_typ, dateipfad, bemerkung)
SELECT 2, 'Allgemeine Bedingungen Einkaufsfinanzierung (Mobilität)', 'Ausführungsbestimmung',
     'docs/workstreams/controlling/Liquiditaet/Allgemeinen_Bedingungen_Einkaufsfinanzierung_Mobilitaet.pdf',
     'Santander Consumer Bank AG, rechtlicher Rahmen (9 S.)'
WHERE NOT EXISTS (SELECT 1 FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Allgemeine Bedingungen Einkaufsfinanzierung%');
INSERT INTO kredit_dokumente (anbieter_id, titel, dokument_typ, dateipfad, bemerkung)
SELECT 2, 'Gebühren- und Leistungsverzeichnis Händlerfinanzierung', 'Gebührenverzeichnis',
     'docs/workstreams/controlling/Liquiditaet/Gebuehren_Leistungsverzeichnis_Haendlerfinanzierung.pdf',
     'Gültig ab 01.09.2025; P@rtnerKonto, SEPA, Auslandszahlung'
WHERE NOT EXISTS (SELECT 1 FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Gebühren%Leistungsverzeichnis%');
INSERT INTO kredit_dokumente (anbieter_id, titel, dokument_typ, dateipfad, bemerkung)
SELECT 2, 'Kreditrahmenvereinbarung P@rtnerPlus (bestätigt)', 'Kreditrahmenvereinbarung',
     'docs/workstreams/controlling/Liquiditaet/Kreditrahmenvereinbarung_P@rtnerPlus_bestätigt.pdf',
     'EKF-2025-001747; Auto Greiner / Autohaus Greiner; Tilgung, Zinsen, Kreditrahmen'
WHERE NOT EXISTS (SELECT 1 FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%P@rtnerPlus%');

-- 2) Ausführungsbestimmungen aus Kreditrahmenvereinbarung (Santander EK: vertragsart_id = 3)
-- Nur einfügen wenn noch keine Santander-Regeln mit diesen Keys existieren
INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1),
    'kreditrahmen_gesamt', 'kreditrahmen_gesamt', '1500000', 'Euro', NULL,
    'Gesamtrahmen P@rtnerPlus EUR 1.500.000. Kann vollständig für Neu- und Gebrauchtfahrzeuge verwendet werden.',
    10, true WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen ab JOIN kredit_vertragsart v ON ab.vertragsart_id = v.id WHERE v.anbieter_id = 2 AND ab.regel_key = 'kreditrahmen_gesamt');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1),
    'kreditrahmen_mobilitaet', 'kreditrahmen_mobilitaet', '500000', 'Euro', 'Mobilitätsfahrzeuge',
    'Max. EUR 500.000 für Mobilitätsfahrzeuge (aktuell zugelassen, max. 7 Jahre ab Ez).',
    11, true WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen ab JOIN kredit_vertragsart v ON ab.vertragsart_id = v.id WHERE v.anbieter_id = 2 AND ab.regel_key = 'kreditrahmen_mobilitaet');

-- Hilfs-Subquery für Kreditrahmen-Dokument
-- Tilgung Neu- & Gebrauchtfahrzeuge
INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'tilgung', 'tilgung_60_tag', '10', 'Prozent', 'Neu- & Gebrauchtfahrzeuge, 60. Tag',
    'Abschlagszahlung 60. Tag: 10 % vom ursprünglichen Finanzierungsbetrag. Frist ab Valutierung.', 20, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'tilgung_60_tag');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'tilgung', 'tilgung_120_tag', '10', 'Prozent', 'Neu- & Gebrauchtfahrzeuge, 120. Tag', 'Abschlagszahlung 120. Tag: 10 %.', 21, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'tilgung_120_tag');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'tilgung', 'tilgung_180_tag', '10', 'Prozent', 'Neu- & Gebrauchtfahrzeuge, 180. Tag', 'Abschlagszahlung 180. Tag: 10 %.', 22, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'tilgung_180_tag');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'tilgung', 'tilgung_360_tag', 'Restsaldo', NULL, 'Neu- & Gebrauchtfahrzeuge, 360. Tag',
    '360. Tag: Restsaldo fällig. Laufzeitverlängerung möglich: +10 % nach 360 Tagen, +10 % nach 540 Tagen, max. 720 Tage.', 23, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'tilgung_360_tag');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'tilgung', 'tilgung_mobilitaet_monatlich', '1.5', 'Prozent', 'Mobilitätsfahrzeuge',
    'Mobilitätsfahrzeuge: monatliche Tilgung 1,5 %; 720. Tag Restsaldo; danach weiter 1,5 % monatlich.', 24, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'tilgung_mobilitaet_monatlich');

-- Zinsaufschlag (auf 6-Monats-Euribor; Mindestreferenz 0 Basispunkte)
INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'zinsaufschlag', 'zinsaufschlag_1_90_tag', '2.00', 'Prozentpunkte', 'Neu- & Gebrauchtfahrzeuge, 1.–90. Tag', 'Zinsaufschlag 1.–90. Tag: 2,00 % (auf 6-Monats-Euribor).', 30, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'zinsaufschlag_1_90_tag');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'zinsaufschlag', 'zinsaufschlag_91_180_tag', '3.50', 'Prozentpunkte', 'Neu- & Gebrauchtfahrzeuge, 91.–180. Tag', 'Zinsaufschlag 91.–180. Tag: 3,50 %.', 31, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'zinsaufschlag_91_180_tag');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'zinsaufschlag', 'zinsaufschlag_181_360_tag', '4.00', 'Prozentpunkte', 'Neu- & Gebrauchtfahrzeuge, 181.–360. Tag', 'Zinsaufschlag 181.–360. Tag: 4,00 %.', 32, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'zinsaufschlag_181_360_tag');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'zinsaufschlag', 'zinsaufschlag_ab_361_tag', '9.90', 'Prozentpunkte', 'Neu- & Gebrauchtfahrzeuge, ab 361. Tag', 'Zinsaufschlag ab 361. Tag bis Laufzeitende: 9,90 %.', 33, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'zinsaufschlag_ab_361_tag');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'zinsaufschlag', 'zinsaufschlag_mobilitaet', '3.50', 'Prozentpunkte', 'Mobilitätsfahrzeuge, 1. Tag bis Laufzeitende', 'Mobilitätsfahrzeuge: Zinsaufschlag 3,50 % (auf 6-Monats-Euribor) für gesamte Laufzeit.', 34, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'zinsaufschlag_mobilitaet');

-- Beleihung / Finanzierungsbetrag
INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'beleihung', 'finanzierungsbetrag_min_pkw', '2000', 'Euro', 'PKW', 'Finanzierungsbetrag mind. 2.000 € (PKW) / 1.000 € (Motorräder), max. 120.000 €.', 40, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'finanzierungsbetrag_min_pkw');

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT 3, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 2 AND titel LIKE '%Kreditrahmen%' LIMIT 1), 'beleihung', 'finanzierungsbetrag_max', '120000', 'Euro', NULL, 'Finanzierungsbetrag pro Einzelkredit max. 120.000 €.', 41, true
WHERE NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen WHERE vertragsart_id = 3 AND regel_key = 'finanzierungsbetrag_max');
