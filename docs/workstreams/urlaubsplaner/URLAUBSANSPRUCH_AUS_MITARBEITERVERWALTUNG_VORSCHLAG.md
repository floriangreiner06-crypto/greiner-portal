# Urlaubsanspruch und fortlaufende Berechnung aus Mitarbeiterverwaltung

**Stand:** 2026-02-13  
**Ziel:** Urlaubsanspruch und fortlaufende Berechnung (Verbraucht, Geplant, Resturlaub) haben **eine Quelle** – die **Mitarbeiterverwaltung** (Admin). Der Urlaubsplaner liest dieselben Daten.

---

## 1. Ausgangslage

- **Urlaubsplaner** berechnet Anspruch und Resturlaub über die View `v_vacation_balance_{year}`, die auf die Tabelle **`vacation_entitlements`** zugreift (pro Mitarbeiter und Jahr: `total_days`, `carried_over`, `added_manually`).
- **Mitarbeiterverwaltung** (Tab „Moduldaten → Urlaubsplaner“) zeigt aktuell einen **fest eingetragenen Wert „27,0 Tage“** (disabled) und keine fortlaufende Berechnung (Verbraucht/Geplant/Resturlaub).
- Die **API** `employee_management_api` liefert pro Mitarbeiter bereits **`vacation_entitlements`** (alle Jahre); es fehlt die Anzeige und Bearbeitung im Frontend sowie die Anzeige der Salden (fortlaufende Berechnung).

**Gewünscht:**  
Urlaubsanspruch und fortlaufende Berechnung kommen **aus dem Mitarbeiterverwaltungsmodul**: dort Anzeige + Pflege, Urlaubsplaner nutzt weiter dieselben Daten (keine Duplikation).

---

## 2. Single Source of Truth

| Was | Tabelle / View | Wo gepflegt | Wo gelesen |
|-----|----------------|-------------|------------|
| Urlaubsanspruch (Jahr) | `vacation_entitlements` (total_days, carried_over, added_manually) | Mitarbeiterverwaltung (künftig) + ggf. Urlaubsplaner-Admin | Urlaubsplaner (View), Mitarbeiterverwaltung (Anzeige) |
| Verbraucht / Geplant / Resturlaub | `v_vacation_balance_{year}` (berechnet aus vacation_entitlements + vacation_bookings) | – (Ergebnis von Buchungen) | Urlaubsplaner, Mitarbeiterverwaltung (Anzeige) |

- **Pflege:** Urlaubsanspruch (und Übertrag/Korrektur) soll primär in der **Mitarbeiterverwaltung** bearbeitet werden können.
- **Berechnung:** Die „fortlaufende Berechnung“ (Verbraucht, Geplant, Resturlaub) bleibt in der View-Logik; beide Module lesen daraus.

---

## 3. Vorschlag Umsetzung

### 3.1 Mitarbeiterverwaltung – Anzeige

- **Jahr-Auswahl** im Tab „Moduldaten → Urlaubsplaner“ (z. B. Dropdown 2025, 2026, 2027; Default: aktuelles Jahr).
- **Urlaubsanspruch (Anzeige):**  
  Aus `employee.vacation_entitlements` für das gewählte Jahr:  
  **Anspruch = total_days + (carried_over || 0) + (added_manually || 0)**  
  Kein fester „27,0 Tage“-Text mehr; Anzeige z. B. „27,0 Tage“ oder „30,0 Tage“ je nach Datensatz.
- **Fortlaufende Berechnung (Anzeige):**  
  Pro gewähltem Jahr anzeigen:
  - **Verbraucht** (genehmigte Urlaubstage)
  - **Geplant** (pending Urlaubstage)
  - **Resturlaub**  
  Quelle: dieselbe View wie im Urlaubsplaner (`v_vacation_balance_{year}`).

**Technik:**

- **Option A:** Beim Laden des Mitarbeiters optionales Query-Parameter `balance_year` an `GET /api/employee-management/employee/<id>`; Backend ergänzt ein Objekt `vacation_balance: { anspruch, verbraucht, geplant, resturlaub }` für dieses Jahr (Abfrage der View).
- **Option B:** Eigenen Endpoint `GET /api/vacation/balance/<employee_id>?year=2026` (oder in employee_management) liefern, der genau eine Zeile aus `v_vacation_balance_{year}` zurückgibt. Frontend ruft nach Jahr-Wechsel auf.

Empfehlung: **Option A** (ein Request, konsistent mit bestehender Detail-Antwort).

### 3.2 Mitarbeiterverwaltung – Bearbeitung

- Wenn **„Urlaubsanpassungen bearbeiten“** aktiviert ist (Checkbox im Tab):
  - Felder sichtbar: **Grundanspruch (Tage)**, **Übertrag**, **Korrektur** (oder wie in `vacation_entitlements`: total_days, carried_over, added_manually).
  - Speichern: Aufruf des bestehenden Endpoints **`POST /api/vacation/admin/update-entitlement`** mit `employee_id`, `year`, `anspruch` (= total_days), `uebertrag` (= carried_over), `korrektur` (= added_manually).
