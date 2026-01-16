# Bugfix: Alarm-E-Mail bei Zeitüberschreitung (TAG 193)

**Datum:** 2026-01-16  
**Problem:** E-Mails werden gesendet, obwohl Mechaniker erst kurz angestempelt haben

---

## 🔍 PROBLEM-ANALYSE

### Symptome
- Mitarbeiter erhalten Alarm-E-Mails, obwohl sie erst kurz angestempelt haben
- Beispiel 1: Auftrag 220759 - 696 min (11.6 Std) gestempelt vs 210 min (3.5 Std) Vorgabe
- Beispiel 2: Auftrag 39819 - 90 min (1.5 Std) gestempelt vs 48 min (0.8 Std) Vorgabe

### Ursache

**Das Problem liegt in der Berechnung der Laufzeit für aktive Aufträge:**

1. **Für aktive Aufträge** wird `laufzeit_min` verwendet, was die **kumulative Laufzeit** ist:
   - Aktuelle Stempelung: `NOW() - start_time` (seit Anstempeln)
   - PLUS: Alle bereits abgeschlossenen Stempelungen für diesen Auftrag/Mechaniker

2. **Beispiel-Szenario:**
   - Auftrag 220759 hat bereits 650 Minuten von früheren Mechanikern/Stempelungen
   - Neuer Mechaniker stempelt sich an (10:00 Uhr)
   - Um 10:05 Uhr läuft die Task (alle 15 Min)
   - `laufzeit_min` = 5 Min (aktuell) + 650 Min (kumulativ) = **655 Min**
   - Vorgabe: 210 Min
   - Überschreitung: 655 / 210 = **312%** → E-Mail wird gesendet! ❌

3. **Das Problem:** Die E-Mail wird gesendet, obwohl der Mechaniker erst 5 Minuten angestempelt hat!

### Code-Stelle

**`celery_app/tasks.py` Zeile 268:**
```python
laufzeit_min = float(ueberschritt.get('laufzeit_min', ueberschritt.get('gestempelt_min', 0)))
```

**`api/werkstatt_data.py` Zeile 1315-1325:**
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

**Das Problem:** `laufzeit_min` ist die **kumulative Laufzeit**, nicht nur die aktuelle Stempelung!

---

## ✅ LÖSUNG

### Option 1: Nur aktuelle Stempelung verwenden (EMPFOHLEN)

Für aktive Aufträge sollte nur `heute_session_min` verwendet werden (die aktuelle Stempelung heute), nicht die Gesamtlaufzeit.

**Vorteile:**
- E-Mails werden nur gesendet, wenn die **aktuelle Stempelung** die Vorgabe überschreitet
- Keine falschen Alarme bei kurz angestempelten Mechanikern
- Logisch: Nur die aktuelle Arbeit zählt

**Nachteile:**
- E-Mails werden nicht gesendet, wenn der Auftrag bereits überschritten ist, aber der aktuelle Mechaniker noch nicht lange arbeitet
- (Aber das ist eigentlich korrekt - der aktuelle Mechaniker hat ja noch nichts falsch gemacht)

### Option 2: Mindestlaufzeit-Schwelle

Eine Mindestlaufzeit-Schwelle einbauen (z.B. mindestens 30 Minuten seit Anstempeln), bevor eine E-Mail gesendet wird.

**Vorteile:**
- Verhindert E-Mails bei sehr kurzen Stempelungen
- Behält kumulative Laufzeit bei (für abgeschlossene Aufträge)

**Nachteile:**
- Komplexer (zusätzliche Prüfung)
- E-Mails werden verzögert gesendet

### Empfehlung: Option 1 + Option 2 kombiniert

1. **Für aktive Aufträge:** Nur `heute_session_min` verwenden (aktuelle Stempelung)
2. **Zusätzlich:** Mindestlaufzeit-Schwelle (z.B. 30 Min) für aktive Aufträge
3. **Für abgeschlossene Aufträge:** Gesamtlaufzeit bleibt (korrekt)

---

## 🔧 IMPLEMENTIERUNG

### Änderungen in `celery_app/tasks.py`

**Zeile 268-282:** Laufzeit-Berechnung für aktive Aufträge korrigieren:

```python
# TAG 193: FIX - Für aktive Aufträge: Nur heute_session_min verwenden
# Für abgeschlossene Aufträge: Gesamtlaufzeit
if 'heute_session_min' in ueberschritt:
    # Aktiver Auftrag: Nur aktuelle Stempelung heute
    laufzeit_min = float(ueberschritt.get('heute_session_min', 0))
    
    # Zusätzlich: Mindestlaufzeit-Schwelle (30 Min) für aktive Aufträge
    if laufzeit_min < 30:
        logger.debug(f"Auftrag {auftrag_nr}: Nur {laufzeit_min:.0f} Min gestempelt (< 30 Min) - überspringe")
        continue
else:
    # Abgeschlossener Auftrag: Gesamtlaufzeit
    laufzeit_min = float(ueberschritt.get('laufzeit_min', ueberschritt.get('gestempelt_min', 0)))
```

---

## 📊 ERWARTETE AUSWIRKUNGEN

### Vorher (Bug):
- Auftrag 220759: Mechaniker stempelt an → 5 Min später E-Mail (weil kumulativ 655 Min)
- Auftrag 39819: Mechaniker stempelt an → 5 Min später E-Mail (weil kumulativ 90 Min)

### Nachher (Fix):
- Auftrag 220759: Mechaniker stempelt an → 5 Min später **KEINE** E-Mail (nur 5 Min aktuell)
- Auftrag 39819: Mechaniker stempelt an → 5 Min später **KEINE** E-Mail (nur 5 Min aktuell)
- E-Mail wird erst gesendet, wenn:
  - Aktuelle Stempelung ≥ 30 Min **UND**
  - Aktuelle Stempelung > Vorgabe

---

## 🧪 TESTING

### Test-Szenarien:

1. **Mechaniker stempelt an, Auftrag bereits überschritten:**
   - Erwartung: **KEINE** E-Mail (nur aktuelle Stempelung zählt)

2. **Mechaniker stempelt an, arbeitet 35 Min, überschreitet Vorgabe:**
   - Erwartung: **E-Mail** wird gesendet (≥ 30 Min UND überschreitet)

3. **Abgeschlossener Auftrag, überschreitet Vorgabe:**
   - Erwartung: **E-Mail** wird gesendet (Gesamtlaufzeit bleibt)

---

## 📝 ZUSAMMENFASSUNG

**Problem:** E-Mails werden gesendet, obwohl Mechaniker erst kurz angestempelt haben, weil die kumulative Laufzeit verwendet wird.

**Lösung:** Für aktive Aufträge nur `heute_session_min` verwenden (aktuelle Stempelung) + Mindestlaufzeit-Schwelle (30 Min).

**Status:** ⏳ Zu implementieren
