# Einsatzwerte Filter-Logik Analyse - Ergebnisse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **ANALYSE ABGESCHLOSSEN**

---

## 🎯 ERKENNTNISSE

### 1. "Blank" Konten werden bereits erfasst ✅

**717001, 727001, 727501 werden ALLE durch die aktuelle Filter-Logik erfasst!**

| Konto | Gesamt | Erfasst | Status |
|-------|--------|---------|-------|
| 717001 | 16,390.27 € | 16,390.27 € | ✅ 100% erfasst |
| 727001 | 71,729.12 € | 71,729.12 € | ✅ 100% erfasst |
| 727501 | -12,608.04 € | -12,608.04 € | ✅ 100% erfasst |

**Grund:**
- Alle haben **6. Ziffer = '1'**
- Werden durch Filter erfasst:
  - Deggendorf Opel: `6. Ziffer='1' AND subsidiary=1 AND branch=1`
  - Deggendorf Hyundai: `6. Ziffer='1' AND subsidiary=2 AND branch=2`

**❌ "Blank" Konten sind NICHT das Problem!**

---

### 2. Ausgeschlossene Konten haben 6. Ziffer = '2'

**Top 30 ausgeschlossene Konten (>10.000€):**

| Konto | Wert | subsidiary | branch | 6.Ziffer |
|-------|------|------------|--------|----------|
| 718002 | -69,544.71 € | 1 | 1 | 2 |
| 711512 | -51,193.05 € | 1 | 1 | 2 |
| 711202 | 36,816.63 € | 1 | 1 | 2 |
| 721202 | -31,437.14 € | 1 | 1 | 2 |
| ... | ... | ... | ... | ... |

**Gemeinsamkeiten:**
- Alle haben `subsidiary=1` (Stellantis)
- Alle haben `branch=1` (Deggendorf)
- Alle haben `6. Ziffer='2'`

**Warum ausgeschlossen?**
- Filter für Deggendorf Opel: `6. Ziffer='1' OR (74xxxx AND branch=1) AND subsidiary=1 AND branch != 3`
- Konten mit `6. Ziffer='2'` werden **nicht erfasst** (außer 74xxxx mit branch=1)

**Summe ausgeschlossene Konten:** -156,681.93 €

---

### 3. MASSIVE Differenz zu GlobalCube ⚠️

**Gesamtbetrieb Einsatzwerte YTD (Jan-Dez 2025):**

| Quelle | Wert |
|--------|------|
| **DRIVE (mit aktueller Logik)** | **26,023,519.41 €** |
| **GlobalCube** | **9,191,864.00 €** |
| **Differenz** | **+16,831,655.41 €** |

**Zerlegung nach Standort:**

| Standort | DRIVE | Filter |
|----------|-------|--------|
| Deggendorf Opel | 13,409,446.48 € | `6.Ziffer='1' OR (74xxxx AND branch=1) AND subsidiary=1 AND branch != 3` |
| Landau | 3,655,537.42 € | `branch=3 AND subsidiary=1` |
| Deggendorf Hyundai | 8,958,535.51 € | `6.Ziffer='1' AND subsidiary=2` |
| **Summe** | **26,023,519.41 €** | |

---

## 🔍 PROBLEM-ANALYSE

### Warum ist die Differenz so groß?

**Mögliche Ursachen:**

1. **Filter-Logik ist falsch:**
   - Aktuelle Logik erfasst zu viele Konten
   - GlobalCube verwendet möglicherweise andere Filter

2. **Konten-Kategorisierung:**
   - GlobalCube schließt möglicherweise bestimmte Konten aus
   - Oder kategorisiert sie anders (z.B. "Neutrales Ergebnis")

3. **Zeitraum-Filter:**
   - GlobalCube verwendet möglicherweise andere Zeiträume
   - Oder andere Datums-Logik

4. **G&V-Filter:**
   - Beide verwenden `posting_text NOT LIKE '%%G&V-Abschluss%%'`
   - Aber möglicherweise andere G&V-Buchungen?

---

## 📊 WICHTIGE ERKENNTNISSE

### ✅ Was wir wissen:

1. **"Blank" Konten (717001, 727001, 727501) werden bereits erfasst**
   - Sie sind NICHT das Problem
   - Sie haben 6. Ziffer='1' und werden korrekt eingeschlossen

2. **Ausgeschlossene Konten haben 6. Ziffer='2'**
   - Summe: -156,681.93 €
   - Aber die Gesamtdifferenz ist 16,831,655.41 €
   - **Die ausgeschlossenen Konten erklären NICHT die Differenz!**

3. **Die aktuelle Filter-Logik erfasst 26 Mio. €, GlobalCube zeigt 9 Mio. €**
   - **Differenz: +16.8 Mio. €**
   - Das ist eine **MASSIVE Übererfassung** in DRIVE!

### ❓ Offene Fragen:

1. **Warum zeigt DRIVE 26 Mio. €, GlobalCube nur 9 Mio. €?**
   - Welche Konten werden von GlobalCube ausgeschlossen?
   - Gibt es eine andere Filter-Logik?

2. **Sind die ausgeschlossenen Konten (6. Ziffer='2') korrekt?**
   - Sollten sie erfasst werden?
   - Oder sind sie korrekt ausgeschlossen?

3. **Gibt es andere Filter, die GlobalCube verwendet?**
   - Z.B. bestimmte Konten-Bereiche ausschließen?
   - Oder andere Kategorisierungen?

---

## 🎯 NÄCHSTE SCHRITTE

1. **Prüfe, welche Konten GlobalCube tatsächlich erfasst:**
   - Vergleiche Konten-Listen zwischen DRIVE und GlobalCube
   - Identifiziere, welche Konten GlobalCube ausschließt

2. **Analysiere die 16.8 Mio. € Differenz:**
   - Welche Konten tragen zur Übererfassung bei?
   - Gibt es Muster (z.B. bestimmte Konten-Bereiche)?

3. **Prüfe, ob die Filter-Logik korrekt ist:**
   - Sollten Konten mit 6. Ziffer='2' erfasst werden?
   - Oder gibt es andere Filter-Kriterien?

---

**KRITISCHE ERKENNTNIS:** Die "blank" Konten sind NICHT das Problem! Die aktuelle Filter-Logik erfasst sie bereits korrekt. Das Problem ist eine **massive Übererfassung** von 16.8 Mio. € in DRIVE gegenüber GlobalCube.