- Berechtigung: Nur für Admins / Vacation-Admin (wie bereits bei `update-entitlement`).

### 3.3 Urlaubsplaner

- **Keine fachliche Änderung:** Urlaubsplaner liest weiter aus `v_vacation_balance_*` bzw. `vacation_entitlements`. Sobald in der Mitarbeiterverwaltung Werte gepflegt werden, sind sie im Urlaubsplaner automatisch sichtbar.

---

## 4. Referenzen zu Usertest / Bugs & Fixes

Aus den Projekt-Dokumenten (Usertest, TAG 198 u. a.):

- **Resturlaub:** Nur **Urlaub** (vacation_type_id = 1) zählt für Verbraucht/Geplant/Resturlaub; Krankheit, ZA, Schulung nicht – bereits in `v_vacation_balance_*` umgesetzt (`docs/URLAUBSPLANER_RESTURLAUB_FIX_TAG198.md`).
- **Jahreswechsel:** `vacation_entitlements` für neues Jahr werden automatisch angelegt (z. B. 27 Tage Standard) – `vacation_year_utils.ensure_vacation_year_setup_simple`, `docs/URLAUBSPLANER_JAHRESWECHSEL_FIX_TAG198.md`.
- **Urlaubstage vom Anspruch abziehen:** Erledigt über die View (verbraucht = approved Urlaub).
- Weitere offene Punkte (E-Mail HR, Darstellung): siehe `docs/URLAUBSPLANER_OFFENE_PUNKTE_LOESUNG_TAG198.md`, `docs/URLAUBSPLANER_USERTEST2_ZUSAMMENFASSUNG_TAG198.md`.

Die **Quelldokumente** aus dem Usertest (Word) liegen unter **F:\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\urlaubsplaner** (bzw. Windows-Sync); im Repo auf dem Server existieren die oben genannten abgeleiteten Docs unter `docs/`.

---

## 5. Konkrete Schritte (Reihenfolge)

1. **Backend (employee_management_api):**  
   Beim `GET /api/employee-management/employee/<id>` optionalen Parameter `balance_year` (Default: aktuelles Jahr) auswerten und ein Objekt **`vacation_balance`** für dieses Jahr aus `v_vacation_balance_{year}` (eine Zeile für diesen employee_id) ermitteln und in der JSON-Antwort mitgeben.

2. **Frontend (mitarbeiterverwaltung.html):**  
   - Im Tab „Moduldaten → Urlaubsplaner“:
     - **Jahr-Dropdown** einführen (z. B. 2025–2027), beim Wechsel Mitarbeiter mit `balance_year=<jahr>` neu laden (oder nur Balance nachladen, wenn Option B).
     - **Urlaubsanspruch:** Wert aus `employee.vacation_entitlements` für gewähltes Jahr (total_days + carried_over + added_manually) anzeigen, **nicht** den festen Text „27,0 Tage“.
     - **Fortlaufende Berechnung:** Anzeige von Verbraucht, Geplant, Resturlaub aus `employee.vacation_balance` (sofern Backend liefert).
     - **„Urlaubsanpassungen bearbeiten“:** Bei Aktivierung Felder für Grundanspruch, Übertrag, Korrektur anzeigen; Speichern über `POST /api/vacation/admin/update-entitlement`.

3. **Berechtigung:** Sicherstellen, dass nur Admins / Vacation-Admin die Anpassung speichern können (wie bei `update-entitlement`).

4. **Optional:** Link „Im Urlaubsplaner anzeigen“ (zweiter Button neben Urlaubsanspruch) auf die Urlaubsplaner-Ansicht für diesen Mitarbeiter/ dieses Jahr setzen.

---

## 6. Kurzfassung

- **Eine Quelle:** `vacation_entitlements` + View `v_vacation_balance_{year}`.
- **Mitarbeiterverwaltung:** Anzeige Urlaubsanspruch + Verbraucht/Geplant/Resturlaub pro Jahr; Bearbeitung Anspruch/Übertrag/Korrektur über bestehenden `update-entitlement`-Endpoint.
- **Urlaubsplaner:** Unverändert; nutzt bereits dieselben Daten.
- **Dokus/Wünsche/Bugs:** Siehe `docs/` (URLAUBSPLANER_*.md, MITARBEITERVERWALTUNG_*.md); Word-Quellen auf F:\…\docs\workstreams\urlaubsplaner.

Wenn du möchtest, können wir als Nächstes mit Schritt 1 (Backend `vacation_balance` in Employee-Detail) und Schritt 2 (Frontend Anzeige + Jahr + Bearbeitung) starten.
