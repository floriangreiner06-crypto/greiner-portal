# Profitabilitäts-Dashboard – KPI-Quellen

**Stand:** TAG 219 (Phase 1)  
**Gültig für:** `verkauf_profitabilitaet_mockup.html` / zukünftiges Template

---

## Übersicht: Woher kommen die Daten?

| KPI / Anzeige | Quelle | Details |
|---------------|--------|---------|
| **Verkaufte Fz** (Anzahl) | Locosoft | Zählung `dealer_vehicles` mit `out_invoice_date IS NOT NULL` + Filter Monat/Jahr + Standort (`out_subsidiary`) |
| **∅ DB pro Fz** | Locosoft (berechnet) | DB1 aus Kalkulation (VK_netto − EK − variable Kosten + VKU); Durchschnitt über alle verkauften Fz des Zeitraums |
| **∅ Standzeit** | Locosoft (berechnet) | `standzeit_tage = out_invoice_date − COALESCE(in_arrival_date, created_date)`; Durchschnitt über alle verkauften Fz |
| **∅ DB nach Standkosten** | Locosoft + Formel | DB1 − Standkosten pro Fz; Durchschnitt. Standkosten = Zinsen + Pauschale (siehe unten) |

---

## Einzelfahrzeug (Tabelle)

| Spalte | Quelle | Technisch |
|--------|--------|-----------|
| Kom.Nr | Locosoft | `dealer_vehicles.dealer_vehicle_number` (+ `dealer_vehicle_type` als Präfix G/N/D) |
| Modell | Locosoft | `vehicles.free_form_model_text` oder `models.description` |
| Kennz. | Locosoft | `vehicles.license_plate` |
| Typ | Locosoft | `dealer_vehicle_type` → NW/GW/VFW (N/G/D) |
| Standzeit | Locosoft | `out_invoice_date − COALESCE(in_arrival_date, created_date)` [Tage] |
| EK | Locosoft | Einsatzwert netto: `calc_basic_charge + calc_accessory + calc_extra_expenses + calc_usage_value_encr_internal + calc_usage_value_encr_external` |
| VK | Locosoft | `out_sale_price` (brutto) |
| DB1 | Locosoft (berechnet) | Wie in `fahrzeug_data`/`kalkulation_helpers`: VK_netto − EK − variable Kosten + VKU (Besteuerung Regel vs. Diff §25a) |
| Standkosten | Formel | `standkosten_zins + standkosten_pauschal` (siehe unten) |
| DB netto | Formel | `DB1 − standkosten_gesamt` |
| DB % | Formel | `(db_nach_standkosten / vk_brutto) × 100` |
| Verkäufer | Locosoft | `dealer_vehicles.out_salesman_number_1` → JOIN `employees_history.employee_number` → `name` |

---

## Standkosten (Formel, keine eigene Tabelle in Phase 1)

- **Standkosten Zinsen:**  
  `ek_netto × ZINSSATZ_JAHR × (standzeit_tage / 365)`  
  (ZINSSATZ_JAHR = 0,05)
- **Standkosten Pauschale:**  
  `standzeit_tage × TAGESSATZ_PAUSCHAL`  
  (TAGESSATZ_PAUSCHAL = 12 €/Tag; Versicherung, Platz, Marketing, Aufbereitung)
- **Standkosten gesamt:**  
  `standkosten_zins + standkosten_pauschal`

*(Optional später: echte Zinsen aus DRIVE `fahrzeugfinanzierungen` pro VIN – Phase 1 nutzt die Formel.)*

---

## Trend-Chart (12 Monate)

| Datenreihe | Quelle |
|------------|--------|
| DB1 | Aggregation aus Locosoft-Kalkulation pro Monat (Summe oder ∅ pro Fz) |
| DB nach Standkosten | Wie oben, nach Abzug Standkosten pro Fz |
| Standzeit | ∅ Standzeit pro Monat (Locosoft) |

Abfrage: `get_profitabilitaet_trend(year, standort)` → 12 Monate.

---

## Verkäufer-Ranking

| Anzeige | Quelle |
|---------|--------|
| Verkäufername | Locosoft `employees_history` (über `out_salesman_number_1`) |
| DB netto pro Verkäufer | Summe (DB1 − Standkosten) aller verkauften Fz des Verkäufers im gewählten Monat/Jahr/Standort |

Abfrage: `get_verkaeufer_profitabilitaet(month, year, standort)`.

---

## Benchmark-Box

| KPI | Quelle | Anmerkung |
|-----|--------|-----------|
| Eure ∅ Standzeit | Wie oben (Locosoft + Formel) | |
| Branche 65 Tage | Konstante / Doku | ZDK Best Practice, nur Anzeige |
| Eurer DB-Anteil am VK | `(Summe DB1 / Summe VK brutto) × 100` oder ∅ pro Fz | Aus Locosoft-Kalkulation |
| Branche >10 % | Konstante / Doku | Nur Anzeige |
| Anteil Fz mit DB > 0 | Zählung aus Locosoft-Daten | Berechnet aus Ergebnismenge |
| Anteil Standzeit <65 Tage | Zählung aus Locosoft-Daten | Berechnet aus Ergebnismenge |

---

## Datenbanken im Überblick

| System | Verwendung |
|--------|------------|
| **Locosoft** (PostgreSQL, read-only) | `dealer_vehicles`, `vehicles`, `models`, `dealer_sales_aid`, `employees_history` – alle Fahrzeug- und Kalkulationsdaten |
| **DRIVE Portal** (PostgreSQL) | Phase 1: nicht zwingend. Optional: `fahrzeugfinanzierungen` für echte Zinsen pro VIN (kann später Standkosten verfeinern) |

Alle in der Tabelle und den Karten dargestellten KPIs kommen in Phase 1 aus **Locosoft** (Rohdaten + Kalkulation wie in `fahrzeug_data`/`kalkulation_helpers`) plus der **Standkosten- und Netto-DB-Formel** im Backend.
