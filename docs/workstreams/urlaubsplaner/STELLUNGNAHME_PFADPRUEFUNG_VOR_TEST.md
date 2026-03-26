# Stellungnahme: Prüfung aller Pfade vor erneutem Test

**Datum:** 2026-02  
**Auftrag:** Alle relevanten Pfade (Buchung, Genehmigung, Rest-Anzeige) prüfen und Stellung abgeben. **Keine Code-Änderungen** in diesem Schritt.

---

## 1. Datenquelle Resturlaub (einheitlich)

| Pfad | Quelle Rest | Locosoft in Berechnung? |
|------|-------------|---------------------------|
| **GET /balance** | View `v_vacation_balance_{year}` → resturlaub, dann `_compute_rest_display(..., 0)` | Nein |
| **GET /my-balance** | View (über Balance-Abfrage), resturlaub aus View; Locosoft-Abruf für Balance **aus** (leerer Start) | Nein |
| **GET /balance (Team-Chef)** | View, `_compute_rest_display(anspruch, resturlaub_view, 0)` | Nein |
| **_get_available_rest_days_for_validation** | View, `_compute_rest_display(..., 0)`; Locosoft wird nicht mehr aufgerufen | Nein |
| **_compute_rest_display** | Gibt nur `resturlaub_view` (gerundet) zurück; Parameter `loco_urlaub` wird ignoriert | Nein |

**Bewertung:** Resturlaub kommt durchgängig nur aus der View (DRIVE). Keine Locosoft-Kappe mehr in der Berechnung.

---

## 2. Pfad: Buchung (POST /book, POST /book-batch)

**Ablauf (vereinfacht):**
1. Session/Employee ermitteln, ggf. for_employee_id (Admin).
2. Doppelbuchung prüfen (bereits gebucht an dem Datum?).
3. **Resturlaub-Validierung** (nur bei type_id = 1): `_get_available_rest_days_for_validation(...)` → verfügbare Tage aus **View**, Vergleich mit angefragten Tagen.
4. Vertretungsregel, Max-Abwesenheit, Berechtigung (Krankheit nur Admin usw.).
5. INSERT in `vacation_bookings` (status pending oder approved je nach Typ/Admin).
6. E-Mail an Genehmiger (bei pending) bzw. an HR (bei sofort approved).

**Risiken / Anmerkungen:**
- Kommentar im Code (Zeile 2451) erwähnt noch „View + Locosoft-Cap“ – **inhaltlich obsolet**, die Funktion nutzt nur View (0 für Locosoft).
- Buchung schreibt nur in `vacation_bookings`; die View liest dieselbe Tabelle → nach Commit ist der nächste Balance-Abruf konsistent (sofern View für das Jahr existiert).

---

## 3. Pfad: Genehmigung (POST /approve)

**Ablauf:**
1. Session, Prüfung Genehmiger/Admin, booking_id.
2. Buchung laden (vacation_bookings); Prüfung status == 'pending', Team-Zuordnung bei Nicht-Admin.
3. UPDATE vacation_bookings SET status = 'approved', approved_by, approved_at, comment.
4. Commit.
5. E-Mail an HR, E-Mail an MA, Kalender (Outlook) – in try/except, Fehler blockieren nicht die Genehmigung.

**Risiken / Anmerkungen:**
- Keine Resturlaub-Prüfung bei Genehmigung (Rest wird nur bei Buchung geprüft). **Fachlich gewollt.**
- Keine Locosoft-Anbindung in diesem Pfad.

---

## 4. Pfad: Storno (POST /cancel)

**Ablauf:** Buchung laden → UPDATE status = 'cancelled', Commit; E-Mail an HR bei vorher approved; Kalender-Einträge löschen (wenn IDs gespeichert).

**Risiken / Anmerkungen:**
- Kein Locosoft in der Logik. View zählt nur pending/approved (type_id=1) → nach Storno sinkt verbraucht/geplant, Rest steigt wieder.

---

## 5. Pfad: Kalender-Anzeige (GET /all-bookings)

**Ablauf:**
1. vacation_bookings für Jahr (approved, pending) aus Portal.
2. **Locosoft-Zuschaltung:** aktuell **deaktiviert** (`if False and LOCOSOFT_AVAILABLE ...`) für „leerer Start“ → Kalender nur aus DRIVE.

