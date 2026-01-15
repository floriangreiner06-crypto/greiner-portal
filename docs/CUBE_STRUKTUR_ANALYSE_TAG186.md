# Cognos Cube Struktur-Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **TIEFE ANALYSE DER CUBE-STRUKTUR**

---

## 🎯 ZIEL

Die **Cognos Cube-Struktur** verstehen, um zu klären:
- Wie werden Konten zu Dimensionen gemappt?
- Wie funktioniert die Hierarchie (Ebene1, Ebene2, Ebene11)?
- Werden "zurückgestellt" Konten gefiltert oder verwendet?

---

## 📊 CUBE-FORMAT

### QU-Format (Query-Struktur)

**Format:** `QU;Level;Item;Level;Item`

**Beispiele:**
- `QU;5;71700C$;5;71700` - Level 5, Konto 71700
- `QU;7;71700_HC$;7;71700_H` - Level 7, Konto 71700_H (Hyundai)
- `QU;32;72700 - Sonstige Einsatzwerte GWC$;32;72700 - Sonstige Einsatzwerte GW` - Level 32, Beschreibung

**Erkenntnis:** Verschiedene Levels repräsentieren verschiedene Ebenen der Hierarchie!

---

## 🔍 LEVEL-ANALYSE

### Level-Verteilung

**Level 5:** Kontonummern (71700, 72700, 72750)
**Level 7:** Kontonummern mit _H Suffix (Hyundai)
**Level 32:** Konten-Beschreibungen ("72700 - Sonstige Einsatzwerte GW")

**Erkenntnis:** Die Levels repräsentieren verschiedene Granularitäts-Ebenen!

---

## 📋 DIMENSIONEN

### Gefundene Dimensionen:

- **Einsatzwerte** ✅
- **Umsatzerlöse** ✅
- **Materialaufwand** ✅
- **Variable Kosten** ✅
- **Direkte Kosten** ✅
- **Indirekte Kosten** ✅

**Erkenntnis:** Diese Dimensionen sind im Cube vorhanden!

---

## 🔗 KONTEN-TO-DIMENSIONEN MAPPING

### 71700, 72700, 72750 im Cube:

**Gefunden:**
- `QU;5;71700C$;5;71700` - Level 5
- `QU;7;71700_HC$;7;71700_H` - Level 7 (Hyundai)
- `QU;5;72700C$;5;72700` - Level 5
- `QU;7;72700_HC$;7;72700_H` - Level 7 (Hyundai)
- `QU;5;72750C$;5;72750` - Level 5
- `QU;7;72750_HC$;7;72750_H` - Level 7 (Hyundai)

**Erkenntnis:** Die Konten sind im Cube vorhanden!

---

## ❓ OFFENE FRAGEN

1. **Wie werden Konten zu Dimensionen gemappt?**
   - Gibt es eine Mapping-Tabelle?
   - Oder liegt es in der Cube-Struktur?

2. **Wie funktioniert Ebene11 = "zurückgestellt"?**
   - Wird es als Filter verwendet?
   - Oder nur als Kategorisierung?

3. **Werden "zurückgestellt" Konten in "Einsatzwerte" verwendet?**
   - Oder werden sie ausgeschlossen?

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Cube-Dimensionen-Hierarchie verstehen:**
   - Wie werden Ebene1, Ebene2, Ebene11 verwendet?
   - Gibt es Filter-Logik in der Hierarchie?

2. ⏳ **Mapping zwischen Konten und Dimensionen finden:**
   - Wie werden 71700, 72700, 72750 zu "Einsatzwerte" gemappt?
   - Gibt es eine Mapping-Tabelle?

3. ⏳ **"Zurückgestellt" Bedeutung klären:**
   - Wird es als Filter verwendet?
   - Oder nur als Kategorisierung?

---

## 📊 STATUS

- ✅ Cube-Format verstanden (QU;Level;Item)
- ✅ Konten 71700, 72700, 72750 im Cube gefunden
- ✅ Dimensionen gefunden (Einsatzwerte, Materialaufwand, etc.)
- ⏳ Mapping zwischen Konten und Dimensionen verstehen
- ⏳ Ebene11 = "zurückgestellt" Bedeutung klären

---

**NÄCHSTER SCHRITT:** Mapping zwischen Konten und Dimensionen finden!
