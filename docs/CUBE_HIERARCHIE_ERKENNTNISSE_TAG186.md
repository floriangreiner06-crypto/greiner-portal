# Cognos Cube Hierarchie-Erkenntnisse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **WICHTIGE ERKENNTNISSE**

---

## 🎯 CUBE-STRUKTUR VERSTANDEN

### QU-Format (Query-Struktur)

**Format:** `QU;Level;Item;Level;Item`

**Level-Bedeutungen:**
- **Level 5:** Kontonummern (71700, 72700, 72750)
- **Level 7:** Kontonummern mit _H Suffix (Hyundai: 71700_H, 72700_H, 72750_H)
- **Level 12:** Dimension "Einsatzwerte"
- **Level 32/34:** Konten-Beschreibungen ("72700 - Sonstige Einsatzwerte GW")
- **Level 14:** Dimension "Direkte Kosten"
- **Level 15:** Dimension "Variable Kosten"
- **Level 16:** Dimension "Indirekte Kosten"
- **Level 18:** Dimension "5. Materialaufwand"

---

## 🔍 ERKENNTNISSE

### 1. Konten im Cube vorhanden ✅

**71700:**
- `QU;5;71700C$;5;71700` (Level 5)
- `QU;7;71700_HC$;7;71700_H` (Level 7, Hyundai)
- Levels: 5, 7, 9, 36, 38

**72700:**
- `QU;5;72700C$;5;72700` (Level 5)
- `QU;7;72700_HC$;7;72700_H` (Level 7, Hyundai)
- `QU;32;72700 - Sonstige Einsatzwerte GWC$;32;72700 - Sonstige Einsatzwerte GW` (Level 32, Beschreibung)
- Levels: 5, 7, 9, 32, 34

**72750:**
- `QU;5;72750C$;5;72750` (Level 5)
- `QU;7;72750_HC$;7;72750_H` (Level 7, Hyundai)
- Levels: 5, 7, 9, 26, 28

### 2. "Zurückgestellt" NICHT im Cube ❌

**Ergebnis:** Keine Treffer für "zurückgestellt" im Cube!

**Erkenntnis:** "Zurückgestellt" wird **nicht als Filter** im Cube verwendet!

### 3. Dimensionen im Cube ✅

**Gefundene Dimensionen:**
- `QU;12;EinsatzwerteC$;12;Einsatzwerte` (Level 12)
- `QU;14;Direkte KostenC$;14;Direkte Kosten` (Level 14)
- `QU;15;Variable KostenC$;15;Variable Kosten` (Level 15)
- `QU;16;Indirekte KostenC$;16;Indirekte Kosten` (Level 16)
- `QU;18;5. MaterialaufwandC$;18;5. Materialaufwand` (Level 18)

### 4. Hierarchie-Struktur

**B$-Format (Hierarchie-Definitionen):**
- `B$;6;Ebene1A$;8;Ebene1 2QU;7;Konto_1` - Ebene1 Definition
- `B$;6;Ebene2A$;8;Ebene2 3QU;6;Ebene1` - Ebene2 -> Ebene1
- `B$;7;Ebene21A$;9;Ebene21 2QU;7;Ebene21` - Ebene21 Definition

**Erkenntnis:** B$-Format definiert die Hierarchie zwischen Ebenen!

---

## 💡 INTERPRETATION

### Hypothese 1: Konten werden verwendet

**Möglichkeit:** Die Konten 71700, 72700, 72750 sind im Cube vorhanden und werden **verwendet**, nicht ausgeschlossen.

**Beweis:**
- Konten sind auf Level 5/7 vorhanden
- "72700 - Sonstige Einsatzwerte GW" ist auf Level 32/34 vorhanden
- "Einsatzwerte" Dimension ist auf Level 12 vorhanden

### Hypothese 2: Hierarchie-Mapping

**Möglichkeit:** Die Konten werden über die Hierarchie zu "Einsatzwerte" gemappt:
- Level 5 (71700, 72700, 72750) -> Level 32/34 (Beschreibungen) -> Level 12 (Einsatzwerte)

**Test:** Prüfe Hierarchie-Verbindungen zwischen Levels

### Hypothese 3: "Zurückgestellt" irrelevant

**Möglichkeit:** "Zurückgestellt" ist nur eine **Kategorisierung in GCStruct**, wird aber **nicht im Cube verwendet**.

**Erkenntnis:** "Zurückgestellt" kommt **nicht im Cube vor**!

---

## 📊 ZUSAMMENFASSUNG

### ✅ Was wir wissen:

1. **Konten 71700, 72700, 72750 sind im Cube vorhanden**
2. **"Zurückgestellt" kommt NICHT im Cube vor**
3. **Dimensionen sind vorhanden (Einsatzwerte, Materialaufwand, etc.)**
4. **Hierarchie-Struktur existiert (B$-Format)**

### ❓ Offene Fragen:

1. **Wie werden Level 5/32/34 zu Level 12 ("Einsatzwerte") gemappt?**
   - Gibt es eine Hierarchie-Verbindung?
   - Oder liegt das Mapping in GCStruct?

2. **Werden die Konten tatsächlich in "Einsatzwerte" verwendet?**
   - Oder werden sie durch andere Mechanismen ausgeschlossen?

3. **Was bedeutet "zurückgestellt" dann?**
   - Wenn es nicht im Cube verwendet wird, was ist seine Funktion?

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Hierarchie-Verbindungen zwischen Levels finden:**
   - Wie werden Level 5 -> Level 12 gemappt?
   - Gibt es B$-Definitionen für diese Verbindungen?

2. ⏳ **GCStruct-Mapping prüfen:**
   - Wie werden Konten aus GCStruct zu Cube-Levels gemappt?
   - Gibt es eine Mapping-Tabelle?

3. ⏳ **Vergleiche mit GlobalCube-BWA:**
   - Werden 71700, 72700, 72750 tatsächlich verwendet?
   - Oder werden sie ausgeschlossen?

---

## 📊 STATUS

- ✅ Cube-Format verstanden (QU;Level;Item)
- ✅ Konten im Cube gefunden
- ✅ Dimensionen gefunden
- ✅ "Zurückgestellt" NICHT im Cube
- ⏳ Hierarchie-Verbindungen verstehen
- ⏳ Mapping zwischen Levels finden

---

**KRITISCHE ERKENNTNIS:** "Zurückgestellt" kommt NICHT im Cube vor! Die Filter-Logik muss woanders liegen!
