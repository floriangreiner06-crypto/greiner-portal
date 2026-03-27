# Standort-Logik SSOT (Single Source of Truth)

**WICHTIG:** Diese Datei ist die **einzige autoritative Quelle** für Standort-Filter-Logik.  
**Alle Module MÜSSEN** die Funktionen aus `api/standort_utils.py` verwenden!

**Letzte Aktualisierung:** TAG 170 (2026-01-08)

---

## 📋 STANDORT-DEFINITIONEN

| Standort ID | Name | Firma | Subsidiary (Locosoft) | Branch (BWA) | Konto-Endziffer (BWA) |
|-------------|------|-------|----------------------|--------------|------------------------|
| 1 | Deggendorf Opel | Stellantis | 1 | 1 | 1 |
| 2 | Deggendorf Hyundai | Hyundai | 2 | 2 | - |
| 3 | Landau | Stellantis | **3** ✅ | 3 | 2 |

**✅ VERIFIZIERT:** Landau `subsidiary = 3` (LANO location)

---

## 🎯 VERWENDUNG: IMMER `api/standort_utils.py` NUTZEN!

### ❌ FALSCH (NICHT SO MACHEN):
```python
# Direkt SQL-Filter schreiben
if standort == 1:
    filter = "AND out_subsidiary = 1"
elif standort == 3:
    filter = "AND out_subsidiary = 1"  # ❌ FALSCH!
```

### ✅ RICHTIG (SO MACHEN):
```python
from api.standort_utils import build_locosoft_filter_verkauf

filter = build_locosoft_filter_verkauf(standort=3, nur_stellantis=False)
# Filter wird automatisch korrekt generiert
```

---

## 📚 BWA-FILTER (loco_journal_accountings)

### Verwendung
```python
from api.standort_utils import build_bwa_filter

firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name = \
    build_bwa_filter(firma='1', standort='1')
```

### Logik

**Umsatz (820000-829999):**
- Deggendorf: `branch_number = 1`
- Landau: `branch_number = 3`
- Hyundai: `branch_number = 2` + `subsidiary_to_company_ref = 2`

**Einsatz (720000-729999):**
- Deggendorf: Konto-Endziffer (6. Ziffer) = `'1'` + `subsidiary_to_company_ref = 1`
- Landau: Konto-Endziffer (6. Ziffer) = `'2'` + `subsidiary_to_company_ref = 1`
- Hyundai: `subsidiary_to_company_ref = 2`

**Kosten (4xxxxx):**
- Gleiche Logik wie Einsatz

**Firma:**
- Stellantis: `subsidiary_to_company_ref = 1`
- Hyundai: `subsidiary_to_company_ref = 2`

### Spezialfälle

**Deggendorf (beide Firmen):**
```python
build_bwa_filter(firma='0', standort='deg-both')
# Filtert: Stellantis (branch=1) + Hyundai (branch=2)
```

---

## 📚 LOCOSOFT-FILTER (dealer_vehicles, orders, invoices)

### Verwendung
```python
from api.standort_utils import (
    build_locosoft_filter_verkauf,
    build_locosoft_filter_bestand,
    build_locosoft_filter_orders
)

# Für dealer_vehicles (Verkäufe)
filter_verkauf = build_locosoft_filter_verkauf(standort=1, nur_stellantis=False)

# Für dealer_vehicles (Bestand)
filter_bestand = build_locosoft_filter_bestand(standort=1, nur_stellantis=False)

# Für orders/invoices
filter_orders = build_locosoft_filter_orders(standort=1)
```

### Logik

**dealer_vehicles (Verkäufe):**
- Deggendorf Opel: `out_subsidiary = 1`
- Deggendorf Hyundai: `out_subsidiary = 2`
- Deggendorf (beide): `out_subsidiary IN (1, 2)`
- Landau: `out_subsidiary = 3` ✅ **VERIFIZIERT**

**dealer_vehicles (Bestand):**
- Gleiche Logik, aber `in_subsidiary` statt `out_subsidiary`

