# Urlaubsplaner — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-18

## Projektkontext (Stand diese Woche)

- **Cursor neu aufgesetzt**, Arbeitsweise auf **Workstreams** umgestellt.
- Dieses Dokument beschreibt den **tatsächlichen** Entwicklungsstand; ältere Session-Wrap-ups (z. B. Phase‑1-Tag‑1) sind historisch.
- **Letzte relevante Entwicklung:** Neue **Mitarbeiterverwaltung** unter **Admin** (TAG 213), angelehnt an Muster „Digitale Personalakte“, mit Inputs aus Usertests.

## Quellen aus Usertest (nicht im Repo)

Word-Dokumente aus Usertests (Vanessa):

- **Windows/Sync:** `F:\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\urlaubsplaner\` bzw.  
  `\\Srvrdb01\...\Server\docs\workstreams\urlaubsplaner\` enthält u. a.:
  - `Mitarbeiterverwaltung.docx`, `Mitarbeiterverwaltung Test.docx`
  - `Urlaubsplaner.docx` — Urlaubsplaner-Verbesserungen / User-Test
  - **`Urlaubsplaner neu.docx`** — weiterer Usertest (Vanessa); Inhalt ausgewertet in `USERTEST_URLAUBSPLANER_NEU_VANESSA.md`

Im Projekt existieren **daraus abgeleitete** Dokumente:

- **Mitarbeiterverwaltung:** `docs/MITARBEITERVERWALTUNG_ANALYSE_TAG213.md`, `docs/MITARBEITERVERWALTUNG_VORGEHENSWEISE_TAG213.md`, `docs/TESTANLEITUNG_MITARBEITERVERWALTUNG_HR.md`
- **Testanleitung MV + Urlaubsplaner (Verbindung):** `docs/TESTANLEITUNG_MITARBEITERVERWALTUNG_UND_URLAUBSPLANER_VANESSA.md` — für Vanessa, inkl. Prüfung der Verbindung Mitarbeiterverwaltung ↔ Urlaubsplaner (Urlaubsanspruch, „Im Urlaubsplaner anzeigen“).
- **Urlaubsplaner Usertest:** `docs/URLAUBSPLANER_USER_TEST_ERGEBNISSE_TAG198.md`, `docs/URLAUBSPLANER_USERTEST2_ZUSAMMENFASSUNG_TAG198.md`
- **Urlaubsplaner neu (Vanessa):** `docs/workstreams/urlaubsplaner/USERTEST_URLAUBSPLANER_NEU_VANESSA.md` — Auswertung von `Urlaubsplaner neu.docx` (Masseneingabe, Urlaubssperre, Reporte, UX)

---

## Beschreibung

Urlaubsplaner deckt Urlaubsanträge, Genehmigungsprozess, Chef-Übersicht, Urlaubsguthaben, Feiertage, Outlook-Kalender und E-Mail-Benachrichtigungen ab.  
**Schnittstelle zu HR:** Mitarbeiterstammdaten werden u. a. in der **Mitarbeiterverwaltung** (Admin) gepflegt; Urlaubsplaner nutzt diese Daten.

## Module & Dateien

### APIs
- `api/vacation_api.py` — Kern-API Urlaub
- `api/vacation_chef_api.py` — Chef-Übersicht, Genehmigungen
- `api/vacation_admin_api.py` — Admin-Funktionen (Urlaubssperren, Masseneingaben, Jahresend-Report, freie Tage)
- Zugehörige Services: `vacation_approver_service.py`, `vacation_calendar_service.py`, `vacation_locosoft_service.py`, `vacation_year_utils.py`

### Templates
- `templates/urlaubsplaner*.html` (urlaubsplaner.html, urlaubsplaner_v2.html, urlaubsplaner_chef.html, urlaubsplaner_admin.html)

### Mitarbeiterverwaltung (Admin, TAG 213)
- Route: `/admin/mitarbeiterverwaltung` (in `app.py`)
- Template: `templates/admin/mitarbeiterverwaltung.html`
- API: `api/employee_management_api.py`, `api/employee_sync_service.py`
- Navigation: **Admin** → **Mitarbeiterverwaltung** (base.html)
- Siehe auch Workstream **hr**: `docs/workstreams/hr/CONTEXT.md`

## DB-Tabellen (PostgreSQL drive_portal)

- Urlaub: `vacation_entitlements`, `vacation_bookings`, `vacation_types`, `holidays`
- Mitarbeiterverwaltung (TAG 213): siehe `migrations/add_mitarbeiterverwaltung_tables_tag213.sql` (u. a. `employee_working_time_models`, `employee_working_time_exceptions`, `employee_vacation_settings`, `employee_contact_data`, `employee_contract_data`, Erweiterungen `employees`)

---

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

### Urlaubsplaner (Kern)
- ✅ Anträge, Genehmigung, Chef-Übersicht, Guthaben, Feiertage im Einsatz
- ✅ Usertest-Fixes TAG 198: Genehmigung, Rollen, Resturlaub, Jahreswechsel, Urlaubssperren, Masseneingaben, Jahresend-Report, freie Tage
- ✅ **Urlaubssperren:** Admin-Löschen über `can_manage_vacation_blocks()` (Admin/Genehmiger); Urlaubssperre in Masseneingabe wahlweise **spezifische Mitarbeiter** (Ziel „Spezifische Mitarbeiter“) oder Abteilung – DB-Spalte `vacation_blocks.employee_ids`, Migration `alter_vacation_blocks_employee_ids.sql`
- ✅ **Schulung & Krankheit:** Nur **Genehmiger** und **Admin** buchbar (Einzelbuchung + Masseneingabe); Zeitausgleich weiterhin nur Admin
- ✅ **Resturlaub-Anzeige (Usertest-Feedback):** Nach Buchung/Genehmigung/Storno/Ablehnung/Jahreswechsel wird die Mitarbeiterliste inkl. Resturlaub neu geladen (`loadAllEmployees`), damit „28 Tage Rest“ sich nach 1 Tag verplant sofort auf 27 aktualisiert; Filter-Dropdowns werden bei erneutem Befüllen nicht mehr doppelt befüllt
- **Outlook-Kalender (Microsoft Graph):** Code in `vacation_calendar_service.py` vorhanden (add_vacation_event); `delete_vacation_event` nicht implementiert. **Aktuell nicht produktiv genutzt** – Option „Löschung bei Widerruf“ nur relevant, wenn Kalender-Integration aktiviert wird.
- 🔧 E-Mails (HR/MA) je nach Integrations-Stand

### Mitarbeiterverwaltung (Admin, TAG 213)
- ✅ Route `/admin/mitarbeiterverwaltung`, Template mit Sidebar (Mitarbeiterliste), Tabs: Deckblatt, Adressdaten, Mitarbeiterdaten (Vertrag, Arbeitszeitmodell, Ausnahmen), Moduldaten (Urlaubsplaner, Zeiten ohne Urlaub)
- ✅ Sync (LDAP/Locosoft/Vollständig), Speichern Deckblatt/Adressdaten
- 🔧 **Vorgehensweise zum Befüllen** (`docs/MITARBEITERVERWALTUNG_VORGEHENSWEISE_TAG213.md`):
  - **Phase 1:** Vertrag in `collectFormData()` ergänzen (`vertrag_company`, `vertrag_department`, `vertrag_entry_date`) und PUT konsistent
  - **Phase 2:** Moduldaten → Urlaubsplaner: Button „Urlaubseinstellungen speichern“, PUT `/api/employee-management/employee/<id>/vacation-settings`
  - **Phase 3:** Arbeitszeitmodelle — Add/Edit/Delete mit Modals, Anbindung an API (statt Dummy/alert)
  - **Phase 4:** Ausnahmen — Add/Delete mit Modal, API-Anbindung
  - **Phase 5:** Zeiten ohne Urlaub — Add/Delete mit Modal, API-Anbindung
- Backend: APIs für Arbeitszeitmodelle, Ausnahmen, Zeiten ohne Urlaub, Urlaubseinstellungen sind vorhanden.

### Vorgehen bei Verbesserungen/Ergänzungen
- **Ablauf:** Siehe `VORGEHEN_VERBESSERUNG_ERGAENZUNG.md` – Feature aus Liste wählen, umsetzen, Status in Feature-Liste + CONTEXT aktualisieren.
- **Backlog:** `FEATURE_LISTE_DRIVE_UMSETZUNG.md` (Priorisierung P1/P2/P3 am Ende).

### Nächstes Vorhaben: Urlaubsanspruch aus Mitarbeiterverwaltung
- **Ziel:** Urlaubsanspruch und fortlaufende Berechnung (Verbraucht, Geplant, Resturlaub) haben **eine Quelle** – die Mitarbeiterverwaltung; der Urlaubsplaner liest dieselben Daten (`vacation_entitlements`, `v_vacation_balance_*`).
- **Vorschlag und Schritte:** `URLAUBSANSPRUCH_AUS_MITARBEITERVERWALTUNG_VORSCHLAG.md` (in diesem Ordner)
- Kurz: Backend um `vacation_balance` pro Jahr im Employee-Detail ergänzen; Frontend Mitarbeiterverwaltung: Jahr-Auswahl, echte Anzeige aus `vacation_entitlements` + Saldo, Bearbeitung über `POST /api/vacation/admin/update-entitlement`.

### Bugfix: Blaue Punkt-Markierung in beide Richtungen (2026-02-13)
- **Problem:** Der blaue Punkt („finale Genehmigung/Buchung“) erschien nur, wenn der Tag zuerst in Locosoft eingetragen war; DRIVE-genehmigte Tage blieben ohne Punkt.
- **Lösung:** Blaue Markierung (`in-locosoft`) wird jetzt für **alle** genehmigten Buchungen angezeigt (`status === 'approved'`) – unabhängig ob Quelle Locosoft oder DRIVE. Locosoft bleibt führendes System; Anzeige im Kalender gilt für beide Richtungen.
- **Datei:** `templates/urlaubsplaner_v2.html` (Render-Logik der Zelle).

### Bugfix: Resturlaub-Anzeige berücksichtigt Locosoft (2026-02-13)
- **Problem:** Die Zahl neben dem Namen (z. B. „Katrin Geppert (27)“) ist der **Resturlaub**. Sie wurde nur aus der View `v_vacation_balance_*` berechnet, die nur **DRIVE**-Buchungen (`vacation_bookings`) kennt. Urlaubstage, die nur in **Locosoft** eingetragen waren (z. B. 12./13.02.), reduzierten die Anzeige nicht → Resturlaub blieb 27.
- **Lösung:** Die Balance-API (`GET /api/vacation/balance`) lädt für alle Mitarbeiter mit Locosoft-ID die Locosoft-Urlaubstage (Url/BUr) und setzt **Resturlaub = min(View-Resturlaub, Anspruch − Locosoft-Urlaub)**. Damit erscheint z. B. bei 2 Tagen Urlaub in Locosoft und 27 Anspruch die Anzeige **25**.
- **Datei:** `api/vacation_api.py` (get_all_balances).

### Feedback 3.2 umgesetzt (2026-02-13)
- **Nr. 3 Urlaubsanspruch-Optionen:** Dropdown in der Mitarbeiterverwaltung auf Personalplaner-Werte umgestellt: **5,5 | 11 | 16 | 22 | 27 | 30** Tage (+ „Andere …“). Datei: `templates/admin/mitarbeiterverwaltung.html`.
- **Rest-Anzeige oben links:** Die Anzeige „Rest“ (oben links und im User-Badge) kam aus `/my-balance` ohne Locosoft-Korrektur → zeigte z. B. 16 statt 11. **Lösung:** In `get_my_balance()` wird `resturlaub` jetzt mit derselben Logik wie in `get_all_balances()` gesetzt: **min(View-Resturlaub, Anspruch − Locosoft-Urlaub)**. Datei: `api/vacation_api.py`.
- **Freie Tage im Arbeitszeitmodell:** Anforderung dokumentiert; Umsetzung vorgeschlagen unter `FREIE_TAGE_ARBEITSZEITMODELL_VORSCHLAG.md` (nur Teilzeit, Freie Tage im Modell pflegen → im Urlaubsplaner ausgrauen; rote Kreise = freie Tage, grüne = Regelarbeitstage). Noch nicht implementiert.

### Usertest „Urlaubsplaner neu“ (Vanessa) umgesetzt (2026-02-16)
- **Masseneingabe:** Option „Spezifische Mitarbeiter“ als Standard, Multi-Select sichtbar; Urlaubssperren werden auch bei Masseneingabe geprüft (kein Admin-Bypass). API: `vacation_admin_api.mass_booking`.
- **Urlaubssperre löschen:** Urlaubsplaner-Admin-Seite zeigt Tabelle „Urlaubssperren“ mit Button „Löschen“ pro Zeile; `DELETE /api/vacation/admin/blocks/<id>`.
- **Farben:** Schulung blau (#5C6BC0), Krankheit (#E91E63); `urlaubsplaner_v2.html` CSS.
- **Meine Anträge:** Ein-/ausklappbar, standardmäßig eingeklappt (weniger unübersichtlich).
- **Monatsauswahl:** Pfeile „Vorheriger“ / „Nächster Monat“ neben Monat/Jahr-Dropdowns.
- **Mitarbeiterverwaltung:** Button „Anwendungen“ entfernt; „Reporte“ öffnet Modal „Urlaubs-Report“ mit Jahr-Auswahl und Tabelle (Name, Abteilung, Anspruch, Genommen, Offen) aus `GET /api/vacation/balance`.
- **Landau/Deggendorf getrennt:** Noch offen (Schema-Erweiterung `vacation_blocks` um Standort möglich).

### Serielle Genehmigung/Ablehnung im Batch-Modal (2026-02-13)
- **Feedback:** „Serielle Genehmigung/Ablehnung ist im Modal nicht möglich. Nur Löschung. Einzelgenehmigung Seitenleiste geht.“
- **Lösung:** Das Modal bei mehreren ausgewählten gebuchten Tagen bietet jetzt **drei Aktionen:** **Genehmigen**, **Ablehnen**, **Löschen**. Genehmigen/Ablehnen erscheinen nur für Genehmiger/Admins und nur, wenn unter den ausgewählten Buchungen mindestens eine **pending** ist; es werden dann nur die offenen Anträge genehmigt bzw. abgelehnt. Optionales Feld „Grund für Ablehnung“ für Batch-Ablehnung. Datei: `templates/urlaubsplaner_v2.html` (Batch-Popup, `showBatchDeletePopup`, `doBatchApprove`, `doBatchReject`).

### Session 2026-02-18 (Bugfixes, Doku, Vorgehen)
- ✅ **Zugriff Urlaubsplaner für Mitarbeiter:** `/api/vacation/balance` war mit `@role_required(['hr','admin'])` geschützt → Mitarbeiter (z. B. Silvia) sahen leere Mitarbeiterliste. Geändert auf `@login_required`, damit alle eingeloggten User die Planer-Liste laden können. Datei: `api/vacation_api.py`.
- ✅ **Masseneingabe:** Ziel springt nicht mehr auf „Abteilung“, wenn Urlaubssperre gewählt wird; `lastMassBookingTarget` merkt die Auswahl (Abteilung / Spezifische Mitarbeiter). Datei: `templates/urlaubsplaner_v2.html`.
- ✅ **Markierung bei Ziehen:** Auswahl (blaue Umrandung) erschien in falscher Zeile (z. B. Silvia wählt Tage, Christian wurde markiert). Beim Ziehen wird jetzt nur die Zeile des gewählten MA (`selEmpId`) markiert (Selector mit `data-e="${empId}"`). Datei: `templates/urlaubsplaner_v2.html`.
- ✅ **Chef-Übersicht Team-Zusammensetzung:** „Service & Empfang“ wird dem Genehmiger „Service“ zugeordnet (`DEPT_TO_APPROVAL_GRP` in `api/vacation_chef_api.py`).
- ✅ **Doku:** HAR-Auswertung personal-login.de (`PERSONAL_LOGIN_HAR_AUSWERTUNG.md`), Feature-Liste DRIVE (`FEATURE_LISTE_DRIVE_UMSETZUNG.md`), Vorgehen Verbesserung/Ergänzung (`VORGEHEN_VERBESSERUNG_ERGAENZUNG.md`); .md ins Windows-Sync kopiert.

### Offene Punkte aus Usertest (Urlaubsplaner)
- **Vanessa testet morgen** (Zugriff Planer, Masseneingabe, Markierung).
- Optional prüfen: falsche Darstellung bei Vanessa (Frontend/Filter), E-Mail an HR nach Genehmigung, Mitarbeiter-Abteilungszuordnungen (laut Usertest-Dokumenten).

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- **HR** (Mitarbeiterverwaltung, Organigramm), **auth-ldap** (Rollen), **integrations** (Microsoft Graph für Kalender/Mail)
