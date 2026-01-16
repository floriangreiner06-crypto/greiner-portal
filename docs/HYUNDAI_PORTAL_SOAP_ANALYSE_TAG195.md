# Hyundai Portal SOAP-Integration: Analyse für TT-Zeit-Prüfung - TAG 195

**Erstellt:** 2026-01-16  
**Portal:** https://hmd.wa.hyundai-europe.com:9443/account/login  
**Erkenntnis:** Portal nutzt Locosoft SOAP - könnte für TT-Zeit-Prüfung genutzt werden!

---

## 🎯 ERKENNTNIS

**Hyundai Auftrags- und Service-Portal:**
- URL: `https://hmd.wa.hyundai-europe.com:9443/account/login`
- **Nutzt Locosoft SOAP** als Backend
- **Könnte GSW Portal-Daten** über Locosoft SOAP bereitstellen

**Mögliche Nutzung:**
- Über Locosoft SOAP auf Hyundai Portal-Daten zugreifen
- Prüfen ob Arbeitsoperationsnummern vorhanden sind
- Automatische TT-Zeit-Prüfung möglich?

---

## 🔍 ANALYSE: LOCOSOFT SOAP FÜR HYUNDAI

### Verfügbare SOAP-Methoden (aktuell)

**Aus `tools/locosoft_soap_client.py`:**

1. **READ-Operationen:**
   - `readWorkOrderDetails(orderNumber)` - Auftragsdetails
   - `readPartInformation(partNumber)` - Teile-Informationen
   - `readAppointment(number)` - Termin-Details
   - `readCustomer(number)` - Kundendaten
   - `readVehicle(number)` - Fahrzeugdaten

2. **LIST-Operationen:**
   - `listOpenWorkOrders()` - Offene Aufträge
   - `listAppointmentsByDate()` - Termine
   - `listCustomers()` - Kunden-Suche
   - `listVehicles()` - Fahrzeug-Suche

3. **WRITE-Operationen:**
   - `writeWorkOrderDetails()` - Auftrag schreiben
   - `writeAppointment()` - Termin schreiben
   - `writeWorkOrderTimes()` - Zeiten buchen

### Fehlende Methoden (für TT-Zeit-Prüfung)

**Was wir brauchen:**
- ❓ `getHyundaiOperationCodes(partNumber, vin)` - Arbeitsoperationsnummern für Teil
- ❓ `checkStandardTime(partNumber, vin)` - Prüft ob Standardarbeitszeit vorhanden
- ❓ `getGSWPortalData(partNumber)` - GSW Portal-Daten für Teil

**Frage:** Gibt es diese Methoden im Locosoft SOAP?

---

## 🛠️ MÖGLICHE LÖSUNGSANSÄTZE

### Option 1: Locosoft SOAP erweitern (Falls möglich)

**Wenn Locosoft SOAP Hyundai-spezifische Methoden hat:**

```python
def check_arbeitsoperationsnummer_via_soap(part_number: str, vin: str) -> bool:
    """
    Prüft über Locosoft SOAP, ob für ein Teil eine Arbeitsoperationsnummer vorhanden ist.
    
    Returns:
        True wenn KEINE Arbeitsoperationsnummer vorhanden (TT-Zeit möglich)
        False wenn Arbeitsoperationsnummer vorhanden (TT-Zeit NICHT möglich)
    """
    client = get_soap_client()
    
    # Prüfe ob Methode existiert
    if hasattr(client.service, 'getHyundaiOperationCodes'):
        result = client.service.getHyundaiOperationCodes(
            partNumber=part_number,
            vin=vin
        )
        # Wenn keine Operation Codes gefunden → TT-Zeit möglich
        return len(result) == 0
    
    # Fallback: Methode nicht verfügbar
    return None  # Unbekannt
```

**Status:** ⏳ **Muss geprüft werden** - Gibt es diese SOAP-Methode?

---

### Option 2: Hyundai Workshop Automation REST API

**Das Portal nutzt auch REST API:**

**Base URL:** `https://hmd.wa.hyundai-europe.com:9092`

**Mögliche Endpunkte:**
- `POST /api/services/app/repairorder/GetRepairOrderDetail` - Auftragsdetails
- `POST /api/services/app/part/GetOperationCodes` - Arbeitsoperationsnummern? (zu prüfen)
- `POST /api/services/app/part/CheckStandardTime` - Standardarbeitszeit prüfen? (zu prüfen)

**Implementierung:**
```python
def check_arbeitsoperationsnummer_via_rest_api(part_number: str, vin: str) -> bool:
    """
    Prüft über Hyundai Workshop Automation REST API.
    """
    # 1. Authentifizierung
    token = authenticate_hyundai_portal()
    
    # 2. API-Call
    response = requests.post(
        'https://hmd.wa.hyundai-europe.com:9092/api/services/app/part/GetOperationCodes',
        headers={'Authorization': f'Bearer {token}'},
        json={'partNumber': part_number, 'vin': vin}
    )
    
    # 3. Prüfe Ergebnis
    if response.status_code == 200:
        data = response.json()
        operation_codes = data.get('result', {}).get('operationCodes', [])
        return len(operation_codes) == 0  # Keine Codes = TT-Zeit möglich
    
    return None
```

