# Features mit Standort-Filter - Übersicht TAG 177

**Datum:** 2026-01-10  
**Zweck:** Vollständige Liste aller Features mit Standort-Filter für Migration auf zentrales Component

---

## Kategorisierung

### ✅ Bereits umgesetzt (mit Tab-Navigation)
- ✅ **Abteilungsleiter-Planung** (`planung/abteilungsleiter_uebersicht.html`)
  - Route: `routes/planung_routes.py`
  - Verwendet: `components/standort_filter_tabs.html`

---

## 🔄 Sollten migriert werden (Dropdown-Filter)

### Controlling
1. **TEK Dashboard V2** (`controlling/tek_dashboard_v2.html`)
   - Route: `routes/controlling_routes.py` → `api_tek()`
   - Filter: Firma + Standort (Dropdowns)
   - Parameter: `firma`, `standort`
   - **Priorität: Hoch** (wird häufig verwendet)

2. **BWA** (`controlling/bwa.html`, `controlling/bwa_v1.html`)
   - Route: `routes/controlling_routes.py`
   - Filter: Firma + Standort (Dropdowns)
   - Parameter: `firma`, `standort`
   - **Priorität: Hoch**

3. **KST-Ziele** (`controlling/kst_ziele.html`)
   - Route: `routes/controlling_routes.py` → `kst_ziele_dashboard()`
   - Filter: Standort (Dropdown)
   - Parameter: `standort`
   - **Priorität: Mittel**

4. **Unternehmensplan** (`controlling/unternehmensplan.html`)
   - Route: `routes/controlling_routes.py` → `unternehmensplan_dashboard()`
   - Filter: Firma + Standort (Dropdowns)
   - Parameter: `firma`, `standort`
   - **Priorität: Mittel**

### Verkauf
5. **GW Dashboard** (`verkauf_gw_dashboard.html`)
   - Route: `routes/app.py` → `verkauf_gw_dashboard()`
   - Filter: Standort (Dropdown)
   - Parameter: `standort`
   - **Priorität: Hoch**

6. **Budget Wizard** (`verkauf_budget_wizard.html`)
   - Route: `routes/app.py`
   - Filter: Standort (Dropdown)
   - Parameter: `standort`
   - **Priorität: Mittel**

7. **Lieferforecast** (`verkauf_lieferforecast.html`)
   - Route: `routes/app.py`
   - Filter: Standort (Dropdown)
   - Parameter: `standort`
   - **Priorität: Niedrig**

8. **Auftragseingang** (`verkauf_auftragseingang.html`)
   - Route: `routes/app.py`
   - Filter: Standort (Dropdown, JavaScript)
   - Parameter: `location` (JavaScript)
   - **Priorität: Mittel**

### Planung
9. **Gesamtplanung** (`planung/gesamtplanung.html`)
   - Route: `routes/planung_routes.py` → `gesamtplanung()`
   - Filter: Standort (Dropdown)
   - Parameter: `standort`
   - **Priorität: Mittel**

10. **Stundensatz-Kalkulation** (`planung/stundensatz_kalkulation.html`)
    - Route: `routes/planung_routes.py`
    - Filter: Standort (Dropdown)
    - Parameter: `standort`
    - **Priorität: Niedrig**

### Werkstatt / After Sales
11. **Werkstatt Dashboard** (`sb/werkstatt_dashboard.html`, `aftersales/werkstatt_dashboard.html`)
    - Route: `routes/werkstatt_routes.py`
    - Filter: Betrieb (Button-Gruppe)
    - Parameter: `betrieb` (1, 3)
    - **Besonderheit:** Button-Gruppe statt Dropdown
    - **Priorität: Hoch**

12. **Werkstatt Aufträge** (`sb/werkstatt_auftraege.html`, `aftersales/werkstatt_auftraege.html`)
    - Route: `routes/werkstatt_routes.py`
    - Filter: Betrieb (Dropdown)
    - Parameter: `betrieb`
    - **Priorität: Mittel**

13. **Werkstatt Übersicht** (`sb/werkstatt_uebersicht.html`, `aftersales/werkstatt_uebersicht.html`)
    - Route: `routes/werkstatt_routes.py`
    - Filter: Betrieb (Dropdown)
    - Parameter: `betrieb`
    - **Priorität: Mittel**

