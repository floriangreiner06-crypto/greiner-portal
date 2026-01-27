# e-autoseller Swagger API - Zusammenfassung

**Datum:** 2026-01-21  
**API-Version:** 2.0.37  
**Status:** ✅ Analyse abgeschlossen

---

## 🎯 Wichtigste Erkenntnisse

### API-Informationen
- **Title:** eAutoseller DMS API
- **Version:** 2.0.37
- **Base URL:** `https://api.eautoseller.de`
- **Format:** OpenAPI 3.0.2
- **Support:** support@eautoseller.de

### Authentifizierung
- **Methode:** ApiKey + ClientSecret (Header)
- **Erforderlich:** Beide müssen im Header mitgesendet werden
- **Hinweis:** Credentials müssen bei eAutoseller Support angefragt werden

### Endpoints-Übersicht
- **Total:** 33 Endpoints
- **Methoden:** GET (18), POST (10), PATCH (1), DELETE (4)
- **Kategorien:** Vehicles, Vehicle Images, Vehicle Files, Vehicle Statistics, Vehicle prices, Publications, etc.

---

## 🔗 Wichtigste Endpoints für unsere Integration

### 1. Fahrzeugliste (`GET /dms/vehicles`)
**Zweck:** Liste aller Fahrzeuge abrufen

**Parameter:**
- `offerReference` (optional) - Angebotsreferenz
- `vin` (optional) - VIN (17 Zeichen)
- `mobileAdId` (optional) - Mobile.de Ad-ID
- `as24AdId` (optional) - AutoScout24 Ad-ID
- `changedSince` (optional) - Nur geänderte seit Datum
- `status` (optional) - Status-Filter

**Response:** JSON mit Fahrzeugliste

**Vorteil gegenüber HTML-Parsing:**
- ✅ Strukturierte JSON-Daten
- ✅ Filter direkt in API
- ✅ Kein HTML-Parsing nötig
- ✅ Bessere Performance

### 2. Einzelnes Fahrzeug (`GET /dms/vehicle/{id}`)
**Zweck:** Details eines einzelnen Fahrzeugs

**Parameter:**
- `id` (path, required) - Fahrzeug-ID

**Response:** JSON mit Fahrzeugdetails

### 3. Fahrzeugübersicht (`GET /dms/vehicle/{id}/overview`)
**Zweck:** Übersicht eines Fahrzeugs

**Parameter:**
- `id` (path, required) - Fahrzeug-ID

**Response:** JSON mit Fahrzeugübersicht

### 4. Fahrzeugdetails (`GET /dms/vehicle/{id}/details`)
**Zweck:** Detaillierte Informationen

**Parameter:**
- `id` (path, required) - Fahrzeug-ID
- `withAdditionalInformation` (optional) - Zusätzliche Infos
- `resolveEquipments` (optional) - Ausstattung auflösen

**Response:** JSON mit vollständigen Fahrzeugdetails

### 5. Preise (`GET /dms/vehicles/prices`)
**Zweck:** Alle aktiven Fahrzeuge mit Preisen

**Parameter:**
- `from` (optional) - Nur Preise seit Datum

**Response:** JSON mit Fahrzeugen und Preisen

### 6. Statistik (`GET /dms/vehicle/{id}/statistics`)
**Zweck:** Fahrzeug-Statistiken (Beta)

**Parameter:**
- `id` (path, required) - Fahrzeug-ID

**Response:** JSON mit Statistiken

---

## 🔐 Authentifizierung

### Header-Parameter
```
ApiKey: <API_KEY>
ClientSecret: <CLIENT_SECRET>
```

### Beispiel (Python requests)
```python
headers = {
    'ApiKey': 'your-api-key',
    'ClientSecret': 'your-client-secret',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

response = requests.get(
    'https://api.eautoseller.de/dms/vehicles',
    headers=headers
)
```

### Credentials anfordern
- **E-Mail:** support@eautoseller.de
- **Zweck:** API-Zugriff für Integration
- **Erforderlich:** ApiKey + ClientSecret

---

## 📊 Vergleich: Aktuell vs. Swagger API

| Feature | Aktuell (HTML) | Swagger API |
|---------|----------------|-------------|
| **Format** | HTML | JSON |
| **Parsing** | BeautifulSoup | Native JSON |
| **Performance** | Langsam (~600KB HTML) | Schnell (nur benötigte Daten) |
| **Filter** | HTML-Parameter | API-Parameter (strukturiert) |
| **Datenqualität** | Teilweise (Parsing-Fehler) | Vollständig (API-Vertrag) |
| **Wartbarkeit** | Fragil (HTML-Änderungen) | Robust (API-Vertrag) |
| **Authentifizierung** | Session (Cookie) | ApiKey + ClientSecret |
| **Base URL** | https://greiner.eautoseller.de/ | https://api.eautoseller.de |

---

## 🎯 Integrations-Plan

### Phase 1: Authentifizierung ⭐⭐⭐
1. **Credentials anfordern**
   - E-Mail an support@eautoseller.de
   - ApiKey + ClientSecret anfordern
   - In `config/credentials.json` speichern

