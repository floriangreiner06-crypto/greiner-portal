# RepDoc API Analyse - TAG 215

**Datum:** 2026-01-27  
**Status:** ✅ **API gefunden, aber Teile-Suche-Endpoint noch nicht identifiziert**

---

## 🎯 ERGEBNISSE

### ✅ API gefunden!

**API-Base-URL:**
```
https://lite.repdoc.com/WsCloudDataServiceLite/api
```

**Authentifizierung:**
- JWT-Token (JSON Web Token)
- Header: `Authorization: <JWT-Token>`
- Zusätzlich: `ClientId: SC_LCB_01_011eJ4eQs1T0YW7t7c8ls9FTK3TPqDoJOAJiWUtgWaPlIgHt`

**Funktionierende Endpoints:**
- ✅ `GET /api/Benutzer/current` - Benutzer-Info (Status 200)

**Nicht gefundene Endpoints:**
- ❌ `/api/Ersatzteile/search` - 404
- ❌ `/api/Ersatzteile/list` - 404
- ❌ `/api/Teile/search` - 404
- ❌ `/api/Parts/search` - 404

---

## 📊 GEFUNDENE API-REQUESTS

### Während Login/Suche:

1. **DataServiceUrl:**
   - `GET https://www.repdoc.com/WM/Ws/Home/DataServiceUrl`
   - Headers: `X-Requested-With: XMLHttpRequest`

2. **Benutzer-Info:**
   - `GET https://lite.repdoc.com/WsCloudDataServiceLite/api/Benutzer/current`
   - Headers: `Authorization: <JWT-Token>`, `ClientId: <ID>`

3. **Arbeitswerte:**
   - `GET https://lite.repdoc.com/WsCloudDataServiceLite/api/Arbeitswerte/list?PageSize=10&SearchText=ProAW`
   - (Wahrscheinlich für Arbeitszeiten, nicht Teile)

4. **Global Actions:**
   - `GET https://lite.repdoc.com/WsCloudDataServiceLite/api/WsCloudUi/GlobalActions/list?version=5`

---

## 🔍 NÄCHSTE SCHRITTE

### Option 1: Weitere API-Endpoints finden
- Während einer tatsächlichen Teile-Suche im Browser die Network-Requests analysieren
- Suche nach Requests zu `lite.repdoc.com` während der Suche
- Mögliche Endpoints: `/api/Ersatzteile/*`, `/api/Teile/*`, `/api/Search/*`

### Option 2: Scraping optimieren
- Da Teile-Suche-Endpoint nicht gefunden wurde, weiter mit Selenium-Scraping
- HTML-Parsing der Suchergebnisse verbessern
- Login funktioniert bereits ✅

### Option 3: TROST/Limex kontaktieren
- Nach API-Dokumentation fragen
- Nach Teile-Suche-Endpoint fragen
- Möglicherweise gibt es eine interne Dokumentation

---

## 💡 ERKENNTNISSE

1. **RepDoc hat eine REST API** ✅
   - Base-URL: `https://lite.repdoc.com/WsCloudDataServiceLite/api`
   - JWT-basierte Authentifizierung
   - CORS-fähig (Origin: https://www.repdoc.com)

2. **Token-Extraktion funktioniert** ✅
   - Token wird nach Login automatisch generiert
   - Token ist in `Authorization`-Header enthalten
   - Token scheint session-basiert zu sein

3. **Teile-Suche-Endpoint unbekannt** ⚠️
   - Verschiedene Endpoint-Namen getestet (alle 404)
   - Muss während echter Suche analysiert werden
   - Oder in API-Dokumentation nachschlagen

---

## 📝 CODE-REFERENZEN

**Erstellte Dateien:**
- `tools/scrapers/repdoc_api_explorer.py` - Network-Request-Analyse
- `tools/scrapers/repdoc_api_test.py` - API-Endpoint-Tests
- `tools/scrapers/repdoc_api_analyze_headers.py` - Header-Analyse
- `tools/scrapers/repdoc_api_with_token.py` - API-Client mit JWT-Token

**Ergebnisse:**
- `/tmp/repdoc_api_requests.json` - Gespeicherte API-Requests

---

## 🎯 EMPFEHLUNG

**Kurzfristig:**
- Weiter mit Selenium-Scraping (Login funktioniert bereits)
- HTML-Parsing der Suchergebnisse verbessern

**Mittelfristig:**
- Während echter Suche im Browser Network-Requests analysieren
- Nach Teile-Suche-Endpoint suchen
- Falls gefunden: Scraper auf API umstellen (viel schneller!)

**Langfristig:**
- TROST/Limex nach API-Dokumentation fragen
- Offizielle API-Integration anstreben

---

**Status:** ✅ API gefunden, aber Teile-Suche-Endpoint noch nicht identifiziert  
**Nächster Schritt:** Scraping optimieren ODER weitere API-Endpoints suchen
