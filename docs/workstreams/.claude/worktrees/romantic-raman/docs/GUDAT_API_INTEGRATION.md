# GUDAT API INTEGRATION - TECHNISCHE DOKUMENTATION

**Stand:** 2025-12-06  
**Status:** ✅ Produktionsreif

---

## 🔐 AUTHENTIFIZIERUNG

### Login-Flow (KRITISCH!)

```python
import requests

session = requests.Session()
BASE_URL = "https://werkstattplanung.net/greiner/deggendorf/kic"

# SCHRITT 1: XSRF-Token holen
response = session.get(BASE_URL)
xsrf_token = session.cookies.get('XSRF-TOKEN')

# SCHRITT 2: Login
headers = {
    'X-XSRF-TOKEN': unquote(xsrf_token),
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': BASE_URL
}

login_response = session.post(
    f"{BASE_URL}/login",
    json={'email': USERNAME, 'password': PASSWORD},
    headers=headers
)

# SCHRITT 3: /ack aufrufen (KRITISCH für laravel_token!)
session.get(f"{BASE_URL}/ack", headers=headers)

# Jetzt sind alle 4 Cookies gesetzt:
# - XSRF-TOKEN
# - laravel_session
# - remember_web_*
# - laravel_token  ← Ohne diesen: 401!
```

### Credentials

```
URL:      https://werkstattplanung.net/greiner/deggendorf/kic
Username: florian.greiner@auto-greiner.de
Password: Hyundai2025!
```

---

## 📡 REST API ENDPOINTS

### Workload/Kapazität

```
GET /api/v1/workload_week_summary?date=YYYY-MM-DD&days=1-14

Response: Array von 16 Teams mit:
{
  "id": 2,
  "category_name": "Mechanik",
  "name": "Allgemeine Reparatur",
  "data": {
    "2025-12-09": {
      "base_workload": 865,      // Kapazität in AW
      "planned_workload": 289,   // Geplant
      "absence_workload": 494,   // Abwesend
      "plannable_workload": 334, // Planbar
      "free_workload": 45,       // Noch frei
      "team_productivity_factor": 0.9,
      "members": [...]           // Mitarbeiter (Namen = "Unknown")
    }
  }
}
```

### Konfiguration

```
GET /api/v1/config

Response: Mandanten-Konfiguration
```

---

## 🔷 GRAPHQL API

### Endpoint

```
POST /graphql
Content-Type: application/json

{"query": "..."}
```

### Verfügbare Queries

#### Termine abrufen

```graphql
query GetAppointments {
  appointments(
    first: 20,
    where: {
      AND: [
        {column: START_DATE_TIME, operator: GTE, value: "2025-12-08"},
        {column: START_DATE_TIME, operator: LT, value: "2025-12-09"}
      ]
    }
  ) {
    data {
      id
      start_date_time
      end_date_time
      type                    # service, customer_bring, finish_pickup, other
      dossier {
        id
        vehicle {
          id
          license_plate
        }
        orders {
          id
          number              # ← LOCOSOFT AUFTRAGSNUMMER!
        }
        states {
          id
          name                # Vorgangsstatus
        }
      }
    }
  }
}
```

#### Dossiers abrufen

```graphql
query GetDossiers {
  dossiers(first: 10, orderBy: [{column: UPDATED_AT, order: DESC}]) {
    data {
      id
      created_at
      updated_at
      vehicle { id, license_plate }
      orders { id, number }
      appointments { id, start_date_time }
      states { id, name }
      tags { id }
    }
  }
}
```

#### Einzelnes Dossier

```graphql
query GetDossier {
  dossier(id: 18980) {
    id
    orders { id, number }
    states { id, name }
  }
}
```

#### Orders

```graphql
query GetOrders {
  orders(first: 10, orderBy: [{column: ID, order: DESC}]) {
    data {
      id
      number        # ← Das ist die Locosoft-Auftragsnummer!
      created_at
    }
  }
}
```

---

## 🔗 LOCOSOFT VERKNÜPFUNG

### Das Mapping

```
Gudat order.number = Locosoft orders.number
```

### SQL-Query für Verknüpfung

```sql
-- Gudat-Termin mit Locosoft-Daten verknüpfen
SELECT 
    o.number AS auftrag_nr,
    o.subsidiary AS betrieb,
    o.order_date,
    o.order_mileage AS km_stand,
    c.first_name || ' ' || c.family_name AS kunde,
    c.home_city AS ort
FROM orders o
LEFT JOIN customers_suppliers c ON o.order_customer = c.customer_number
WHERE o.number = 219379;  -- ← Gudat order.number
```

### Betriebszuordnung

```python
BETRIEBE = {
    1: {'name': 'Stellantis Deggendorf', 'marke': 'Opel', 'nummern': '31-39xxx'},
    2: {'name': 'Hyundai Deggendorf', 'marke': 'Hyundai', 'nummern': '201xxx-220xxx'},
    3: {'name': 'Stellantis Landau', 'marke': 'Opel', 'nummern': '16xxx-313xxx'}
}
```

---

## 📊 TEAM-IDs

| ID | Kategorie | Name | Typ |
|----|-----------|------|-----|
| 2 | Mechanik | Allgemeine Reparatur | Intern |
| 3 | Mechanik | Diagnosetechnik | Intern |
| 4 | Mechanik | Qualitätsmanagement | Intern |
| 5 | Mechanik | NW/GW | Intern |
| 6 | Mechanik | TÜV/AU (Dekra) | Intern |
| 11 | Mechanik | TÜV/AU | Intern |
| 16 | Mechanik | Hauptuntersuchung | Intern |
| 7-10, 12-15 | Externe | Aufbereitung, Smart Repair, etc. | Extern |

---

## ⚠️ WICHTIGE HINWEISE

1. **Session-basiert:** Immer `requests.Session()` verwenden
2. **XSRF-Token:** Muss URL-decoded werden bei Verwendung im Header
3. **Referer-Header:** Pflicht bei allen Requests
4. **Rate-Limiting:** Unbekannt, vorsichtig sein
5. **Mitarbeiter-Namen:** Werden als "Unknown" zurückgegeben (DSGVO?)

---

## 🧪 TEST-BEFEHLE

```bash
# Client testen
cd /opt/greiner-portal
source venv/bin/activate
python3 tools/gudat_client.py

# Termine exportieren
python3 tools/gudat_termine_export.py

# Locosoft-Verknüpfung testen
python3 tools/gudat_locosoft_link.py
```

---

**Autor:** Claude + Florian Greiner  
**Erstellt:** 2025-12-06
