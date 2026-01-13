# GlobalCube Excel-Analyse Ergebnisse - TAG 184

**Datum:** 2026-01-13  
**Status:** ✅ Excel-Struktur verstanden, Werte extrahiert

---

## 📋 ANALYSIERTE DATEIEN

1. **F.03 BWA Vorjahres-Vergleich (8).xlsx** - Gesamtbetrieb
2. **F.03 BWA Vorjahres-Vergleich DEG.xlsx** - Deggendorf
3. **F.03 BWA Vorjahres-Vergleich DEg HYU.xlsx** - Deggendorf Hyundai
4. **F.03 BWA Vorjahres-Vergleich LAN.xlsx** - Landau

---

## 🔍 EXCEL-STRUKTUR (Landau - vollständig analysiert)

### Spalten-Mapping:
- **Spalte A:** Haupt-Positionen
- **Spalte B:** Unter-Positionen
- **Spalte C (3):** Monat Dez./2025
- **Spalte G (7):** Monat Dez./2024 (Vorjahr)
- **Spalte Q (17):** Kumuliert Dez./2025 (YTD)
- **Spalte U (21):** Kumuliert Dez./2024 (Vorjahr YTD)

### BWA-Positionen (Landau):
- **Zeile 10:** "1 - NW" = Umsatzerlöse
- **Zeile 11:** "2 - GW" = Einsatzwerte
- **Zeile 20:** "Provisionen" = DB1 (Bruttoertrag)
- **Zeile 22:** "Fertigmachen" (Spalte A/B) = Variable Kosten
- **Zeile 32:** "Deckungsbeitrag" = Direkte Kosten
- **Zeile 33:** "Indirekte Kosten" (Spalte B) = Indirekte Kosten

---

## 📊 LANDAU VERGLEICH MIT DRIVE (Dez 2025)

### Monat (Dezember 2025):

| Position | Excel | DRIVE | Differenz | Status |
|----------|-------|-------|-----------|--------|
| Umsatzerlöse | 320.120,53 € | 320.120,53 € | 0,00 € | ✅ 0,00% |
| Einsatzwerte | 270.455,29 € | 270.455,29 € | 0,00 € | ✅ 0,00% |
| Bruttoertrag (DB1) | 49.665,24 € | 49.665,24 € | 0,00 € | ✅ 0,00% |
| Variable Kosten | 7.043,73 € | 6.173,95 € | -869,78 € | ❌ -12,35% |
| Direkte Kosten | 38.723,80 € | 38.723,80 € | 0,00 € | ✅ 0,00% |
| Indirekte Kosten | 38.445,61 € | 39.304,39 € | 858,78 € | ⚠️ 2,23% |
| Betriebsergebnis | -34.547,90 € | -34.536,90 € | 11,00 € | ✅ -0,03% |

**Ergebnis:** 5 von 7 Positionen passen perfekt (0% Differenz), 1 Position akzeptabel (2,23%), 1 Position mit größerer Differenz (Variable Kosten -12,35%)

### YTD (Sep-Dez 2025):

| Position | Excel | DRIVE | Differenz | Status |
|----------|-------|-------|-----------|--------|
| Umsatzerlöse | 1.385.360,01 € | 1.385.353,71 € | -6,30 € | ✅ -0,00% |
| Einsatzwerte | 1.133.115,18 € | 1.133.115,18 € | 0,00 € | ✅ 0,00% |
| Bruttoertrag | 252.244,83 € | 252.238,53 € | -6,30 € | ✅ -0,00% |
| Variable Kosten | 39.161,97 € | 25.905,53 € | -13.256,44 € | ❌ -33,85% |
| Direkte Kosten | 140.761,54 € | 140.761,54 € | 0,00 € | ✅ 0,00% |
| Indirekte Kosten | 137.810,45 € | 148.628,95 € | 10.818,50 € | ❌ 7,85% |

**Ergebnis:** YTD hat größere Differenzen, besonders bei Variable Kosten (-33,85%)

---

## ⚠️ OFFENE FRAGEN

### 1. Variable Kosten Differenz
- **Monat:** Excel 7.043,73 € vs DRIVE 6.173,95 € (-869,78 €, -12,35%)
- **YTD:** Excel 39.161,97 € vs DRIVE 25.905,53 € (-13.256,44 €, -33,85%)

**Mögliche Ursachen:**
- Excel "Fertigmachen" enthält Positionen die DRIVE nicht als Variable Kosten zählt
- DRIVE hat andere Filter-Logik für Variable Kosten
- Weitere Variable Kosten Positionen in Excel nicht erfasst

### 2. Indirekte Kosten Differenz (YTD)
- **Monat:** Excel 38.445,61 € vs DRIVE 39.304,39 € (858,78 €, 2,23%) ✅
- **YTD:** Excel 137.810,45 € vs DRIVE 148.628,95 € (10.818,50 €, 7,85%) ❌

**Mögliche Ursachen:**
- YTD-Berechnung unterschiedlich
- Weitere Indirekte Kosten Positionen in Excel nicht erfasst

---

## 🚀 NÄCHSTE SCHRITTE

### Priorität HOCH:
1. ⏳ **Variable Kosten vollständig erfassen**
   - Prüfe welche Positionen in Excel zu Variable Kosten gehören
   - Vergleiche mit DRIVE Variable Kosten Filter-Logik

2. ⏳ **DEG und HYU Excel analysieren**
   - Gleiche Struktur-Analyse für Deggendorf und Hyundai
   - Vergleich mit DRIVE

### Priorität MITTEL:
3. ⏳ **YTD-Differenzen analysieren**
   - Warum sind YTD-Differenzen größer als Monat?
   - Prüfe ob Excel YTD anders berechnet wird

4. ⏳ **Gesamtbetrieb Excel analysieren**
   - Struktur verstehen
   - Vergleich mit DRIVE Gesamtbetrieb

---

## 📁 GENERIERTE DATEIEN

- `/opt/greiner-portal/docs/globalcube_analysis/excel_landau_final_tag184.json`
- `/opt/greiner-portal/scripts/parse_excel_landau_final.py`
- `/opt/greiner-portal/scripts/analyse_globalcube_excel_alle_standorte.py`

---

## 💡 FAZIT

**Was funktioniert:**
- ✅ Excel-Struktur für Landau vollständig verstanden
- ✅ Umsatz, Einsatz, DB1, Direkte Kosten: Perfekte Übereinstimmung (0% Differenz)
- ✅ Betriebsergebnis: Fast perfekt (-0,03% Differenz)

**Was noch fehlt:**
- ⏳ Variable Kosten: Differenz -12,35% (Monat) / -33,85% (YTD)
- ⏳ Indirekte Kosten YTD: Differenz 7,85%
- ⏳ DEG und HYU Excel noch nicht vollständig analysiert

**Empfehlung:**
- **Nächster Schritt:** DEG und HYU Excel mit gleicher Logik analysieren
- **Dann:** Variable Kosten Differenz genauer untersuchen

---

*Erstellt: TAG 184 | Autor: Claude AI*
