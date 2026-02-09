# Mitarbeiterverwaltung – Vorgehensweise zum Befüllen der Funktionen

**Stand:** TAG 213  
**Ziel:** Template-Funktionen mit Leben füllen; bis auf Sync ist aktuell nur Dummy/Anzeige.

---

## Ist-Zustand (kurz)

| Bereich | Status | Anmerkung |
|--------|--------|-----------|
| **Sidebar** | ✅ OK | Mitarbeiterliste, Gruppierung, Auswahl, Suche |
| **Deckblatt** | ✅ OK | Anzeige + Sync; Speichern über `saveEmployee()` (PUT) |
| **Adressdaten** | ✅ OK | Felder in `collectFormData()`; PUT übernimmt sie |
| **Vertrag** | ⚠️ Teilweise | Felder angezeigt; `collectFormData()` fehlen `vertrag_company`, `vertrag_department`, `vertrag_entry_date` (nur Deckblatt-Varianten werden gespeichert) |
| **Arbeitszeitmodell** | ❌ Dummy | Tabelle wird aus `employee.working_time_models` gerendert; Add/Edit/Delete nur `alert('…')` |
| **Ausnahmen** | ❌ Dummy | Tabelle aus `employee.exceptions`; Add/Delete nur Placeholder |
| **Zeiten ohne Urlaub** | ❌ Dummy | Tabelle aus `employee.periods_without_vacation`; Add/Delete nur Placeholder |
| **Moduldaten → Urlaubsplaner** | ❌ Nicht gespeichert | Formular ist da, aber kein Aufruf von PUT `/vacation-settings`; keine Sammlung in `collectFormData()` |
| **Sync** | ✅ OK | Vorschau, LDAP, Locosoft, Vollständig |

**Backend:** Die APIs für Arbeitszeitmodelle, Ausnahmen, Zeiten ohne Urlaub und Urlaubseinstellungen sind vorhanden und nutzbar (CRUD bzw. GET/PUT).

---

## Vorgehensweise (Phasen)

### Phase 1 – Basis konsolidieren (schnell)

- **Vertrag & Speichern**
  - In `collectFormData()` die Vertrag-Felder ergänzen, die noch fehlen:
    - `vertrag_company` → `data.company` (oder klar machen: nur eine Quelle „Firma“, z. B. Deckblatt)
    - `vertrag_department` → `data.department_name`
    - `vertrag_entry_date` → `data.entry_date`
  - Sicherstellen, dass PUT `/employee/<id>` alle genutzten Felder aus dem Vertrag-Tab akzeptiert (ist bereits der Fall für `company`, `department_name`, `entry_date`).
- **Optional:** In `employee_management_api` prüfen, ob `row_to_dict(row)` überall mit `cursor` aufgerufen wird (wie in `employee_sync_service`), falls irgendwo KeyError bei Spaltennamen auftritt.

**Ergebnis:** Alles, was in Deckblatt/Adresse/Vertrag bearbeitet wird, landet konsistent in der DB.

---

### Phase 2 – Moduldaten Urlaubsplaner (hoher Nutzen)

- **Speichern der Urlaubseinstellungen**
  - Im Tab „Moduldaten“ → „Urlaubsplaner“:
    - Beim Klick auf einen Button „Urlaubseinstellungen speichern“ (oder beim allgemeinen „Speichern“, wenn dieser Tab aktiv ist):
      - Werte aus den Feldern lesen:  
        `settings_show_in_planner`, `settings_show_birthday`, `settings_vacation_expires`,  
        `settings_max_carry_over`, `settings_weekend_limit`, `settings_max_vacation_length`,  
        `settings_calculation_method`, `settings_entry_from`, `settings_entry_until`
      - Request: `PUT /api/employee-management/employee/<id>/vacation-settings` mit JSON-Body (wie API erwartet).
  - Nach erfolgreichem Speichern: entweder Meldung „Urlaubseinstellungen gespeichert“ und optional `selectEmployee(currentEmployeeId)` erneut aufrufen, damit die Anzeige aktuell ist.
- **Urlaubsanspruch „27,0 Tage“:**  
  Erstmal als Anzeige/Dummy lassen; spätere Anbindung an `vacation_entitlements` oder Berechnung kann in einem eigenen Schritt kommen.

**Ergebnis:** Urlaubsplaner-Einstellungen pro Mitarbeiter sind editierbar und werden persistiert.

---

### Phase 3 – Arbeitszeitmodelle

- **Tabelle:** Bleibt wie jetzt (Daten aus `employee.working_time_models`).
- **Hinzufügen**
  - `addWorkingTimeModel()`:
    - Modal (oder Inline-Bereich) mit Feldern: Startdatum, Enddatum (optional), Stunden/Woche, Arbeitstage/Woche, Beschreibung (optional), ggf. Std.-Lohn/Bruttolohn.
    - Submit → `POST /api/employee-management/employee/<id>/working-time-models` mit JSON.
    - Bei Erfolg: Modal schließen, `selectEmployee(currentEmployeeId)` oder nur den Bereich „Arbeitszeitmodell“ neu rendern (Daten neu von GET Detail holen).
