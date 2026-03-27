# eAutoseller Browser-Analyse - Quick Start

**Schnelle Anleitung für die Browser-Analyse**

---

## 🚀 SCHNELLSTART (5 Minuten)

### 1. Browser öffnen & Login
1. Öffne Chrome/Firefox/Edge
2. Drücke **F12** (Entwicklertools)
3. Gehe zu **Network-Tab** (Netzwerk)
4. Aktiviere Filter: **XHR** oder **Fetch**
5. Login auf: https://greiner.eautoseller.de/
   - User: `fGreiner`
   - Pass: `fGreiner12`

### 2. Aktionen durchführen
**Während Network-Tab offen ist:**
- Fahrzeugliste öffnen
- Ein Fahrzeug öffnen
- Fahrzeug bearbeiten (falls möglich)
- Andere Funktionen nutzen

### 3. API-Calls identifizieren
**Im Network-Tab:**
- Alle Requests mit Status 200 prüfen
- Auf **XHR** oder **Fetch** Requests fokussieren
- Rechtsklick → **Copy → Copy as cURL** (für später)

### 4. Request-Details dokumentieren
**Für jeden API-Call:**
- **URL** notieren
- **Method** (GET, POST, etc.)
- **Headers** (besonders Authorization)
- **Request Body** (bei POST/PUT)
- **Response** (Format & Struktur)

---

## 📋 WAS ZU DOKUMENTIEREN

### Für jeden API-Call:

```markdown
## Endpoint: [Name]

**URL:** GET/POST /api/...
**Headers:**
- Authorization: Bearer ...
- Content-Type: application/json

**Request:**
```json
{
  "param": "value"
}
```

**Response:**
```json
{
  "data": [...]
}
```
```

---

## 🎯 WICHTIGSTE ENDPOINTS ZU FINDEN

1. **Login** - Wie wird authentifiziert?
2. **Fahrzeugliste** - Wie werden Fahrzeuge abgerufen?
3. **Fahrzeugdetails** - Wie werden Details geladen?
4. **Fahrzeug speichern** - Wie werden Änderungen gespeichert?

---

## 💡 TIPPS

- **Screenshots** von wichtigen Requests machen
- **HAR-Export:** Network-Tab → Rechtsklick → "Save as HAR"
- **Postman:** Requests als Collection speichern

---

**Detaillierte Anleitung:** Siehe `EAUTOSELLER_BROWSER_ANALYSE_ANLEITUNG.md`

