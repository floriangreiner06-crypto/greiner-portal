# Analyse Resturlaub Jennifer Bielmeier – nur Daten, keine Annahmen

**Datum:** 2026-02  
**Kontext:** Florian Greiner ist eingeloggt → Banner zeigt **seine** Werte (Anspruch 27, Rest 27). In der Mitarbeiterliste steht Jennifer Bielmeier mit **(26)** = ihr angezeigter Rest. User: „Jennifer hat 10 Tage geplant und genehmigt, warum 26 Rest?“ – Analyse mit echten DB-Daten.

---

## 1. Kontext Screenshot (Korrektur)

- **Banner (Anspruch 27, Rest 27):** Bezieht sich auf den **eingeloggten User** = Florian Greiner (employee_id 19).
- **„(26)“ neben „Jennifer Bielmeier“:** Ist der **Resturlaub von Jennifer** (employee_id 4), wie die API/View für sie liefert.

---

## 2. Daten aus der Datenbank (Abfragen ausgeführt)

### 2.1 Jennifer Bielmeier – Anspruch (Mitarbeiterverwaltung / Moduldaten)

| employee_id | year | total_days | carried_over | added_manually | anspruch_berechnet |
|-------------|------|------------|--------------|----------------|--------------------|
| 4           | 2026 | 28         | 0            | 0              | **28**             |

→ Anspruch 28 ist in DRIVE korrekt eingetragen.

### 2.2 Jennifer Bielmeier – Buchungen 2026 (vacation_bookings)

| id   | booking_date | day_part | status   | vacation_type_id | typ_name             |
|------|--------------|----------|----------|-------------------|----------------------|
| 7449 | 2026-01-23   | full     | approved | 6                 | Ausgleichstag        |
| 7731 | 2026-05-21   | full     | approved | 1                 | Urlaubstag (beantragt) |
| 7732 | 2026-05-22   | full     | approved | 1                 | Urlaubstag (beantragt) |

**Summe in DB:**

| status   | vacation_type_id | typ_name      | tage |
|----------|------------------|---------------|------|
| approved | 1                | Urlaubstag    | **2.0** |
| approved | 6                | Ausgleichstag | 1.0  |

→ In DRIVE stehen für Jennifer 2026 **nur 2 genehmigte Urlaubstage (type_id = 1)** und 1 Ausgleichstag (type_id = 6).

### 2.3 View v_vacation_balance_2026 (Definition)

- **verbraucht** = Summe Tage aus `vacation_bookings` mit **status = 'approved'** und **vacation_type_id = 1** (nur Urlaub).
- **geplant** = Summe Tage mit **status = 'pending'** und **vacation_type_id = 1**.
- **resturlaub** = anspruch − verbraucht − geplant.

Auswertung nur type_id = 1 → View ignoriert Ausgleichstag (6) und alle anderen Typen.

### 2.4 View-Ausgabe für Jennifer

| employee_id | name             | anspruch | verbraucht | geplant | resturlaub |
|-------------|------------------|----------|------------|---------|------------|
| 4           | Jennifer Bielmeier | 28     | 2.0        | 0       | **26**     |

→ Rechnung: 28 − 2 − 0 = **26**. Die View ist damit **konsistent mit den aktuellen Daten** in `vacation_entitlements` und `vacation_bookings`.

---

## 3. Schlussfolgerung aus den Daten

- Die **Berechnung** (Anspruch − verbraucht − geplant, nur type_id = 1) ist eindeutig und passt zu den gespeicherten Werten.
- **Warum 26 und nicht weniger?** Weil in `vacation_bookings` für Jennifer 2026 **nur 2 Urlaubstage (type_id = 1)** mit status `approved` vorkommen. Weitere 8 Tage „geplant und genehmigt“ sind in dieser Tabelle **nicht** vorhanden.
- Mögliche Ursachen (ohne Annahme zu treffen):
  - Die 10 Tage wurden **nur in Locosoft** erfasst und nie in DRIVE gebucht/genehmigt.
  - Die 10 Tage wurden in DRIVE unter **anderem Typ** (nicht type_id = 1) oder anderem Jahr/Mitarbeiter gebucht.
  - Die 10 Tage wurden in DRIVE nie angelegt (Erfassungsfehler/Abweichung zwischen Realität und System).

Um zu klären, **wo** die 10 Tage liegen, müsste man prüfen: weitere Buchungen für employee_id 4 (andere Jahre/Typen), Doppeleinträge, oder ob die Erwartung „10 Tage“ aus Locosoft/Excel/Absprache kommt und in DRIVE nachgetragen werden müssten.

---

## 4. Kurzfassung

| Frage | Antwort (nur aus Daten) |
|-------|--------------------------|
| Ist Jennifers Anspruch in DRIVE eingetragen? | Ja, 28 Tage (vacation_entitlements). |
| Wie viele Urlaubstage (type_id = 1) hat die View für sie 2026? | 2 verbraucht, 0 geplant. |
| Warum Rest 26? | 28 − 2 = 26; entspricht der View-Definition. |
| Wo sind die „10 Tage geplant und genehmigt“? | Nicht in `vacation_bookings` für employee_id 4, Jahr 2026, type_id 1. |

Die „ganze Berechnung“ im Sinne der Formel (Rest = Anspruch − verbrauchter Urlaub − geplanter Urlaub) ist damit nicht fehlerhaft; die Abweichung kommt daher, dass **in DRIVE nur 2 Urlaubstage** für Jennifer 2026 gespeichert sind. Nächster Schritt: klären, wo die übrigen Tage geführt werden (Locosoft, anderes System, Nachpflege in DRIVE).
