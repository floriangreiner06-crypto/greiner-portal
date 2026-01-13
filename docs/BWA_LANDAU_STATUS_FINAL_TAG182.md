# BWA Landau - Status Final (TAG 182)

**Datum:** 2026-01-12  
**Status:** ⚠️ Verbleibende Differenz von 19.058,09 €

---

## ✅ KORREKTUREN DURCHGEFÜHRT

### 1. Einsatz-Filter korrigiert
- **Vorher:** `6. Ziffer='2'` → enthält Deggendorf-Konten (branch_number=1)
- **Nachher:** `branch_number=3` ✅
- **Ergebnis:** Einsatz jetzt korrekt (1.133.115,18 € vs. GlobalCube 1.133.115,00 €) → Differenz: 0,18 €

### 2. Kosten-Filter bestätigt
- **Filter:** `6. Ziffer='2'` ✅ (bleibt so)
- **Grund:** Kosten mit `6. Ziffer='2'` haben hauptsächlich `branch_number=1`, gehören aber zu Landau
- **Bestätigung:** Keine Überschneidung mit Deggendorf (filtert mit `branch=1 AND 6. Ziffer='1'`)

### 3. 74xxxx Korrektur
- **Problem:** 74xxxx Konten mit `branch_number=1` wurden fälschlicherweise für Landau gezählt
- **Lösung:** Ausgeschlossen (nicht mehr nötig, da Einsatz jetzt `branch_number=3` verwendet)

---

## 📊 AKTUELLE WERTE (YTD Sep-Dez 2025)

| Position | DRIVE | GlobalCube | Differenz | Status |
|----------|-------|------------|-----------|--------|
| Umsatz | 1.385.353,71 € | 1.385.360,00 € | -6,29 € | ✅ |
| Einsatz | 1.133.115,18 € | 1.133.115,00 € | 0,18 € | ✅ |
| Variable Kosten | 26.008,95 € | ? | ? | ⚠️ |
| Direkte Kosten | 140.761,54 € | ? | ? | ⚠️ |
| Indirekte Kosten | 148.628,95 € | ? | ? | ⚠️ |
| **Betriebsergebnis** | **-63.160,91 €** | **-82.219,00 €** | **19.058,09 €** | ⚠️ |
| Neutrales Ergebnis | 0,00 € | -127,00 € | -127,00 € | ⚠️ |

---

## 🔍 VERBLEIBENDE DIFFERENZ ANALYSE

**BE-Differenz: 19.058,09 €**

**Aufschlüsselung:**
1. **Neutrales Ergebnis:** -127,00 € (GlobalCube) vs. 0,00 € (DRIVE) → Differenz: -127,00 €
2. **Verbleibend:** 19.058 - 127 = 18.931,09 €

**Mögliche Ursachen:**
1. **Kosten-Differenz:** Die aufgedrillten Kosten in GlobalCube ergeben möglicherweise andere Summen
2. **Fehlende Kosten:** Möglicherweise fehlen Kosten in DRIVE
3. **Zusätzliche Kosten:** Möglicherweise werden Kosten in DRIVE gezählt, die in GlobalCube nicht gezählt werden
4. **Kategorisierung:** Variable/Direkte/Indirekte Kosten möglicherweise anders kategorisiert

---

## 📋 GESAMTSUMME vs. EINZELBETRIEBE

**Problem:** Gesamtsumme stimmt nicht mit Summe Einzelbetriebe überein:

| Position | Gesamt | Summe Einzel | Differenz |
|----------|--------|--------------|-----------|
| Umsatz | 10.603.687,48 € | 10.618.393,36 € | -14.705,88 € |
| Einsatz | 9.191.864,14 € | 9.152.706,16 € | 39.157,98 € |
| BE | -375.905,08 € | -323.459,26 € | -52.445,82 € |

**Ursache:** 
- Gesamtsumme zählt ALLE Konten (keine Filter)
- Einzelbetriebe zählen nur bestimmte Konten (mit Filtern)
- Möglicherweise gibt es Konten, die weder Deggendorf noch Landau noch Hyundai zugeordnet werden

---

## 💡 NÄCHSTE SCHRITTE

1. ⏳ **Neutrales Ergebnis analysieren**
   - GlobalCube: -127,00 €
   - DRIVE: 0,00 €
   - Prüfe 2xxxxx Konten für Landau

2. ⏳ **Kosten-Differenz aufklären**
   - Aufgedrillte Kosten aus GlobalCube: 306.932 €
   - DRIVE Kosten: 315.399 €
   - Differenz: 8.467 €
   - Möglicherweise fehlen Kosten in GlobalCube oder werden anders kategorisiert

3. ⏳ **Gesamtsumme-Problem lösen**
   - Warum stimmt Gesamtsumme nicht mit Summe Einzelbetriebe?
   - Gibt es Konten, die nicht zugeordnet werden?

4. ⏳ **Verbleibende 18.931 € aufklären**
   - Nach Neutrales Ergebnis (-127 €) verbleiben 18.931 €
   - Weitere Analyse erforderlich

---

## ✅ IMPLEMENTIERT

- [x] Einsatz-Filter auf `branch_number=3` geändert
- [x] Kosten-Filter bleiben bei `6. Ziffer='2'`
- [x] Alle Funktionen aktualisiert
- [x] Service neu gestartet
- [x] Tests durchgeführt

---

## ⚠️ OFFENE FRAGEN

1. **Warum haben Kosten mit `6. Ziffer='2'` hauptsächlich `branch_number=1`?**
   - Sind diese wirklich für Landau?
   - Oder gibt es ein Problem mit der Konten-Zuordnung?

2. **Warum stimmt die Gesamtsumme nicht?**
   - Prüfe ob Gesamtsumme = Summe Einzelbetriebe
   - Möglicherweise Doppelzählungen oder fehlende Zuordnungen

3. **Neutrales Ergebnis:**
   - GlobalCube zeigt -127,00 €
   - DRIVE zeigt 0,00 €
   - Muss analysiert werden
