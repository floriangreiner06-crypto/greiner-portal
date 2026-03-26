# Code-Review: Urlaubsplaner & angeschlossene Module

**Stand:** 2026-02-25  
**Anlass:** Modul wirkt buggy; gezielte Prüfung aller Schnittstellen und verbundenen Module.

---

## 1. Erfasster Umfang

### Kern-APIs
- `api/vacation_api.py` – Anträge, Buchung, Balance, Validierung, my-team
- `api/vacation_admin_api.py` – Admin, Masseneingabe, Jahresend-Report, Exporte
- `api/vacation_chef_api.py` – Chef-Übersicht (nutzt vacation_api)
- `api/vacation_approver_service.py` – Genehmiger-Logik
- `api/vacation_calendar_service.py` – Outlook-Kalender
- `api/vacation_locosoft_service.py` – Locosoft-Abwesenheiten
- `api/vacation_year_utils.py` – Jahr-Setup, Views

### Schnittstellen / verbundene Module
- Mitarbeiterverwaltung: `api/employee_management_api.py`, `api/employee_sync_service.py` (Anspruch, show_in_planner)
- Auth: `decorators/auth_decorators.py`, Genehmiger-Gruppen (LDAP)
- Routes: Urlaubsplaner-Routen in `routes/app.py`
- Templates: `urlaubsplaner*.html`, `admin/mitarbeiterverwaltung.html`

### Referenz-Docs
- `docs/workstreams/urlaubsplaner/CONTEXT.md`
- `docs/workstreams/urlaubsplaner/ANALYSE_RESTURLAUB_FEHLERQUELLEN.md`

---

## 2. Kritische Befunde (Bug-Risiko)

### 2.1 Resturlaub in Admin-Report/Export ≠ Anzeige im Planer

**Ort:** `api/vacation_admin_api.py` – `report_monthly()` und `report_monthly_export()`

**Problem:**  
Der monatliche Report (JSON + CSV) liest **nur** die View `v_vacation_balance_{year}` und nutzt **weder** Locosoft **noch** `_compute_rest_display()`.  
Im Planer gilt: Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub).

**Folge:**  
- Export kann **höheren** Rest zeigen als die Anzeige im Urlaubsplaner (wenn in Locosoft schon Urlaub gebucht ist).
- Nutzer sehen z. B. im Planer „16 Rest“, im Export „20 Rest“ → Verwirrung und Vertrauensverlust.

**Empfehlung:**  
- Entweder: In `vacation_admin_api` für jeden Mitarbeiter Locosoft-Urlaub holen und `_compute_rest_display(anspruch, resturlaub_view, loco_urlaub)` aufrufen (wie in `/balance`), **oder**
- Report explizit kennzeichnen: „Resturlaub nur Portal (ohne Locosoft-Abgleich)“ und in CONTEXT.md dokumentieren.

---

### 2.2 Locosoft: Connection-Leak bei Fehlern

**Ort:** `api/vacation_locosoft_service.py` – `get_absences_for_employee()`, `get_absences_for_employees()`

**Problem:**  
Bei Exception wird `return {...}` ausgeführt, **ohne** `conn.close()`. Die Locosoft-Verbindung bleibt offen.

**Folge:**  
Bei wiederholten Locosoft-Fehlern (Netzwerk, Timeout, DB-Fehler) können Verbindungen aufgebraucht werden.

**Empfehlung:**  
`try/except/finally` nutzen und `conn.close()` im `finally` aufrufen, oder Context Manager für Locosoft-Connection verwenden (analog zu `db_session()`).

---

### 2.3 Validierung: Fehler verschluckt → 0 Rest

**Ort:** `api/vacation_api.py` – `_get_available_rest_days_for_validation()`

**Problem:**  
Bei jeder Exception (z. B. View existiert nicht, DB-Fehler) wird `return 0.0, None` zurückgegeben und nur `print(...)` ausgegeben.

**Folge:**  
- Wenn z. B. das Jahr-Setup fehlschlägt oder die View fehlt, kann **jede** Buchung mit „Nicht genug Resturlaub! Verfügbar: 0 Tage“ abgelehnt werden – auch bei eigentlich ausreichend Rest.
- Umgekehrt: Wenn durch einen Bug `available_days` fälschlich hoch ist, könnte zu viel gebucht werden.

**Empfehlung:**  
- Logging mit `logging.getLogger(__name__).exception(...)` statt `print`, damit Fehler in Logs sichtbar sind.
- Optional: Bei Fehlern in der Rest-Berechnung **nicht** pauschal 0 zurückgeben, sondern Fehler an den Aufrufer durchreichen (z. B. 500 mit Hinweis „Resturlaub konnte nicht ermittelt werden“), damit nicht still „0 verfügbar“ angenommen wird.

