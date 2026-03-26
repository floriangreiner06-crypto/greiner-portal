# L744PR Verkaufsnachweisliste – Abgleich unserer Abfrage

**Stand:** 2026-02-17

## Filter im Locosoft-Dialog (aus Screenshot)

| Dialogfeld | Wert im Screenshot | Entsprechung in Locosoft-DB |
|------------|--------------------|-----------------------------|
| **Rechnungsdatum** | 01.01.26 – 31.01.26 | `dealer_vehicles.out_invoice_date` bzw. `invoices.invoice_date` |
| **Verkaufsberater** | 1003 – 9001 | `dealer_vehicles.out_salesman_number_1` (VKB) |
| **Fahrzeugart/Kom-Nr.** | D – V (und 00000–9999999) | Anderes Feld/Kodierung; für Stückzahl nutzen wir **Verkaufsart** |
| **Verkaufsart** | B – U | `dealer_vehicles.out_sale_type` (B, F, L …) → Filter `>= 'B' AND <= 'U'` |
| **Verkaufender Betrieb** | 1 – 1 („sowie 0 und 0 und 0“) | `dealer_vehicles.out_subsidiary` (1 = DEG Opel, 2 = HYU, 3 = LAN) |
| Bestelldatum / Erstzulassung | 00.00.0000 – 17.02.2026 | Optional; für reine Monatsauswertung oft offen |

## Unsere SQL-Abfrage (analog)

Grundgerüst wie im Report: verkaufte Fahrzeuge mit Rechnung im Zeitraum.

```sql
SELECT
    dv.out_invoice_date     AS rg_datum,
    i.service_date          AS leistungsdatum,
    dv.out_invoice_number   AS rg_nr,
    dv.out_subsidiary       AS verk_betrieb,
    dv.out_salesman_number_1 AS verk_vkb,
    dv.out_sale_type        AS fz_art,
    m.description           AS modell_bez,
    i.total_net             AS rg_netto,
    v.vin                   AS fahrgestellnr
FROM dealer_vehicles dv
LEFT JOIN vehicles v ON ...
LEFT JOIN models m ON ...
INNER JOIN invoices i
    ON dv.out_invoice_type = i.invoice_type
   AND dv.out_invoice_number::integer = i.invoice_number
   AND i.subsidiary = dv.out_subsidiary
WHERE dv.out_invoice_date IS NOT NULL
  AND dv.out_invoice_date >= :von AND dv.out_invoice_date < :bis
  -- L744PR-äquivalent (Screenshot):
  AND (dv.out_salesman_number_1 BETWEEN 1003 AND 9001)   -- Verkaufsberater
  AND dv.out_sale_type >= 'B' AND dv.out_sale_type <= 'U' -- Verkaufsart B–U
  -- AND dv.out_subsidiary = 1   -- nur wenn im Dialog „Verkaufender Betrieb 1 bis 1“ gesetzt
ORDER BY dv.out_invoice_date, dv.out_invoice_number;
```

## Abweichungen / offene Punkte

1. **Verkaufender Betrieb:** Im Screenshot war nur Betrieb 1 gewählt. Wenn der Export für alle Standorte läuft, keinen Filter auf `out_subsidiary` setzen (oder 1, 2, 3).
2. **Verkaufsart B–U:** Im Dialog „Verkaufsart B–U“ → wir setzen `out_sale_type >= 'B' AND <= 'U'`. Damit liefert die Abfrage **dieselbe Stückzahl (72)** wie ohne Art-Filter, da alle Januar-Verkäufe B/F/L sind. „Fahrzeugart/Kom-Nr. D–V“ ist ein anderes Feld (Kom.-Nr.); für die reine Stückzahl reicht Verkaufsart B–U.
3. **Ankaufs-/Zugangstyp:** Checkboxen (Inzahlungnahme, Leasing-Rückläufer, …) – ggf. Zuordnung zu Locosoft-Feldern (z. B. `in_used_vehicle_buy_type`) nötig, um 1:1 zu sein.
4. **Rg-Typ H/Z, Storno:** L744PR könnte nur Hauptrechnungen liefern; dann `invoices.is_canceled = false` und ggf. Rechnungstyp prüfen.

## Testergebnis (Januar 2026)

| Variante | Treffer |
|----------|--------|
| Rechnungsdatum 01.01.–31.01. | 72 |
| + L744PR (VKB 1003–9001, **Verkaufsart B–U**), alle Betriebe | **72** |
| + L744PR + nur Betrieb 1 | 43 |

**Stückzahl 93 in eurer 0126.xls:** In der DB gibt es für Januar 2026 **72 verkaufte Fahrzeuge** (dealer_vehicles + Rechnung im Zeitraum). Die **21 zusätzlichen Zeilen** in der Excel kommen sehr wahrscheinlich durch **Report-Optionen** im L744PR-Dialog:
- „inkl. Zusatzcodes/Zusatztermine/KM-/Ablesestände“
- „inkl. Aufschlüsselung aufteilbarer Zahlungen“

→ Pro Fahrzeug können im Export **mehrere Zeilen** entstehen (z. B. eine Hauptzeile + Zusatzzeilen). Diese Zusatzzeilen können wir ohne Locosoft-Reportlogik nicht aus der DB erzeugen. **Gleiche Stückzahl (72)** erreichen wir mit der Abfrage; für 93 Zeilen müsste die Zusatzlogik nachgebaut oder der Report weiter analysiert werden.

## Script

`scripts/provisions_januar_filter_test.py`:
- **--l744pr**: Filter wie im Screenshot (VKB 1003–9001, Verkaufsart B–U) → **72 Treffer** (Jan 2026).
- **--betrieb 1**: nur `out_subsidiary = 1` (43 Treffer Jan 2026).
