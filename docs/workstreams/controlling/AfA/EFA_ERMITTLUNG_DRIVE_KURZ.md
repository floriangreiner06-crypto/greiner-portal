# Ist die AfA-Ermittlung in DRIVE korrekt?

**Kurzantwort: Ja.** Die Berechnung entspricht linearer AfA über die Nutzungsdauer mit „Anschaffungsmonat zählt mit“.

---

## 1. Was DRIVE rechnet

- **Methode:** linear (nur diese ist implementiert).
- **Nutzungsdauer:** 72 Monate (Standard VFW/Mietwagen), pro Fahrzeug in `afa_anlagevermoegen.nutzungsdauer_monate` pflegbar.
- **Monatliche AfA:**  
  `afa_monatlich = Anschaffungskosten_netto / nutzungsdauer_monate`  
  (z. B. 72.000 € / 72 = 1.000 €/Monat).
- **Restbuchwert zum Stichtag:**  
  `Restbuchwert = AK − (Monate × afa_monatlich)`  
  mit **Monate** = Anzahl Monate **einschließlich** Anschaffungsmonat und **einschließlich** Stichtagsmonat, maximal Nutzungsdauer, mindestens 0.

Formel Monate (aus `berechne_restbuchwert`):

```text
Monate = (Stichtag.Jahr − Anschaffung.Jahr) × 12 + (Stichtag.Monat − Anschaffung.Monat) + 1
Monate = min(max(Monate, 0), nutzungsdauer_monate)
```

Damit gilt: **Anschaffungsmonat zählt mit**, und der **Stichtagsmonat zählt voll** (z. B. Stichtag 2.3.2026 → März 2026 wird mitgezählt).

---

## 2. Stichproben (aus Testlauf)

| Szenario | Erwartung | DRIVE |
|----------|-----------|--------|
| Anschaffung 15.3.2024, AK 72.000 €, Stichtag 1.3.2024 | 1 Monat AfA → 71.000 € | 71.000 € |
| Stichtag 1.4.2024 | 2 Monate → 70.000 € | 70.000 € |
| Stichtag 1.3.2026 | 25 Monate → 47.000 € | 47.000 € |
| Anschaffung 1/2018, Stichtag 1/2024 (72 Monate) | Rest 0 € | 0 € |

→ Restbuchwert und implizit „AfA bisher“ (AK − Restbuchwert) sind damit rechnerisch korrekt.

---

## 3. Besonderheiten

- **Tageszulassung:** Fahrzeuge mit `tageszulassung = true` werden in der Monatsberechnung und bei AfA-Summen **nicht** berücksichtigt (keine AfA).
- **Abgang:** In der Monatsberechnung werden nur Fahrzeuge gebucht, die im jeweiligen Monat noch aktiv sind (`anschaffungsdatum <= Monatsende`, `abgangsdatum` leer oder >= Monatsanfang). Abgangsmonat zählt damit voll (letzter Monat wird noch abgeschrieben).
- **Buchungslogik:** Pro Monat wird genau **ein** AfA-Betrag (= `afa_monatlich`) gebucht; anteilige erste/letzte Monate werden **nicht** gebildet (volle Monate, wie mit Buchhaltung vereinbart).

---

## 4. Abgleich mit Buchhaltung

- Nutzungsdauer 72 Monate entspricht dem Feedback der Buchhaltung (keine abweichende Nutzungsdauer in den Excel-Listen gefunden).
- Konten und Buchungslogik (Soll/Haben, 090301/090302/090401/090402 etc.) sind in `AFA_BUCHHALTUNG_FEEDBACK.md` abgebildet.

---

**Fazit:** Die AfA-Ermittlung in DRIVE (Restbuchwert, AfA bisher, monatliche AfA) ist fachlich korrekt. Die Differenz zu den Locosoft-Guthaben kommt daher, dass in Locosoft bisher pauschal abgeschrieben wurde und die Pauschalen nicht den in DRIVE kalkulierten Einzel-AfA entsprechen.

**Verkaufspreisempfehlung:** Die Gesamtdifferenz (DRIVE-Summe Restbuchwerte minus Buchhaltungs-Guthaben) kann in den **Verkaufsempfehlungen** berücksichtigt werden: Umgebungsvariable **AFA_DIFFERENZ_DRIVE_LOCOSOFT** (€, positiv). Pro Fahrzeug wird ein anteiliger **Aufschlag** (nach Buchwert) berechnet – so viel Aufschlag wäre nötig, um den „echten“ Buchgewinn (bezogen auf DRIVE) beim Verkauf wenigstens zu realisieren. Ohne Setzen der Variable bleibt der Aufschlag 0.
