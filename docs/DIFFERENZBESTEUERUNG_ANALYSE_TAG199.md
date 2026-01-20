# Differenzbesteuerung - Analyse und Lösung

**TAG:** 199  
**Datum:** 2026-01-19  
**Problem:** DB-Berechnung für Regel- vs. Differenzbesteuerung stimmt nicht

---

## Problem

**Markiertes Fahrzeug (Händler# 111282):**
- VK: 25.257 €
- EK: 21.453 €
- Kalk. DB: 3.774 €
- **Status:** Regelbesteuert (laut Benutzer)

**Aktuelle Berechnung:**
- Regel (F): `VK/1.19 - EK - Kosten = 21.224 - 21.453 = -229 €` ❌
- Diff (B): `(VK - EK) / 1.19 - Kosten = 3.804 / 1.19 = 3.197 €` ❌

**Beide Berechnungen passen nicht zum angezeigten Wert (3.774 €)!**

---

## Analyse

### 1. Besteuerungsart erkennen

**Feld:** `out_sale_type` in `dealer_vehicles`
- `F` = Faktura/Regelbesteuerung
- `B` = Brutto/Differenzbesteuerung §25a
- `L` = Leasing
- `NULL` = Noch nicht gesetzt (Bestandsfahrzeuge)

**Problem:** Für **Bestandsfahrzeuge** (noch nicht verkauft) ist `out_sale_type` oft NULL!

### 2. Fallback-Logik benötigt

Wenn `out_sale_type` NULL ist, müssen wir die Besteuerungsart anders bestimmen:

**Mögliche Ansätze:**
1. **Default:** Gebrauchtwagen = immer Differenzbesteuerung (§25a)
2. **Invoice Type:** `out_invoice_type = 8` = Gebrauchtwagen = immer §25a
3. **Einkaufsrechnung prüfen:** `in_buy_invoice_no` + `invoices`-Tabelle

**Hinweis aus sync_sales.py (Zeile 127):**
```python
# NEU TAG181: Invoice Type (8 = Gebrauchtfahrzeug = immer §25a)
dv.out_invoice_type,
```

### 3. Korrekte DB-Berechnung

**Regelbesteuerung (F):**
```
VK_netto = VK_brutto / 1.19
DB = VK_netto - EK - Kosten
```

**Differenzbesteuerung §25a (B):**
```
Marge_brutto = VK_brutto - EK
Marge_netto = Marge_brutto / 1.19
DB = Marge_netto - Kosten
```

**Wichtig:** 
- Bei Regelbesteuerung wird MwSt auf den **gesamten VK** berechnet
- Bei Differenzbesteuerung wird MwSt nur auf die **Marge** berechnet

---

## Lösung

### 1. Besteuerungsart bestimmen

```sql
CASE
    -- Explizit gesetzt
    WHEN dv.out_sale_type = 'F' THEN 'Regel'
    WHEN dv.out_sale_type = 'B' THEN 'Diff25a'
    WHEN dv.out_sale_type = 'L' THEN 'Leasing'
    -- Fallback: Invoice Type prüfen
    WHEN dv.out_invoice_type = 8 THEN 'Diff25a'  -- Gebrauchtwagen = immer §25a
    -- Fallback: Default für GW = Differenzbesteuerung
    WHEN dv.dealer_vehicle_type = 'G' THEN 'Diff25a'
    -- Sonst: Regelbesteuerung
    ELSE 'Regel'
END as besteuerung
```

### 2. DB-Berechnung korrigieren

**Aktuell (FEHLER):**
```sql
-- Regel (F): VK/1.19 - EK - Kosten
WHEN dv.out_sale_type = 'F'
THEN ROUND(COALESCE(dv.out_sale_price, 0) / 1.19, 2) - (
    COALESCE(dv.calc_basic_charge, 0) + ...
) - COALESCE(dv.calc_cost_internal_invoices, 0)
```

**Problem:** EK wird als Brutto behandelt, sollte aber Netto sein!

**Korrekt:**
```sql
-- Regel (F): VK_netto - EK_netto - Kosten
WHEN besteuerung = 'Regel'
THEN ROUND(
    COALESCE(dv.out_sale_price, 0) / 1.19, 2
) - ROUND(
    (COALESCE(dv.calc_basic_charge, 0) + ...) / 1.19, 2
) - COALESCE(dv.calc_cost_internal_invoices, 0)
```

**Oder:** EK ist bereits Netto? Dann:
```sql
-- Regel (F): VK_netto - EK - Kosten
WHEN besteuerung = 'Regel'
THEN ROUND(COALESCE(dv.out_sale_price, 0) / 1.19, 2) - (
    COALESCE(dv.calc_basic_charge, 0) + ...
) - COALESCE(dv.calc_cost_internal_invoices, 0)
```

**Differenzbesteuerung (B):**
```sql
-- Diff25a (B): (VK - EK) / 1.19 - Kosten
WHEN besteuerung = 'Diff25a'
THEN ROUND(
    GREATEST(
        COALESCE(dv.out_sale_price, 0) - (
            COALESCE(dv.calc_basic_charge, 0) + ...
        ), 0
    ) / 1.19, 2
) - COALESCE(dv.calc_cost_internal_invoices, 0)
```

---

## Test-Fahrzeug (111282)

**Daten:**
- VK: 25.257 € (brutto)
- EK: 21.453 € (brutto?)
- Kalk. DB: 3.774 € (aktuell angezeigt)

**Bei Regelbesteuerung:**
- VK_netto = 25.257 / 1.19 = 21.224,37 €
- EK_netto = 21.453 / 1.19 = 18.027,73 € (wenn EK brutto)
- DB = 21.224,37 - 18.027,73 = 3.196,64 € ❌ (passt nicht zu 3.774 €)

**Bei Differenzbesteuerung:**
- Marge_brutto = 25.257 - 21.453 = 3.804 €
- Marge_netto = 3.804 / 1.19 = 3.196,64 €
- DB = 3.196,64 - Kosten = ? ❌ (passt auch nicht)

**Frage:** Sind die Kosten bereits abgezogen? Oder ist EK bereits Netto?

---

## Nächste Schritte

1. ✅ Prüfen: Ist EK brutto oder netto in Locosoft?
2. ✅ Prüfen: Welche Kosten werden abgezogen?
3. ✅ Fallback-Logik implementieren für `out_sale_type IS NULL`
4. ✅ DB-Berechnung validieren mit echten Daten

---

## Referenzen

- `api/fahrzeug_data.py` Zeile 155-225 (aktuelle Implementierung)
- `scripts/sync/sync_sales.py` Zeile 127 (Invoice Type 8 = §25a)
- `docs/DB_SCHEMA_LOCOSOFT.md` (Feld-Definitionen)
