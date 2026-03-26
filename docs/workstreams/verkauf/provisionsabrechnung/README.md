# Provisionsabrechnung Verkäufer (DRIVE-Integration)

## Zwei getrennte Provisionssysteme

1. **Verkäufer (Außendienst/Verkauf):** PDFs pro Person/Monat (z. B. **Kraus Rafael**, **Schmid Roland**; weitere: Fialkowski, Löbel, Pellkofer, Penn, Punzmann, …). Gleiche Rohdaten (Locosoft-Export), Filter/Sortierung im Excel-Tool, dann PDF pro Verkäufer + Sammel-PDFs für Lohnbuchhaltung (AS, FP, ML, MP, RK, RS, DF, EP).
2. **Verkaufsleiter:** Anton Süß – **eigenes Provisionssystem**, andere Logik. Die Dateien „Süß Anton_MMYY.xlsx“ / „Süß Anton_MMYY.pdf“ und ggf. „Kopie von Süß Anton_…“ gehören zu diesem separaten Abrechnungslauf. Für Tests/Beispiele Verkäufer-Provisionslogik werden **nicht** Anton Süß, sondern z. B. Kraus Rafael und Roland Schmid verwendet.

Bei DRIVE-Integration: Verkäufer-Provisionslogik und Verkaufsleiter-Provisionslogik getrennt betrachten (evtl. nacheinander abbilden).

## Ausgangslage (Verkäufer)

- **Bisher:** Export aus Locosoft (ausgelieferte Fahrzeuge) → Excel-Tool filtert/sortiert → PDF-Abrechnung für Verkäufer und Lohnbuchhaltung.
- **Ziel:** Provisionsabrechnungssystem in DRIVE integrieren (Filter/Sortierung ggf. in DB oder Locosoft-PostgreSQL).

## Verzeichnis

- Doku und spätere Locosoft-Listen/Abgleiche: dieses Verzeichnis.
- Windows-Sync: `\\Srvrdb01\...\Server\docs\workstreams\verkauf\provisionsabrechnung\` (bzw. `/mnt/greiner-portal-sync/docs/workstreams/verkauf/provisionsabrechnung/` auf dem Server). Dort liegen nach `python3 scripts/provisions_berechnung_kraus_jan2026.py --sync` die **Einzelberechnung** (CSV + Report) zum Vergleich mit der echten Abrechnung.
- **Regeln (bekannt + offen):** `PROVISIONSREGELN_SYSTEM.md` – zentrale Stelle zum Pflegen und Bestätigen der Provisionsregeln; Skripte richten sich danach.

## Doku

- **Analyse Rohdaten + PDFs:** `ANALYSE_DATEN_UND_ABRECHNUNGEN.md` (CSV-Spalten, Ordnerstruktur, Verkäufer-PDFs = manueller Versand, Sammel-PDFs für Lohnbuchhaltung, offene Punkte für DRIVE).

## Nächste Schritte

1. Locosoft-Liste (Struktur/Spalten) bereitstellen.
2. Prüfen: Filter in DRIVE-PostgreSQL oder Locosoft-PostgreSQL abbilden.

---
*Angelegt: 2026-02-17, Workstream: verkauf*