---

### 2.4 Buch-Batch: Jahr aus erstem Datum

**Ort:** `api/vacation_api.py` – `book_vacation_batch()`: `booking_year = int(dates[0][:4])`

**Problem:**  
Wenn `dates` mehrere Jahre umfasst (z. B. 30.12.2025 + 02.01.2026), wird nur 2025 zur Resturlaub-Validierung verwendet. Resturlaub für 2026 wird nicht geprüft.

**Empfehlung:**  
- Entweder: Batch auf ein Kalenderjahr beschränken (alle Daten müssen dasselbe Jahr haben) und mit Fehlermeldung ablehnen, **oder**
- Pro Jahr die angefragten Tage summieren und für jedes Jahr `_get_available_rest_days_for_validation` aufrufen und prüfen.

---

## 3. Mittlere Befunde (Konsistenz / Wartbarkeit)

### 3.1 Rest-Formel nur teilweise zentral

**Stand:**  
- `_compute_rest_display()` wird in `vacation_api` in `/balance`, `/my-balance`, `/my-team` und in der Buchungsvalidierung genutzt → **gut**.
- **vacation_admin_api** (Report/Export) nutzt sie **nicht** → siehe 2.1.

**Empfehlung:**  
Alle Stellen, die „Resturlaub“ ausgeben (Anzeige oder Export), sollten dieselbe Logik nutzen (eine Funktion + optional Locosoft-Aufruf).

---

### 3.2 employee_data / locosoft_id bei Buchung

**Ort:** `vacation_api.py` – `book_vacation()` und `book_vacation_batch()` nutzen `(employee_data or {}).get('locosoft_id')` bzw. `(target_employee_data or {}).get('locosoft_id')`.

**Risiko:**  
Wenn `employee_data`/`target_employee_data` aus einer anderen Quelle kommt und `locosoft_id` fehlt, wird Locosoft-Urlaub = 0 angenommen. Rest kann dann **höher** erscheinen als in der Team-Liste (wo ggf. Locosoft geladen wurde).  
Konsistenz prüfen: Wird für die gebuchte Person immer dieselbe Employee-Datenquelle (inkl. locosoft_id) verwendet wie in `/balance` und `/my-team`?

---

### 3.3 Fehlerbehandlung Genehmiger

**Ort:** `vacation_api.py` – `get_my_balance()`: `get_approver_summary` in try/except; bei Fehler Default-`approver_info`.

**Bewertung:**  
Gut, verhindert 500 bei Genehmiger-Fehlern. Sicherstellen, dass im Frontend bei fehlgeschlagenem Approver-Load trotzdem Balance und Kalender nutzbar bleiben (laut CONTEXT bereits so umgesetzt).

---

## 4. Positive Punkte

- **SSOT Rest-Anzeige:** `_compute_rest_display()` existiert und wird in Balance, my-balance, my-team und Validierung genutzt.
- **Jahr-Validierung:** `_validate_vacation_year()` mit Whitelist verhindert SQL-Injection bei dynamischem View-Namen.
- **Vertretungsregel / Abwesenheitsgrenzen:** Zentrale Prüfungen in Buchung und Batch.
- **Strukturelle Entkopplung:** Genehmiger-Fehler brechen my-balance nicht mit 500.

---

## 5. Empfohlene Reihenfolge der Behebung

| Priorität | Thema | Aufwand | Datei(en) |
|-----------|--------|---------|-----------|
| 1 | Admin-Report/Export: Rest = gleiche Logik wie Planer (Locosoft + _compute_rest_display) | Mittel | vacation_admin_api.py |
| 2 | Locosoft: Connection im finally schließen (oder Context Manager) | Gering | vacation_locosoft_service.py |
| 3 | _get_available_rest_days: Logging + ggf. Fehler nach oben statt still 0 | Gering | vacation_api.py |
| 4 | Buch-Batch: Klarheit bei mehreren Jahren (ablehnen oder pro Jahr prüfen) | Gering | vacation_api.py |

---

## 6. Kurz-Checkliste für spätere Änderungen

- [ ] Jede neue Stelle, die „Resturlaub“ anzeigt oder exportiert, nutzt `_compute_rest_display()` und ggf. Locosoft.
- [ ] Locosoft-Zugriffe: Verbindung immer schließen (finally/Context Manager).
- [ ] Validierungsfehler nicht still als „0 verfügbar“ behandeln; loggen und ggf. explizit Fehlerantwort.
- [ ] Batch-Buchungen über Jahresgrenze: Verhalten dokumentieren oder einschränken.

Dieses Dokument kann bei Bugfixes und Erweiterungen als Referenz genutzt und bei Umsetzung der Punkte aktualisiert werden.
