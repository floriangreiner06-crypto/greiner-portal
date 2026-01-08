# Stundensatz-Kalkulation Template (Befüllt mit BWA-Daten)
## TAG 169: Template für genauere Werkstatt-Planung

**Erstellt:** 2026-01-07 17:20:44

### BWA-Daten (Vorjahr 2024/25)

#### Standort 1: Deggendorf

| Kennzahl | Wert |
|----------|------|
| **Umsatz (Jahr)** | 1,463,200.52 € |
| **Einsatz (Jahr)** | 779,722.65 € |
| **DB1 (Jahr)** | 683,477.87 € |
| **Variable Kosten (Jahr)** | 222,242.14 € |
| **Direkte Kosten (Jahr)** | 248,563.07 € |
| **DB2 (Jahr)** | 212,672.66 € |
| **Stunden verkauft (Jahr)** | 13,222.32 h |
| **Stundensatz** | 110.66 €/h |
| **Kosten pro Stunde** | 35.61 €/h |
| **DB1 pro Stunde** | 51.69 €/h |
| **DB2 pro Stunde** | 16.08 €/h |

#### Standort 2: Hyundai DEG

| Kennzahl | Wert |
|----------|------|
| **Umsatz (Jahr)** | 491,576.24 € |
| **Einsatz (Jahr)** | 273,285.69 € |
| **DB1 (Jahr)** | 218,290.55 € |
| **Variable Kosten (Jahr)** | 85,898.54 € |
| **Direkte Kosten (Jahr)** | 115,570.91 € |
| **DB2 (Jahr)** | 16,821.10 € |
| **Stunden verkauft (Jahr)** | 9,231.92 h |
| **Stundensatz** | 53.25 €/h |
| **Kosten pro Stunde** | 21.82 €/h |
| **DB1 pro Stunde** | 23.65 €/h |
| **DB2 pro Stunde** | 1.82 €/h |

#### Standort 3: Landau

| Kennzahl | Wert |
|----------|------|
| **Umsatz (Jahr)** | 1,954,776.76 € |
| **Einsatz (Jahr)** | 1,053,008.34 € |
| **DB1 (Jahr)** | 901,768.42 € |
| **Variable Kosten (Jahr)** | 308,140.68 € |
| **Direkte Kosten (Jahr)** | 364,133.98 € |
| **DB2 (Jahr)** | 229,493.76 € |
| **Stunden verkauft (Jahr)** | 13,222.32 h |
| **Stundensatz** | 147.84 €/h |
| **Kosten pro Stunde** | 50.84 €/h |
| **DB1 pro Stunde** | 68.20 €/h |
| **DB2 pro Stunde** | 17.36 €/h |

### Excel-Struktur

#### Sheet: Externer Verrechnungssatz

| Zeile | Spalte | Wert |
|-------|--------|------|
| 1 | A | Berechnung des Stundenverrechnungssatzes für Autoh |
| 3 | B | Kosten des Unternehmens pro Jahr |
| 4 | C | € |
| 5 | A | + |
| 5 | B | Löhne, Gehälter, Sozialabgaben |
| 5 | C | 54100.0 |
| 6 | A | + |
| 6 | B | Lieferanten |
| 7 | A | + |
| 7 | B | Mieten und Nebenkosten |
| 8 | A | + |
| 8 | B | Büro und Verwaltungskosten |
| 8 | C | 71960.0 |
| 9 | A | + |
| 9 | B | Provisionen / Gratifikationen |
| 10 | A | + |
| 10 | B | Training/Weiterbildung |
| 11 | A | + |
| 11 | B | Leerlauf produktive MA/ entgangene ER |
| 12 | A | + |
| 12 | B | Werkstattwagen |
| 13 | A | + |
| 13 | B | Werbung/Verkaufsförderung |
| 14 | A | + |
| 14 | B | Garantie |
| 15 | A | + |
| 15 | B | Kulanz |
| 16 | A | + |
| 16 | B | Frachtkosten |
| 17 | A | + |
| 17 | B | Hilfs- und Betriebsstoffe |
| 18 | A | + |
| 18 | B | Werkzeuge/Kleinteile |
| 19 | A | + |
| 19 | B | Entsorgung/Recycling |
| 20 | A | + |
| 20 | B | Instandhaltung |
| 21 | A | + |
| 21 | B | Aufw. für Diagnosegeräte |
| 22 | A | + |
| 22 | B | Sonstige Kosten |
| 22 | C | 65000.0 |
| 23 | A | = |
| 23 | B | Gesamt Kosten |
| 23 | C | 191060.0 |
| 26 | B | Berechnung der fakturierfähigen Tage |
| 26 | E | Stundenverrechnunngssatz |
| 28 | B | Tage im Jahr |
| 28 | C | 365.0 |
| 28 | E | 80.27731092436976 |
| 29 | A | - |
| 29 | B | Samstage und Sonntage |
| 29 | C | 104.0 |
| 30 | A | - |
| 30 | B | Feiertage |
| 30 | C | 9.0 |
| 31 | A | - |
| 31 | B | Urlaubstage |
| 31 | C | 30.0 |
| 32 | A | - |
| 32 | B | Krankheit bedingte Ausfalltage/Schulungstage |
| 32 | C | 12.0 |
| 33 | A | = |
| 33 | B | tatsächliche Arbeitstage (Anwesenheitstage) |
| 33 | C | 210.0 |
| 36 | B | Berechnung der fakturierfähigen Stunden |

