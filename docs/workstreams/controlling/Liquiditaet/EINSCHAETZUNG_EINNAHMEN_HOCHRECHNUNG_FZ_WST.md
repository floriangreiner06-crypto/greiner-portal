# Einschätzung: Einnahmen-Hochrechnung aus Fahrzeug- und Werkstattaufträgen

**Workstream:** Controlling / Liquidität  
**Stand:** 2026-02  
**Kontext:** Liquiditätsvorschau soll erwartete Einnahmen auf Basis **vorliegender** Fahrzeugaufträge und Werkstattaufträge abbilden (nicht nur Ø/Tag aus Vergangenheit).

---

## Kurzfassung

| Bereich | Datenverfügbarkeit | Einschätzung |
|--------|---------------------|--------------|
| **Fahrzeug – Auftrag, noch nicht in Rechnung** | `dealer_vehicles`: `out_sales_contract_date` gesetzt, `out_invoice_date` NULL; Betrag: `out_estimated_invoice_value` / `out_sale_price` | **Gut nutzbar.** Feldbesetzung und VIN-Zuordnung (Join zu `vehicles`) prüfen – Skript liefert Zählung/Stichprobe. |
| **Fahrzeug – Bereits in Rechnung, Zahlung ausstehend** | `dealer_vehicles.out_invoice_date` + `out_sale_price` im Projektionszeitraum | **Gut nutzbar.** Erwarteter Zahlungseingang = Rechnungsdatum + Zahlungsziel (z. B. 14 Tage). |
| **Fahrzeug – Ablöse Einkaufsfinanzierung** | Portal: `fahrzeugfinanzierungen` (VIN, `aktueller_saldo`, `aktiv`) | **Nutzerbar.** VIN aus Locosoft (über `vehicles`) → Ablöse pro VIN abfragbar; Netto = Verkaufserlös − Ablöse. |
| **Werkstatt – Offene Aufträge** | Locosoft: `orders` + `labours` (`is_invoiced = false`), Summe `net_price_in_order` | **Nutzerbar.** Einschränkung: erwartetes Datum = Schätzung (z. B. order_date + 7 + 14 Tage). |
| **Werkstatt – Rechnungen im Zeitraum** | Locosoft: `invoices` mit `invoice_date` im Fenster, `invoice_type` 2,3,4,5,6 (Werkstatt) | **Gut nutzbar.** Betrag = `total_net`; Zahlungseingang = invoice_date + Zahlungsziel. |

**Fazit:** Die Daten für eine **Hochrechnung der Einnahmen** aus Fahrzeug- und Werkstattaufträgen sind in Locosoft (und für Ablöse im Portal) vorhanden. Empfohlen wird, zuerst das **Datenprüf-Skript** auszuführen und die Ausgabe zu sichten; danach die Integration in die Liquiditätsvorschau gemäß Konzept umzusetzen.

### Doppel-VINs (Aufträge vs. Rechnungen)

Dieselbe **VIN** kann in Locosoft in **beiden** Listen vorkommen: z. B. eine N-Zeile (Neuwagen) noch mit `out_invoice_date` NULL („Auftrag“) und eine T/V-Zeile (Tageszulassung/Umsetzung) desselben Fahrzeugs bereits mit Rechnungsdatum. Für Liquidität zählt jede VIN nur **einmal**. Das Export-Skript **bereinigt** das: Wenn eine VIN in „Rechnungen im Zeitraum“ vorkommt, wird sie in der Liste „Aufträge“ weggelassen (Priorität Rechnungen, da Fälligkeit/Ablöse am Rechnungsdatum anfällt).

### Ablöse einfinanzierter Fahrzeuge

**Ja** – wir berücksichtigen die Ablöse: Pro VIN wird aus der **Portal-DB** (`fahrzeugfinanzierungen`, `aktiv = true`) die Summe **aktueller_saldo** geholt. In den CSV-Exporten und in der Konsolenausgabe gibt es die Spalten **ablöse_eur** und **netto_liquiditaet_eur** (VK − Ablöse). So sieht Dispo pro Position den erwarteten **Netto-Liquiditätseffekt** (Zahlungseingang Kunde minus Ablöse an die Bank). Bei der späteren Integration in die Liquiditätsvorschau wird dieselbe Logik verwendet: + Verkaufserlös, − Ablöse pro VIN.

### Erste Lauf-Ausgabe (Beispiel 60-Tage-Zeitraum, März 2026)

| Kennzahl | Wert |
|----------|------|
| Fahrzeug – Auftrag, noch nicht in Rechnung | 154 Stück; **out_estimated_invoice_value** durchweg 0 → Betrag aus **out_sale_price** (ca. 4,79 M€ gesamt) |
| Fahrzeug – Bereits in Rechnung im Zeitraum | 39 Stück, ca. 878 k€ |
| NW – readmission_date im Zeitraum | 13 Fahrzeuge |
| Werkstatt – Offene Positionen (nicht fakturiert) | 879 Aufträge, ca. 293 k€; davon 425 mit order_date/estimated_outbound im Zeitraum, ca. 68 k€ |
| Werkstatt – Rechnungen im Zeitraum | 63 Rechnungen, ca. 17 k€ |
| VIN für Ablöse-Check (Fahrzeug-Aufträge) | 154 von 154 zuordenbar |

**Pragmatik:** Für „Auftrag, noch nicht in Rechnung“ in der Implementierung **out_sale_price** verwenden (out_estimated_invoice_value ist in Locosoft aktuell nicht befüllt).

