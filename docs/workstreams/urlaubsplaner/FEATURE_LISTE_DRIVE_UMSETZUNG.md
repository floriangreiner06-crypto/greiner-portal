# Feature-Liste: DRIVE-Urlaubsplaner – Umsetzung & Referenz

**Zweck:** Priorisierbare Liste von Funktionen für den DRIVE-Urlaubsplaner.  
**Referenz:** personal-login.de (kvg-hzf) / HAR-Auswertung, Usertests, CONTEXT.  
**Status-Spalte:** ✅ vorhanden | 🔶 teilweise | ❌ fehlt/geplant

---

## Legende

| Status | Bedeutung |
|--------|-----------|
| ✅ | In DRIVE umgesetzt und nutzbar |
| 🔶 | Teilweise (z.B. nur Admin, oder ohne Locosoft-Anbindung) |
| ❌ | Fehlt oder nur als Anforderung dokumentiert |

**Priorität (optional):** P1 = wichtig für Tagesgeschäft, P2 = wichtig, P3 = nice-to-have.

---

## 1. Stammdaten & Mitarbeiter

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 1.1 | Mitarbeiterliste mit Abteilung/Standort | MA im Planer nach Abteilung gruppiert, Standortfilter | ✅ | – | `v_vacation_balance_*`, Filter Abteilung/Standort |
| 1.2 | Mitarbeiterstammdaten (Name, Eintritt, Austritt) | Basis für Anzeige und Berechtigungen | ✅ | HAR ds_VORNAME, ds_NAME, ds_date_EINTRITT | `employees`, Mitarbeiterverwaltung |
| 1.3 | „Im Urlaubsplaner anzeigen“ pro MA | MA gezielt ausblenden (z.B. Auszubildende) | ✅ | – | `employee_vacation_settings.show_in_planner` |
| 1.4 | Arbeitszeitmodell pro MA | Regelarbeitszeiten / Teilzeit | 🔶 | HAR pageId 11 | MV: Arbeitszeitmodell-Tab, API vorhanden; Anzeige im Planer (z.B. freie Tage) optional |
| 1.5 | Ausnahmen vom Arbeitszeitmodell | Einzelne Tage/Zeiträume abweichend | 🔶 | – | MV: Ausnahmen-Tab, API vorhanden |
| 1.6 | Freischaltung Urlaubsplaner pro MA | MA darf Planer nutzen / buchen | ✅ | HAR ds_UP_FREISCHALTUNG | `employee_vacation_settings`, Rechte |

---

## 2. Urlaubsanspruch & Saldo

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 2.1 | Jahresanspruch (Tage) pro MA/Jahr | z.B. 27, 30, 22 | ✅ | HAR ds_URLAUB_ANSPRUCH | `vacation_entitlements.total_days` |
| 2.2 | Übertrag aus Vorjahr | Resturlaub mitgenommen | ✅ | HAR ds_full_UP_MAX_UEBERTRAG | `vacation_entitlements.carried_over` |
| 2.3 | Max. Übertrag begrenzen | Obergrenze Übertragstage | 🔶 | HAR ds_UP_MAX_UEBERTRAG | Logik bei Jahreswechsel/Import; Konfiguration optional |
| 2.4 | Verbraucht / Geplant / Rest | Anspruch − verbraucht − geplant = Rest | ✅ | – | View `v_vacation_balance_*`, nur Urlaub (type_id=1) |
| 2.5 | Resturlaub-Anzeige inkl. Locosoft | Rest mindert sich auch durch Locosoft-Urlaub | ✅ | – | `/balance`, `/my-balance` mit Locosoft-Abzug |
| 2.6 | Anspruch-Varianten (5,5 / 11 / 16 / 22 / 27 / 30) | Dropdown in MV | ✅ | – | Mitarbeiterverwaltung, update-entitlement |
| 2.7 | Kein Verfall (Übertrag nicht verfallen) | Option „Kein Verfall“ | ❌ | HAR ds_UP_KEIN_VERFALL | Konfiguration pro MA oder global möglich |
| 2.8 | Max. Urlaubslänge pro Buchung | z.B. max. 14 Tage am Stück | ❌ | HAR ds_MAXURLAUBLAENGE | Validierung bei Buchung denkbar |

