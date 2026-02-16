# AfA-Modul Vorführwagen/Mietwagen — Discovery

**Stand:** 2026-02-16  
**Workstream:** Controlling

## 1. DRIVE Portal DB — Fahrzeugbezogene Tabellen

Abgefragt: Tabellen mit `%fahr%`, `%vehicle%`, `%vfw%`, `%miet%`.

**Gefundene Tabellen (Auszug):**
- `fahrzeugfinanzierungen` — EK-Finanzierungen (Zinsen, Verträge), **keine** explizite VFW/Mietwagen-Kennzeichnung
- `fahrzeuge_mit_zinsen` — abgeleitete View/Liste
- `dealer_vehicles`, `vehicles` — vermutlich Locosoft-Spiegel
- `loco_vehicles`, `loco_dealer_vehicles`, `loco_*` — Locosoft-Stammdaten

**Struktur `fahrzeugfinanzierungen`:**
- Enthält: `vin`, `vin_kurz`, `hersteller`, `modell`, `vertragsbeginn`, `lieferdatum`, `aktivierungsdatum`, `rechnungsbetrag`, `aktiv`, etc.
- **Kein** Feld für Fahrzeugart (VFW/Mietwagen) oder Anlagevermögen.
- Eignet sich als **Referenz** (finanzierung_id) für verknüpfte AfA-Posten, nicht als SSOT für VFW/Mietwagen-Liste.

**Fazit:** In der DRIVE Portal DB gibt es **keine** bestehende Tabelle, die VFW/Mietwagen als Anlagevermögen mit AfA abbildet. Neuanlage der Tabelle `afa_anlagevermoegen` ist erforderlich.

---

## 2. Locosoft — Fahrzeugart / Verwendungszweck

**Tabellen:** `vehicles`, `dealer_vehicles`, `stock` (nur columns abgefragt).

**Relevante Spalten:**
- **vehicles:** `dealer_vehicle_type`, `dealer_vehicle_number`, `first_registration_date`, `subsidiary`, `license_plate`, `vin`, `free_form_make_text`, `free_form_model_text`
- **dealer_vehicles:** `dealer_vehicle_type`, `vehicle_number`, `location`, `in_arrival_date`, `is_rental_or_school_vehicle`, `calc_total_writedown`, `in_buy_list_price`, diverse `in_*`/`out_*` Felder

**Fahrzeugart / Verwendungszweck:**
- `dealer_vehicle_type` — Unterscheidung Vorführwagen vs. andere (Typen je nach Locosoft-Konvention)
- `is_rental_or_school_vehicle` — Kennzeichnung Mietwagen/Schulungsfahrzeug

**Fazit:** Locosoft enthält die Information, ob ein Fahrzeug VFW oder Mietwagen ist. Eine spätere Anreicherung oder ein Import aus Locosoft (z.B. Stammdaten EK, Zulassungsdatum) ist möglich. Für die erste Version des AfA-Moduls werden die Daten **manuell in DRIVE** gepflegt; optional kann ein Abgleich mit Locosoft (z.B. über VIN) ergänzt werden.

---

## 3. FIBU — Konten 444xxx (kalkulatorische Abschreibungen)

**Tabelle:** `fibu_buchungen` (Spalten: `nominal_account`, `amount`, `debit_credit`, `posting_text`, `accounting_date`, …).  
Es gibt **keine** Spalte `description`; verwendet wurde `posting_text`.

**Ergebnis der Abfrage (444000–444999):**
- Konten **444001**, **444002** etc. sind belegt.
- Beispiele: `posting_text` wie „WKB 01/2025“, „WKB 02/24“, „Auflösung kalk. Kosten“, „Nachbuchungen 31.08.24“.
- Beträge pro Buchung in Cent (amount/100 = Euro), Soll/Haben über `debit_credit`.

**Fazit:** Der Bereich 444xxx wird für kalkulatorische Abschreibungen genutzt und ist in der BWA-Kategorisierung bereits berücksichtigt. Das AfA-Modul liefert die **Buchungsliste** (Beträge pro Monat/Fahrzeug); das konkrete **Sachkonto** (z.B. 4440xx für VFW/Mietwagen) muss mit der Buchhaltung (Florian) geklärt werden.

---

## 4. Zusammenfassung für die Umsetzung

| Aspekt | Befund |
|--------|--------|
| **SSOT VFW/Mietwagen-Liste** | Nicht vorhanden → neue Tabelle `afa_anlagevermoegen` in DRIVE |
| **Referenz Finanzierung** | Optional: `fahrzeugfinanzierungen.id` → `afa_anlagevermoegen.finanzierung_id` |
| **Referenz Locosoft** | Optional: `locosoft_fahrzeug_id` für Abgleich mit Locosoft |
| **FIBU 444xxx** | Vorhanden und genutzt; AfA-Modul liefert Buchungsliste für Einbuchung in Locosoft |
| **Sachkonto AfA** | Noch mit Buchhaltung klären |

---

## 5. Nächste Schritte

1. Migration `afa_anlagevermoegen` + `afa_buchungen` ausführen.
2. API und Berechnungslogik (linear, 72 Monate, monatsgenau) implementieren.
3. Dashboard, Monatsübersicht und Buchungsliste bereitstellen.
4. Optional: Celery-Task für monatliche AfA-Berechnung; Klärung Sachkonto 444xxx für VFW/Mietwagen.
