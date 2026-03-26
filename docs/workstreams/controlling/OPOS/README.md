# OPOS – Offene Posten (Locosoft-Export & DRIVE-Abfrage)

**Ordner:** Locosoft-OPOS-Exporte (CSV/XLS) und Referenz für die DRIVE-Abfrage.

## Locosoft-Report L362PR

- **Titel:** „Ausdruck unausgeglichener Personenkonten“ (Unausgeglichene Personenkonten)
- **Dialog:** Personenkonto 10000–9999999, Kunden + Lieferanten, Stichtag, optional „von Rg. schreibendem Mitarbeiter“, Ausgabeform z. B. Microsoft Excel.
- **Export:** z. B. `Loco-Soft_OPOS-Export_per19-02-26.csv` / `.xls` (Stichtag im Dateinamen).

## Spalten-Mapping Locosoft → DRIVE

| Locosoft (CSV/Excel) | DRIVE / FIBU |
|---------------------|--------------|
| **Nummer** | `customer_number` (Personenkonto = Debitoren-/Kreditorenkonto) |
| **Name** (Kunde/Lieferant) | `loco_customers_suppliers` (family_name, first_name) |
| **Rechnungsnummer** | `journal_accountings.invoice_number` |
| **Rechnungsdatum** | `journal_accountings.invoice_date` |
| **Mitarbeiter** | `journal_accountings.employee_number` (= „Rg. schreibender Mitarbeiter“) → Verkäufername über `employees.locosoft_id` |
| **Postensaldo** / Betrag | Saldo aus Soll/Haben je Position; in FIBU `posted_value` in **Cent** |

## DRIVE-Abfrage

- **Skript:** `scripts/sql/offene_posten_fahrzeugverkauf.sql`
- **Ansprechpartner (Verkäufer/Rechnungsersteller):**
  - **Fahrzeugverkauf:** Verkäufer aus **Ablieferung** (Tabelle `sales`: Match Rechnungsnr+Datum oder Kunde+Datum). Bei Fz-Verkauf schreibt der Verkäufer die Rechnung nicht – die Info steht nur in der Verkaufs-Rechnung; Locosoft-OPOS hat sie nicht.
  - **Sonstige Rechnungen** (Werkstatt, Teile, …): **Rechnungsersteller** aus FIBU `employee_number` (= „Mitarbeiter“ wie im Locosoft-Export).
- Spalte **ist_fahrzeugverkauf** (true/false) kennzeichnet, ob die Zuordnung aus `sales` kam.
- **Debitorenbereich** in der Abfrage: 150000–199999 (Forderungen). Locosoft-Dialog nutzt 10000–9999999 (alle Personenkonten); bei Bedarf in der SQL anpassen.

## Dateien in diesem Ordner

- `Loco-Soft_OPOS-Export_per19-02-26.csv` – Beispiel-Export per 19.02.26
- Screenshot Locosoft-UI: siehe Sync-Ordner (gleichnamig im Windows-Sync unter `docs/workstreams/controlling/OPOS/`)