**Status:** ⏳ **Muss geprüft werden** - Gibt es diese REST-Endpunkte?

---

### Option 3: Kombination (Empfohlen)

**Workflow:**
1. **Technische Prüfung** (automatisch):
   - Garantieauftrag?
   - Stempelzeiten vorhanden?
   - Schadhaften Teil identifiziert?

2. **SOAP/REST-API-Prüfung** (automatisch, falls verfügbar):
   - Prüfe über Locosoft SOAP oder Hyundai REST API
   - Gibt es Arbeitsoperationsnummern für das Teil?
   - Wenn NEIN → TT-Zeit möglich
   - Wenn JA → TT-Zeit NICHT möglich

3. **Manuelle Prüfung** (Fallback):
   - Wenn API nicht verfügbar oder unklar
   - Serviceberater prüft im Portal
   - Serviceberater bestätigt

4. **KI-Analyse** (Unterstützung):
   - Begründung für TT-Zeit
   - Empfehlung basierend auf Diagnose-Komplexität

---

## 🔧 IMPLEMENTIERUNGS-STRATEGIE

### Schritt 1: SOAP-Methoden prüfen

**Test-Script erstellen:**
```python
# scripts/test_hyundai_soap_methods.py
from tools.locosoft_soap_client import get_soap_client

client = get_soap_client()

# Prüfe verfügbare Methoden
print("Verfügbare SOAP-Methoden:")
for method_name in dir(client.service):
    if not method_name.startswith('_'):
        print(f"  - {method_name}")

# Test mit Teilenummer
part_number = "98850J7500"  # Beispiel
vin = "KMHKR81CPNU005366"   # Beispiel

# Prüfe ob Hyundai-spezifische Methoden existieren
hyundai_methods = [
    'getHyundaiOperationCodes',
    'checkHyundaiStandardTime',
    'getGSWPortalData',
    'listHyundaiOperationCodes'
]

for method_name in hyundai_methods:
    if hasattr(client.service, method_name):
        print(f"✅ {method_name} verfügbar!")
        # Test-Call
        try:
            result = getattr(client.service, method_name)(partNumber=part_number)
            print(f"   Ergebnis: {result}")
        except Exception as e:
            print(f"   Fehler: {e}")
    else:
        print(f"❌ {method_name} NICHT verfügbar")
```

### Schritt 2: REST API prüfen (falls SOAP nicht verfügbar)

**Test-Script für REST API:**
```python
# scripts/test_hyundai_rest_api.py
import requests

# Authentifizierung
auth_url = 'https://hmd.wa.hyundai-europe.com:8443/api/TokenAuth/AuthenticateForApp'
response = requests.post(auth_url, json={
    'userNameOrEmailAddress': '...',
    'password': '...',
    'rememberClient': True
})

token = response.json()['result']['accessToken']

# Test: Prüfe ob Endpunkt für Arbeitsoperationsnummern existiert
test_endpoints = [
    '/api/services/app/part/GetOperationCodes',
    '/api/services/app/part/CheckStandardTime',
    '/api/services/app/repairorder/GetOperationCodesForPart'
]

for endpoint in test_endpoints:
    url = f'https://hmd.wa.hyundai-europe.com:9092{endpoint}'
    response = requests.post(
        url,
        headers={'Authorization': f'Bearer {token}'},
        json={'partNumber': '98850J7500', 'vin': 'KMHKR81CPNU005366'}
    )
    print(f"{endpoint}: {response.status_code}")
    if response.status_code == 200:
        print(f"  ✅ Verfügbar: {response.json()}")
```

### Schritt 3: Integration in TT-Zeit-Analyse

