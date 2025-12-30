# eAutoseller API Analyse

**Datum:** 2025-12-29  
**URL:** https://greiner.eautoseller.de/  
**Credentials:** fGreiner / fGreiner12

---

## 🔍 ERGEBNISSE DER WEB-RECHERCHE

### Bekannte eAutoseller APIs:

1. **flashXML API** (XML-basiert)
   - **Zweck:** Direkte Datenabfragen im XML-Format
   - **Features:** 
     - Fahrzeugdaten in Echtzeit
     - Automatisches Klickmonitoring
   - **URL:** `/eaxml` oder `/flashxml`
   - **Auth:** Benötigt AuthCode
   - **Dokumentation:** https://www.eautoseller.de/hp/eaxml.asp

2. **Upload API** (CSV-Format)
   - **Zweck:** Upload von Fahrzeugdaten
   - **Format:** Erweitertes mobile.de CSV-Format
   - **URL:** `/api/upload` oder `/upload`
   - **Dokumentation:** https://www.eautoseller.de/hp/api.asp

---

## 🛠️ EXPLORATION-TOOL

**Script erstellt:** `scripts/explore_eautoseller_api.py`

### Verwendung:

```bash
# Auf Server ausführen
cd /opt/greiner-portal
source venv/bin/activate
python3 scripts/explore_eautoseller_api.py
```

### Was das Script macht:

1. **Login-Test** - Prüft ob Login möglich ist
2. **API-Endpoints erkunden** - Testet bekannte Endpoints
3. **flashXML API testen** - Testet verschiedene Parameter
4. **JavaScript-Analyse** - Sucht nach API-Calls im Frontend
5. **Authentifizierte Endpoints** - Testet mit Basic Auth

---

## 📋 MÖGLICHE API-ENDPOINTS (zu testen)

### XML/JSON APIs:
- `/eaxml` - flashXML API
- `/flashxml` - Alternative flashXML URL
- `/api/xml` - Generische XML API
- `/api/flashxml` - API-Variante

### REST APIs:
- `/api/v1/vehicles` - Fahrzeuge (REST)
- `/api/vehicles` - Fahrzeuge (REST)
- `/api/fahrzeuge` - Fahrzeuge (DE)
- `/api/data` - Generische Daten

### Upload:
- `/api/upload` - Upload API
- `/upload` - Alternative Upload URL

### SOAP (falls vorhanden):
- `/soap` - SOAP Endpoint
- `/api/soap` - API SOAP Variante

---

## 🔑 AUTHENTIFIZIERUNG

### AuthCode erforderlich

Für die flashXML API wird ein **AuthCode** benötigt, der von eAutoseller bereitgestellt wird.

**Anfrage:**
- Kontakt: ITKrebs GmbH & Co. KG (eAutoseller Support)
- Website: https://www.eautoseller.de
- Zweck: AuthCode für API-Zugriff anfordern

### Mögliche Auth-Methoden:

1. **AuthCode als Parameter:**
   ```
   /eaxml?authcode=XXXXX
   ```

2. **Basic Authentication:**
   ```
   Username: fGreiner
   Password: fGreiner12
   ```

3. **Session-basiert:**
   - Login über Web-Interface
   - Session-Cookie für API-Calls

---

## 🔍 MANUELLE ANALYSE (Browser)

### Entwicklertools nutzen:

1. **Login auf eAutoseller:**
   - https://greiner.eautoseller.de/
   - User: fGreiner
   - Pass: fGreiner12

2. **Browser-Entwicklertools öffnen:**
   - F12 drücken
   - Tab "Network" öffnen
   - Filter: "XHR" oder "Fetch"

3. **Aktionen durchführen:**
   - Fahrzeuge anzeigen
   - Fahrzeug bearbeiten
   - Daten abrufen

4. **API-Calls identifizieren:**
   - Alle Requests im Network-Tab prüfen
   - URLs notieren
   - Request/Response analysieren
   - Headers prüfen (Auth, Content-Type)

---

## 📝 BEISPIEL-REQUESTS (nach Analyse)

### flashXML API Beispiel:

```python
import requests

url = "https://greiner.eautoseller.de/eaxml"
params = {
    "authcode": "DEIN_AUTHCODE",
    "action": "vehicles",  # oder "list", "categories", etc.
    "format": "xml"  # oder "json"
}

response = requests.get(url, params=params)
print(response.text)
```

### REST API Beispiel (falls vorhanden):

```python
import requests
from requests.auth import HTTPBasicAuth

url = "https://greiner.eautoseller.de/api/vehicles"
auth = HTTPBasicAuth("fGreiner", "fGreiner12")

response = requests.get(url, auth=auth)
data = response.json()
print(data)
```

---

## 🎯 NÄCHSTE SCHRITTE

### 1. AuthCode anfordern
- Kontakt: eAutoseller Support
- Zweck: API-Zugriff für Integration

### 2. Exploration-Script ausführen
```bash
python3 scripts/explore_eautoseller_api.py
```

### 3. Browser-Analyse durchführen
- Entwicklertools öffnen
- API-Calls identifizieren
- Dokumentieren

### 4. API-Client erstellen
- Nach erfolgreicher Identifikation
- Python-Client für DRIVE Portal
- Integration in bestehende Struktur

---

## 📚 LINKS & DOKUMENTATION

- **eAutoseller Homepage:** https://www.eautoseller.de
- **flashXML Dokumentation:** https://www.eautoseller.de/hp/eaxml.asp
- **Upload API Dokumentation:** https://www.eautoseller.de/hp/api.asp
- **Support:** Über eAutoseller Website kontaktieren

---

## ⚠️ HINWEISE

1. **SSL-Zertifikat:** Möglicherweise Self-Signed, `verify=False` bei Bedarf
2. **Rate Limiting:** Unbekannt - vorsichtig testen
3. **API-Version:** VAP Version 3 - möglicherweise neue API-Struktur
4. **Dokumentation:** Offizielle API-Dokumentation anfordern

---

**Status:** 🔄 Exploration läuft  
**Nächster Schritt:** Script ausführen & Browser-Analyse

