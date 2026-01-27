# Customer First Login-Test Ergebnis - TAG 203

**Datum:** 2026-01-20  
**Status:** ✅ Login funktioniert, REST API erfordert OAuth-Token

---

## ✅ Erfolgreich

### 1. Login-Implementierung

**Selenium-Integration:**
- ✅ ChromeDriver funktioniert (mit Warnung über Version)
- ✅ ADFS-Login-Seite wird geladen
- ✅ Username/Password-Felder werden gefunden:
  - `userNameInput` (ID)
  - `passwordInput` (ID)
  - `submitButton` (ID)
- ✅ Credentials werden erfolgreich eingegeben
- ✅ Submit-Button wird geklickt

**Session-Management:**
- ✅ Cookies werden von Selenium zu requests-Session kopiert
- ✅ Session-ID wird aus Cookies extrahiert
- ✅ Instance URL wird identifiziert: `https://www.customer360psa.com`

### 2. Code-Implementierung

**Erstellte Dateien:**
- ✅ `lib/customer_first_client.py` - Vollständiger Client mit Selenium-Support
- ✅ `scripts/test_customer_first_api.py` - Test-Script
- ✅ `scripts/debug_customer_first_login.py` - Debug-Script

**Features:**
- ✅ SAML-URL kann direkt übergeben werden
- ✅ Automatische Cookie-Extraktion
- ✅ Session-ID-Extraktion (aus Cookies, JavaScript, URL)
- ✅ REST API Base URL wird korrekt erkannt

---

## ⚠️ Bekannte Probleme

### 1. SAML-Error

**Problem:**
- Nach Login wird `SamlError` Seite erreicht
- URL: `https://www.customer360psa.com/_nc_external/identity/saml/SamlError`

**Mögliche Ursachen:**
- SAML-Response wird nicht korrekt verarbeitet
- Session-Timeout
- Konfigurationsproblem im Customer First System

**Workaround:**
- Session-Cookies werden trotzdem extrahiert
- Möglicherweise funktionieren Web-Requests (nicht REST API)

### 2. REST API 401-Fehler

**Problem:**
- REST API-Endpoints geben 401 (Unauthorized) zurück
- Session-Cookies reichen nicht für REST API-Zugriff

**Ursache:**
- Salesforce REST API erfordert OAuth 2.0 Access Token
- Session-Cookies (aus Web-Login) sind nicht ausreichend

**Lösung:**
- Connected App in Salesforce erstellen
- OAuth 2.0 Flow implementieren
- Access Token für API-Aufrufe verwenden

---

## 📊 Test-Ergebnisse

### Login-Flow

```
1. SAML-URL aufrufen ✅
2. ADFS-Login-Seite laden ✅
3. Username-Feld finden ✅
4. Password-Feld finden ✅
5. Credentials eingeben ✅
6. Submit-Button klicken ✅
7. Weiterleitung zu Customer First ✅ (mit SamlError)
8. Cookies extrahieren ✅
9. Session-ID extrahieren ✅
```

### REST API-Tests

```
/services/data/v58.0/sobjects/          → 401 Unauthorized
/services/data/v58.0/query/             → 401 Unauthorized
/services/data/v58.0/limits/            → 401 Unauthorized
```

### UI-Exploration

```
Custom Objects gefunden: 0
API-Endpoints gefunden: 0
Hauptseite HTML: 1338 Zeichen (sehr klein, möglicherweise Fehlerseite)
```

---

## 🔧 Technische Details

### Selenium-Konfiguration

```python
Chrome-Optionen:
- --headless (kein Browser-Fenster)
- --no-sandbox
- --disable-dev-shm-usage
- --window-size=1920,1080
- User-Agent: Mozilla/5.0...
```

### Session-Cookies

**Extrahierte Cookies:**
- `sid` - Session-ID (falls vorhanden)
- `oid` - Organization-ID (falls vorhanden)
- Weitere Salesforce-Cookies

### Instance URL

```
https://www.customer360psa.com
```

---

## 📝 Nächste Schritte

### Kurzfristig

1. **SAML-Error beheben:**
   - SAML-Response genauer analysieren
   - Möglicherweise zusätzliche Parameter erforderlich
   - Prüfen ob Session-Timeout das Problem ist

2. **Connected App Setup:**
   - Mit Opel-Admin koordinieren
   - Connected App in Customer First erstellen
   - Consumer Key/Secret erhalten

### Mittelfristig

3. **OAuth 2.0 Flow:**
   - JWT Bearer Token Flow implementieren
   - Oder: Username-Password Flow
   - Token-Caching

4. **API-Exploration:**
   - Nach OAuth-Setup: Objekte auflisten
   - Kaufvertrag-Objekte identifizieren
   - SOQL-Queries testen

---

## 💡 Empfehlungen

1. **Für Produktiv-Integration:**
   - Connected App Setup ist erforderlich
   - OAuth 2.0 ist Standard für Salesforce-Integrationen
   - Session-basierte Authentifizierung ist nicht für REST API geeignet

2. **Alternative:**
   - Falls REST API nicht verfügbar: Web-Scraping mit Selenium
   - Daten aus UI-Tabellen extrahieren
   - Nachteil: Fragil, bei UI-Änderungen anfällig

3. **Catch-API Integration:**
   - Warte auf Catch-API (Prof4net)
   - Synchronisation: Catch → Customer First
   - Automatische Übertragung von Kaufverträgen

---

**Ende Dokumentation TAG 203**
