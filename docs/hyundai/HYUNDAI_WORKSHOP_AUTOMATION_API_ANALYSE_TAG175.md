# Hyundai Workshop Automation API - Analyse

**Erstellt:** 2026-01-09 (TAG 175)  
**Basis:** HAR-Datei von Hyundai Workshop Automation

---

## 🎯 ERKENNTNIS

**Hyundai Workshop Automation** verwendet eine **REST API** (nicht SOAP direkt):
- **Base URL:** `https://hmd.wa.hyundai-europe.com`
- **Ports:** 8443 (Auth), 9092 (API)
- **Format:** JSON (REST API)

**Wichtig:** Diese API ist **separat** von Locosoft SOAP, aber Locosoft kann möglicherweise als Gateway fungieren!

---

## 🔍 API-STRUKTUR

### Base URLs
- **Auth:** `https://hmd.wa.hyundai-europe.com:8443`
- **API:** `https://hmd.wa.hyundai-europe.com:9092`
- **Parts Catalog:** `https://asoneq.hyundai-corp.io/quotation/partscatalogservice`

### Authentifizierung
```
POST /api/TokenAuth/AuthenticateForApp
Body: {
  "userNameOrEmailAddress": "...",
  "password": "...",
  "rememberClient": true
}
Response: {
  "result": {
    "accessToken": "...",
    "encryptedAccessToken": "...",
    "expireInSeconds": 86400
  }
}
```

### Headers
- `Authorization: Bearer {accessToken}`
- `Abp.Localization.CultureName: de-DE`

---

## 📋 GEFUNDENE API-ENDPUNKTE

### 1. Authentifizierung
- `POST /api/TokenAuth/AuthenticateForApp` - Login
- `POST /api/services/app/session/GetCurrentLoginInformations` - Session-Info

### 2. Repair Orders
- `POST /api/services/app/repairorder/SearchRepairOrders` - Suche Aufträge
  - Request: `{"SearchCriteria": {"SearchDateFromLocal": "...", "SearchDateToLocal": "..."}}`
  - Response: Liste von Repair Orders mit `dmsroNo` (Locosoft Auftragsnummer!)

### 3. Parts Catalog Service
- `POST /quotation/partscatalogservice/selectparts/selectvehicleinfobyvin` - Fahrzeuginfo per VIN
- `POST /quotation/partscatalogservice/selectparts/selectlargegroupinfobyvin` - Teilegruppen

### 4. Weitere Endpunkte
- `POST /api/services/app/SystemCode/GetSystemCodesForApp` - System-Codes
- `POST /api/services/app/tenantSettings/GetAllSettingsForApp` - Tenant-Settings
- `POST /api/services/app/user/GetUsersForApp` - Benutzer
- `POST /api/services/app/scheduleItem/SearchScheduleItems` - Termine
- `POST /api/services/app/scheduleItem/SearchScheduleTargets` - Termin-Ziele

---

## 🔧 REPAIR ORDER STRUKTUR

### Gefundene Felder
```json
{
  "dmsroNo": "4824.057",  // ← Locosoft Auftragsnummer!
  "roDateTimeLocal": "2026-01-08 10:57:17",
  "roStatusEnum": "PreRO",
  "requestItems": [],  // ← Hier sollten Teile sein!
  "priceSummary": {
    "partPrice": 0.0,
    "partPriceWithTax": 0.0
  },
  "vehicle": {
    "vin": "TMAJD81B7SJ575110"
  }
}
```

### Wichtig
- `dmsroNo` = Locosoft Auftragsnummer (z.B. "4824.057")
- `requestItems` = Array (aktuell leer in HAR, aber hier sollten Teile sein!)

---

## 🎯 FÜR TEILEBEZUG BENÖTIGT

### Zu prüfen:
1. **GetRepairOrderDetail-Endpunkt?**
   - Gibt es `GET /api/services/app/repairorder/GetRepairOrderDetail/{id}`?
   - Oder `POST /api/services/app/repairorder/GetRepairOrderDetail`?

2. **RequestItems-Struktur:**
   - Wie sehen `requestItems` aus, wenn sie gefüllt sind?
   - Enthalten sie Teile-Informationen?
   - Enthalten sie Mobis Bestellnummern?

3. **Locosoft-Integration:**
   - Wie kommuniziert Hyundai Workshop Automation mit Locosoft?
   - Gibt es einen SOAP-Endpunkt in Locosoft für Hyundai Automation?
   - Oder ist es eine direkte REST-API-Verbindung?

---

## 📝 NÄCHSTE SCHRITTE

### 1. Locosoft SOAP prüfen
- [ ] Gibt es einen SOAP-Endpunkt für Hyundai Automation?
- [ ] Kann Locosoft als Gateway zu Hyundai Workshop Automation fungieren?
- [ ] Welche SOAP-Methoden sind für Hyundai verfügbar?

### 2. Hyundai Workshop Automation API
- [ ] GetRepairOrderDetail-Endpunkt finden
- [ ] RequestItems mit Teile-Daten analysieren
- [ ] API-Client erstellen

### 3. Integration
- [ ] Über Locosoft SOAP (wenn möglich)
- [ ] Oder direkt über Hyundai Workshop Automation REST API

---

## 🔗 RELEVANTE DATEIEN

- HAR-Datei: `/mnt/greiner-portal-sync/Hyundai_Garantie/hmd.wa.hyundai-europe.com.har`
- Response: `/tmp/repairorder_response.json`

---

**Status:** ⏳ Wartet auf weitere Analyse - GetRepairOrderDetail-Endpunkt finden
