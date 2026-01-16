# Hybrid-Ansatz Implementierung - TAG 194

**Datum:** 2026-01-16  
**Status:** ⚠️ **IN ARBEIT** - Parameter-Anzahl-Problem

---

## Problem

Die Query hat nach Formatierung nur **9 %s Platzhalter**, aber wir übergeben **9 Parameter**. `auftraege_mit_aw` fehlt in der formatierten Query.

---

## Implementierung

### CTE-Struktur

1. **stempelungen_roh** - Basis-Stempelungen (2x %s)
2. **auftraege_mit_aw** - Aufträge MIT AW (verwendet stempelungen_roh, keine eigenen Parameter)
3. **positionen_ohne_aw_auf_auftraegen_mit_aw** - Positionen OHNE AW auf Aufträgen MIT AW
4. **positionen_ohne_aw_anteilig** - 10.6% der Stempelzeit
5. **st_anteil_hybrid** - Zeit-Spanne + Positionen OHNE AW

### Parameter

```python
params = [
    von, bis,  # stempelungen_dedupliziert (erste CTE) - 2x %s
    von, bis,  # stempelzeit_leistungsgrad (TAG 192) - 2x %s
    von, bis,  # stempelungen_roh (TAG 194) - 2x %s
    von, bis,  # anwesenheit - 2x %s
    MECHANIKER_EXCLUDE  # TAG 192 - 1x %s
]
# Gesamt: 9 Parameter
```

---

## Nächste Schritte

1. ✅ CTE-Struktur korrigiert (auftraege_mit_aw verwendet stempelungen_roh)
2. ⚠️ Parameter-Anzahl angepasst (9 Parameter)
3. ❌ Test fehlgeschlagen - `auftraege_mit_aw` fehlt in formatierten Query

**Problem:** Die Query-Struktur scheint korrekt zu sein, aber `auftraege_mit_aw` wird nicht in die formatierte Query eingefügt.

**Mögliche Ursachen:**
- CTE-Reihenfolge-Problem
- Formatierungsfehler in f-string
- SQL-Syntax-Fehler

---

**Status:** ⚠️ **MUSS KORRIGIERT WERDEN**
