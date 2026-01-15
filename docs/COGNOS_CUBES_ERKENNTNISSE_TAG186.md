# Cognos Cubes (.mdc) - Erkenntnisse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **WICHTIGE ERKENNTNISSE GEFUNDEN**

---

## 🎯 ERKENNTNISSE

### 1. Echte Cubes gefunden

**Lage:** Backup-Verzeichnisse (z.B. `/mnt/globalcube/Cubes/f_belege__20260113182842/`)

**Größe:** 36 MB (nicht nur 51 Bytes wie die Stub-Dateien)

**Format:** Binär (PowerCube), aber Strings können extrahiert werden

---

### 2. Konten im Cube enthalten! ✅

**Gefundene Konten:**
- **71700** - Mehrfach im Cube gefunden
- **72700** - Mehrfach im Cube gefunden ("Sonstige Einsatzwerte GW")
- **72750** - Mehrfach im Cube gefunden

**Format im Cube:**
```
QU;5;71700C$;5;71700
QU;5;72700C$;5;72700
QU;5;72750C$;5;72750
QU;7;71700_HC$;7;71700_H
QU;7;72700_HC$;7;72700_H
QU;7;72750_HC$;7;72750_H
```

**Erkenntnis:** Die Konten sind **im Cube vorhanden**! Sie werden nicht komplett ausgeschlossen.

---

### 3. Struktur im Cube

**Gefundene Begriffe:**
- "Einsatzwerte" ✅
- "5. Materialaufwand" ✅
- "72700 - Sonstige Einsatzwerte GW" ✅
- "Bruttoertrag" (Berechnung: "Umsatzerlöse" * -1 - "Einsatzwerte")

**Erkenntnis:** Der Cube enthält die BWA-Struktur mit Materialaufwand und Einsatzwerten.

---

### 4. "Zurückgestellt" nicht gefunden

**Ergebnis:** Keine Treffer für "zurückgestellt" oder "zurueckgestellt" im Cube.

**Erkenntnis:** "Zurückgestellt" wird **nicht als Filter** im Cube verwendet!

---

## 💡 INTERPRETATION

### Hypothese 1: Konten werden verwendet

**Möglichkeit:** Die Konten 71700, 72700, 72750 sind im Cube enthalten und werden **verwendet**, nicht ausgeschlossen.

**Bedeutung:**
- GlobalCube verwendet diese Konten möglicherweise **trotz** "zurückgestellt" Zuordnung
- "Zurückgestellt" bedeutet möglicherweise **nicht** "ausgeschlossen"

### Hypothese 2: Filter liegt woanders

**Möglichkeit:** Die Filter-Logik liegt **nicht im Cube**, sondern:
- In den Cognos-Report-Definitionen (.txt)
- In den SQL-Queries, die den Cube füllen
- In der Datenquelle (LOC_Belege View)

**Test:** Prüfe SQL-Queries, die den Cube füllen

---

## 📊 ZUSAMMENFASSUNG

### ✅ Was wir wissen:

1. **71700, 72700, 72750 sind im Cube enthalten**
2. **"Zurückgestellt" wird nicht als Filter im Cube verwendet**
3. **Die Konten werden in "Einsatzwerte" und "5. Materialaufwand" verwendet**

### ❓ Offene Fragen:

1. **Werden die Konten tatsächlich in der BWA verwendet?**
   - Oder werden sie durch andere Filter ausgeschlossen?

2. **Was bedeutet "zurückgestellt" genau?**
   - Wenn es nicht im Cube verwendet wird, was ist seine Funktion?

3. **Wo liegt die Filter-Logik?**
   - In den SQL-Queries?
   - In den Report-Definitionen?
   - In der Datenquelle?

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Prüfe SQL-Queries, die den Cube füllen:**
   - Gibt es Filter in den SQL-Queries?
   - Werden 71700, 72700, 72750 ausgeschlossen?

2. ⏳ **Prüfe Cognos-Report-Definitionen:**
   - Gibt es Filter in den Report-Definitionen?
   - Werden bestimmte Konten ausgeschlossen?

3. ⏳ **Vergleiche mit GlobalCube-Ausgaben:**
   - Werden 71700, 72700, 72750 tatsächlich in der BWA verwendet?
   - Oder werden sie durch andere Mechanismen ausgeschlossen?

---

## 📊 STATUS

- ✅ Echte Cubes gefunden (36 MB)
- ✅ Konten 71700, 72700, 72750 im Cube enthalten
- ✅ "Einsatzwerte" und "5. Materialaufwand" im Cube
- ❌ "Zurückgestellt" nicht als Filter im Cube
- ⏳ Filter-Logik in SQL-Queries prüfen
- ⏳ Bedeutung von "zurückgestellt" klären

---

**KRITISCHE ERKENNTNIS:** Die Konten sind im Cube enthalten! Sie werden nicht durch "zurückgestellt" ausgeschlossen!
