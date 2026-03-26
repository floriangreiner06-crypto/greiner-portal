# Erstzulassung (EZ) – OCR-Erkenntnis: Monat 3 vs. 5

**Workstream:** Werkstatt → Fahrzeuganlage  
**Stand:** 2026-02-25

## Beobachtung

- **EZ erkannt (OCR):** 12.03.2021  
- **EZ korrekt (Sichtprüfung ZB1):** 12.05.2021  

Die **erste KI (AWS Bedrock/Claude)** und **LM Studio (Vision)** machen denselben Fehler: Der **Monat** wird als **03** statt **05** gelesen.

## Einordnung

- **Typische OCR-Verwechslung:** Auf dem Zulassungsbescheinigung Teil 1 (ZB1) sind die Ziffern **3** und **5** (und teils **8**) in manchen Schriftarten/Druckqualitäten schwer unterscheidbar. Das betrifft vor allem das **Erstzulassungsdatum** (Feld B), da dort TT.**MM**.JJJJ – der Monat – oft klein oder unscharf gedruckt ist.
- **Konsequenz:** Falsches EZ fließt in Locosoft, AfA, T-Regel (Verkauf) und Auswertungen ein. Nutzer sollten das EZ-Feld nach dem Scan **immer prüfen**, insbesondere den Monat.

## Maßnahmen (Stand 2026-02-25)

1. **Prompt (SCAN_PROMPT)** in `api/fahrzeugschein_scanner.py`:  
   EZ-Anweisung um den Hinweis ergänzt: *„Auf dem ZB1 werden die Ziffern 3 und 5 (und ggf. 8) im Datum oft verwechselt – Monat und Tag einzeln genau prüfen.“*  
   Damit sowohl Bedrock- als auch LM-Studio-OCR diese typische Verwechslung explizit mitbekommen.

2. **Post-Processing** (bereits vorhanden):  
   - EZ in der Zukunft → auf `null` setzen (vermutlich falsches Feld, z. B. Ausstellungsdatum).  
   - Keine automatische „3→5“-Korrektur ohne weitere Plausibilität (z. B. VIN-Modelljahr), um keine echten 03-Monate zu verfälschen.

3. **Dokumentation:**  
   Dieser Workstream-Kontext (`EZ_OCR_ERKENNTNIS_ERSTZULASSUNG.md`) und Verweis in `docs/workstreams/werkstatt/CONTEXT.md`, damit künftige Anpassungen (andere Modelle, zusätzliche Plausibilitätsprüfung) die Erkenntnis berücksichtigen.

## Optionen für später

- **Plausibilität EZ vs. VIN:** Wenn aus der VIN das Modelljahr abgeleitet wird (z. B. 2021), könnte ein erkannter EZ-Monat 03 bei typischem Produktions-/Zulassungszeitraum geprüft oder als Warnung angezeigt werden (kein Auto-Korrektur ohne klare Regel).
- **Fokus-Prompt nur EZ:** Analog zum zweiten VIN-only-Call einen optionalen „EZ-only“-Call (Bild + kurzer Prompt „Nur Feld B. Datum der ersten Zulassung, Format TT.MM.JJJJ“), falls sich die Fehlerrate sonst nicht reduziert.

---

**Referenz:** `api/fahrzeugschein_scanner.py` (SCAN_PROMPT, _parse_ez_date, EZ-Zukunft-Check in `scan`/`scan_with_lm_studio`).
