# TODO FOR CLAUDE - SESSION START TAG 160

**Letzte Session:** TAG 159 (2026-01-02)
**Fokus:** Data-Module Pattern für Sales/Fahrzeuge

---

## KONTEXT

TAG 159 hat zwei neue Data-Module nach dem SSOT-Pattern erstellt:

### Neu erstellt:
- `api/fahrzeug_data.py` - Fahrzeugbestand aus Locosoft
- `api/verkauf_data.py` - Verkaufs/Sales-Daten
- `api/verkauf_api.py` refaktoriert (Version 3.0)

### Pattern-Architektur:
```
api/*_data.py     -> Datenlogik (SSOT)
api/*_api.py      -> HTTP-Handling (Blueprint)
templates/*.html  -> Frontend
```

---

## AUFGABEN TAG 160

### Priorität 1: fahrzeug_api.py erstellen

Die Fahrzeug-Routes brauchen noch einen Blueprint:

```python
# api/fahrzeug_api.py
from flask import Blueprint, jsonify, request
from api.fahrzeug_data import FahrzeugData

fahrzeug_api = Blueprint('fahrzeug_api', __name__, url_prefix='/api/fahrzeug')

@fahrzeug_api.route('/gw', methods=['GET'])
def get_gw_bestand():
    standort = request.args.get('standort', type=int)
    kategorie = request.args.get('kategorie')
    return jsonify(FahrzeugData.get_gw_bestand(standort, kategorie))

# etc.
```

Und in app.py registrieren:
```python
from api.fahrzeug_api import fahrzeug_api
app.register_blueprint(fahrzeug_api)
```

### Priorität 2: GW-Dashboard

Template für GW-Bestand mit Standzeit-Ampel:

```
templates/verkauf/gw_dashboard.html
- Standzeit-Kategorien als Cards
- Fahrzeugliste mit Filter
- Ampel-Farben (grün/gelb/rot/schwarz)
- Aktionen: "Zur Börse", "Händler-VK"
```

Route in verkauf_routes.py hinzufügen.

### Priorität 3: Gap-Tracker (aus TAG 158)

API-Endpoint für monatlichen Fortschritt zum 1%-Ziel:

```python
# api/controlling_api.py
@controlling_api.route('/gap-tracker', methods=['GET'])
def get_gap_tracker():
    """
    IST vs. SOLL Vergleich für 1% Renditeziel
    """
    gj = request.args.get('gj', '2025/26')
    # ...
```

---

## WICHTIGE DATEIEN

```
api/fahrzeug_data.py    - SSOT Fahrzeugbestand (fertig)
api/verkauf_data.py     - SSOT Verkauf (fertig)
api/verkauf_api.py      - Verkauf-Endpoints (refaktoriert)
api/fahrzeug_api.py     - TODO: erstellen
app.py                  - Blueprint-Registration
```

---

## DATENBANK-REFERENZ

### Locosoft (PostgreSQL, read-only)
```sql
-- GW-Bestand
SELECT * FROM dealer_vehicles dv
JOIN vehicles v ON dv.vehicle_number = v.internal_number
WHERE dv.out_invoice_date IS NULL
  AND dv.dealer_vehicle_type = 'G'

-- Standzeit berechnen
CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) as standzeit_tage
```

### DRIVE Portal (PostgreSQL)
```sql
-- Sales-Daten (Mirror von Locosoft)
SELECT * FROM sales WHERE out_invoice_date IS NOT NULL
```

---

## LINKS

- **GW-Analyse (TAG 158):** `docs/TAG158_GAP_ANALYSE_MASSNAHMENPLAN.md`
- **Session Wrap-Up:** `docs/sessions/SESSION_WRAP_UP_TAG159.md`

---

*Vorbereitet für TAG 160*
