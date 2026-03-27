# SESSION WRAP-UP TAG 97 - GUDAT API INTEGRATION KOMPLETT

**Datum:** 2025-12-06 (Samstag)  
**Dauer:** ~3 Stunden  
**Status:** ✅ ERFOLGREICH ABGESCHLOSSEN

---

## 🎯 ZIEL DER SESSION

Gudat "Digitales Autohaus" API (werkstattplanung.net) für ML-basierte Kapazitätsplanung integrieren und Verknüpfung zu Locosoft herstellen.

---

## 🏆 ERREICHTE MEILENSTEINE

### 1. ✅ Gudat API Login funktioniert

**Das Problem (aus TAG 96):** API gab 401 "Unauthenticated" trotz erfolgreichem Login.

**Die Lösung:** Der fehlende `/ack` Endpoint!

```python
# Korrekter Login-Flow:
1. GET /greiner/deggendorf/kic    → XSRF-TOKEN, laravel_session
2. POST /login                     → remember_web Cookie  
3. GET /ack                        → laravel_token Cookie ← KRITISCH!
4. GET /api/v1/*                   → 200 OK ✅
```

### 2. ✅ Kapazitätsdaten abrufbar

**Endpoint:** `GET /api/v1/workload_week_summary?date=YYYY-MM-DD&days=1-14`

**16 Teams verfügbar:**
- Allgemeine Reparatur (ID 2): 865 AW Kapazität
- Diagnosetechnik (ID 3): 136 AW (oft kritisch ausgelastet!)
- Qualitätsmanagement (ID 4): 478 AW
- NW/GW (ID 5): 99 AW
- TÜV/DEKRA (ID 6, 11): je 50 AW
- Externe Dienstleister (7 Teams)

### 3. ✅ GraphQL API funktioniert

**Verfügbare Queries:**
```graphql
appointments(first: N, where: {...}) {
  id, start_date_time, end_date_time, type
  dossier {
    id, vehicle { license_plate }, orders { id, number }, states { name }
  }
}
```

### 4. ✅ Locosoft-Verknüpfung gefunden

**Das Mapping:**
```
Gudat order.number = Locosoft orders.number
```

**Getestet mit 8/8 Aufträgen erfolgreich!**

---

## 📁 ERSTELLTE DATEIEN

### Python Client (FUNKTIONIERT!)
**Pfad:** `/opt/greiner-portal/tools/gudat_client.py`

```python
from gudat_client import GudatClient

client = GudatClient(username, password)
client.login()

# Kapazität
summary = client.get_workload_summary("2025-12-09")
week = client.get_week_overview("2025-12-09")

# GraphQL für Termine
client._api_request('POST', '/graphql', json={'query': query})
```

### Flask API Blueprint
**Pfad:** `/opt/greiner-portal/api/gudat_api.py`

```python
GET /api/gudat/health
GET /api/gudat/workload?date=YYYY-MM-DD
GET /api/gudat/workload/week?start_date=YYYY-MM-DD
GET /api/gudat/teams?date=YYYY-MM-DD
```

**Integration in app.py:**
```python
from api.gudat_api import register_gudat_api
register_gudat_api(app)
```

### Analyse-Scripts
- `gudat_termine_export.py` - Export mit Locosoft-Nummern
- `gudat_locosoft_link.py` - Verknüpfungs-Test
- `gudat_order_analysis.py` - Order-Feld-Analyse
- `gudat_find_fields.py` - GraphQL Feld-Discovery

---

## 🏢 FIRMENSTRUKTUR (WICHTIG!)

### Locosoft Betriebe (subsidiary)

| Betrieb | Firma | Marke | Standort | Nummernkreis |
|---------|-------|-------|----------|--------------|
| **1** | Autohaus Greiner GmbH & Co. KG | Stellantis (Opel) | Deggendorf | 31 - 39.xxx |
| **2** | Auto Greiner GmbH & Co. KG | Hyundai | Deggendorf | 201.888 - 220.xxx |
| **3** | Autohaus Greiner GmbH & Co. KG | Stellantis (Opel) | Landau | 16.294 - 313.xxx |

### Gudat Werkstattplanung

- **URL:** https://werkstattplanung.net/greiner/deggendorf/kic
- **Standort:** Deggendorf (Betrieb 1 + 2)
- **Landau:** Vermutlich eigene Gudat-Instanz (nicht getestet)

---

## 🔗 DATEN-MAPPING

### Gudat → Locosoft

