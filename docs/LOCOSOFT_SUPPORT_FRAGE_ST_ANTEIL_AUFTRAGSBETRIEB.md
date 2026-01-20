# Locosoft Support-Anfrage: St-Anteil Berechnung nach Auftragsbetrieb

**Betreff:** Dringend - St-Anteil Berechnung weicht ab, benötige exakte Formel nach Auftragsbetrieb

**Priorität:** Hoch  
**Datum:** 2026-01-19  
**System:** Greiner Portal DRIVE (Integration mit Locosoft)  
**Referenz:** Vorherige Anfrage zu AW-Anteil (TAG 192)

---

## Problem

Wir versuchen, die **St-Anteil (Stempelzeit)** Berechnung aus Locosoft in unserem System nachzubilden. Trotz Zugriff auf die gleichen Rohdaten (`times` Tabelle) weichen unsere Ergebnisse ab, besonders wenn die Stempelzeit nach **Auftragsbetrieb** aufgeteilt wird.

**Wichtig:** Wir haben verstanden, dass:
- **MA-Betrieb:** Hier ist die Anwesenheit (type=1)
- **Auftragsbetrieb:** Hier wird die Stempelzeit (type=2) nach Auftragsbetrieb aufgeteilt

---

## Konkretes Beispiel: MA 5007 (Reitmeier) - 07.01.2026

### Locosoft-Werte (aus UI):
```
MA-Betrieb 01 DEGO:
  St-Ant.: 9:06 Std (9 Stunden 6 Minuten)

MA-Betrieb 01 DEGO + Auftragsbetrieb 02 DEGH:
  St-Ant.: 3:59 Std (3 Stunden 59 Minuten)

GESAMT: 13:05 Std = 9:06 + 3:59 ✓
```

### Unsere Berechnungen:

| Methode | DEGO | DEGH | GESAMT |
|---------|------|------|--------|
| **Locosoft** | 9:06 | 3:59 | 13:05 |
| **Auftrags-basiert** | 3:21 | 4:43 | 8:04 |
| **Zeit-Spanne** | 8:05 | 5:17 | - |
| **Position-basiert** | 13:31 | 24:31 | 38:02 |

**Ergebnis:**
- **DEGH:** Auftrags-basierte Berechnung (4:43) ist sehr nah an Locosoft (3:59) ✅
- **DEGO:** Zeit-Spanne (8:05) ist nah an Locosoft (9:06), aber noch 1:01 Std Abweichung ❌

---

## Konkrete Fragen

### 1. St-Anteil Berechnung nach Auftragsbetrieb

**Frage 1.1:** Wie wird die St-Anteil nach Auftragsbetrieb aufgeteilt?
- Wird die Stempelzeit (type=2) nach dem `subsidiary` Feld der `orders` Tabelle gruppiert?
- Oder gibt es eine andere Logik zur Zuordnung von Stempelungen zu Auftragsbetrieben?

**Frage 1.2:** Warum gibt es unterschiedliche Werte für DEGO vs. DEGH?
- Verwendet Locosoft unterschiedliche Berechnungsmethoden für verschiedene Betriebe?
- Oder gibt es unterschiedliche Filterkriterien?

**Frage 1.3:** Was bedeutet "MA-Betrieb 01 DEGO + Auftragsbetrieb 02 DEGH"?
- Ist das die Summe der Stempelzeiten auf Aufträgen, die zu DEGH gehören?
- Oder gibt es eine andere Interpretation?

---

### 2. Deduplizierung von Stempelungen

**Frage 2.1:** Wie werden überlappende Stempelungen dedupliziert?
- Wenn ein Mechaniker zur gleichen Zeit auf verschiedenen Positionen desselben Auftrags stempelt, wie wird das gezählt?
- Beispiel: 08:00-09:00 auf Position 1 und 08:00-09:00 auf Position 2 desselben Auftrags
  - Zählt das als 1 Std (auftrags-basiert) oder 2 Std (position-basiert)?

**Frage 2.2:** Wie werden überlappende Stempelungen auf verschiedenen Aufträgen gezählt?
- Beispiel: 08:00-09:00 auf Auftrag A und 08:00-09:00 auf Auftrag B
  - Zählt das als 1 Std (zeit-basiert) oder 2 Std (auftrags-basiert)?

**Frage 2.3:** Welche Deduplizierungs-Logik wird für DEGO verwendet?
- Unsere Zeit-Spanne (8:05) ist nah an Locosoft (9:06), aber nicht perfekt
- Wird für DEGO die Zeit-Spanne (erste bis letzte Stempelung) verwendet?
- Oder gibt es eine andere Methode?

**Frage 2.4:** Welche Deduplizierungs-Logik wird für DEGH verwendet?
- Unsere auftrags-basierte Berechnung (4:43) ist sehr nah an Locosoft (3:59)
- Wird für DEGH die Summe der auftrags-basierten Stempelzeiten verwendet?
- Oder gibt es eine andere Methode?

---

### 3. Pausenzeiten

**Frage 3.1:** Werden Pausenzeiten von der St-Anteil abgezogen?
- Wenn ja, wie werden Pausenzeiten berücksichtigt?
- Werden konfigurierte Pausenzeiten aus `employees_breaktimes` verwendet?
- Oder gibt es eine feste Pausenzeit pro Tag?

**Frage 3.2:** Könnte die Abweichung von 1:01 Std (DEGO) durch Pausenzeiten erklärt werden?
- Unsere Zeit-Spanne: 8:05 Std
- Locosoft: 9:06 Std
- Differenz: 1:01 Std ≈ 61 Min
- Ist das eine konfigurierte Pausenzeit?

