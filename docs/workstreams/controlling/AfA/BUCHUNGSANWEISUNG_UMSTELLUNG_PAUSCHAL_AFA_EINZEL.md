# Buchungsanweisung: Umstellung Pauschale AfA → Einzelabschreibung (DRIVE)

**Zweck:** Pauschale AfA-Rückstellung (Locosoft/Sachkonten 090301, 090302, 090401, 090402) ertragswirksam auflösen und stattdessen pro Fahrzeug die Einzelwertberichtigung des Buchwerts (an DRIVE-Restbuchwerte angepasst) buchen.

**Stichtag / Werte:** Bitte mit aktuellem Stichtag und von DRIVE bereitgestellter Liste (Fahrzeug, Anschaffungskosten, Restbuchwert, kumulierte AfA) durchführen. Die folgenden Beträge sind Beispielwerte (Stand Abgleichsdokument).

---

## Ausgangslage

| | Buchhaltung (pauschal) | DRIVE (Einzel) |
|---|------------------------|----------------|
| Kumulierte AfA | 338.200,88 € (090301, 090302, 090401, 090402) | 428.619,09 € |
| Restbuchwert (abgeleitet bzw. Summe) | 2.450.925,67 € | 2.360.507,46 € |

→ Durch die Umstellung entsteht ertragswirksam **weiterer Abschreibungsbedarf** von **90.418,21 €** (Differenz der AfA bzw. Minderung der Restbuchwerte).

---

## Schritt 1: Auflösung der pauschalen AfA (ertragswirksam)

Die bestehende **pauschale AfA-Rückstellung** wird in voller Höhe aufgelöst. Die Gegenbuchung erfolgt **ertragswirksam** (Auflösung Rückstellung = Ertrag).

| Soll | Haben | Betrag (€) | Buchungstext |
|------|--------|------------|--------------|
| 090301 RENT DEG | 3240 Auflösung Rückstellungen (o.ä.) | 45.540,69 | Auflösung pauschale AfA Vorführ-/Mietwagen (Umstellung Einzelabschreibung DRIVE), Stichtag … |
| 090302 RENT LAN | 3240 Auflösung Rückstellungen | 24.921,69 | wie oben |
| 090401 VFW Opel DEG | 3240 Auflösung Rückstellungen | 66.873,00 | wie oben |
| 090402 VFW Opel LAN | 3240 Auflösung Rückstellungen | 21.692,90 | wie oben |
| 090401 VFW HYU | 3240 Auflösung Rückstellungen | 179.172,60 | wie oben |
| **Summe Soll** | **Summe Haben** | **338.200,88** | |

**Hinweis:** Kontonummer „3240“ (Auflösung Rückstellungen) bitte an euren Kontenrahmen anpassen (z. B. SKR03/SKR04 oder GlobalCube); ggf. „Sonstige Erträge“ oder separates Ertragskonto für Rückstellungsauflösung verwenden.

---

## Schritt 2: Einzelwertberichtigung / Einzelabschreibung pro Fahrzeug

Ziel: Pro Fahrzeug soll der **Buchwert in der Buchhaltung** dem **Restbuchwert aus DRIVE** entsprechen.

- **Datenquelle:** DRIVE liefert je Fahrzeug (z. B. Export/Liste): Kennzeichen, Anschaffungskosten (AK), Restbuchwert (DRIVE), kumulierte AfA (AK − Restbuchwert).
- **Buchungslogik:** Es ist die **kumulierte AfA pro Fahrzeug** zu buchen (Wertberichtigung/Einzelabschreibung), sodass:  
  **Buchwert = Anschaffungskosten − gebuchte AfA = Restbuchwert (DRIVE).**

**Variante A – Einzelbuchung pro Fahrzeug (wenn Einzelkonten/Subkonten pro Fahrzeug geführt werden):**

| Soll | Haben | Betrag (€) | Buchungstext |
|------|--------|------------|--------------|
| 6540 Abschreibungen Sachanlagen (o.ä.) | 0951 AfA Vorführ-/Mietwagen (oder Fahrzeug-AfA-Konto) | [AfA-Betrag Fahrzeug 1] | Einzelabschreibung Vorführ-/Mietwagen, Kennz. …, Stichtag … |
| … | … | … | (wiederholt pro Fahrzeug) |
| **Summe** | **Summe** | **428.619,09** | Summe aller Einzel-AfA = kumulierte AfA DRIVE |

**Variante B – Sammelbuchung mit Belegliste:**

- **Eine** Buchung: Soll 6540 (Aufwand) mit **Summe 428.619,09 €**, Haben 0951 (AfA) mit **428.619,09 €**.
- **Beleg/Anlage:** Liste aller Fahrzeuge mit Kennzeichen, Anschaffungskosten, Restbuchwert (DRIVE), AfA-Betrag (AK − Restbuchwert), ggf. Konto 090301/090302/090401/090402 zur Zuordnung Standort.

**Konten:** 6540 und 0951 bitte an euren Kontenrahmen anpassen (z. B. Abschreibungen auf Sachanlagen, AfA-Konto zu 0950 Vorführ-/Mietwagen).

---

## Zusammenfassung der Effekte

| Schritt | Soll | Haben | Effekt |
|---------|------|--------|--------|
| 1 – Auflösung Pauschale | 090301, 090302, 090401, 090402 | 3240 (Erlös) | Pauschale AfA weg, Ertrag +338.200,88 € |
| 2 – Einzelabschreibung | 6540 (Aufwand) | 0951 (AfA) | AfA-Aufwand 428.619,09 € |
| **Saldo ertragswirksam** | | | **−90.418,21 €** (Mehraufwand = weiterer Abschreibungsbedarf) |

Nach Umsetzung entsprechen die Buchwerte in der Buchhaltung den DRIVE-Restbuchwerten; künftige Abschreibungen können monatlich/saisonell aus DRIVE übernommen werden.

---

## Was DRIVE liefern kann

- **Liste für Schritt 2:** Export/Report pro Stichtag mit allen aktiven AfA-Fahrzeugen: Kennzeichen, Anschaffungskosten netto, Restbuchwert (DRIVE), kumulierte AfA (AK − Restbuchwert), optional Zuordnung zu 090301/090302/090401/090402 (Standort).
- **CSV für Buchhaltung / Stapelverarbeitung:** Geplant; Formatierung und ggf. Stapelverarbeitung werden mit Locosoft abgestimmt. Sobald Anforderungen (Spalten, Format, Trennzeichen) vorliegen, kann ein CSV-Export in DRIVE umgesetzt werden.
- **PDF Auktion (Zeitnah):** In den Verkaufsempfehlungen (Controlling → AfA → Verkaufsempfehlungen) können Fahrzeuge einzeln an- und abgewählt werden; Button „PDF Auktion exportieren“ erzeugt ein PDF mit: Marke (aus Locosoft), Typ, EZ, Km Stand, Abverkaufspreis (unser ermittelter = Buchwert + 50 % Zinsen). Layout wie DRIVE-Report-Standard.

---

**Stand:** März 2026 · Kontenrahmen (3240, 6540, 0950, 0951) mit Buchhaltung/Steuerberater abstimmen.
