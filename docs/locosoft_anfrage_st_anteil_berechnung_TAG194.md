# Locosoft Support-Anfrage: St-Anteil Berechnung

**Betreff:** Dringend - St-Anteil Berechnung weicht ab, benötige exakte Formel

**Priorität:** Hoch  
**Datum:** 2026-01-16  
**System:** Greiner Portal DRIVE (Integration mit Locosoft)

---

## Problem

Wir versuchen, die St-Anteil (Stempel Anteil) Berechnung aus Locosoft in unserem System nachzubilden. Trotz Zugriff auf die gleichen Rohdaten (times, labours) weichen unsere Ergebnisse bei bestimmten Mechanikern erheblich ab.

---

## Problembeschreibung

Bei der Berechnung des "St-Anteil" für Mechaniker zeigen sich Abweichungen zwischen unserer Implementierung und den Werten in Locosoft. Insbesondere bei Mechanikern mit vielen Stempelungen auf mehrere Positionen oder Positionen ohne Arbeitswerte (AW) sind die Abweichungen größer.

### Beispiel: Mechaniker 5007 (Reitmeier, Tobias)

**Zeitraum:** 01.01.2026 - 16.01.2026

**Locosoft UI (Zeitraum-GESAMTSUMMEN):**
- AW-Anteil: 52:35 (3155 Min)
- Stmp.Anteil: 82:51 (4971 Min)
- Leistungsgrad: 63.5%

**Unsere Berechnung:**
- AW-Anteil: 53:12 (3192 Min) ✅ **passt sehr gut (1.2% Diff)**
- St-Anteil: 56:00 (3360 Min) ❌ **Abweichung: 1611 Min (32.4%)**

---

## Unsere aktuelle Implementierung

Wir berechnen den "St-Anteil" position-basiert mit anteiliger Verteilung:

1. **Stempelungen deduplizieren** pro Mechaniker/Auftrag/Position/Zeit
2. **Anteilige Verteilung** bei Stempelungen auf mehrere Positionen:
   - Wenn eine Stempelung auf mehrere Positionen geht, wird die Stempelzeit anteilig nach AW verteilt
   - Beispiel: 60 Min Stempelung auf Position 1.1 (10 AW) und 1.2 (10 AW)
     → 30 Min pro Position = 30 Min St-Anteil
3. **Aggregation** pro Position und Mechaniker

**SQL-Logik:**
```sql
-- Stempelungen deduplizieren
stempelungen_roh AS (
    SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
        employee_number, order_number, order_position, order_position_line,
        start_time, end_time,
        EXTRACT(EPOCH FROM (end_time - start_time)) / 60 as stempel_minuten
    FROM times
    WHERE type = 2 AND end_time IS NOT NULL
        AND order_number > 31
        AND order_position IS NOT NULL
    ORDER BY employee_number, order_number, order_position, order_position_line, start_time, end_time
),
-- Anteilige Verteilung basierend auf AW
stempelungen_mit_anteil AS (
    SELECT
        sr.*,
        l.time_units as aw_position,
        SUM(l.time_units) OVER (
            PARTITION BY sr.employee_number, sr.order_number, sr.start_time, sr.end_time
        ) as gesamt_aw_stempelung
    FROM stempelungen_roh sr
    JOIN labours l ON sr.order_number = l.order_number
        AND sr.order_position = l.order_position
        AND sr.order_position_line = l.order_position_line
    WHERE l.time_units > 0
),
-- Stempelanteil pro Position (anteilig verteilt)
stempelanteil_pro_position AS (
    SELECT
        employee_number, order_number, order_position, order_position_line,
        SUM(stempel_minuten * (aw_position / NULLIF(gesamt_aw_stempelung, 0))) as stempelanteil_minuten
    FROM stempelungen_mit_anteil
    GROUP BY employee_number, order_number, order_position, order_position_line
)
```

---

## Getestete Varianten

Wir haben verschiedene Berechnungsvarianten getestet, um die Locosoft-Logik nachzubilden:

| Variante | Ergebnis | Diff zu Locosoft |
|----------|----------|------------------|
| Position-basiert (anteilig verteilt) | 3360 Min | 1611 Min (32.4%) |
| OHNE anteilige Verteilung | 3602 Min | 1369 Min (27.5%) |
| Zeit-Spanne (erste bis letzte Stempelung) | 3691 Min | 1280 Min (25.7%) |
| Zeit-Spanne MINUS Lücken | 3602 Min | 1369 Min (27.5%) |
| Zeit-Spanne MINUS Lücken MINUS Pausen | 3294 Min | 1677 Min (33.7%) |

**Keine der Varianten passt genau zu Locosoft's 4971 Min!**

---

## Spezielle Fälle bei Mechaniker 5007

- **300 Stempelungen** auf **206 Positionen**
- **203 Positionen OHNE AW** mit **12049 Min** Stempelzeit
- **43 von 57 Stempelungen** gehen auf **mehrere Positionen** (75.4%)
- **Stempelzeit auf mehrere Positionen:** 2585 Min

**Frage:** Werden Positionen OHNE AW in der "St-Anteil"-Berechnung berücksichtigt? Wenn ja, wie?

---

## Vergleich mit anderem Mechaniker

Bei Mechaniker 5014 (Litwin, Jaroslaw) im gleichen Zeitraum passt unsere Berechnung besser:

**Locosoft UI:**
- Stmp.Anteil: 34:38 (2078 Min)

**Unsere Berechnung:**
- St-Anteil: 34:42 (2082 Min) ✅ **nur 4 Min Differenz (0.2%)**

**Unterschied zu Mechaniker 5007:**
- Weniger Stempelungen auf mehrere Positionen
- Weniger Positionen OHNE AW

---

## Konkrete Fragen

1. **Wie wird "St-Anteil" (Stempel Anteil) genau berechnet?**
   - Wird die Stempelzeit anteilig verteilt, wenn eine Stempelung auf mehrere Positionen geht?
   - Oder wird die gesamte Stempelzeit gezählt?

2. **Werden Positionen OHNE AW (time_units = 0) berücksichtigt?**
   - Wenn ja, wie wird die Stempelzeit für diese Positionen berechnet?
   - Wird die gesamte Stempelzeit gezählt oder anteilig verteilt?

3. **Gibt es Unterschiede zwischen "St-Anteil" und "Stmp.Anteil"?**
   - Werden beide gleich berechnet?
   - Oder gibt es unterschiedliche Berechnungslogiken?

4. **Wie werden Stempelungen dedupliziert?**
   - Pro Mechaniker/Auftrag/Position/Zeit?
   - Oder gibt es eine andere Deduplizierungslogik?

5. **Werden bestimmte Aufträge oder Positionen ausgeschlossen?**
   - Gibt es Filter, die wir noch nicht berücksichtigen?

---

## Daten für Analyse

Falls Sie die Berechnung nachvollziehen möchten, können wir Ihnen gerne:
- Export der Stempelungen für Mechaniker 5007 im Zeitraum 01.01-16.01.2026
- Detaillierte Aufschlüsselung der Positionen und AW-Werte
- Vergleichswerte für andere Mechaniker

zur Verfügung stellen.

---

## Vielen Dank

Wir würden uns sehr über eine Klärung der Berechnungslogik freuen, damit wir die KPI-Berechnungen in DRIVE korrekt nachbilden können.

**Kontakt:**  
Greiner Portal DRIVE  
[Ihre Kontaktdaten]

---

## Anhang: Technische Details

**Datenbank:** PostgreSQL (Locosoft DB, read-only)  
**Tabellen:** `times`, `labours`, `orders`  
**Filter:** 
- `times.type = 2` (Arbeitszeit)
- `times.order_number > 31` (externe Aufträge)
- `times.order_position IS NOT NULL`
- `times.order_position_line IS NOT NULL`

**Zeitraum:** 01.01.2026 - 16.01.2026
