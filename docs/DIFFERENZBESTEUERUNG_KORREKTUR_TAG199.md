# Differenzbesteuerung - Korrektur basierend auf Kommissionsnummer

**TAG:** 199  
**Datum:** 2026-01-19  
**Update:** Korrektur basierend auf Kommissionsnummer-Logik

---

## Wichtige Erkenntnis

**Die Kommissionsnummer beginnt mit einem Buchstaben, der die Besteuerungsart anzeigt:**

- **"D"** = Differenzbesteuert (nur bei Ankauf von Privatpersonen oder differenzbesteuerten Fahrzeugen)
- **"G"** = Gebrauchtwagen (Regelbesteuert, wenn `out_sale_type = 'F'` oder NULL)
- **"N"** = Neuwagen
- etc.

**Beispiele aus Screenshots:**
- `Kom.Nr. G 111282` → Regelbesteuert (dealer_vehicle_type = 'G')
- `Kom.Nr. D 315735` → Differenzbesteuert (dealer_vehicle_type = 'D')

---

## Implementierte Logik

### Priorität 1: `out_sale_type` (explizit gesetzt)
```sql
WHEN dv.out_sale_type = 'F' THEN 'Regel'
WHEN dv.out_sale_type = 'B' THEN 'Diff25a'
WHEN dv.out_sale_type = 'L' THEN 'Leasing'
```

### Priorität 2: `dealer_vehicle_type` (Kommissionsnummer-Buchstabe)
```sql
-- Kommissionsnummer beginnt mit "D" = Differenzbesteuert
WHEN dv.dealer_vehicle_type = 'D' THEN 'Diff25a'
```

### Priorität 3: `out_invoice_type` (Fallback)
```sql
-- Invoice Type 8 = Gebrauchtwagen = immer §25a
WHEN dv.out_invoice_type = 8 THEN 'Diff25a'
```

### Default: Regelbesteuerung
```sql
-- Sonst: Regelbesteuerung (Standard für GW mit dealer_vehicle_type = 'G')
ELSE 'Regel'
```

---

## Vollständige Logik

```sql
CASE
    -- Explizit gesetzt: out_sale_type hat Priorität
    WHEN dv.out_sale_type = 'F' THEN 'Regel'
    WHEN dv.out_sale_type = 'B' THEN 'Diff25a'
    WHEN dv.out_sale_type = 'L' THEN 'Leasing'
    -- Kommissionsnummer beginnt mit "D" = Differenzbesteuert
    WHEN dv.dealer_vehicle_type = 'D' THEN 'Diff25a'
    -- Fallback: Invoice Type 8 = Gebrauchtwagen = immer §25a
    WHEN dv.out_invoice_type = 8 THEN 'Diff25a'
    -- Sonst: Regelbesteuerung (Standard für GW mit dealer_vehicle_type = 'G')
    ELSE 'Regel'
END as besteuerung
```

---

## DB-Berechnung

**Regelbesteuerung:**
```
VK_netto = VK_brutto / 1.19
DB = VK_netto - EK_netto - Kosten
```

**Differenzbesteuerung:**
```
Marge_brutto = VK_brutto - EK_brutto
Marge_netto = Marge_brutto / 1.19
DB = Marge_netto - Kosten
```

**Hinweis:** `calc_*`-Felder sind bereits NETTO in Locosoft!

---

## Änderungen

**Datei:** `api/fahrzeug_data.py`
- ✅ `get_gw_bestand()` - Besteuerungsart-Erkennung korrigiert
- ✅ Priorität: `out_sale_type` → `dealer_vehicle_type = 'D'` → `out_invoice_type = 8` → Default

---

## Test-Fahrzeuge

**Fahrzeug 1 (111282):**
- Kom.Nr.: `G 111282`
- `dealer_vehicle_type = 'G'`
- `out_sale_type = 'F'` (oder NULL)
- **Erwartet:** Regelbesteuert ✅

**Fahrzeug 2 (315735):**
- Kom.Nr.: `D 315735`
- `dealer_vehicle_type = 'D'`
- Angekauft von: Privatperson
- **Erwartet:** Differenzbesteuert ✅

---

## Status

✅ **Implementiert und korrigiert**

Die Logik erkennt jetzt korrekt:
1. Explizit gesetzte `out_sale_type`
2. Kommissionsnummer mit "D" (differenzbesteuert)
3. Fallback über `out_invoice_type = 8`
4. Default: Regelbesteuerung
