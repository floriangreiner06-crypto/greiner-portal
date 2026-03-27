# TODO FOR CLAUDE - SESSION START TAG 156

**Letzte Session:** TAG 155 (2026-01-02)
**Ziel:** Budget-Wizard finalisieren oder neues Modul starten

---

## KONTEXT

TAG 155 hat das Budget-Planungsmodul erstellt:
- 5-Fragen-Wizard mit Slider-Eingaben
- IST 2024 Daten aus GlobalCube Excel extrahiert
- API-Endpoints fuer Wizard implementiert
- Frontend-Template erstellt

**Aktueller Stand:**
- `/verkauf/budget/wizard` - Neuer 5-Fragen-Wizard
- `/verkauf/budget` - Bestehendes Dashboard
- budget_data.py und budget_api.py erweitert

---

## AUFGABEN TAG 156

### Option A: Budget-Wizard finalisieren

1. **Speichern implementieren**
   - POST `/api/budget/wizard/<typ>/speichern`
   - In budget_plan Tabelle schreiben
   - User-Tracking (erstellt_von)

2. **Standort-Filter ergaenzen**
   - Dropdown im Wizard fuer Standort-Auswahl
   - Standort-spezifische IST-Daten laden
   - Landau-Warnung anzeigen (negatives BE)

3. **Dashboard-Verlinkung**
   - Button im Budget-Dashboard zum Wizard
   - Wizard-Ergebnisse im Dashboard anzeigen

### Option B: teile_data.py erweitern

Naechster SSOT-Modul fuer Teilelager:
```python
class TeileData:
    @staticmethod
    def get_lagerbestand(...)
    @staticmethod
    def get_umschlaghaeufigkeit(...)
    @staticmethod
    def get_bestellvorschlaege(...)
```

**Consumer:** parts_api.py, renner_penner_api.py

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
api/budget_data.py           - SSOT Budget (neu TAG 155)
api/budget_api.py            - Budget-Endpoints (erweitert TAG 155)
templates/verkauf_budget_wizard.html - Wizard UI (neu TAG 155)
routes/verkauf_routes.py     - /verkauf/budget/wizard Route

projects/budget_planungsmodul/GREINER_BENCHMARK_2024.md - IST-Daten
```

---

## GLOBALCUBE IST 2024 ZUSAMMENFASSUNG

| Bereich | Stueck | Bruttoertrag | BE/Fzg |
|---------|--------|--------------|--------|
| NW Gesamt | 535 | 1.69 Mio | 3.165 |
| GW Gesamt | 615 | 1.10 Mio | 1.795 |
| **Gesamt** | **1.150** | **2.80 Mio** | **2.432** |

**Standort-Highlights:**
- DEG Hyundai: 742k BE (Beste Performance)
- Landau NW: -56k BE (KRITISCH!)

---

## API-ENDPOINTS (TAG 155)

```
GET  /api/budget/globalcube-ist/2024         - IST-Daten
GET  /api/budget/wizard/NW                   - Wizard fuer NW
GET  /api/budget/wizard/GW                   - Wizard fuer GW
POST /api/budget/wizard/NW/berechnen         - NW-Plan berechnen
POST /api/budget/wizard/GW/berechnen         - GW-Plan berechnen
```

---

## PORTAL URLs

Korrekte Domains:
- **https://portal.auto-greiner.de**
- **https://drive.auto-greiner.de**

Budget-Wizard:
- **https://drive.auto-greiner.de/verkauf/budget/wizard**

---

## PYTHON AUF WINDOWS

Python 3.12 ist installiert:
```cmd
"C:\Program Files\Python312\python.exe" --version
"C:\Program Files\Python312\python.exe" -m pip list
```

Mit openpyxl fuer Excel-Verarbeitung.

---

*Erstellt: 2026-01-02*
