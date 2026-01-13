# Excel-Analyse Zusammenfassung - TAG 184

**Datum:** 2026-01-13  
**Status:** ✅ Excel-Struktur analysiert, Werte-Interpretation benötigt weitere Arbeit

---

## 📋 GEFUNDENE EXCEL-DATEI

**Datei:** `/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx`  
**Größe:** 34 KB  
**Format:** Excel OpenXML (ZIP)  
**Sheet:** Seite1_1

---

## 🔍 EXCEL-STRUKTUR

### Header-Struktur (Zeile 6):
- Spalte 1: "%"
- Spalte 3: "Dez./2024" (Vorjahr Monat)
- Spalte 5: "Trend"
- Spalte 7: "Dez./2024" (Vorjahr Kumuliert?)
- Spalte 9: "Abw."
- Spalte 10: "% Abw."
- Spalte 12: "Neuwagen Stk."

### Daten-Zeilen:
- **Zeile 7:** "Einsatzwerte" - Werte: 42, 33, 9 (wahrscheinlich Stückzahlen oder Metriken)
- **Zeile 8:** "Bruttoertrag" - Werte: 39, 37, 2
- **Zeile 10:** "1 - NW" - Werte: 2190825.64, 1813438.59, 377387.05 (Euro-Werte!)

**Erkenntnis:** Die Excel-Datei enthält sowohl Stückzahlen als auch Euro-Werte, aber die Struktur ist komplexer als erwartet.

---

## ⚠️ PROBLEM: WERTE-INTERPRETATION

**Gefundene Werte:**
- Einsatzwerte: 42, 33 (nicht in Euro)
- Bruttoertrag: 39, 37 (nicht in Euro)
- Variable Kosten: 900.82 (möglicherweise Euro?)
- Direkte Kosten: 638.93, 4132.42 (möglicherweise Euro?)
- Indirekte Kosten: 189141.46 (möglicherweise Euro?)
- Betriebsergebnis: 51850.0 (möglicherweise Euro?)

**Problem:**
- Die Werte passen nicht zu DRIVE-Werten
- Excel-Werte sind viel kleiner oder in einem anderen Format
- Mögliche Ursachen:
  1. Werte sind in Tausenden
  2. Werte sind für einen anderen Standort/Zeitraum
  3. Excel-Struktur ist anders als erwartet

---

## 📊 VERGLEICH MIT DRIVE (Landau, Dez 2025)

**DRIVE-Werte:**
- Umsatz: 320.120,53 €
- Einsatz: 270.455,29 €
- DB1: 49.665,24 €
- Variable Kosten: 6.173,95 €
- Direkte Kosten: 38.723,80 €
- Indirekte Kosten: 39.304,39 €
- Betriebsergebnis: -34.536,90 €

**Excel-Werte (interpretiert):**
- Einsatzwerte: 42,00 (passt nicht!)
- Bruttoertrag: 6.559,63 (passt nicht!)
- Variable Kosten: 900,82 (passt nicht!)
- Direkte Kosten: 638,93 (passt nicht!)
- Betriebsergebnis: 51.850,00 (passt nicht!)

**Differenz:** Alle Werte passen nicht - Excel-Struktur muss anders interpretiert werden.

---

## 💡 MÖGLICHE LÖSUNGEN

### 1. Excel-Struktur genauer analysieren
- Welche Spalten enthalten welche Werte?
- Gibt es mehrere Sheets?
- Sind die Werte in Tausenden?

### 2. Alternative Excel-Dateien suchen
- Gibt es andere BWA-Excel-Dateien?
- Gibt es CSV-Exports?

### 3. Direkt aus Portal scrapen
- Nach Auth-Fix: Portal-Reports direkt scrapen
- Enthält exakte Werte ohne Interpretation

### 4. HAR-Dateien verwenden
- Bereits vorhandene HAR-Analysen nutzen
- Enthalten tatsächliche Portal-Werte

---

## 🚀 NÄCHSTE SCHRITTE

### Priorität HOCH:
1. ⏳ **Excel-Struktur vollständig verstehen**
   - Alle Spalten identifizieren
   - Werte-Format verstehen (Tausenden? Prozent? Anderes?)

2. ⏳ **Alternative Datenquellen nutzen**
   - HAR-Dateien analysieren (bereits vorhanden)
   - Portal-Reports scrapen (nach Auth-Fix)

### Priorität MITTEL:
3. ⏳ **Weitere Excel-Dateien suchen**
   - Gibt es andere BWA-Exports?
   - Gibt es CSV-Versionen?

---

## 📁 GENERIERTE DATEIEN

- `/opt/greiner-portal/docs/globalcube_analysis/excel_bwa_values_tag184.json`
- `/opt/greiner-portal/scripts/parse_globalcube_excel_complete.py`
- `/opt/greiner-portal/scripts/vergleiche_excel_drive_bwa.py`

---

## 💡 FAZIT

**Was funktioniert:**
- ✅ Excel-Datei gefunden und analysiert
- ✅ Struktur teilweise verstanden
- ✅ Shared Strings extrahiert

**Was noch fehlt:**
- ⏳ Vollständige Werte-Interpretation
- ⏳ Korrekte Zuordnung von Spalten zu Werten
- ⏳ Vergleich mit DRIVE (nach korrekter Interpretation)

**Empfehlung:**
- **Nächster Schritt:** HAR-Dateien analysieren (bereits vorhanden, enthalten echte Werte)
- **Alternativ:** Excel-Struktur vollständig reverse-engineeren

---

*Erstellt: TAG 184 | Autor: Claude AI*
