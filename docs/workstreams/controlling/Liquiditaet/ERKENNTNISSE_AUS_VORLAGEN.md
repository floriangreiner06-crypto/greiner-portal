# Erkenntnisse aus den Excel-Vorlagen zur Liquiditätsplanung

**Stand:** 2026-03  
**Quelle:** Kollegen-Vorlagen im Ordner `docs/workstreams/controlling/Liquiditaet/`  
- `2025-08-15_Liquiditätsplan Woche.xlsx`  
- `2025-08-15_Master Liqui-Plan.xlsx`

---

## 1. Liquiditätsplan Woche (wöchentliche Planung)

### Aufbau

- **Zeitachse:** Spalten = **Wochen** (Datum pro Woche).
- Pro Woche je zwei Spalten: **Eingänge** und **Ausgänge** (in rd. EUR).

### Kategorien (für unsere Kategorisierung/Validierung nutzbar)

| Art | Kategorie in Vorlage | Zuordnung DRIVE / Bankenspiegel |
|-----|----------------------|----------------------------------|
| **Eingänge** | NW Auslieferg. | Fahrzeugverkauf Neuwagen (Zahlungseingang) |
| | Vfwg. Zul. | Vorführwagen Zulassung / Verkauf |
| | GW Auslief. | Gebrauchtwagen Auslieferung |
| | GW Auslief. Autoverleih | Auslieferung Autoverleih |
| | sonstige Eingänge | Sonstige Einnahmen |
| **Ausgänge** | Restgehalt/Gehälter | Personal |
| | Sozialvers. | Personal / Sozialversicherung |
| | Steuer | Steuern |
| | Lieferanten | Lieferanten |
| | Werk./T+Z | Werkstatt / Teile+Zubehör (Betrieb) |
| | GW Einkauf Nehlsen/Leasing | Einkauf GW / Leasing |
| | Vers.etc | Versicherung etc. (Betrieb) |
| | sonstige Ausgänge | Sonstige Ausgaben |

### Weitere Punkte

- **Drei Einheiten:** Autohaus, Autoverl., Verw. KG – jeweils eigener **SALDO**-Verlauf.
- **E/A** = Netto (Einnahmen − Ausgaben) pro Woche.
- Die Vorlage bestätigt: **NW/GW Auslieferung** als zentrale Einnahme-Kategorien und **Gehalt, Steuer, Lieferanten, Werkstatt, Versicherung** als Ausgaben – deckungsgleich mit unserer Transaktions-Kategorisierung und mit erwarteten Einnahmen aus Fahrzeugverkauf.

**Erkenntnis für DRIVE:** Wöchentliche Aggregation nach diesen Kategorien (bereits in Bankenspiegel vorhanden) wäre validierbar gegen die Excel-Vorlage. Optional: Ansicht „Liquiditätsplan Woche“ mit gleichen Kategorienamen.

---

## 2. Master Liqui-Plan (tägliche Planung, pro Standort)

### Aufbau

- **Blätter:** Grunddaten, Standort 1, Standort 2, Standort 3, Standort 4, Holding.
- **Grunddaten:** Kreditlimits pro Bank (Bank 1–8) und pro **Standort**, in T€. Summe „gesamtes Kreditlimit“.
- **Pro Standort:** Planung **täglich** (Montag–Sonntag, dann Folgewoche). Zeilen:
  - **Saldo zum Tagesbeginn**
  - **Einnahmen:** Debitoren, Verbund, Hersteller Bank 1/2, Schecks, Geldverkehr → **Summe Einnahmen**
  - **Ausgaben:** Lohn/Gehalt, Lohnsteuer, Sozialversicherung, Mieten, **Ablösung Fzge**, Hersteller Bank, Kreditoren → Summe Ausgaben

### Wichtige Erkenntnis: „Ablösung Fzge“

- In der Vorlage ist **„Ablösung Fzge“** (Ablösung Fahrzeuge) explizit als **Ausgaben**-Position geführt.
- Das entspricht genau der in unserer Doku beschriebenen **Ablösung der Einkaufsfinanzierung** bei Verkauf einfinanzierter Fahrzeuge: Verkaufserlös (Einnahme) und Ablöse (Ausgabe) müssen beide geplant werden.

