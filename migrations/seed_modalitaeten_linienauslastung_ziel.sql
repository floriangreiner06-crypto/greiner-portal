-- Ziel Linienauslastung Stellantis (Steuerparameter aus Vorschlag, nicht aus PDF/CSV)
-- Wird von Auswertungen/Einkaufsfinanzierung gelesen (SSOT Soll-Wert).

INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, dokument_id, regel_typ, regel_key, regel_wert, einheit, bedingung, volltext, sortierung, aktiv)
SELECT va.id, (SELECT id FROM kredit_dokumente WHERE anbieter_id = 1 LIMIT 1),
    'ziel', 'linienauslastung_ziel', '85', 'Prozent', 'Ziel Auslastung der Linie (Stellantis EK)',
    'Steuerparameter: Ziel Linienauslastung in % für Stellantis EK-Finanzierung. Von Einkaufsfinanzierung/Auswertungen lesbar.',
    15, true
FROM kredit_vertragsart va
JOIN kredit_anbieter a ON va.anbieter_id = a.id
WHERE a.kuerzel = 'Stellantis' AND va.produkt_code = 'EK-NW'
  AND NOT EXISTS (SELECT 1 FROM kredit_ausfuehrungsbestimmungen ab WHERE ab.vertragsart_id = va.id AND ab.regel_key = 'linienauslastung_ziel');
