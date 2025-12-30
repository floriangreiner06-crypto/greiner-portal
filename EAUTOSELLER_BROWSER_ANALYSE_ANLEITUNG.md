# eAutoseller Browser-Analyse Anleitung

**Ziel:** API-Endpoints und Request-Strukturen identifizieren

---

## 🔍 SCHRITT 1: LOGIN & VORBEREITUNG

### 1.1 Browser öffnen
- Chrome, Firefox oder Edge
- Entwicklertools aktivieren (F12)

### 1.2 Login auf eAutoseller
- **URL:** https://greiner.eautoseller.de/
- **User:** fGreiner
- **Pass:** fGreiner12

### 1.3 Entwicklertools vorbereiten
1. **Network-Tab öffnen**
   - F12 → Tab "Network" (Netzwerk)
   - Filter: "XHR" oder "Fetch" aktivieren
   - "Preserve log" aktivieren (Logs behalten)

2. **Console-Tab öffnen**
   - Für JavaScript-Fehler und Logs

---

## 🔍 SCHRITT 2: NETWORK-TRAFFIC ANALYSIEREN

### 2.1 Nach Login
**Aktion:** Nach erfolgreichem Login Network-Tab prüfen

**Zu dokumentieren:**
- [ ] Alle Requests nach Login
- [ ] URLs der API-Calls
- [ ] Request-Methoden (GET, POST, etc.)
- [ ] Request-Headers (besonders Authorization)
- [ ] Request-Body (bei POST/PUT)
- [ ] Response-Status (200, 401, etc.)
- [ ] Response-Format (JSON, XML, HTML)

**Beispiel-Notizen:**
```
POST /api/login
Headers: Content-Type: application/json
Body: {"username": "fGreiner", "password": "..."}
Response: 200, {"token": "..."}
```

### 2.2 Hauptseite laden
**Aktion:** Hauptseite/Dashboard öffnen

**Zu prüfen:**
- [ ] Welche Daten werden geladen?
- [ ] Gibt es AJAX/Fetch-Calls?
- [ ] Werden Fahrzeugdaten abgerufen?

### 2.3 Fahrzeuge anzeigen
**Aktion:** Fahrzeugliste/Fahrzeugübersicht öffnen

**Zu dokumentieren:**
- [ ] API-Endpoint für Fahrzeugliste
- [ ] Request-Parameter (Filter, Pagination, etc.)
- [ ] Response-Struktur
- [ ] Datenformat (JSON, XML)

**Beispiel:**
```
GET /api/vehicles?page=1&limit=20
Response: {"vehicles": [...], "total": 150}
```

### 2.4 Einzelnes Fahrzeug öffnen
**Aktion:** Ein Fahrzeug aus der Liste öffnen

**Zu dokumentieren:**
- [ ] API-Endpoint für Fahrzeugdetails
- [ ] ID-Parameter (wie wird Fahrzeug identifiziert?)
- [ ] Response-Struktur

**Beispiel:**
```
GET /api/vehicles/12345
Response: {"id": 12345, "make": "...", "model": "..."}
```

### 2.5 Fahrzeug bearbeiten
**Aktion:** Fahrzeug bearbeiten/speichern

**Zu dokumentieren:**
- [ ] API-Endpoint für Update
- [ ] Request-Method (PUT, PATCH, POST?)
- [ ] Request-Body-Struktur
- [ ] Validierung

**Beispiel:**
```
PUT /api/vehicles/12345
Body: {"price": 15000, "km": 50000}
Response: 200, {"success": true}
```

---

## 🔍 SCHRITT 3: REQUEST-DETAILS DOKUMENTIEREN

### 3.1 Für jeden API-Call notieren:

#### Request-Informationen:
- **URL:** Vollständige URL
- **Method:** GET, POST, PUT, DELETE, etc.
- **Headers:**
  - Authorization (Token, Basic Auth, Cookie?)
  - Content-Type
  - Accept
  - Custom Headers
- **Query Parameters:** ?param=value
- **Body:** Bei POST/PUT (JSON, Form-Data, etc.)

#### Response-Informationen:
- **Status Code:** 200, 201, 400, 401, 404, etc.
- **Content-Type:** application/json, application/xml, etc.
- **Response Body:** Struktur dokumentieren
- **Response Headers:** Wichtige Header (z.B. Pagination)

### 3.2 Beispiel-Dokumentation:

