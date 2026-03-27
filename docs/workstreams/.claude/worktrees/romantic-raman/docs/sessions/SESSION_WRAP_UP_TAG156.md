# SESSION WRAP-UP TAG 156

**Datum:** 2026-01-02
**Fokus:** Budget-Wizard Finalisierung + GlobalCube Exploration + Standort-Filter

---

## ERREICHT

### 1. GlobalCube Q:\ Laufwerk erfolgreich exploriert

Zugriff auf `\\srvgc01\GlobalCube` hergestellt und Struktur analysiert:

**Cube-Verzeichnis (`Q:\Cubes`):**
- Taegliche Cube-Generierung (z.B. `v_verkauf__20260102084631`)
- MDC-Files (MultiDimensional Cubes) fuer IBM Cognos PowerPlay
- Bereiche: v_verkauf, s_aftersales, z_monteure, f_belege, etc.

**CSV-Exporte (`Q:\System\LOCOSOFT\Export`):**
- `LOC_Belege_NW_GW_VK.csv` (15 MB) - NW/GW Verkaufsbelege
- `loc_belege.csv` (102 MB) - Alle Buchungen
- Taeglich um ~09:40 aktualisiert

**Extrahierte Daten 2022-2025:**
| Jahr | NW Stueck | GW Stueck | Gesamt |
|------|-----------|-----------|--------|
| 2023 | 162 | 213 | 375 |
| 2024 | 563 | 764 | 1.327 |
| 2025 | 492 | 788 | 1.280 |

**Hinweis:** Bruttoertrag-Werte sind in den CSVs leer - werden in PowerPlay Cubes aggregiert.

### 2. Budget-Wizard Speichern implementiert

**Neuer API-Endpoint:**
```
POST /api/budget/wizard/<typ>/speichern
```

Features:
- Speichert Jahresplan auf alle 12 Monate (Saisonalisierung)
- Verteilt automatisch auf Standorte (DEG 48%, HYU 26-44%, LAN 8-26%)
- PostgreSQL UPSERT (ON CONFLICT UPDATE)
- Rueckgabe mit Standort-Verteilung

### 3. Frontend komplett funktional

`verkauf_budget_wizard.html` erweitert:
- `savePlan()` ruft jetzt API `/wizard/<typ>/speichern`
- Erfolgs-Modal mit Standort-Verteilung
- Automatischer Redirect zum Dashboard nach 2.5s
- Fehlerbehandlung mit Button-Reset

### 4. Dashboard-Link zum Wizard

`verkauf_budget.html`:
- Neuer Button "5-Fragen-Wizard" (gelb) im Hero-Bereich
- Direktlink zu `/verkauf/budget/wizard`

---

## DATEIEN ERSTELLT/GEAENDERT

### Neu erstellt:
1. `projects/budget_planungsmodul/extract_globalcube_data.py` - CSV-Parser fuer GlobalCube
2. `projects/budget_planungsmodul/GREINER_HISTORISCH_2022_2025.md` - Extrahierte Daten
3. `projects/budget_planungsmodul/globalcube_verkauf_2022_2025.json` - JSON-Export

### Geaendert:
1. `api/budget_api.py` - Neuer Endpoint `wizard_speichern()`
2. `templates/verkauf_budget_wizard.html` - `savePlan()` mit API-Call
3. `templates/verkauf_budget.html` - Wizard-Button im Hero

---

## TECHNISCHE DETAILS

### GlobalCube Architektur

```
Q:\
├── Cubes/                 # Taeglich generierte MDC-Files
│   ├── v_verkauf__YYYYMMDD...
│   ├── s_aftersales__...
│   └── ...
├── GCStruct/             # Struktur-Definitionen
│   ├── Kontenrahmen/     # SKR51 Mapping
│   └── Export/           # Export-Definitionen
└── System/LOCOSOFT/Export/  # CSV-Rohdaten
    ├── loc_belege.csv    # 102 MB
    ├── LOC_Belege_NW_GW_VK.csv
    └── ...
```

### Wizard-Speicher-Flow

```
1. Frontend: formValues sammeln
2. POST /api/budget/wizard/NW/speichern
3. Backend:
   - Bruttoertrag, DB1, Umsatz berechnen
   - Saisonalisierung anwenden (12 Monate)
   - Standort-Verteilung (3 Standorte)
   - 36 INSERTs in budget_plan
4. Response mit Zusammenfassung
5. Frontend: Modal + Redirect
```

