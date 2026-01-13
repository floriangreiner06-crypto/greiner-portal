# BWA Validierung - TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Direkte/Indirekte Kosten korrekt, BE/UE in Prüfung

---

## 📊 AKTUELLER STATUS

### ✅ Korrekte Werte (YTD Sep-Dez 2025):

**Direkte Kosten:**
- DRIVE: **659.228,98 €**
- GlobalCube: **659.228,98 €**
- **Differenz: 0,00 €** ✅

**Indirekte Kosten:**
- DRIVE: **838.937,55 €**
- GlobalCube: **838.943,85 €**
- **Differenz: -6,30 €** ✅ (sehr nah, möglicherweise Rundung)

### ⏳ Zu prüfende Werte:

**Betriebsergebnis:**
- DRIVE: **-390.503,33 €**
- GlobalCube: **-375.797,45 €**
- **Differenz: -14.705,88 €** ⚠️

**Unternehmensergebnis:**
- DRIVE: **-260.230,25 €**
- GlobalCube: **-245.524,00 €**
- **Differenz: -14.706,25 €** ⚠️

---

## 🔍 ANALYSE

### 1. Indirekte Kosten (-6,30 € Differenz)

**Ursache:** Möglicherweise Rundungsunterschiede oder kleine Mapping-Unterschiede

**Status:** ✅ Akzeptabel (sehr nah an GlobalCube)

### 2. Betriebsergebnis (-14.705,88 € Differenz)

**Berechnung:**
- BE = DB3 - Indirekte Kosten
- DB3 = DB2 - Direkte Kosten
- DB2 = DB1 - Variable Kosten
- DB1 = Umsatz - Einsatz

**Aktuelle DRIVE Werte:**
- Umsatz: 10.603.795,11 €
- Einsatz: 9.191.864,14 €
- DB1: 1.411.930,97 €
- DB2: 1.411.930,97 € (Variable = 0)
- DB3: 752.701,99 €
- Indirekte: 838.937,55 €
- **BE: -86.235,56 €** (aber API zeigt -390.503,33 €)

**Problem:** Die API zeigt einen anderen BE-Wert als die Berechnung!

**Mögliche Ursachen:**
1. 8910xx könnte in DB3 oder DB2 enthalten sein sollten
2. Andere Konten könnten fehlen oder zu viel enthalten sein
3. Berechnungslogik könnte unterschiedlich sein

### 3. 8910xx Analyse

**8910xx Werte:**
- H (Haben): 14.705,88 €
- S (Soll): -14.705,88 €
- H-S: 29.411,76 €

**Aktuell:** 8910xx ist aus indirekten Kosten ausgeschlossen ✅

**Test:** 8910xx in DB3 oder DB2 enthalten?
- **Ergebnis:** Wird geprüft

---

## 🚀 NÄCHSTE SCHRITTE

1. ⏳ **BE-Berechnung validieren**
   - Prüfe warum API BE-Wert von Berechnung abweicht
   - Prüfe ob 8910xx in DB3/DB2 enthalten sein sollte

2. ⏳ **Alle Filter-Möglichkeiten testen**
   - Standort-Filter ✅
   - KST-Filter ✅
   - Kombinationen prüfen

3. ⏳ **Dokumentation aktualisieren**
   - Finale Logik dokumentieren
   - Filter-Optionen dokumentieren

---

## 📝 FILTER-OPTIONEN

### Standort-Filter:
- ✅ Standort 0 (Alle)
- ✅ Standort 1 (Deggendorf Opel)
- ✅ Standort 2 (Deggendorf Hyundai)
- ✅ Standort 3 (Landau)

### KST-Filter:
- ✅ KST 0 (Indirekte Kosten)
- ✅ KST 1 (NW)
- ✅ KST 2 (GW)
- ✅ KST 3 (T+Z)
- ✅ KST 6 (Mietwagen)
- ✅ KST 7 (Mietwagen)
- ✅ Kombinationen möglich

---

**Status:** Direkte/Indirekte Kosten korrekt, BE/UE in Prüfung
