# Auth & LDAP — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-03-02

### Rechteverwaltung Entschlackung (2026-03-02)
- **Vorschlag B:** Nur Sicht „Nach Rolle“ bearbeitbar; „Nach Feature“ und „Matrix“ nur Übersicht (read-only). Speichern nur aus „Nach Rolle“. Feature-Karten ohne Stift-Button.
- **Vorschlag D:** Haupt-Tabs auf 3 reduziert: **User & Rollen** (User-Liste + Rollen & Module/Feature-Zugriff in einem Tab), **Mitarbeiter & Urlaub** (Pills: Mitarbeiter-Konfig, Urlaubsverwaltung, Mitarbeiterverwaltung), **Einstellungen** (Pills: Navigation, Title-Mapping, E-Mail Reports, Architektur).
- **Vorschlag C:** Filter-Verhalten für Listen (Auftragseingang, Auslieferungen, OPOS, Leistungsübersicht Werkstatt) inline: kleines Dropdown neben dem Feature-Haken in der Rollen-Ansicht; separate Karte „Filter-Verhalten für Listen“ entfernt.

### Fix: Rollen/Features-Speichern (2026-02-27)
- **Problem:** Änderungen an Rollen & Feature-Zugriff wurden nicht gespeichert.
- **Ursache:** In `saveRoleFeatures()` wurden immer die Checkboxen aus `roleFeaturesGrouped` (Tab „Rollen-Features“) ausgelesen, auch wenn der Nutzer im Tab „Feature-Zugriff“ (Dropdown + `roleFeaturesList`) geändert hatte → falsche/leere Feature-Liste ging an die API.
- **Lösung:** Checkbox-Container an den Rollen-Kontext gekoppelt: Wenn Rolle aus Button (`selectedRoleForFeatures`) → `roleFeaturesGrouped`, sonst aus Dropdown → `roleFeaturesList`.

## Beschreibung

Auth umfasst LDAP/AD-Integration, RBAC, Session-Management, Rollen-Config, Dashboard-Personalisierung, Rechte-Verwaltung und Portal-Name-Survey. **Theme & Design:** Vorschläge und Mockups für ein zentrales DRIVE-Theme (Farben, Schriften, Startseite) liegen in diesem Workstream-Ordner (MOCKUP_THEME_*.html, EINSCHAETZUNG_DRIVE_DESIGN_ANPASSUNG.md, README_THEME_MOCKUPS.md). Die Umsetzung von Theme und Badges pro Rolle wird hier mitgeführt. Siehe WORKSTREAM_THEME_DESIGN_EMPFEHLUNG.md für die Frage „eigener Workstream Design?“.

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
- ✅ **Rechteverwaltung – Bug OPOS/Features bleiben nicht gespeichert (2026-02-27):** Ursache war ein pro-Worker-Cache in `get_feature_access_from_db()`: Nach Speichern sah ein anderer Gunicorn-Worker weiter alte Daten. Cache deaktiviert (`CACHE_TTL = timedelta(0)` in `config/roles_config.py`). Verbesserungsvorschlag zu Redundanz (Rollen-Features / Matrix / Nach Feature / Navigation) und Administrierbarkeit: `VORSCHLAG_RECHTEVERWALTUNG_VEREINFACHUNG.md`.
- ✅ **Rechteverwaltung – UI vereinfacht (2026-02-27):** Ein Tab **Feature-Zugriff** ersetzt die drei Tabs „Rollen-Features“, „Matrix“, „Nach Feature“. Innerhalb des Tabs: Pills „Nach Rolle“ (Rollen-Buttons + Checkboxen + Speichern), „Nach Feature“ (Dropdown Rolle + Liste + Feature-Karten), „Matrix (Übersicht)“ (read-only). Ein Speicher-Pfad, eine Quelle der Wahrheit.
- ✅ **Verkauf-Menü: alle Punkte mit eigenem Feature (2026-02-27):** Migration `migration_verkauf_features_complete.sql`: Features verkaeufer_zielplanung, planung, provision, provision_vkl, leasys, gw_standzeit angelegt; alle Verkauf-Nav-Items auf passendes requires_feature umgestellt. Rolle „Verkauf“ hat nur auftragseingang, auslieferungen, provision, whatsapp_verkauf – sieht z. B. nicht: eAutoseller, GW-Standzeit, Planung/Budget/Lieferforecast, Verkäufer-Zielplanung, Leasys, Provisions-Dashboard (VKL). Routen mit Feature-Check geschützt (verkauf_routes, provision_routes, app.py leasys-programmfinder).
- ✅ **Navigation nur berechtigte Punkte (2026-02-27):** Unter „Controlling“ waren Übersichten, Planung, Analysen für alle sichtbar (kein requires_feature). Jetzt: requires_feature = ‚controlling‘ für diese drei Einträge (Migration); leere Dropdowns werden rekursiv ausgeblendet (navigation_utils). Verkäufer (nur OPOS) sehen unter Controlling nur noch z. B. „Offene Posten (OPOS)“.
- ✅ **Parent-Kind für alle Menüs (2026-03-02):** Einträge ohne eigenes requires_feature erben vom Eltern-Menü (navigation_utils). Admin (6) und Team Greiner (44, 45) per Migration nachgezogen. Doku: `NAVIGATION_PARENT_CHILD_RECHTE.md`.
- ✅ **Startseite nur nach Rolle (2026-02-27):** User mit Rolle „Verkauf“ konnten zuvor „Bankenspiegel“ als Startseite zugewiesen bekommen. Ursache: Dropdown nutzte `user.roles` (DB-Rollen) statt `effective_portal_role`, und `available_dashboards` hatte kein `requires_feature`. Fix: Migration `migration_dashboards_requires_feature.sql` setzt `requires_feature` pro Dashboard; Frontend filtert mit `effective_portal_role`; Backend prüft beim Speichern, ob die Rolle des Users Zugriff auf die gewählte Startseite hat (sonst 400).
- ✅ **Filter-Verhalten für Listen (2026-02-27):** Pro Feature (Auftragseingang, Auslieferungen, OPOS) und Rolle konfigurierbar: **Nur eigene** (Filter nicht auflösbar), **Eigene, Filter auflösbar**, **Alle, kann filtern**. Tabelle `feature_filter_mode`, API `api/admin_api.py` + `api/feature_filter_mode.py` (get_filter_mode), Rechteverwaltung: im Tab Feature-Zugriff → Nach Rolle → Karte „Filter-Verhalten für Listen“ mit Dropdowns. Auftragseingang, Auslieferungen, OPOS lesen den Modus und setzen UI/API entsprechend.
- ✅ **Leistungsübersicht Werkstatt – Filter „nur eigene“ (2026-03-02):** Feature `werkstatt_leistungsuebersicht` in Filter-Verhalten und Navi; API `/api/werkstatt/leistung` filtert bei own_only auf angemeldeten Mechaniker (Locosoft-ID aus ldap_employee_mapping). Rechteverwaltung: „Leistungsübersicht Werkstatt“ in Filter-Tabelle; Rolle werkstatt default own_only. Migration `migration_feature_filter_werkstatt_leistung.sql`, `fix_navigation_leistungsuebersicht_feature.sql`.
- ✅ **Locosoft-ID in Rechteverwaltung sichtbar (2026-03-02):** Modal „Mitarbeiter bearbeiten“ zeigt **Locosoft-ID (für Filter „nur eigene“)** aus `ldap_employee_mapping`; API `GET /api/employee-management/employee/<id>` liefert `mapping_locosoft_id`. Doku: `LOCOSOFT_ID_ANZEIGE_UND_FILTER.md`.
- ✅ **User fehlt / Login schlägt fehl (2026-03-02):** User-Liste kommt aus Tabelle `users` (Eintrag nur bei erstem erfolgreichen LDAP-Login). Prüfanleitung für fehlende User (z. B. Christian Raith): `PRUEFUNG_USER_FEHLT_LOGIN.md`. Typo in ldap_employee_mapping (chrsitian→christian) für Christian Raith korrigiert.
- ✅ **Dashboard nur für berechtigte Rollen (2026-03-02):** Top-Level „Dashboard“ mit `requires_feature = 'dashboard'`; Rolle werkstatt standardmäßig ohne Feature → Dashboard in Navi ausgeblendet. Migration `fix_navigation_dashboard_requires_feature.sql`.

