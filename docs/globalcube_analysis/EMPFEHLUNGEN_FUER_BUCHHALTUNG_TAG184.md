# Empfehlungen für Buchhaltung - Abweichungen Analyse - TAG 184

**Datum:** 2026-01-13  
**An:** Christian (Buchhaltung)  
**Betreff:** Abweichungen Excel vs. DRIVE - Was prüfen?

---

## 🎯 ÜBERSICHT DER ABWEICHUNGEN

### ❌ Landau - Variable Kosten: -12,35% (-869,78 €)
### ⚠️ DEG - Betriebsergebnis: 4,57% (-4.690,90 €)
### ⚠️ DEG - Bruttoertrag: -2,02% (-3.222,37 €)
### ⚠️ Landau - Indirekte Kosten: 2,23% (858,78 €)

---

## 📋 EMPFEHLUNGEN FÜR CHRISTIAN

### 1. ❌ Landau - Variable Kosten: -12,35% (-869,78 €)

**Was prüfen:**

#### A) Excel/GlobalCube Portal Filter-Einstellungen
- **Frage:** Warum summiert Excel Landau Variable Kosten DEG + Landau (alle branches)?
- **Prüfen:**
  - GlobalCube Portal Report-Einstellungen für Landau Variable Kosten
  - Filter-Einstellungen im Portal (branch-Filter)
  - Warum werden Konten von DEG (branch=1) in Landau Report angezeigt?
- **Erwartung:** Excel sollte nur Landau (branch=3) enthalten, nicht DEG (branch=1)

#### B) Konten 494021, 497061, 497221
- **Frage:** Warum enthält Excel "Fertigmachen" diese 3 Konten?
- **Prüfen:**
  - Welche Konten-Typen sind das? (Kontenplan prüfen)
  - Gehören diese Konten zu DEG oder Landau?
  - Warum werden sie in Excel Landau "Fertigmachen" angezeigt?
- **Bekannt:**
  - 494021: 2.458,40 € (branch=1 = DEG)
  - 497061: 132,50 € (branch=1 = DEG)
  - 497221: 239,61 € (branch=3 = Landau)
  - **Summe:** 2.830,51 €

#### C) GlobalCube Mapping-Logik
- **Frage:** Gibt es eine Mapping-Logik die diese Konten zu "Fertigmachen" zuordnet?
- **Prüfen:**
  - GlobalCube Struktur-Dateien (`Kontenrahmen.csv`, `Struktur_GuV.xml`)
  - Mapping zwischen Konten und Excel-Positionen
  - Warum werden nur diese 3 Konten mit 6. Ziffer='1' zu "Fertigmachen" zugeordnet?

**Empfehlung:**
- ✅ **DRIVE Filter ist korrekt** (nur Landau, branch=3)
- ⚠️ **Excel zeigt falsche Werte** (summiert DEG + Landau)
- 💡 **Prüfe GlobalCube Portal Filter-Einstellungen** - Warum summiert Excel nur bei Variable Kosten?

---

### 2. ⚠️ DEG - Betriebsergebnis: 4,57% (-4.690,90 €)

**Was prüfen:**

#### A) Einsatzwerte Differenz (0,32% = 3.222,37 €)
- **Frage:** Warum zeigt Excel 997.174,42 € statt DRIVE 1.000.396,79 €?
- **Prüfen:**
  - Welche Konten fehlen in Excel oder sind in DRIVE zusätzlich?
  - Gibt es Konten die Excel nicht zählt?
  - Filter-Unterschiede zwischen Excel und DRIVE?

#### B) Indirekte Kosten Differenz (1,87% = 1.468,53 €)
- **Frage:** Warum zeigt Excel 78.730,35 € statt DRIVE 80.198,88 €?
- **Prüfen:**
  - Excel verwendet "Kalk. Kosten" = 78.730,35 €
  - DRIVE verwendet Standard-Indirekte Kosten Filter = 80.198,88 €
  - Welche Konten fehlen in Excel "Kalk. Kosten"?
  - Gibt es Konten die DRIVE zählt, aber Excel nicht?

