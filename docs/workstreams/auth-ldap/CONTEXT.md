# Auth & LDAP — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-24

## Beschreibung

Auth umfasst LDAP/AD-Integration, RBAC, Session-Management, Rollen-Config, Dashboard-Personalisierung, Rechte-Verwaltung und Portal-Name-Survey.

## Module & Dateien

### Auth
- `auth/auth_manager.py` — Session, Berechtigungen, `change_password()`
- `auth/ldap_connector.py` — LDAP/AD-Anbindung, `change_user_password()` (AD unicodePwd)

### Config
- `config/roles_config.py` — Rollen-Definition

### Decorators
- `decorators/auth_decorators.py` — Zugriffskontrollen

### Templates
- `templates/admin/rechte_verwaltung*.html`
- `templates/admin/user_dashboard_config*.html`
- `templates/profil_passwort.html` — Self-Service Passwort ändern

### Rollen
- `admin`, `finance`, `sales`, `hr`, `manager`, `employee`

## DB-Tabellen (PostgreSQL drive_portal)

- `users`, `ldap_employee_mapping` (und ggf. rollenbezogene Tabellen)

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ **AD-Passwort ändern (Self-Service):** Nutzer können unter „Passwort ändern“ (User-Dropdown) ihr Active-Directory-Passwort ändern. Das neue Passwort gilt ab der nächsten Anmeldung für Windows und Drive. LDAPS (Port 636), ldap3 `ad_modify_password` (DELETE+ADD unicodePwd). Route: `/profil/passwort`, Template: `profil_passwort.html`. Erfolgs-/Fehler-Feedback direkt auf der Seite („Vom AD bestätigt“ / „vom AD-Server nicht akzeptiert“). Fehlermeldungen nutzerfreundlich übersetzt (Keys in ldap_connector, `PASSWORT_FEHLER_UEBERSETZUNG` + `_passwort_fehler_fuer_anwender()` in app.py) – keine technischen/englischen Texte im UI.
- ✅ LDAP-Login, Rollen, RBAC, Rechte-Verwaltung im Einsatz
- ✅ **Option B (Rechte nur aus Portal):** Zugriff wird ausschließlich in der Rechteverwaltung festgelegt. LDAP liefert nur Identität (wer darf sich anmelden). Pro User eine **Rolle** zuweisen (Dropdown „Rolle zuweisen“). „— Bitte zuweisen —“ = noch keine Rolle → Zugriff wie „mitarbeiter“ (minimal). OU/Title (AD) nur zur Info.
- ✅ **Rollen & Feature-Zugriff:** Im Tab „Feature-Zugriff“: Block „Rollen & Feature-Zugriff“ – Rolle wählen, Features an/abwählen, speichern. Zusätzlich „Nach Feature“ (bestehende Karten).
- ✅ **Organigramm:** Abteilungen, Hierarchie (Tree), **Vertretungsregeln** (CRUD, PostgreSQL `substitution_rules`), **Genehmigungsregeln** (Modal „Neue Regel“ mit Abteilungsname wie „Geschäftsführung“, Speichern/Löschen). Genehmiger-Dropdown konsistent mit bestehenden Regeln (Abteilungsnamen, nicht Kurzcodes wie GL).
- ✅ **Vertretungsregel → Urlaubsplaner:** Vertreter darf im Zeitraum, in dem die vertretene Person abwesend ist, keinen Urlaub buchen (Prüfung in `vacation_api.book_vacation`, `book_batch`, `vacation_admin_api.mass_booking`). Testanleitung Vanessa ergänzt.
- ✅ **Rechteverwaltung – Modal „Mitarbeiter bearbeiten“:** Tab „Mitarbeiter-Konfig“: Stift öffnet Modal mit Stammdaten, Vertretungen und Urlaub (Anspruch/Jahr, Einstellungen). Link „Alle Vertretungsregeln im Organigramm“ → `/admin/organigramm#substitutes`; Organigramm wertet Hash aus und öffnet Tab **Vertretungen** (nicht Abteilungen). Template: `rechte_verwaltung.html`, Organigramm: `organigramm.html` (switchToTab, Hash).
- 🔧 Dashboard-Personalisierung je nach Projektstand

## Offene Entscheidungen

- (Keine aktuell)

## Wichtige Hinweise (TAG 2026-02-19, Session-Ende)

- **Wirksame Portal-Rolle** (Navi + Features): 1) **admin** in `user_roles` → voller Zugriff; 2) **users.portal_role_override** (in Rechteverwaltung gesetzt) → diese Rolle; 3) sonst **mitarbeiter** (Default, kein LDAP-Fallback mehr).
- Diagnose pro User: `python scripts/checks/check_user_portal_role.py "Nachname"`.
- Ausführlich: `docs/workstreams/auth-ldap/PORTAL_ROLLE_WARUM_GRANULARER.md`.

## Abhängigkeiten

- Infrastruktur (App-Start), HR (Mitarbeiter-Mapping)
