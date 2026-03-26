# Liquiditätsvorschau: Erwartete Einnahmen aus Fahrzeugverkauf & Werkstatt (Locosoft)

**Workstream:** Controlling  
**Stand:** 2026-03  
**Frage:** Erwartete Einnahmen aus Aufträgen/Rechnungen „aus der Zukunft“ (Fahrzeugverkauf) und Locosoft-Werkstattaufträgen in die Liquiditätsvorschau einbeziehen – mit Auf-/Abschlag auf den Schnitt. Geht das?

---

## Kurzantwort: **Ja, das geht**

Die Daten sind in Locosoft vorhanden. Wir können:

1. **Fahrzeugverkauf:** Aufträge (noch nicht in Rechnung gestellt) und/oder Rechnungen mit (erwartetem) Zahlungseingang in der Projektionsperiode heranziehen und mit einem konfigurierbaren Auf- oder Abschlag (z. B. 95 % = vorsichtiger Schnitt) bewerten.
2. **Werkstatt:** Locosoft-Aufträge (`orders`) mit Leistungswerten (`labours`/`parts`), die noch nicht fakturiert sind oder deren Rechnungsdatum in der Zukunft liegt, bewerten und mit Auf-/Abschlag in die Vorschau legen.

---

## 1. Fahrzeugverkauf – Daten & Logik

**Bereits in DRIVE vorhanden (noch nicht in Liquiditätsvorschau):** Das Modul **Lieferforecast** (`api/verkauf_data.py` → `get_lieferforecast`) nutzt Locosoft bereits für geplante **NW**-Auslieferungen: `vehicles.readmission_date` (Lieferdatum) + `orders`/`invoices` liefern pro Fahrzeug Datum und Netto-Erlös. TEK und Auslieferungen-Modul nutzen `dealer_vehicles` mit `out_invoice_date` (IST, fakturierte Auslieferungen). Für die Liquiditätsvorschau können wir entweder dieselbe Logik wie Lieferforecast (readmission_date + Netto) nutzen oder zusätzlich `dealer_vehicles` (Aufträge/Rechnungen in der Zukunft) wie in 1.1 beschrieben. GW: prüfen, ob Locosoft ein geplantes Lieferdatum analog zu NW führt.

### 1.1 Datenquelle Locosoft: `dealer_vehicles`

| Szenario | Bedingung | Betrag | Erwartetes Datum (Zahlungseingang) |
|----------|-----------|--------|------------------------------------|
| **Auftrag, noch nicht in Rechnung** | `out_sales_contract_date IS NOT NULL` und `out_invoice_date IS NULL` | z. B. `out_estimated_invoice_value` oder `out_sale_price_internet` (Kalkulation/Verkaufspreis) | Auftragsdatum + X Tage bis „typ. Rechnung“ + Y Tage Zahlungsziel, z. B. `out_sales_contract_date + 14 + 14` |
| **Bereits in Rechnung, Zahlung ausstehend** | `out_invoice_date` in [heute, Ende Projektion] | `out_sale_price` oder aus `invoices.total_net` | `out_invoice_date + Zahlungsziel` (z. B. +14 Tage) |

- **Auf-/Abschlag:** Ein Faktor (z. B. **0,95** = 5 % Abschlag für Aufträge, die noch storniert werden können, oder **1,0** für bereits fakturierte Verkäufe) wird auf den Betrag angewendet. Konfigurierbar pro Quelle (Auftrag vs. Rechnung).
- **Aggregation:** Pro **erwartetem Zahlungsdatum** werden alle zugehörigen Beträge (nach Auf-/Abschlag) summiert und als „Erwartete Einnahmen Fahrzeugverkauf“ in die tägliche Projektion übernommen.

### 1.2 Ist das Fahrzeug einfinanziert? – Welche Transaktionen berücksichtigen?

Bei Fahrzeugaufträgen bzw. -rechnungen in der Zukunft muss unterschieden werden, ob das Fahrzeug **einkaufsfinanziert** ist (Santander, Stellantis, Genobank, ggf. Hyundai). Nur dann ist der **Nettoliquiditätseffekt** korrekt.

| Fall | Transaktionen für Liquidität |
|------|------------------------------|
| **Nicht einfinanziert** | Nur **+ Zahlungseingang** (Verkaufserlös) am erwarteten Datum. |
| **Einfinanziert** | **+ Zahlungseingang** (Verkaufserlös) und **− Ablösung/Tilgung** der Einkaufsfinanzierung. Der **Nettoeffekt** = Verkaufserlös − Ablösebetrag (i. d. R. aktueller Saldo der Linie). |

**Datenquelle Ablöse:** Tabelle **`fahrzeugfinanzierungen`** (Portal-PostgreSQL), Schlüssel z. B. **VIN** (aus Locosoft `dealer_vehicles`/`vehicles`). Pro einfinanziertes Fahrzeug: `aktueller_saldo` = Betrag, der bei Verkauf an die Bank zurückgezahlt wird (Ablösung). Optional: `finanzinstitut` (Santander, Stellantis, Genobank) für Ausweis nach Linie.

