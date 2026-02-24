# Urlaubsplaner — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-24 (Bugfix Genehmigen 403, Bereinigung Debug-Code)

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
- ✅ **Schulung & Krankheit (Test DRIVE):** **Krankheit (type_id 5)** nur **Admin** buchbar (Einzelbuchung, Buch-Batch, Masseneingabe); **Schulung (9)** Genehmiger oder Admin; Zeitausgleich nur Admin. Buch-Batch prüfte fälschlich type_id 3 → korrigiert auf 5.
- ✅ **Vertretungsregel (Organigramm):** Vertreter darf im Zeitraum, in dem die vertretene Person Urlaub/Abwesenheit hat, **keinen Urlaub** buchen. Prüfung in Einzelbuchung, Buch-Batch und Masseneingabe; Fehlermeldung mit Namen der vertretenen Person. Masseneingabe meldet übersprungene Buchungen per `substitute_conflict_skipped` in der Antwort. Tabelle `substitution_rules` (auth-ldap/Organigramm).
- ✅ **Max. Abwesenheit pro Abteilung/Standort:** Es gilt eine Obergrenze für planbare Abwesenheit (nur **Urlaub + Schulung**; Krankheit nicht planbar) von **50 % pro Abteilung und Standort** (Deggendorf, Landau). Default 50 %, **pro Abteilung editierbar** im Organigramm (Tab „Abwesenheitsgrenzen“). Tabelle `department_absence_limits`, Migration `migrations/add_department_absence_limits.sql`. Prüfung in Einzelbuchung, Buch-Batch und Masseneingabe; bei Überschreitung Fehlermeldung mit blockierten Tagen.
- ✅ **Resturlaub und Krankheit (Vanessa/Stefan Geier):** Krankheitstage dürfen den Resturlaub **nicht** mindern. Die View zählt nur `vacation_type_id = 1` (Urlaub). Wenn Locosoft fälschlich Krankheit als Urlaub (Url/BUr) führt, drückt das die Anzeige. **Safeguard:** Wenn „Anspruch − Locosoft-Urlaub“ mehr als 0,5 Tage unter dem View-Resturlaub liegt, wird der **View-Resturlaub** angezeigt (in `/balance`, `/my-balance` und Validierung). Siehe `RESTURLAUB_KEINE_KRANKHEIT.md`.
- ✅ **Resturlaub-Anzeige (Usertest-Feedback):** Nach Buchung/Genehmigung/Storno/Ablehnung/Jahreswechsel wird die Mitarbeiterliste inkl. Resturlaub neu geladen (`loadAllEmployees`), damit „28 Tage Rest“ sich nach 1 Tag verplant sofort auf 27 aktualisiert; Filter-Dropdowns werden bei erneutem Befüllen nicht mehr doppelt befüllt
- ✅ **Genehmiger-Erkennung (Test Dispo):** Margit/Jennifer bekamen E-Mail, aber kein Genehmigungs-Modal. **Fix 1:** Username-Lookup case-insensitive und mit/ohne Domain (`_normalize_ldap_username`). **Fix 2:** AD-Gruppe „Genehmiger für Urlaub Dispo“ wird erkannt – LDAP liefert den **CN** der Gruppe (Anzeigename), nicht „GRP_Urlaub_Genehmiger_*“. In `vacation_approver_service.py` gilt ein User als Genehmiger, wenn er in einer Gruppe ist, die **entweder** `GRP_Urlaub_Genehmiger_*` / `GRP_Urlaub_Admin` **oder** im Namen „Genehmiger“ und „Urlaub“ enthält (`_is_approver_group()`). Damit zählt „Genehmiger für Urlaub Dispo“.
- ✅ **Strukturelle Entkopplung (Genehmiger vs. Kalender):** Damit ein Fehler in der Genehmiger-Logik nicht die ganze Seite leer macht: (1) **Backend** `get_my_balance`: `get_approver_summary` in try/except – bei Exception sicheres Default-`approver_info`, kein 500. (2) **Frontend** `loadMe`: bei `!r.success` kein harter Return ohne Hinweis; Konsole warnt, `isAppr`/`isAdmin` auf false, danach laufen `loadAllEmployees` und Kalender weiter. (3) `loadAllEmployees` bei Fehler: `allEmployees = []` explizit, klare Konsole-Meldung.
- ✅ **Resturlaub SSOT (Test DRIVE):** Eine zentrale Funktion `_compute_rest_display(anspruch, resturlaub_view, loco_urlaub)` in `vacation_api.py` – Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub). Verwendet in Balance, My-Balance, Validierung und Team-Übersicht; **Zeitausgleich (ZA)** mindert Rest nicht (nur Locosoft-`urlaub` = Url/BUr; ZA in Locosoft getrennt, Doku in `vacation_locosoft_service.py`).
- **Outlook-Kalender (Microsoft Graph):** Ab 2026-02: Bei Genehmigung schreibt DRIVE in **zwei** Ziele – (1) Shared Mailbox **drive@** (Übersicht für Führungskräfte, Sichtbarkeit nur für FK in M365 konfigurieren, siehe `KALENDER_DRIVE_NUR_FUEHRUNGSKRAEFTE.md`), (2) **persönlicher M365-Kalender** des Mitarbeiters (erscheint in Team-Ansicht des Vorgesetzten). Event-IDs in `vacation_bookings` für Storno-Löschung. Die Outlook-Kalendergruppe „Team: …“ kommt aus AD/M365, nicht aus DRIVE – siehe `OUTLOOK_TEAMKALENDER_VS_DRIVE.md`.
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

