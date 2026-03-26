# Pool Handelsgeschäft / Geschäftsleitung (Verkäufer-Zielplanung)

**Stand:** 2026-02  
**Zweck:** Diese Mitarbeiter werden bei der Verteilung der Verkäufer-Ziele (Kalenderjahr, z. B. 630 NW / 900 GW) **nicht** berücksichtigt – ihre (geplanten) Verkäufe werden vom Gesamtziel abgezogen, der Rest auf die übrigen Verkäufer nach historischer Leistung verteilt.

## Konfiguration

**Mitarbeiternummern (Locosoft `out_salesman_number_1` / `employee_number`):**

| Nr   | Name            | Rolle / Anmerkung     |
|------|-----------------|------------------------|
| 9001 | Greiner, Florian | Geschäftsleitung       |
| 1003 | Sterr, Rolf      | Filialleitung          |
| 2000 | Süß, Anton       | Verkaufsleitung        |

→ **Pool Handelsgeschäft = [9001, 1003, 2000]**

Verwendung in Scripts/API: Diese drei Nummern von der Zielverteilung ausnehmen; deren 2025-Verkäufe (oder manuell geplante 2026-Werte) vom Konzernziel abziehen.

## Referenz 2025 (aus Stückzahl-Analyse)

| Nr   | Name            | NW  | GW  | Summe |
|------|-----------------|-----|-----|-------|
| 9001 | Greiner, Florian | 1  | 179 | 180   |
| 1003 | Sterr, Rolf      | 0  | 111 | 111   |
| 2000 | Süß, Anton       | 35 | 27  | 62    |
| **Handelsgeschäft gesamt** | **36** | **317** | **353** |

→ Bei Verteilung 2026 (630 NW, 900 GW) und Plan Handelsgeschäft = 2025-Ist:  
**Pool für Verteilung** = 630 − 36 = **594 NW**, 900 − 317 = **583 GW** (für die übrigen Verkäufer).

## NW nach Marken (Zielverteilung)

NW-Ziele werden nach **Marke** getrennt verteilt (Locosoft `out_make_number`: Hyundai 27, Opel 40, Leapmotor 41):

| Marke        | Verteilung auf |
|--------------|----------------|
| **Hyundai**  | Nur **Roland (2006)** und **Edeltraud (2001)**; die beiden haben keine Relevanz für Opel. |
| **Opel**     | Alle Verkäufer **außer** 2001, 2006 (und außer Pool Handelsgeschäft). |
| **Leapmotor**| **Alle** Verkäufer (außer Pool). |

Konzernziele pro Marke optional (`ziel_nw_hyundai`, `ziel_nw_opel`, `ziel_nw_leapmotor`); sonst Aufteilung aus Gesamt-NW nach Referenzjahr-Anteilen.

---

## Auftragseingang (Vertragsdatum) vs. Verkäufe (Rechnungsdatum)

Die **Verkäufer-Zielplanung im Portal** nutzt **Auftragseingang** (Vertragsdatum `out_sales_contract_date`), nicht Fakturierung (`out_invoice_date`). Entspricht der Auswertung im Verkäuferarbeitsplatz Catch und dem DRIVE-Modul „Auftragseingang“. **NW** = N (Neuwagen), V (Vorführwagen), **T (Tageszulassung)**; **GW** = D, G. Dedup-Regel wie in `api/verkauf_data.py`: N wird nicht gezählt, wenn dieselbe Fahrzeugnummer am gleichen Vertragsdatum als T oder V vorkommt. Die CSV-Scripts unter `scripts/verkauf/stueckzahl_analyse_*.py` zählen weiterhin nach **Rechnungsdatum** (Verkäufe); bei Bedarf können sie um einen Modus „Auftragseingang“ ergänzt werden.
