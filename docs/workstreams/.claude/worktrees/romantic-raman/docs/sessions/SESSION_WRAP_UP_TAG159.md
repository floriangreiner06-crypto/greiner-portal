# SESSION WRAP-UP TAG 159/160

**Datum:** 2026-01-02
**Fokus:** Sales/Fahrzeug Data-Module (SSOT Pattern) + GW-Dashboard

---

## ERREICHT

### 1. fahrzeug_data.py erstellt (SSOT Fahrzeugbestand)

**Datei:** `api/fahrzeug_data.py` (659 LOC)

Neues Data-Modul für Fahrzeug-Bestandsdaten direkt aus Locosoft:

| Methode | Beschreibung |
|---------|--------------|
| `get_gw_bestand()` | GW-Bestand mit Standzeit-Kategorien |
| `get_nw_pipeline()` | Bestellte NW (nicht fakturiert) |
| `get_vfw_bestand()` | Vorführwagen-Bestand |
| `get_standzeit_statistik()` | Aggregierte Standzeit-Stats |
| `get_standzeit_warnungen()` | Fahrzeuge die Aktion brauchen |
| `get_bestand_nach_standort()` | Übersicht nach Standort |

**Standzeit-Kategorien:**
- `frisch`: 0-60 Tage
- `ok`: 61-90 Tage
- `risiko`: 91-120 Tage
- `penner`: 121-180 Tage
- `leiche`: >180 Tage

### 2. verkauf_data.py erstellt (SSOT Verkauf)

**Datei:** `api/verkauf_data.py` (875 LOC)

Neues Data-Modul für Verkaufs/Sales-Daten:

| Methode | Beschreibung |
|---------|--------------|
| `get_auftragseingang()` | Aufträge heute + Monat |
| `get_auftragseingang_summary()` | Nach Marke aggregiert |
| `get_auftragseingang_detail()` | Mit Modell-Aufschlüsselung |
| `get_auslieferung_summary()` | Auslieferungen nach Marke |
| `get_auslieferung_detail()` | Einzelfahrzeuge mit DB |
| `get_verkaufer_liste()` | Alle Verkäufer |
| `get_lieferforecast()` | Geplante Lieferungen |
| `get_verkaufer_performance()` | Performance-KPIs **NEU** |

### 3. verkauf_api.py refaktoriert

**Version:** 3.0 (vorher 2.4)
**Reduzierung:** ~1270 → ~480 LOC (-62%)

Alle Datenlogik nach `verkauf_data.py` ausgelagert:
- API-Layer nur noch für HTTP-Handling
- Konsistentes Return-Format
- Neuer Endpoint: `/api/verkauf/performance`

---

## ARCHITEKTUR-PATTERN

### Data-Module (SSOT)

```
api/werkstatt_data.py    - Werkstatt (Mechaniker, Aufträge)
api/fahrzeug_data.py     - Bestand (GW, NW, VFW)        **NEU**
api/verkauf_data.py      - Sales (Aufträge, Auslieferungen)  **NEU**
api/controlling_data.py  - TEK, BWA
api/unternehmensplan_data.py - GlobalCube BWA
```

### Pattern-Regeln

1. **Class-based** mit `@staticmethod`
2. **Logging** mit `logger.info()` für Tracing
3. **Docstrings** mit Args/Returns/Example
4. **Return Dict** mit `success`, `data`, `meta`
5. **Wrapper Functions** am Ende für direkten Import
6. **Keine Business Logic** - nur Datenabruf + Aggregation

### Locosoft-Tabellen

```sql
-- Fahrzeuge
dealer_vehicles: Händlerfahrzeuge (Bestand, Kalkulation)
vehicles: Stammdaten (VIN, Modell, EZ)
JOIN: dv.vehicle_number = v.internal_number

-- Fahrzeugtypen
N = Neuwagen, G = Gebrauchtwagen, D = Demo/VFW, V = Vermietwagen, T = Tausch

-- Standorte
1 = DEG Opel, 2 = DEG Hyundai, 3 = Landau
```

