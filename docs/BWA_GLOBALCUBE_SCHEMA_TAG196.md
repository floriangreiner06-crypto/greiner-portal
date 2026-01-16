# BWA GlobalCube Schema - Kostenstellen-Mapping TAG 196

**Datum:** 2026-01-16  
**TAG:** 196  
**Status:** ✅ **IMPLEMENTIERT**

---

## 🎯 ANFORDERUNG

**GlobalCube Schema - Kostenstellen-Mapping:**
- 10 = NW (Neuwagen)
- 20 = GW (Gebrauchtwagen)
- 30 = Mechanik
- 40 = Karosserie
- 50 = Teile
- 60 = Clean Park (CP)
- 70 = Mietwagen
- 80 = Sonstiges

---

## ✅ IMPLEMENTIERT

### BEREICHE_CONFIG erweitert:

```python
BEREICHE_CONFIG = {
    'NW': {'name': 'Neuwagen', 'erlos_prefix': '81', 'einsatz_prefix': '71', 'order': 1},
    'GW': {'name': 'Gebrauchtwagen', 'erlos_prefix': '82', 'einsatz_prefix': '72', 'order': 2},
    'ME': {'name': 'Mechanik', 'erlos_prefix': '84', 'einsatz_prefix': '74', 'order': 3},
    'KA': {'name': 'Karosserie', 'erlos_range': (840500, 840599), 'einsatz_range': (745000, 745999), 'order': 4},
    'TZ': {'name': 'Teile & Zubehör', 'erlos_prefix': '83', 'einsatz_prefix': '73', 'order': 5},
    'CP': {'name': 'Clean Park', 'erlos_range': (870000, 879999), 'einsatz_range': (770000, 779999), 'order': 6},
    'MW': {'name': 'Mietwagen', 'erlos_range': (860000, 869999), 'einsatz_range': (760000, 769999), 'order': 7},
    'SO': {'name': 'Sonstige', 'erlos_range': (850000, 859999), 'einsatz_range': (750000, 759999), 'order': 8}
}
```

### Mechanik-Bereich angepasst:

- **8405xx (Karosserie Erlös)** ausgeschlossen → separater Bereich "KA"
- **8406xx (Lackierung Erlös)** ausgeschlossen → extern vergeben
- **745xxx (Karosserie Einsatz)** ausgeschlossen → separater Bereich "KA"
- **746xxx (Lackierung Einsatz)** ausgeschlossen → extern vergeben

### KST-Zuordnung aktualisiert:

```python
kst_zu_bereich = {
    '1': 'NW',  # 10 = Neuwagen
    '2': 'GW',  # 20 = Gebrauchtwagen
    '3': 'ME',  # 30 = Mechanik
    '4': 'KA',  # 40 = Karosserie
    '5': 'TZ',  # 50 = Teile & Zubehör
    '6': 'CP',  # 60 = Clean Park
    '7': 'MW'   # 70 = Mietwagen
}
```

---

## 📊 ERGEBNISSE

**Bereiche Dezember 2025:**
- NW - Neuwagen: 78.992,85 €
- GW - Gebrauchtwagen: 33.313,24 €
- ME - Mechanik: 75.604,86 € (ohne Karosserie/Lack)
- KA - Karosserie: 0,00 € (zu prüfen)
- TZ - Teile & Zubehör: 109.866,38 €
- CP - Clean Park: 0,00 € (zu prüfen)
- MW - Mietwagen: 11.995,18 €
- SO - Sonstige: 0,00 €

---

## ⚠️ OFFENE PUNKTE

1. **Karosserie (KA):** Zeigt 0,00 € - muss geprüft werden, ob 8405xx Konten existieren
2. **Clean Park (CP):** Zeigt 0,00 € - muss geprüft werden, welche Konten verwendet werden sollten
3. **Lackierung:** Wird aktuell ausgeschlossen (extern vergeben) - muss geprüft werden, ob das korrekt ist

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Karosserie-Konten prüfen:** Existieren 8405xx Konten?
2. ⏳ **Clean Park-Konten prüfen:** Welche Konten sollten für CP verwendet werden?
3. ⏳ **Lackierung prüfen:** Sollte 8406xx wirklich ausgeschlossen werden?