---

## 3. Buchung & Anträge

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 3.1 | Urlaub buchen (Einzeltag / Bereich) | Klick/Ziehen, Halbtag möglich | ✅ | – | Buch-Popup, `day_part` |
| 3.2 | Buchungsarten: Urlaub, ZA, Krank, Schulung | Typen mit Farbe/Icons | ✅ | – | `vacation_types`, nur Urlaub zählt für Rest |
| 3.3 | Antrag einreichen → pending | MA reicht ein, Genehmiger sichtbar | ✅ | – | `status = pending`, Zu genehmigen |
| 3.4 | Genehmigen / Ablehnen (einzeln + Batch) | OK / Ablehnen, optional Grund | ✅ | – | Sidebar, Batch-Modal |
| 3.5 | Stornieren / Löschen | Bereits genehmigte Buchung zurückziehen | ✅ | – | Popup, API |
| 3.6 | Masseneingabe (Abteilung / MA-Liste / Alle) | Mehrere MA, mehrere Tage, Buchungsart | ✅ | – | Masseneingabe-Modal, Urlaubssperre prüfbar |
| 3.7 | Automatisch genehmigen (Masseneingabe) | Option bei Massenbuchung | ✅ | – | Checkbox im Modal |
| 3.8 | Buchungszeitraum einschränken (von–bis) | Nur in bestimmten Zeiträumen buchbar | ❌ | HAR ds_date_UP_BUCHEN_VON/_BIS | Validierung oder Admin-Einstellung |

---

## 4. Urlaubssperren & Freie Tage

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 4.1 | Urlaubssperre (Datum + Abteilung oder MA) | Sperre für Abteilung oder konkrete MA | ✅ | – | `vacation_blocks`, Masseneingabe „Urlaubssperre“ |
| 4.2 | Sperre löschen (Admin) | Tabelle Urlaubssperren mit Löschen-Button | ✅ | – | Urlaubsplaner-Admin |
| 4.3 | Feiertage | Tage ausgegraut, nicht buchbar | ✅ | – | `holidays`, Kalender |
| 4.4 | Freie Tage (Betriebsferien etc.) | Zusätzliche freie Tage, ggf. Anspruchsminderung | ✅ | – | `free_days`, affects_vacation_entitlement (TAG 209) |
| 4.5 | Sperre pro Standort | Landau vs. Deggendorf getrennt | ❌ | – | CONTEXT: „Landau/Deggendorf getrennt“ offen |

---

## 5. Genehmigung & Workflow

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 5.1 | Genehmiger pro Abteilung/Standort | Wer darf genehmigen (Priorität 1/2) | ✅ | HAR Berechtigungen | `vacation_approval_rules` |
| 5.2 | Chef-Übersicht (Teams + offene Anträge) | Übersicht aller Genehmiger mit Team und Salden | ✅ | – | `vacation_chef_api`, Chef-Seite |
| 5.3 | „Zu genehmigen“ in Sidebar | Offene Anträge für eingeloggten Genehmiger | ✅ | – | Sidebar, `/requests` |
| 5.4 | Workflow-/Wertungsskript (z.B. Verfall) | Erweiterte Regeln wie Referenz | ❌ | HAR ds_UP_WF_*, ds_UP_WERTUNGSSKRIPTE_ID | Optional für spätere Erweiterung |
| 5.5 | E-Mail bei Genehmigung/Ablehnung | Benachrichtigung an MA | 🔶 | – | Je nach Integrations-Stand |

---

## 6. Berichte & Export

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 6.1 | Urlaubs-Report (Jahr, Anspruch/Genommen/Offen) | Tabelle pro Jahr | ✅ | Usertest | Report-Modal aus MV, `/api/vacation/balance` |
| 6.2 | Jahresend-Report (Export) | Download für Jahresabschluss | ✅ | – | Admin, year-end-report |
| 6.3 | Export Kalender (z.B. Outlook) | Eintrag bei Genehmigung | 🔶 | – | Outlook-Anbindung; Löschung bei Widerruf fehlt |