### Standort-Verteilung (basierend auf 2024)

| Typ | DEG Opel | HYU | Landau |
|-----|----------|-----|--------|
| NW  | 48%      | 44% | 8%     |
| GW  | 48%      | 26% | 26%    |

---

## ARCHITEKTUR-ERKENNTNISSE (GlobalCube)

Fuer DRIVE uebernehmen:
1. **Pre-aggregierte Daten** - Unsere `_data.py` Module = "Cubes"
2. **Taegliche Snapshots** - Celery-Jobs fuer Materialized Views
3. **Klare Datenpipeline** - Rohdaten -> Aggregation -> Report

### 5. Standort-Filter im Wizard (Teil 2 der Session)

**Datei:** `templates/verkauf_budget_wizard.html`

Neu hinzugefuegt:
- Standort-Selector mit 4 Buttons (Alle, Deggendorf, DEG Hyundai, Landau)
- Landau-Warnung mit rotem Badge "BE negativ!" bei NW
- Standort-spezifische IST-Daten werden automatisch geladen
- Speichern sendet Standort-ID mit (oder verteilt auf alle)

**JavaScript-Erweiterungen:**
- `selectStandort(id)` - Wechselt Standort und laedt Daten neu
- `updateStandortButtons()` - Zeigt Stk/BE pro Standort
- `STANDORT_DATEN` - Lokale Konstante mit IST 2024 Daten

### 6. Wizard-Plaene im Dashboard

**Datei:** `templates/verkauf_budget.html`

Neu:
- Sektion "Budget 2026 (Wizard-Plan)" wird angezeigt wenn Plaene existieren
- Zeigt NW/GW Stueck und DB1 als KPI-Cards
- Link zum Wizard zum Bearbeiten
- Letzte Aenderung und Standort-Verteilung im Footer

**API-Endpoint:**
```
GET /api/budget/wizard-plaene?jahr=2026
```

Response:
- `plaene[]` - Liste aller gespeicherten Plaene
- `zusammenfassung` - NW/GW Totals
- `letzte_aenderung`, `erstellt_von`, `strategie`

---

## OFFEN / NAECHSTE SCHRITTE

### Fuer TAG 157:

1. **teile_data.py starten** (Option B aus TAG 154)
   - SSOT fuer Teilelager/Renner-Penner

2. **PDF-Export fuer Budget-Plan** (optional)

3. **Locosoft SOAP Client** (Option C)

---

## DATEIEN GEAENDERT (Teil 2)

1. `templates/verkauf_budget_wizard.html` - Standort-Selector + Landau-Warnung
2. `templates/verkauf_budget.html` - Wizard-Plan-Anzeige
3. `api/budget_api.py` - Neuer Endpoint `/wizard-plaene`

---

## API-ENDPOINTS (TAG 156)

```
# Bestehend (TAG 155):
GET  /api/budget/globalcube-ist/2024
GET  /api/budget/wizard/NW?standort=1  # Mit Standort-Filter!
GET  /api/budget/wizard/GW?standort=2
GET  /api/budget/wizard/NW
GET  /api/budget/wizard/GW
POST /api/budget/wizard/NW/berechnen
POST /api/budget/wizard/GW/berechnen

# Neu (TAG 156):
POST /api/budget/wizard/NW/speichern
POST /api/budget/wizard/GW/speichern
GET  /api/budget/wizard-plaene?jahr=2026  # Gespeicherte Plaene abrufen
```

---

## PORTAL URLs

- **Budget-Dashboard:** https://drive.auto-greiner.de/verkauf/budget
- **Budget-Wizard:** https://drive.auto-greiner.de/verkauf/budget/wizard

---

## GLOBALCUBE ZUGRIFF

Windows Netzlaufwerk:
```
Q:\ -> \\srvgc01\GlobalCube
```

Wichtige Pfade:
```
Q:\Cubes\v_verkauf__*          # Verkaufs-Cubes
Q:\System\LOCOSOFT\Export\     # CSV-Rohdaten
Q:\GCStruct\Kontenrahmen\      # SKR51-Mapping
```

---

*Erstellt: 2026-01-02 | TAG 156*
