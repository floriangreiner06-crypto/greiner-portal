# TAG 177 Logik Rekonstruktion - TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **IMPLEMENTIERT**

---

## 🎯 ZIEL

Die ursprüngliche TAG 177 Logik (für August 2025 validiert, 23,99 € Differenz) wiederherstellen und auf Dezember 2025 anwenden.

---

## 📋 TAG 177 LOGIK (August 2025)

**Direkte Kosten:** Folgende Kontenbereiche werden **AUS direkten Kosten AUSGESCHLOSSEN**:

1. **410021** (Spezifisches Konto)
2. **411xxx** (411000-411999, Ausbildungsvergütung)
3. **489xxx** (489000-489999, Sonstige Kosten)

**Validierung für August 2025:**
- DRIVE: 1.736.667,53 €
- GlobalCube: 1.736.691,52 €
- **Differenz:** 23,99 € ✅ (Rundungsdifferenz)

**Quelle:** `docs/LOESUNG_DIREKTE_KOSTEN_411XXX_489XXX_410021_TAG177.md`

---

## 🔍 AKTUELLE SITUATION (TAG 182 - Dezember 2025)

**Problem:** Die TAG 177 Logik wurde in TAG 182 geändert:
- 411xxx **ENTHALTEN** in direkten Kosten
- 410021 **ENTHALTEN** in direkten Kosten
- 489xxx **AUSGESCHLOSSEN** (komplett)

**Ergebnis für Dezember 2025:**
- Direkte Kosten YTD: 659.134,64 € (TAG 182 Logik)
- GlobalCube Referenz: 659.229,00 €
- **Differenz:** -94,36 €

**Aber:** Die ursprüngliche TAG 177 Logik hatte nur 23,99 € Differenz für August 2025!

---

## ✅ IMPLEMENTIERTE ÄNDERUNGEN

**Datei:** `api/controlling_api.py`

**Änderung:** TAG 177 Logik wiederhergestellt - 411xxx + 489xxx + 410021 aus direkten Kosten ausschließen:

```python
AND NOT (
    nominal_account_number = 410021
    OR nominal_account_number BETWEEN 411000 AND 411999  # ← HINZUGEFÜGT
    OR nominal_account_number BETWEEN 415100 AND 415199
    OR nominal_account_number BETWEEN 424000 AND 424999
    OR nominal_account_number BETWEEN 435500 AND 435599
    OR nominal_account_number BETWEEN 438000 AND 438999
    OR nominal_account_number BETWEEN 455000 AND 456999
    OR nominal_account_number BETWEEN 487000 AND 487099
    OR nominal_account_number BETWEEN 489000 AND 489999
    OR nominal_account_number BETWEEN 491000 AND 497999
)
```

**Aktualisierte Stellen:**
1. ✅ `_berechne_bwa_werte()` - Monatswerte (Zeile ~550)
2. ✅ `_berechne_bwa_ytd()` - YTD-Werte (Zeile ~1100)
3. ✅ Abteilungsbezogene Query (monatliche BWA, Zeile ~2060)
4. ✅ YTD Abteilungsbezogene Query (Zeile ~2420)

**Hinweis:** Die abteilungsbezogenen Queries hatten eine spezielle Logik für 489xxx (nur KST 0 ausgeschlossen), die jetzt auf komplett ausgeschlossen geändert wurde.

---

## 🧪 ERWARTETE ERGEBNISSE

**Für Dezember 2025 (YTD Sep-Dez):**

**Direkte Kosten:**
- Vorher (TAG 182): 659.134,64 €
- Erwartet (TAG 177): ~625.530,17 € (411xxx + 410021 + 489xxx ausgeschlossen)
- GlobalCube: 659.229,00 €

**Hypothese:**
- Wenn TAG 177 Logik für Dezember 2025 korrekt ist: ~33.698,83 € Differenz zu GlobalCube
- Wenn TAG 182 Logik für Dezember 2025 korrekt ist: ~94,36 € Differenz zu GlobalCube

**Frage:** Welche Logik ist für Dezember 2025 korrekt?

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Server neu starten:** `sudo systemctl restart greiner-portal`
2. ⏳ **BWA-Werte für Dezember 2025 abrufen:**
   - Landau (firma=1, standort=2)
   - Gesamtbetrieb (firma=0, standort=0)
3. ⏳ **Mit GlobalCube vergleichen:**
   - Monat Dezember 2025
   - YTD Sep-Dez 2025
4. ⏳ **Ergebnis analysieren:**
   - Ist die TAG 177 Logik für Dezember 2025 korrekt?
   - Oder ist die TAG 182 Logik korrekt?
   - Gibt es zeitabhängige Unterschiede?

---

## 🔄 LOGIK-UNTERSCHIEDE

### TAG 177 (August 2025):
- **Direkte Kosten:** 411xxx + 489xxx + 410021 **AUSGESCHLOSSEN**
- **Ergebnis:** 23,99 € Differenz ✅

### TAG 182 (Dezember 2025):
- **Direkte Kosten:** 411xxx + 410021 **ENTHALTEN**, 489xxx **AUSGESCHLOSSEN**
- **Ergebnis:** 94,36 € Differenz bei direkten Kosten

### TAG 186 (Rekonstruktion):
- **Direkte Kosten:** 411xxx + 489xxx + 410021 **AUSGESCHLOSSEN** (wie TAG 177)
- **Erwartung:** Testen, ob diese Logik für Dezember 2025 korrekt ist

---

## 💡 HYPOTHESE

**Mögliche Erklärungen:**

1. **Zeitabhängige Logik:** Die Logik könnte sich je nach Zeitraum ändern
2. **Mapping-Fehler:** Die ursprüngliche TAG 177 Logik war falsch, aber zufällig für August 2025 korrekt
3. **GlobalCube-Änderung:** GlobalCube könnte unterschiedliche Filter für verschiedene Zeiträume verwenden
4. **Datenqualität:** Unterschiedliche Datenqualität zwischen August 2025 und Dezember 2025

**Empfehlung:**
- TAG 177 Logik testen und mit GlobalCube vergleichen
- Wenn Differenz größer als 23,99 €: TAG 182 Logik war korrekt
- Wenn Differenz ~23,99 €: TAG 177 Logik ist korrekt

---

## 📊 STATUS

- ✅ TAG 177 Logik rekonstruiert
- ✅ Code-Änderungen implementiert
- ⏳ Server-Restart erforderlich
- ⏳ Validierung gegen GlobalCube ausstehend

---

**Nächster Schritt:** Server neu starten und BWA-Werte für Dezember 2025 abrufen.
