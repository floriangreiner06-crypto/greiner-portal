# IBM Cognos Analyse-Optionen - TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Optionen evaluiert

---

## 🔍 GEPRÜFTE OPTIONEN

### 1. Cognos REST API ❌

**Status:** Nicht verfügbar (ältere Cognos-Version)

**Ergebnis:**
- `/api/v1` → 401 (Authentifizierung erforderlich, aber kein JSON)
- `/bi/v1/disp` → 200 (HTML, nicht JSON)
- Endpunkte geben HTML zurück, keine REST API

**Erkenntnis:** Cognos-Version unterstützt keine moderne REST API.

---

### 2. Python-Bibliotheken ❌

**Geprüfte Bibliotheken:**
- `cognos-api` - Nicht verfügbar
- `ibm-cognos` - Nicht verfügbar
- `cognos-rest` - Nicht verfügbar
- `pycognos` - Nicht verfügbar
- `cognos-sdk` - Nicht verfügbar

**Erkenntnis:** Keine offiziellen Python-Bibliotheken für Cognos verfügbar.

---

### 3. IBM Cognos Add-ons ⚠️

**Verfügbare Add-ons:**
1. **IBM Cognos Analysis for Microsoft Excel** ✅
   - Integriert Cognos mit Excel
   - Könnte helfen, Daten zu extrahieren
   - **Problem:** Benötigt Excel-Installation und Add-on

2. **IBM Cognos Dynamic Query Analyzer** ⚠️
   - Analysiert Abfragen
   - **Problem:** Nicht für Daten-Extraktion gedacht

3. **IBM Cognos SDK** (Java-basiert) ⚠️
   - Offizielles SDK für Cognos
   - **Problem:** Java-basiert, nicht Python

---

## ✅ PRAKTIKABLE LÖSUNGEN

### Option 1: Direkte Portal-Analyse (Bereits durchgeführt) ✅

**Was wir bereits haben:**
- ✅ Portal-Zugriff (http://10.80.80.10:9300/bi/)
- ✅ Login (Greiner / Hawaii#22)
- ✅ Struktur-Dateien analysiert (`Struktur_GuV.xml`, `Struktur_Controlling.xml`)
- ✅ f_belege Cube analysiert
- ✅ Excel-Exporte analysiert

**Vorteile:**
- Funktioniert sofort
- Keine zusätzlichen Tools nötig
- Bereits durchgeführt

**Nachteile:**
- Manuelle Analyse erforderlich
- Keine automatische Daten-Extraktion

---

### Option 2: Cognos Content Store (Datenbank) analysieren ⏳

**Idee:** Cognos speichert Metadaten in einer Datenbank (Content Store)

**Möglichkeiten:**
1. Content Store DB direkt analysieren (falls Zugriff)
2. Struktur-Dateien weiter analysieren (bereits begonnen)
3. Cube-Definitionen analysieren

**Vorteile:**
- Direkter Zugriff auf Metadaten
- Filter-Logik könnte in DB sein

**Nachteile:**
- Benötigt DB-Zugriff
- Komplexe Struktur

---

### Option 3: Excel-Exporte weiter analysieren ⏳

**Was wir haben:**
- `/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx`
- Bereits teilweise analysiert

**Nächste Schritte:**
1. Excel-Struktur vollständig verstehen
2. Werte korrekt extrahieren (Spalten-Header identifizieren)
3. Vergleich mit DRIVE durchführen

**Vorteile:**
- Excel ist bereits vorhanden
- Enthält BWA-Werte
- Vergleich möglich

**Nachteile:**
- Werte müssen korrekt interpretiert werden
- Spalten-Header müssen identifiziert werden

---

### Option 4: Cognos SDK (Java) ⚠️

**Möglichkeit:** Java-SDK verwenden und via Jython/JPype in Python nutzen

**Vorteile:**
- Offizielles SDK
- Vollständiger Zugriff

**Nachteile:**
- Sehr komplex
- Java-Abhängigkeit
- Hoher Aufwand

---

## 🎯 EMPFEHLUNG

### Sofort umsetzbar: Excel-Exporte weiter analysieren ✅

**Warum:**
- Excel ist bereits vorhanden
- Enthält BWA-Werte
- Vergleich mit DRIVE möglich
- Keine zusätzlichen Tools nötig

**Nächste Schritte:**
1. Excel-Spalten-Header identifizieren (Monat, YTD, Vorjahr)
2. Werte für Dezember 2025 und YTD Sep-Dez 2025 extrahieren
3. Vergleich mit DRIVE durchführen
4. Unterschiede analysieren

### Mittelfristig: Struktur-Dateien weiter analysieren ✅

**Warum:**
- Struktur-Dateien enthalten Filter-Logik
- Bereits teilweise analysiert
- Keine zusätzlichen Tools nötig

**Nächste Schritte:**
1. Konto-Mappings zu Struktur-IDs finden
2. Filter-Logik extrahieren
3. Ausbildung-Position (411xxx) validieren

---

## 📊 STATUS

- ✅ Cognos API geprüft (nicht verfügbar)
- ✅ Python-Bibliotheken geprüft (nicht verfügbar)
- ✅ Add-ons recherchiert
- ✅ Praktikable Lösungen identifiziert
- ⏳ Excel-Exporte weiter analysieren
- ⏳ Struktur-Dateien weiter analysieren

---

## 🔧 TOOLS

**Cognos API Explorer:**
```bash
cd /opt/greiner-portal
python3 scripts/cognos_api_explorer.py
```

**Excel-Analyse:**
```bash
cd /opt/greiner-portal
python3 scripts/globalcube_explorer.py
```

---

**Empfehlung:** Excel-Exporte weiter analysieren und Struktur-Dateien vertiefen.
