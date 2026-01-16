# Bugfix: Laufzeit-Berechnung für aktive Aufträge (TAG 193)

**Datum:** 2026-01-16  
**Problem:** `laufzeit_min` summiert ALLE Stempelungen des Mechanikers für den Auftrag, nicht nur die aktuelle

---

## 🔍 PROBLEM-ANALYSE

### Symptome aus Locosoft-Daten

**Auftrag 220759:**
- Mitarbeiter 5014 hat mehrere Positionen gestempelt:
  - Position 1.01: 07:54-09:03 (69 Min) - Stmp.Anteil: 7 Min
  - Weitere Positionen mit verschiedenen Stempelzeiten
- Die E-Mail zeigte: **696 Min (11.6 Std)** gestempelt vs 210 Min (3.5 Std) Vorgabe

**Auftrag 39819:**
- Mitarbeiter 5004 hat Position 1.03 gestempelt:
  - Gestempelt: 15.01.26 9:48 bis 10:18 (30 Min)
  - Auftr.AW: 5,00, Stemp.AW: 5,00
- Die E-Mail zeigte: **90 Min (1.5 Std)** gestempelt vs 48 Min (0.8 Std) Vorgabe

### Ursache: Falsche Laufzeit-Berechnung

**Code-Stelle: `api/werkstatt_data.py` Zeile 1315-1325:**

```sql
laufzeit_min = EXTRACT(EPOCH FROM (NOW() - t.start_time))/60
    + COALESCE((
        SELECT SUM(dur) FROM (
            SELECT DISTINCT ON (start_time, end_time) duration_minutes as dur
            FROM times t2
            WHERE t2.order_number = t.order_number
              AND t2.employee_number = t.employee_number
              AND t2.end_time IS NOT NULL
              AND t2.type = 2
        ) dedup
    ), 0)
```

**Das Problem:**
1. `EXTRACT(EPOCH FROM (NOW() - t.start_time))/60` = Aktuelle Stempelung seit `start_time`
2. **PLUS:** Alle bereits abgeschlossenen Stempelungen für diesen Auftrag UND diesen Mechaniker
3. **OHNE Datums-Filter!** → Summiert ALLE Stempelungen, auch von anderen Tagen!

**Beispiel-Szenario:**
- Auftrag 220759 wurde gestern bereits 650 Min gestempelt (von verschiedenen Mechanikern)
- Heute stempelt Mechaniker 5014 sich an (10:00 Uhr)
- Um 10:05 Uhr: `laufzeit_min` = 5 Min (aktuell) + 650 Min (kumulativ) = **655 Min**
- Vorgabe: 210 Min
- Überschreitung: 655 / 210 = **312%** → E-Mail wird gesendet! ❌

**Das Problem:** Die Laufzeit summiert ALLE Stempelungen des Mechanikers für diesen Auftrag, nicht nur die aktuelle Stempelung!

---

## ✅ LÖSUNG

### Problem 1: `laufzeit_min` summiert alle Stempelungen

**Fix:** `laufzeit_min` sollte nur die **aktuelle Stempelung** sein, nicht die Summe aller Stempelungen.

**Aber:** `laufzeit_min` wird für `fortschritt_prozent` verwendet, was die **Gesamtlaufzeit** des Mechanikers für den Auftrag sein sollte.

**Lösung:** 
- `laufzeit_min` = Gesamtlaufzeit des Mechanikers für den Auftrag (korrekt für Fortschritt)
- `heute_session_min` = Nur aktuelle Stempelung heute (korrekt für E-Mail-Alarm)

### Problem 2: E-Mail-Logik verwendet `laufzeit_min` statt `heute_session_min`

**Fix:** E-Mail-Logik sollte `heute_session_min` verwenden (bereits implementiert in TAG 193).

### Problem 3: `laufzeit_min` summiert auch Stempelungen von anderen Tagen

**Fix:** Datums-Filter hinzufügen, wenn abgeschlossene Stempelungen summiert werden.

---

## 🔧 IMPLEMENTIERUNG

