# Analyse: Motocost Dashboard für auto1.com Integration

**TAG:** 212  
**Datum:** 2026-01-26  
**Status:** 🔍 **ANALYSE IN PROGRESS**

---

## 🎯 ZIEL

Integration des motocost-Dashboards für Zukäufer Rolf und Anton in DRIVE Portal.  
Das Dashboard zeigt interessante auto1.com Angebote basierend auf gesammelten Daten.

---

## 📊 ERKANNTE STRUKTUR

### Technologie-Stack
- **Plattform:** Grafana Dashboard
- **URL:** https://dashboard.motocost.com
- **Authentifizierung:** Grafana Login (Email + Passwort)
- **Login-Daten:**
  - Email: `Florian.greiner@auto-greiner.de`
  - Passwort: `fdg547fdgEE`

### Grafana-Erkennung
- ✅ Grafana-Dashboard erkannt
- ✅ `window.grafanaBootData` vorhanden
- ✅ Standard Grafana-API-Struktur (`/api/*`)

---

## 🔐 AUTHENTIFIZIERUNG

### Status: ⚠️ **Login-Problem**

**Versuchte Methoden:**
1. ❌ HTML-Formular-Login (keine Formulare gefunden - JavaScript-basiert)
2. ❌ Grafana `/api/login` mit JSON
3. ❌ Grafana `/api/login` mit form-data

**Ergebnis:**
- Alle Versuche führen zu `401 Unauthorized`
- Mögliche Gründe:
  - OAuth/LDAP-Authentifizierung (nicht Standard-Login)
  - Spezielle Grafana-Konfiguration
  - Falsche API-Endpoints

**Nächste Schritte:**
1. Manuelles Login im Browser durchführen
2. Browser-DevTools analysieren (Network-Tab)
3. Cookies/Headers nach Login extrahieren
4. OAuth-Provider prüfen (`/api/auth/providers`)

---

## 🔍 VERFÜGBARE API-ENDPOINTS

### Gefundene Endpoints (401 ohne Auth):
- `/api/login` - Login-Endpoint
- `/api/user` - User-Informationen
- `/api/auth/keys` - API-Keys
- `/api/auth/providers` - OAuth-Provider

### Erwartete Grafana-Endpoints (nach Login):
- `/api/dashboards/*` - Dashboard-Daten
- `/api/datasources` - Datenquellen
- `/api/search` - Dashboard-Suche
- `/api/query` - Daten-Abfragen

---

## 💡 INTEGRATIONS-OPTIONEN

### Option 1: API-Integration (EMPFOHLEN) ⭐⭐⭐

**Voraussetzungen:**
- ✅ Grafana API-Zugriff nach Login
- ✅ API-Keys oder Session-Cookies
- ✅ Dashboard-UIDs identifizieren

**Vorgehen:**
1. Login via API (oder Session-Cookies)
2. Dashboard-Daten via `/api/dashboards/uid/{uid}`
3. Query-Daten via `/api/datasources/{id}/query`
4. Daten in DRIVE importieren

**Vorteile:**
- ✅ Automatisiert
- ✅ Echtzeit-Daten
- ✅ Keine Scraping-Logik nötig

**Nachteile:**
- ⚠️ API-Zugriff muss funktionieren
- ⚠️ Abhängigkeit von Grafana-API

---

### Option 2: Browser-Automation (Selenium/Playwright) ⭐⭐

**Vorgehen:**
1. Selenium/Playwright für Login
2. Dashboard-Seite laden
3. Daten aus HTML/JavaScript extrahieren
4. In DRIVE importieren

**Vorteile:**
- ✅ Funktioniert auch ohne direkte API
- ✅ Kann JavaScript-basierte Dashboards handhaben

**Nachteile:**
- ❌ Komplexer (Browser-Automation)
- ❌ Langsamer (Browser-Overhead)
- ❌ Wartungsaufwand (bei Änderungen)

---

### Option 3: Manueller Export + Import ⭐

**Vorgehen:**
1. Rolf/Anton exportieren Daten aus Dashboard (CSV/Excel)
2. Upload in DRIVE
3. Automatische Verarbeitung

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ Keine API-Abhängigkeit

**Nachteile:**
- ❌ Manueller Schritt nötig
- ❌ Nicht automatisiert

---

## 🎯 EMPFOHLENE VORGEWHENSWEISE

### Phase 1: Authentifizierung klären (SOFORT)

1. **Browser-Login analysieren:**
   ```bash
   # User soll sich manuell einloggen
   # Browser DevTools → Network-Tab öffnen
   # Login durchführen
   # Request analysieren:
   #   - URL
   #   - Method (POST/GET)
   #   - Headers
   #   - Body/Form-Data
   #   - Cookies nach Login
   ```

