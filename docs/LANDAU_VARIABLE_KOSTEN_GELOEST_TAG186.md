# Landau Variable Kosten - GELÖST TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **GELÖST**

---

## ✅ PROBLEM GELÖST

**Landau Variable Kosten YTD:**
- Vorher: 25.905,53 €
- Nachher: 39.161,97 €
- GlobalCube: 39.162,00 €
- **Differenz:** -0,03 € (0,00%) ✅

**Landau Variable Kosten Monat:**
- Vorher: 6.173,95 €
- Nachher: 7.043,73 €
- GlobalCube: 7.044,00 €
- **Differenz:** -0,27 € (0,00%) ✅

---

## 🔍 IDENTIFIZIERTE KONTEN

**Konten mit branch_number=3 aber 6. Ziffer='1':**
- **497031:** 7.494,13 € (17 Buchungen)
- **497061:** 2.940,69 € (10 Buchungen)
- **497211:** 1.903,64 € (8 Buchungen)
- **497221:** 874,16 € (4 Buchungen)
- **497011:** 43,82 € (2 Buchungen)
- **Summe:** 13.256,44 € ✅ (entspricht genau der fehlenden Differenz!)

**Erkenntnis:**
- Diese Konten gehören zu Landau (branch_number=3)
- Aber sie haben 6. Ziffer='1' (nicht '2')
- Der alte Filter (nur 6. Ziffer='2') hat sie nicht erfasst
- **Lösung:** branch_number=3 ODER 6. Ziffer='2' verwenden

---

## 🔧 CODE-ÄNDERUNG

**Datei:** `api/controlling_api.py`

**Änderung:** Landau Variable Kosten Filter erweitert:

```python
# Vorher:
variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"

# Nachher:
variable_kosten_filter = "AND (branch_number = 3 OR substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2') AND subsidiary_to_company_ref = 1"
```

**Aktualisierte Stellen:**
1. ✅ `_berechne_bwa_werte()` - Monatswerte (Zeile ~491)
2. ✅ `_berechne_bwa_ytd()` - YTD-Werte (Zeile ~1041)
3. ✅ `get_bwa_v2()` - Abteilungsbezogen (Zeile ~2000)

---

## 📊 ERGEBNISSE

**Landau YTD Sep-Dez 2025:**
- Variable Kosten: 39.161,97 € vs. GlobalCube 39.162,00 € → -0,03 € ✅
- DB2: 213.076,56 € vs. GlobalCube 213.083,00 € → -6,44 € ✅
- Direkte Kosten: 140.667,20 € vs. GlobalCube 140.762,00 € → -94,80 € ✅
- Betriebsergebnis: -62.963,15 € vs. GlobalCube -82.219,00 € → +19.255,85 € ⚠️

**Verbesserung:**
- Variable Kosten: Von -13.256,47 € auf -0,03 € (99,99% Verbesserung!) ✅

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Gesamtbetrieb Einsatz analysieren:**
   - Warum +31.905,97 € Differenz (YTD)?
   - Mögliche Doppelzählungen bei 74xxxx Konten?

2. ⏳ **Landau Betriebsergebnis analysieren:**
   - Warum +19.255,85 € Differenz (YTD)?
   - Hängt mit Variable Kosten zusammen?

---

## 📊 STATUS

- ✅ Landau Variable Kosten gelöst (nur -0,03 € / -0,27 € Differenz)
- ⏳ Gesamtbetrieb Einsatz analysieren
- ⏳ Weitere Differenzen analysieren

---

**Ergebnis:** Landau Variable Kosten sind jetzt perfekt! ✅
