# Termin im Planer nicht sichtbar - Problem-Analyse (TAG 200)

**Datum:** 2026-01-20  
**Problem:** Termine werden erstellt, erscheinen in Terminliste, aber NICHT im grafischen Planer

---

## ✅ WAS FUNKTIONIERT

1. ✅ **Termine werden erstellt** (SOAP `writeAppointment` erfolgreich)
2. ✅ **Termine existieren** (`read_appointment` erfolgreich)
3. ✅ **Termine in Liste** (`listAppointmentsByDate` findet Termine)
4. ✅ **Terminliste-Ausdruck** zeigt Termine korrekt

## ❌ PROBLEM

**Termine erscheinen NICHT im grafischen Planer (Tagesübersicht)**

---

## 🔍 SYSTEMATISCHE ANALYSE

### Schritt 1: Bestehenden Termin analysieren

**Ziel:** Einen funktionierenden Termin aus Locosoft lesen und mit unserem vergleichen

```python
# Beispiel: Termin aus Locosoft lesen
termin = soap_client.read_appointment(existing_appointment_number)
# Alle Felder ausgeben und vergleichen
```

**Fragen:**
- Welche Felder hat ein funktionierender Termin?
- Gibt es Felder, die wir nicht setzen?
- Gibt es Unterschiede in `type`, `returnDateTime`, etc.?

### Schritt 2: SOAP-Signatur prüfen

**Ziel:** Alle verfügbaren Parameter für `writeAppointment` identifizieren

Aus Fehler-Log (vorher):
```
Signature: `number: xsd:int, text: xsd:string, customerNumber: xsd:int, 
vehicleNumber: xsd:int, bringDateTime: xsd:dateTime, bringServiceAdvisor: xsd:int, 
returnDateTime: xsd:dateTime, returnServiceAdvisor: xsd:int, comment: xsd:string, 
type: {http://soap.loco_soft.de/}type, urgency: xsd:int, vehicleStatus: xsd:int, 
inProgress: xsd:int, workOrderNumber: xsd:int, rentalCarNumber: xsd:int`
```

**Mögliche fehlende Parameter:**
- `urgency` - Dringlichkeit?
- `vehicleStatus` - Fahrzeugstatus?
- `inProgress` - In Bearbeitung?
- `returnServiceAdvisor` - Serviceberater für Rückgabe?

### Schritt 3: Locosoft-Konfiguration prüfen

**Mögliche Ursachen:**
1. **Workshop-Filter:** Planer zeigt nur bestimmte Workshops
2. **Termin-Typ-Filter:** Planer zeigt nur bestimmte Typen
3. **Dauer-Filter:** Planer zeigt nur Termine mit Dauer > 0
4. **Mechaniker-Zuweisung:** Planer zeigt nur zugewiesene Termine
5. **Station-Zuweisung:** Planer zeigt nur Termine mit Station

### Schritt 4: Vergleich mit manuell erstellten Terminen

**Vorgehen:**
1. In Locosoft manuell einen Termin erstellen (für Auftrag #40167)
2. Termin per SOAP lesen
3. Alle Felder mit unserem vergleichen
4. Unterschiede identifizieren

---

## 🚀 LÖSUNGSANSÄTZE

### Ansatz 1: Alle verfügbaren Parameter setzen

```python
appointment_data = {
    'number': 0,
    'bringDateTime': bring_datetime,
    'returnDateTime': return_datetime,
    'text': f'Auftrag #{auftrag_nr}',
    'type': 'fix',
    'comment': f'Gudat-Sync - Auftrag {auftrag_nr}',
    'customerNumber': kunde_nr,
    'vehicleNumber': fahrzeug_nr,
    'workOrderNumber': auftrag_nr,
    'bringServiceAdvisor': serviceberater_nr,
    'returnServiceAdvisor': serviceberater_nr,  # NEU
    'urgency': 1,  # NEU: Standard-Dringlichkeit
    'vehicleStatus': 0,  # NEU: Standard-Status
    'inProgress': 0  # NEU: Nicht in Bearbeitung
}
```

### Ansatz 2: Locosoft-Support kontaktieren

**Frage an Locosoft:**
- Welche Parameter sind erforderlich, damit ein Termin im grafischen Planer erscheint?
- Gibt es spezielle Einstellungen/Konfigurationen?
- Muss ein Termin einem Mechaniker/Station zugewiesen werden?

### Ansatz 3: Termin-Typ testen

**Verschiedene Typen testen:**
- `'fix'` - Fester Termin (aktuell)
- `'real'` - Realer Termin?
- `'loose'` - Lose Anlieferung (ursprünglich)

### Ansatz 4: Dauer/returnDateTime prüfen

**Problem:** `returnDateTime` könnte falsch berechnet werden

**Lösung:**
- Sicherstellen, dass `returnDateTime` NACH `bringDateTime` liegt
- Mindest-Dauer: 30 Minuten
- Prüfen, ob Dauer > 0 in Locosoft angezeigt wird

---

## 📋 NÄCHSTE SCHRITTE

### 1. Bestehenden Termin analysieren
```bash
# Script erstellen, das einen bestehenden Termin aus Locosoft liest
# und alle Felder ausgibt
```

### 2. Alle Parameter testen
```python
# Termin mit ALLEN verfügbaren Parametern erstellen
# Schrittweise Parameter entfernen, um Minimum zu finden
```

### 3. Locosoft-Support kontaktieren
- Dokumentation anfordern
- Spezifische Frage stellen: "Warum erscheint Termin nicht im Planer?"

### 4. Manuellen Termin vergleichen
- In Locosoft manuell Termin erstellen
- Per SOAP lesen
- Mit unserem vergleichen

---

## ⚠️ HINWEISE

- Termine werden **definitiv erstellt** (validiert)
- Problem liegt wahrscheinlich an **fehlenden Parametern** oder **Locosoft-Konfiguration**
- Systematisches Vorgehen erforderlich, da SOAP-Dokumentation unvollständig