#### C) Summe der Differenzen
- **Frage:** Erklärt die Summe der kleinen Differenzen das Betriebsergebnis?
- **Prüfen:**
  - Einsatz: -3.222,37 €
  - DB1: -3.222,37 € (Folge von Einsatz)
  - Indirekte Kosten: -1.468,53 €
  - **Summe:** -7.913,27 € (aber Betriebsergebnis nur -4.690,90 €)
  - **→ Variable Kosten und Direkte Kosten passen perfekt (0% Differenz)**

**Empfehlung:**
- ⚠️ **Akzeptabel** - Summe kleiner Differenzen
- 💡 **Prüfe Einsatzwerte** - Warum 0,32% Differenz?
- 💡 **Prüfe Indirekte Kosten** - Warum verwendet Excel "Kalk. Kosten" statt Standard-Filter?

---

### 3. ⚠️ DEG - Bruttoertrag: -2,02% (-3.222,37 €)

**Was prüfen:**

#### A) Einsatzwerte Differenz (0,32% = 3.222,37 €)
- **Frage:** Warum zeigt Excel 997.174,42 € statt DRIVE 1.000.396,79 €?
- **Prüfen:**
  - Welche Konten fehlen in Excel?
  - Gibt es Konten die DRIVE zählt, aber Excel nicht?
  - Filter-Unterschiede?

**Empfehlung:**
- ⚠️ **Akzeptabel** - Kleine Differenz (0,32%)
- 💡 **Prüfe Einsatzwerte** - Welche Konten fehlen in Excel?

---

### 4. ⚠️ Landau - Indirekte Kosten: 2,23% (858,78 €)

**Was prüfen:**

#### A) Excel "Indirekte Kosten" vs. DRIVE Standard-Filter
- **Frage:** Warum zeigt Excel 38.445,61 € statt DRIVE 39.304,39 €?
- **Prüfen:**
  - Excel verwendet "Indirekte Kosten" (Spalte B, Zeile 33) = 38.445,61 €
  - DRIVE verwendet Standard-Indirekte Kosten Filter = 39.304,39 €
  - Welche Konten fehlen in Excel "Indirekte Kosten"?
  - Gibt es Konten die DRIVE zählt, aber Excel nicht?

#### B) Indirekte Kosten Filter-Unterschiede
- **Frage:** Gibt es Filter-Unterschiede zwischen Excel und DRIVE?
- **Prüfen:**
  - Excel "Indirekte Kosten" Position
  - DRIVE Standard-Indirekte Kosten Filter (KST 0, 424xx, 438xx, 498xx, 89xxxx)
  - Welche Konten werden unterschiedlich behandelt?

**Empfehlung:**
- ⚠️ **Akzeptabel** - Kleine Differenz (2,23%)
- 💡 **Prüfe Indirekte Kosten Position** - Welche Konten fehlen in Excel?

---

## 🔍 ALLGEMEINE PRÜFPUNKTE

### 1. Excel/GlobalCube Portal Filter-Einstellungen
- **Prüfen:** Sind die Filter-Einstellungen im Portal korrekt?
- **Besonders:** Warum summiert Excel nur bei Variable Kosten DEG + Landau?

### 2. Konten-Mapping
- **Prüfen:** Gibt es ein Mapping zwischen Konten und Excel-Positionen?
- **Besonders:** Warum werden nur bestimmte Konten (494021, 497061, 497221) zu "Fertigmachen" zugeordnet?

### 3. Branch-Filter
- **Prüfen:** Werden branch-Filter korrekt angewendet?
- **Besonders:** Warum zeigt Excel Landau Konten von DEG (branch=1)?

### 4. YTD-Berechnung
- **Prüfen:** Warum sind YTD-Differenzen größer als Monat-Differenzen?
- **Besonders:** Landau Variable Kosten YTD: -33,85% vs. Monat: -12,35%

---

