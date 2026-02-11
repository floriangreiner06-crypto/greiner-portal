# TODO für Claude Session Start TAG 204

**Erstellt:** 2026-01-20  
**Letzte Session:** TAG 203

---

## 📋 Offene Aufgaben

### 1. Customer First API - OAuth 2.0 Setup (Hoch)

**Connected App in Salesforce erstellen:**
- Problem: REST API erfordert OAuth-Token (401-Fehler)
- Lösung: Connected App in Customer First erstellen (benötigt Admin-Zugriff)
- Schritte:
  1. Mit Opel-Admin koordinieren
  2. Connected App erstellen (Setup → App Manager → New Connected App)
  3. OAuth Settings aktivieren
  4. Scopes: `Full access (full)`, `Perform requests on your behalf at any time (refresh_token, offline_access)`
  5. Consumer Key / Consumer Secret erhalten
- Datei: `lib/customer_first_client.py` - OAuth-Flow implementieren
- **Priorität:** Hoch

**OAuth 2.0 Flow implementieren:**
- JWT Bearer Token Flow (Server-to-Server, empfohlen)
- Oder: Username-Password Flow (einfacher, aber weniger sicher)
- Token-Caching für Performance
- Datei: `lib/customer_first_client.py`
- **Priorität:** Hoch

---

### 2. Customer First API - API-Endpoints identifizieren (Mittel)

**Kaufvertrag-Objekte finden:**
- Nach OAuth-Setup: Objekte auflisten (`/services/data/v58.0/sobjects/`)
- Custom Objects identifizieren (möglicherweise `Vehicle_Order__c`, `Dealer_Order__c`, etc.)
- SOQL-Queries testen
- Datei: `lib/customer_first_client.py` - `search_kaufvertraege()` erweitern
- **Priorität:** Mittel

**API-Endpoints dokumentieren:**
- Gefundene Objekte dokumentieren
- Feld-Struktur dokumentieren
- SOQL-Queries dokumentieren
- Datei: `docs/CUSTOMER_FIRST_API_EXPLORATION_TAG203.md`
- **Priorität:** Mittel

---

### 3. Customer First API - SAML-Error beheben (Mittel)

**SAML-Error analysieren:**
- Problem: Nach Login wird `SamlError` Seite erreicht
- URL: `https://www.customer360psa.com/_nc_external/identity/saml/SamlError`
- Mögliche Ursachen:
  - SAML-Response wird nicht korrekt verarbeitet
  - Session-Timeout
  - Konfigurationsproblem
- Lösung: SAML-Response genauer analysieren
- Datei: `lib/customer_first_client.py` - `_login_with_selenium()`
- **Priorität:** Mittel

---

### 4. Code-Optimierung (Niedrig)

**ChromeDriver aktualisieren:**
- Problem: ChromeDriver Version (142) nicht kompatibel mit Chrome (143)
- Lösung: ChromeDriver aktualisieren
- **Priorität:** Niedrig (funktioniert trotzdem)

**Web-Scraping als Alternative:**
- Falls REST API nicht verfügbar: Web-Scraping mit Selenium
- Daten aus UI-Tabellen extrahieren
- Nachteil: Fragil, bei UI-Änderungen anfällig
- **Priorität:** Niedrig (nur als Fallback)

---

## 🔍 Qualitätsprobleme (aus TAG 203)

### ⚠️ Bekannte Issues

1. **SAML-Error nach Login**
   - Session-Cookies werden trotzdem extrahiert
   - Möglicherweise funktioniert Web-Zugriff nicht vollständig
   - **Priorität:** Mittel
   - **Empfehlung:** SAML-Response genauer analysieren

2. **REST API erfordert OAuth-Token**
   - Session-Cookies reichen nicht
   - Connected App Setup erforderlich
   - **Priorität:** Hoch
   - **Empfehlung:** Mit Opel-Admin koordinieren

3. **ChromeDriver Version-Warnung**
   - Funktioniert trotzdem
   - **Priorität:** Niedrig
   - **Empfehlung:** Optional aktualisieren

---

## 📝 Wichtige Hinweise für nächste Session

### Aktuelle Features (TAG 203):
- ✅ Customer First API Client erstellt
- ✅ Login mit Selenium funktioniert
- ✅ Session-Cookies werden extrahiert
- ⚠️ REST API erfordert OAuth-Token (Connected App Setup nötig)
- ⚠️ SAML-Error tritt auf (aber Login funktioniert technisch)

### Technische Details:
- **SAML-URL:** `https://sts.fiatgroup.com/adfs/ls/?SAMLRequest=...`
- **Instance URL:** `https://www.customer360psa.com`
- **REST API Base:** `https://www.customer360psa.com/services/data/v58.0`
- **Credentials:** Von Rafael erhalten (DE-001007V.d004)

### Wichtige Dateien:
- `lib/customer_first_client.py` - Haupt-Client
- `scripts/test_customer_first_api.py` - Test-Script
- `docs/CUSTOMER_FIRST_API_EXPLORATION_TAG203.md` - Dokumentation
- `docs/CUSTOMER_FIRST_LOGIN_TEST_ERGEBNIS_TAG203.md` - Test-Ergebnisse

### Dependencies:
- `selenium` - Für JavaScript-basierte Login-Seiten
- `beautifulsoup4` - Für HTML-Parsing
- `requests` - Für HTTP-Requests

---

## 🐛 Bekannte Bugs

**Keine kritischen Bugs bekannt.**

**Kleinere Issues:**
- SAML-Error nach Login (Session-Cookies werden trotzdem extrahiert)
- REST API 401-Fehler (erwartet, OAuth-Token erforderlich)
- ChromeDriver Version-Warnung (funktioniert trotzdem)

---

## 📚 Dokumentation

**Erstellt in TAG 203:**
- `docs/CUSTOMER_FIRST_API_EXPLORATION_TAG203.md` - Vollständige Exploration
- `docs/CUSTOMER_FIRST_LOGIN_TEST_ERGEBNIS_TAG203.md` - Test-Ergebnisse

**Zu aktualisieren:**
- API-Dokumentation (nach OAuth-Setup)
- Objekt-Struktur dokumentieren
- SOQL-Queries dokumentieren

---

## 🔄 Nächste Schritte (Priorität)

1. **Hoch:** Connected App Setup (mit Opel-Admin koordinieren)
2. **Hoch:** OAuth 2.0 Flow implementieren
3. **Mittel:** API-Endpoints identifizieren (nach OAuth-Setup)
4. **Mittel:** SAML-Error beheben
5. **Niedrig:** ChromeDriver aktualisieren
6. **Niedrig:** Web-Scraping als Alternative (falls REST API nicht verfügbar)

---

**Ende TODO_FOR_CLAUDE_SESSION_START_TAG204**