**Erweiterte API-Funktion:**
```python
@ai_api.route('/analysiere/tt-zeit/<int:auftrag_id>', methods=['POST'])
@login_required
def analysiere_tt_zeit(auftrag_id: int):
    """
    Analysiert ob TT-Zeit möglich ist.
    
    Prüft:
    1. Technische Voraussetzungen
    2. Arbeitsoperationsnummer (via SOAP/REST, falls verfügbar)
    3. KI-Analyse (Begründung, Empfehlung)
    """
    # 1. Technische Prüfung
    is_garantie = check_garantieauftrag(auftrag_id)
    schadhaftes_teil = hole_schadhaftes_teil(auftrag_id)
    stempelzeiten = get_stempelzeiten(auftrag_id)
    
    # 2. Prüfe Arbeitsoperationsnummer (falls verfügbar)
    arbeitsoperationsnummer_vorhanden = None
    if schadhaftes_teil:
        # Versuche über SOAP
        arbeitsoperationsnummer_vorhanden = check_via_soap(
            schadhaftes_teil['teilenummer'],
            get_vin(auftrag_id)
        )
        
        # Falls SOAP nicht verfügbar, versuche REST API
        if arbeitsoperationsnummer_vorhanden is None:
            arbeitsoperationsnummer_vorhanden = check_via_rest_api(
                schadhaftes_teil['teilenummer'],
                get_vin(auftrag_id)
            )
    
    # 3. Entscheidung
    if arbeitsoperationsnummer_vorhanden is True:
        # Arbeitsoperationsnummer vorhanden → TT-Zeit NICHT möglich
        return jsonify({
            'success': True,
            'tt_zeit_moeglich': False,
            'grund': 'Arbeitsoperationsnummer mit Vorgabezeit vorhanden (GSW Portal)',
            'schadhaftes_teil': schadhaftes_teil
        })
    elif arbeitsoperationsnummer_vorhanden is False:
        # KEINE Arbeitsoperationsnummer → TT-Zeit möglich
        # Weiter mit KI-Analyse...
        pass
    else:
        # Unbekannt → Manuelle Prüfung erforderlich
        return jsonify({
            'success': True,
            'tt_zeit_moeglich': None,  # Unbekannt
            'warnung': '⚠️ Bitte im GSW Portal prüfen!',
            'manuelle_pruefung_erforderlich': True,
            'schadhaftes_teil': schadhaftes_teil
        })
```

---

## 📋 NÄCHSTE SCHRITTE

### 1. SOAP-Methoden prüfen ⏳

**Test-Script erstellen:**
- [ ] Verfügbare SOAP-Methoden auflisten
- [ ] Prüfen ob Hyundai-spezifische Methoden existieren
- [ ] Test mit echten Teilenummern

### 2. REST API prüfen ⏳

**Falls SOAP nicht verfügbar:**
- [ ] Authentifizierung testen
- [ ] Verfügbare Endpunkte prüfen
- [ ] Prüfen ob Arbeitsoperationsnummern-Endpunkt existiert

### 3. Integration ⏳

**Falls API verfügbar:**
- [ ] API-Client implementieren
- [ ] Integration in TT-Zeit-Analyse
- [ ] Fallback auf manuelle Prüfung

**Falls API nicht verfügbar:**
- [ ] Manuelle Prüfung mit Bestätigungs-Button
- [ ] Dokumentation der Prüfung

---

## 💡 ERWARTETE ERGEBNISSE

### Szenario A: SOAP/REST API verfügbar ✅

**Vorteile:**
- ✅ Vollautomatische Prüfung
- ✅ Kein manueller Schritt nötig
- ✅ Rechtssicher (direkt aus GSW Portal)

**Implementierung:**
- API-Client für SOAP/REST
- Automatische Prüfung in TT-Zeit-Analyse
- KI-Analyse als zusätzliche Unterstützung

### Szenario B: API nicht verfügbar ⚠️

**Lösung:**
- Manuelle Prüfung durch Serviceberater
- Bestätigungs-Button im Frontend
- Dokumentation der Prüfung

**Implementierung:**
- Warnung: "Bitte im GSW Portal prüfen!"
- Button: "✅ GSW Portal geprüft - Keine Arbeitsoperationsnummer"
- Speicherung der Bestätigung

---

## 🔗 RELEVANTE DATEIEN

**Code:**
- `tools/locosoft_soap_client.py` - SOAP-Client
- `api/garantie_soap_api.py` - Garantie SOAP API
- `api/ai_api.py` - AI API (TT-Zeit-Analyse)

**Dokumentation:**
- `docs/hyundai/HYUNDAI_WORKSHOP_AUTOMATION_API_ANALYSE_TAG175.md`
- `docs/hyundai/MOBIS_TEILEBEZUG_LOCOSOFT_SOAP_TAG175.md`
- `docs/TT_ZEIT_VORAUSSETZUNGEN_KORREKTUR_TAG195.md`

---

## ✅ EMPFEHLUNG

**Kombinierter Ansatz:**

1. **Zuerst prüfen:** Gibt es SOAP/REST-Methoden für Arbeitsoperationsnummern?
   - Test-Script erstellen
   - Verfügbare Methoden auflisten
   - Test mit echten Daten

2. **Falls verfügbar:** Automatische Prüfung implementieren
   - API-Client erstellen
   - Integration in TT-Zeit-Analyse
   - Vollautomatisch

3. **Falls nicht verfügbar:** Manuelle Prüfung
   - Warnung im Frontend
   - Bestätigungs-Button
   - Dokumentation

**Nächster Schritt:** Test-Script erstellen und SOAP-Methoden prüfen!

---

**Erstellt:** TAG 195  
**Status:** Analyse erstellt, bereit für Tests
