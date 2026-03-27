# Migration: Standort-Filter auf SSOT umstellen

**Datum:** TAG 170 (2026-01-08)  
**Status:** In Arbeit

---

## ✅ BEREITS MIGRIERT

1. **`api/gewinnplanung_v2_gw_data.py`**
   - ✅ Locosoft-Filter: Nutzt jetzt `build_locosoft_filter_verkauf()` und `build_locosoft_filter_bestand()`
   - ✅ BWA-Filter: Nutzt jetzt `build_bwa_filter()`

---

## 📋 NOCH ZU MIGRIEREN

### Priorität 1 (KRITISCH)
1. **`api/abteilungsleiter_planung_data.py`**
   - `_lade_vorjahr_referenz()`: Locosoft-Filter
   - `lade_ist_werte_fuer_monat()`: BWA + Locosoft-Filter

### Priorität 2 (HOCH)
2. **`routes/controlling_routes.py`**
   - `get_stueckzahlen_locosoft()`: Locosoft-Filter

### Priorität 3 (MITTEL)
3. Weitere Dateien nach Bedarf

---

## 🔧 MIGRATIONS-SCHRITTE

### Schritt 1: Import hinzufügen
```python
from api.standort_utils import (
    build_bwa_filter,
    build_locosoft_filter_verkauf,
    build_locosoft_filter_bestand,
    build_locosoft_filter_orders
)
```

### Schritt 2: Alte Filter-Logik entfernen
```python
# ❌ ALT (entfernen):
if standort == 1:
    filter = "AND out_subsidiary = 1"
elif standort == 3:
    filter = "AND out_subsidiary = 1"  # ❌ FALSCH!
```

### Schritt 3: Zentrale Funktionen verwenden
```python
# ✅ NEU (verwenden):
filter = build_locosoft_filter_verkauf(standort=3, nur_stellantis=False)
```

### Schritt 4: Testen!
- Alte Werte vs. neue Werte vergleichen
- Bei Abweichungen: Prüfen, ob alte Logik falsch war

---

## 📝 CHECKLISTE

- [ ] Import hinzugefügt
- [ ] Alte Filter-Logik entfernt
- [ ] Zentrale Funktionen verwendet
- [ ] Getestet (alte vs. neue Werte)
- [ ] Dokumentation aktualisiert (falls nötig)

---

**WICHTIG:** Nach Migration immer testen, ob die Werte konsistent sind!

