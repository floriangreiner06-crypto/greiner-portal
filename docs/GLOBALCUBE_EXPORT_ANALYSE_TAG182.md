# GlobalCube Export-Analyse - TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Export analysiert

---

## 📋 EXPORT-INFORMATIONEN

**Datei:** `/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx`  
**Format:** Excel (OpenXML)  
**Sheet:** Seite1_1

**Gefundene BWA-Positionen in Shared Strings:**
- Umsatzerlöse
- Einsatzwerte
- Variable Kosten
- Trainingskosten
- Fahrzeugkosten
- Werbekosten
- Direkte Kosten
- Personalkosten
- Gemeinkosten
- Deckungsbeitrag
- Indirekte Kosten
- Raumkosten
- Kalk. Kosten
- Umlagekosten
- Betriebsergebnis

---

## 🔍 ANALYSE-ERGEBNISSE

### 1. Excel-Struktur

**Format:** OpenXML (ZIP-basiert)  
**Dateien im ZIP:**
- `xl/sharedStrings.xml` - Alle Text-Strings (53 Strings)
- `xl/worksheets/Sheet1.xml` - Sheet-Daten (63,912 Bytes)
- `xl/workbook.xml` - Workbook-Struktur

### 2. BWA-relevante Begriffe gefunden ✅

**In Shared Strings:**
- ✅ "Direkte Kosten"
- ✅ "Indirekte Kosten"
- ✅ "Betriebsergebnis"
- ✅ "Umsatzerlöse"
- ✅ "Einsatzwerte"
- ✅ "Deckungsbeitrag"

**Erkenntnis:** Excel enthält BWA-Struktur, Werte müssen aus Sheet-Daten extrahiert werden.

---

## 🚀 NÄCHSTE SCHRITTE

### Priorität 1: Werte extrahieren ⏳

**Ziel:** BWA-Werte aus Excel extrahieren und mit DRIVE vergleichen

**Methoden:**
1. Sheet-Daten vollständig parsen
2. Werte für direkte/indirekte Kosten extrahieren
3. Vergleich mit DRIVE-Berechnungen
4. Unterschiede identifizieren

### Priorität 2: Ausbildung-Position finden ⏳

**Ziel:** Prüfen ob "Ausbildung" oder "Trainingskosten" in Excel ist

**Methoden:**
1. Suche nach "Ausbildung" oder "Trainingskosten" in Excel
2. Welche Werte sind in dieser Position?
3. Vergleich mit 411xxx

---

## 📊 STATUS

- ✅ Excel-Datei analysiert (ZIP-Format)
- ✅ Shared Strings extrahiert
- ✅ BWA-relevante Begriffe identifiziert
- ⏳ Sheet-Daten noch nicht vollständig geparst
- ⏳ Werte noch nicht extrahiert
- ⏳ Vergleich mit DRIVE noch nicht durchgeführt

---

## 🔧 TOOLS

**Analyse-Script:**
```bash
cd /opt/greiner-portal
python3 scripts/globalcube_explorer.py
```

**Excel-Datei:**
- `/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx`

---

**Nächster Schritt:** Sheet-Daten vollständig parsen und Werte extrahieren.
