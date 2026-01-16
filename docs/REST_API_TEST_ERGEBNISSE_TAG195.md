# Hyundai REST API Test-Ergebnisse - TAG 195

**Datum:** 2026-01-16  
**Ziel:** Prüfen ob REST API verfügbar ist und ob Endpunkte für Arbeitsoperationsnummern existieren

---

## ✅ KONNEKTIVITÄT

**Status:** ✅ **Server sind erreichbar!**

| Server | URL | Status | Ergebnis |
|--------|-----|--------|----------|
| **Auth-Server** | `https://hmd.wa.hyundai-europe.com:8443` | ✅ 200 | Erreichbar |
| **API-Server** | `https://hmd.wa.hyundai-europe.com:9092` | ✅ 200 | Erreichbar |

**Fazit:** Beide Server antworten korrekt!

---

## ⚠️ AUTHENTIFIZIERUNG

**Status:** ⏳ **Credentials benötigt**

**Erforderlich:**
- Username/Email für Hyundai Workshop Automation
- Passwort

**Hinweis:** 
- Credentials müssen in `config/credentials.json` unter `hyundai` eingetragen werden
- Format:
```json
{
  "hyundai": {
    "username": "dein-username",
    "password": "dein-passwort"
  }
}
```

**Bekannte Credentials (aus Dokumentation):**
- GWMS Portal: `david.moser@auto-greiner.de` / `LuisaSandra092025!!`
- **Frage:** Sind das die gleichen Credentials für Workshop Automation?

---

## 📋 ZU TESTENDE ENDPUNKTE

### Bekannte Endpunkte (aus Dokumentation TAG 175):

1. **Authentifizierung:**
   - `POST /api/TokenAuth/AuthenticateForApp`
   - Request: `{"userNameOrEmailAddress": "...", "password": "...", "rememberClient": true}`
   - Response: `{"result": {"accessToken": "...", "expireInSeconds": 86400}}`

2. **Repair Orders:**
   - `POST /api/services/app/repairorder/SearchRepairOrders`
   - Request: `{"SearchCriteria": {"SearchDateFromLocal": "...", "SearchDateToLocal": "..."}}`
   - Response: Liste von Repair Orders mit `dmsroNo` (Locosoft Auftragsnummer)

3. **Session:**
   - `POST /api/services/app/session/GetCurrentLoginInformations`

4. **System Codes:**
   - `POST /api/services/app/SystemCode/GetSystemCodesForApp`

### Vermutete Endpunkte (für TT-Zeit-Prüfung):

5. **GetOperationCodes** (Vermutung):
   - `POST /api/services/app/part/GetOperationCodes`
   - Request: `{"partNumber": "...", "vin": "..."}`
   - **Zweck:** Prüft ob Arbeitsoperationsnummern für ein Teil vorhanden sind

6. **CheckStandardTime** (Vermutung):
   - `POST /api/services/app/part/CheckStandardTime`
   - Request: `{"partNumber": "...", "vin": "..."}`
   - **Zweck:** Prüft ob Standardarbeitszeit vorhanden ist

7. **GetRepairOrderDetail** (Vermutung):
   - `POST /api/services/app/repairorder/GetRepairOrderDetail`
   - Request: `{"dmsroNo": "..."}`
   - **Zweck:** Detaillierte Auftragsinformationen inkl. Arbeitsoperationsnummern

---

## 🔧 TEST-SCRIPT

**Datei:** `scripts/test_hyundai_rest_api.py`

**Funktionen:**
1. ✅ Konnektivitätstest (funktioniert)
2. ⏳ Authentifizierungstest (benötigt Credentials)
3. ⏳ API-Endpunkt-Test (benötigt Token)

