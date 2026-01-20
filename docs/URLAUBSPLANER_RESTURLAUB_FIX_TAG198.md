# Resturlaub-Berechnung Fix (TAG 198)

**Datum:** 2026-01-18  
**Problem:** Resturlaub wurde falsch berechnet - alle Buchungstypen wurden gezählt statt nur Urlaub

---

## 🐛 PROBLEM

**View `v_vacation_balance_{year}` zählte ALLE Buchungen:**
- ❌ Urlaub (vacation_type_id = 1)
- ❌ Krankheit (vacation_type_id = 5)
- ❌ Zeitausgleich (vacation_type_id = 6)
- ❌ Schulung (vacation_type_id = 9)
- ❌ etc.

**Beispiel - Vanessa Groll:**
- **Vorher:** 27 Anspruch, 0 verbraucht, **4.0 geplant**, 23 Resturlaub ❌ (falsch - zählte 3 Krankheitstage mit)
- **Nachher:** 27 Anspruch, 0 verbraucht, **1.0 geplant**, 26 Resturlaub ✅ (korrekt - nur Urlaub gezählt)

**Impact:**
- ❌ Resturlaub wurde zu niedrig angezeigt
- ❌ Krankheitstage wurden fälschlicherweise vom Urlaubsanspruch abgezogen
- ❌ ZA und Schulung wurden fälschlicherweise vom Urlaubsanspruch abgezogen

---

## ✅ FIX

**View-Definition korrigiert:**
- ✅ Nur `vacation_type_id = 1` (Urlaub) wird gezählt
- ✅ Krankheit, ZA, Schulung werden NICHT vom Resturlaub abgezogen

**Geänderte Views:**
- ✅ `v_vacation_balance_2025` - gefixt
- ✅ `v_vacation_balance_2026` - gefixt
- ✅ `v_vacation_balance_2027` - erstellt (für Jahreswechsel)

**Funktion erstellt:**
- ✅ `create_vacation_balance_view(year)` - erstellt/korrigiert View für beliebiges Jahr

---

## 📝 CODE-ÄNDERUNGEN

### View-Definition (vorher):
```sql
-- Verbrauchte Tage (approved) - ZÄHLTE ALLE TYPEN ❌
SELECT SUM(...)
FROM vacation_bookings vb
WHERE vb.status = 'approved'
-- FEHLT: AND vb.vacation_type_id = 1
```

### View-Definition (nachher):
```sql
-- Verbrauchte Tage (approved) - NUR URLAUB ✅
SELECT SUM(...)
FROM vacation_bookings vb
WHERE vb.status = 'approved'
  AND vb.vacation_type_id = 1  -- TAG 198: Nur Urlaub zählen!
```

---

## 🧪 TEST-ERGEBNISSE

**Vanessa Groll (2026):**
- 1 Urlaubstag pending (09.01.)
- 3 Krankheitstage pending (12.-14.01.)
- **Vorher:** 4.0 geplant, 23 Resturlaub ❌
- **Nachher:** 1.0 geplant, 26 Resturlaub ✅

**Bianca Greindl (2026):**
- 41 Tage Anspruch (27 Standard + 14 Resturlaub?)
- 0 verbraucht, 0 geplant
- **Resturlaub:** 41 Tage ✅ (korrekt)

**Herbert Huber (2026):**
- 27 Tage Anspruch
- 0 verbraucht, 0 geplant (alle Buchungen sind in 2025)
- **Resturlaub:** 27 Tage ✅ (korrekt)

---

## 📋 DATEIEN

1. ✅ `scripts/migrations/fix_vacation_balance_view_resturlaub_tag198.sql` - Fix für 2026
2. ✅ `scripts/migrations/fix_vacation_balance_views_all_years_tag198.sql` - Fix für alle Jahre + Funktion

---

## ✅ STATUS

- [x] View 2025 gefixt
- [x] View 2026 gefixt
- [x] View 2027 erstellt
- [x] Funktion für zukünftige Jahre erstellt
- [x] Test bestätigt (Vanessa zeigt korrekte Werte)

**Status:** ✅ **Abgeschlossen - Resturlaub wird jetzt korrekt berechnet**