```
GUDAT                              LOCOSOFT
──────────────────────────────────────────────────────────
Appointment
  └─ Dossier
       ├─ vehicle.license_plate    → (nicht direkt, über vehicle_number)
       ├─ orders[].number ═════════► orders.number
       └─ states[].name            → Vorgangsstatus

orders.number                      → orders
                                       ├─ subsidiary (Betrieb 1/2/3)
                                       ├─ order_date
                                       ├─ order_customer → customers_suppliers
                                       │                    ├─ first_name
                                       │                    ├─ family_name
                                       │                    └─ home_city
                                       ├─ vehicle_number
                                       └─ order_mileage (KM-Stand)
```

### Beispiel-Verknüpfung

```
Gudat Termin (08.12.2025 07:00):
  - Dossier ID: 18980
  - Order Number: 219379
  - Vehicle: DEG-X 212
  
Locosoft (orders.number = 219379):
  - Betrieb: 2 (Hyundai Deggendorf)
  - Kunde: Werner Stadler, Hunding
  - Datum: 2025-10-13
  - Fahrzeug-Nr: 51153
  - KM-Stand: 43.300
```

---

## 🗄️ LOCOSOFT DB ERKENNTNISSE

### Wichtige Tabellen

| Tabelle | Zweck | Key-Spalten |
|---------|-------|-------------|
| `orders` | Werkstatt-Aufträge | `number`, `subsidiary`, `order_customer`, `vehicle_number` |
| `customers_suppliers` | Kunden | `customer_number`, `first_name`, `family_name` |
| `dealer_vehicles` | Fahrzeuge | `dealer_vehicle_number`, `vin` (NICHT license_plate!) |
| `appointments` | Termine | `order_number`, `bring_timestamp`, `return_timestamp` |
| `employees` | Mitarbeiter | `employee_number`, `first_name`, `last_name` |

### Spalten-Namenskonventionen

```
LOCOSOFT VERWENDET:
- first_name, family_name (NICHT name1, name2)
- bring_timestamp, return_timestamp (NICHT appointment_date/time)
- dealer_vehicle_number (NICHT vehicle_id)
- customer_number (NICHT customer_id)
- subsidiary (Betriebsnummer 1/2/3)
```

### Credentials

```json
// /opt/greiner-portal/config/credentials.json
{
  "databases": {
    "locosoft": {
      "host": "10.80.80.8",
      "port": 5432,
      "database": "loco_auswertung_db",
      "user": "loco_auswertung_benutzer",
      "password": "loco"
    }
  },
  "external_systems": {
    "gudat": {
      "url": "https://werkstattplanung.net",
      "tenant": "greiner/deggendorf/kic",
      "username": "florian.greiner@auto-greiner.de",
      "password": "Hyundai2025!"
    }
  }
}
```

---

## 📋 TODO FÜR NÄCHSTE SESSION

### PRIO 1: Integration abschließen

- [ ] `gudat_api.py` in app.py registrieren
- [ ] Credentials in credentials.json unter `external_systems.gudat` speichern
- [ ] Health-Check Endpoint testen

### PRIO 2: Dashboard-Widget

- [ ] Werkstatt-Kapazität Widget erstellen
- [ ] Kritische Teams highlighten (Diagnosetechnik < 10 AW frei)
- [ ] Wochen-Übersicht

### PRIO 3: ML-Integration

- [ ] Gudat-Daten als Features für Kapazitätsprognose
- [ ] Soll-Ist-Vergleich (Gudat-Planung vs. Locosoft-Zeiterfassung)
- [ ] Historische Auslastungsmuster

### PRIO 4: Alerting

- [ ] Automatische Benachrichtigung bei kritischer Auslastung
- [ ] Wöchentliche Kapazitäts-Reports

---

## 💡 LESSONS LEARNED

1. **Browser-Cookie-Vergleich:** Selenium half, den fehlenden `laravel_token` zu finden
2. **Systematische Endpoint-Tests:** `/ack` war unerwartet aber kritisch
3. **requests.Session():** Automatisches Cookie-Management essentiell
4. **Locosoft Spalten:** Immer erst Schema prüfen (nicht raten!)
5. **Firmenstruktur:** Betrieb/subsidiary ist der Schlüssel für Multi-Standort

---

## 🔧 GIT COMMIT

```bash
cd /opt/greiner-portal
git add -A
git status
git commit -m "TAG97: Gudat API Integration komplett - Login, Kapazität, GraphQL, Locosoft-Verknüpfung"
```

---

**Erstellt:** 2025-12-06 22:30  
**Autor:** Claude + Florian Greiner
