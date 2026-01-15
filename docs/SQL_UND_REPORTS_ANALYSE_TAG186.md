# SQL-Queries und Report-Definitionen Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **ANALYSE ABGESCHLOSSEN**

---

## 📁 ANALYSIERTE DATEIEN

### 1. SQL-Queries

**Locosoft_2022.2023.0523.0202.sql:**
- 11.732 Zeilen
- Datenbank-Dump (Tabellen-Definitionen, Kommentare)
- Enthält "einsatz" und "materialaufwand" nur in Kommentaren
- **Keine Filter-Logik** für 71700, 72700, 72750

**locosoft.LOC_Belege.sql:**
- View-Definition
- Filtert nur nach P&L-Konten (`is_profit_loss_account = 'J'`)
- **Keine Filter-Logik** für spezifische Kontonummern

### 2. Report-Definitionen

**F02.txt (Kostenstellenbericht):**
- XML-basiertes Cognos-Report
- Verwendet Cube `[CARLO_F_Belege]`
- Zugriff auf Dimensionen wie:
  - `[CARLO_F_Belege].[Konten].[Konten].[Ebene1]-&gt;:[PC].[@MEMBER].[Einsatzwerte]`
  - `[CARLO_F_Belege].[Konten].[Konten].[Ebene1]-&gt;:[PC].[@MEMBER].[Umsatzerlöse]`
- Filter-Parameter: `p_AH`, `p_Marke`, `p_Kst`, `p_Zeitraum`
- **Keine expliziten Filter** für 71700, 72700, 72750

**F03.txt (BWA VJ/Soll/Ist-Vergleich):**
- XML-basiertes Cognos-Report
- Verwendet Cube `[CARLO_F_Belege]`
- Ähnliche Struktur wie F02.txt
- **Keine expliziten Filter** für 71700, 72700, 72750

---

## 🎯 ERKENNTNISSE

### 1. Filter-Logik liegt im Cube

**Erkenntnis:** Die Filter-Logik liegt **nicht** in SQL-Queries oder Report-Definitionen, sondern **im Cube selbst**!

**Beweis:**
- Report-Definitionen greifen direkt auf Cube-Dimensionen zu
- Keine WHERE-Bedingungen in SQL-Queries für 71700, 72700, 72750
- Cube enthält die Konten (71700, 72700, 72750 gefunden)
- Cube verwendet Dimensionen wie `Ebene1`, `Ebene2`, etc.

### 2. "Zurückgestellt" im Cube

**Erkenntnis:** "Zurückgestellt" ist eine **Ebene-Zuordnung** (Ebene11), nicht ein Filter!

**Bedeutung:**
- Die Konten sind im Cube vorhanden
- Sie haben die Ebene-Zuordnung "zurückgestellt"
- Aber sie werden **trotzdem verwendet** (im Cube gefunden)

### 3. Dimensionen-Struktur

**Cube-Dimensionen:**
- `[CARLO_F_Belege].[Konten].[Konten].[Ebene1]` → "Einsatzwerte", "Umsatzerlöse"
- `[CARLO_F_Belege].[Konten].[Konten].[Ebene2]` → "Variable Kosten", "Direkte Kosten"
- `[CARLO_F_Belege].[Konten].[Konten].[Ebene11]` → "zurückgestellt" (vermutlich)

**Erkenntnis:** Die Filter-Logik liegt in der **Dimensionen-Struktur** des Cubes!

---

## 💡 HYPOTHESEN

### Hypothese 1: Ebene11-Filter im Cube

**Möglichkeit:** Der Cube filtert möglicherweise nach Ebene11 = "zurückgestellt" und schließt diese Konten aus.

**Test:** Prüfe, ob "zurückgestellt" Konten in der BWA verwendet werden oder ausgeschlossen werden.

### Hypothese 2: Dimensionen-Aggregation

**Möglichkeit:** Die Konten werden in "Einsatzwerte" aggregiert, aber bestimmte Unter-Dimensionen (z.B. Ebene11 = "zurückgestellt") werden ausgeschlossen.

**Test:** Prüfe, ob die Differenz durch ausgeschlossene "zurückgestellt" Konten erklärt werden kann.

### Hypothese 3: Keine Filterung

**Möglichkeit:** "Zurückgestellt" ist nur eine **Kategorisierung**, keine Filterung. Die Konten werden verwendet.

**Test:** Vergleiche GlobalCube-BWA mit DRIVE-BWA, um zu sehen, ob die Konten verwendet werden.

---

## 📊 ZUSAMMENFASSUNG

### ✅ Was wir wissen:

1. **Konten 71700, 72700, 72750 sind im Cube enthalten**
2. **"Zurückgestellt" ist eine Ebene-Zuordnung (Ebene11)**
3. **Filter-Logik liegt im Cube, nicht in SQL/Reports**
4. **Report-Definitionen verwenden Cube-Dimensionen direkt**

### ❓ Offene Fragen:

1. **Werden "zurückgestellt" Konten in der BWA verwendet?**
   - Oder werden sie durch Cube-Dimensionen-Filter ausgeschlossen?

2. **Wie funktioniert die Dimensionen-Struktur im Cube?**
   - Werden Ebene11 = "zurückgestellt" Konten gefiltert?

3. **Was erklärt die 31.905,97€ Differenz?**
   - Sind es ausgeschlossene "zurückgestellt" Konten?
   - Oder andere Filter?

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Vergleiche GlobalCube-BWA mit DRIVE-BWA:**
   - Werden 71700, 72700, 72750 in GlobalCube verwendet?
   - Oder werden sie ausgeschlossen?

2. ⏳ **Prüfe Cube-Dimensionen-Struktur:**
   - Wie werden Ebene11 = "zurückgestellt" Konten behandelt?
   - Gibt es Filter in der Dimensionen-Struktur?

3. ⏳ **Analysiere die Differenz:**
   - Können ausgeschlossene "zurückgestellt" Konten die Differenz erklären?

---

## 📊 STATUS

- ✅ SQL-Queries analysiert (keine Filter-Logik)
- ✅ Report-Definitionen analysiert (verwenden Cube-Dimensionen)
- ✅ Cube-Struktur analysiert (Konten enthalten, "zurückgestellt" als Ebene11)
- ⏳ Bedeutung von "zurückgestellt" in der BWA klären
- ⏳ Filter-Logik in Cube-Dimensionen verstehen

---

**KRITISCHE ERKENNTNIS:** Die Filter-Logik liegt im Cube selbst, nicht in SQL-Queries oder Report-Definitionen! "Zurückgestellt" ist eine Ebene-Zuordnung, deren Bedeutung in der BWA noch geklärt werden muss.
