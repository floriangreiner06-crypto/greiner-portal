# TAG 182 Logik Validierung - TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **VALIDIERT**

---

## 🎯 ZIEL

Die korrekte Logik für direkte Kosten für Dezember 2025 identifizieren.

---

## 📊 ANALYSE-ERGEBNISSE

### TAG 177 Logik (411xxx + 489xxx + 410021 ausgeschlossen)

**Monat Dezember 2025:**
- DRIVE: 181.216,91 €
- GlobalCube: 189.866,00 €
- **Differenz:** -8.649,09 € (-4,56%)

**YTD Sep-Dez 2025:**
- DRIVE: 625.530,17 €
- GlobalCube: 659.229,00 €
- **Differenz:** -33.698,83 € (-5,11%)

### TAG 182 Logik (nur 489xxx ausgeschlossen, 411xxx + 410021 enthalten)

**Monat Dezember 2025:**
- DRIVE: 189.849,47 €
- GlobalCube: 189.866,00 €
- **Differenz:** -16,53 € (-0,01%) ✅

**YTD Sep-Dez 2025:**
- DRIVE: 659.134,64 €
- GlobalCube: 659.229,00 €
- **Differenz:** -94,36 € (-0,01%) ✅

---

## 🔍 AUSGESCHLOSSENE KONTEN

### Monat Dezember 2025:
- **411xxx:** 8.412,33 €
- **410021:** 220,23 €
- **489xxx:** 16,81 €
- **Summe:** 8.649,37 €

**Erkenntnis:** Die Summe der ausgeschlossenen Konten (8.649,37 €) entspricht genau der Differenz zwischen TAG 177 und GlobalCube (8.649,09 €)!

### YTD Sep-Dez 2025:
- **411xxx:** 32.548,10 €
- **410021:** 1.056,37 €
- **489xxx:** 94,34 €
- **Summe:** 33.698,81 €

**Erkenntnis:** Die Summe der ausgeschlossenen Konten (33.698,81 €) entspricht genau der Differenz zwischen TAG 177 und GlobalCube (33.698,83 €)!

---

## ✅ FAZIT

**TAG 182 Logik ist korrekt für Dezember 2025!**

**Richtige Logik:**
- ✅ **411xxx** (Ausbildungsvergütung) sollte **ENTHALTEN** sein in direkten Kosten
- ✅ **410021** sollte **ENTHALTEN** sein in direkten Kosten
- ✅ **489xxx** sollte **AUSGESCHLOSSEN** sein aus direkten Kosten

**Ergebnis:**
- Monat: Nur -16,53 € Differenz zu GlobalCube (0,01%)
- YTD: Nur -94,36 € Differenz zu GlobalCube (0,01%)

**Verbesserung:**
- Von -8.649,09 € (TAG 177) auf -16,53 € (TAG 182) für Monat
- Von -33.698,83 € (TAG 177) auf -94,36 € (TAG 182) für YTD

---

## 🔄 CODE-ÄNDERUNGEN

**Datei:** `api/controlling_api.py`

**Änderung:** Direkte Kosten - 411xxx + 410021 enthalten, nur 489xxx ausgeschlossen:

```python
# Vorher (TAG 177):
AND NOT (
    nominal_account_number = 410021
    OR nominal_account_number BETWEEN 411000 AND 411999
    OR nominal_account_number BETWEEN 489000 AND 489999
    ...
)

# Nachher (TAG 182):
AND NOT (
    nominal_account_number BETWEEN 489000 AND 489999
    ...
)
```

**Aktualisierte Stellen:**
1. ✅ `_berechne_bwa_werte()` - Monatswerte
2. ✅ `_berechne_bwa_ytd()` - YTD-Werte
3. ✅ Abteilungsbezogene Queries (monatlich und YTD)

**Hinweis:** Indirekte Kosten bleiben unverändert - dort werden 411xxx + 410021 weiterhin ausgeschlossen (korrekt, da sie zu direkten Kosten gehören).

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Server neu starten:** `sudo systemctl restart greiner-portal`
2. ⏳ **BWA-Werte testen:**
   - Gesamtbetrieb (firma=0, standort=0)
   - Landau (firma=1, standort=2)
3. ⏳ **Mit GlobalCube vergleichen:**
   - Monat Dezember 2025
   - YTD Sep-Dez 2025
4. ⏳ **Weitere Differenzen analysieren:**
   - Einsatz: +3.222,36 € Differenz (Monat)
   - Einsatz: +31.905,97 € Differenz (YTD)

---

## 📊 STATUS

- ✅ TAG 182 Logik validiert
- ✅ Code-Änderungen implementiert
- ⏳ Server-Restart erforderlich
- ⏳ Validierung gegen GlobalCube ausstehend

---

**Nächster Schritt:** Server neu starten und BWA-Werte für Dezember 2025 testen.
