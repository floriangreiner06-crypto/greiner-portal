# Teile-Stock SSOT - TAG 176

**Datum:** 2026-01-09  
**Zweck:** SSOT für Lagerbestand-Abfragen aus Locosoft

---

## 🎯 PROBLEM

**Vorher:**
- `teile_status_api.py` prüfte Lagerbestand direkt in SQL
- Problem: `parts_stock` hat mehrere `stock_no` (1, 2, 3) für verschiedene Lager
- Query: `LEFT JOIN parts_stock ps ON p.part_number = ps.part_number` OHNE `stock_no` Filter
- Folge: Wenn Teil in stock_no=1 vorhanden (3 Stück), aber stock_no=3 = 0, wurde es trotzdem als fehlend angezeigt

**Beispiel:**
- Teil `1620012580` in Auftrag #20853 (subsidiary=1)
- stock_no=1: stock_level=3.00 ✅ (auf Lager!)
- stock_no=3: stock_level=0.00 ❌
- **Problem:** Query zeigte Teil als fehlend, obwohl es auf Lager ist!

---

## ✅ LÖSUNG: SSOT-Funktion

**Neue Datei:** `api/teile_stock_utils.py`

### Funktionen:

1. **`get_stock_level_for_subsidiary(part_number, subsidiary, required_amount=0, use_soap=True)`**
   - SSOT für Lagerbestand-Abfragen
   - Versucht zuerst SOAP, dann DB-Fallback
   - Aggregiert über alle `stock_no` des Standorts (SUM)
   - Returns: Dict mit `stock_level`, `is_available`, `source` ('soap' oder 'db')

2. **`is_part_available(part_number, subsidiary, required_amount)`**
   - Kurzform: Prüft ob Teil verfügbar ist
   - Returns: True/False

3. **`get_missing_parts_for_order(order_number, subsidiary)`**
   - Ermittelt fehlende Teile für einen Auftrag
   - Verwendet SSOT-Funktion

4. **`get_stock_level_via_soap(part_number, subsidiary=None)`**
   - Versucht Lagerbestand über Locosoft SOAP zu holen
   - Falls SOAP nicht verfügbar: None

---

## 📊 STOCK_NO MAPPING

**Wichtig:** Alle `subsidiary` haben alle `stock_no` (1, 2, 3)!

```python
STOCK_NO_MAPPING = {
    1: [1, 2, 3],  # Deggendorf Opel: Alle Lager
    2: [1, 2, 3],  # Deggendorf Hyundai: Alle Lager
    3: [1, 2, 3],  # Landau: Alle Lager
}
```

**Lösung:** Aggregieren über alle `stock_no` (SUM)

---

## 🔧 ÄNDERUNGEN IN TEILE_STATUS_API

### Vorher:
```sql
LEFT JOIN parts_stock ps ON p.part_number = ps.part_number
WHERE (ps.stock_level IS NULL OR ps.stock_level < p.amount)
```

**Problem:** Mehrere Zeilen pro Teil (eine pro stock_no), WHERE-Bedingung falsch

### Nachher:
```sql
LEFT JOIN parts_stock ps ON p.part_number = ps.part_number
GROUP BY ...
HAVING COALESCE(SUM(ps.stock_level), 0) < p.amount
```

**Lösung:** Aggregiert über alle stock_no (SUM)

---

## 🧪 SOAP-INTEGRATION

**Status:** Vorbereitet, aber noch nicht vollständig getestet

**SOAP-Methode:** `readPartInformation(partNumber)`

**Zu prüfen:**
- Gibt SOAP `stock_level` zurück?
- Welche Felder enthält die SOAP-Response?
- Ist `stock_no` in SOAP-Response enthalten?

**Fallback:** DB-Abfrage (funktioniert bereits)

---

## 📝 VERWENDUNG

### In `teile_status_api.py`:

```python
from api.teile_stock_utils import get_stock_level_for_subsidiary, is_part_available

# Lagerbestand prüfen
stock_info = get_stock_level_for_subsidiary('1620012580', subsidiary=1, required_amount=1.0)
if stock_info['is_available']:
    print(f"Teil verfügbar: {stock_info['stock_level']} Stück (Quelle: {stock_info['source']})")
```

### Direkt in SQL (wenn nötig):

```sql
-- Aggregiert über alle stock_no
SELECT 
    p.part_number,
    p.amount as menge,
    COALESCE(SUM(ps.stock_level), 0) as lagerbestand
FROM parts p
LEFT JOIN parts_stock ps ON p.part_number = ps.part_number
GROUP BY p.part_number, p.amount
HAVING COALESCE(SUM(ps.stock_level), 0) < p.amount
```

---

## ✅ ERFOLGSKRITERIEN

- [x] SSOT-Funktion erstellt
- [x] Query in `teile_status_api.py` angepasst (SUM über stock_no)
- [x] SOAP-Integration vorbereitet
- [x] DB-Fallback funktioniert
- [ ] SOAP-Test (wenn SOAP stock_level zurückgibt)

---

## 🐛 BEHOBENE BUGS

1. **Teil 1620012580:** Wird jetzt korrekt als verfügbar erkannt (stock_level=3.00)
2. **Mehrfache stock_no:** Aggregiert korrekt (SUM)
3. **SSOT:** Zentrale Funktion für alle Module

---

**Status:** ✅ Implementiert - Bereit zum Testen!
