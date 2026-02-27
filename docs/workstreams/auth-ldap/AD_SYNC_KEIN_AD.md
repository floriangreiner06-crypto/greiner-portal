# „Kein AD“ im Urlaubsplaner – AD-Zuordnung synchronisieren

## Was bedeutet „kein AD“?

**„Kein AD“** = **Portal kennt keine Zuordnung dieses Mitarbeiters zu einem AD-Benutzer** (kein Eintrag in `ldap_employee_mapping` mit `ldap_username`).

- Im Urlaubsplaner: **⚠️ Abteilung (kein AD)** = dieser MA hat kein AD-Mapping.
- Wenn **AD-Änderungen** (z. B. Abteilung) für jemanden trotzdem gesynct werden, liegt das am **AD-Abteilungs-Sync** (`sync_ad_departments.py`): Dieser findet Mitarbeiter auch per **E-Mail-Prefix** (Teil vor @) = sAMAccountName, wenn noch kein Mapping existiert. Er aktualisiert dann die Abteilung – **ohne** bisher das Mapping anzulegen. Das führte dazu, dass „AD-Daten werden gesynct“ und „kein AD“ gleichzeitig auftraten.

**Abgleich (seit Fix):** Beim **AD-Abteilungs-Sync** wird nun automatisch ein Eintrag in `ldap_employee_mapping` angelegt/aktualisiert, sobald ein Mitarbeiter per E-Mail-Prefix im AD gefunden wird. Dann verschwindet „kein AD“ nach dem nächsten Lauf von `sync_ad_departments` (oder nach dem LDAP-Employee-Sync).

## Muss sich der Mitarbeiter einmal anmelden?

**Nein.** Die Anmeldung im Portal **erstellt das Mapping nicht**. Beim Login wird nur geprüft, ob der User im AD existiert; die Zuordnung „AD-User → Mitarbeiter“ kommt aus `ldap_employee_mapping`. Ohne Eintrag dort kann der User sich zwar einloggen, erscheint im Urlaubsplaner aber weiter unter „kein AD“.

## Wie synchronisieren wir?

### Option 1a: AD-Abteilungs-Sync ausführen (legt Mapping bei Treffer per E-Mail-Prefix an)

Wenn für einen MA bereits **Abteilungsdaten aus dem AD** übernommen werden (weil sAMAccountName = E-Mail-Teil vor @), legt dieses Skript beim Lauf automatisch das fehlende Mapping an – „kein AD“ verschwindet danach.

```bash
cd /opt/greiner-portal
.venv/bin/python scripts/sync/sync_ad_departments.py
```

(Alternativ Task „AD Department Sync“ im Task Manager.)

### Option 1b: LDAP-Employee-Sync (PostgreSQL) ausführen

Das Skript liest alle aktiven AD-User, matcht sie mit `employees` (E-Mail, Vor-/Nachname, Fallback: E-Mail-Lokalteil = sAMAccountName) und schreibt `ldap_employee_mapping`.

```bash
cd /opt/greiner-portal
.venv/bin/python scripts/sync/sync_ldap_employees_pg.py
```

- **Voraussetzung:** MA in AD angelegt, in `employees` mit passender E-Mail bzw. sAMAccountName = Teil vor @ der E-Mail.
- Danach erscheinen sie nicht mehr unter „kein AD“.

### Option 2: Manuell in der Datenbank

Falls nur eine Person nachgezogen werden soll (z. B. Vincent Pursch):

1. **employee_id** und **locosoft_id** von Vincent in `employees` ermitteln:
   ```sql
   SELECT id, locosoft_id, first_name, last_name, email FROM employees WHERE aktiv = true AND (last_name ILIKE '%Pursch%' OR first_name ILIKE '%Vincent%');
   ```
2. **AD-Benutzername** (sAMAccountName) von Vincent kennen (z. B. `vpursch` oder `vincent.pursch`).
3. Eintrag anlegen (falls noch keiner existiert) oder bestehenden aktualisieren:
   ```sql
   -- Prüfen ob Eintrag existiert:
   SELECT * FROM ldap_employee_mapping WHERE employee_id = <employee_id>;
   -- Falls nein: Einfügen
   INSERT INTO ldap_employee_mapping (ldap_username, ldap_email, employee_id, locosoft_id, verified)
   VALUES ('vpursch', 'vincent.pursch@auto-greiner.de', <employee_id>, <locosoft_id>, 1);
   -- Falls ja: Aktualisieren
   UPDATE ldap_employee_mapping SET ldap_username = 'vpursch', ldap_email = 'vincent.pursch@auto-greiner.de' WHERE employee_id = <employee_id>;
   ```

Nach dem Sync bzw. manuellen Eintrag: **Kein Portal-Neustart nötig** – beim nächsten Laden des Urlaubsplaners erscheint der MA mit normaler Abteilung (ohne „kein AD“).

## Siehe auch

- `scripts/sync/sync_ad_departments.py` – AD-Abteilungen + **Anlegen des Mappings**, wenn MA per E-Mail-Prefix gefunden wird
- `scripts/sync/sync_ldap_employees_pg.py` – LDAP → ldap_employee_mapping (E-Mail/Name/Fallback E-Mail-Lokalteil)
- `scripts/sync/sync_ldap_employees.py` – alter SQLite-Sync (Legacy)
- `api/vacation_api.py` – Abfrage `employees_with_ad` für Anzeige „kein AD“
