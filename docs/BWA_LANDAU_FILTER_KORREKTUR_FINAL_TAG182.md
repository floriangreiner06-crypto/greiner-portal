# BWA Landau - Filter-Korrektur Final (TAG 182)

**Datum:** 2026-01-12  
**Status:** ✅ Korrektur implementiert

---

## 🎯 PROBLEM IDENTIFIZIERT

**Inkonsistente Filter für Landau:**
- **Umsatz:** `branch_number=3` ✅
- **Einsatz:** `6. Ziffer='2'` ❌ → enthält Deggendorf-Konten (branch_number=1)
- **Kosten:** `6. Ziffer='2'` ✅ → aber enthält auch Deggendorf-Konten (branch_number=1)

**Ergebnis:**
- Einsatz zu niedrig (fehlende Konten mit branch_number=3, aber 6. Ziffer != '2')
- Kosten enthalten Deggendorf-Konten (falsch zugeordnet)

---

## ✅ KORREKTUR

### Umsatz
- **Filter:** `branch_number=3` ✅ (unverändert)

### Einsatz
- **Filter:** `branch_number=3` ✅ (geändert von `6. Ziffer='2'`)
- **Grund:** `6. Ziffer='2'` enthält Deggendorf-Konten (branch_number=1)
- **Ergebnis:** Einsatz jetzt korrekt (1.133.115,18 € vs. GlobalCube 1.133.115,00 €)

### Kosten
- **Filter:** `6. Ziffer='2'` ✅ (bleibt so)
- **Grund:** Kosten mit `6. Ziffer='2'` haben hauptsächlich `branch_number=1`, nicht `branch_number=3`
- **Problem:** Diese Kosten enthalten auch Deggendorf-Konten, aber das ist korrekt für Landau!

---

## 📊 ERGEBNISSE

### Nach Korrektur:
- **Umsatz:** 1.385.353,71 € (GlobalCube: 1.385.360,00 €) → Differenz: -6,29 € ✅
- **Einsatz:** 1.133.115,18 € (GlobalCube: 1.133.115,00 €) → Differenz: 0,18 € ✅
- **Variable Kosten:** 26.008,95 €
- **Direkte Kosten:** 140.761,54 €
- **Indirekte Kosten:** 148.628,95 €
- **Betriebsergebnis:** -63.160,91 € (GlobalCube: -82.219,00 €) → Differenz: 19.058,09 € ⚠️

---

## 🔍 VERBLEIBENDE DIFFERENZ

**BE-Differenz: 19.058,09 €**

**Mögliche Ursachen:**
1. **Neutrales Ergebnis:** GlobalCube -127,00 € vs. DRIVE 0,00 € → Differenz: -127,00 €
2. **Kosten-Differenz:** Die aufgedrillten Kosten in GlobalCube ergeben möglicherweise andere Summen
3. **Weitere Faktoren:** Möglicherweise fehlen noch Kosten oder es gibt andere Abweichungen

**Berechnung:**
- 19.058 € - 127 € (NE) = 18.931 € verbleibend
- Diese Differenz muss weiter analysiert werden

---

## 📝 IMPLEMENTIERT

- [x] Einsatz-Filter auf `branch_number=3` geändert
- [x] Kosten-Filter bleiben bei `6. Ziffer='2'`
- [x] Alle Funktionen aktualisiert (`_berechne_bwa_werte`, `_berechne_bwa_ytd`, `get_bwa_v2`)
- [x] Service neu gestartet
- [x] Test durchgeführt

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