**Risiken / Anmerkungen:**
- Kalender und Rest-Anzeige sind damit aus derselben Quelle (DRIVE). Kein Widerspruch mehr „voll im Kalender, leer in der Zahl“.

---

## 6. View v_vacation_balance_{year}

**Logik (aus Migration TAG 209 / fix_vacation_balance_free_days_tag209.sql):**
- **anspruch:** vacation_entitlements (total_days + carried_over + added_manually) minus freie Tage (free_days mit affects_vacation_entitlement).
- **verbraucht:** Summe Tage aus vacation_bookings, **status = 'approved'**, **vacation_type_id = 1** (nur Urlaub).
- **geplant:** Summe Tage aus vacation_bookings, **status = 'pending'**, **vacation_type_id = 1**.
- **resturlaub:** anspruch − (verbraucht + geplant) in der View formelhaft.

**Hinweis:** Die **Funktion** `create_vacation_balance_view(year_val)` in fix_vacation_balance_free_days_tag209.sql verwendet **`WHERE e.aktiv = 1`**. Unter PostgreSQL ist `employees.aktiv` typischerweise boolean – dann wäre `e.aktiv = true` bzw. `e.aktiv IS NOT DISTINCT FROM true` korrekt. Die **einzelnen** View-Definitionen (z. B. create_vacation_balance_2026.sql, fix_vacation_balance_view_resturlaub_tag198.sql) nutzen **`e.aktiv = true`**. Wenn neue Jahre über die **Funktion** angelegt werden, könnte `aktiv = 1` zu Problemen führen. Für die **bereits** existierenden Views (z. B. 2025, 2026) wurde vermutlich die richtige Migration (mit `aktiv = true`) ausgeführt – zur Sicherheit sollte einmal geprüft werden, welche View-Definition auf dem Server aktuell gilt.

---

## 7. Frontend: Rest-Anzeige nach Aktionen

| Aktion | Aufruf nach Erfolg | _lastVacationBooking |
|--------|---------------------|-----------------------|
| **Buchung (submit)** | loadMyBook, loadAllBookings, loadAllEmployees(bookingYear), loadMe(bookingYear) | **Vor** Reload gelöscht (Fix 27→26) → Server-Wert wird 1:1 angezeigt. |
| **Typ ändern (changeType)** | loadMyBook, loadAllBookings, loadAllEmployees, loadMe | Nicht gesetzt → unkritisch. |
| **Storno (doDelete)** | loadMyBook, loadAllBookings, **loadMe** (kein loadAllEmployees) | Nicht gesetzt. |
| **Genehmigen (doApprove)** | loadMyBook, loadAllBookings, **loadMe** (kein loadAllEmployees) | Nicht gesetzt. |
| **Ablehnen (doBatchReject)** | loadMyBook, loadAllBookings, **loadMe** (kein loadAllEmployees) | Nicht gesetzt. |
| **Batch-Löschen (doBatchDelete)** | loadMyBook, loadAllBookings, loadAllEmployees, loadMe | Nicht gesetzt. |

**Risiken / Anmerkungen:**
- **Storno (doDelete) und Genehmigung/Ablehnung (doApprove, doBatchReject):** Es wird **kein** `loadAllEmployees()` aufgerufen. Die **Liste** (Rest-Zahl neben dem Namen in der Tabelle) kann sich daher **nicht** aktualisieren; nur die Sidebar (loadMe) und der Kalender (loadAllBookings) werden neu geladen. Wer „Rest“ in der **Zeile** des betroffenen MA erwartet, sieht die Änderung erst nach Wechsel des Monats/Jahres oder Reload. **Mögliche Verwirrung**, kein Doppelabzug mehr.
- **Buchung:** Doppelabzug (27→26) ist durch Löschen von _lastVacationBooking vor dem Reload behoben.

---

## 8. Weitere Stellen (kurz)

- **Masseneingabe (admin mass-booking):** Schreibt in vacation_bookings, keine Locosoft-Logik für Rest. Nach Aktion: loadAllEmployees, loadAllBookings, loadMe → Liste und Rest aktuell.
- **my-balance:** Kein Locosoft-Abruf mehr für Balance (Banner zeigt verbraucht/0 aus DRIVE).
- **GET /my-bookings:** Locosoft-Abruf für „in_locosoft“-Badge pro Buchung – **nur Anzeige**, beeinflusst Rest nicht.

