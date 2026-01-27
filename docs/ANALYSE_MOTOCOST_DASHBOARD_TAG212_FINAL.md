# Analyse: Motocost Dashboard - FINALE ERKENNTNISSE

**TAG:** 212  
**Datum:** 2026-01-26  
**Status:** ✅ **ANALYSE ABGESCHLOSSEN**

---

## 🎯 ZUSAMMENFASSUNG

Das **motocost-Dashboard** ist ein **Grafana-Dashboard**, das interessante **auto1.com Angebote** anzeigt. Die Daten kommen aus einer **MongoDB-Datenbank** und werden über Grafana-Queries abgerufen.

**Wichtigste Erkenntnisse:**
- ✅ **28 Felder** pro Fahrzeug verfügbar
- ✅ **MongoDB-Datenquelle** (UID: `de3b0tgjwgm4gb`)
- ✅ **Grafana API** für Datenabfrage (`/api/ds/query`)
- ✅ **Dashboard UID:** `aehahbds97bpcb` (Home), `eemy79vsj9jwgc` (Auto Bewerten)

---

## 📊 DATENSTRUKTUR

### Fahrzeugdaten (28 Felder)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `firstSeen` | time | Erstes Sehen des Fahrzeugs |
| `lastSeen` | time | Letztes Sehen des Fahrzeugs |
| `p90` | number | 90. Perzentil (Preis) |
| `p10` | number | 10. Perzentil (Preis) |
| `Median` | number | Median-Preis |
| `EK Auto1` | number | Einkaufspreis bei Auto1 |
| `EK_inkl_Kosten` | number | EK inkl. aller Kosten |
| `Transport` | number | Transportkosten |
| `Nachlass` | number | Nachlass |
| `% Nachlass` | number | Nachlass in Prozent |
| `Ertrag` | number | Erwarteter Ertrag |
| `Modell` | string | Fahrzeugmodell |
| `Marke` | string | Fahrzeugmarke |
| `EZ` | time | Erstzulassung |
| `km` | number | Kilometerstand |
| `Kraftstoff` | string | Kraftstoffart |
| `Getriebe` | string | Getriebeart |
| `Sitze` | number | Anzahl Sitze |
| `Unfallschaden` | boolean | Unfallschaden vorhanden? |
| `Steuer` | boolean | Steuer bezahlt? |
| `Auffälligkeiten` | boolean | Auffälligkeiten vorhanden? |
| `Watchlist` | boolean | Auf Watchlist? |
| `Service` | string | Service-Status |
| `Auktion` | string | Auktions-Status |
| `Bild` | string | Bild-URL |
| `Link` | string | Link zum Fahrzeug |
| `Anzahl Vergleichspreise` | number | Anzahl Vergleichspreise |
| `Nummer` | string | Fahrzeugnummer/Stock-Number |

---

## 🔧 TECHNISCHE DETAILS

### Grafana-API-Endpoints

**Datenquelle:**
- **Type:** `meln5674-mongodb-community`
- **UID:** `de3b0tgjwgm4gb`
- **Query-Endpoint:** `/api/ds/query?ds_type=meln5674-mongodb-community`

**Dashboard-Endpoints:**
- `/api/dashboards/home` - Home-Dashboard
- `/api/dashboards/uid/aehahbds97bpcb` - Home-Dashboard (UID)
- `/api/dashboards/uid/eemy79vsj9jwgc` - "Auto Bewerten" Dashboard
- `/api/search` - Dashboard-Suche

**Weitere Endpoints:**
- `/api/annotations` - Annotations
- `/api/folders/cehrnouguadc0c` - Ordner-Info
- `/api/plugins/*` - Plugin-Einstellungen

### Query-Struktur

**Request:**
```json
{
  "queries": [
    {
      "refId": "A",
      "datasource": {
        "uid": "de3b0tgjwgm4gb"
      },
      "expr": "...",  // MongoDB-Query (wird nicht in HAR angezeigt)
      "rawSql": "..." // Alternative SQL-Query
    }
  ]
}
```

**Response:**
```json
{
  "results": {
    "A": {
      "frames": [
        {
          "schema": {
            "fields": [
              {
                "name": "firstSeen",
                "type": "time"
              },
              // ... weitere Felder
            ]
          },
          "data": {
            "values": [
              [/* Timestamps */],
              [/* Werte Feld 1 */],
              [/* Werte Feld 2 */],
              // ...
            ]
          }
        }
      ]
    }
  }
}
```

---

## 🔐 AUTHENTIFIZIERUNG