14. **Renner/Penner** (`sb/renner_penner.html`, `aftersales/renner_penner.html`)
    - Route: `routes/werkstatt_routes.py`
    - Filter: Betrieb (Dropdown)
    - Parameter: `betrieb`
    - **Priorität: Niedrig**

15. **Werkstatt Anwesenheit** (`sb/werkstatt_anwesenheit.html`, `aftersales/werkstatt_anwesenheit.html`)
    - Route: `routes/werkstatt_routes.py`
    - Filter: Betrieb (Dropdown)
    - Parameter: `betrieb`
    - **Priorität: Niedrig**

16. **Werkstatt Stempeluhr** (`sb/werkstatt_stempeluhr.html`, `aftersales/werkstatt_stempeluhr.html`)
    - Route: `routes/werkstatt_routes.py`
    - Filter: Betrieb (Dropdown)
    - Parameter: `betrieb`
    - **Priorität: Niedrig**

17. **Kapazitätsplanung** (`sb/kapazitaetsplanung.html`, `aftersales/kapazitaetsplanung.html`)
    - Route: `routes/werkstatt_routes.py`
    - Filter: Betrieb (Dropdown)
    - Parameter: `betrieb`
    - **Priorität: Niedrig**

18. **Teile Status** (`sb/werkstatt_teile_status.html`, `aftersales/werkstatt_teile_status.html`)
    - Route: `routes/werkstatt_routes.py`
    - Filter: Betrieb (Dropdown)
    - Parameter: `betrieb`
    - **Priorität: Niedrig**

### Sonstige
19. **Urlaubsplaner V2** (`urlaubsplaner_v2.html`)
    - Route: `routes/app.py`
    - Filter: Standort (Dropdown)
    - Parameter: `standort`
    - **Priorität: Mittel**

20. **Organigramm** (`organigramm.html`)
    - Route: `routes/app.py`
    - Filter: Standort (Dropdown)
    - Parameter: `standort`
    - **Priorität: Niedrig**

---

## 📊 Zusammenfassung

### Nach Kategorie:
- **Controlling:** 4 Features
- **Verkauf:** 4 Features
- **Planung:** 2 Features (1 bereits umgesetzt)
- **Werkstatt/After Sales:** 8 Features
- **Sonstige:** 2 Features

### Nach Priorität:
- **Hoch:** 5 Features (TEK, BWA, GW Dashboard, Werkstatt Dashboard, Abteilungsleiter-Planung ✅)
- **Mittel:** 8 Features
- **Niedrig:** 7 Features

### Nach Filter-Typ:
- **Dropdown:** 18 Features
- **Button-Gruppe:** 1 Feature (Werkstatt Dashboard)
- **Tabs:** 1 Feature ✅ (Abteilungsleiter-Planung)

---

## Migration-Plan

### Phase 1: High-Priority Features
1. TEK Dashboard V2
2. BWA
3. GW Dashboard
4. Werkstatt Dashboard (Button → Tabs)

### Phase 2: Medium-Priority Features
5. KST-Ziele
6. Unternehmensplan
7. Budget Wizard
8. Auftragseingang
9. Gesamtplanung
10. Werkstatt Aufträge/Übersicht

### Phase 3: Low-Priority Features
11. Alle anderen Features

---

## Besonderheiten

### Werkstatt-Features
- Verwenden `betrieb` statt `standort`
- Nur Betrieb 1 (Deggendorf) und 3 (Landau)
- Kein Betrieb 2 (Hyundai DEG)
- **Lösung:** Component erweitern für `betrieb`-Parameter

### Firma + Standort Kombination
- TEK, BWA, Unternehmensplan haben Firma + Standort
- **Lösung:** Component erweitern oder separate Firma-Filter behalten

### JavaScript-Filter
- Auftragseingang verwendet JavaScript für Filter
- **Lösung:** Auf Server-Side Filter umstellen oder Component mit JavaScript-Integration

---

**Status:** 📋 Analyse abgeschlossen, ⏳ Migration offen
