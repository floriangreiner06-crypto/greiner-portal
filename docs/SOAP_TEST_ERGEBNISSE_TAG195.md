# SOAP-Test Ergebnisse - TAG 195

**Datum:** 2026-01-16  
**Ziel:** Prüfen ob Locosoft SOAP für TT-Zeit-Prüfung nutzbar ist

---

## ✅ SOAP-VERBINDUNG

**Status:** ✅ **SOAP funktioniert!**

- ✅ SOAP-Client erfolgreich initialisiert
- ✅ Verbindung zu `10.80.80.7:8086` funktioniert
- ✅ WSDL erfolgreich geladen

---

## 📋 VERFÜGBARE SOAP-METHODEN

### READ-Operationen:
- ✅ `readWorkOrderDetails(orderNumber)` - Auftragsdetails
- ✅ `readPartInformation(...)` - Teile-Informationen (andere Signatur!)
- ✅ `readLaborInformation(...)` - Arbeits-Informationen
- ✅ `readLaborAndPartInformation(...)` - Arbeits- und Teile-Informationen
- ✅ `readAppointment(number)` - Termin-Details
- ✅ `readCustomer(number)` - Kundendaten
- ✅ `readVehicle(number)` - Fahrzeugdaten

### LIST-Operationen:
- ✅ `listOpenWorkOrders()` - Offene Aufträge
- ✅ `listAppointmentsByDate()` - Termine
- ✅ `listCustomers()` - Kunden-Suche
- ✅ `listVehicles()` - Fahrzeug-Suche

### WRITE-Operationen:
- ✅ `writeWorkOrderDetails()` - Auftrag schreiben
- ✅ `writeAppointment()` - Termin schreiben
- ✅ `writeWorkOrderTimes()` - Zeiten buchen

---

## ❌ FEHLENDE METHODEN

**Hyundai-spezifische Methoden NICHT verfügbar:**
- ❌ `getHyundaiOperationCodes` - NICHT verfügbar
- ❌ `checkHyundaiStandardTime` - NICHT verfügbar
- ❌ `getGSWPortalData` - NICHT verfügbar
- ❌ `listHyundaiOperationCodes` - NICHT verfügbar
- ❌ `getOperationCodesForPart` - NICHT verfügbar
- ❌ `checkStandardTime` - NICHT verfügbar
- ❌ `getPartOperationCodes` - NICHT verfügbar

**Fazit:** Locosoft SOAP hat **keine direkten Methoden** für GSW Portal-Daten!

---

## 🔍 ANALYSE: readWorkOrderDetails

**Getestet mit:** Auftrag 202665 (Hyundai Garantie)

**Ergebnis:**
```json
{
  "number": 202665,
  "date": "2023-03-13T14:24:00",
  "status": "INVOICED_EMPTY",
  "line": [],  // ← Leer! Keine Positionen
  "customer": null,
  "vehicle": null,
  ...
}
```

**Erkenntnis:**
- ✅ `readWorkOrderDetails` funktioniert
- ❌ Enthält **KEINE** detaillierten Positionen (`line` ist leer)
- ❌ Enthält **KEINE** Arbeitsoperationsnummern
- ❌ Enthält **KEINE** GSW Portal-Daten

---

## 🔍 ANALYSE: readLaborInformation / readLaborAndPartInformation

**Signatur:** `(*args, **kwargs)` - Generisch, Parameter unbekannt

**Status:** ⏳ **Muss getestet werden** - Parameter müssen ermittelt werden

**Mögliche Parameter:**
- `orderNumber`?
- `partNumber`?
- `operationCode`?

**Nächster Schritt:** WSDL analysieren oder Test-Calls mit verschiedenen Parametern

---

## 💡 MÖGLICHE LÖSUNGEN

### Option 1: readLaborAndPartInformation testen ⭐

**Vermutung:** Diese Methode könnte Arbeitsoperationsnummern enthalten!

