# Mobis EDMOS Print-Endpunkt - Zusammenfassung

**Datum:** 2026-01-09 (TAG 175)  
**HAR-Dateien analysiert:**
- `edos.mobiseurope.com.har` - Normale Navigation
- `edos.mobiseurope.com_print.har` - Print-Aktion

---

## ✅ GEFUNDEN

### 1. Rechnungen abrufen: `JVCDSW022A cmd=inquery`

**Endpunkt:**
```
POST https://edos.mobiseurope.com/EDMOSN/ServiceController?act=JVCDSW022A&cmd=inquery
```

**Response enthält:**
- Liste von Rechnungen mit `DIV_IVC_NO` (Rechnungsnummer)
- `INVOICE_PRT = "Print"` - Zeigt dass Print möglich ist
- `DIV_ICD_TYP` - Typ (z.B. "D" für Delivery)

**Beispiel:**
```xml
<Row>
  <Col id="DIV_IVC_NO">HG60000530</Col>
  <Col id="INVOICE_PRT">Print</Col>
  <Col id="DIV_ICD_TYP">D</Col>
</Row>
```

---

## ❌ NICHT GEFUNDEN

### Print/Download-Endpunkt

**Analyse-Ergebnis:**
- ❌ Kein direkter Print-Endpunkt in HAR-Datei gefunden
- ❌ Keine PDF-Responses in HAR-Datei
- ❌ Keine Download-URLs in Responses

**Mögliche Gründe:**
1. PDF wird **clientseitig** über JavaScript generiert
2. Print-Endpunkt wird über **separaten Request** aufgerufen (nicht in HAR erfasst)
3. Print erfolgt über **Browser Print-Dialog** (nicht über API)

---

## 🔍 MÖGLICHE ENDPUNKTE (ZU TESTEN)

Basierend auf der Nexacro-Struktur könnten folgende Endpunkte existieren:

### Option 1: `JVCDSW022A cmd=print`
```
POST /EDMOSN/ServiceController?act=JVCDSW022A&cmd=print
```
**Request-Parameter (vermutet):**
- `DIV_IVC_NO` - Rechnungsnummer
- `DIV_ICD_TYP` - Typ

### Option 2: `JVCDSW022A cmd=export`
```
POST /EDMOSN/ServiceController?act=JVCDSW022A&cmd=export
```

### Option 3: `JVCDSW022A cmd=download`
```
POST /EDMOSN/ServiceController?act=JVCDSW022A&cmd=download
```

### Option 4: `JVCDSW022A cmd=getPdf`
```
POST /EDMOSN/ServiceController?act=JVCDSW022A&cmd=getPdf
```

---

## 🧪 TEST-VORSCHLAG

### 1. Manueller Test
1. In Mobis einloggen
2. Zu Rechnungen navigieren (`JVCDSW022A`)
3. Eine Rechnung auswählen
4. **Browser DevTools öffnen** (F12 → Network)
5. **Print-Button klicken**
6. Network-Requests analysieren

### 2. API-Test
```python
# Test verschiedene cmd-Parameter
for cmd in ['print', 'export', 'download', 'getPdf']:
    response = client.call_service(
        act='JVCDSW022A',
        cmd=cmd,
        parameters={
            'DIV_IVC_NO': 'HG60000530',
            'DIV_ICD_TYP': 'D'
        }
    )
    # Prüfe Response auf PDF
```

---

## 💡 ALTERNATIVE LÖSUNGEN

### Falls kein API-Endpunkt verfügbar:

1. **Selenium + Browser Print:**
   - Selenium öffnet Mobis
   - Navigiert zu Rechnung
   - Triggert Browser Print-Dialog
   - Speichert als PDF

2. **Locosoft SOAP:**
   - Prüfen ob Locosoft SOAP Zugriff auf Mobis-Rechnungen hat
   - `getMobisInvoice()` oder ähnliche Methode

3. **Hyundai Workshop Automation:**
   - Prüfen ob dort Rechnungen verfügbar sind
   - HAR-Datei `hmd.wa.hyundai-europe.com.har` analysieren

---

## 📋 NÄCHSTE SCHRITTE

1. [ ] **Manueller Test:** Browser DevTools beim Drucken öffnen
2. [ ] **API-Test:** Verschiedene `cmd`-Parameter testen
3. [ ] **Alternative:** Selenium-Lösung implementieren
4. [ ] **Alternative:** Locosoft SOAP prüfen
5. [ ] **Alternative:** Hyundai Workshop Automation prüfen

---

**Status:** ⏳ Print-Endpunkt noch zu identifizieren - HAR-Analyse abgeschlossen
