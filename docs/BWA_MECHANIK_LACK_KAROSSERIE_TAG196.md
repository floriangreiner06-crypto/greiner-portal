# BWA Mechanik - Lack/Karosserie Ausschluss - TAG 196

**Datum:** 2026-01-16  
**TAG:** 196  
**Status:** ⚠️ **IN BEARBEITUNG**

---

## 🎯 PROBLEM IDENTIFIZIERT

**Mechanik-Bereich Dezember 2025:**
- DRIVE: 93.862,80 €
- GlobalCube: 86.419,00 € (zeigt "Mechanik+Karo")
- Differenz: +7.443,80 € (DRIVE zu hoch)

**Erkenntnis:** Lack und Karosserie werden extern vergeben und sollten ausgeschlossen werden.

---

## 📊 ANALYSE

### Konten-Werte Dezember 2025:

| Bereich | Konten | Wert |
|---------|--------|------|
| **Lackierung Erlös** | 8406xx | 18.257,94 € |
| **Lackierung Einsatz** | 746xxx | 0,00 € (keine Buchungen) |
| **Karosserie Erlös** | 8405xx | 0,00 € (keine Buchungen) |
| **Karosserie Einsatz** | 745xxx | 0,00 € (keine Buchungen) |

### Test-Ergebnisse:

| Variante | Bruttoertrag | Differenz zu GlobalCube |
|----------|--------------|------------------------|
| **Alle 84xxxx (aktuell)** | 93.922,38 € | **+7.503,38 €** |
| **Ohne 8406xx (Lackierung)** | 75.664,44 € | **-10.754,56 €** |
| **Ohne 8405xx + 8406xx** | 75.664,44 € | **-10.754,56 €** |

---

## ⚠️ PROBLEM

**Ohne 8406xx (Lackierung) ist der Wert zu niedrig!**

- 8406xx Wert: 18.257,94 €
- Ohne 8406xx: 75.664,44 €
- GlobalCube: 86.419,00 €
- Differenz: -10.754,56 €

**Das bedeutet:**
- Wenn wir 8406xx ausschließen, fehlen 10.754,56 €
- Aber 8406xx ist nur 18.257,94 €
- Das passt nicht zusammen!

**Mögliche Ursachen:**
1. GlobalCube zeigt "Mechanik+Karo" - vielleicht ist Karosserie doch enthalten?
2. Es gibt andere Konten, die ausgeschlossen werden sollten?
3. GlobalCube verwendet andere Filter-Logik?

---

## ✅ IMPLEMENTIERT

**Aktuell:** Nur 8406xx (Lackierung Erlös) und 746xxx (Lackierung Einsatz) ausgeschlossen.

**Code-Änderungen:**
- `_berechne_bereich_werte()` - Mechanik-Bereich (Erlös und Einsatz)
- Zeile 1701: `erlos_where` für Mechanik ohne 8406xx
- Zeile 1723: `einsatz_where` für Mechanik ohne 746xxx

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Prüfen, was GlobalCube genau zeigt:**
   - Enthält GlobalCube "Mechanik+Karo" wirklich Karosserie?
   - Oder bedeutet "Karo" etwas anderes?

2. ⏳ **Weitere Konten prüfen:**
   - Gibt es andere 84xxxx Konten, die ausgeschlossen werden sollten?
   - Gibt es andere 74xxxx Konten, die ausgeschlossen werden sollten?

3. ⏳ **Filter-Logik prüfen:**
   - Verwendet GlobalCube andere Filter für Mechanik?
   - Gibt es Standort-spezifische Unterschiede?

---

## 📊 STATUS

- ✅ Code-Änderung implementiert (nur 8406xx ausgeschlossen)
- ⚠️ Ergebnis noch nicht korrekt (zu niedrig)
- ⏳ Weitere Analyse erforderlich