**Test nötig:**
```python
# Zu testen:
labor_info = client.service.readLaborAndPartInformation(
    orderNumber=order_number,
    partNumber=part_number  # oder andere Parameter?
)
```

**Status:** ⏳ **Muss getestet werden**

---

### Option 2: Hyundai Workshop Automation REST API ⭐⭐

**Da SOAP keine direkten Methoden hat:**
- Prüfe ob REST API verfügbar ist
- URL: `https://hmd.wa.hyundai-europe.com:9092`
- Authentifizierung erforderlich

**Status:** ⏳ **Muss geprüft werden**

---

### Option 3: Manuelle Prüfung (Fallback) ⭐⭐⭐

**Wenn keine API verfügbar:**
- Serviceberater prüft im Portal
- Bestätigungs-Button im Frontend
- Dokumentation der Prüfung

**Status:** ✅ **Immer möglich**

---

## 🎯 EMPFEHLUNG

### Nächste Schritte (Priorität):

1. **readLaborAndPartInformation testen** ⏳
   - Parameter ermitteln (WSDL analysieren)
   - Test mit echten Daten
   - Prüfen ob Arbeitsoperationsnummern enthalten sind

2. **Hyundai REST API prüfen** ⏳
   - Authentifizierung testen
   - Verfügbare Endpunkte prüfen
   - Prüfen ob Arbeitsoperationsnummern-Endpunkt existiert

3. **Manuelle Prüfung implementieren** ✅
   - Als Fallback immer verfügbar
   - Warnung im Frontend
   - Bestätigungs-Button

---

## 📊 ZUSAMMENFASSUNG

| Aspekt | Status | Ergebnis |
|--------|--------|----------|
| **SOAP-Verbindung** | ✅ | Funktioniert |
| **Hyundai-spezifische Methoden** | ❌ | Nicht verfügbar |
| **readWorkOrderDetails** | ✅ | Funktioniert, aber keine Positionen |
| **readLaborAndPartInformation** | ⏳ | Muss getestet werden |
| **REST API** | ⏳ | Muss geprüft werden |
| **Manuelle Prüfung** | ✅ | Immer möglich |

---

## ✅ DATENBANK-STRUKTUR

**Tabelle:** `loco_labours`

**Relevante Spalten:**
- ✅ `labour_operation_id` - Arbeitsoperationsnummer (z.B. "28257RTT", "BASICA00")
- ✅ `order_number` - Auftragsnummer
- ✅ `time_units` - AW (Arbeitseinheiten)
- ✅ `charge_type` - 60 = Garantie
- ✅ `labour_type` - 'G' = Garantie

**Erkenntnis:**
- ✅ Arbeitsoperationsnummern sind in Locosoft gespeichert
- ❌ Aber: GSW Portal-Daten (ob Standardarbeitszeit existiert) sind **NICHT** in Locosoft
- ❌ Wir können nicht prüfen, ob Hyundai im GSW Portal eine Standardarbeitszeit für ein Teil hat

---

## 🎯 FAZIT

### Was funktioniert:
- ✅ SOAP-Verbindung funktioniert
- ✅ `readWorkOrderDetails` funktioniert
- ✅ `labour_operation_id` ist in Datenbank vorhanden

### Was fehlt:
- ❌ Keine SOAP-Methode für GSW Portal-Daten
- ❌ Keine Möglichkeit, automatisch zu prüfen ob Standardarbeitszeit existiert
- ❌ `readWorkOrderDetails` enthält keine GSW Portal-Daten

### Lösung:
- ⚠️ **Manuelle Prüfung erforderlich** - Serviceberater muss im GSW Portal prüfen
- ✅ Oder: Hyundai REST API prüfen (falls verfügbar)

---

**Erstellt:** TAG 195  
**Status:** SOAP getestet, keine direkten Methoden für GSW Portal gefunden, manuelle Prüfung erforderlich