## 📊 PRIORITÄTEN

### Priorität HOCH:
1. ⚠️ **Landau Variable Kosten** - Excel summiert DEG + Landau
   - Prüfe GlobalCube Portal Filter-Einstellungen
   - Prüfe warum Konten von DEG in Landau Report angezeigt werden

### Priorität MITTEL:
2. ⚠️ **DEG Einsatzwerte** - 0,32% Differenz
   - Prüfe welche Konten fehlen in Excel

3. ⚠️ **DEG Indirekte Kosten** - 1,87% Differenz
   - Prüfe warum Excel "Kalk. Kosten" verwendet statt Standard-Filter

4. ⚠️ **Landau Indirekte Kosten** - 2,23% Differenz
   - Prüfe welche Konten fehlen in Excel "Indirekte Kosten"

### Priorität NIEDRIG:
5. ⏳ **YTD-Differenzen** - Größer als Monat-Differenzen
   - Prüfe warum YTD-Differenzen größer sind

---

## 💡 FRAGEN FÜR CHRISTIAN

### 1. GlobalCube Portal
- **Frage:** Welche Filter-Einstellungen werden im Portal für Landau Variable Kosten verwendet?
- **Frage:** Warum summiert Excel nur bei Variable Kosten DEG + Landau, nicht bei anderen Positionen?

### 2. Konten-Mapping
- **Frage:** Gibt es ein Mapping zwischen Konten und Excel-Positionen?
- **Frage:** Warum werden nur bestimmte Konten (494021, 497061, 497221) zu "Fertigmachen" zugeordnet?

### 3. Konten-Typen
- **Frage:** Welche Konten-Typen sind 494021, 497061, 497221?
- **Frage:** Gehören diese Konten zu DEG oder Landau?

### 4. Excel-Export
- **Frage:** Wie werden Excel-Exports erstellt?
- **Frage:** Gibt es unterschiedliche Filter für verschiedene Positionen?

---

## 📁 ZUSÄTZLICHE INFORMATIONEN

### Für Christian verfügbar:
- ✅ Vollständige Abweichungen-Übersicht
- ✅ Konten-Analyse (Variable Kosten Landau)
- ✅ Excel-Struktur-Analyse (alle Standorte)
- ✅ Fertigmachen Differenz-Analyse

### Dateien im Windows Sync:
- `/mnt/greiner-portal-sync/docs/ABWEICHUNGEN_UEBERSICHT_TAG184.md`
- `/mnt/greiner-portal-sync/docs/ABWEICHUNGEN_KOMPAKT_TAG184.md`
- `/mnt/greiner-portal-sync/docs/FERTIGMACHEN_LOESUNG_FINAL_TAG184.md`
- `/mnt/greiner-portal-sync/docs/EXCEL_ANALYSE_FINAL_TAG184.md`

---

## 🎯 ZUSAMMENFASSUNG FÜR CHRISTIAN

**Hauptproblem:**
- Excel Landau Variable Kosten summiert fälschlicherweise DEG + Landau
- DRIVE Filter ist korrekt (nur Landau, branch=3)
- **Keine DRIVE-Änderungen nötig!**

**Was prüfen:**
1. ⚠️ **GlobalCube Portal Filter-Einstellungen** - Warum summiert Excel DEG + Landau?
2. ⚠️ **Konten 494021, 497061, 497221** - Warum werden sie zu "Fertigmachen" zugeordnet?
3. ⚠️ **DEG Einsatzwerte** - Welche Konten fehlen in Excel?
4. ⚠️ **Indirekte Kosten** - Warum verwendet Excel andere Positionen als DRIVE?

**Empfehlung:**
- ✅ **DRIVE Filter ist korrekt** - keine Änderungen nötig
- ⚠️ **Excel zeigt falsche Werte** - Portal-Filter prüfen
- 💡 **Fokus auf Landau Variable Kosten** - Größte Abweichung (-12,35%)

---

*Erstellt: TAG 184 | Autor: Claude AI*
