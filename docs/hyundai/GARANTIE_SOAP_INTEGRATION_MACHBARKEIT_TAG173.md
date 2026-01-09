# Garantie SOAP-Integration: Machbarkeitsanalyse

**Erstellt:** 2026-01-09 (TAG 173)  
**Zweck:** Fehlende Arbeiten (BASICA00, TT-Zeit, RQ0) per SOAP in Locosoft schreiben

---

## ✅ VORAUSSETZUNGEN

### 1. SOAP-Client vorhanden
- ✅ `tools/locosoft_soap_client.py` existiert
- ✅ `writeWorkOrderDetails()` Methode vorhanden
- ✅ `readWorkOrderDetails()` Methode vorhanden
- ✅ Verbindung getestet (10.80.80.7:8086)

### 2. Konfiguration
- ✅ SOAP-Host: 10.80.80.7
- ✅ SOAP-Port: 8086
- ✅ User: 9001
- ✅ Password: Max2024
- ✅ Interface-Version: 2.2

---

## 🔍 ANALYSE: writeWorkOrderDetails

### Aktuelle Implementierung

```python
def write_work_order_details(self, work_order: Dict) -> Dict:
    """
    Erstellt oder aktualisiert einen Auftrag.
    
    Args:
        work_order: Dict mit Auftrags-Daten
    
    Returns:
        Dict mit 'success', 'number', 'message'
    """
    result = self.service.writeWorkOrderDetails(workOrder=work_order)
    return {...}
```

### Offene Fragen

1. **Struktur von `work_order` Dict?**
   - Welche Felder sind erforderlich?
   - Wie werden Arbeitspositionen (labours) übergeben?
   - Muss der komplette Auftrag gesendet werden oder nur die neue Position?

2. **Arbeitspositionen hinzufügen:**
   - Können wir einzelne Positionen hinzufügen?
   - Oder müssen wir den kompletten Auftrag mit allen Positionen senden?

3. **Felder für Arbeitsposition:**
   - `orderPosition`: Position-Nummer
   - `orderPositionLine`: Zeilen-Nummer
   - `operationCode`: Arbeitsnummer (z.B. 'BASICA00')
   - `timeUnits`: AW
   - `description`: Beschreibung
   - `chargeType`: 60 = Garantie
   - `labourType`: 'G' = Garantie

---

## 🚀 IMPLEMENTIERUNGS-ANSATZ

### Variante 1: Kompletter Auftrag (Sicherer)

```python
# 1. Aktuellen Auftrag lesen
work_order = client.read_work_order_details(order_number)

# 2. Neue Position hinzufügen
new_labour = {
    'orderPosition': max_position + 1,
    'operationCode': 'BASICA00',
    'timeUnits': 1.0,
    'description': 'GDS-Grundprüfung',
    'chargeType': 60,
    'labourType': 'G'
}
work_order['labours'].append(new_labour)

# 3. Kompletten Auftrag zurückschreiben
client.write_work_order_details(work_order)
```

**Vorteile:**
- ✅ Sicher (keine Daten gehen verloren)
- ✅ Funktioniert garantiert

**Nachteile:**
- ⚠️ Mehr Datenübertragung
- ⚠️ Risiko bei vielen Positionen

### Variante 2: Nur neue Position (Effizienter)

```python
# Nur neue Position senden
new_work_order = {
    'number': order_number,
    'labours': [{
        'orderPosition': 999,  # Auto-generiert?
        'operationCode': 'BASICA00',
        'timeUnits': 1.0,
        ...
    }]
}
client.write_work_order_details(new_work_order)
```

**Vorteile:**
- ✅ Effizienter
- ✅ Weniger Datenübertragung

**Nachteile:**
- ⚠️ Unklar ob Locosoft das unterstützt
- ⚠️ Muss getestet werden

---

## 📋 API-ENDPOINTS (bereits erstellt)

### 1. BASICA00 hinzufügen
```
POST /api/garantie/soap/add-basica00/<order_number>
```

**Beispiel:**
```bash
curl -X POST http://10.80.80.20:5000/api/garantie/soap/add-basica00/220345 \
  -H "Cookie: session=..."
```

**Response:**
```json
{
  "success": true,
  "message": "BASICA00 erfolgreich hinzugefügt",
  "data": {
    "labour_number": 2,
    "operation_code": "BASICA00",
    "time_units": 1.0
  }
}
```

### 2. TT-Zeit hinzufügen
```
POST /api/garantie/soap/add-tt-zeit/<order_number>
Body: {
  "time_units": 0.8,
  "operation_code": "28257RTT",  // Optional
  "description": "TT-Zeit Diagnose"
}
```

### 3. RQ0 hinzufügen
```
POST /api/garantie/soap/add-rq0/<order_number>
```

### 4. Verbindung testen
```
GET /api/garantie/soap/test-connection
```

---

## 🧪 NÄCHSTE SCHRITTE

### 1. Struktur prüfen
```python
# Test: Auftrag lesen und Struktur analysieren
work_order = client.read_work_order_details(220345)
print(json.dumps(work_order, indent=2, default=str))
```

### 2. Test-Schreiben
```python
# Test: Eine Position hinzufügen (auf Test-Auftrag)
result = add_labour_to_work_order(
    order_number=220345,
    operation_code='BASICA00',
    time_units=1.0,
    description='GDS-Grundprüfung (Test)'
)
```

### 3. Integration ins Dashboard
- Buttons im Live-Dashboard mit API-Calls verbinden
- Erfolgs-/Fehler-Meldungen anzeigen
- Auto-Refresh nach erfolgreichem Schreiben

---

## ⚠️ RISIKEN & HINWEISE

### Risiken:
1. **Datenverlust:** Wenn wir den kompletten Auftrag überschreiben, könnten Daten verloren gehen
2. **Struktur-Änderungen:** Locosoft könnte die Struktur ändern
3. **Berechtigungen:** SOAP-User (9001) muss Schreibrechte haben

### Hinweise:
1. **Backup:** Vor dem Schreiben sollte ein Backup erstellt werden
2. **Validierung:** Prüfen ob Auftrag noch offen ist
3. **Duplikate:** Prüfen ob Position bereits existiert

---

## 💡 ALTERNATIVE: Locosoft direkt öffnen

Falls SOAP nicht funktioniert:
- Link zu Locosoft generieren: `http://10.80.80.7/locosoft/order/220345`
- Serviceberater öffnet Locosoft manuell
- Position wird manuell hinzugefügt

---

## 📝 TODO

- [ ] Struktur von `readWorkOrderDetails` analysieren
- [ ] Test-Schreiben auf Test-Auftrag durchführen
- [ ] Buttons im Dashboard mit API verbinden
- [ ] Fehlerbehandlung verbessern
- [ ] Validierung hinzufügen (Duplikate, Status, etc.)
- [ ] Logging für Audit-Trail

---

*Machbarkeitsanalyse erstellt: 2026-01-09 (TAG 173)*
