# AfA-Modul — Richtige Fahrzeuge aus Locosoft ermitteln

**Stand:** 2026-02-16  
**Ziel:** Kriterien und Feldabgleich, um VFW und Mietwagen aus Locosoft für den AfA-Import zu identifizieren und zu befüllen.

---

## 1. Welche Fahrzeuge zählen als VFW / Mietwagen?

### Locosoft-Kennzeichnung (Auswertung 2026-02)

| `dealer_vehicle_type` | Bedeutung (Locosoft-Konvention) | Anzahl (Beleg) |
|----------------------|----------------------------------|----------------|
| **V** | **Vorführwagen** | 484 |
| **N** | Neuwagen | 1.723 |
| **G** | Gebrauchtwagen | 1.986 |
| **D** | (z. B. Demopool) | 1.014 |
| **T** | (z. B. Tageszulassung) | 325 |

| `is_rental_or_school_vehicle` | Bedeutung | Anzahl |
|-------------------------------|-----------|--------|
| **true** | Mietwagen / Schulungsfahrzeug | 292 |
| false | Kein Mietwagen | 5.240 |

**Vorgehensweise für AfA:**

- **Vorführwagen (VFW):** `dealer_vehicle_type = 'V'` und `is_rental_or_school_vehicle = false` (reine VFW).
- **Mietwagen:** `is_rental_or_school_vehicle = true` — **nur eigene Mietwagen:** Kennzeichen enthält „X“ oder `pre_owned_car_code IN ('X', 'M')` (Jahreswagenkennzeichen; Buchhaltungs-Excel-Listen nutzen Jw-Kz „M“, Locosoft „X“ für eigene). Damit erscheinen keine Fahrzeuge, die woanders Mietwagen waren.

**Noch zu bestätigen (Buchhaltung/Florian):**  
Sind die Locosoft-Codes bei euch so belegt (V = Vorführwagen, D = …)? Gibt es weitere Typen, die als Anlagevermögen AfA-pflichtig sind?

---

## 2. Nur „aktive“ Fahrzeuge (noch im Anlagevermögen)

- **Nicht mehr buchen**, wenn bereits verkauft/ausgebucht:  
  `dealer_vehicles.deactivated_date IS NULL` und `dealer_vehicles.deactivated_by_employee_no IS NULL`.
- **Nur noch nicht verkaufte Fahrzeuge als Kandidaten:**  
  `dealer_vehicles.out_invoice_date IS NULL` (Rechnungsdatum Verkauf). Verkaufte Fahrzeuge erscheinen nicht mehr in der Kandidatenliste.

---

## 3. Feldabgleich Locosoft → `afa_anlagevermoegen`

| AfA-Feld (DRIVE)           | Locosoft-Quelle | Tabelle        | Hinweis |
|---------------------------|------------------|----------------|---------|
| `vin`                     | `vin`            | `vehicles`     | Join über `vehicle_number` = `vehicles.internal_number` |
| `kennzeichen`             | `license_plate`  | `vehicles` oder `dealer_vehicles.out_license_plate` | |
| `fahrzeug_bezeichnung`    | `free_form_model_text` / `models.description` | `vehicles` + `models` | Modell/Bezeichnung |
| `marke` / `modell`        | `makes.name`, `models.description` | `vehicles` → `makes` / `models` | Optional |
| `fahrzeugart`             | abgeleitet       | —             | `'VFW'` wenn Typ V (und nicht Mietwagen), sonst `'MIETWAGEN'` wenn `is_rental_or_school_vehicle` |
| `betriebsnr`              | `subsidiary`     | `vehicles` / `dealer_vehicles.in_subsidiary` | 1 = DEG Opel, 2 = HYU, 3 = LAN |
| `anschaffungsdatum`       | **siehe unten**  | `dealer_vehicles` / `vehicles` | Siehe Abschnitt 4 |
| `anschaffungskosten_netto`| **siehe unten**  | `dealer_vehicles` | Siehe Abschnitt 5 |
| `locosoft_fahrzeug_id`    | `dealer_vehicle_number` oder `vehicle_number` (internal_number) | `dealer_vehicles` | Eindeutige Referenz zurück zu Locosoft |

**Join:**  
`dealer_vehicles.vehicle_number = vehicles.internal_number` (und ggf. `dealer_vehicle_type` / `dealer_vehicle_number` übereinstimmend).

---

## 4. Anschaffungsdatum („Zulassung als VFW/Mietwagen“)

Mögliche Quellen in Locosoft:

| Feld | Tabelle         | Bedeutung |
|------|-----------------|-----------|
| `in_arrival_date` | `dealer_vehicles` | Ankunft/Eingang beim Händler |
| `first_registration_date` | `vehicles` | Erstzulassung |
| `in_accounting_document_date` | `dealer_vehicles` | Buchungsdatum (FIBU) |

**Empfehlung:** Für AfA „Zulassung als VFW/Mietwagen“ fachlich klären:  
Entweder **Ankunft** (`in_arrival_date`) oder **Buchungsdatum** (`in_accounting_document_date`). Wenn Locosoft ein explizites „Datum Umstellung auf VFW/Mietwagen“ hat, das nutzen.

---

## 5. Anschaffungskosten netto (EK netto) — geklärt

In der Locosoft-UI entspricht der **„Einsatzwert des Fahrzeugs (ohne Steuer)“** auf dem Reiter **Kalkulation** dem EK netto. Dieser Wert liegt in der Locosoft-DB in den Kalkulationsfeldern von `dealer_vehicles` — **dieselbe Logik wie bei der DB1-/Profitabilitäts-Berechnung**.

### Locosoft-Felder (SSOT im Projekt: `api/kalkulation_helpers.py` → `sql_ek_netto()`)

