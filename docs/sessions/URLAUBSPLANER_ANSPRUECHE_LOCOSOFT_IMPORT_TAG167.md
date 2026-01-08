# Urlaubsansprüche aus Locosoft importieren - TAG 167

**Datum:** 2026-01-05  
**Problem:** Jahresurlaubsanspruch (J.Url.ges.) aus Locosoft importieren

---

## Problem

Der Jahresurlaubsanspruch (J.Url.ges.) ist in Locosoft nicht direkt in der Datenbank gespeichert, sondern wird in der Anwendung berechnet als:

```
J.Url.ges. = Standard-Anspruch + Resturlaub aus Vorjahr
```

**Beispiel Edith:**
- Locosoft zeigt: J.Url.ges. = 39 Tage
- Portal berechnet: 27 Tage (Standard) + 0 Tage (Resturlaub) = 27 Tage
- **Abweichung:** 12 Tage fehlen

---

## Berechnungslogik

### Aktuelle Berechnung (Script)

1. **Standard-Anspruch:** 27 Tage (fest)
2. **Resturlaub Vorjahr:**
   - Anspruch Vorjahr (aus Portal `vacation_entitlements`)
   - Verbraucht Vorjahr (aus Locosoft `absence_calendar`)
   - Resturlaub = max(0, Anspruch - Verbraucht)
3. **Gesamtanspruch:** Standard + Resturlaub

### Problem bei Edith

- **2025:** Anspruch = 32 Tage (27 + 5 added_manually), Verbraucht = 35 Tage
- **Resturlaub 2025:** 32 - 35 = -3 Tage → wird auf 0 gesetzt
- **2026:** Standard 27 + Resturlaub 0 = 27 Tage
- **ABER:** Locosoft zeigt 39 Tage

**Mögliche Ursachen:**
1. Edith hat einen individuellen Standard-Anspruch (z.B. 30 Tage statt 27)
2. Resturlaub wird anders berechnet (z.B. aus 2024 übernommen)
3. Locosoft verwendet eine andere Berechnungslogik

---

## Lösung

### Option 1: Manuelle Pflege (aktuell)
- Ansprüche werden manuell in `vacation_entitlements` gepflegt
- Edith wurde auf 39 Tage korrigiert

### Option 2: Locosoft-Export
- Export aus Locosoft-Anwendung (J.Url.ges. pro Mitarbeiter)
- Import in Portal

### Option 3: Verbesserte Berechnung
- Script verwendet individuellen Standard-Anspruch (falls vorhanden)
- Berücksichtigt `added_manually` und `carried_over` korrekt

---

## Script: `import_vacation_entitlements_2026_from_locosoft.py`

**Aktuelle Logik:**
```python
def get_vacation_entitlement_from_locosoft(...):
    # Standard-Anspruch: 27 Tage
    standard_anspruch = 27.0
    
    # Resturlaub Vorjahr = Anspruch Vorjahr - Verbraucht Vorjahr
    resturlaub_vorjahr = max(0.0, anspruch_vorjahr - verbraucht_vorjahr)
    
    # Gesamtanspruch = Standard + Resturlaub
    gesamt_anspruch = standard_anspruch + resturlaub_vorjahr
```

**Problem:** Verwendet festen Standard 27 Tage, berücksichtigt keine individuellen Ansprüche.

---

## Nächste Schritte

1. ✅ Script erstellt: Berechnet Standard + Resturlaub
2. ⏳ Prüfen ob individuelle Standard-Ansprüche in Locosoft gespeichert sind
3. ⏳ Locosoft-Export-Funktion prüfen
4. ⏳ Berechnungslogik mit HR abgleichen

---

**Status:** Script funktioniert für Standard-Fälle, aber nicht für individuelle Ansprüche wie Edith (39 Tage).

