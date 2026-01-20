# BUGFIX: Felder vertauscht in Werkstatt-Dashboard (TAG 196)

**Datum:** 2026-01-18  
**Status:** ⚠️ **IN ARBEIT**

---

## 🚨 Problem

Das Werkstatt-Dashboard zeigt falsche Werte:
- Stempelzeit: 2.113,3 Std (sollte eigentlich Anwesenheit sein)
- Anwesenheit: 626,4 Std (sollte eigentlich Stempelzeit sein)
- **Stempelzeit > Anwesenheit ist physikalisch unmöglich!**

---

## 🔍 Root Cause

Die Felder sind in `api/werkstatt_data.py` Zeile 383-385 vertauscht:

**VORHER (FALSCH):**
```python
'stempelzeit': st_anteil_position.get(emp_nr, 0),  # Gibt 2.113 Std zurück
'anwesenheit': anwesenheit.get(emp_nr, {}).get('anwesend_min', 0),  # Gibt 626 Std zurück
```

**Problem:**
- `get_st_anteil_position_basiert()` gibt tatsächlich die **Anwesenheit** zurück (größere Zahl)
- `get_anwesenheit_rohdaten()` gibt tatsächlich die **Stempelzeit** zurück (kleinere Zahl)

---

## ✅ Fix

**NACHHER (KORREKT):**
```python
'stempelzeit': anwesenheit.get(emp_nr, {}).get('anwesend_min', 0),  # FIX: War st_anteil_position
'anwesenheit': st_anteil_position.get(emp_nr, 0),  # FIX: War anwesenheit.get()
```

---

## ⚠️ WARNUNG

**Dieser Fix ist noch nicht vollständig getestet!**

Nach dem Fix:
- Stempelzeit: 3.119,6 Std (immer noch > Anwesenheit) ❌
- Anwesenheit: 2.113,3 Std

**Das Problem ist komplexer als erwartet!**

Mögliche Ursachen:
1. Anwesenheitsdaten (type=1) sind unvollständig
2. Stempelzeit-Berechnung ist falsch (doppelte Zählung?)
3. Die Funktionen selbst geben falsche Werte zurück

---

## 🔧 Nächste Schritte

1. **Prüfe Anwesenheitsdaten:**
   - Sind `type=1` Daten vollständig?
   - Warum gibt `get_anwesenheit_rohdaten()` nur 626 Std zurück statt 3.244 Std?

2. **Prüfe Stempelzeit-Berechnung:**
   - Warum gibt `get_st_anteil_position_basiert()` 2.113 Std zurück?
   - Ist der 75% Faktor korrekt?

3. **Test mit echten Daten:**
   - Prüfe einzelne Mechaniker
   - Vergleiche mit Locosoft UI

---

**Erstellt:** TAG 196  
**Status:** ⚠️ **IN ARBEIT - Fix noch nicht vollständig**
