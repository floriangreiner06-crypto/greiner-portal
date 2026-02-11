-- Seed: Wissensdatenbank M4 – Checklisten-Positionen + Urteile
-- Einmal ausführen; bei erneutem Lauf werden Checkliste/Urteile nur eingefügt wenn noch leer.
-- Datum: 2026-02-11

BEGIN;

-- ============================================================================
-- 1. CHECKLISTE-POSITIONEN (nur wenn noch keine Einträge)
-- ============================================================================

INSERT INTO unfall_checkliste_positionen (bezeichnung, haeufigkeit, rechtslage, sort_order)
SELECT b, h, r, s FROM (VALUES
  ('Verbringungskosten (Transport zur Lackiererei)', 'Sehr häufig', 'BGH: fast immer berechtigt', 10),
  ('UPE-Aufschläge (Ersatzteilpreisaufschläge)', 'Sehr häufig', 'Berechtigt bei konkreter Abrechnung', 20),
  ('Beilackierung angrenzender Bauteile', 'Häufig', 'Technisch notwendig für Farbtonsicherheit', 30),
  ('Desinfektionskosten', 'Häufig', 'Strittig, oft durchsetzbar', 40),
  ('Stundenverrechnungssätze (Verweis auf günstigere Werkstatt)', 'Sehr häufig', 'Markenwerkstatt steht uns als Vertragswerkstatt zu', 50),
  ('Kleinersatzteile / Befestigungssätze', 'Häufig', 'Pauschale ist branchenüblich', 60),
  ('Probefahrtkosten', 'Mittel', 'Technisch notwendig zur Qualitätssicherung', 70),
  ('Reinigungskosten', 'Mittel', 'Bei Unfallschaden berechtigt', 80),
  ('Entsorgungskosten', 'Mittel', 'Fallen real an', 90),
  ('Mietwagenkosten bei Verzögerung', 'Bei Reparaturverzug', 'Werkstattrisiko liegt beim Schädiger (BGH)', 100),
  ('Ofentrocknung', 'Mittel', 'Technisch notwendig für Lackhaltbarkeit', 110),
  ('Unfallverhütungskosten', 'Selten', 'Arbeitssicherheit, berechtigt', 120)
) AS t(b, h, r, s)
WHERE NOT EXISTS (SELECT 1 FROM unfall_checkliste_positionen LIMIT 1);

-- ============================================================================
-- 2. URTEILE (nur wenn noch keine Einträge)
-- ============================================================================

INSERT INTO unfall_urteile (aktenzeichen, gericht, urteil_datum, position_kategorie, kurzfassung, volltext_link)
SELECT az, g, d, pk, kf, link FROM (VALUES
  ('BGH VI ZR 42/73', 'BGH', '1973-01-01'::DATE, 'Werkstattrisiko, allgemein', 'Grundsatzurteil Werkstattrisiko: Risiko trägt der Schädiger/Versicherung, nicht der Geschädigte.', NULL),
  ('BGH VI ZR 53/09', 'BGH', '2009-01-01'::DATE, 'Stundenverrechnungssätze, Markenwerkstatt', 'Fahrzeug unter 3 Jahre: Anspruch auf Reparatur in Markenwerkstatt.', NULL),
  ('BGH VI ZR 267/14', 'BGH', '2014-01-01'::DATE, 'Stundenverrechnungssätze, Referenzwerkstatt', 'Referenzwerkstatt muss zumutbar erreichbar sein – 20 km bereits unzumutbar.', NULL),
  ('AG Dinslaken 32 C 147/22', 'AG Dinslaken', '2022-01-01'::DATE, 'Verbringungskosten, Desinfektion, Probefahrt', 'Alle Nebenpositionen (Desinfektion, Probefahrt, Verbringung) bestätigt.', NULL),
  ('BGH 16.01.2024 (5 Urteile)', 'BGH', '2024-01-16'::DATE, 'Werkstattrisiko, allgemein', '5 Urteile: Versicherung muss Werkstattrechnung ungekürzt zahlen. Geschädigter trägt kein Werkstattrisiko. Auch „überhöhte“ Positionen muss die Versicherung zahlen.', NULL)
) AS u(az, g, d, pk, kf, link)
WHERE NOT EXISTS (SELECT 1 FROM unfall_urteile LIMIT 1);

-- ============================================================================
-- 3. URTEIL ↔ CHECKLISTE (Zuordnung: welches Urteil für welche Position)
-- ============================================================================

INSERT INTO unfall_urteile_checkliste (urteil_id, checkliste_position_id)
SELECT u.id, c.id FROM unfall_urteile u, unfall_checkliste_positionen c
WHERE u.aktenzeichen = 'AG Dinslaken 32 C 147/22' AND c.bezeichnung LIKE 'Verbringungskosten%'
   OR u.aktenzeichen = 'AG Dinslaken 32 C 147/22' AND c.bezeichnung LIKE 'Desinfektionskosten%'
   OR u.aktenzeichen = 'AG Dinslaken 32 C 147/22' AND c.bezeichnung LIKE 'Probefahrtkosten%'
   OR u.aktenzeichen = 'BGH VI ZR 53/09' AND c.bezeichnung LIKE 'Stundenverrechnungssätze%'
   OR u.aktenzeichen = 'BGH VI ZR 267/14' AND c.bezeichnung LIKE 'Stundenverrechnungssätze%'
   OR u.aktenzeichen = 'BGH VI ZR 42/73' AND c.bezeichnung LIKE 'Verbringungskosten%'
   OR u.aktenzeichen = 'BGH VI ZR 42/73' AND c.bezeichnung LIKE 'Mietwagenkosten%'
   OR u.aktenzeichen = 'BGH 16.01.2024 (5 Urteile)' AND c.bezeichnung LIKE 'Verbringungskosten%'
   OR u.aktenzeichen = 'BGH 16.01.2024 (5 Urteile)' AND c.bezeichnung LIKE 'Stundenverrechnungssätze%'
ON CONFLICT (urteil_id, checkliste_position_id) DO NOTHING;

COMMIT;