### Rollout: Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub) (2026-02)
- **Anspruch:** Führend aus Mitarbeiterverwaltung (Portal). Kein pauschaler Weihnachten/Silvester-Abzug; Halbtage als Buchungen erfassen.
- **Rest:** Damit Kalender (zeigt Portal + Locosoft) und Rest-Zahl übereinstimmen: **Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub)**. Locosoft-Urlaub (Url/BUr) wird wieder in Balance, My-Balance, Validierung und Team einbezogen. So zählen auch nur in Locosoft gebuchte Tage (z. B. Dezember) für den Rest.

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

### Vertretungsregel + Resturlaub nach Eingabe (Usertest Vanessa, 2026-02)
- **Vertretungsregel:** Fehlermeldung „Sie vertreten …“ nannte bisher immer die **erste** Vertretungsperson (z. B. Doris Egginger). Wenn Ramona an einem Tag aber **Sandra Brendel** vertritt (Sandra hat Urlaub) und Doris nicht, war die Meldung falsch. **Fix:** In `_check_substitute_vacation_conflict` wird für die Meldung die Person verwendet, **die an den blockierten Tagen tatsächlich Urlaub hat** (`conflict_vertretene_name`). Datei: `api/vacation_api.py`.
- **Resturlaub wird nach Eingabe nicht neu berechnet:** Backend-Test (`scripts/test_urlaub_resturlaub_nach_buchung.py`) bestätigt: View liefert nach Buchung korrekt reduzierten Rest. **Fixes:** (1) **Optimistisches Update:** Direkt nach erfolgreicher Buchung wird in `allEmployees` der Resturlaub des gebuchten MA um die gebuchten Tage verringert und `render()` sowie ggf. „Mein Rest“ in der Sidebar sofort aktualisiert. (2) Balance-Abfragen mit `fetch(..., { cache: 'no-store' })` und Backend-Header `Cache-Control: no-store`. (3) 120 ms Verzögerung vor Reload; danach erneutes `loadAllEmployees()`/`loadMe()` als Quelle der Wahrheit. Dateien: `templates/urlaubsplaner_v2.html`, `api/vacation_api.py`.

### Serielle Genehmigung/Ablehnung im Batch-Modal (2026-02-13)
- **Feedback:** „Serielle Genehmigung/Ablehnung ist im Modal nicht möglich. Nur Löschung. Einzelgenehmigung Seitenleiste geht.“
- **Lösung:** Das Modal bei mehreren ausgewählten gebuchten Tagen bietet jetzt **drei Aktionen:** **Genehmigen**, **Ablehnen**, **Löschen**. Genehmigen/Ablehnen erscheinen nur für Genehmiger/Admins und nur, wenn unter den ausgewählten Buchungen mindestens eine **pending** ist; es werden dann nur die offenen Anträge genehmigt bzw. abgelehnt. Optionales Feld „Grund für Ablehnung“ für Batch-Ablehnung. Datei: `templates/urlaubsplaner_v2.html` (Batch-Popup, `showBatchDeletePopup`, `doBatchApprove`, `doBatchReject`).

### Session 2026-02-18 (Bugfixes, Doku, Vorgehen)
- ✅ **Zugriff Urlaubsplaner für Mitarbeiter:** `/api/vacation/balance` war mit `@role_required(['hr','admin'])` geschützt → Mitarbeiter (z. B. Silvia) sahen leere Mitarbeiterliste. Geändert auf `@login_required`, damit alle eingeloggten User die Planer-Liste laden können. Datei: `api/vacation_api.py`.
- ✅ **Masseneingabe:** Ziel springt nicht mehr auf „Abteilung“, wenn Urlaubssperre gewählt wird; `lastMassBookingTarget` merkt die Auswahl (Abteilung / Spezifische Mitarbeiter). Datei: `templates/urlaubsplaner_v2.html`.
- ✅ **Markierung bei Ziehen:** Auswahl (blaue Umrandung) erschien in falscher Zeile (z. B. Silvia wählt Tage, Christian wurde markiert). Beim Ziehen wird jetzt nur die Zeile des gewählten MA (`selEmpId`) markiert (Selector mit `data-e="${empId}"`). Datei: `templates/urlaubsplaner_v2.html`.
- ✅ **Chef-Übersicht Team-Zusammensetzung:** „Service & Empfang“ wird dem Genehmiger „Service“ zugeordnet (`DEPT_TO_APPROVAL_GRP` in `api/vacation_chef_api.py`).
- ✅ **Doku:** HAR-Auswertung personal-login.de (`PERSONAL_LOGIN_HAR_AUSWERTUNG.md`), Feature-Liste DRIVE (`FEATURE_LISTE_DRIVE_UMSETZUNG.md`), Vorgehen Verbesserung/Ergänzung (`VORGEHEN_VERBESSERUNG_ERGAENZUNG.md`); .md ins Windows-Sync kopiert.

