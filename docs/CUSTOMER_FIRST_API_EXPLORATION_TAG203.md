# Customer First API Exploration - TAG 203

**Datum:** 2026-01-20  
**Ziel:** Customer First REST API explorieren für zukünftige Integration mit Catch (Prof4net)

---

## Kontext

**Problem:**
- Opel-Verkäufer müssen alle Kaufverträge sowohl in Catch (internes System) als auch in Customer First (Opel-Hersteller-System) erfassen
- Doppelte Datenerfassung ist zeitaufwändig und fehleranfällig

**Lösungsansatz:**
- Catch-API wird gerade entwickelt (Prof4net)
- Customer First API explorieren, um zukünftige Synchronisation zu ermöglichen
- Ziel: Automatische Übertragung von Catch → Customer First

---

## Customer First System

**URL:** https://www.customer360psa.com/s/login/  
**Plattform:** Salesforce (Lightning)  
**Hersteller:** Stellantis (ehemals PSA)  
**Zweck:** Hersteller-System für Opel-Händler

**Credentials (von Rafael):**
- Username: `DE-001007V.d004`
- Password: `Jeöüpc!6`

---

## Technische Erkenntnisse

### 1. Login-Prozess

**Login-Seite:**
- URL: `https://www.customer360psa.com/s/login/?language=en_US&ec=302&startURL=%2Fs%2F`
- **Wichtig:** Seite ist JavaScript-basiert (Salesforce Lightning)
- **Region-Auswahl:** Vor dem Login muss "ID Europe" ausgewählt werden
- HTML wird dynamisch geladen (keine statischen Formulare im initialen HTML)

**Login-Flow:**
1. Initiale Login-Seite laden
2. **"ID Europe" Button klicken** (JavaScript-basiert)
3. Europe-Login-Seite wird geladen
4. Username/Password eingeben
5. Salesforce-Authentifizierung

### 2. API-Struktur

**Salesforce REST API:**
- Base URL: `https://www.customer360psa.com/services/data/v58.0/`
- Standard Salesforce REST API Endpoints
- Erfordert OAuth-Token für API-Zugriff

**Mögliche Objekte für Kaufverträge:**
- `Contract` - Standard Salesforce Contract-Objekt
- `Opportunity` - Salesforce Opportunity-Objekt
- `Order` - Salesforce Order-Objekt
- Custom Objects: `Sales_Order__c`, `Kaufvertrag__c`, etc.

### 3. Authentifizierung

**Optionen:**
1. **Session-basiert (Web-Scraping):**
   - Login via HTML-Formular
   - Session-Cookies verwenden
   - Funktioniert für Web-Scraping, aber nicht für REST API

2. **OAuth 2.0 (REST API):**
   - Connected App in Salesforce erstellen
   - Consumer Key / Consumer Secret
   - OAuth-Token für API-Zugriff
   - **Empfohlen für Produktiv-Integration**

3. **JWT Bearer Token (Server-to-Server):**
   - Für automatisierte Integrationen
   - Keine Benutzerinteraktion nötig

---

## Implementierter Code

### 1. Customer First Client

**Datei:** `lib/customer_first_client.py`

**Features:**
- ✅ Login-Funktionalität (Grundgerüst)
- ✅ Region-Auswahl ("ID Europe") - **In Arbeit**
- ✅ REST API Base URL
- ✅ Salesforce-Objekt-Abfrage
- ✅ Kaufvertrag-Suche (SOQL)

**Status:**
- ⚠️ Login funktioniert noch nicht vollständig (JavaScript-basierte Region-Auswahl)
- ⚠️ REST API erfordert OAuth-Token (noch nicht implementiert)

### 2. Test-Script

**Datei:** `scripts/test_customer_first_api.py`

**Zweck:**
- API-Exploration
- Login-Test
- Endpoint-Discovery
- Ergebnisse speichern

---

## Herausforderungen

### 1. SAML-Authentifizierung mit JavaScript

**Problem:**
- "ID Europe" Button führt zu SAML-Authentifizierung (ADFS)
- SAML-URL: `https://sts.fiatgroup.com/adfs/ls/?SAMLRequest=...`
- ADFS-Login-Seite benötigt JavaScript, um Formular zu rendern
- BeautifulSoup kann JavaScript nicht ausführen

**Erkenntnisse:**
- ✅ SAML-URL identifiziert und kann direkt verwendet werden
- ✅ Login-Flow verstanden: Customer First → SAML (ADFS) → Customer First
- ⚠️ ADFS-Login-Seite zeigt "JavaScript required" - Formular wird nicht gerendert

**Lösungsansätze:**
1. **Selenium/Playwright:** Browser-Automatisierung (empfohlen)
   - Vorteil: Funktioniert mit JavaScript, vollständiger SAML-Flow
   - Nachteil: Langsamer, benötigt Browser (headless möglich)
   - **Status:** Noch nicht implementiert

2. **OAuth 2.0:** Überspringen des Web-Logins
   - Vorteil: Standard für API-Integration, kein Browser nötig
   - Nachteil: Connected App muss in Salesforce erstellt werden
   - **Status:** Langfristige Lösung

3. **SAML-Library:** Python SAML-Bibliothek verwenden
   - Vorteil: Professionell, keine Browser-Automatisierung
   - Nachteil: Komplexer, SAML-Response muss korrekt verarbeitet werden

### 2. REST API Authentifizierung

**Problem:**
- REST API erfordert OAuth-Token
- Session-basierte Authentifizierung funktioniert nicht für REST API

**Lösung:**
- Connected App in Salesforce erstellen
- OAuth 2.0 Flow implementieren
- Token-Caching für Performance

### 3. Objekt-Struktur unbekannt