**Erkenntnis für DRIVE:** In der Liquiditätsvorschau und bei „Erwartete Einnahmen Fahrzeug“ müssen wir **Ablösung Fzge** (aus `fahrzeugfinanzierungen.aktueller_saldo`) weiterhin als eigene Ausgabe abbilden bzw. als Netto (Verkaufserlös − Ablöse) ausweisen, damit die Planung mit der Vorlage vergleichbar ist.

### Weitere Kategorien im Master

| Vorlage | DRIVE / Anmerkung |
|---------|--------------------|
| Debitoren | OPOS / Forderungseingänge; erwartete Einnahmen aus Rechnungen |
| Verbund | Verbund-/Konzerntransfers |
| Hersteller Bank 1/2 | Hersteller-Zahlungen (z. B. Stellantis, Santander – eher Ausgaben Tilgung) |
| Lohn/Gehalt, Lohnsteuer, Sozialvers. | Personal (bereits Kategorie) |
| Mieten | Miete & Nebenkosten |
| Ablösung Fzge | EK-Finanzierung Ablöse (fahrzeugfinanzierungen) |
| Kreditoren | Lieferanten |

---

## 3. Abgeleitete Empfehlungen für DRIVE

1. **Kategorien konsistent halten**  
   Die in den Vorlagen genutzten Begriffe (NW Auslieferg., GW Auslief., Restgehalt/Gehälter, Steuer, Lieferanten, Werk./T+Z, sonstige Eingänge/Ausgänge, **Ablösung Fzge**) sollten in DRIVE entweder 1:1 vorkommen oder klar zuordenbar sein (z. B. „Einkaufsfinanzierung“ für Ablösung Fzge), damit ein Abgleich mit der Excel-Planung möglich ist.

2. **Ablösung Fahrzeuge explizit**  
   Bei erwarteten Einnahmen aus Fahrzeugverkauf: wie bereits dokumentiert **einfinanzierte Fahrzeuge** prüfen und **Ablösebetrag** (aktueller_saldo) als Ausgabe oder als Netto (Verkauf − Ablöse) abbilden. Die Vorlage bestätigt „Ablösung Fzge“ als eigene Planungsposition.

3. **Optional: wöchentliche Ansicht**  
   Analog „Liquiditätsplan Woche“ eine Ansicht „Pro Woche“ mit Eingänge/Ausgaben nach gleichen Kategorien anbieten (Daten aus Bankenspiegel + erwartete Bewegungen), zur Validierung gegen die Excel-Vorlage.

4. **Optional: Kreditlimits / Standorte**  
   Der Master enthält Kreditlimits pro Bank und Standort. Wenn DRIVE Konten/Banken den Standorten zugeordnet werden und Kreditlinien gepflegt werden, könnte eine Anzeige „Verfügbare Linie“ pro Standort oder gesamt die Vorlage ergänzen (thematisch in `bankenspiegel_api` / Konten bereits angelegt).

5. **Tagesgenaue Planung**  
   Der Master plant **täglich** (Saldo Tagesbeginn, Einnahmen, Ausgaben, Saldo Ende). Unsere aktuelle Vorschau ist bereits tagesbasiert; die Vorlage bestätigt, dass die Granularität „Tag“ und die Trennung Einnahmen/Ausgaben pro Tag sinnvoll ist.

---

## 4. Dateien im Repo

- `2025-08-15_Liquiditätsplan Woche.xlsx` – wöchentliche Planung, Kategorien Eingänge/Ausgänge, Autohaus/Autoverl./Verw. KG.
- `2025-08-15_Master Liqui-Plan.xlsx` – Grunddaten (Kreditlimits), Standort 1–4 + Holding, tägliche Planung inkl. „Ablösung Fzge“.

Beide liegen unter `docs/workstreams/controlling/Liquiditaet/` und können für Abgleich und Validierung der DRIVE-Liquiditätsvorschau genutzt werden.