### Rollout: Kein pauschaler Weihnachten/Silvester-Abzug mehr (2026-02)
- **Entscheidung:** Da wir auf Locosoft-Daten verzichten und DRIVE mit halben Tagen umgehen kann: Die pauschale „1 Tag Abzug“ (0,5 + 0,5 für 24.12. und 31.12.) wurde entfernt. Halbe Tage Weihnachten/Silvester werden als **normale Urlaubsbuchungen** im Planer erfasst und zählen in verbraucht. Anspruch und Rest = reiner View-Wert (Mitarbeiterverwaltung + vacation_bookings), keine Abzüge mehr in der API.

### Datenkorrektur + Resturlaub Jennifer/Margit (2026-02, Vanessa)
- **Margit Loibl:** Anspruch 2026 war im Portal mit 23 Tagen geführt, in Locosoft 27/28. Korrektur: `migrations/fix_margit_loibl_urlaubsanspruch_2026.sql` setzt `total_days = 27` für Margit Loibl, Jahr 2026.
- **Jennifer / Margit – Resturlaub:** Wenn bereits mehrere Tage in Locosoft verplant sind, zeigt der Urlaubsplaner den Rest als **min(View-Rest, Anspruch − Locosoft-Urlaub)**. Dafür muss die Locosoft-Verbindung stehen (Mitarbeiter mit Locosoft-ID). Jennifer (1008) und Margit Loibl (1004) haben in Locosoft 2026 z. B. 10 bzw. 8 Urlaubstage; die Anzeige sollte nach Reload 17 bzw. 18 Rest liefern (nach Abzug Weihnachten/Silvester). Bei weiterem Abweichen: Locosoft-Verbindung prüfen oder Anspruch in der Mitarbeiterverwaltung abgleichen.

### Bugfix: Resturlaub-Validierung bei negativem Locosoft-Wert (2026-02, Buchhaltung)
- **Problem:** Buchhaltung konnte Urlaub nicht eintragen (z. B. Bianca Greindl, zuvor Silvia): Liste zeigte z. B. 6 Rest, Fehlermeldung „Verfügbar: -5,0 Tage“. Ursache: Locosoft meldete mehr Urlaubstage als Portal-Anspruch → Validierung rechnete negativen Rest, Anzeige nutzt View/Fallback und zeigte positiven Rest.
- **Lösung:** In `api/vacation_api.py` (Einzelbuchung + book-batch): Wenn `available_days < 0`, Resturlaub aus View `v_vacation_balance_{Jahr}` lesen und für Validierung verwenden (≥ 0). So stimmen Anzeige und Buchungsprüfung überein.
- **Doku:** `BUGFIX_RESTURLAUB_VALIDIERUNG_NEGATIV.md` – für künftige Fälle in derselben Thematik.

### Usertest-Fixes: Resturlaub konsistent, 0 Rest ablehnen, Neuberechnung (2026-02)
- **Sandra Schimmer:** „Wieder zu wenig Resturlaub“ trotz 16 Tage Rest in der Liste → Validierung nutzte andere Quelle (Locosoft-Formel) als die Anzeige (View + Locosoft-Cap). **Lösung:** Hilfsfunktion `_get_available_rest_days_for_validation()` berechnet verfügbaren Rest **wie die Balance-Anzeige** (View + min(View, Anspruch − Locosoft)); Einzel- und Batch-Buchung nutzen diese Quelle. Kein Abweichen mehr zwischen Liste und Buchungsprüfung.
- **Herbert Huber:** 0 Tage Rest, Buchung trotzdem möglich → Bei Batch fehlte View-Fallback, `available_days` blieb `None`. **Lösung:** Batch nutzt dieselbe Hilfsfunktion (immer View-Basis); bei 0 Rest wird abgelehnt (`requested_days > available_days`).
- **Keine Neuberechnung des Resturlaubs:** Nach Urlaubsantrag bzw. Typ-Änderung blieb die angezeigte Restzahl unverändert. **Lösung:** Nach Typ-Änderung (Edit-Popup) wird `loadAllEmployees()` aufgerufen, damit die Tabelle den Resturlaub neu lädt. Nach Antrag-Einreichung war `loadAllEmployees()` bereits vorhanden.