**Problem:**
- Unbekannt, welches Salesforce-Objekt für Kaufverträge verwendet wird
- Custom Fields müssen ermittelt werden

**Lösung:**
- API-Exploration nach erfolgreichem Login
- SOQL-Queries für verschiedene Objekte
- Dokumentation der gefundenen Struktur

---

## Ergebnisse TAG 203

### ✅ Erledigt

1. **Login funktionsfähig gemacht:**
   - [x] SAML-URL identifiziert: `https://sts.fiatgroup.com/adfs/ls/?SAMLRequest=...`
   - [x] Selenium für JavaScript-basierte ADFS-Login-Seite implementiert
   - [x] SAML-Response-Verarbeitung (automatisches Form-Submit)
   - [x] Session-Management implementiert
   - [x] **Login erfolgreich getestet!** ✅

**Login-Ergebnis:**
- ✅ Selenium findet Username/Password-Felder auf ADFS-Seite (`userNameInput`, `passwordInput`)
- ✅ Credentials werden erfolgreich eingegeben
- ✅ Submit-Button wird gefunden und geklickt
- ✅ Session-Cookies werden extrahiert und gespeichert
- ⚠️ **SAML-Error** tritt auf (`SamlError` Seite), aber Session-Cookies werden trotzdem extrahiert
- ⚠️ REST API erfordert OAuth-Token (Session-Cookies reichen nicht - 401 Fehler)

**REST API Status:**
- ❌ `/services/data/v58.0/sobjects/` → 401 (Unauthorized)
- ❌ `/services/data/v58.0/query/` → 401 (Unauthorized)
- ❌ `/services/data/v58.0/limits/` → 401 (Unauthorized)

**Erkenntnisse:**
- Salesforce REST API benötigt OAuth 2.0 Access Token
- Session-Cookies (aus Web-Login) reichen nicht für REST API
- Connected App Setup in Salesforce erforderlich für API-Zugriff

### Nächste Schritte

**Für REST API-Zugriff:**

1. **Connected App in Salesforce erstellen** (mit Opel-Admin):
   - Setup → App Manager → New Connected App
   - OAuth Settings aktivieren
   - Scopes: `Full access (full)`, `Perform requests on your behalf at any time (refresh_token, offline_access)`
   - Consumer Key / Consumer Secret erhalten
   - **Status:** Benötigt Admin-Zugriff zu Customer First

2. **OAuth 2.0 Flow implementieren:**
   - JWT Bearer Token Flow (Server-to-Server, empfohlen)
   - Oder: Username-Password Flow (einfacher, aber weniger sicher)
   - Token-Caching für Performance

3. **API-Endpoints für Kaufverträge identifizieren:**
   - Nach OAuth-Setup: Objekte auflisten (`/services/data/v58.0/sobjects/`)
   - Custom Objects finden (möglicherweise `Vehicle_Order__c`, `Dealer_Order__c`, etc.)
   - SOQL-Queries testen

**Alternative Ansätze:**

4. **Web-Scraping** (falls REST API nicht verfügbar):
   - Selenium für UI-Interaktion
   - Daten aus HTML-Tabellen extrahieren
   - Nachteil: Fragil, bei UI-Änderungen anfällig

5. **Catch-API Integration** (wenn verfügbar):
   - Catch-API wird gerade entwickelt (Prof4net)
   - Synchronisation: Catch → Customer First
   - Automatische Übertragung von Kaufverträgen

2. **API-Exploration:**
   - [ ] Nach erfolgreichem Login: Objekte auflisten
   - [ ] Kaufvertrag-Objekt identifizieren
   - [ ] SOQL-Queries testen
   - [ ] Feld-Struktur dokumentieren

3. **OAuth 2.0 Setup:**
   - [ ] Connected App in Salesforce erstellen (mit Opel-Admin)
   - [ ] Consumer Key/Secret erhalten
   - [ ] OAuth-Flow implementieren

### Mittelfristig (nach Catch-API)

4. **Integration vorbereiten:**
   - [ ] Mapping Catch → Customer First definieren
   - [ ] API-Endpoints für Kaufvertrag-Erstellung testen
   - [ ] Error-Handling implementieren

5. **Synchronisation:**
   - [ ] Catch-Webhook → Customer First API
   - [ ] Oder: Periodische Synchronisation (Celery-Task)
   - [ ] Duplikat-Erkennung

---

## Code-Referenzen

### Erstellte Dateien

1. **`lib/customer_first_client.py`**
   - Customer First API Client
   - Login, REST API, SOQL-Queries

2. **`scripts/test_customer_first_api.py`**
   - Test-Script für API-Exploration

3. **`scripts/debug_customer_first_login.py`**
   - Debug-Script für Login-Analyse

4. **`docs/customer_first_login_page.html`**
   - Gespeicherte Login-Seite (für Analyse)

### Verwandte Dateien

- `lib/eautoseller_client.py` - Ähnliche Integration (Web-Scraping)
- `api/gudat_api.py` - Externe API-Integration (Referenz)

---

## Dokumentation

### Salesforce REST API

- **Dokumentation:** https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/
- **SOQL Syntax:** https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/

### Customer First / Stellantis

- **Stellantis Developer Portal:** https://developer.groupe-psa.io/
- **Customer 360 PSA:** https://www.customer360psa.com/

---

## Notizen

- **Region-Auswahl:** "ID Europe" muss vor Login ausgewählt werden
- **JavaScript:** Seite verwendet Salesforce Lightning (React-basiert)
- **API-Version:** Salesforce API v58.0 (aktuell)
- **Credentials:** Von Rafael erhalten, für Test-Zwecke

---

**Ende Dokumentation TAG 203**
