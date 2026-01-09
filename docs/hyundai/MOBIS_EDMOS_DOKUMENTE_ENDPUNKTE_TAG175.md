# Mobis EDMOS - Dokumente/Rechnungen Endpunkte

**Erstellt:** 2026-01-09 (TAG 175)  
**HAR-Datei:** `edos.mobiseurope.com.har`

---

## 🎯 GEFUNDENE ENDPUNKTE

### 1. Rechnungen abrufen: `JVCDSW022A cmd=inquery`

**Endpunkt:**
```
POST https://edos.mobiseurope.com/EDMOSN/ServiceController?act=JVCDSW022A&cmd=inquery
```

**Request (Nexacro XML):**
```xml
<Root xmlns="http://www.nexacroplatform.com/platform/dataset">
  <Parameters>
    <Parameter id="G_JDBC">EDMOS_JDBC</Parameter>
    <Parameter id="G_LOCAL_CD_USE">Y</Parameter>
    <Parameter id="C_USR_ID">G2403Koe</Parameter>
    <Parameter id="C_PAGE_NO">0</Parameter>
    <Parameter id="C_FETCH_COUNT">100</Parameter>
    <!-- Weitere Parameter... -->
  </Parameters>
</Root>
```

**Response (Nexacro XML):**
```xml
<Root>
  <Dataset id="dsList">
    <ColumnInfo>
      <Column id="DIV_IVC_NO" type="string"/>      <!-- Rechnungsnummer -->
      <Column id="DIV_FR_DT" type="string"/>       <!-- Datum -->
      <Column id="DIV_IVC_ITM" type="bigdecimal"/> <!-- Anzahl Positionen -->
      <Column id="DIV_IVC_QT" type="bigdecimal"/>   <!-- Menge -->
      <Column id="DIV_TIVC_AMT" type="bigdecimal"/> <!-- Betrag -->
      <Column id="DIV_TVAT_AMT" type="bigdecimal"/> <!-- MwSt -->
      <Column id="DIV_TOTAL" type="bigdecimal"/>   <!-- Gesamt -->
      <Column id="DIV_ICD_TYP" type="string"/>      <!-- Typ (D=Delivery, etc.) -->
      <Column id="INVOICE_PRT" type="string"/>     <!-- "Print" wenn verfügbar -->
      <Column id="CREDIT_PRT" type="string"/>       <!-- Credit Print -->
      <!-- Weitere Spalten... -->
    </ColumnInfo>
    <Rows>
      <Row>
        <Col id="DIV_IVC_NO">HG50168708</Col>
        <Col id="DIV_FR_DT">20251201</Col>
        <Col id="INVOICE_PRT">Print</Col>
        <!-- ... -->
      </Row>
    </Rows>
  </Dataset>
</Root>
```

**Wichtige Felder:**
- `DIV_IVC_NO` - Rechnungsnummer (z.B. "HG50168708")
- `INVOICE_PRT` - "Print" wenn Rechnung verfügbar ist
- `DIV_ICD_TYP` - Typ (D=Delivery, etc.)
- `DIV_FR_DT` - Datum (Format: YYYYMMDD)

---

### 2. Print/Download-Endpunkt (ANALYSE PRINT-HAR)

**HAR-Datei analysiert:** `edos.mobiseurope.com_print.har`

**Ergebnis:**
- ❌ **Kein direkter Print-Endpunkt in HAR-Datei gefunden**
- ✅ `INVOICE_PRT = "Print"` in Response vorhanden (zeigt dass Print möglich ist)
- ⚠️ PDF wird wahrscheinlich **clientseitig** generiert oder über separaten Endpunkt

**Mögliche Endpunkte (zu testen):**
1. `JVCDSW022A cmd=print` - Rechnung drucken/PDF
2. `JVCDSW022A cmd=export` - Rechnung exportieren
3. `JVCDSW022A cmd=download` - Rechnung herunterladen
4. `JVCDSW022A cmd=getPdf` - PDF abrufen

**Request-Parameter (vermutet):**
- `DIV_IVC_NO` - Rechnungsnummer (z.B. "HG60000530")
- `DIV_ICD_TYP` - Typ (z.B. "D" für Delivery)
- Weitere Parameter aus `cmd=inquery` Request

**Hinweis aus Login-Response:**
```
"You are not allowed to print more than 10 pdf at a time!"
```

**⚠️ NÄCHSTE SCHRITTE:**
- Manuell in Mobis eine Rechnung drucken und Browser DevTools öffnen
- Oder: Verschiedene `cmd`-Parameter testen (print, export, download, getPdf)
- Response-Format prüfen (PDF, Base64, Download-Link, etc.)

---

## 📋 ANDERE GEFUNDENE SERVICES

### `JVCDSW006A` - Board/Notice Service
- `cmd=onLoadCompleted` - Lädt Board-Daten
- `cmd=inqueryBoard` - Sucht Board-Einträge
- Enthält PDF-Anhänge: `DNW_ATH_FLE1`, `DQA_ATH_FLE1` mit Dateinamen wie "RS-ET-2025-006.pdf"

### `JVCUZW000A` - User Service
- `cmd=login` - Login
- `cmd=insertUUS` - User-Update

---

## 🔍 NÄCHSTE SCHRITTE

### 1. Print/Download-Endpunkt finden ✅ HAR analysiert
- [x] HAR-Datei mit Print-Aktion analysiert (`edos.mobiseurope.com_print.har`)
- [ ] **Print-Endpunkt nicht in HAR gefunden** - wahrscheinlich clientseitig oder separater Endpunkt
- [ ] Verschiedene `cmd`-Parameter testen:
  - `JVCDSW022A cmd=print`
  - `JVCDSW022A cmd=export`
  - `JVCDSW022A cmd=download`
  - `JVCDSW022A cmd=getPdf`
- [ ] Browser DevTools beim Drucken öffnen (falls möglich)

### 2. Parameter prüfen
- [ ] Welche Parameter werden für Print benötigt?
  - Rechnungsnummer (`DIV_IVC_NO`)?
  - Typ (`DIV_ICD_TYP`)?
  - Weitere Parameter?

### 3. Response-Format prüfen
- [ ] Ist es ein PDF-Download?
- [ ] Base64-kodiert?
- [ ] Direkter Download-Link?

### 4. Implementierung
- [ ] API-Client erweitern: `get_invoice_pdf(invoice_number)`
- [ ] In Garantieakte-Workflow integrieren
- [ ] Als Anhang zur Garantieakte hinzufügen

---

## 💡 HINWEISE

1. **Nexacro-Format:** Alle Requests/Responses sind im Nexacro XML-Format
2. **Session:** JSESSIONID Cookie erforderlich (nach Login)
3. **Encoding:** UTF-8
4. **Print-Limit:** Max. 10 PDFs gleichzeitig

---

**Status:** ⏳ Print/Download-Endpunkt noch zu identifizieren
