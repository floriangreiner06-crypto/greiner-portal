# PROMPT FÜR NÄCHSTE SESSION (TAG 98+)

## KONTEXT FÜR CLAUDE

```
Du arbeitest am GREINER PORTAL (GREINER DRIVE) - einem integrierten ERP-System für ein Autohaus.

Server: 10.80.80.20 (srvlinux01)
User: ag-admin
Pfad: /opt/greiner-portal/
Sync: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server → /mnt/greiner-portal-sync/

WICHTIG:
1. Lies IMMER zuerst die PROJECT_INSTRUCTIONS.txt und CLAUDE.md
2. Lies das letzte SESSION_WRAP_UP (aktuell: TAG97)
3. Nutze project_knowledge_search für Kontext
4. Kopiere Dateien vor Ausführung: cp /mnt/greiner-portal-sync/... /opt/greiner-portal/...
```

---

## AKTUELLER STAND (nach TAG 97)

### ✅ GUDAT API INTEGRATION ABGESCHLOSSEN

**Was funktioniert:**
- Login mit 3-Schritt-Flow (GET /kic → POST /login → GET /ack)
- Kapazitätsdaten abrufen (16 Teams)
- GraphQL für Termine/Dossiers/Orders
- Locosoft-Verknüpfung: `Gudat order.number = Locosoft orders.number`

**Dateien erstellt:**
- `/opt/greiner-portal/tools/gudat_client.py` - Python Client
- `/opt/greiner-portal/api/gudat_api.py` - Flask Blueprint (NOCH NICHT REGISTRIERT!)
- `/opt/greiner-portal/docs/GUDAT_API_INTEGRATION.md` - Technische Doku

### FIRMENSTRUKTUR

```
Betrieb 1 = Stellantis Deggendorf (Aufträge 31-39xxx)
Betrieb 2 = Hyundai Deggendorf (Aufträge 201xxx-220xxx)
Betrieb 3 = Stellantis Landau (Aufträge 16xxx-313xxx)
```

### LOCOSOFT DB ERKENNTNISSE

```
Host: 10.80.80.8
DB: loco_auswertung_db
User: loco_auswertung_benutzer

Wichtige Tabellen:
- orders (number, subsidiary, order_customer, vehicle_number)
- customers_suppliers (customer_number, first_name, family_name)
- dealer_vehicles (dealer_vehicle_number, vin) - ACHTUNG: kein license_plate!
- appointments (order_number, bring_timestamp, return_timestamp)

Spalten-Konventionen:
- first_name/family_name (NICHT name1/name2)
- subsidiary (Betriebsnummer)
- _number Suffix für IDs (customer_number, vehicle_number, etc.)
```

---

## OFFENE TODOS (PRIO-REIHENFOLGE)

### PRIO 1: Gudat Integration fertigstellen

```python
# In app.py hinzufügen:
from api.gudat_api import register_gudat_api
register_gudat_api(app)

# Credentials in credentials.json unter "external_systems.gudat":
{
  "url": "https://werkstattplanung.net",
  "tenant": "greiner/deggendorf/kic",
  "username": "florian.greiner@auto-greiner.de",
  "password": "Hyundai2025!"
}
```

### PRIO 2: Dashboard-Widget Werkstatt-Kapazität

- Aktuelle Auslastung pro Team anzeigen
- Kritische Teams highlighten (< 10 AW frei)
- Wochenübersicht

### PRIO 3: ML-Integration

- Gudat-Kapazitätsdaten als Features
- Soll-Ist-Vergleich mit Locosoft-Zeiterfassung
- Historische Auslastungsmuster

### PRIO 4: Alerting

- Kritische Auslastung → E-Mail/Notification
- Wöchentliche Reports

---

## BEFEHLE FÜR SESSION-START

```bash
# 1. Verbinden
ssh ag-admin@10.80.80.20

# 2. Projekt-Verzeichnis
cd /opt/greiner-portal

# 3. Venv aktivieren
source venv/bin/activate

# 4. Sync prüfen
ls -la /mnt/greiner-portal-sync/

# 5. Git Status
git status

# 6. Letzte Änderungen
git log --oneline -5
```

---

## WICHTIGE DATEIEN ZUM LESEN

1. `docs/SESSION_WRAP_UP_TAG97.md` - Letzte Session
2. `docs/GUDAT_API_INTEGRATION.md` - Gudat API Doku
3. `tools/gudat_client.py` - Python Client
4. `api/gudat_api.py` - Flask Blueprint

---

## BEISPIEL-PROMPT

```
Ich arbeite am Greiner Portal weiter. Letzte Session war TAG 97 (Gudat API Integration).

Aktueller Stand:
- Gudat API funktioniert (Login, Kapazität, GraphQL)
- Locosoft-Verknüpfung funktioniert (order.number = orders.number)
- Flask Blueprint erstellt aber noch nicht registriert

Heute will ich:
1. gudat_api.py in app.py registrieren
2. Dashboard-Widget für Werkstatt-Kapazität erstellen

Bitte lies zuerst docs/SESSION_WRAP_UP_TAG97.md und docs/GUDAT_API_INTEGRATION.md
```

---

**Erstellt:** 2025-12-06
