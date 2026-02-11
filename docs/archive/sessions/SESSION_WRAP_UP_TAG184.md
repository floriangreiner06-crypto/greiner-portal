# Session Wrap-Up TAG 184

**Datum:** 2026-01-13  
**Dauer:** Vollständige Excel-Analyse aller Standorte + Kontenanalyse

---

## ✅ ERREICHTE ZIELE

### 1. Excel-Struktur für alle Standorte verstanden ✅
- **Landau:** Vollständige Struktur analysiert
- **DEG:** Vollständige Struktur analysiert
- **HYU:** Vollständige Struktur analysiert
- **Gesamtbetrieb:** Vollständige Struktur analysiert

### 2. BWA-Werte extrahiert und mit DRIVE verglichen ✅
- Alle 4 Excel-Dateien analysiert
- Werte extrahiert und mit DRIVE API verglichen
- Abweichungen identifiziert und dokumentiert

### 3. Fertigmachen Differenz erklärt ✅
- **Problem:** Excel Landau Variable Kosten = 7.043,73 € vs. DRIVE 6.173,95 € (-12,35%)
- **Lösung:** Excel summiert DEG + Landau (alle branches), nicht nur Landau
- **Erkenntnis:** Excel zeigt Konten von DEG (branch=1) in Landau Report

### 4. Kontenanalyse durchgeführt ✅
- DRIVE Variable Kosten Konten extrahiert (6.173,95 € - perfekt!)
- Excel "Fertigmachen" Konten identifiziert
- Differenz erklärt: Excel enthält zusätzlich Konten 494021, 497061, 497221 (alle branches)

---

## 📊 ERGEBNISSE

### Excel vs. DRIVE Vergleich (Dezember 2025):

**HYU (Beste Übereinstimmung):**
- 6 von 7 Positionen perfekt (0% Differenz)
- 1 Position fast perfekt (0,44% Differenz)

**Gesamtbetrieb:**
- 6 von 7 Positionen perfekt oder fast perfekt (<1% Differenz)

**Landau:**
- 5 von 7 Positionen perfekt (0% Differenz)
- Variable Kosten: -12,35% (Excel summiert DEG+Landau) - **ERKLÄRT**

**DEG:**
- 4 von 7 Positionen perfekt (0% Differenz)
- Alle anderen <5% Differenz

### Indirekte Kosten Position (standort-spezifisch):
- **Gesamtbetrieb:** "Kalk. Kosten"
- **Landau:** "Indirekte Kosten" (Spalte B)
- **DEG:** "Kalk. Kosten"
- **HYU:** "Gewerbesteuer"

---

## 🔍 WICHTIGSTE ERKENNTNISSE

### 1. Excel Landau Variable Kosten summiert DEG + Landau
- **Excel:** Summiert alle branches für subsidiary=1
- **DRIVE:** Filtert korrekt nur Landau (branch=3)
- **Ergebnis:** Excel zeigt falsche Werte, DRIVE Filter ist korrekt ✅

### 2. Excel "Fertigmachen" Filter:
```
491xx-497xx mit 6. Ziffer='2' (alle branches, subsidiary=1)
+ Konten 494021, 497061, 497221 (alle branches, subsidiary=1)
= 7.048,89 € (Differenz zu Excel: 5,16 € = 0,07%) ✅
```

### 3. Indirekte Kosten Position ist standort-spezifisch
- Jeder Standort hat eine andere Excel-Position für Indirekte Kosten
- DRIVE verwendet Standard-Filter (konsistent)

---

## 📁 ERSTELLTE DATEIEN

### Dokumentation:
- `/opt/greiner-portal/docs/globalcube_analysis/ABWEICHUNGEN_UEBERSICHT_TAG184.md`
- `/opt/greiner-portal/docs/globalcube_analysis/ABWEICHUNGEN_KOMPAKT_TAG184.md`
- `/opt/greiner-portal/docs/globalcube_analysis/EMPFEHLUNGEN_FUER_BUCHHALTUNG_TAG184.md`
- `/opt/greiner-portal/docs/globalcube_analysis/FERTIGMACHEN_LOESUNG_FINAL_TAG184.md`
- `/opt/greiner-portal/docs/globalcube_analysis/EXCEL_ANALYSE_FINAL_TAG184.md`
- `/opt/greiner-portal/docs/globalcube_analysis/EXCEL_ALLE_STANDORTE_ERGEBNISSE_TAG184.md`
- `/opt/greiner-portal/docs/globalcube_analysis/KONTENANALYSE_ERGEBNISSE_TAG184.md`