| Locosoft-Feld | Bedeutung (UI „Kalkulation“) |
|---------------|-----------------------------|
| `calc_basic_charge` | Fahrzeuggrundpreis |
| `calc_accessory` | Zubehör bei Anlieferung |
| `calc_extra_expenses` | Fracht/Brief/Nebenkosten |
| **`calc_usage_value_encr_internal`** | **Einsatzerhöhung interne Rechnungen** |
| `calc_usage_value_encr_external` | Einsatzerhöhung externe Rechnungen |
| `calc_usage_value_encr_other` | sonstige Einsatzwerterhöhungen |
| `calc_total_writedown` | kumulierte Abschreibungssumme |

**Formel für Anschaffungskosten_netto (AfA) = Einsatzwert ohne Steuer:**

```text
anschaffungskosten_netto =
  calc_basic_charge + calc_accessory + calc_extra_expenses
  + calc_usage_value_encr_internal + calc_usage_value_encr_external + calc_usage_value_encr_other
  - calc_total_writedown
```

**Referenz im Projekt:**  
- `api/kalkulation_helpers.py`: `sql_ek_netto(alias)` (nutzt internal + external; `_other` optional ergänzbar).  
- `scripts/sync/sync_sales.py`: „Einsatzerhöhung interne Rechnungen“ = `calc_usage_value_encr_internal` (TAG83).  
- DB1/Profitabilität: EK netto = dieselbe Formel (siehe z. B. `docs/DB_BERECHNUNG_KORREKTUR_TAG199.md`).

**Validierung an drei Vorführwagen (Locosoft-DB-Abfrage mit obiger Formel):**

| Kom.-Nr. | Einsatzwert (UI) | In DB (Formel inkl. usage_value_encr_*) |
|----------|------------------|----------------------------------------|
| V 211198 | 40.839,91 € | 40.839,91 € ✓ |
| V 111454 | 29.999,85 € | 29.999,85 € ✓ |
| V 111613 | 27.547,24 € | 27.547,24 € ✓ |

---

## 6. Nächste Schritte (technisch)

1. **Codes bestätigen:** Mit Florian/Buchhaltung abgleichen: V = Vorführwagen, D/T = …, und ob alle AfA-relevanten Fahrzeuge über `dealer_vehicle_type` + `is_rental_or_school_vehicle` abgedeckt sind.
2. **Anschaffungsdatum:** Entscheidung, welches Locosoft-Feld = „Zulassung als VFW/Mietwagen“ (z. B. `in_arrival_date` oder `in_accounting_document_date`).
3. **Anschaffungskosten_netto:** Klären, ob ein Locosoft-Feld als EK netto genutzt werden kann; wenn nein, EK weiter manuell in DRIVE pflegen.
4. **Import-Baustein:** Sobald 1–3 feststehen, in DRIVE z. B. einen „Import aus Locosoft“ (Button/API/Celery) umsetzen:  
   - Abfrage auf `dealer_vehicles` + `vehicles` mit obigen Filtern,  
   - Zuordnung zu VFW vs. MIETWAGEN,  
   - Befüllung von `afa_anlagevermoegen` inkl. `locosoft_fahrzeug_id`;  
   - **anschaffungskosten_netto** ggf. aus Locosoft, sonst leer lassen und manuell nachpflegen.

---

## 7. Beispiel-SQL (Locosoft) — Kandidaten für AfA

```sql
-- Vorführwagen (V, nicht Mietwagen)
SELECT dv.dealer_vehicle_type, dv.dealer_vehicle_number, dv.vehicle_number,
       dv.in_arrival_date, dv.in_buy_list_price, dv.in_acntg_cost_unit_new_vehicle,
       dv.is_rental_or_school_vehicle, dv.in_subsidiary
FROM dealer_vehicles dv
WHERE dv.dealer_vehicle_type = 'V'
  AND (dv.deactivated_date IS NULL AND dv.deactivated_by_employee_no IS NULL)
  AND dv.is_rental_or_school_vehicle = false;

-- Mietwagen (is_rental_or_school_vehicle = true)
SELECT dv.dealer_vehicle_type, dv.dealer_vehicle_number, dv.vehicle_number,
       dv.in_arrival_date, dv.in_buy_list_price, dv.in_acntg_cost_unit_new_vehicle,
       dv.in_subsidiary
FROM dealer_vehicles dv
WHERE dv.is_rental_or_school_vehicle = true
  AND (dv.deactivated_date IS NULL AND dv.deactivated_by_employee_no IS NULL);
```

Join mit `vehicles` für VIN, Kennzeichen, Modell:

```sql
SELECT v.vin, v.license_plate, v.internal_number, v.first_registration_date,
       v.free_form_make_text, v.free_form_model_text, v.subsidiary,
       dv.dealer_vehicle_number, dv.in_arrival_date, dv.in_buy_list_price,
       dv.in_acntg_cost_unit_new_vehicle, dv.is_rental_or_school_vehicle
FROM dealer_vehicles dv
JOIN vehicles v ON v.internal_number = dv.vehicle_number
  AND v.dealer_vehicle_type = dv.dealer_vehicle_type
  AND v.dealer_vehicle_number = dv.dealer_vehicle_number
WHERE (dv.dealer_vehicle_type = 'V' AND dv.is_rental_or_school_vehicle = false)
   OR dv.is_rental_or_school_vehicle = true
  AND (dv.deactivated_date IS NULL AND dv.deactivated_by_employee_no IS NULL);
```

Damit habt ihr die **Liste der richtigen Fahrzeuge** aus Locosoft; für die AfA-Buchung fehlen noch die verbindlichen Festlegungen zu Anschaffungsdatum und Anschaffungskosten_netto (Abschnitte 4 und 5).
