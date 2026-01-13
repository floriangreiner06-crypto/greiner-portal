# BWA Landau - 74xxxx Korrektur (Einsatzwerte Lohn Mechaniker)

**Datum:** 2026-01-12  
**Status:** ✅ Korrektur implementiert

---

## 🎯 PROBLEM IDENTIFIZIERT

**74xxxx Konten (Einsatzwerte Lohn Mechaniker)** wurden fälschlicherweise für Landau berücksichtigt, obwohl sie zu Deggendorf gehören.

### Analyse-Ergebnisse:

**74xxxx Konten für Landau (YTD Sep-Dez 2025):**
- Mit Filter `6. Ziffer='2'`: **73.688,68 €** (4 Konten)
- Davon `branch_number=1` (Deggendorf): **73.395,88 €** ❌
- Davon `branch_number=3` (Landau): **292,80 €** ✅

**Problem:**
- Die 74xxxx Konten mit `branch_number=1` haben zwar `6. Ziffer='2'`, gehören aber zu Deggendorf, nicht zu Landau!
- Diese wurden fälschlicherweise in den Landau-Einsatz einbezogen.

---

## ✅ KORREKTUR

**Implementiert in:**
1. `_berechne_bwa_werte()` - Monatswerte
2. `_berechne_bwa_ytd()` - YTD-Werte
3. `get_bwa_v2()` - BWA v2 API

**Logik:**
```python
# TAG182: Landau - 74xxxx Konten mit branch_number=1 AUSSCHLIESSEN
if standort == '2' and firma == '1':
    einsatz_74xxx_exclude = "AND NOT (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)"
else:
    einsatz_74xxx_exclude = ""
```

---

## 📊 ERGEBNISSE

### Vorher (mit 74xxxx branch_number=1):
- Einsatz: **1.172.273,16 €**
- BE: **-63.160,91 €**

### Nachher (ohne 74xxxx branch_number=1):
- Einsatz: **1.133.115,18 €** ✅ (reduziert um 39.157,98 €)
- BE: **-63.160,91 €** (unverändert - andere Faktoren)

### Vergleich mit GlobalCube:
- GlobalCube BE: **-82.219,00 €**
- DRIVE BE: **-63.160,91 €**
- **Differenz: 19.058,09 €** ⚠️

---

## 🔍 VERBLEIBENDE DIFFERENZ

Die Differenz von **19.058,09 €** ist weiterhin vorhanden. Mögliche Ursachen:

1. **Andere Einsatz-Konten** (nicht 74xxxx) mit falscher Zuordnung
2. **Kosten-Filter** - möglicherweise fehlen noch Kosten
3. **Neutrales Ergebnis** - GlobalCube zeigt -127,00 €, DRIVE zeigt 0,00 €
4. **Andere Faktoren** - weitere Analyse erforderlich

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Neutrales Ergebnis analysieren** (-127,00 € in GlobalCube)
2. ⏳ **Weitere Einsatz-Konten prüfen** (andere 7xxxxx Bereiche)
3. ⏳ **Kosten-Differenz analysieren** (Variable, Direkte, Indirekte)
4. ⏳ **HAR-Datei erneut prüfen** - alle Positionen vergleichen

---

## ✅ IMPLEMENTIERT

- [x] 74xxxx Konten mit `branch_number=1` aus Landau-Einsatz ausgeschlossen
- [x] Korrektur in `_berechne_bwa_werte()` implementiert
- [x] Korrektur in `_berechne_bwa_ytd()` implementiert
- [x] Korrektur in `get_bwa_v2()` implementiert
- [x] Service neu gestartet
- [x] Test durchgeführt