**Logik für die Vorschau:**

1. Für jede geplante Verkaufsposition (Auftrag oder Rechnung in der Zukunft) aus Locosoft: **VIN** ermitteln.
2. In **Portal-DB** prüfen: Existiert in `fahrzeugfinanzierungen` ein aktiver Eintrag mit dieser VIN (`aktiv = true`)? Wenn **ja** → Fahrzeug ist einfinanziert; **Ablösebetrag** = `aktueller_saldo` (ggf. Summe, falls mehrere Linien pro VIN möglich).
3. **Erwarteter Zahlungseingang** (Verkaufserlös, mit Auf-/Abschlag) und **erwartetes Ablösedatum** ansetzen (z. B. gleicher Tag wie Zahlungseingang oder +1…3 Tage später, je nach Prozess).
4. In der Projektion **an diesem Tag** (oder aufgeteilt):
   - **+ Verkaufserlös** (Einnahme),
   - **− Ablösebetrag** (Ausgabe),
   - Anzeige optional als **Netto** (eine Zeile „Erw. Einnahmen Fz netto“) oder getrennt („Verkaufserlös“ / „Ablöse EK-Fin.“), damit die Validierung nachvollziehbar ist.

So werden bei Fahrzeugaufträgen/Rechnungen in der Zukunft **alle relevanten Transaktionen** berücksichtigt: Erlös und Ablöse der Einfinanzierung. Ohne Abzug der Ablöse wäre die Liquidität überzeichnet.

### 1.3 Technik

- Abfrage auf **Locosoft-PostgreSQL** (bestehende `locosoft_session()` / `get_locosoft_connection()`).
- Kein neues Datenmodell im Portal nötig; die Vorschau-API (`get_cashflow_vorschau` oder eigenes Modul) ruft bei Bedarf Locosoft ab und mergt die Zeitreihe „erwartete Einnahmen Fahrzeug“ in die bestehende Projektion (zusätzlich zum bisherigen Ø/Tag oder ersetzt diesen für die Tage, an denen konkrete Fahrzeug-Einnahmen anfallen).

---

## 2. Werkstatt – Daten & Logik

### 2.1 Datenquellen Locosoft: `orders`, `labours`, `parts`, `invoices`

| Szenario | Bedingung | Betrag | Erwartetes Datum |
|----------|-----------|--------|-------------------|
| **Auftrag, noch nicht fakturiert** | `orders.order_date` (oder `estimated_outbound_time`) in der Projektionsperiode; zugehörige `labours` mit `is_invoiced = false` | Summe `labours.net_price_in_order` (+ Teile aus `parts` je Position) pro Auftrag | z. B. `order_date + 7` (Fertigstellung) + 14 (Zahlungsziel) = erwarteter Zahlungseingang |
| **Bereits fakturiert, Rechnungsdatum in der Zukunft** | `invoices.invoice_date` in [heute, Ende] und `invoice_type` in (2,3,4,5,6) (Werkstatt) | `invoices.total_net` | `invoice_date + Zahlungsziel` |

- **Auf-/Abschlag:** Ebenfalls ein Faktor (z. B. **0,90** für noch nicht fakturierte Werkstattaufträge wegen Stornos/Rabatten, **1,0** für bereits gestellte Rechnungen).
- **Aggregation:** Pro erwartetem Zahlungsdatum Summe → „Erwartete Einnahmen Werkstatt“.

### 2.2 Technik

- Abfragen auf Locosoft: `orders` + Join auf `labours` (und ggf. `parts`) für offene Positionen; `invoices` für Werkstatt-Rechnungen mit `invoice_date` im Projektionszeitraum.
- **Zusätzlich:** Geplante/offene Aufträge sind über **Locosoft SOAP** erkennbar: `listOpenWorkOrders()` liefert die offenen Aufträge, `readWorkOrderDetails(orderNumber)` die Details (bei offenen Aufträgen ggf. Positionen; bei fakturierten in Tests teils leer). Für Umsatz/Netto ist die PostgreSQL-Quelle (`labours.net_price_in_order`) derzeit die sichere Basis. Siehe `Liquiditaet/GEPLANTE_WERKSTATTAUFTRAGE_LOCOSOFT_SOAP.md`.
- Die Werkstatt-Zeitreihe wird analog zum Fahrzeugverkauf in die Liquiditätsvorschau integriert (pro Tag: erwartete Einnahmen Werkstatt).

---

## 3. Integration in die Liquiditätsvorschau

### 3.1 Option A: Zusätzlich zum bestehenden Ø/Tag

- **Bisher:** Ein fester „Erwartete Einnahmen (Ø/Tag)“ aus den letzten 90 Tagen Bankbewegungen.
- **Erweiterung:** Pro Tag in der Projektion:
  - **Erwartete Einnahmen Fahrzeug** (aus Locosoft Aufträgen/Rechnungen) + **Erwartete Einnahmen Werkstatt** (aus Locosoft Aufträgen/Rechnungen) berechnen.
  - Wenn an einem Tag **keine** Locosoft-basierten Einnahmen anfallen: weiterhin den **Ø/Tag** verwenden (Fallback).
  - Wenn an einem Tag Locosoft-Daten anfallen: diese (mit Auf-/Abschlag) nutzen; optional den Ø-Wert für diesen Tag reduzieren oder weglassen, um Doppelzählung zu vermeiden (konfigurierbar).

