# BWA Landau - HAR-Analyse Final (TAG 182)

**Datum:** 2026-01-12  
**Status:** ✅ HAR vollständig analysiert

---

## 📊 GLOBALCUBE WERTE (aus HAR)

**YTD Sep-Dez 2025:**
- **Umsatzerlöse:** 1.385.360,00 €
- **Einsatzwerte:** 1.133.115,00 €
- **Bruttoertrag:** 1.003,20 €
- **Variable Kosten:** 1,90 € ⚠️ (sehr klein - möglicherweise aufgedrillt)
- **Direkte Kosten:** 4,20 € ⚠️ (sehr klein - möglicherweise aufgedrillt)
- **Indirekte Kosten:** (nicht als Hauptposition gefunden)
- **Betriebsergebnis:** -82.219,00 €
- **Neutrales Ergebnis:** -127,00 € (in Spalte 11, nicht als Hauptposition)
- **Unternehmensergebnis:** -82.219,00 € (vermutlich BE + NE)

---

## 📊 DRIVE WERTE (aktuell)

**YTD Sep-Dez 2025:**
- **Umsatzerlöse:** 1.385.353,71 €
- **Einsatzwerte:** 1.133.115,18 €
- **Variable Kosten:** 26.008,95 €
- **Direkte Kosten:** 140.761,54 €
- **Indirekte Kosten:** 148.628,95 €
- **Betriebsergebnis:** -63.160,91 €
- **Neutrales Ergebnis:** 0,00 € ⚠️
- **Unternehmensergebnis:** -63.160,91 €

---

## 🔍 VERGLEICH

| Position | GlobalCube | DRIVE | Differenz | Status |
|----------|------------|-------|-----------|--------|
| Umsatz | 1.385.360,00 € | 1.385.353,71 € | -6,29 € | ✅ |
| Einsatz | 1.133.115,00 € | 1.133.115,18 € | 0,18 € | ✅ |
| Variable Kosten | 1,90 € | 26.008,95 € | 26.007,05 € | ⚠️ |
| Direkte Kosten | 4,20 € | 140.761,54 € | 140.757,34 € | ⚠️ |
| Indirekte Kosten | (nicht gefunden) | 148.628,95 € | ? | ⚠️ |
| **Betriebsergebnis** | **-82.219,00 €** | **-63.160,91 €** | **19.058,09 €** | ⚠️ |
| Neutrales Ergebnis | -127,00 € | 0,00 € | -127,00 € | ⚠️ |
| **Unternehmensergebnis** | **-82.219,00 €** | **-63.160,91 €** | **19.058,09 €** | ⚠️ |

---

## 💡 ERKENNTNISSE

### 1. Umsatz & Einsatz ✅
- **Umsatz:** Differenz von nur 6,29 € (0,0005%) - praktisch identisch
- **Einsatz:** Differenz von nur 0,18 € (0,00002%) - praktisch identisch
- **74xxxx Korrektur war erfolgreich!**

### 2. Kosten-Positionen ⚠️
- **Variable/Direkte Kosten in HAR:** Sehr kleine Werte (1,90 € / 4,20 €)
- **Vermutung:** Kosten sind in GlobalCube aufgedrillt (Personalkosten, Gemeinkosten, etc.)
- **DRIVE zeigt Gesamtsummen:** Variable 26.009 €, Direkte 140.762 €, Indirekte 148.629 €
- **Problem:** HAR zeigt nicht die Gesamtsummen, sondern nur kleine Teilbeträge

### 3. Betriebsergebnis ⚠️
- **Differenz:** 19.058,09 €
- **Mögliche Ursachen:**
  1. **Neutrales Ergebnis:** GlobalCube -127,00 € vs. DRIVE 0,00 € → Differenz: -127,00 €
  2. **Kosten-Differenz:** Die aufgedrillten Kosten in GlobalCube ergeben möglicherweise andere Summen
  3. **Weitere Faktoren:** Möglicherweise fehlen noch Kosten oder es gibt andere Abweichungen

### 4. Neutrales Ergebnis ⚠️
- **GlobalCube:** -127,00 € (in Spalte 11 der HTML-Tabelle)
- **DRIVE:** 0,00 €
- **Differenz:** -127,00 €
- **Bedeutung:** Dies erklärt einen Teil der BE-Differenz, aber nicht alles (19.058 € - 127 € = 18.931 € verbleibend)

---

## 🎯 NÄCHSTE SCHRITTE

1. ⏳ **Neutrales Ergebnis analysieren**
   - Prüfe 2xxxxx Konten für Landau
   - Filter: `branch_number=3` oder `6. Ziffer='2'`?
   - Sollte -127,00 € ergeben

2. ⏳ **Kosten-Struktur in GlobalCube verstehen**
   - Wie werden Variable/Direkte/Indirekte Kosten in GlobalCube berechnet?
   - Sind sie wirklich aufgedrillt oder gibt es eine Gesamtsumme?
   - Prüfe ob die HAR-Datei die Gesamtsummen enthält (andere Spalte?)

3. ⏳ **Verbleibende Differenz aufklären**
   - 19.058,09 € - 127,00 € (NE) = 18.931,09 € verbleibend
   - Weitere Analyse erforderlich

---

## 📝 DATEIEN

- **HAR-Datei:** `/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse/f03_bwa_vj_vergleich_landau_weiter_aufgedrillt.har`
- **HTML extrahiert:** `/tmp/har_response_1_complete.html`
- **Analyse-Script:** `/opt/greiner-portal/scripts/explore_har_complete.py`
