# Konkrete Umsetzung: Provision aktiv / deaktiv pro Mitarbeiter

**Zweck:** VKL (z. B. Anton Süß) und GF erhalten keine Provisionsabrechnung. Über ein Mitarbeiter-Flag „Provision aktiv“ steuern, wer in der Abrechnung berücksichtigt wird.

**Stand:** 2026-02-17 (Festlegung); Umsetzung abgeschlossen (Migration, API, UI, Provision-Filter + Meldung).

---

## 1. Datenmodell

### 1.1 Tabelle `employees`

- **Neue Spalte:** `provision_aktiv`  
  - Typ: `BOOLEAN`  
  - Default: `true` (Rückwärtskompatibilität: alle bisherigen MA gelten als „erhält Provision“)  
  - Bedeutung: `true` = wird bei Provisionsabrechnung berücksichtigt (Vorlauf-Liste, „Meine Provision“); `false` = wird ausgenommen (z. B. VKL, GF).

### 1.2 Migration (PostgreSQL)

- Datei: `migrations/add_employees_provision_aktiv.sql`
- Inhalt: `ALTER TABLE employees ADD COLUMN IF NOT EXISTS provision_aktiv BOOLEAN DEFAULT true;`
- Optional: `COMMENT ON COLUMN employees.provision_aktiv IS 'false = von Provisionsabrechnung ausgenommen (z.B. VKL, GF)';`

---

## 2. Mitarbeiterverwaltung (UI + API)

### 2.1 API

- **GET** `/api/employee-management/employee/<id>`  
  - In der zurückgegebenen `employee`-Struktur Feld **`provision_aktiv`** aufnehmen (boolean, Default true wenn NULL).
- **PUT** `/api/employee-management/employee/<id>`  
  - Body darf **`provision_aktiv`** enthalten (boolean).  
  - Bei Vorhandensein: `UPDATE employees SET provision_aktiv = %s WHERE id = %s` (ggf. in der bestehenden Update-Logik mit anderen Feldern).

### 2.2 UI (Mitarbeiterverwaltung)

- **Ort:** Tab **„Mitarbeiterdaten“** (Vertrag) oder eigener kleiner Abschnitt **„Vergütung / Provision“** im gleichen Tab.  
  - Empfehlung: Direkt unter „Nach Austritt deaktivieren“ einen weiteren Abschnitt **„Provision“** mit einer Checkbox.
- **Label:** z. B. **„Erhält Provision (VKB-Abrechnung)“**  
  - Checkbox: angehakt = `provision_aktiv = true`, nicht angehakt = `provision_aktiv = false`.
- **Hilfetext (optional):** „Wenn deaktiviert, erscheint die Person nicht in der Vorlauf-Liste und erhält keine Provisionsabrechnung (z. B. Verkaufsleitung, Geschäftsführung).“
- Beim **Speichern** des Mitarbeiters muss der Wert der Checkbox als `provision_aktiv` im PUT-Body mitgeschickt werden (analog zu `deactivate_after_exit` / `aktiv`).

---

## 3. Provisionsmodul (Verhalten)

### 3.1 Dashboard „Verkäufer (Vorlauf erstellen)“

- **Aktuell:** Alle `salesman_number`, die im gewählten Monat Verkäufe haben, werden angezeigt (aus `sales` + `employees` für Namen).
- **Neu:** Nur noch Verkäufer anzeigen, für die ein Mitarbeiter mit `locosoft_id = salesman_number` existiert und **`provision_aktiv = true`** ist.
  - **Ausnahme:** Wenn zu einer VKB-Nummer **kein** Eintrag in `employees` existiert (LEFT JOIN liefert NULL), weiterhin anzeigen (Rückwärtskompatibilität / Sync-Lücke).
- **Technisch:** In `api/provision_service.py`, Funktion `get_dashboard_daten()`, die SQL-Abfrage für `verkaeufer` anpassen:
  - Statt nur `LEFT JOIN employees e ON e.locosoft_id = s.salesman_number`  
  - Filter: `AND (e.id IS NULL OR e.provision_aktiv = true)`  
  - Damit: Unbekannte VKB weiter sichtbar; bekannte MA mit `provision_aktiv = false` (Anton Süß, GF) erscheinen nicht in der Liste.

### 3.2 „Meine Provision“ (Verkäufer-Ansicht)

- **Aktuell:** Wenn `locosoft_id` des eingeloggten Users gesetzt ist, wird die Live-Berechnung angezeigt.
- **Neu:** Wenn der zugehörige Mitarbeiter **`provision_aktiv = false`** hat:
  - Keine Berechnung anzeigen (oder nur Summen 0).
  - Stattdessen eine **klare Meldung** anzeigen, z. B.:  
    **„Für Sie wird keine Provisionsabrechnung durchgeführt (z. B. Verkaufsleitung / Geschäftsführung).“**
- **Technisch:** In `api/provision_api.py` (Live-Preview) bzw. im Aufruf von `berechne_live_provision`:
  - Vor der Berechnung: Mitarbeiter über `employees` (per `locosoft_id` des Users) laden und `provision_aktiv` prüfen.
  - Wenn `provision_aktiv = false`: Response mit `success: true`, aber z. B. `provision_deaktiviert: true` und `message: "..."`; Frontend zeigt dann die Meldung statt der Tabelle.

---

## 4. Zusammenfassung der Änderungen (Checkliste)

| Nr | Bereich | Änderung |
|----|---------|----------|
| 1 | DB | Migration: `employees.provision_aktiv` (BOOLEAN DEFAULT true) |
| 2 | API | GET employee: `provision_aktiv` im Response |
| 3 | API | PUT employee: `provision_aktiv` akzeptieren und speichern |
| 4 | UI | Mitarbeiterverwaltung: Checkbox „Erhält Provision (VKB-Abrechnung)“ (Vertrag/Provision), Speichern mitsenden |
| 5 | Provision | `get_dashboard_daten()`: Verkäuferliste nur mit `e.id IS NULL OR e.provision_aktiv = true` |
| 6 | Provision | Live-Preview / „Meine Provision“: bei `provision_aktiv = false` feste Meldung statt Berechnung |

---

## 5. Nach der Umsetzung (manuell)

- Für **Anton Süß** (Verkaufsleitung) und **GF** (z. B. Florian) in der Mitarbeiterverwaltung den Mitarbeiter öffnen und **„Erhält Provision“** deaktivieren (Checkbox abwählen).  
- Danach erscheinen sie nicht mehr in „Verkäufer (Vorlauf erstellen)“ und sehen unter „Meine Provision“ die Hinweis-Meldung.

---

## 6. Optional (später)

- In der **Rechteverwaltung** pro User einen schreibgeschützten Hinweis anzeigen: „Provision (Abrechnung): aktiv/inaktiv“ – Wert aus dem gemappten Mitarbeiter (`provision_aktiv`), ohne die SSOT in die Rechteverwaltung zu verlagern.
