# SESSION WRAP-UP TAG 155

**Datum:** 2026-01-02
**Fokus:** Budget-Planungsmodul mit 5-Fragen-Wizard

---

## ERREICHT

### 1. GlobalCube-Datenextraktion
- **Planung_2025.xlsx** analysiert und Struktur verstanden
- IST-Daten 2024 fuer NW und GW vollstaendig extrahiert
- Python 3.12 auf Windows installiert (C:\Program Files\Python312\python.exe)
- openpyxl installiert fuer Excel-Parsing

### 2. Benchmark-Dokumentation erstellt
**Datei:** `projects/budget_planungsmodul/GREINER_BENCHMARK_2024.md`

Extrahierte Kennzahlen:
| Bereich | Stueck | Umsatz | Bruttoertrag | BE/Fzg |
|---------|--------|--------|--------------|--------|
| NW | 535 | 14.58 Mio | 1.69 Mio | 3.165 |
| GW | 615 | 9.88 Mio | 1.10 Mio | 1.795 |
| **Gesamt** | **1.150** | **24.46 Mio** | **2.80 Mio** | **2.432** |

**Standort-Analyse:**
- DEG Hyundai: Beste Performance (742k BE bei 397 Fzg)
- Landau NW: KRITISCH (-56k Betriebsergebnis)

### 3. budget_data.py SSOT-Modul
**Datei:** `api/budget_data.py`

Neues Datenmodul mit:
- `BudgetData` Klasse als Single Source of Truth
- `GREINER_IST_2024` - Komplette 2024 IST-Daten
- `BRANCHEN_BENCHMARKS` - DEKRA/ZDK Vergleichswerte
- `SAISONALISIERUNG` - Monatsverteilung in %
- Methoden: `get_ist_vorjahr()`, `get_empfehlungen()`, `calculate_monthly()`

### 4. budget_api.py erweitert
**Datei:** `api/budget_api.py`

Neue Endpoints (TAG 155):
- `GET /api/budget/globalcube-ist/<jahr>` - IST-Daten aus Excel
- `GET /api/budget/wizard/<typ>` - 5-Fragen-Wizard Daten
- `POST /api/budget/wizard/<typ>/berechnen` - Budget berechnen

Ergaenzungen:
- `GLOBALCUBE_IST_2024` Dict mit allen Standort-Daten
- `BRANCHEN_BENCHMARKS` und `SAISONALISIERUNG`

### 5. Budget-Wizard Frontend
**Datei:** `templates/verkauf_budget_wizard.html`

Features:
- 5-Fragen-Wizard mit Slider-Eingaben
- Typ-Auswahl (NW/GW) mit Live-Update
- Progress-Dots fuer Schritte
- Vorjahres-Benchmarks als Default-Werte
- Bewertungs-Badges (excellent/gut/kritisch)
- Strategie-Auswahl (konservativ/moderat/ambitioniert)
- Zusammenfassung mit Monatsverteilung

### 6. Route hinzugefuegt
**Datei:** `routes/verkauf_routes.py`

Neue Route:
- `/verkauf/budget/wizard` bzw. `/verkauf/planung/wizard`

---

## DATEIEN ERSTELLT/GEAENDERT

### Neu erstellt:
1. `projects/budget_planungsmodul/GREINER_BENCHMARK_2024.md`
2. `projects/budget_planungsmodul/extract_excel.py`
3. `projects/budget_planungsmodul/KONZEPT_DRIVE_BUDGET_PLANUNG.md`
4. `api/budget_data.py`
5. `templates/verkauf_budget_wizard.html`

### Geaendert:
1. `api/budget_api.py` - Neue Wizard-Endpoints + IST-Daten
2. `routes/verkauf_routes.py` - Neue Wizard-Route

---

## TECHNISCHE DETAILS

### Python Installation (Windows)
```
C:\Program Files\Python312\python.exe
```
Mit openpyxl fuer Excel-Verarbeitung.

### Neue API-Endpoints
```
GET  /api/budget/globalcube-ist/2024
GET  /api/budget/wizard/NW
GET  /api/budget/wizard/GW
POST /api/budget/wizard/NW/berechnen
POST /api/budget/wizard/GW/berechnen
```

### Wizard-Fragen
1. Stueckzahl-Ziel (Slider)
2. Bruttoertrag pro Fahrzeug (Slider + Benchmark)
3. Variable Kosten-Quote (Slider, invertiert)
4. Wachstumsstrategie (Auswahl: konservativ/moderat/ambitioniert)
5. Bestaetigung mit Zusammenfassung

---

## OFFEN / NAECHSTE SCHRITTE

### Fuer TAG 156:
1. **Wizard-Speichern** implementieren (POST in budget_plan Tabelle)
2. **Verlinkung** im Budget-Dashboard zum Wizard
3. **Standort-Filter** im Wizard ergaenzen (Deggendorf/Hyundai/Landau)
4. **teile_data.py** fuer Lager-Modul fortsetzen (Option B aus TAG 154)

### Optional:
- Locosoft SOAP Client starten (Option C aus TAG 154)
- PDF-Export fuer Budget-Plan

---

## HINWEISE FUER NAECHSTE SESSION

### Zugriff auf Budget-Wizard:
```
https://drive.auto-greiner.de/verkauf/budget/wizard
```

### Test der API:
```bash
curl http://10.80.80.20:5000/api/budget/wizard/NW
curl http://10.80.80.20:5000/api/budget/globalcube-ist/2024
```

### Python auf Windows:
```cmd
"C:\Program Files\Python312\python.exe" -m pip list
```

---

*Erstellt: 2026-01-02 | TAG 155*