---

## 9. Zusammenfassung

| Bereich | Stand | Offene Punkte |
|---------|--------|----------------|
| **Rest-Berechnung** | Nur View (DRIVE), kein Locosoft | – |
| **Buchung** | Validierung aus View; Buchung nur in vacation_bookings | Kommentar „Locosoft-Cap“ im Code obsolet (kosmetisch). |
| **Genehmigung** | Nur UPDATE + E-Mails/Kalender, keine Rest-Logik | – |
| **Kalender** | Nur DRIVE (Locosoft aus) | – |
| **Frontend Rest nach Buchung** | _lastVacationBooking vor Reload gelöscht → kein 27→26 mehr | – |
| **Frontend Rest nach Storno/Genehmigung/Ablehnung** | loadAllEmployees wird nicht aufgerufen | Rest in der **Mitarbeiterliste** aktualisiert sich erst bei anderem Reload (z. B. Monat wechseln oder Seite neu laden). |
| **View-Definition** | verbraucht/geplant/resturlaub nur type_id=1, Jahr über booking_date | Falls neue Jahre über Funktion erstellt werden: `e.aktiv = 1` in der Funktion prüfen (PostgreSQL boolean). |

**Empfehlung vor Test:**  
Die geprüften Pfade sind für „Rest nur aus DRIVE“ und „leerer Start“ konsistent. Für den Test relevant: Nach **Buchung** sollte die Rest-Anzeige stabil bleiben (27 bleibt 27 nach Reload). Nach **Storno** oder **Genehmigung/Ablehnung** nur Sidebar/Kalender sofort aktuell; die Zahl in der **Zeile** der Tabelle ggf. erst nach Reload/Seitenwechsel – das kann man im Test beobachten und bei Bedarf in einem Folgeschritt durch Aufruf von loadAllEmployees nach Storno/Genehmigung/Ablehnung glätten.

---

## 10. Funktion „Urlaubssperre“ (Review nachgeholt)

**Datenquelle / Anzeige:**
- **GET /api/vacation/blocks-and-free-days:** Liefert Urlaubssperren (`vacation_blocks`) und freie Tage (`free_days`) für das Frontend. Frontend zeigt gesperrte Tage optisch (z. B. „blocked“, roter Strich) und verhindert Klick nur per UI – die **Backend-Validierung** muss trotzdem greifen.
- **Admin:** GET/POST/DELETE `/api/vacation/admin/blocks` – Lesen, Anlegen (Abteilung **oder** spezifische Mitarbeiter über `employee_ids`), Löschen. Berechtigung: `can_manage_vacation_blocks()`.

**Prüfung bei Buchung:**

| Pfad | Urlaubssperre (vacation_blocks) | Freie Tage (free_days) |
|------|---------------------------------|-------------------------|
| **POST /book (Einzelbuchung)** | **Nicht geprüft** | **Nicht geprüft** |
| **POST /book-batch** | Geprüft, aber **nur** nach `department_name`; Sperren mit **nur** `employee_ids` (spezifische MA) werden **nicht** berücksichtigt | Geprüft |
| **POST /api/vacation/admin/mass-booking** | Geprüft: **department_name ODER** `employee_ids` (spezifische MA) | Nicht in der geprüften Stelle; ggf. separat |

**Bewertung:**
- **Lücke Einzelbuchung:** Über „Einzelbuchung“ (ein Tag, normales Buchen) können **Urlaubssperre und Betriebsferien umgangen** werden – das Backend prüft beides dort nicht.
- **Lücke book-batch:** Sperren, die nur für **spezifische Mitarbeiter** angelegt sind (`employee_ids` gesetzt, ohne Abteilung), werden in **book-batch** nicht erkannt; nur Abteilungs-Sperren greifen.
- **Empfehlung:** Urlaubssperre und freie Tage auch in **POST /book** prüfen (analog zu book-batch, inkl. Berücksichtigung von `employee_ids`). In **book-batch** die Logik um „Sperre für spezifische MA“ ergänzen (wie in mass-booking), damit konsistent.

**Keine Änderungen** an Code in dieser Stellungnahme vorgenommen.