---

## NEUE ENDPOINTS

### Fahrzeug-API (noch nicht registriert)

```
/api/fahrzeug/gw              - GW-Bestand
/api/fahrzeug/gw/statistik    - Standzeit-Statistik
/api/fahrzeug/gw/warnungen    - Problemfälle
/api/fahrzeug/nw              - NW-Pipeline
/api/fahrzeug/vfw             - VFW-Bestand
/api/fahrzeug/standorte       - Bestand nach Standort
```

### Verkauf-API (erweitert)

```
/api/verkauf/performance      - NEU: Verkäufer-Performance
```

---

## DATEIEN

### Erstellt
- `api/fahrzeug_data.py` - 659 LOC
- `api/verkauf_data.py` - 875 LOC
- `api/fahrzeug_api.py` - ~180 LOC
- `templates/verkauf_gw_dashboard.html` - GW-Dashboard mit Standzeit-Ampel
- `docs/sessions/SESSION_WRAP_UP_TAG159.md`
- `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG160.md`

### Geändert
- `api/verkauf_api.py` - Refaktoriert auf Data-Module
- `app.py` - fahrzeug_api Blueprint registriert
- `routes/verkauf_routes.py` - GW-Dashboard Route hinzugefügt

---

## TAG 160 - FORTSETZUNG (gleiche Session)

### 4. fahrzeug_api.py erstellt

**Datei:** `api/fahrzeug_api.py` (~180 LOC)

Blueprint für Fahrzeug-Endpoints:

| Endpoint | Beschreibung |
|----------|--------------|
| `/api/fahrzeug/health` | Health Check |
| `/api/fahrzeug/gw` | GW-Bestand mit Filtern |
| `/api/fahrzeug/gw/statistik` | Standzeit-Statistik |
| `/api/fahrzeug/gw/warnungen` | Problemfälle (>90 Tage) |
| `/api/fahrzeug/gw/dashboard` | Kombinierte Dashboard-Daten |
| `/api/fahrzeug/nw` | NW-Pipeline |
| `/api/fahrzeug/vfw` | VFW-Bestand |
| `/api/fahrzeug/standorte` | Bestand nach Standort |

### 5. GW-Dashboard Template erstellt

**Datei:** `templates/verkauf_gw_dashboard.html`
**URLs:** `/verkauf/gw-bestand` oder `/verkauf/gw-dashboard`

Features:
- Statistik-Karten (Bestand, Lagerwert, Problemfälle)
- Standzeit-Ampel (klickbar zum Filtern)
- Top 10 Problemfälle-Tabelle
- Fahrzeugliste mit allen Details
- Filter nach Standort und Kategorie

---

## NÄCHSTE SCHRITTE (TAG 161)

1. **Gap-Tracker implementieren**
   - Aus TAG 158 Gap-Analyse
   - Monatlicher IST vs SOLL Vergleich

2. **CSV-Export für GW-Dashboard**

3. **Testen auf Server**

---

## CODE-BEISPIELE

### fahrzeug_data.py nutzen

```python
from api.fahrzeug_data import FahrzeugData

# GW-Bestand mit Standzeit > 90 Tage
data = FahrzeugData.get_gw_bestand(kategorie='risiko')
print(f"{len(data['fahrzeuge'])} Risiko-Fahrzeuge")

# Standzeit-Statistik
stats = FahrzeugData.get_standzeit_statistik()
print(f"Problemfälle: {stats['problemfaelle']['anzahl']}")
```

### verkauf_data.py nutzen

```python
from api.verkauf_data import VerkaufData

# Auftragseingang Dezember
data = VerkaufData.get_auftragseingang(month=12, year=2025)
print(f"Heute: {data['summe_heute']['gesamt']} Aufträge")

# Verkäufer-Performance
perf = VerkaufData.get_verkaufer_performance(month=12, year=2025)
for vk in perf['performance']:
    print(f"{vk['verkaufer_name']}: {vk['db1_prozent']}% DB")
```

---

*Erstellt: TAG 159 | Autor: Claude AI*