---

### 4. Filterkriterien

**Frage 4.1:** Welche Filterkriterien werden für die St-Anteil Berechnung verwendet?
- Werden nur bestimmte Aufträge berücksichtigt? (z.B. `order_number > 31`, nur abgerechnete, etc.)
- Werden nur bestimmte Auftragsarten berücksichtigt? (intern vs. extern, Garantie, etc.)
- Gibt es Filter auf `order_status` oder andere Felder?

**Frage 4.2:** Werden Stempelungen mit `end_time IS NULL` ausgeschlossen?
- Oder gibt es eine andere Behandlung für offene Stempelungen?

**Frage 4.3:** Gibt es unterschiedliche Filter für DEGO vs. DEGH?
- Könnte das die unterschiedlichen Berechnungsmethoden erklären?

---

### 5. Zeit-Spanne vs. Summe

**Frage 5.1:** Wird für DEGO die Zeit-Spanne (erste bis letzte Stempelung) verwendet?
- Unsere Zeit-Spanne: 8:05 Std (08:46-16:52)
- Locosoft: 9:06 Std
- Abweichung: 1:01 Std
- Wird die Zeit-Spanne verwendet, oder gibt es eine andere Methode?

**Frage 5.2:** Wird für DEGH die Summe der auftrags-basierten Stempelzeiten verwendet?
- Unsere Summe: 4:43 Std
- Locosoft: 3:59 Std
- Abweichung: 0:44 Std
- Wird die Summe verwendet, oder gibt es eine andere Methode?

**Frage 5.3:** Wie werden Lücken zwischen Stempelungen behandelt?
- Werden Lücken zwischen Stempelungen von der Zeit-Spanne abgezogen?
- Oder wird die komplette Zeit-Spanne verwendet?

---

### 6. Technische Details

**Frage 6.1:** Können Sie eine SQL-Query oder Pseudocode bereitstellen, der die St-Anteil Berechnung beschreibt?
- Besonders für die Aufteilung nach Auftragsbetrieb
- Mit allen verwendeten Filterkriterien

**Frage 6.2:** Gibt es eine Dokumentation zur St-Anteil Berechnung?
- Besonders zur Aufteilung nach Auftragsbetrieb
- Mit Beispielen und Erklärungen

**Frage 6.3:** Können Sie konkrete Beispiele mit Datenbankwerten und erwarteten Ergebnissen bereitstellen?
- Für MA 5007 am 07.01.2026
- Mit Erklärung, warum Locosoft 9:06 Std (DEGO) und 3:59 Std (DEGH) berechnet

---

## Was wir benötigen

1. **Exakte Formel** für die St-Anteil Berechnung nach Auftragsbetrieb
2. **SQL-Query** oder **Pseudocode**, der die Berechnung beschreibt
3. **Konkrete Beispiele** mit Datenbankwerten und erwarteten Ergebnissen
4. **Dokumentation** zu allen verwendeten Filterkriterien
5. **Erklärung** der unterschiedlichen Berechnungsmethoden für DEGO vs. DEGH (falls vorhanden)

---

## Unsere aktuellen Hypothesen (die nicht funktionieren)

### Hypothese 1: Auftrags-basierte Deduplizierung
```sql
DISTINCT ON (employee_number, order_number, start_time, end_time)
```
- **Ergebnis:** DEGO 3:21 Std (zu niedrig), DEGH 4:43 Std (nah)
- **Problem:** DEGO passt nicht

### Hypothese 2: Zeit-Spanne (erste bis letzte Stempelung)
```sql
MIN(start_time) bis MAX(end_time) pro Tag
```
- **Ergebnis:** DEGO 8:05 Std (nah), DEGH 5:17 Std (zu hoch)
- **Problem:** DEGH passt nicht

### Hypothese 3: Position-basierte Berechnung
```sql
DISTINCT ON (employee_number, order_number, order_position, 
             order_position_line, start_time, end_time)
```
- **Ergebnis:** DEGO 13:31 Std (zu hoch), DEGH 24:31 Std (zu hoch)
- **Problem:** Beide zu hoch

---

## Datenbank-Struktur (Referenz)

**Tabelle `times`:**
- `employee_number`: Mitarbeiternummer
- `type`: 1 = Anwesenheit, 2 = Stempelzeit
- `order_number`: Auftragsnummer
- `order_position`: Position
- `order_position_line`: Positionszeile
- `start_time`: Startzeit
- `end_time`: Endzeit

**Tabelle `orders`:**
- `number`: Auftragsnummer
- `subsidiary`: Betrieb (1 = DEGO, 2 = DEGH, 3 = LAN)

**Tabelle `employees_breaktimes`:**
- `employee_number`: Mitarbeiternummer
- `break_start`: Pausenstart
- `break_end`: Pausenende

---

## Erwartete Antwort

Wir benötigen eine **exakte Beschreibung** der St-Anteil Berechnung, damit wir:
1. Die Berechnung in DRIVE korrekt nachbilden können
2. Die Abweichungen zu Locosoft minimieren können (< 1% Abweichung)
3. Konsistente Ergebnisse für alle Mechaniker und Zeiträume erhalten

**Priorität:** Hoch, da die St-Anteil Berechnung die Grundlage für Leistungsgrad und andere KPIs ist.

---

## Kontakt

**System:** Greiner Portal DRIVE  
**Server:** 10.80.80.20  
**Datenbank:** Locosoft (read-only Zugriff)  
**Dokumentation:** `docs/ANALYSE_MA_5007_07_01_2026.md`

---

**Vielen Dank für Ihre Unterstützung!**