### Änderung 1: Datums-Filter für abgeschlossene Stempelungen

**`api/werkstatt_data.py` Zeile 1317-1324:**

```sql
-- VORHER (FALSCH):
SELECT SUM(dur) FROM (
    SELECT DISTINCT ON (start_time, end_time) duration_minutes as dur
    FROM times t2
    WHERE t2.order_number = t.order_number
      AND t2.employee_number = t.employee_number
      AND t2.end_time IS NOT NULL
      AND t2.type = 2
      -- KEIN Datums-Filter! → Summiert ALLE Tage!
) dedup

-- NACHHER (KORREKT):
SELECT SUM(dur) FROM (
    SELECT DISTINCT ON (start_time, end_time) duration_minutes as dur
    FROM times t2
    WHERE t2.order_number = t.order_number
      AND t2.employee_number = t.employee_number
      AND t2.end_time IS NOT NULL
      AND t2.type = 2
      AND DATE(t2.start_time) = %s  -- NUR HEUTE!
) dedup
```

**Aber:** Das ist bereits implementiert in Zeile 1312! Das Problem ist woanders...

### Änderung 2: Prüfe ob `laufzeit_min` auch andere Tage summiert

**Problem:** Die Query in Zeile 1317-1324 hat KEINEN Datums-Filter für `laufzeit_min`, nur für `heute_abgeschlossen_min`!

**Fix:** Datums-Filter auch für `laufzeit_min` hinzufügen:

```sql
laufzeit_min = EXTRACT(EPOCH FROM (NOW() - t.start_time))/60
    + COALESCE((
        SELECT SUM(dur) FROM (
            SELECT DISTINCT ON (start_time, end_time) duration_minutes as dur
            FROM times t2
            WHERE t2.order_number = t.order_number
              AND t2.employee_number = t.employee_number
              AND t2.end_time IS NOT NULL
              AND t2.type = 2
              AND DATE(t2.start_time) = %s  -- NUR HEUTE!
        ) dedup
    ), 0)
```

---

## 📊 ERWARTETE AUSWIRKUNGEN

### Vorher (Bug):
- Auftrag 220759: Mechaniker stempelt an → `laufzeit_min` = 5 Min (aktuell) + 650 Min (alle Tage) = 655 Min
- E-Mail wird sofort gesendet

### Nachher (Fix):
- Auftrag 220759: Mechaniker stempelt an → `laufzeit_min` = 5 Min (aktuell) + 0 Min (nur heute) = 5 Min
- E-Mail wird erst gesendet, wenn:
  - Aktuelle Stempelung ≥ 30 Min **UND**
  - Aktuelle Stempelung > Vorgabe

---

## 🧪 TESTING

### Test-Szenarien:

1. **Mechaniker stempelt an, Auftrag wurde gestern bereits gestempelt:**
   - Erwartung: `laufzeit_min` = nur aktuelle Stempelung (nicht gestern)
   - E-Mail: **KEINE** (nur aktuelle Stempelung zählt)

2. **Mechaniker stempelt an, hat heute bereits andere Positionen gestempelt:**
   - Erwartung: `laufzeit_min` = aktuelle Stempelung + heute abgeschlossene Stempelungen
   - E-Mail: Nur wenn Gesamtlaufzeit heute > Vorgabe

3. **Mechaniker stempelt an, arbeitet 35 Min, überschreitet Vorgabe:**
   - Erwartung: **E-Mail** wird gesendet (≥ 30 Min UND überschreitet)

---

## 📝 ZUSAMMENFASSUNG

**Problem:** `laufzeit_min` summiert ALLE Stempelungen des Mechanikers für den Auftrag (auch von anderen Tagen), nicht nur die aktuelle Stempelung.

**Lösung:** 
1. Datums-Filter für abgeschlossene Stempelungen in `laufzeit_min` hinzufügen
2. E-Mail-Logik verwendet bereits `heute_session_min` (TAG 193 Fix)

**Status:** ⏳ Zu implementieren