2. **Authentifizierung implementieren**
   - Header-basierte Auth im Client
   - Credentials aus Config laden
   - Fallback zu Environment Variables

### Phase 2: Basis-Endpoints ⭐⭐
1. **Fahrzeugliste (`GET /dms/vehicles`)**
   - Ersetzt HTML-Parsing von `kfzuebersicht.asp`
   - Filter-Parameter implementieren
   - JSON-Response parsen

2. **Fahrzeugdetails (`GET /dms/vehicle/{id}/details`)**
   - Ersetzt HTML-Parsing von Detail-Seiten
   - Hereinnahme-Datum direkt aus API

3. **Preise (`GET /dms/vehicles/prices`)**
   - Für Dashboard-KPIs
   - Aktuelle Preise mit Timestamps

### Phase 3: Erweiterte Features ⭐
1. **Statistiken (`GET /dms/vehicle/{id}/statistics`)**
   - Für Dashboard-KPIs
   - Standzeit-Statistiken

2. **Bilder (`GET /dms/vehicle/{id}/images`)**
   - Fahrzeugbilder abrufen
   - Für Frontend-Anzeige

3. **Dateien (`GET /dms/vehicle/{id}/files`)**
   - Anhänge abrufen
   - Für Dokumenten-Management

### Phase 4: Migration ⭐
1. **Schrittweise Migration**
   - Swagger-API als Standard
   - HTML-Parsing als Fallback
   - Feature-Flag für API

2. **Tests**
   - Unit-Tests für neue Endpoints
   - Integration-Tests
   - Vergleich mit HTML-Parsing

3. **Dokumentation**
   - API-Dokumentation aktualisieren
   - Code-Beispiele
   - Migration-Guide

---

## 💻 Code-Beispiele

### Neuer API-Client (Beispiel)

```python
# lib/eautoseller_client.py

class EAutosellerClient:
    BASE_URL = "https://api.eautoseller.de"
    
    def __init__(self, api_key, client_secret):
        self.api_key = api_key
        self.client_secret = client_secret
        self.session = requests.Session()
        self.session.headers.update({
            'ApiKey': self.api_key,
            'ClientSecret': self.client_secret,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_vehicles(self, offer_reference=None, vin=None, 
                     changed_since=None, status=None):
        """Ruft Fahrzeugliste ab (Swagger API)"""
        params = {}
        if offer_reference:
            params['offerReference'] = offer_reference
        if vin:
            params['vin'] = vin
        if changed_since:
            params['changedSince'] = changed_since
        if status:
            params['status'] = status
        
        response = self.session.get(
            f"{self.BASE_URL}/dms/vehicles",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_vehicle_by_id(self, vehicle_id):
        """Ruft Fahrzeugdetails ab"""
        response = self.session.get(
            f"{self.BASE_URL}/dms/vehicle/{vehicle_id}/details",
            params={
                'withAdditionalInformation': True,
                'resolveEquipments': True
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_vehicle_prices(self, from_date=None):
        """Ruft Preise ab"""
        params = {}
        if from_date:
            params['from'] = from_date.isoformat()
        
        response = self.session.get(
            f"{self.BASE_URL}/dms/vehicles/prices",
            params=params
        )
        response.raise_for_status()
        return response.json()
```

---

## ⚠️ Wichtige Hinweise

### 1. Credentials erforderlich
- **ApiKey** und **ClientSecret** müssen bei eAutoseller Support angefragt werden
- Ohne Credentials funktioniert die API nicht
- Aktuell: HTML-Parsing als Fallback behalten

### 2. Migration-Strategie
- **Schrittweise:** Swagger-API parallel zu HTML implementieren
- **Fallback:** HTML-Parsing bei API-Fehlern
- **Feature-Flag:** Möglichkeit zum Umschalten

### 3. Rate Limiting
- API könnte Rate Limiting haben
- Vorsichtig testen
- Caching implementieren

### 4. Beta-Endpoints
- Einige Endpoints sind als "Beta" markiert
- Können sich ändern
- Vorsichtig verwenden

---

## 📚 Referenzen

- **Swagger-Dokumentation:** `scripts/tests/eAutoseller.json`
- **Analyse:** `docs/EAUTOSELLER_SWAGGER_ANALYSE.md`
- **Aktuelle Implementierung:** `lib/eautoseller_client.py`
- **Support:** support@eautoseller.de

---

## 🎯 Nächste Schritte

1. ✅ **Swagger-Dokumentation analysiert**
2. ⏳ **Credentials anfordern** (support@eautoseller.de)
3. ⏳ **API-Client erweitern** (neue Methoden hinzufügen)
4. ⏳ **Integration testen** (mit echten Credentials)
5. ⏳ **Migration durchführen** (schrittweise)

---

**Status:** ✅ Analyse abgeschlossen, ⏳ Warten auf API-Credentials  
**Letzte Aktualisierung:** 2026-01-21
