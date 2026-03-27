# GUDAT API Integration - ERFOLGREICH!

## Stand: TAG 97 (2025-12-06)

### ✅ STATUS: FUNKTIONIERT!

Die werkstattplanung.net API (Gudat "Digitales Autohaus") ist jetzt vollständig integriert.

---

## Der entscheidende Durchbruch

**Das Problem war:** Nach dem Login fehlte der **`laravel_token`** Cookie!

**Die Lösung:** Der `/ack` Endpoint muss nach dem Login aufgerufen werden, um den `laravel_token` Cookie zu erhalten.

### Korrekter Login-Flow:

```
1. GET /greiner/deggendorf/kic     → XSRF-TOKEN, laravel_session
2. POST /greiner/deggendorf/kic/login  → remember_web Cookie
3. GET /greiner/deggendorf/kic/ack     → laravel_token Cookie ← KRITISCH!
4. GET /api/v1/*                       → API funktioniert!
```

---

## Dateien

### Client
- **`/opt/greiner-portal/tools/gudat_client.py`** - Python Client (v2.1)
  - `GudatClient` Klasse
  - `login()` - Korrekter Login-Flow inkl. /ack
  - `get_workload_summary(date)` - Tages-Kapazität
  - `get_week_overview(start_date)` - Wochen-Übersicht
  - `get_workload_raw(date, days)` - Rohdaten

### API
- **`/opt/greiner-portal/api/gudat_api.py`** - Flask Blueprint
  - `GET /api/gudat/health` - Health-Check
  - `GET /api/gudat/workload?date=YYYY-MM-DD` - Tages-Kapazität
  - `GET /api/gudat/workload/week?start_date=YYYY-MM-DD` - Woche
  - `GET /api/gudat/workload/raw?date=YYYY-MM-DD&days=7` - Rohdaten
  - `GET /api/gudat/teams?date=YYYY-MM-DD` - Team-Details

### Config
- **`/opt/greiner-portal/config/credentials.json`**
  ```json
  {
    "external_systems": {
      "gudat": {
        "username": "florian.greiner@auto-greiner.de",
        "password": "Hyundai2025!",
        "base_url": "https://werkstattplanung.net/greiner/deggendorf/kic"
      }
    }
  }
  ```

---

## API Endpoints (Gudat)

### Workload API
```
GET /api/v1/workload_week_summary?date=YYYY-MM-DD&days=1-14
```

### Response-Struktur
```json
[
  {
    "id": 2,
    "category_id": 2,
    "category_name": "Mechanik",
    "name": "Allgemeine Reparatur",
    "data": {
      "2025-12-09": {
        "base_workload": 865,
        "planned_workload": 289,
        "absence_workload": 494,
        "plannable_workload": 334,
        "free_workload": 82,
        "team_productivity_factor": 0.9,
        "members": [...]
      }
    }
  }
]
```

---

## Nutzung

### Python Client direkt
```python
from gudat_client import GudatClient

client = GudatClient("user@example.com", "password")
if client.login():
    summary = client.get_workload_summary('2025-12-09')
    print(f"Kapazität: {summary['total_capacity']} AW")
    print(f"Geplant: {summary['planned']} AW")
    print(f"Frei: {summary['free']} AW")
```

### Flask API (nach Integration in app.py)
```bash
curl http://localhost:5000/api/gudat/workload?date=2025-12-09
curl http://localhost:5000/api/gudat/workload/week
```

---

## Integration in app.py

```python
# In app.py hinzufügen:
from api.gudat_api import register_gudat_api

# Nach Flask-App Erstellung:
register_gudat_api(app)
```

---

## Kapazitäts-Daten (Beispiel)

### Montag 09.12.2025
- **Kapazität:** 2.242 AW
- **Geplant:** 550 AW (24.5%)
- **Abwesend:** 872 AW
- **Frei:** 783 AW
- **Status:** 🟢 OK

### 16 Teams
- Allgemeine Reparatur (Mechanik)
- Diagnosetechnik
- Qualitätsmanagement
- Smart Repair (Extern)
- Aufbereitung (Extern)
- Windschutzscheiben (Extern)
- u.v.m.

---

## Nächste Schritte

1. ✅ ~~API-Client implementieren~~ DONE!
2. ✅ ~~Flask API erstellen~~ DONE!
3. ⏳ In app.py integrieren
4. ⏳ Dashboard-Widget für Kapazität erstellen
5. ⏳ ML-Modell mit Gudat-Daten erweitern
6. ⏳ Automatische Alerts bei Überlastung

---

## Lessons Learned

1. **Cookie-Analyse ist kritisch** - Alle Cookies genau prüfen
2. **Selenium hilft beim Debugging** - Browser zeigt was wirklich passiert
3. **/ack Endpoint** - Unerwartete Endpoints können kritische Cookies setzen
4. **requests.Session()** - Automatisches Cookie-Management ist essentiell
