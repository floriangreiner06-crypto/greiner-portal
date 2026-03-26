# Wiedereintreter / Re-Hire: Mitarbeiter erscheint nicht im Urlaubsplaner

## Kontext

Wenn ein Mitarbeiter (z. B. nach Kündigung) wieder eingestellt wird und im AD neu angelegt wird, erscheint er oft **nicht** im Urlaubsplaner. Typischer Fall: „Manuel Kerscher“ – letztes Jahr gekündigt, heute im AD angelegt.

## Warum erscheint er nicht?

1. **Urlaubsplaner-Liste** kommt aus der View `v_vacation_balance_{Jahr}`. Diese View zeigt **nur Mitarbeiter mit `employees.aktiv = true`**.
2. **Alter Datensatz:** Beim Austritt wird der Mitarbeiter in der Regel auf `aktiv = false` gesetzt. Der Datensatz bleibt in `employees` erhalten, erscheint aber nicht mehr in der View.
3. **LDAP-Sync** (`sync_ldap_employees_pg.py`) ordnet AD-User nur **bestehenden Mitarbeitern mit `aktiv = true`** zu. Ein Wiedereintreter mit `aktiv = false` wird daher **nicht** automatisch zugeordnet – sein AD-Login bleibt „ohne Match“.

## Lösung (Schritte)

### 1. Mitarbeiter in der DB finden

```sql
-- In PostgreSQL (drive_portal) ausführen:
SELECT id, first_name, last_name, email, aktiv, entry_date, exit_date, department_name, location
FROM employees
WHERE LOWER(last_name) LIKE '%kerscher%' AND LOWER(first_name) LIKE '%manuel%';
```

Falls ein Eintrag mit `aktiv = false` existiert → das ist der alte Datensatz.

### 2. Mitarbeiter reaktivieren

```sql
-- ID aus Schritt 1 einsetzen (z. B. 123):
UPDATE employees
SET aktiv = true,
    exit_date = NULL
WHERE id = <EMPLOYEE_ID>;
```

Optional: `entry_date` auf das neue Einstiegsdatum setzen, falls gewünscht.

### 3. LDAP-Zuordnung herstellen

- **Option A (empfohlen):** In der **Mitarbeiterverwaltung** (Admin → Mitarbeiterverwaltung) den Mitarbeiter suchen, öffnen und **„Sync von LDAP“** bzw. **„Vollständig“** ausführen. Dafür muss in `ldap_employee_mapping` bereits ein Eintrag mit seiner `employee_id` existieren (z. B. manuell angelegt, siehe Option B).
- **Option B:** LDAP-Mapping manuell anlegen, falls der Sync ihn nicht findet (AD-Anmeldename und E-Mail anpassen):

```sql
-- employee_id aus Schritt 1, ldap_username = AD-Anmeldename (sAMAccountName):
INSERT INTO ldap_employee_mapping (ldap_username, ldap_email, employee_id, locosoft_id, verified)
VALUES ('manuel.kerscher', 'manuel.kerscher@auto-greiner.de', <EMPLOYEE_ID>, NULL, 1);
-- Falls bereits ein Eintrag für diese employee_id existiert, stattdessen:
-- UPDATE ldap_employee_mapping SET ldap_username = 'manuel.kerscher', ldap_email = '...', verified = 1 WHERE employee_id = <EMPLOYEE_ID>;
```

Danach in der Mitarbeiterverwaltung **„Sync von LDAP“** ausführen, um Abteilung/Standort/E-Mail aus dem AD zu übernehmen.

### 4. Urlaubsanspruch für das Jahr

Beim nächsten Aufruf des Urlaubsplaners für das aktuelle Jahr wird `ensure_vacation_year_setup_simple(year)` ausgeführt und legt für **alle aktiven Mitarbeiter** fehlende `vacation_entitlements` an. Falls Manuel sofort sichtbar sein soll, einmal Urlaubsplaner-Seite mit dem Jahr aufrufen oder z. B.:

```sql
-- Jahr anpassen (z. B. 2026), EMPLOYEE_ID aus Schritt 1:
INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually, updated_at)
VALUES (<EMPLOYEE_ID>, 2026, 27, 0, 0, CURRENT_TIMESTAMP)
ON CONFLICT (employee_id, year) DO NOTHING;
```

### 5. „Im Urlaubsplaner anzeigen“

In der Tabelle `employee_vacation_settings` gilt **standardmäßig** `show_in_planner = true`. Nur wenn dort explizit `show_in_planner = false` gesetzt ist, wird der Mitarbeiter ausgeblendet. Nach Reaktivierung normalerweise nicht nötig.

---

## Kurz-Checkliste

- [ ] In `employees`: Eintrag für Manuel gefunden?
- [ ] `aktiv = true` und ggf. `exit_date = NULL` gesetzt?
- [ ] In `ldap_employee_mapping`: Eintrag mit seiner `employee_id` und AD-Username?
- [ ] Optional: In Mitarbeiterverwaltung „Sync von LDAP“ / „Vollständig“ ausgeführt?
- [ ] Urlaubsplaner-Seite (Jahr 2026) einmal geladen → `vacation_entitlements` werden automatisch ergänzt.

Nach diesen Schritten erscheint der Wiedereintreter in der Urlaubsplaner-Liste (sofern keine Filter wie Abteilung/Standort ihn ausblenden).
