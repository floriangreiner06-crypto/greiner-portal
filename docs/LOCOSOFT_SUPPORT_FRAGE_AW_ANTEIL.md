# Frage an Locosoft-Support: AW-Anteil-Berechnung für Leistungsgrad

**Datum:** 2026-01-XX  
**Betreff:** Berechnung des AW-Anteils für Leistungsgrad-Berechnung  
**Priorität:** Hoch (kritisch für faire Mechaniker-Bewertung)

---

## Problemstellung

Wir versuchen, die Leistungsgrad-Berechnung aus Locosoft in unserem System nachzuvollziehen. Dabei haben wir eine **erhebliche Abweichung** bei der Berechnung des **AW-Anteils** festgestellt.

### Beispiel: Mechaniker 5007 (Tobias Reitmeier), Zeitraum 01.12.2025 - 08.12.2025

**Locosoft-UI zeigt:**
- AW-Anteil: **85:06** (5106 Minuten = 851 AW)
- Stmp.Anteil: **142:23** (8543 Minuten)
- Leistungsgrad: **59,8%**

**Unsere Berechnung ergibt:**
- AW-Anteil: **62:09** (3729 Minuten = 621.5 AW)
- Stmp.Anteil: **142:16** (8536 Minuten) ✅ **Abweichung nur -0.1%**
- Leistungsgrad: **43,7%**

**Abweichung AW-Anteil: -1377 Minuten (-27.0%)**

---

## Unsere Berechnungslogik (getestete Hypothesen)

Wir haben verschiedene Berechnungslogiken getestet:

### Hypothese 1: invoice_date + mechanic_no
```sql
SELECT SUM(l.time_units) 
FROM labours l
JOIN invoices i ON l.invoice_number = i.invoice_number 
WHERE i.invoice_date >= '2025-12-01' AND i.invoice_date <= '2025-12-08'
  AND l.mechanic_no = 5007
  AND l.time_units > 0
```
**Ergebnis:** 264 AW (1584 Min) - **Abweichung: -69.0%**

### Hypothese 2: Proportional zur Stempelzeit pro Position
```sql
-- Stempelzeit pro Position pro Mechaniker
-- AW-Anteil = time_units × (Stempelzeit_Mechaniker / Gesamt-Stempelzeit_Position)
```
**Ergebnis:** 436.5 AW (2619 Min) - **Abweichung: -48.7%**

### Hypothese 3: ALLE Positionen von Aufträgen mit Stempelung
```sql
WITH auftraege_mit_stempelung AS (
    SELECT DISTINCT t.order_number
    FROM times t
    WHERE t.type = 2
      AND t.employee_number = 5007
      AND t.start_time >= '2025-12-01' AND t.start_time < '2025-12-09'
)
SELECT SUM(l.time_units)
FROM auftraege_mit_stempelung ams
JOIN labours l ON ams.order_number = l.order_number
WHERE l.time_units > 0
```
**Ergebnis:** 621.5 AW (3729 Min) - **Abweichung: -27.0%** ✅ **Beste Übereinstimmung**

---

## Konkrete Fragen

### 1. Welche Logik verwendet Locosoft für die AW-Anteil-Berechnung?

- Werden **alle Positionen** eines Auftrags gezählt, bei dem der Mechaniker gestempelt hat?
- Oder nur die Positionen, auf die **tatsächlich gestempelt** wurde?
- Wird der AW-Anteil **proportional zur Stempelzeit** verteilt, wenn mehrere Mechaniker an einem Auftrag arbeiten?

### 2. Welche Filter werden angewendet?

- Wird `is_invoiced = true` gefiltert?
- Wird `labour_type` gefiltert (z.B. nur externe Positionen, keine internen)?
- Wird basierend auf `invoice_date` oder `start_time` (Stempelzeit) gefiltert?

### 3. Wie wird der AW-Anteil bei mehreren Mechanikern berechnet?

**Beispiel-Szenario:**
- Auftrag 12345 hat 3 Positionen: Position 1 = 10 AW, Position 2 = 5 AW, Position 3 = 3 AW
- Mechaniker A stempelt 60 Minuten
- Mechaniker B stempelt 40 Minuten
- Gesamt-Stempelzeit = 100 Minuten

**Frage:** Wie wird der AW-Anteil für Mechaniker A berechnet?
- Option A: 10 AW + 5 AW + 3 AW = 18 AW (alle Positionen)
- Option B: (10 + 5 + 3) × (60 / 100) = 10.8 AW (proportional)
- Option C: Nur Positionen, auf die Mechaniker A gestempelt hat?

### 4. Gibt es spezielle Regeln für Diagnosetechniker?

Mechaniker 5007 (Tobias Reitmeier) ist **Diagnosetechniker**. Gibt es spezielle Berechnungsregeln für diese Rolle?

### 5. Welche Tabellen/Spalten werden verwendet?

Können Sie uns die **exakte SQL-Logik** oder die verwendeten Tabellen/Spalten nennen, die Locosoft für die AW-Anteil-Berechnung verwendet?

---

## Technische Details

**Datenbank:** PostgreSQL (loco_auswertung_db)  
**Relevante Tabellen:**
- `times` (Stempelungen)
- `labours` (Arbeitspositionen mit time_units)
- `invoices` (Rechnungen mit invoice_date)

**Filter-Kriterien:**
- `times.type = 2` (Arbeitszeit, nicht Anwesenheit)
- `times.order_number > 31` (externe Aufträge)
- `labours.time_units > 0` (nur Positionen mit AW)

---

## Erwartetes Ergebnis

Wir benötigen eine **präzise Beschreibung** der Locosoft-Logik, damit wir:
1. Die Leistungsgrad-Berechnung korrekt nachvollziehen können
2. Mechaniker fair bewerten können
3. Die Abweichung von -27.0% eliminieren können

**Ziel:** AW-Anteil-Berechnung mit **< 1% Abweichung** zu Locosoft.

---

## Kontakt

Bei Rückfragen stehen wir gerne zur Verfügung.

**Vielen Dank für Ihre Unterstützung!**