### Offene Punkte aus Usertest (Urlaubsplaner)
- Optional prüfen: falsche Darstellung bei Vanessa (Frontend/Filter), E-Mail an HR nach Genehmigung, Mitarbeiter-Abteilungszuordnungen (laut Usertest-Dokumenten).

### Qualität unzureichend – Test nach 5 Min abgebrochen (2026-02-24)
- **Quelle:** `Test DRIVE.docx` (Windows-Sync: `docs/workstreams/urlaubsplaner/`). Test wurde nach kurzer Zeit abgebrochen; vier konkrete Fehler dokumentiert.
- **Stellungnahme:** `STELLUNGNAHME_TEST_DRIVE_QUALITAET.md` – Einschätzung und Abarbeitungsreihenfolge.
- **Die vier Punkte:** (1) Resturlaub Susanne Kerscher falsch (16−3=13 erwartet, 14 angezeigt), (2) Susanne Kerscher kann Krankheit eintragen (sollte nur Admin), (3) Bei Zeitausgleich werden Urlaubstage abgezogen, (4) Vertretungsregel nicht mehr aktiv. **Vor weiterem Rollout (z. B. Disposition) diese Punkte prüfen/beheben.**

### Rechteverwaltung: ein Feature, Embed, Personalakte-Link (2026-02-24)
- ✅ **Mitarbeiter-Konfig-Modal erweitert:** In Rechteverwaltung → Tab „Mitarbeiter-Konfig“ öffnet der Stift ein großes Modal mit Stammdaten (Abteilung, Standort), Vertretungen (Vertritt/Wird vertreten), **Urlaub** (Jahr, Anspruch, Übertrag, Korrektur, Max. Urlaubslänge, Berechnung). Ein Klick „Speichern“ speichert Stammdaten + Urlaubseinstellungen + Urlaubsanspruch (POST update-entitlement).
- ✅ **Embed-Ansicht:** Urlaubsverwaltung und Mitarbeiterverwaltung werden in den Rechteverwaltung-Tabs mit `?embed=1` geladen → keine doppelte Navigation (Verschachtelung). `base_embed.html`, Routen mit `base_template=base_embed.html` bei `embed=1`.
- ✅ **Hinweise Redundanz:** In Digitaler Personalakte (Moduldaten/Urlaub) Hinweis auf Urlaubsverwaltung; in Urlaubsplaner-Admin Hinweis auf Digitale Personalakte.
- ✅ **Link „Digitale Personalakte bearbeiten“:** Öffnet `/admin/mitarbeiterverwaltung?embed=1&employee_id=<id>`; Personalakte wählt den Mitarbeiter automatisch (`employee_id` aus URL, `requestAnimationFrame(() => selectEmployee(id))`).
- ✅ **Testanleitung:** `docs/TESTANLEITUNG_VANESSA_RECHTEVERWALTUNG_MITARBEITER_URLAUB.md` – für Vanessa/Test-Team: alle Änderungen (Modal, Links, Embed, Hinweise) durchspielen. Test läuft.

### Bugfix: Genehmigen 403 – „Fehler beim Genehmigen“ (Margit für Susanne, 2026-02-24)
- **Ursache:** In `vacation_approver_service.py` warf `get_team_for_approver()` eine Exception, weil in `get_team_by_manager()` und in der Admin-Team-Abfrage **boolean-Spalten** mit Integer verglichen wurden: `loco_employees.is_latest_record = 1` und teils `e.aktiv = 1`. PostgreSQL: „operator does not exist: boolean = integer“. Die Exception wurde gefangen → leeres Team → 403 „Kein Team zugeordnet“.
- **Fix:** Alle betroffenen Stellen auf PostgreSQL-taugliche Vergleiche umgestellt: `le.is_latest_record IS NOT DISTINCT FROM true`, `e.aktiv = true`. Dateien: `api/vacation_approver_service.py` (get_team_by_manager, Admin-Block).
- **Beibehalten:** Abteilungs-Erweiterung aus Anzeigenamen; Kalender-Event-IDs in eigener DB-Session; try/except um E-Mails/Kalender; Fallback auf `current_user` und case-insensitiver Lookup in `get_employee_from_session`; `credentials: 'include'` und 4xx-Body-Parsing im Frontend.
- **Bereinigt:** Debug-Logging (APPROVE 401/403), `reason`/`debug` in API-Responses, lange Toast-/Konsole-Debug-Ausgaben im Frontend.

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- **HR** (Mitarbeiterverwaltung, Organigramm), **auth-ldap** (Rollen), **integrations** (Microsoft Graph für Kalender/Mail)
