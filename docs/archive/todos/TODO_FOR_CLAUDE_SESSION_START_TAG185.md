# TODO für Claude - Session Start TAG 185

**Datum:** Nach Buchhaltung Besprechung  
**Status:** ⏳ Warte auf Ergebnisse der Besprechung

---

## 📋 ÜBERGABE VON TAG 184

### Was wurde erreicht:
- ✅ Excel-Struktur für alle Standorte verstanden
- ✅ BWA-Werte extrahiert und mit DRIVE verglichen
- ✅ Fertigmachen Differenz erklärt (Excel summiert DEG+Landau)
- ✅ Kontenanalyse durchgeführt
- ✅ Dokumentation für Buchhaltung erstellt

### Wichtigste Erkenntnis:
**Excel Landau Variable Kosten summiert fälschlicherweise DEG + Landau!**
- Excel: 7.043,73 € (DEG + Landau)
- DRIVE: 6.173,95 € (nur Landau)
- **DRIVE Filter ist korrekt - keine Änderungen nötig!**

---

## ⏳ OFFENE FRAGEN (Warte auf Buchhaltung)

### 1. Landau Variable Kosten (-12,35%)
- **Frage:** Warum summiert Excel DEG + Landau?
- **Christian prüft:**
  - GlobalCube Portal Filter-Einstellungen
  - Konten 494021, 497061, 497221
  - Konten-Mapping

### 2. DEG Einsatzwerte (0,32%)
- **Frage:** Welche Konten fehlen in Excel?
- **Christian prüft:**
  - Excel vs. DRIVE Konten-Vergleich

### 3. Indirekte Kosten (DEG 1,87%, LAN 2,23%)
- **Frage:** Warum verwendet Excel andere Positionen als DRIVE?
- **Christian prüft:**
  - Excel "Kalk. Kosten" vs. DRIVE Standard-Filter
  - Excel "Indirekte Kosten" vs. DRIVE Standard-Filter

---

## 🚀 NÄCHSTE SCHRITTE (Nach Buchhaltung Besprechung)

### Priorität HOCH:
1. ⏳ **Ergebnisse der Buchhaltung Besprechung**
   - Was hat Christian herausgefunden?
   - Gibt es neue Erkenntnisse?
   - Sollen DRIVE Filter angepasst werden?

2. ⏳ **GlobalCube Portal Filter prüfen**
   - Wenn Christian Filter-Einstellungen gefunden hat
   - Portal-Reports analysieren

### Priorität MITTEL:
3. ⏳ **Konten-Mapping analysieren**
   - Wenn Christian Mapping-Logik gefunden hat
   - GlobalCube Struktur-Dateien analysieren

4. ⏳ **YTD-Differenzen analysieren**
   - Wenn Monat-Differenzen geklärt sind
   - YTD-Berechnung prüfen

### Priorität NIEDRIG:
5. ⏳ **GlobalCube Scraper Auth-Problem beheben**
   - Wenn Portal-Filter verstanden
   - Für automatische Extraktion

---

## 📁 WICHTIGE DATEIEN

### Dokumentation (Windows Sync):
- `ABWEICHUNGEN_UEBERSICHT_TAG184.md` - Vollständige Übersicht
- `ABWEICHUNGEN_KOMPAKT_TAG184.md` - Kompakte Übersicht
- `EMPFEHLUNGEN_FUER_BUCHHALTUNG_TAG184.md` - Empfehlungen für Christian
- `FERTIGMACHEN_LOESUNG_FINAL_TAG184.md` - Fertigmachen Differenz-Analyse
- `EXCEL_ANALYSE_FINAL_TAG184.md` - Excel-Analyse Zusammenfassung

### Scripts:
- `scripts/parse_excel_landau_final.py` - Landau Excel Parser
- `scripts/parse_excel_deg_hyu.py` - DEG/HYU Excel Parser
- `scripts/parse_excel_gesamtbetrieb.py` - Gesamtbetrieb Excel Parser
- `scripts/analyse_variable_kosten_landau.py` - Variable Kosten Konten-Analyse
- `scripts/analyse_fertigmachen_differenz.py` - Fertigmachen Differenz-Analyse

---

## 💡 ERINNERUNG

**DRIVE Filter ist korrekt!**
- Keine Änderungen an DRIVE Code nötig
- Excel zeigt falsche Werte (summiert DEG+Landau)
- Warte auf Ergebnisse der Buchhaltung Besprechung

---

*Erstellt: TAG 184 | Autor: Claude AI*