2. **Grafana-Konfiguration prüfen:**
   - OAuth-Provider aktiv?
   - LDAP-Authentifizierung?
   - Custom-Auth?

3. **API-Keys prüfen:**
   - Gibt es Service-Accounts?
   - API-Keys für automatisierten Zugriff?

---

### Phase 2: Datenstruktur analysieren (nach Login)

1. **Dashboard-UIDs identifizieren:**
   ```bash
   GET /api/search?query=auto1
   # → Liste aller Dashboards
   ```

2. **Datenquellen identifizieren:**
   ```bash
   GET /api/datasources
   # → Liste aller Datenquellen
   ```

3. **Dashboard-Daten abrufen:**
   ```bash
   GET /api/dashboards/uid/{uid}
   # → Dashboard-Konfiguration
   # → Panel-Definitionen
   # → Query-Definitionen
   ```

4. **Daten abfragen:**
   ```bash
   POST /api/datasources/{id}/query
   # → Rohdaten (JSON)
   ```

---

### Phase 3: DRIVE-Integration (nach Analyse)

1. **Datenbank-Schema:**
   ```sql
   CREATE TABLE auto1_angebote (
       id SERIAL PRIMARY KEY,
       auto1_id VARCHAR(50) UNIQUE,
       vin VARCHAR(17),
       marke VARCHAR(50),
       modell VARCHAR(200),
       baujahr INTEGER,
       km_stand INTEGER,
       preis_ek DECIMAL(10,2),
       preis_vk_erwartet DECIMAL(10,2),
       db_erwartet DECIMAL(10,2),
       standort_empfohlen INTEGER,
       interessant BOOLEAN DEFAULT false,
       status VARCHAR(20),
       zukaeufer VARCHAR(50),
       notizen TEXT,
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. **API-Modul:**
   - `api/zukauf_api.py` - Datenlogik
   - `lib/motocost_client.py` - Grafana-Client

3. **Routes:**
   - `routes/zukauf_routes.py` - Flask-Routes

4. **Templates:**
   - `templates/zukauf/auto1_angebote.html` - Dashboard

---

## 📝 NÄCHSTE SCHRITTE

### SOFORT (User-Aktion erforderlich):

1. **✅ Browser-Login durchführen:**
   - DevTools öffnen (F12)
   - Network-Tab aktivieren
   - Login durchführen
   - Request analysieren:
     - Welche URL wird aufgerufen?
     - Welche Daten werden gesendet?
     - Welche Cookies werden gesetzt?

2. **✅ Dashboard-Struktur dokumentieren:**
   - Welche Dashboards gibt es?
   - Welche Daten werden angezeigt?
   - Welche Filter/Kriterien sind verfügbar?

3. **✅ API-Zugriff prüfen:**
   - Nach Login: `/api/user` aufrufen
   - Funktioniert es?
   - Welche Rechte hat der User?

---

### DANACH (Technische Umsetzung):

1. **Grafana-Client implementieren:**
   - Login-Funktion
   - Dashboard-Abfrage
   - Daten-Extraktion

2. **DRIVE-Integration:**
   - Datenbank-Schema
   - API-Module
   - Frontend-Dashboard

3. **Automatisierung:**
   - Celery-Task für regelmäßigen Import
   - Benachrichtigungen bei interessanten Angeboten

---

## 🔧 TECHNISCHE DETAILS

### Grafana API-Referenz:
- **Login:** `POST /api/login` (user, password)
- **User:** `GET /api/user`
- **Dashboards:** `GET /api/search?query=...`
- **Dashboard-Daten:** `GET /api/dashboards/uid/{uid}`
- **Query:** `POST /api/datasources/{id}/query`

### Scripts erstellt:
- ✅ `scripts/analyse_motocost_dashboard.py` - Analyse-Script

### Dokumentation:
- ✅ `docs/ANALYSE_MOTOCOST_DASHBOARD_TAG212.md` - Diese Datei

---

## ❓ OFFENE FRAGEN

1. **Authentifizierung:**
   - Wie funktioniert der Login genau?
   - Gibt es OAuth/LDAP?
   - Gibt es API-Keys?

2. **Datenstruktur:**
   - Welche Daten werden angezeigt?
   - Welche Felder sind verfügbar?
   - Gibt es Export-Funktionen?

3. **Integration:**
   - Soll es automatisiert sein?
   - Wie oft sollen Daten aktualisiert werden?
   - Welche Filter/Kriterien sind wichtig?

---

**Status:** ⏳ **Warte auf User-Input (Browser-Login-Analyse)**