- **Bearbeiten**
  - `editWorkingTimeModel(id)`:
    - Gleiche Felder wie beim Hinzufügen, vorbelegt mit dem bestehenden Datensatz.
    - Submit → `PUT /api/employee-management/employee/<id>/working-time-models/<model_id>`.
    - Bei Erfolg: Anzeige aktualisieren wie beim Hinzufügen.
- **Löschen**
  - `deleteWorkingTimeModel(id)`: Bestätigungsdialog, dann `DELETE .../working-time-models/<model_id>`, danach Anzeige aktualisieren.

**Ergebnis:** Arbeitszeitmodelle (Teilzeit/Vollzeit) vollständig pflegbar.

---

### Phase 4 – Ausnahmen (Arbeitszeitmodelle)

- **Tabelle:** Bleibt (Daten aus `employee.exceptions`).
- **Hinzufügen**
  - `addException()`:
    - Modal: Von-Datum, Bis-Datum, Typ (z. B. Sonderurlaub, Elternzeit, Sabbatical – feste Liste oder Freitext), Beschreibung, Checkbox „Beeinflusst Urlaubsanspruch“.
    - Submit → `POST .../employee/<id>/exceptions`.
- **Löschen**
  - `deleteException(id)`: Bestätigung, dann `DELETE .../exceptions/<id>`, Anzeige aktualisieren.

**Ergebnis:** Ausnahmen der Arbeitszeitmodelle (Sonderurlaub etc.) vollständig pflegbar.

---

### Phase 5 – Zeiten ohne Urlaubsanspruch

- **Tabelle:** Bleibt (Daten aus `employee.periods_without_vacation`).
- **Hinzufügen**
  - `addPeriodWithoutVacation()`:
    - Modal: Von-Datum, Bis-Datum, Typ, Beschreibung.
    - Submit → `POST .../employee/<id>/periods-without-vacation`.
- **Löschen**
  - `deletePeriodWithoutVacation(id)`: Bestätigung, `DELETE .../periods-without-vacation/<id>`, Anzeige aktualisieren.

**Ergebnis:** Zeiten ohne Urlaubsanspruch vollständig pflegbar.

---

## Reihenfolge und Aufwand (grobe Schätzung)

1. **Phase 1** – ca. 0,5 h (nur `collectFormData` + ggf. PUT/API-Check).
2. **Phase 2** – ca. 1 h (Button, JS zum Sammeln der Felder, fetch PUT, Erfolgsbehandlung).
3. **Phase 3** – ca. 2–2,5 h (2 Modals: Anlegen + Bearbeiten, Delete, Anbindung an API).
4. **Phase 4** – ca. 1–1,5 h (1 Modal Anlegen, Delete).
5. **Phase 5** – ca. 1 h (analog Phase 4).

**Gesamt grob:** ~6–7 h für alle Phasen.

---

## Technische Stichpunkte

- **API-Basis:** `API_BASE = '/api/employee-management'` (bereits im Template).
- **Arbeitszeitmodelle:**  
  POST/PUT erwarten u. a. `start_date`, `end_date`, `hours_per_week`, `working_days_per_week`, `description` (optional `weekly_hours`, `hourly_wage`, `gross_wage`).
- **Ausnahmen:**  
  POST erwartet `from_date`, `to_date`, `exception_type`, `description`, `affects_vacation_entitlement`.
- **Zeiten ohne Urlaub:**  
  POST erwartet `from_date`, `to_date`, `period_type`, `description`.
- **Urlaubseinstellungen:**  
  PUT erwartet die in `employee_vacation_settings` definierten Felder (z. B. `show_in_planner`, `show_birthday`, `vacation_expires`, `max_carry_over`, `weekend_limit`, `max_vacation_length`, `calculation_method`, `entry_from`, `entry_until`); Datum-Felder als ISO-String oder `null`.

---

## Optional später

- **„Neuer Mitarbeiter“:** Anlegen eines neuen Datensatzes in `employees` (+ ggf. `ldap_employee_mapping`) und Weiterleitung in die Bearbeitung.
- **Urlaubsanspruch:** Anzeige/Berechnung aus `vacation_entitlements` oder Locosoft anbinden („27,0 Tage“ ersetzen).
- **Terminkonten** (`employee_appointment_accounts`): Falls gewünscht, eigene Tabelle/CRUD wie bei Arbeitszeitmodellen.

Wenn du möchtest, können wir mit **Phase 1 + 2** starten (Basis + Urlaubseinstellungen), danach Phase 3–5 nacheinander umsetzen.