**Ausführung:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python3 scripts/test_hyundai_rest_api.py
```

---

## 📊 STATUS

| Test | Status | Ergebnis |
|------|--------|----------|
| **Konnektivität** | ✅ | Beide Server erreichbar |
| **Authentifizierung** | ⏳ | Credentials benötigt |
| **API-Endpunkte** | ⏳ | Wartet auf Authentifizierung |
| **GetOperationCodes** | ⏳ | Muss getestet werden |
| **CheckStandardTime** | ⏳ | Muss getestet werden |

---

## 🎯 NÄCHSTE SCHRITTE

### 1. Credentials beschaffen ⏳

**Optionen:**
- Prüfen ob GWMS-Credentials auch für Workshop Automation funktionieren
- Neue Credentials für Workshop Automation anfordern
- In `config/credentials.json` eintragen

### 2. Authentifizierung testen ⏳

**Nach Credentials:**
- Test-Script erneut ausführen
- Prüfen ob Token erhalten wird
- Prüfen ob Token gültig ist

### 3. API-Endpunkte testen ⏳

**Nach erfolgreicher Authentifizierung:**
- Bekannte Endpunkte testen (SearchRepairOrders, etc.)
- Vermutete Endpunkte testen (GetOperationCodes, etc.)
- Prüfen ob Arbeitsoperationsnummern-Endpunkt existiert

### 4. Integration ⏳

**Falls Endpunkt verfügbar:**
- API-Client implementieren
- Integration in TT-Zeit-Analyse
- Automatische Prüfung implementieren

**Falls Endpunkt nicht verfügbar:**
- Manuelle Prüfung als Fallback
- Bestätigungs-Button im Frontend

---

## 💡 ERWARTETE ERGEBNISSE

### Szenario A: GetOperationCodes verfügbar ✅

**Vorteile:**
- ✅ Vollautomatische Prüfung
- ✅ Kein manueller Schritt nötig
- ✅ Rechtssicher (direkt aus API)

**Implementierung:**
```python
def check_arbeitsoperationsnummer_via_rest_api(part_number: str, vin: str) -> bool:
    token = authenticate_hyundai_portal()
    response = requests.post(
        'https://hmd.wa.hyundai-europe.com:9092/api/services/app/part/GetOperationCodes',
        headers={'Authorization': f'Bearer {token}'},
        json={'partNumber': part_number, 'vin': vin}
    )
    operation_codes = response.json().get('result', {}).get('operationCodes', [])
    return len(operation_codes) == 0  # Keine Codes = TT-Zeit möglich
```

### Szenario B: Endpunkt nicht verfügbar ⚠️

**Lösung:**
- Manuelle Prüfung durch Serviceberater
- Bestätigungs-Button im Frontend
- Dokumentation der Prüfung

---

## 📝 ZUSAMMENFASSUNG

**Ergebnis:**
- ✅ Server sind erreichbar
- ⏳ Authentifizierung benötigt Credentials
- ⏳ API-Endpunkte müssen getestet werden

**Empfehlung:**
1. Credentials beschaffen
2. Authentifizierung testen
3. API-Endpunkte testen
4. Falls verfügbar: Integration implementieren
5. Falls nicht verfügbar: Manuelle Prüfung als Fallback

---

## ⚠️ FIREWALL-PROBLEM

**Update:** Credentials wurden getestet, aber Web-Firewall blockiert Requests!

**Problem:**
- Firewall blockiert alle API-Requests
- Fehlermeldung: "The request / response that are contrary to the Web firewall security policies have been blocked"
- Client IP: 85.209.26.80 (Server-IP)

**Mögliche Lösungen:**
1. Firewall-Whitelist: Server-IP muss in Whitelist
2. VPN-Verbindung: Über VPN zugreifen
3. Locosoft SOAP: Als Alternative prüfen
4. Manuelle Prüfung: Als Fallback implementieren

**Siehe:** `docs/REST_API_FIREWALL_PROBLEM_TAG195.md`

---

**Erstellt:** TAG 195  
**Status:** Konnektivität OK, Authentifizierung getestet, aber Firewall blockiert Requests
