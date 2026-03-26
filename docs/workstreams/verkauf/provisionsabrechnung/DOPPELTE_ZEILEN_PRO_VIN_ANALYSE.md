# Doppelte Zeilen pro VIN in L744PR-Export (0126.csv)

**Stand:** 2026-02-17

## Ausgangslage

- CSV hat **167 Zeilen** (1 Kopfzeile + 166 Datenzeilen; Nutzer nannte 93 in xls – ggf. nach Filter).
- In der DB gibt es **72 verkaufte Fahrzeuge** (dealer_vehicles) mit Rechnungsdatum Januar 2026.
- Differenz: **166 − 72 = 94** „überzählige“ Zeilen → kommen durch **mehrere Zeilen pro VIN** zustande.

## Analyse nach VIN

| Kategorie | Anzahl VINs | Zeilen gesamt | Ursache |
|-----------|-------------|----------------|---------|
| **Nur 1 Zeile pro VIN** | 1 | 1 | Eindeutiger Verkauf |
| **Mehrere Zeilen pro VIN** | 72 | 165 | Siehe unten |

### 1) Echte Duplikate (gleiche Rg-Nr., gleiches Rg.Netto)

- **55 VINs** erscheinen **zweimal** mit exakt derselben Rechnung (gleiche Rg-Nr., gleiches Rg.Netto, gleicher Deckungsbeitrag).
- **110 Zeilen** → **55 überzählige Zeilen**.
- **Ursache:** Der Report L744PR gibt dieselbe Verkaufszeile offenbar **doppelt** aus. Mögliche Gründe:
  - Gruppierung/Gliederung im Report (z. B. Ausgabe nach Verkaufsberater **und** nach Fahrzeugart, sodass derselbe Verkauf in beiden Blöcken steht).
  - Export-Option, die jede Zeile zweimal schreibt.

### 2) Mehrere Rechnungen/Positionen pro VIN (verschiedene Rg-Nr. oder Beträge)

- **17 VINs** haben **2–4 Zeilen** mit **unterschiedlichen** Rg-Nr. oder Rg.Netto.
- **55 Zeilen** → **38 überzählige Zeilen** (55 − 17 = 38).

**Rg-Typ:**

- **H** = Hauptrechnung (Fahrzeug).
- **Z** = Zusatzrechnung (z. B. Zubehör, Nebenkosten, Korrektur).

**Beispiele:**

- Eine VIN mit **H** (z. B. 35.702,88 €) und **Z** (1.088,24 €) → Zubehör/Nebenkosten auf eigener Rechnung.
- Teilweise **mehrere Z** pro VIN (z. B. 1.088,24 und −50,00).
- Bei manchen VINs erscheint **dieselbe Rg-Nr. (H) zweimal** mit unterschiedlichem Rg.Netto (z. B. 35.702,88 vs. 36.791,12) – evtl. durch Report-Option **„inkl. Aufschlüsselung aufteilbarer Zahlungen“** (eine Rechnung, mehrere Exportzeilen).

## Zusammenfassung: Woher kommen die Doppelzeilen?

| Ursache | Überzählige Zeilen (ca.) |
|---------|---------------------------|
| Echte Duplikate (55 VINs × 1 zusätzliche Zeile) | 55 |
| Mehrere Rechnungen/Positionen pro VIN (17 VINs, H+Z oder H+Z+Z) | 38 |
| **Summe** | **93** |

## Konsequenz für unsere Abfrage

- **72 Zeilen** = eine Zeile **pro Fahrzeug** (dealer_vehicles, eine Rechnung pro Verkauf) – das ist die **Stückzahl**, die wir mit der aktuellen Abfrage korrekt abbilden.
- Die **93 zusätzlichen Zeilen** im Export entstehen durch:
  1. **Report-Duplikate:** dieselbe Zeile zweimal ausgegeben (55 Fälle).
  2. **Haupt- + Zusatzrechnungen:** pro VIN mehrere Rechnungen (H + Z), die der Report als getrennte Zeilen ausgibt (17 VINs, 38 Zusatzzeilen).

Um **93 Zeilen** wie im Export zu erzeugen, müsste man:
- die **Zusatzrechnungen (Rg-Typ Z)** zu den Hauptrechnungen aus Locosoft laden (z. B. über `invoices` / Verknüpfung zu `dealer_vehicles` oder journal_accountings) und
- die **Report-Duplikate** nachbilden oder akzeptieren, dass unsere Abfrage nur die 72 Fahrzeugverkäufe ohne Duplikate liefert.
