# Profitabilität vs. Auslieferung – Datenquellen und DB-Berechnung

**Stand:** TAG 219  
**Ziel:** Eine einzige Quelle für Deckungsbeitrag (keine redundanten Berechnungen).

---

## Vergleich

| Aspekt | Auslieferung (Detail) | Profitabilität (vor Umstellung) |
|--------|------------------------|----------------------------------|
| **Datenquelle** | DRIVE-Tabelle `sales` | Locosoft live: `dealer_vehicles` + `dealer_sales_aid` |
| **DB-Berechnung** | Bereits in `sales` gespeichert (berechnet beim **sync_sales.py**) | Live mit `kalkulation_helpers` (EK, VK, VKU, Formel) |
| **MwSt** | Aus Locosoft `invoices` (full_vat_value + reduced_vat_value) | Aus Formel (VK/1.19 oder Marge/1.19) |
| **Besteuerung** | sync_sales: `out_invoice_type == 8` oder `out_sale_type == 'B'` → Diff | kalkulation_helpers: **dealer_vehicle_type** (D/G) zuerst, dann out_sale_type, dann out_invoice_type |
| **EK** | sync_sales: basic_charge + accessory + extra_expenses + usage_value_encr_**internal** (ohne external) | kalkulation_helpers: + usage_value_encr_**external** |
| **VKU** | Aus `dealer_sales_aid.claimed_amount` (im Sync) | Gleich (dealer_sales_aid) |

**Fazit:** Zwei getrennte Rechenwege → Abweichungen möglich (MwSt aus Rechnung vs. Formel, andere Besteuerungslogik, EK mit/ohne usage_value_encr_external). Auslieferung und Profitabilität zeigten daher nicht zwingend denselben DB.

---

## Empfehlung (SSOT)

**Profitabilität nutzt dieselbe Quelle wie Auslieferung:** Tabelle **`sales`** (DRIVE Portal).

- **DB1, DB %, VK, VKU:** aus `sales` (berechnet in `sync_sales.py`).
- **Standzeit:** weiter aus Locosoft (ein Batch-Abruf für die verkauften Fahrzeuge des Monats: `in_arrival_date`, `out_invoice_date`), da `sales` aktuell kein `in_arrival_date` hat.
- **Standkosten / DB netto:** wie bisher im Profitabilitätsmodul (Standzeit × Zinssatz + Pauschale, DB netto = DB1 − Standkosten).

Damit gilt: **Eine Berechnung für DB** (sync_sales beim Schreiben in `sales`), Auslieferung und Profitabilität lesen dieselben Werte.

---

## Umsetzung (erledigt)

- **`api/profitabilitaet_data.py`** liest Verkäufe aus der DRIVE-Tabelle **sales** (Filter: out_invoice_date Monat/Jahr, out_subsidiary, optional dealer_vehicle_type). DB1, DB %, VK, VKU, EK-Komponenten und Verkäufername kommen aus **sales** bzw. **employees** (JOIN über locosoft_id). **Standzeit** wird weiterhin aus Locosoft in einem Batch-Abruf geholt (`_fetch_standzeit_loco`) und per (dealer_vehicle_number, dealer_vehicle_type) gemerged.
- **`kalkulation_helpers`** werden für die Profitabilitäts-**Verkaufs**liste nicht mehr verwendet; sie bleiben SSOT für **GW-Bestand** (fahrzeug_data) und andere Locosoft-Bestandsauswertungen.
- **Auslieferung (Detail)** und **Profitabilität** nutzen damit dieselben DB-Werte (aus sales, berechnet in sync_sales.py).