## Auf Eis gelegt (vorerst)

- **Modul zur LDAP-Bearbeitung:** Bearbeitung von LDAP/AD-Daten im Portal (z. B. Abteilung, Standort, Vorgesetzter im Portal ändern, ggf. Zurückschreiben ins AD) ist **vorerst nicht geplant**. AD ↔ Drive (Sync, Mapping, Login, Passwort-Self-Service) läuft; weitere LDAP-Edit-Funktionen bleiben zurückgestellt.

- ✅ **Rechte & Navi am User (Option A, 2026-03-02):** Button „Rechte & Navi“ (Auge) pro User in der User & Rollen-Tabelle; Modal zeigt wirksame Rolle, Feature-Liste und sichtbare Navigation (read-only). API: `GET /api/admin/user/<id>/effective-rights`. `navigation_utils.get_navigation_for_role(role, allowed_features)` für Navi-Vorschau. Doku: `NACHSTER_SCHRITT_RECHTE_USER_SICHT.md`, `EINSCHAETZUNG_BEARBEITUNG_AM_USER.md`.

## Nächster Schritt (optional)

- Weitere UX-Anpassungen an der Rechteverwaltung oder andere Workstreams.

## Offene Entscheidungen

- (Keine aktuell)

## Wichtige Hinweise (TAG 2026-02-19, Session-Ende)

- **Wirksame Portal-Rolle** (Navi + Features): 1) **admin** in `user_roles` → voller Zugriff; 2) **users.portal_role_override** (in Rechteverwaltung gesetzt) → diese Rolle; 3) sonst **mitarbeiter** (Default, kein LDAP-Fallback mehr).
- Diagnose pro User: `python scripts/checks/check_user_portal_role.py "Nachname"`.
- Ausführlich: `docs/workstreams/auth-ldap/PORTAL_ROLLE_WARUM_GRANULARER.md`.

## Abhängigkeiten

- Infrastruktur (App-Start), HR (Mitarbeiter-Mapping)
