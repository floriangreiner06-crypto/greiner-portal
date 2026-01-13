# GlobalCube BWA Mapping Exploration - TAG 182

**Datum:** 2026-01-12  
**Status:** 🔍 Exploration läuft

---

## 🎯 ZIEL

Die tatsächliche GlobalCube BWA-Logik und Mapping-Regeln durch direkte Analyse extrahieren, anstatt zu raten.

---

## 📋 GEFUNDENE RESSOURCEN

### GlobalCube Portal
- **URL:** http://10.80.80.10:9300
- **Status:** ✅ Erreichbar (HTTP 200)

### GlobalCube Strukturen
- **Pfad:** `/mnt/globalcube/GCStruct`
- **Status:** ✅ Gefunden
- **Neueste Struktur:** `AutohausGreiner_20260109_161135.zip`
- **Relevante XML-Dateien:**
  - `Xml/Struktur_GuV.xml` - **GUV/BWA-Struktur**
  - `Xml/Struktur_Controlling.xml` - Controlling-Struktur
  - `Kontenrahmen/Kontenrahmen.csv` - **Konto-Mapping**

### GlobalCube Cubes
- **Pfad:** `/mnt/globalcube/Cubes`
- **Status:** ✅ Gefunden
- **Relevante Cubes:**
  - `f_belege` - Belege-Cube (33 MB, könnte BWA-Daten enthalten)
  - `dashboard_gesamt` - Dashboard-Cube

---

## 🔍 ANALYSE-ERGEBNISSE

### 1. Kontenrahmen CSV

**Struktur:**
- Spalten: `Konto_Nr`, `Konto_Bezeichnung`, `Konto_Art`, `Kostenstelle`, `STK`
- Encoding: `latin-1`
- Format: Semikolon-separiert

**BWA-relevante Konten:**
- **Umsatz-Konten (8xxxxx):** Im Kontenrahmen vorhanden
- **Einsatz-Konten (7xxxxx):** Im Kontenrahmen vorhanden
- **Kosten-Konten (4xxxxx):** Im Kontenrahmen vorhanden

### 2. GuV-Struktur XML

**Root-Element:**
- Tag: `Ebene`
- Attribute: `Name="Struktur_GuV"`, `StrukturId="48"`

**Nächste Schritte:**
- Vollständige XML-Struktur analysieren
- BWA-Positionen identifizieren
- Filter-Logik extrahieren

### 3. Controlling-Struktur XML

**Noch zu analysieren**

---

## 🚀 NÄCHSTE SCHRITTE

1. ⏳ **GuV-XML vollständig analysieren**
   - Alle Ebenen und Positionen extrahieren
   - Filter-Logik identifizieren
   - Konto-Mappings dokumentieren

2. ⏳ **Kontenrahmen CSV durchsuchen**
   - Alle BWA-relevanten Konten auflisten
   - Kostenstellen-Mappings extrahieren
   - Besondere Konten identifizieren (411xxx, 489xxx, 410021, etc.)

3. ⏳ **Controlling-XML analysieren**
   - BWA-spezifische Strukturen identifizieren
   - Berechnungslogik extrahieren

4. ⏳ **GlobalCube Portal Reports analysieren**
   - BWA-Reports finden
   - Filter-Parameter extrahieren
   - JavaScript-Logik analysieren

5. ⏳ **Mapping-Dokumentation erstellen**
   - Vollständige Konto-Mappings
   - Filter-Logik dokumentieren
   - Abweichungen identifizieren

---

## 📝 ERGEBNISSE

*Wird während der Exploration aktualisiert...*

---

## 🔧 TOOLS

**Explorer-Script:**
- `/opt/greiner-portal/scripts/globalcube_explorer.py`
- Analysiert GlobalCube-Strukturen, Cubes und Portal**Ausführung:**
```bash
cd /opt/greiner-portal
python3 scripts/globalcube_explorer.py
```
