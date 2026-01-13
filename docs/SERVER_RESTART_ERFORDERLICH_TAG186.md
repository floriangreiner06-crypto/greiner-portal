# Server-Restart erforderlich - TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ⏳ **AUSSTEHEND**

---

## ⚠️ WICHTIG

Der Server läuft noch mit der **alten Logik (TAG 177)**. Die Code-Änderungen sind implementiert, aber der Server muss neu gestartet werden, damit sie wirksam werden.

---

## 📊 AKTUELLE WERTE (noch mit alter Logik)

**Gesamtbetrieb - Monat Dezember 2025:**
- Direkte Kosten: **181.216,91 €** (TAG 177 Logik)
- GlobalCube: 189.866,00 €
- **Differenz:** -8.649,09 € (-4,56%) ❌

**Gesamtbetrieb - YTD Sep-Dez 2025:**
- Direkte Kosten: **625.530,17 €** (TAG 177 Logik)
- GlobalCube: 659.229,00 €
- **Differenz:** -33.698,83 € (-5,11%) ❌

---

## ✅ ERWARTETE WERTE (nach Server-Restart mit TAG 182 Logik)

**Gesamtbetrieb - Monat Dezember 2025:**
- Direkte Kosten: **189.849,47 €** (TAG 182 Logik)
- GlobalCube: 189.866,00 €
- **Differenz:** -16,53 € (-0,01%) ✅

**Gesamtbetrieb - YTD Sep-Dez 2025:**
- Direkte Kosten: **659.134,64 €** (TAG 182 Logik)
- GlobalCube: 659.229,00 €
- **Differenz:** -94,36 € (-0,01%) ✅

**Verbesserung:**
- Monat: Von -8.649,09 € auf -16,53 € (99,8% Verbesserung!)
- YTD: Von -33.698,83 € auf -94,36 € (99,7% Verbesserung!)

---

## 🔧 CODE-ÄNDERUNGEN

**Implementiert:** TAG 182 Logik für direkte Kosten
- ✅ 411xxx (Ausbildungsvergütung) **ENTHALTEN** in direkten Kosten
- ✅ 410021 **ENTHALTEN** in direkten Kosten
- ✅ 489xxx **AUSGESCHLOSSEN** aus direkten Kosten

**Aktualisierte Stellen:**
1. ✅ `_berechne_bwa_werte()` - Monatswerte (Zeile ~550)
2. ✅ `_berechne_bwa_ytd()` - YTD-Werte (Zeile ~1100)
3. ✅ Abteilungsbezogene Queries (monatlich und YTD)

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Server neu starten:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

2. ⏳ **BWA-Werte testen:**
   ```bash
   python3 scripts/vergleiche_bwa_gesamt_globalcube.py
   python3 scripts/vergleiche_bwa_landau_globalcube.py
   ```

3. ⏳ **Validierung:**
   - Prüfen, ob direkte Kosten jetzt 189.849,47 € (Monat) und 659.134,64 € (YTD) sind
   - Mit GlobalCube vergleichen

---

## 📊 STATUS

- ✅ TAG 182 Logik validiert
- ✅ Code-Änderungen implementiert
- ⏳ **Server-Restart erforderlich**
- ⏳ Validierung gegen GlobalCube ausstehend

---

**Bitte Server neu starten, dann werden die neuen Werte automatisch aktiv!**
