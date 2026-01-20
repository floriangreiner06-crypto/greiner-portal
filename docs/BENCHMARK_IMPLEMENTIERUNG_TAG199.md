# Benchmark-Implementierung Phase 1 - TAG 199

**Datum:** 2026-01-XX  
**Status:** ✅ Implementiert (Backend), ⏳ Dashboard noch offen

---

## ✅ IMPLEMENTIERT

### 1. **SSOT: Benchmark-Werte** (`utils/kpi_definitions.py`)

**Hinzugefügt:**
- `MARKT_BENCHMARKS` Dict mit allen Branchendurchschnittswerten
- `get_markt_benchmark(kpi_name)` - Holt Benchmark-Wert
- `vergleiche_mit_markt(ist_wert, kpi_name)` - Vergleicht Ist vs. Benchmark

**Benchmark-Werte:**
- Leistungsgrad: 100%
- Auslastungsgrad: 90%
- Anwesenheitsgrad: 79%
- Effizienz: 71%
- Stundensatz: 148,55 € (Durchschnitt Deutschland)
- Stunden pro Durchgang: 1,8h
- Bruttomarge: 45%
- Teile-Marge: 58%
- Kundenbindungsrate: 75%

**Quelle:** DAT Report, IBISWorld, Auto Zeitung (2023-2025)

### 2. **API erweitert** (`api/werkstatt_api.py`)

**Hinzugefügt:**
- Benchmark-Vergleiche für alle Haupt-KPIs
- Neue Response-Feld: `benchmarks` mit Vergleichsdaten

**Vergleiche:**
- Leistungsgrad vs. Markt
- Produktivität vs. Markt
- Anwesenheitsgrad vs. Markt
- Effizienz vs. Markt
- Stundensatz vs. Markt
- Stunden pro Durchgang vs. Markt

**Response-Format:**
```json
{
  "benchmarks": {
    "leistungsgrad": {
      "ist": 85.0,
      "benchmark": 100.0,
      "differenz": -15.0,
      "differenz_prozent": -15.0,
      "status": "schlechter",
      "icon": "📉"
    },
    ...
  }
}
```

### 3. **Exports** (`utils/__init__.py`)

**Hinzugefügt:**
- `MARKT_BENCHMARKS`
- `get_markt_benchmark`
- `vergleiche_mit_markt`

---

## ⏳ AUSSTEHEND

### 4. **Dashboard erweitern** (`templates/aftersales/werkstatt_uebersicht.html`)

**Geplant:**
- Benchmark-Vergleiche in KPI-Cards anzeigen
- "vs. Branchendurchschnitt" Badges
- Farbcodierung (grün = besser, rot = schlechter)
- Tooltips mit Details

**Beispiel:**
```
Leistungsgrad: 85% 📉 vs. Markt 100% (-15%)
```

---

## 📋 NÄCHSTE SCHRITTE

1. **Dashboard erweitern** (Frontend)
   - Benchmark-Vergleiche in KPI-Cards
   - Badges mit Status-Icons
   - Tooltips mit Details

2. **WESP-Termin** (morgen)
   - API-Preis klären
   - Datenschutz klären
   - Entscheidung: WESP API oder statische Benchmarks

3. **Phase 2 (optional)**
   - WESP API-Integration (falls Preis akzeptabel)
   - Dynamische Benchmarks statt statische

---

## 🎯 ARCHITEKTUR

**SSOT-Prinzip befolgt:**
- ✅ Alle Benchmark-Werte in `utils/kpi_definitions.py` (SSOT)
- ✅ Vergleichs-Logik zentral in `vergleiche_mit_markt()`
- ✅ API nutzt SSOT-Funktionen
- ✅ Keine Redundanzen

**Struktur:**
```
utils/kpi_definitions.py (SSOT)
  ├── MARKT_BENCHMARKS (Dict)
  ├── get_markt_benchmark() (Funktion)
  └── vergleiche_mit_markt() (Funktion)
       ↓
api/werkstatt_api.py
  └── Nutzt SSOT-Funktionen
       ↓
templates/aftersales/werkstatt_uebersicht.html
  └── Zeigt Benchmark-Vergleiche an
```

---

**Erstellt:** TAG 199  
**Status:** ✅ Backend fertig, ⏳ Frontend ausstehend
