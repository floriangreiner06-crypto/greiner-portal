# Prüfung: User fehlt in Rechteverwaltung / kann sich nicht einloggen

## Warum fehlt jemand in der User-Liste?

Die Liste **„User & Rollen“** in der Rechteverwaltung kommt aus der Tabelle **`users`**. Ein Eintrag wird **nur beim ersten erfolgreichen LDAP-Login** angelegt. Wer sich noch nie erfolgreich angemeldet hat, erscheint **nicht** in der Liste – unabhängig davon, ob er in `employees` oder `ldap_employee_mapping` existiert.

## Beispiel: Christian Raith (Mechaniker)

- **employees:** Vorhanden (id 53, christian.raith@auto-greiner.de, Werkstatt, aktiv, locosoft_id 5002).
- **ldap_employee_mapping:** Vorhanden (ldap_username = christian.raith, employee_id 53).  
  Hinweis: E-Mail-Tippfehler wurde korrigiert (chrsitian → christian).
- **users:** **Kein Eintrag** → erscheint nicht in der Rechteverwaltung und hat noch nie erfolgreich per LDAP eingeloggt.

Folgerung: Der **LDAP-Login** schlägt für Christian fehl (oder er hat sich noch nie versucht). Bis der Login einmal gelingt, wird kein Eintrag in `users` erzeugt und er bleibt in der User-Liste unsichtbar.

## Mögliche Ursachen (LDAP/AD)

1. **Falscher Benutzername** – Login mit **sAMAccountName** (z. B. `christian.raith` oder `craith`). Mit Christian abklären, womit er sich an Windows anmeldet.
2. **Falsches Passwort** – z. B. abgelaufen oder geändert.
3. **Konto deaktiviert oder gesperrt** – im AD prüfen (Active Directory-Benutzer und -Computer).
4. **Konto außerhalb der LDAP-Suche** – `get_user_details()` sucht unter `LDAP_BASE_DN`; liegt das Konto außerhalb, schlägt der Abruf der Details nach dem Bind fehl.

## LDAP-Login testen (Server)

```bash
cd /opt/greiner-portal
.venv/bin/python -c "
from auth.ldap_connector import LDAPConnector
c = LDAPConnector()
# Nur Bind testen (ohne Passwort im Log):
user = 'christian.raith'  # oder sAMAccountName aus AD
pw = input('Passwort für ' + user + ': ')
ok, err = c.authenticate_user(user, pw)
print('Login:', 'OK' if ok else err)
if ok:
    d = c.get_user_details(user)
    print('Details:', 'OK' if d else 'Nicht gefunden (evtl. außerhalb LDAP_BASE_DN)')
    if d:
        print('  Anzeigename:', d.get('display_name'))
        print('  Mail:', d.get('email'))
"
```

Alternativ den interaktiven Test im LDAP-Connector nutzen:

```bash
cd /opt/greiner-portal
.venv/bin/python auth/ldap_connector.py
```

Dort optional Schritt „Test-Login“ mit Benutzername `christian.raith` (oder dem tatsächlichen sAMAccountName) und Passwort ausführen.

## Nach erfolgreichem Login

Sobald Christian sich **einmal erfolgreich** am Portal anmeldet, wird automatisch ein Eintrag in `users` angelegt. Danach erscheint er in der Rechteverwaltung unter „User & Rollen“ und kann eine Portal-Rolle (z. B. werkstatt) zugewiesen bekommen.

## DB-Checks (Referenz)

```sql
-- Mitarbeiter vorhanden?
SELECT id, first_name, last_name, email, aktiv FROM employees WHERE last_name ILIKE '%Raith%';

-- Mapping AD → Mitarbeiter vorhanden?
SELECT * FROM ldap_employee_mapping WHERE ldap_username = 'christian.raith';

-- User (nur nach erstem erfolgreichen Login)
SELECT id, username, display_name, last_login FROM users WHERE username ILIKE '%raith%';
```
