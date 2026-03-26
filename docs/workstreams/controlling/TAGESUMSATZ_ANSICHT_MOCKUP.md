# Tagesumsatz-Ansicht – Mockup & Design

**Stand:** 2026-02-26  
**Workstream:** Controlling  

## Ziel

Zusätzliche Ansicht **Tagesumsatz** im Portal, damit du nicht jedes Mal in Locosoft (272/273) filtern musst. Die **TEK bleibt unberührt** (Buchungsdatum/FIBU); die Tagesumsatz-Ansicht nutzt **Rechnungsdatum** aus Locosoft-PostgreSQL (invoices, dealer_vehicles).

## Design-Orientierung (Recherche)

- **Fokus:** 3–7 KPIs, wichtigste Infos oben links, klare Hierarchie.
- **KPI-Karten:** Absolutwerte + ggf. Vergleich (Vortag/Vorwoche); klare Bezeichnungen.
- **Revenue by Category:** Umsatz nach Bereichen (Werkstatt vs. Fahrzeug) wie in 272/273.
- **Single Source of Truth:** Eine Datenquelle (Locosoft PostgreSQL), tagesaktuell.

## Mockup

- **Route:** `/controlling/tagesumsatz`
- **Template:** `templates/controlling/tagesumsatz_mockup.html`

### Inhalt

1. **Header:** Titel „Tagesumsatz“, Untertitel „Nach Rechnungsdatum (wie Locosoft 272/273)“.
2. **Datum-Filter:** Einzelnes Datum (Date-Picker), Default heute; Buttons „Aktualisieren“, „Heute“.
3. **Hinweis-Banner:** Daten aus Locosoft (Rechnungsdatum), tagesaktuell; TEK unberührt.
4. **KPI-Karten (4):**
   - Gesamtumsatz netto (inkl. Brutto-Sub)
   - Dienstleistung + ET (272): Lohn + Teile netto
   - Fahrzeug (273): NW + GW netto
   - Anzahl Rechnungen (mit Kurzaufteilung)
5. **Optional – Ertragszeile (3 Karten):** Lohn Bruttoertrag, Teile Bruttoertrag, Fahrzeug-DB (wenn API liefert).
6. **Sektion „Dienstleistung & Ersatzteile (L272PR)“:** Tabelle nach Rechnungsart (Werkstatt, Garantie, Intern, …) mit Anzahl, Lohn netto, Teile netto, Summe netto.
7. **Sektion „Fahrzeugrechnungen (L273PR)“:** Tabelle Typ (Neufahrzeug 7, Vorführ/GW/Tageszul. 8) mit Anzahl, Umsatz netto, optional DB.
8. **Optional:** Mini-Balkendiagramm „Umsatz nach Tag (letzte 7 Tage)“.

Aktuell sind **Beispieldaten** eingetragen; die API-Anbindung ist vorbereitet (TODO in `loadData()`).

## Nächste Schritte (Umsetzung)

1. **API:** `GET /api/controlling/tagesumsatz?datum=YYYY-MM-DD` implementieren.
   - Daten aus Locosoft: `invoices` (invoice_date, invoice_type, job_amount_net, part_amount_net, total_net/total_gross), `dealer_vehicles` (out_invoice_date, out_sale_price, calc_* für DB).
   - Aggregation: Summen pro Tag, Aufteilung nach invoice_type (2–6 für 272, 7/8 für 273), Anzahl Rechnungen.
2. **Frontend:** In `tagesumsatz_mockup.html` die Funktion `loadData()` mit `fetch('/api/controlling/tagesumsatz?datum=' + datum)` füllen und DOM (KPI-Karten, Tabellen) aus der Response befüllen.
3. **Navigation:** Eintrag unter Controlling (z. B. „Tagesumsatz“) – per DB-Navigation (Migration) oder Fallback-Menü.
4. **Optional:** Ertrag (Lohn/Teile Bruttoertrag) aus labours/parts + usage_value berechnen oder vereinfacht weglassen; Fahrzeug-DB aus dealer_vehicles.calc_*.

## Dateien

| Datei | Zweck |
|-------|--------|
| `templates/controlling/tagesumsatz_mockup.html` | Mockup-UI |
| `routes/controlling_routes.py` | Route `/controlling/tagesumsatz` |
| `docs/workstreams/controlling/TAGESUMSATZ_ERTRAG_LOCOSOFT_272_273_ANALYSE.md` | Datenbasis (invoices, parts, dealer_vehicles) |
| `docs/workstreams/controlling/TAGESUMSATZ_ANSICHT_MOCKUP.md` | Diese Doku |
