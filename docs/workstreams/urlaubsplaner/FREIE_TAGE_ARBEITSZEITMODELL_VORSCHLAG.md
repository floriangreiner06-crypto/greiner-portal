# Freie Tage im Arbeitszeitmodell (Feedback 3.2)

**Stand:** 2026-02-13  
**Quelle:** Feedback 3.2 (Vanessa/Personalplaner), Referenz: urlaubsplaner.pdf

## Anforderung

- **Freie Tage** sollen im **Arbeitszeitmodell** eingetragen werden können (z. B. welche Wochentage für die Person frei sind).
- Diese Tage sollen im **Urlaubsplaner ausgegraut** werden (nicht buchbar / als freie Tage sichtbar).
- **Darstellung:** Freie Tage = rote Kreise, Regelarbeitstage = grüne Tage (laut Referenz-PDF).
- **Nur bei Teilzeitkräften** anpassbar (Vollzeit = alle Werktage Arbeit).

## Aktueller Stand

- **Globale freie Tage** (z. B. Betriebsferien) gibt es bereits: Tabelle `free_days`, API `/blocks-and-free-days`, im Planer als `free-day` (grau, 🚫) dargestellt.
- **Arbeitszeitmodell** (`employee_working_time_models`): enthält u. a. `hours_per_week`, `working_days_per_week`, aber **keine** Information, *welche* Wochentage frei sind.

## Vorschlag Umsetzung

### 1. Datenmodell

- In **employee_working_time_models** eine optionale Spalte ergänzen, z. B.:
  - **free_weekdays** `SMALLINT[]` (PostgreSQL) – Werte 0–6 (Sonntag = 0, Montag = 1, …, Samstag = 6), z. B. `{0, 6}` = Wochenende frei, `{3, 4}` = Mi/Do frei.
- Oder **working_weekdays** `SMALLINT[]` – nur die Arbeitstage (z. B. `{1,2,3,4,5}` = Mo–Fr); freie Tage = Komplement.  
  → Empfehlung: **free_weekdays**, da explizit „Freie Tage“.

### 2. API

- **Employee-Management:** Beim Erstellen/Aktualisieren eines Arbeitszeitmodells `free_weekdays` mitgeben (nur bei Teilzeit relevant; Frontend kann bei Vollzeit leer lassen).
- **Urlaubsplaner:** Beim Laden der Mitarbeiter (z. B. `/balance` oder separater Endpoint) pro Mitarbeiter das **aktuelle** Arbeitszeitmodell für das gewählte Jahr auflösen und **free_weekdays** mitliefern (aus dem gültigen Modell zum Stichtag).

### 3. Mitarbeiterverwaltung (Frontend)

- Im Modal **Arbeitszeitmodell** (Add/Edit):
  - Nur anzeigen, wenn **Teilzeit** (z. B. `hours_per_week < 38` oder Kennzeichen „Teilzeit“): Bereich **„Freie Tage (Wochentage ohne Arbeit)“** mit z. B. Checkboxen Mo–So (oder Multi-Select).
  - Beim Speichern `free_weekdays` als Array der gewählten Wochentagsnummern senden.

### 4. Urlaubsplaner (Frontend)

- Pro Mitarbeiter **free_weekdays** aus der API haben.
- Beim Rendern einer Zelle (Mitarbeiter **E**, Datum **D**):  
  Wenn `weekday(D)` in `E.free_weekdays`, Zelle mit Klasse **emp-free-day** (oder Wiederverwendung **free-day**) versehen und **ausgrauen** (nicht klickbar).
- Optional: **Rote Kreise** für freie Tage, **grüne** für Regelarbeitstage wie im PDF (CSS-Anpassung).

### 5. Reihenfolge

1. Migration: Spalte `free_weekdays` zu `employee_working_time_models` hinzufügen.  
2. API: Create/Update Arbeitszeitmodell + Lesen in Balance/Employee-Daten.  
3. Mitarbeiterverwaltung: UI für Freie Tage (nur Teilzeit).  
4. Urlaubsplaner: Nutzung von `free_weekdays` beim Zellen-Render + Ausgrauen.

## Abgrenzung

- **free_days (Tabelle):** weiterhin für **unternehmensweite** freie Tage (Betriebsferien etc.) – alle Mitarbeiter.
- **free_weekdays (Arbeitszeitmodell):** **personenbezogen**, nur Teilzeit, wöchentlich wiederkehrend.

## Referenz

- Feedback 3.2: „Freie Tage sollten noch in Arbeitszeitmodell eingetragen werden können (somit ausgrauen im Urlaubsplaner). Freie Tage sind mit roten Kreisen hinterlegt, die grünen Tage sind die Regelarbeitstage. Soll nur bei Teilzeitkräften angepasst werden.“