---

## Vorgehensweise: Nur Daten, keine hochgerechneten Schnitte

**Entscheidung:** Wir nehmen **keine** hochgerechneten Durchschnitte (z. B. „Ø Einnahmen/Tag aus letzten 90 Tagen“) in die Projektion. Es zählen nur:

- **Erwartete Einnahmen:** ausschließlich aus **Locosoft** (Fahrzeug-Aufträge/Rechnungen + Werkstatt-Aufträge/Rechnungen), pro erwartetem Zahlungsdatum; Ablöse einfinanzierter Fahrzeuge aus dem Portal abgezogen.
- **Ausgaben:** bekannte Abflüsse aus unseren Daten (Transaktionen mit Buchungsdatum im Zeitraum, Tilgungen mit Fälligkeit im Zeitraum, ggf. weitere wiederkehrende Zahlungen, sofern im System abgebildet).

An Tagen **ohne** Locosoft-Eintrag sind die erwarteten Einnahmen **0** – transparent und nachvollziehbar. Ein „Ø Einnahmen/Tag (Vergangenheit)“ kann optional nur als **Hinweis** angezeigt werden, ohne in die Saldo-Projektion einzugehen.

---

## 1. Datenprüfung durchführen

Vor der Implementierung die tatsächlichen Mengen und Beträge prüfen:

```bash
cd /opt/greiner-portal
python scripts/check_liquiditaet_locosoft_daten.py --tage 60
```

Das Skript liefert u. a.:

- **Fahrzeug:** Anzahl Aufträge (noch nicht in Rechnung), Summen `out_estimated_invoice_value` / `out_sale_price`; Anzahl bereits in Rechnung mit Rechnungsdatum im Zeitraum; NW-Lieferungen (`readmission_date`); wie viele Aufträge über VIN (Join zu `vehicles`) für Ablöse-Check zuordenbar sind.
- **Werkstatt:** Anzahl offener Aufträge (mit nicht fakturierten `labours`) und Summe `net_price_in_order`; davon mit `order_date`/`estimated_outbound_time` im Zeitraum; Anzahl Werkstatt-Rechnungen im Zeitraum und Summe `total_net`.

**Interpretation:**

- Wenn **out_estimated_invoice_value** oft NULL ist: stärker `out_sale_price` oder Fallback-Logik nutzen.
- Wenn **VIN-Zuordnung** deutlich unter der Anzahl Aufträge liegt: Ablöse nur für Teilmenge möglich; Rest nur als Verkaufserlös (ohne Abzug Ablöse) oder Nachpflege der Locosoft-Daten prüfen.
- **Werkstatt:** Offene Summe kann groß sein (alle nicht fakturierten Positionen); für Vorschau ggf. auf Aufträge mit erwarteter Fertigstellung im Zeitraum begrenzen (order_date/estimated_outbound_time).

---

## 2. Limitationen und Risiken

| Thema | Einschätzung |
|-------|--------------|
| **Zahlungsziel** | Derzeit pauschal (z. B. 14 Tage). Individuelle Zahlungsbedingungen aus Locosoft wären optional. |
| **Storno/Rabatt** | Aufträge können storniert oder mit Rabatt fakturiert werden. Daher im Konzept **Auf-/Abschlag** (z. B. 0,95 für Fahrzeug-Aufträge, 0,90 für Werkstatt-Aufträge) vorgesehen. |
| **Erwartetes Datum bei „noch nicht in Rechnung“** | Geschätzt (z. B. Auftrag + 14 Tage Rechnung + 14 Tage Zahlung). Abweichungen möglich. |
| **Locosoft-Verfügbarkeit** | Bei Ausfall Locosoft: Fallback auf Ø/Tag oder 0 für Locosoft-basierte Erwartung. |
| **invoice_type Werkstatt** | Werte 2,3,4,5,6 laut Konzept; ggf. mit Locosoft-Doku abgleichen. |

---

## 3. Empfehlung

1. **Skript ausführen** und Ausgabe archivieren (z. B. für Projektionszeitraum 60 Tage).
2. **Implementierung** wie in `LIQUIDITAET_ERWARTETE_EINNAHMEN_LOCOSOFT.md` beschrieben:
   - Modul `api/cashflow_erwartung_locosoft.py` mit `get_erwartete_einnahmen_fahrzeug()` und `get_erwartete_einnahmen_werkstatt()`
   - Ablöse aus Portal `fahrzeugfinanzierungen` pro VIN
   - Anbindung in `get_cashflow_vorschau` (optionaler Parameter `mit_locosoft_erwartung=True`)
   - Auf-/Abschlagsfaktoren konfigurierbar halten
3. **Frontend:** Erwartete Einnahmen Fz/WST in der Vorschau getrennt oder zusammengefasst anzeigen; Tooltip/Legende zu Abschlägen.

---

## 4. Referenzen

- Konzept: `docs/workstreams/controlling/LIQUIDITAET_ERWARTETE_EINNAHMEN_LOCOSOFT.md`
- Datenprüfung: `scripts/check_liquiditaet_locosoft_daten.py`
- Lieferforecast (NW): `api/verkauf_data.py` → `get_lieferforecast()`
- Cashflow-Vorschau: `api/cashflow_vorschau.py` → `get_cashflow_vorschau()`
- Locosoft-Schema: `docs/DB_SCHEMA_LOCOSOFT.md`
