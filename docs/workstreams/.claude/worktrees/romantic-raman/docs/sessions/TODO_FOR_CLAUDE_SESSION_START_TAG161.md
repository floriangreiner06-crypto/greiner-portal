# TODO FOR CLAUDE - SESSION START TAG 161

**Letzte Session:** TAG 159/160 (2026-01-02)
**Fokus:** SSOT Data-Module + GW-Dashboard

---

## KONTEXT

TAG 159/160 hat das SSOT-Pattern auf Verkauf/Fahrzeuge erweitert:

### Neue Module:
- `api/fahrzeug_data.py` (659 LOC) - Fahrzeugbestand aus Locosoft
- `api/verkauf_data.py` (875 LOC) - Verkaufs/Sales-Daten
- `api/fahrzeug_api.py` (~180 LOC) - REST-API Blueprint
- `templates/verkauf_gw_dashboard.html` - GW-Standzeit Dashboard

### GW-Dashboard Features:
- Standzeit-Ampel (frisch/ok/risiko/penner/leiche)
- Statistik-Karten (Bestand, Lagerwert, Problemfaelle)
- Problemfaelle-Tabelle (Top 10 >90 Tage)
- Fahrzeugliste mit Filtern
- URL: `/verkauf/gw-bestand` oder `/verkauf/gw-dashboard`

---

## AUFGABEN TAG 161

### Prioritaet 1: CSV-Export fuer GW-Dashboard

Das Dashboard hat einen Export-Button, aber die Funktion ist noch TODO:

```javascript
// templates/verkauf_gw_dashboard.html Zeile 374-377
function exportCSV() {
    // TODO: CSV Export implementieren
    alert('CSV Export wird vorbereitet...');
}
```

**Optionen:**
1. Frontend-only (JavaScript generiert CSV aus currentData)
2. Backend-Endpoint `/api/fahrzeug/gw/export`

### Prioritaet 2: Gap-Tracker (aus TAG 158)

API-Endpoint fuer monatlichen Fortschritt zum 1%-Ziel:

```
/api/controlling/gap-tracker?gj=2025/26

Response:
{
  "monate": [
    {
      "monat": "Sep 2025",
      "ist_ergebnis": -45000,
      "soll_ergebnis": 15000,
      "gap": -60000,
      "kumuliert_ist": -45000,
      "kumuliert_soll": 15000
    },
    ...
  ],
  "jahres_gap": -120000,
  "trend": "negativ"
}
```

Datenquellen:
- IST: TEK aus controlling_data.py
- SOLL: Budget-Plan aus budget_plan Tabelle

### Prioritaet 3: Server-Test GW-Dashboard

Das Dashboard muss auf dem Server getestet werden:

```bash
# API testen
curl -s http://localhost:5000/api/fahrzeug/health
curl -s http://localhost:5000/api/fahrzeug/gw/dashboard | python3 -m json.tool | head -50

# Browser-Test
# https://drive.auto-greiner.de/verkauf/gw-bestand
```

---

## ARCHITEKTUR-REFERENZ

### Data-Module (SSOT Pattern)
```
api/werkstatt_data.py    - Werkstatt (3,413 LOC)
api/fahrzeug_data.py     - Bestand (659 LOC)
api/verkauf_data.py      - Sales (875 LOC)
api/controlling_data.py  - TEK, BWA
api/unternehmensplan_data.py - GlobalCube BWA
```

### Standzeit-Kategorien
```python
KATEGORIEN = {
    'frisch': (0, 60),      # Grueen
    'ok': (61, 90),         # Blau
    'risiko': (91, 120),    # Gelb
    'penner': (121, 180),   # Rot
    'leiche': (181, 9999)   # Schwarz
}
```

### Locosoft Fahrzeug-Join
```sql
SELECT dv.*, v.*
FROM dealer_vehicles dv
JOIN vehicles v ON dv.vehicle_number = v.internal_number
WHERE dv.out_invoice_date IS NULL
  AND dv.dealer_vehicle_type = 'G'
```

---

## WICHTIGE DATEIEN

```
api/fahrzeug_data.py     - SSOT Fahrzeugbestand
api/fahrzeug_api.py      - REST-Endpoints
api/controlling_data.py  - TEK-Daten (fuer Gap-Tracker)
templates/verkauf_gw_dashboard.html - Dashboard
docs/TAG158_GAP_ANALYSE_MASSNAHMENPLAN.md - Gap-Analyse
```

---

## SERVER-BEFEHLE

```bash
# Sync nach Aenderungen
rsync -av /mnt/greiner-portal-sync/api/ /opt/greiner-portal/api/
rsync -av /mnt/greiner-portal-sync/templates/ /opt/greiner-portal/templates/

# Neustart (nur bei Python-Aenderungen)
sudo systemctl restart greiner-portal

# Logs
journalctl -u greiner-portal -f --since "5 minutes ago"
```

---

*Vorbereitet fuer TAG 161*
