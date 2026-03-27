# TODO FOR CLAUDE - SESSION START TAG 157

**Letzte Session:** TAG 156 (2026-01-02)
**Ziel:** Naechstes Modul starten

---

## KONTEXT

TAG 156 hat das **Budget-Planungsmodul komplett abgeschlossen**:

### Wizard Features:
- 5-Fragen-Wizard mit Slider-Eingaben
- Standort-Selector (Alle, DEG Opel, DEG Hyundai, Landau)
- Landau-Warnung mit "BE negativ!" Badge bei NW
- Speichern in budget_plan Tabelle (36 Eintraege: 3 Standorte x 12 Monate)
- Erfolgs-Modal mit Standort-Verteilung

### Dashboard Integration:
- Wizard-Plan-Sektion zeigt NW/GW Stueck + DB1
- Bearbeiten-Button fuehrt zum Wizard
- Letzte Aenderung + Standort-Verteilung angezeigt

### GlobalCube Exploration:
- Q:\ Laufwerk gemappt (\\srvgc01\GlobalCube)
- Cubes-Struktur analysiert
- CSV-Exporte gefunden (102 MB loc_belege.csv)
- Stueckzahlen 2022-2025 extrahiert

---

## AUFGABEN TAG 157

### Option A: teile_data.py (SSOT Teilelager)

Naechstes Datenmodul fuer Teile/Lager:
```python
class TeileData:
    @staticmethod
    def get_lagerbestand(standort=None)
    @staticmethod
    def get_umschlaghaeufigkeit(zeitraum='12m')
    @staticmethod
    def get_renner_penner(standort=None)
    @staticmethod
    def get_bestellvorschlaege()
```

Consumer: parts_api.py, renner_penner_api.py

### Option B: Architektur-Refactoring (GlobalCube-inspiriert)

Pre-aggregierte Daten einfuehren:
1. **Materialized Views** fuer historische Aggregate
2. **Celery-Jobs** fuer taegliche/woechentliche Snapshots
3. **Cache-Layer** fuer haeufige Abfragen

Betroffene Module:
- TEK-Dashboard (taeglich reicht)
- Jahresvergleiche (Snapshots)
- Renner/Penner (woechentlich)

### Option C: Locosoft SOAP Client

Phase 1 der Gudat-Abloesung:
```python
# locosoft_soap_client.py
from zeep import Client

class LocosoftSOAPClient:
    WSDL_URL = 'http://10.80.80.7:8086/?wsdl'
    AUTH = ('9001', 'Max2024')

    def list_appointments_by_date(...)
    def list_open_work_orders(...)
```

---

## WICHTIGE DATEIEN

```
api/budget_api.py            - Budget-Endpoints + Wizard (erweitert TAG 156)
api/budget_data.py           - SSOT Budget (TAG 155)
templates/verkauf_budget_wizard.html - Wizard UI
templates/verkauf_budget.html - Budget Dashboard

projects/budget_planungsmodul/extract_globalcube_data.py - CSV-Parser
projects/budget_planungsmodul/GREINER_HISTORISCH_2022_2025.md - Extrahierte Daten
```

---

## GLOBALCUBE ZUGRIFF

```
Q:\ = \\srvgc01\GlobalCube

Q:\Cubes\v_verkauf__*          - Verkaufs-Cubes (taeglich)
Q:\System\LOCOSOFT\Export\     - CSV-Rohdaten
Q:\GCStruct\Kontenrahmen\      - SKR51-Mapping
```

---

## API-ENDPOINTS

```
# Budget-Wizard (TAG 155-156):
GET  /api/budget/wizard/NW?standort=1   # Mit Standort-Filter
GET  /api/budget/wizard/GW
POST /api/budget/wizard/NW/berechnen
POST /api/budget/wizard/GW/berechnen
POST /api/budget/wizard/NW/speichern
POST /api/budget/wizard/GW/speichern
GET  /api/budget/wizard-plaene?jahr=2026  # Gespeicherte Plaene

# Budget-Dashboard:
GET  /api/budget/dashboard
GET  /api/budget/globalcube-ist/2024
GET  /api/budget/benchmark/<jahr>
```

---

## PORTAL URLs

- **Budget-Dashboard:** https://drive.auto-greiner.de/verkauf/budget
- **Budget-Wizard:** https://drive.auto-greiner.de/verkauf/budget/wizard

---

## PYTHON AUF WINDOWS

```cmd
"C:\Program Files\Python312\python.exe" --version
"C:\Program Files\Python312\python.exe" -m pip list
```

Mit openpyxl fuer Excel-Verarbeitung.

---

## HISTORISCHE STUECKZAHLEN (aus GlobalCube CSV)

| Jahr | NW | GW | Gesamt |
|------|-----|-----|--------|
| 2023 | 162 | 213 | 375 |
| 2024 | 563 | 764 | 1.327 |
| 2025 | 492 | 788 | 1.280 |

Hinweis: BE-Werte sind in CSV leer, werden in PowerPlay Cubes aggregiert.

---

*Erstellt: 2026-01-02*
