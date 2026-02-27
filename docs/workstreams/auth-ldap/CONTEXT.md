# Auth & LDAP — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-27

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
- ✅ **AD Service-Account statt Administrator/Florian (2026-02-27):** Ein technischer Account (svc_portal) wird für LDAP und alle CIFS-Mounts genutzt. Doku: `AD_DRIVE_ACCOUNT_STATT_ADMINISTRATOR_VORSCHLAG.md`, `AD_SERVICE_ACCOUNT_RECHTE_UND_UMSTELLUNG.md`, `DRIVE_FEATURES_AD_ACCOUNT_UEBERSICHT.md`. fstab für CIFS korrigiert (Leerzeichen als `\040`), Buchhaltung-Mount in fstab ergänzt (`scripts/add_fstab_buchhaltung.sh`). Mounts und LDAP mit venv getestet – alles OK.
- ✅ **vacation_approver_service:** PostgreSQL-Fix für `get_team_for_approver` (Admin-Fall: SELECT DISTINCT + ORDER BY – Order-By-Ausdruck in Select-Liste).
- ✅ **AD vs. Drive / „kein AD“ (2026-02-27):** sync_ad_departments legt beim Lauf automatisch `ldap_employee_mapping` an, wenn ein MA per E-Mail-Prefix im AD gefunden wird (bisher nur Abteilung aktualisiert) – „kein AD“ verschwindet dann. ldap3 in requirements.txt + .venv; Aufruf Sync: `.venv/bin/python`. Doku: `AD_SYNC_KEIN_AD.md` (Bedeutung „kein AD“, Option 1a Abteilungs-Sync).

## Auf Eis gelegt (vorerst)

- **Modul zur LDAP-Bearbeitung:** Bearbeitung von LDAP/AD-Daten im Portal (z. B. Abteilung, Standort, Vorgesetzter im Portal ändern, ggf. Zurückschreiben ins AD) ist **vorerst nicht geplant**. AD ↔ Drive (Sync, Mapping, Login, Passwort-Self-Service) läuft; weitere LDAP-Edit-Funktionen bleiben zurückgestellt.

## Offene Entscheidungen

- (Keine aktuell)

## Wichtige Hinweise (TAG 2026-02-19, Session-Ende)

- **Wirksame Portal-Rolle** (Navi + Features): 1) **admin** in `user_roles` → voller Zugriff; 2) **users.portal_role_override** (in Rechteverwaltung gesetzt) → diese Rolle; 3) sonst **mitarbeiter** (Default, kein LDAP-Fallback mehr).
- Diagnose pro User: `python scripts/checks/check_user_portal_role.py "Nachname"`.
- Ausführlich: `docs/workstreams/auth-ldap/PORTAL_ROLLE_WARUM_GRANULARER.md`.

## Abhängigkeiten

- Infrastruktur (App-Start), HR (Mitarbeiter-Mapping)