```markdown
## API: Fahrzeugliste abrufen

**Endpoint:** GET /api/vehicles

**Headers:**
- Authorization: Bearer {token}
- Content-Type: application/json
- Accept: application/json

**Query Parameters:**
- page: 1 (optional)
- limit: 20 (optional)
- filter: {make, model, price} (optional)

**Response (200 OK):**
```json
{
  "vehicles": [
    {
      "id": 12345,
      "make": "BMW",
      "model": "320d",
      "price": 15000,
      "km": 50000
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 20
}
```

**Fehler (401 Unauthorized):**
```json
{
  "error": "Unauthorized",
  "message": "Invalid token"
}
```
```

---

## 🔍 SCHRITT 4: JAVASCRIPT-ANALYSE

### 4.1 Sources-Tab prüfen
1. **Sources-Tab öffnen** (Quellen)
2. **JavaScript-Dateien durchsuchen:**
   - Nach API-URLs suchen
   - Nach fetch/axios/$.ajax suchen
   - Nach API-Konstanten suchen

**Zu suchen:**
- `api/`
- `fetch(`
- `axios.`
- `$.ajax(`
- `XMLHttpRequest`
- `baseURL`
- `API_URL`

### 4.2 Console-Befehle
**In Console ausführen:**
```javascript
// Suche nach API-URLs
console.log(window.API_URL);
console.log(window.apiBaseUrl);
console.log(window.config);

// Prüfe ob API-Client vorhanden
console.log(window.api);
console.log(window.axios);
```

---

## 🔍 SCHRITT 5: COOKIES & SESSION

### 5.1 Application-Tab prüfen
1. **Application-Tab öffnen** (Anwendung)
2. **Cookies prüfen:**
   - Welche Cookies werden gesetzt?
   - Session-Cookie?
   - Auth-Token?

3. **Local Storage prüfen:**
   - Gespeicherte Tokens?
   - API-Konfiguration?

4. **Session Storage prüfen:**
   - Temporäre Daten?

---

## 📋 CHECKLISTE FÜR DOKUMENTATION

### API-Endpoints:
- [ ] Login-Endpoint
- [ ] Logout-Endpoint
- [ ] Fahrzeugliste
- [ ] Fahrzeugdetails
- [ ] Fahrzeug erstellen
- [ ] Fahrzeug aktualisieren
- [ ] Fahrzeug löschen
- [ ] Weitere Endpoints

### Authentifizierung:
- [ ] Auth-Methode (Token, Basic Auth, Cookie?)
- [ ] Token-Format
- [ ] Token-Lebensdauer
- [ ] Refresh-Mechanismus

### Datenstrukturen:
- [ ] Fahrzeug-Objekt-Struktur
- [ ] Request-Body-Formate
- [ ] Response-Formate
- [ ] Fehler-Formate

### Besonderheiten:
- [ ] Pagination
- [ ] Filtering
- [ ] Sorting
- [ ] Rate Limiting
- [ ] CORS-Einstellungen

---

## 🎯 ERGEBNIS-DOKUMENTATION

Nach der Analyse eine Datei erstellen:

**Datei:** `docs/EAUTOSELLER_API_ENDPOINTS.md`

**Inhalt:**
- Liste aller gefundenen Endpoints
- Request/Response-Beispiele
- Authentifizierung
- Fehlerbehandlung
- Code-Beispiele für Integration

---

## 💡 TIPPS

1. **Screenshots machen:**
   - Network-Tab mit Requests
   - Request-Details
   - Response-Details

2. **Export-Funktion nutzen:**
   - Network-Tab → Rechtsklick → "Save as HAR"
   - Kann später analysiert werden

3. **Postman/Insomnia:**
   - Requests aus Browser kopieren
   - Als Collection speichern
   - Für spätere Tests nutzen

4. **Mehrere Aktionen testen:**
   - Nicht nur eine Aktion
   - Verschiedene Bereiche testen
   - Edge-Cases prüfen

---

## 🚀 NACH DER ANALYSE

1. **Dokumentation erstellen:**
   - Alle Endpoints dokumentieren
   - Code-Beispiele erstellen

2. **API-Client entwickeln:**
   - Python-Client für DRIVE Portal
   - Integration in bestehende Struktur

3. **Tests schreiben:**
   - Unit-Tests für API-Calls
   - Integration-Tests

---

**Viel Erfolg bei der Analyse! 🔍**

