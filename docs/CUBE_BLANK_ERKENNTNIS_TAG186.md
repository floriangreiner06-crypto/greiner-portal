# Cognos Cube "Blank" Erkenntnis TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🎯 **KRITISCHE ERKENNTNIS!**

---

## 🎯 KRITISCHE ERKENNTNIS

### "Blank" / "Leerstelle" für 71700, 72700, 72750

**Gefundene Zeilen:**
```
QU;9;( blank )B$;14;( Leerstelle )A$;20;( Leerstelle )~71700
QU;9;( blank )B$;14;( Leerstelle )A$;20;( Leerstelle )~72700
QU;9;( blank )B$;14;( Leerstelle )A$;20;( Leerstelle )~72750
```

**Format-Analyse:**
- **Level 9:** "( blank )"
- **Level 14:** "( Leerstelle )"
- **Level 20:** "( Leerstelle )"
- **Konto:** 71700, 72700, 72750

**Erkenntnis:** Die Konten haben **"blank"** und **"Leerstelle"** Zuordnungen!

---

## 💡 INTERPRETATION

### Hypothese 1: "Blank" = Ausgeschlossen

**Möglichkeit:** Konten mit "blank" Zuordnung werden von GlobalCube **ausgeschlossen** oder in eine **leere Kategorie** verschoben.

**Bedeutung:**
- 71700, 72700, 72750 werden möglicherweise **nicht in "Einsatzwerte"** verwendet
- Sie werden in "blank" / "Leerstelle" Kategorie verschoben
- Das würde die Differenz erklären!

### Hypothese 2: "Blank" = Neutrales Ergebnis

**Möglichkeit:** "Blank" Konten werden in "Neutrales Ergebnis" verschoben, nicht in "Einsatzwerte".

**Test:** Prüfe, ob "blank" Konten in "Neutrales Ergebnis" verwendet werden

### Hypothese 3: "Blank" = Nicht verwendet

**Möglichkeit:** "Blank" Konten werden **komplett ausgeschlossen** und nicht in der BWA verwendet.

**Test:** Vergleiche mit GlobalCube-BWA, um zu sehen, ob diese Konten verwendet werden

---

## 📊 ZUSAMMENFASSUNG

### ✅ Was wir wissen:

1. **Konten 71700, 72700, 72750 haben "blank" Zuordnungen**
2. **"Zurückgestellt" kommt NICHT im Cube vor**
3. **"Blank" könnte die Filter-Logik sein!**

### ❓ Offene Fragen:

1. **Werden "blank" Konten in "Einsatzwerte" verwendet?**
   - Oder werden sie ausgeschlossen?

2. **Was bedeutet "blank" genau?**
   - Ausgeschlossen?
   - Neutrales Ergebnis?
   - Oder etwas anderes?

3. **Kann "blank" die 31.905,97€ Differenz erklären?**
   - Wenn ja, welche Konten werden ausgeschlossen?

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Prüfe, ob "blank" Konten in "Einsatzwerte" verwendet werden:**
   - Gibt es eine Hierarchie-Verbindung?
   - Oder werden sie ausgeschlossen?

2. ⏳ **Analysiere andere "blank" Konten:**
   - Welche anderen Konten haben "blank"?
   - Werden sie alle ausgeschlossen?

3. ⏳ **Vergleiche mit GlobalCube-BWA:**
   - Werden 71700, 72700, 72750 tatsächlich verwendet?
   - Oder werden sie durch "blank" ausgeschlossen?

---

## 📊 STATUS

- ✅ "Blank" / "Leerstelle" für 71700, 72700, 72750 gefunden
- ✅ "Zurückgestellt" NICHT im Cube
- ⏳ Bedeutung von "blank" klären
- ⏳ Prüfen, ob "blank" Konten ausgeschlossen werden

---

**KRITISCHE ERKENNTNIS:** "Blank" / "Leerstelle" könnte die Filter-Logik sein, die 71700, 72700, 72750 ausschließt!