### Status: ⚠️ **Session-basiert**

**Erkenntnisse:**
- ❌ Keine Cookies in HAR-Datei gefunden
- ❌ Keine Authorization-Header gefunden
- ✅ **Session-basierte Authentifizierung** (Browser-Session)

**Problem:**
- Grafana verwendet Browser-Sessions für Authentifizierung
- Session-Cookies werden im Browser gespeichert
- Nicht direkt über API nutzbar ohne aktive Session

**Lösungsansätze:**

1. **Browser-Automation (Selenium/Playwright)** ⭐⭐⭐
   - Browser öffnen
   - Login durchführen
   - Session-Cookies extrahieren
   - API-Requests mit Cookies durchführen

2. **API-Keys (falls verfügbar)** ⭐⭐
   - Grafana Service-Account erstellen
   - API-Key generieren
   - Direkter API-Zugriff ohne Browser

3. **Manueller Export** ⭐
   - Daten manuell exportieren
   - CSV/JSON-Upload in DRIVE

---

## 💡 INTEGRATIONS-OPTIONEN

### Option 1: Grafana-API-Client (EMPFOHLEN) ⭐⭐⭐

**Voraussetzungen:**
- ✅ API-Zugriff (Session-Cookies oder API-Keys)
- ✅ MongoDB-Datenquelle-UID bekannt
- ✅ Query-Struktur verstanden

**Vorgehen:**
1. **Authentifizierung:**
   - Browser-Automation für Login
   - Session-Cookies extrahieren
   - Oder: API-Keys verwenden

2. **Datenabfrage:**
   ```python
   POST /api/ds/query?ds_type=meln5674-mongodb-community
   {
     "queries": [{
       "refId": "A",
       "datasource": {"uid": "de3b0tgjwgm4gb"},
       "expr": "..."  # MongoDB-Query
     }]
   }
   ```

3. **Datenverarbeitung:**
   - Response parsen (Grafana Frame-Format)
   - In DRIVE-Datenbank importieren
   - Automatische DB-Berechnung

**Vorteile:**
- ✅ Automatisiert
- ✅ Echtzeit-Daten
- ✅ Direkter API-Zugriff

**Nachteile:**
- ⚠️ Authentifizierung komplex (Session-basiert)
- ⚠️ MongoDB-Query-Struktur muss verstanden werden

---

### Option 2: Browser-Automation (Selenium) ⭐⭐

**Vorgehen:**
1. Selenium/Playwright starten
2. Login durchführen
3. Dashboard-Seite laden
4. Daten aus HTML/JavaScript extrahieren
5. In DRIVE importieren

**Vorteile:**
- ✅ Funktioniert auch ohne direkte API
- ✅ Kann JavaScript-basierte Dashboards handhaben

**Nachteile:**
- ❌ Komplexer (Browser-Overhead)
- ❌ Langsamer
- ❌ Wartungsaufwand

---

### Option 3: Manueller Export + Import ⭐

**Vorgehen:**
1. Rolf/Anton exportieren Daten (CSV/Excel)
2. Upload in DRIVE
3. Automatische Verarbeitung

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ Keine API-Abhängigkeit

**Nachteile:**
- ❌ Manueller Schritt nötig
- ❌ Nicht automatisiert

---

## 🎯 EMPFOHLENE UMSETZUNG

### Phase 1: Grafana-Client (1-2 Wochen)

**Schritte:**
1. **Browser-Automation für Login:**
   ```python
   # Selenium/Playwright
   browser = launch_browser()
   page = browser.new_page()
   page.goto('https://dashboard.motocost.com/login')
   page.fill('input[name="user"]', email)
   page.fill('input[name="password"]', password)
   page.click('button[type="submit"]')
   cookies = page.context.cookies()
   ```

2. **Grafana-API-Client:**
   ```python
   class MotocostClient:
       def __init__(self, cookies):
           self.session = requests.Session()
           for cookie in cookies:
               self.session.cookies.set(cookie['name'], cookie['value'])
       
       def query_vehicles(self):
           response = self.session.post(
               'https://dashboard.motocost.com/api/ds/query',
               params={'ds_type': 'meln5674-mongodb-community'},
               json={
                   'queries': [{
                       'refId': 'A',
                       'datasource': {'uid': 'de3b0tgjwgm4gb'},
                       # MongoDB-Query hier
                   }]
               }
           )
           return self._parse_grafana_response(response.json())
   ```

