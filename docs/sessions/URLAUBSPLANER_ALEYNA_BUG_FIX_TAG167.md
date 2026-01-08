# Urlaubsplaner Aleyna Bug Fix - TAG 167

**Datum:** 2026-01-05  
**Problem:** Aleyna Irep 05.01.2026 - In DRIVE wird "Schulung" angezeigt, aber in Locosoft steht "Krankheit"

---

## Problem

**User-Report:**
- In DRIVE wird für Aleyna am 05.01.2026 "Schulung" angezeigt
- In Locosoft steht für Aleyna am 05.01.2026 "Krankheit" (reason: 'Krn')

**Untersuchung:**
1. ✅ DRIVE DB: `vacation_type_id = 5` = "Krankheit" (korrekt)
2. ✅ Locosoft: `reason = 'Krn'` = Krankheit (korrekt)
3. ❌ Frontend: `CLS = {5:'schulung'}` und `TYPE_NAME = {5:'Schulung'}` (FALSCH!)

---

## Root Cause

**Frontend-Mapping falsch:**
```javascript
// VORHER (FALSCH):
const CLS = {1:'urlaub',2:'urlaub',3:'krank',5:'schulung',6:'za'};
const TYPE_NAME = {1:'Urlaub',2:'Sonderurlaub',3:'Krank',5:'Schulung',6:'Zeitausgleich'};
```

**Problem:**
- `vacation_type_id = 5` sollte "Krankheit" sein (wie in DB)
- `vacation_type_id = 9` sollte "Schulung" sein (wie in DB)

**DB-Schema:**
```
vacation_types:
  id=1: Urlaubstag (beantragt)
  id=2: Urlaubstag (genehmigt)
  id=3: Urlaubstag (abgelehnt)
  id=5: Krankheit  ← sollte im Frontend "Krankheit" sein
  id=6: Ausgleichstag
  id=9: Schulung   ← sollte im Frontend "Schulung" sein
  id=12: Seminar
```

---

## Fix

**Frontend-Mapping korrigiert:**
```javascript
// NACHHER (KORREKT):
const ICON = {1:'🏖️',2:'👶',3:'🤒',5:'🤒',6:'⏰',9:'📚',12:'📚'};
const CLS = {1:'urlaub',2:'urlaub',3:'krank',5:'krank',6:'za',9:'schulung',12:'schulung'};
const TYPE_NAME = {1:'Urlaub',2:'Sonderurlaub',3:'Krank',5:'Krankheit',6:'Zeitausgleich',9:'Schulung',12:'Seminar'};
```

**Änderungen:**
- ✅ `5: 'krank'` statt `5: 'schulung'` (CLS)
- ✅ `5: 'Krankheit'` statt `5: 'Schulung'` (TYPE_NAME)
- ✅ `9: 'schulung'` hinzugefügt (CLS)
- ✅ `9: 'Schulung'` hinzugefügt (TYPE_NAME)
- ✅ `12: 'schulung'` hinzugefügt (CLS)
- ✅ `12: 'Seminar'` hinzugefügt (TYPE_NAME)
- ✅ Icons für 9 und 12 hinzugefügt

---

## Test

**Erwartetes Ergebnis:**
- Aleyna am 05.01.2026 sollte jetzt "Krankheit" (🤒) anzeigen, nicht "Schulung" (📚)
- Schulungen sollten mit `vacation_type_id = 9` korrekt als "Schulung" angezeigt werden

---

**Status:** ✅ Frontend-Mapping korrigiert, Template synchronisiert

