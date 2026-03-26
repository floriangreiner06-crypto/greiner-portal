# Testanleitung AfA-Modul — für Christian (Buchhaltung)

**Stand:** 2026-02-17  
**Ziel:** Das AfA-Modul (Vorführwagen / Mietwagen) testen und prüfen, ob Konten, Buchungsliste und Bestände für die Buchhaltung stimmen.

---

## 1. Zugang

1. Im Browser **http://drive** aufrufen und einloggen.
2. Im Menü: **Controlling** → **AfA Vorführwagen / Mietwagen**.
3. Die AfA-Seite sollte mit KPI-Karten (Aktive VFW, Aktive Mietwagen, Restbuchwert, AfA pro Monat) und Tabellen laden.

**Erwartung:** Seite öffnet ohne Fehlermeldung.

---

## 2. Monatsübersicht und Buchungsliste (wichtig für die Buchung)

1. Auf der Seite nach unten scrollen bis **„Monatsübersicht — Buchungsliste für Locosoft“**.
2. **Monat** wählen (z. B. aktueller Monat oder Vormonat).
3. Auf **„Berechnen“** klicken (legt ggf. fehlende AfA-Buchungen für den Monat an).
4. Tabelle prüfen: Pro Zeile stehen **Kennzeichen**, **Bezeichnung**, **Art** (VFW/Mietwagen), **Soll**, **Haben**, **AfA-Betrag**.
5. **Summe** unten = Betrag für die Monatsbuchung (sollte mit eurer DATEV/Belegung abgleichbar sein).
6. **„CSV exportieren“** klicken → CSV-Datei wird heruntergeladen. Darin: Soll- und Haben-Konten pro Zeile.

**Konten zum Abgleich (Stand 2026-02):**

| Bereich           | Soll  | Haben  |
|-------------------|-------|--------|
| Mietwagen DEG     | 450001 | 022501 |
| Mietwagen LAN     | 450002 | 022502 |
| Mietwagen HYU     | 450001 | 022501 |
| VFW DEG           | 450001 | 318001 |
| VFW LAN           | 450002 | 318002 |
| VFW HYU           | 450001 | 318001 |
| VFW Leapmotor     | 450001 | 318201 |

**Erwartung:** Summe und Konten (Soll/Haben) in der Tabelle bzw. CSV entsprechen euren Buchungsvorgaben. Bitte prüfen, ob die **Kontonummern** (022501, 022502, 318001, 318002, 318201) und die **Soll-Konten** (450001/450002) so für euch stimmen.

---

## 3. Bestand (Fahrzeugliste) vs. eure Listen

1. Oben auf der Seite: **Fahrzeuge (VFW / Mietwagen)** — Tabelle mit allen erfassten Fahrzeugen.
2. Filter **Bestand** (z. B. 2025/26) und ggf. **Art** (VFW / MIETWAGEN) nutzen.
3. Prüfen: Entspricht die **Anzahl** und die **Aufteilung** (VFW vs. Mietwagen, ggf. nach Standort) ungefähr euren Excel-Listen?

**Erwartung:** Stückzahlen und Zuordnung (VFW/Mietwagen) sind plausibel. Abweichungen bitte notieren.

---

## 4. „Bestand laden“ (Locosoft) und Zeilennummern

1. Weiter nach unten zu **„Aus Locosoft importieren“**.
2. **„Bestand laden“** klicken.
3. Es erscheint eine Tabelle mit Fahrzeugen aus Locosoft, die noch **nicht** in AfA sind und **noch nicht verkauft** (VFW Typ V, Mietwagen mit Jw-Kz **M**).
4. Spalten: **Nr.** (Zeilennummer), Kennzeichen, VIN, Bezeichnung, Art, Anschaffung, EK netto, **Detail** (Button).
5. Optional: Bei einer Zeile auf **„Detail“** klicken → Fenster mit Locosoft-Daten (VIN, Kom.Nr., Kalkulation, EK netto) öffnet sich.

**Erwartung:** Tabelle lädt, Zeilen sind nummeriert. Detail-Button öffnet die Locosoft-Details.

---

## 5. Abgangs-Kontrolle (DRIVE vs. Locosoft)

1. Abschnitt **„Abgangs-Kontrolle“** suchen.
2. **„Aktualisieren“** klicken.
3. Zwei Bereiche:
   - **„Bitte Abgang in DRIVE prüfen“:** Fahrzeuge, die in Locosoft schon als verkauft gelten, in DRIVE aber noch „aktiv“. → Sollten in DRIVE als Abgang erfasst werden.
   - **„Abgang in DRIVE“:** Bereits in DRIVE als verkauft geführt, mit Locosoft-Rechnungsdatum zur Kontrolle.

**Erwartung:** Liste ist plausibel. Wenn unter „Bitte Abgang prüfen“ Einträge stehen, bitte prüfen und ggf. Abgang in DRIVE nachziehen.

---

## 6. Tageszulassung (nicht AfA-pflichtig)

1. In der **Fahrzeugliste** (oben) bei einem Fahrzeug auf **„Detail“** klicken.
2. Im geöffneten Fenster: Checkbox **„Tageszulassung (nicht AfA-pflichtig)“** und Button **„Speichern“**.
3. Wenn die Checkbox gesetzt wird und gespeichert: Das Fahrzeug erscheint **nicht** in der Monatsübersicht/Buchungsliste und nicht in der AfA-Summe (nur noch in der Liste mit Badge „Tageszul.“).

**Erwartung:** Checkbox speichern funktioniert; Tageszulassungen erscheinen nicht in der Buchungsliste.

---

## 7. Rückmeldung

Bitte nach dem Test kurz notieren:

- **Konten:** Stimmen Soll/Haben (450001, 450002, 022501, 022502, 318001, 318002, 318201) mit eurer Buchhaltung?
- **Buchungsliste/Summe:** Passt die Monatssumme und die Aufteilung zu euren Erwartungen?
- **Bestand:** Passen die Stückzahlen (VFW/Mietwagen) grob zu euren Listen?
- **Abgangs-Kontrolle:** Sind die Hinweise verständlich und hilfreich?
- **Sonstige Punkte:** Was fehlt, was ist unklar, was sollte anders sein?

Ansprechpartner für technische Fragen: Florian / IT.

---

*Ende der Testanleitung*