---

## 7. Berechtigungen & Rollen

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 7.1 | Rolle: MA (eigene Buchung, eigene Anträge) | Standard-Nutzer | ✅ | – | Login, Rechte |
| 7.2 | Rolle: Genehmiger (Team genehmigen) | Zugriff auf Chef-Übersicht, Zu genehmigen | ✅ | – | `urlaub_genehmigen`, approval_rules |
| 7.3 | Rolle: HR/Admin (Sperren, Masseneingabe, Reporte) | Volle Admin-Funktionen | ✅ | – | hr/admin, vacation_admin_api |
| 7.4 | Berechtigungsmatrix (fein granulierte Rechte) | Wie Referenz pageId 87 | 🔶 | HAR Berechtigungen | DRIVE: grobe Rollen; feine Matrix optional |

---

## 8. Anzeige & UX

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 8.1 | Kalender Monat/Jahr, Filter Abteilung/Standort | Planer-Ansicht | ✅ | – | urlaubsplaner_v2 |
| 8.2 | Farben/Icons pro Buchungsart | Urlaub grün, ZA blau, Krank pink, Schulung blau | ✅ | – | CSS, Icons |
| 8.3 | „In Locosoft“-Markierung (blauer Punkt) | Zeigt an: in Locosoft erfasst / genehmigt | ✅ | – | Render-Logik approved |
| 8.4 | Meine Anträge ein-/ausklappbar | Weniger Überblick | ✅ | Usertest | Sidebar |
| 8.5 | Monatsnavigation (Pfeile vor/zurück) | Neben Monat/Jahr | ✅ | Usertest | Buttons |
| 8.6 | Freie Tage im Arbeitszeitmodell anzeigen | Teilzeit: welche Tage frei (ausgegraut) | ❌ | CONTEXT | FREIE_TAGE_ARBEITSZEITMODELL_VORSCHLAG.md |

---

## 9. Integration & Technik

| Nr | Feature | Beschreibung | Status | Referenz | DRIVE-Ort / Anmerkung |
|----|---------|--------------|--------|----------|------------------------|
| 9.1 | Locosoft: Urlaubstage für Resturlaub | Rest = min(View, Anspruch − Locosoft-Urlaub) | ✅ | – | vacation_locosoft_service, /balance |
| 9.2 | Locosoft: Abwesenheiten (Url, BUr, Snd, Krn, ZA) | Anzeige/Korrektur | ✅ | – | Nur Url/BUr mindern Rest; Snd nicht |
| 9.3 | Jahreswechsel: neue Entitlements + View | Automatisch neues Jahr anlegen | ✅ | – | vacation_year_utils |
| 9.4 | Balance für alle MA (Planer-Liste) | Jeder eingeloggte User sieht Liste | ✅ | Security-Fix | /balance mit login_required |

---

## Priorisierung (Vorschlag)

- **Bereits erledigt (kein Backlog):** Alle ✅ und die meisten 🔶.
- **P1 (wenn Lücke schmerzt):** 2.7 (Kein Verfall), 4.5 (Sperre pro Standort), 8.6 (Freie Tage im Arbeitszeitmodell).
- **P2:** 2.8 (Max. Urlaubslänge), 3.8 (Buchungszeitraum), 5.5 (E-Mail), 6.3 (Outlook-Löschung).
- **P3:** 5.4 (Wertungsskript), 7.4 (feine Berechtigungsmatrix).

---

## Nutzung der Liste

1. **Status** bei Umsetzung von 🔶/❌ auf ✅ setzen (oder 🔶 bei Teilumsetzung).
2. **Priorität** pro Feature festlegen (P1/P2/P3) und in Backlog/Sprint aufnehmen.
3. **DRIVE-Ort** ergänzen, sobald Code/Route/View existiert.
4. **Neue Features** als neue Zeilen ergänzen; Referenz „personal-login“ oder „Usertest“ oder „intern“ angeben.

Die Liste lebt im Workstream **urlaubsplaner** und kann in CONTEXT.md verlinkt werden.