**orders/invoices:**
- Deggendorf Opel: `subsidiary = 1`
- Deggendorf Hyundai: `subsidiary = 2`
- Deggendorf (beide): `subsidiary IN (1, 2)`
- Landau: `subsidiary = 3` ✅ **VERIFIZIERT**

### Spezialfälle

**Opel DEG (nur Stellantis, ohne Hyundai):**
```python
build_locosoft_filter_verkauf(standort=1, nur_stellantis=True)
# Filtert: Nur subsidiary = 1
```

**Deggendorf (beide):**
```python
build_locosoft_filter_verkauf(standort=1, nur_stellantis=False)
# Filtert: subsidiary IN (1, 2)
```

---

## 🔍 BEREICHS-SPEZIFISCHE LOGIK

### Werkstatt, Teile, Sonstige
**Keine Marken-Unterscheidung!**
- Standort 1 (Deggendorf): Beide Firmen (Stellantis + Hyundai)
- Standort 3 (Landau): Beide Firmen (Stellantis + Hyundai)

**BWA-Filter:**
```python
# Deggendorf: branch_number = 1 (beide Firmen)
# Landau: branch_number = 3 (beide Firmen)
```

**Locosoft-Filter:**
```python
# Deggendorf: subsidiary IN (1, 2)
# Landau: subsidiary = ? ⚠️
```

### NW (Neuwagen), GW (Gebrauchtwagen)
**Firma + Standort Filterung!**
- Standort 1, 3: Nur Stellantis (`subsidiary_to_company_ref = 1`)
- Standort 2: Nur Hyundai (`subsidiary_to_company_ref = 2`)

**BWA-Filter:**
```python
# Deggendorf: branch_number = 1 + subsidiary_to_company_ref = 1
# Landau: branch_number = 3 + subsidiary_to_company_ref = 1
# Hyundai: branch_number = 2 + subsidiary_to_company_ref = 2
```

**Locosoft-Filter:**
```python
# Deggendorf: out_subsidiary = 1
# Landau: out_subsidiary = ? ⚠️
# Hyundai: out_subsidiary = 2
```

---

## ⚠️ BEKANNTE PROBLEME

### 1. Landau subsidiary-Wert ✅ GELÖST
**Problem:** Landau wurde fälschlicherweise mit `subsidiary = 1` gefiltert.

**Lösung:** ✅ **KORRIGIERT** - Landau verwendet `subsidiary = 3` (LANO location)
- Verifiziert durch `scripts/analyse_landau_locosoft.py`
- Alle Filter-Funktionen in `api/standort_utils.py` aktualisiert

### 2. Inkonsistente Implementierungen
**Problem:** Verschiedene Dateien verwenden unterschiedliche Filter-Logik:
- `api/controlling_api.py`: BWA-Filter (korrekt)
- `api/gewinnplanung_v2_gw_data.py`: Locosoft-Filter (möglicherweise falsch)
- `api/abteilungsleiter_planung_data.py`: Mischung

**Lösung:** Alle Dateien auf `api/standort_utils.py` umstellen.

---

## 📝 MIGRATION: Bestehende Dateien aktualisieren

### Dateien, die aktualisiert werden müssen:
1. `api/gewinnplanung_v2_gw_data.py` - Locosoft-Filter
2. `api/abteilungsleiter_planung_data.py` - BWA + Locosoft-Filter
3. `routes/controlling_routes.py` - Locosoft-Filter
4. Weitere Dateien nach Bedarf

### Vorgehen:
1. Import hinzufügen: `from api.standort_utils import ...`
2. Alte Filter-Logik entfernen
3. Zentrale Funktionen verwenden
4. Testen!

---

## 🔗 REFERENZEN

- **Zentrale Funktionen:** `api/standort_utils.py`
- **BWA-Filter (alt, wird ersetzt):** `api/controlling_api.py::build_firma_standort_filter()`
- **Session-Dokumentation:** `docs/sessions/ALLE_KOSTENSTELLEN_SSOT_ANALYSE_TAG167.md`

---

**WICHTIG:** Wenn du Standort-Filter brauchst, **IMMER** `api/standort_utils.py` verwenden!  
**NIEMALS** eigene Filter-Logik schreiben!