3. **Datenbank-Schema:**
   ```sql
   CREATE TABLE auto1_angebote (
       id SERIAL PRIMARY KEY,
       stock_number VARCHAR(50) UNIQUE,
       marke VARCHAR(50),
       modell VARCHAR(200),
       ez DATE,
       km_stand INTEGER,
       kraftstoff VARCHAR(20),
       getriebe VARCHAR(20),
       sitze INTEGER,
       ek_auto1 DECIMAL(10,2),
       ek_inkl_kosten DECIMAL(10,2),
       transport DECIMAL(10,2),
       nachlass DECIMAL(10,2),
       nachlass_prozent DECIMAL(5,2),
       ertrag DECIMAL(10,2),
       p90 DECIMAL(10,2),
       p10 DECIMAL(10,2),
       median DECIMAL(10,2),
       unfallschaden BOOLEAN,
       steuer BOOLEAN,
       auffaelligkeiten BOOLEAN,
       watchlist BOOLEAN,
       service VARCHAR(50),
       auktion VARCHAR(50),
       bild_url TEXT,
       link TEXT,
       anzahl_vergleichspreise INTEGER,
       first_seen TIMESTAMP,
       last_seen TIMESTAMP,
       interessant BOOLEAN DEFAULT false,
       status VARCHAR(20), -- 'neu', 'interesse', 'angebot', 'gekauft'
       zukaeufer VARCHAR(50), -- 'Rolf', 'Anton'
       notizen TEXT,
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

---

### Phase 2: DRIVE-Integration (1 Woche)

1. **API-Modul:**
   - `lib/motocost_client.py` - Grafana-Client
   - `api/zukauf_api.py` - Datenlogik
   - `routes/zukauf_routes.py` - Flask-Routes

2. **Frontend:**
   - `templates/zukauf/auto1_angebote.html` - Dashboard
   - Filter (Marke, Preis, DB, Standort)
   - Status-Tracking
   - Notizen

3. **Automatisierung:**
   - Celery-Task für regelmäßigen Import
   - Benachrichtigungen bei interessanten Angeboten

---

## 📝 NÄCHSTE SCHRITTE

### SOFORT:

1. **✅ MongoDB-Query-Struktur verstehen:**
   - Wie werden die Queries formuliert?
   - Welche Filter sind verfügbar?
   - Kann man die Query aus dem Dashboard extrahieren?

2. **✅ Authentifizierung klären:**
   - Gibt es API-Keys?
   - Oder Browser-Automation nötig?
   - Session-Cookies extrahieren

3. **✅ Test-Integration:**
   - Grafana-Client implementieren
   - Test-Query durchführen
   - Datenstruktur validieren

---

## 🔧 TECHNISCHE HINWEISE

### Grafana Frame-Format

Grafana verwendet ein spezielles Frame-Format für Daten:
- **Schema:** Feld-Definitionen (Name, Typ)
- **Data:** Arrays mit Werten (jedes Array = ein Feld)
- **Values:** Alle Werte für ein Feld in einem Array

**Beispiel:**
```json
{
  "schema": {
    "fields": [
      {"name": "firstSeen", "type": "time"},
      {"name": "Modell", "type": "string"}
    ]
  },
  "data": {
    "values": [
      [1746803051510, 1747307159276, ...],  // firstSeen (Timestamps)
      ["BMW 320d", "Audi A4", ...]          // Modell (Strings)
    ]
  }
}
```

### MongoDB-Query

Die MongoDB-Query wird nicht in der HAR-Datei angezeigt (nur RefId und Datasource). Die Query muss aus dem Dashboard extrahiert werden oder durch Reverse-Engineering ermittelt werden.

---

## 📚 DOKUMENTATION

**Erstellt:**
- ✅ `scripts/analyse_har_file.py` - HAR-Analyse-Script
- ✅ `scripts/analyse_motocost_queries.py` - Query-Analyse-Script
- ✅ `docs/ANALYSE_MOTOCOST_DASHBOARD_TAG212.md` - Erste Analyse
- ✅ `docs/ANALYSE_MOTOCOST_DASHBOARD_TAG212_FINAL.md` - Diese Datei

**HAR-Datei:**
- `/mnt/greiner-portal-sync/docs/dashboard.motocost.com.har` (22.8 MB)
- `/mnt/greiner-portal-sync/docs/dashboard.motocost.com_analysis.json` - Analyse-Ergebnisse
- `/mnt/greiner-portal-sync/docs/dashboard.motocost.com_queries_analysis.json` - Query-Analyse

---

**Status:** ✅ **Bereit für Implementierung**  
**Nächster Schritt:** Grafana-Client implementieren oder MongoDB-Query-Struktur klären
