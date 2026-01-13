# Zusammenfassung: Probleme und Lösungen TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **TEILWEISE GELÖST**

---

## ✅ GELÖSTE PROBLEME

### 1. Direkte Kosten Gesamtbetrieb ✅

**Problem:**
- DRIVE: 181.216,91 € (TAG 177 Logik)
- GlobalCube: 189.866,00 €
- **Differenz:** -8.649,09 €

**Lösung:**
- TAG 182 Logik: 411xxx + 410021 enthalten, nur 489xxx ausgeschlossen
- **Ergebnis:** 189.849,47 € → -16,53 € Differenz (99,8% Verbesserung!) ✅

**Identifizierte Konten:**
- 411xxx: 8.412,33 € (Monat) / 32.548,10 € (YTD)
- 410021: 220,23 € (Monat) / 1.056,37 € (YTD)
- 489xxx: 16,81 € (Monat) / 94,34 € (YTD)

### 2. Landau Variable Kosten ✅

**Problem:**
- DRIVE: 25.905,53 € (nur 6. Ziffer='2')
- GlobalCube: 39.162,00 €
- **Differenz:** -13.256,47 €

**Lösung:**
- Filter erweitert: branch_number=3 ODER 6. Ziffer='2'
- **Ergebnis:** 39.161,97 € → -0,03 € Differenz (99,99% Verbesserung!) ✅

**Identifizierte Konten:**
- **497031:** 7.494,13 € (branch=3, 6.Ziffer='1')
- **497061:** 2.940,69 € (branch=3, 6.Ziffer='1')
- **497211:** 1.903,64 € (branch=3, 6.Ziffer='1')
- **497221:** 874,16 € (branch=3, 6.Ziffer='1')
- **497011:** 43,82 € (branch=3, 6.Ziffer='1')
- **Summe:** 13.256,44 € ✅

---

## ⚠️ VERBLEIBENDE PROBLEME

### 1. Gesamtbetrieb Einsatz YTD 🚨

**Problem:**
- DRIVE: 9.223.769,97 €
- GlobalCube: 9.191.864,00 €
- **Differenz:** +31.905,97 € (+0,35%)

**Auswirkung:**
- Verursacht Betriebsergebnis-Differenz von -31.708,15 € (YTD)
- Verursacht DB1-Differenz von -31.912,61 € (YTD)

**Analyse:**
- Mit 74xxxx Sonderbehandlung: 9.223.769,97 €
- Ohne 74xxxx Sonderbehandlung: 9.150.374,09 €
- **Differenz:** 73.395,88 €

**Top 10 Konten (nach Betrag):**
1. 724201: 1.010.388,99 € (157 Buchungen)
2. 721201: 615.241,58 € (141 Buchungen)
3. 718001: 602.145,96 € (100 Buchungen)
4. 723101: 574.517,95 € (143 Buchungen)
5. 720301: 435.159,66 € (107 Buchungen)
6. 721202: 396.255,90 € (51 Buchungen)
7. 713111: 363.996,53 € (47 Buchungen)
8. 730301: 254.984,04 € (1164 Buchungen)
9. 710631: 250.767,76 € (31 Buchungen)
10. 730001: 238.767,14 € (1400 Buchungen)

**Fragen:**
1. Welche dieser Konten erfasst GlobalCube nicht?
2. Sollen bestimmte Konten ausgeschlossen werden?
3. Gibt es Konten mit branch_number, die falsch zugeordnet sind?

**Benötigte Informationen:**
- Liste der Konten, die GlobalCube für Gesamtbetrieb Einsatz erfasst (YTD Sep-Dez 2025)
- Prüfen, ob bestimmte Konten ausgeschlossen werden sollten
- Prüfen, ob es Doppelzählungen gibt

### 2. Gesamtbetrieb Betriebsergebnis YTD ⚠️

**Problem:**
- DRIVE: -407.613,15 €
- GlobalCube: -375.905,00 €
- **Differenz:** -31.708,15 € (-8,44%)

**Erkenntnis:**
- Die Differenz entspricht fast genau der Einsatz-Differenz (+31.905,97 €)
- **Hypothese:** Wenn Einsatz korrekt wäre, wäre Betriebsergebnis auch korrekt

---

## 📋 BENÖTIGTE INFORMATIONEN

### Für Gesamtbetrieb Einsatz:

**Konkrete Fragen:**
1. Welche Konten erfasst GlobalCube für Gesamtbetrieb Einsatz (YTD Sep-Dez 2025)?
2. Sollen bestimmte Konten ausgeschlossen werden?
3. Gibt es Konten mit branch_number, die falsch zugeordnet sind?

**Top 10 Konten, die analysiert werden müssen:**
- 724201, 721201, 718001, 723101, 720301, 721202, 713111, 730301, 710631, 730001

**Mögliche Ursachen:**
- 74xxxx Konten werden möglicherweise falsch zugeordnet
- Konten mit bestimmten branch_number werden doppelt gezählt
- Konten mit bestimmten subsidiary werden falsch zugeordnet

---

## 💡 LÖSUNGSANSATZ

### Option 1: GlobalCube-Konten-Liste vergleichen
- Liste der Konten, die GlobalCube erfasst, mit DRIVE vergleichen
- Identifiziere fehlende oder zusätzliche Konten

### Option 2: Filter-Logik anpassen
- Basierend auf Konten-Analyse Filter korrigieren
- Möglicherweise bestimmte Konten ausschließen

### Option 3: Branch-Number-Logik prüfen
- Prüfen, ob Konten mit bestimmten branch_number falsch zugeordnet sind
- Möglicherweise Filter-Logik für Gesamtbetrieb anpassen

---

## 📊 STATUS

- ✅ Direkte Kosten Gesamtbetrieb: Gelöst (nur -16,53 € / -94,36 € Differenz)
- ✅ Landau Variable Kosten: Gelöst (nur -0,03 € / -0,27 € Differenz)
- ⏳ Gesamtbetrieb Einsatz: Analyse erforderlich (Konten-Liste benötigt)
- ⏳ Gesamtbetrieb Betriebsergebnis: Hängt mit Einsatz zusammen

---

**Nächster Schritt:** GlobalCube-Konten-Liste für Gesamtbetrieb Einsatz besorgen und vergleichen.
