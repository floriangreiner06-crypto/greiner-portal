# HAR-Analyse Ergebnisse - TAG 182

**Datum:** 2026-01-12  
**HAR-Datei:** `f03_bwa_vj_vergleich_alle_beriebe_angehackt.har`

---

## 🎯 ERGEBNISSE

### 1. Report-Identifikation

**Report-ID:**
```
storeID("i176278575AB142B18A70E1BDFAE95614")
```

**API-Endpoint:**
```
POST http://10.80.80.10:9300/bi/v1/reports
```

**SOAP-Format:**
- Cognos BI SOAP API
- Namespace: `http://developer.cognos.com/schemas/reportService/1`

---

### 2. Parameter-Struktur

**Zeit-Filter:**
```
[F_Belege].[Zeit].[Zeit].[Monat]->:[PC].[@MEMBER].[20251201-20251231]
```
- Format: `YYYYMMDD-YYYYMMDD` (Zeitraum)
- Beispiel: `20251201-20251231` = Dezember 2025

**Standort-Filter:**
```
[AH-Gruppe].[Betrieb]->:[PC].[@MEMBER].[XX]
```
- `[00]` = Deggendorf (Opel)
- `[01]` = Deggendorf HYU (Hyundai)
- `[02]` = Landau

**Vollständige Parameter-Struktur:**
```xml
<bus:parameterValues SOAP-ENC:arrayType="bus:parameterValue[4]">
  <item xsi:type="bus:parameterValue">
    <bus:name xsi:type="xsd:string">[F_Belege].[Zeit].[Zeit].[Monat]</bus:name>
    <bus:value SOAP-ENC:arrayType="bus:simpleParameterValue[1]">
      <item xsi:type="bus:simpleParameterValue">
        <bus:use xsi:type="xsd:string">[F_Belege].[Zeit].[Zeit].[Monat]->:[PC].[@MEMBER].[20251201-20251231]</bus:use>
        <bus:display xsi:type="xsd:string">Dez./2025</bus:display>
      </item>
    </bus:value>
  </item>
  <item xsi:type="bus:parameterValue">
    <bus:name xsi:type="xsd:string">[AH-Gruppe].[Betrieb]</bus:name>
    <bus:value SOAP-ENC:arrayType="bus:simpleParameterValue[1]">
      <item xsi:type="bus:simpleParameterValue">
        <bus:use xsi:type="xsd:string">[AH-Gruppe].[Betrieb]->:[PC].[@MEMBER].[02]</bus:use>
        <bus:display xsi:type="xsd:string">Landau</bus:display>
      </item>
    </bus:value>
  </item>
</bus:parameterValues>
```

---

### 3. Response-Struktur

**Format:** `multipart/related`

**Parts:**
1. **Part 1:** SOAP-Envelope (XML, ~24 KB)
2. **Part 2:** HTML-Report (HTML, ~29 KB) - **Enthält BWA-Werte!**
3. **Part 3:** XML-Report-Definition (XML, ~354 KB)

**Content-Type:**
```
multipart/related; boundary=1768228493085.-6782409587813279369.-1326771125
```

---

### 4. Authentifizierung

**Token:**
```
authenticityToken: VjHWOxCiNmt6Y2F9FC3K6AYFlwdUwl4WEWsVdNwCtWbQRA==
```

**Context-ID:**
```
CAFW000000a0Q0FGQTYwMDAwMDAwMDlBaFFBQUFBR1RDRU1ib0szN3RLbDkwNnZXVUVuU3FsckFRY0FBQUJUU0VFdE1qVTJJQUFBQU1DV1dXTTRaaTdMdkpLamNNZHcxT3JpQzZhaExuNUdBVTBEOTlsTGtsdnA0OTExNzR8cnM_
```

---

## 🚀 NÄCHSTE SCHRITTE

### 1. SOAP-Request-Generator erstellen

**Ziel:** Automatisch SOAP-Requests mit verschiedenen Parametern generieren

**Parameter-Kombinationen:**
- Alle Standorte × Alle Monate
- Einzelne Standorte × Einzelne Monate
- YTD-Berechnungen

### 2. Response-Parser erstellen

**Ziel:** BWA-Werte aus HTML-Response extrahieren

**Vorgehen:**
- Multipart-Response parsen
- HTML-Part extrahieren
- Tabellen parsen
- BWA-Werte strukturiert extrahieren

### 3. Vergleichs-Script erstellen

**Ziel:** Systematischer Vergleich DRIVE vs. GlobalCube

**Features:**
- Alle Standorte/Marken
- Alle BWA-Positionen
- Monat vs. YTD
- Differenz-Analyse

---

## 📊 ERWARTETE ERGEBNISSE

Nach Implementierung:
- ✅ Exakte BWA-Werte für alle Standorte/Marken
- ✅ Validierung der DRIVE-Werte
- ✅ Identifikation aller Differenzen
- ✅ Filter-Logik vollständig verstanden

---

## 🔧 TOOLS

**Erstellt:**
- ✅ `scripts/analyse_globalcube_har.py` - HAR-Analyse
- ✅ `/tmp/cognos_soap_request.xml` - SOAP-Request
- ✅ `/tmp/cognos_response.txt` - Response
- ✅ `/tmp/cognos_headers.json` - Headers

**Zu erstellen:**
- ⏳ `scripts/cognos_soap_client.py` - SOAP-Client
- ⏳ `scripts/cognos_bwa_extractor.py` - BWA-Werte-Extraktor
- ⏳ `scripts/vergleiche_bwa_cognos_drive.py` - Vergleichs-Script

---

## 📝 NOTIZEN

- **Cube-Name:** `[F_Belege]` - Das ist der Haupt-Cube für BWA-Daten
- **MDX-Syntax:** Cognos verwendet MDX-ähnliche Syntax für Filter
- **Parameter-Format:** `[Dimension].[Hierarchy].[Level]->:[PC].[@MEMBER].[Value]`
- **Standort-Mapping:**
  - `[00]` = Deggendorf Opel
  - `[01]` = Deggendorf Hyundai
  - `[02]` = Landau