### 3.2 Option B: Nur Locosoft-basierte Erwartung (konfigurierbar)

- Nur noch erwartete Einnahmen aus Fahrzeug + Werkstatt (Locosoft) in die Vorschau; der 90-Tage-Durchschnitt entfällt oder wird nur als Hinweis „Ø Einnahmen/Tag (Vergangenheit)“ angezeigt.

### 3.3 Auf-/Abschlag konfigurierbar

- **Fahrzeug Aufträge (noch nicht in Rechnung):** z. B. 0,95 (5 % Abschlag).
- **Fahrzeug Rechnungen (bereits gestellt):** z. B. 1,0.
- **Werkstatt Aufträge (noch nicht fakturiert):** z. B. 0,90 (10 % Abschlag).
- **Werkstatt Rechnungen:** z. B. 1,0.
- Speicherort: Konstante in Code oder kleine Konfigurationstabelle/Config-Datei (z. B. `config/cashflow_erwartung.py`).

---

## 4. Implementierungs-Schritte (Vorschlag)

1. **Neues Modul** (z. B. `api/cashflow_erwartung_locosoft.py`):
   - `get_erwartete_einnahmen_fahrzeug(von_datum, bis_datum, abschlag_auftrag=0.95, abschlag_rechnung=1.0)` → Zeitreihe pro Datum: **Einnahmen** (Verkaufserlös nach Auf-/Abschlag) und **Ablöse** (Summe `fahrzeugfinanzierungen.aktueller_saldo` pro VIN aus den geplanten Verkäufen). Pro Datum: VIN aus Locosoft → Abfrage Portal `fahrzeugfinanzierungen` (VIN, aktiv = true) → Ablöse = COALESCE(SUM(aktueller_saldo), 0); Netto-Einnahme Fz = Verkaufserlös − Ablöse.
   - `get_erwartete_einnahmen_werkstatt(...)` → Zeitreihe { datum: betrag }.
2. **Anbindung in `get_cashflow_vorschau`:**
   - Optionaler Parameter `mit_locosoft_erwartung=True`.
   - Aufruf der beiden Funktionen für (heute, heute + tage); Merge in `reihe[].erwartete_einnahmen_fahrzeug` und `reihe[].erwartete_einnahmen_werkstatt`; Saldo-Formel um diese Beträge erweitern.
3. **Frontend:** In der Tabelle „Erwartete Bewegungen“ ggf. zwei zusätzliche Spalten „Erw. Einnahmen Fz“ und „Erw. Einnahmen WST“ oder eine zusammengefasste „Erwartete Einnahmen (Locosoft)“; Hinweis auf Auf-/Abschlag in Tooltip oder Legende.
4. **Konfiguration:** Auf-/Abschlagsfaktoren zentral (Konstante oder Config), damit Buchhaltung/Controlling sie anpassen kann.

---

## 5. Abhängigkeiten & Einschränkungen

- **Locosoft-Verfügbarkeit:** Wenn Locosoft nicht erreichbar ist, nur Fallback (Ø/Tag oder 0) für die Locosoft-Erwartung.
- **Zahlungsziel:** Aktuell pauschal (z. B. 14 Tage). Später optional aus Kundendaten/Zahlungsbedingungen, falls in Locosoft verfügbar.
- **Rechnungsdatum bei Aufträgen:** Bei „noch nicht in Rechnung“ muss ein geschätztes Rechnungsdatum (z. B. Auftrag + 14 Tage) und daraus Zahlungseingang (Rechnung + 14 Tage) angenommen werden.
- **Werkstatt:** `labours.is_invoiced` und Zuordnung zu `invoices` prüfen (Schema Locosoft), damit keine Doppelzählung entsteht.
- **Einfinanzierung:** Für korrekten Nettoliquiditätseffekt bei Fahrzeugverkäufen muss pro VIN in der **Portal-DB** (`fahrzeugfinanzierungen`) geprüft werden, ob das Fahrzeug einfinanziert ist; Ablösebetrag = `aktueller_saldo`. VIN-Matching zwischen Locosoft (dealer_vehicles/vehicles) und Portal muss eindeutig sein (z. B. TRIM, Großschreibung).

---

## 6. Fazit

**Ja** – erwartete Einnahmen aus Fahrzeugverkauf (Aufträge und/oder Rechnungen mit Zahlungseingang in der Zukunft) und aus Werkstattleistungen (Locosoft-Aufträge/Rechnungen) können in die Liquiditätsvorschau einfließen, mit Auf- oder Abschlag auf den Schnitt. Die Daten liegen in Locosoft; die Umsetzung erfordert Abfragen auf `dealer_vehicles`, `invoices`, `orders`, `labours` (und ggf. `parts`), eine klare Regel für erwartetes Zahlungsdatum sowie die Integration in die bestehende Projektion und Konfiguration der Faktoren.