### Scripts:
- `/opt/greiner-portal/scripts/parse_excel_landau_final.py`
- `/opt/greiner-portal/scripts/parse_excel_deg_hyu.py`
- `/opt/greiner-portal/scripts/parse_excel_gesamtbetrieb.py`
- `/opt/greiner-portal/scripts/analyse_variable_kosten_landau.py`
- `/opt/greiner-portal/scripts/analyse_fertigmachen_differenz.py`

### JSON-Daten:
- `/opt/greiner-portal/docs/globalcube_analysis/excel_landau_final_tag184.json`
- `/opt/greiner-portal/docs/globalcube_analysis/excel_deg_tag184.json`
- `/opt/greiner-portal/docs/globalcube_analysis/excel_hyu_tag184.json`
- `/opt/greiner-portal/docs/globalcube_analysis/excel_gesamtbetrieb_tag184.json`
- `/opt/greiner-portal/docs/globalcube_analysis/kontenanalyse_variable_kosten_landau_tag184.json`
- `/opt/greiner-portal/docs/globalcube_analysis/fertigmachen_differenz_analyse_tag184.json`

### Windows Sync:
- `/mnt/greiner-portal-sync/docs/ABWEICHUNGEN_UEBERSICHT_TAG184.md`
- `/mnt/greiner-portal-sync/docs/ABWEICHUNGEN_KOMPAKT_TAG184.md`
- `/mnt/greiner-portal-sync/docs/EMPFEHLUNGEN_FUER_BUCHHALTUNG_TAG184.md`
- `/mnt/greiner-portal-sync/docs/FERTIGMACHEN_LOESUNG_FINAL_TAG184.md`
- `/mnt/greiner-portal-sync/docs/EXCEL_ANALYSE_FINAL_TAG184.md`

---

## ⏳ OFFENE FRAGEN

### 1. Warum summiert Excel nur bei Variable Kosten DEG + Landau?
- **Frage:** Warum nicht bei Umsatz, Einsatz, DB1, Direkte Kosten?
- **Mögliche Ursachen:** Portal-Filter-Fehler, Report-Einstellungen, Mapping-Logik

### 2. Warum werden nur Konten 494021, 497061, 497221 zu "Fertigmachen" zugeordnet?
- **Frage:** Gibt es eine Mapping-Logik?
- **Mögliche Ursachen:** GlobalCube Struktur-Dateien, Konten-Typen, Filter-Logik

### 3. YTD-Differenzen größer als Monat-Differenzen
- **Frage:** Warum sind YTD-Differenzen größer?
- **Mögliche Ursachen:** YTD-Berechnung unterschiedlich, kumulative Fehler

---

## 🚀 NÄCHSTE SCHRITTE (TAG 185)

### Priorität HOCH:
1. ⏳ **Buchhaltung Besprechung**
   - Abweichungen mit Christian besprechen
   - GlobalCube Portal Filter-Einstellungen prüfen
   - Konten 494021, 497061, 497221 analysieren

2. ⏳ **GlobalCube Portal Filter prüfen**
   - Warum summiert Excel nur bei Variable Kosten DEG + Landau?
   - Filter-Einstellungen für Landau Variable Kosten prüfen

### Priorität MITTEL:
3. ⏳ **Konten-Mapping analysieren**
   - Warum werden nur bestimmte Konten zu "Fertigmachen" zugeordnet?
   - GlobalCube Struktur-Dateien analysieren

4. ⏳ **YTD-Differenzen analysieren**
   - Warum sind YTD-Differenzen größer als Monat-Differenzen?
   - YTD-Berechnung prüfen

### Priorität NIEDRIG:
5. ⏳ **GlobalCube Scraper Auth-Problem beheben**
   - Nach Buchhaltung Besprechung
   - Wenn Portal-Filter verstanden

---

## 💡 FAZIT

**Was funktioniert:**
- ✅ Excel-Struktur für alle Standorte vollständig verstanden
- ✅ BWA-Werte extrahiert und mit DRIVE verglichen
- ✅ Fertigmachen Differenz erklärt (Excel summiert DEG+Landau)
- ✅ Kontenanalyse durchgeführt

**Was noch offen ist:**
- ⏳ Warum summiert Excel nur bei Variable Kosten DEG + Landau?
- ⏳ Warum werden nur bestimmte Konten zu "Fertigmachen" zugeordnet?
- ⏳ YTD-Differenzen größer als Monat-Differenzen

**Empfehlung:**
- ✅ **DRIVE Filter ist korrekt** - keine Änderungen nötig
- ⚠️ **Excel zeigt falsche Werte** - Portal-Filter prüfen
- 💡 **Buchhaltung Besprechung** - Abweichungen mit Christian besprechen

---

*Erstellt: TAG 184 | Autor: Claude AI*
