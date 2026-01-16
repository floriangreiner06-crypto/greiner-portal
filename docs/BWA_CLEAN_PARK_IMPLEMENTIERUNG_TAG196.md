# BWA Clean Park Implementierung - TAG 196

**Datum:** 2026-01-16  
**TAG:** 196  
**Status:** ✅ **IMPLEMENTIERT**

---

## 🎯 ANFORDERUNG

**GlobalCube Schema - Kostenstellen-Mapping:**
- 60 = Clean Park (CP)

**GlobalCube zeigt:** "Mechanik+Karo" = 86.419,00 €

---

## ✅ IMPLEMENTIERT

### Clean Park Konten gefunden:

- **847xxx (Erlös):** 23.197,92 €
  - 847102: "Erlöse Clean Park Landau"
  - Weitere 847xxx Konten: 847001, 847051, 847081, 847091, 847201, 847301

- **747xxx (Einsatz):** 5.689,49 €
  - 747102: "Aufw.Landau Waschanlage"
  - Weitere 747xxx Konten: 747001, 747002, 747201, 747301

- **Bruttoertrag Clean Park:** 17.508,43 €

### BEREICHE_CONFIG erweitert:

```python
'CP': {
    'name': 'Clean Park',
    'erlos_range': (847000, 847999),  # 847xxx = Clean Park Erlös
    'einsatz_range': (747000, 747999),  # 747xxx = Clean Park Einsatz
    'order': 6
}
```

### Mechanik-Bereich angepasst:

- **847xxx (Clean Park Erlös)** aus Mechanik ausgeschlossen
- **747xxx (Clean Park Einsatz)** aus Mechanik ausgeschlossen

---

## 📊 ERGEBNISSE

**Bereiche Dezember 2025:**
- ME - Mechanik: 58.096,43 € (ohne Karosserie/Lack/CP)
- CP - Clean Park: 17.508,43 €
- **Summe Mechanik+CP:** 75.604,86 €

**Vergleich mit GlobalCube:**
- GlobalCube "Mechanik+Karo": 86.419,00 €
- DRIVE Mechanik+CP: 75.604,86 €
- **Differenz: -10.814,14 €** (DRIVE zu niedrig)

---

## ⚠️ OFFENE FRAGE

**GlobalCube zeigt "Mechanik+Karo":**
- "Karo" könnte "Karosserie" bedeuten (aber Karosserie hat 0,00 €)
- "Karo" könnte "Clean Park" bedeuten (aber Differenz bleibt -10.814,14 €)
- Es könnten weitere Konten fehlen, die zu Mechanik gehören sollten

**Mögliche Erklärungen:**
1. Es gibt weitere Konten, die zu "Mechanik+Karo" gehören
2. GlobalCube verwendet andere Filter-Logik
3. "Karo" bedeutet etwas anderes als erwartet

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Prüfen, was "Karo" in GlobalCube bedeutet:**
   - Ist es wirklich "Karosserie" oder "Clean Park"?
   - Gibt es andere Konten, die zu "Karo" gehören?

2. ⏳ **Weitere Konten prüfen:**
   - Gibt es andere 84xxxx Konten, die zu Mechanik gehören sollten?
   - Gibt es andere 74xxxx Konten, die zu Mechanik gehören sollten?

3. ⏳ **Filter-Logik prüfen:**
   - Verwendet GlobalCube andere Filter für Mechanik?
   - Gibt es Standort-spezifische Unterschiede?

---

## ✅ STATUS

- ✅ Clean Park Bereich implementiert (847xxx/747xxx)
- ✅ Mechanik-Bereich angepasst (847xxx/747xxx ausgeschlossen)
- ⚠️ Differenz zu GlobalCube bleibt (-10.814,14 €)
- ⏳ Weitere Analyse erforderlich
