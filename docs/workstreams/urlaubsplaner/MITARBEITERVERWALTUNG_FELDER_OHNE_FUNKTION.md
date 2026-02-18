# Mitarbeiterverwaltung – Felder ohne Funktion

**Stand:** 2026-02-13  
**Geprüft:** `templates/admin/mitarbeiterverwaltung.html` + `collectFormData()` + API-Anbindung

---

## Kurzüberblick

Die meisten Bereiche sind **mit Funktion**: Deckblatt (inkl. Sync), Adressdaten, Vertrag, Arbeitszeitmodelle (Add/Edit/Delete), Ausnahmen, Zeiten ohne Urlaub, Moduldaten Urlaubsplaner (Einstellungen + Urlaubsanspruch-Dropdown).  
Nachfolgend nur die **Felder/Bereiche, die noch ohne echte Funktion** sind.

---

## 1. Deckblatt

| Feld | ID | Status | Anmerkung |
|------|-----|--------|-----------|
| **Gruppe** | `deckblatt_group` | ❌ Ohne Funktion | Wird mit `value=""` gerendert, **nie aus API befüllt**; ist **nicht in collectFormData()** und wird beim Speichern nicht mitgeschickt. Sollte entweder aus Stammdaten (z. B. Locosoft `grp_code` / Abteilung) befüllt und ggf. gespeichert werden oder als reine Anzeige gekennzeichnet werden. |
| **Letzter Login** | (kein id, disabled) | ❌ Ohne Funktion | Immer „Nicht verfügbar“, **kein Backend-Anschluss**. Könnte später aus Session/Auth-Log ermittelt werden. |

**Reine Anzeige (bewusst nicht editierbar):**  
Betriebszugehörigkeit, Alter – berechnet aus Eintritt/Geburtstag, kein Speicherfeld.

---

## 2. Adressdaten

Alle erfassten Felder (Straße, Land, PLZ, Ort, Telefon privat/Firma, Personal-Nr., E-Mail etc.) sind in **collectFormData()** und werden per PUT gespeichert.  
**Keine** Felder ohne Funktion.  
(Falls in der DB noch `private_fax` / `company_fax` existieren, sind sie im Template nicht angebunden – optional ergänzbar.)

---

## 3. Mitarbeiterdaten → Vertrag

Alle Vertragsfelder (Firma, Abteilung, Eintritt, Beschäftigung, Probezeit, Befristung, Kündigungsfristen, Land, Bundesland, „Nach Austritt deaktivieren“ etc.) sind in **collectFormData()** und werden per PUT übernommen. **„Nach Austritt deaktivieren“** (Stand nach Mail-Anfrage): Beim Setzen des Hakens wird zusätzlich **aktiv = false** gesetzt; der Mitarbeiter erscheint dann nicht mehr im Urlaubsplaner (View/API filtern nach aktiv = true). In der Mitarbeiterverwaltung werden alle MA inkl. inaktive angezeigt (mit „(inaktiv)“), damit der Haken gesetzt/entfernt werden kann.

**Automatisierung Locosoft:** Wenn beim **Locosoft-Sync** ein Austrittsdatum (termination_date/leave_date) übernommen wird und dieses Datum **in der Vergangenheit** liegt, setzt der Sync automatisch **aktiv = false** und **deactivate_after_exit = true**. So erscheinen ausgetretene MA nach dem nächsten Sync nicht mehr im Urlaubsplaner, ohne dass der Haken manuell gesetzt werden muss. Zusätzlich: Hat ein MA bereits ein Austrittsdatum in der Vergangenheit in der DB, aber ist noch aktiv, wird er beim nächsten Sync ebenfalls automatisch deaktiviert. Implementierung: `api/employee_sync_service.py` (sync_employee_from_locosoft).  
**Keine** Felder ohne Funktion.

---

## 4. Mitarbeiterdaten → Arbeitszeitmodell / Ausnahmen / Zeiten ohne Urlaub

Add/Edit/Delete sind umgesetzt (Modals + API).  
**Keine** Felder ohne Funktion.

---

## 5. Moduldaten → Urlaubsplaner

- **Urlaubseinstellungen** (Im Planer anzeigen, Geburtstag, Max. Übertrag, Urlaubslänge, Eintragungsfreigabe etc.): werden in **collectVacationSettingsData()** gelesen und per **PUT vacation-settings** gespeichert (auch beim allgemeinen „Speichern“).
- **Urlaubsanspruch:** Jahr-Dropdown + Tage-Dropdown (inkl. „Andere“) mit **„Urlaubsanspruch speichern“** → **POST /api/vacation/admin/update-entitlement**.

**Keine** Felder ohne Funktion mehr.

---

## 6. Sonstiges

- **Terminkonten** (`employee_appointment_accounts`): In der aktuellen Oberfläche **kein** eigener Bereich; laut Vorgehensweise optional später.  
- **„Neuer Mitarbeiter“**: Kein Button/Flow zum Anlegen eines neuen MA – aktuell ohne Funktion (gewollt oder später geplant).

---

## Zusammenfassung: Noch ohne Funktion

| Bereich | Feld / Element | Empfehlung |
|---------|----------------|------------|
| Deckblatt | **Gruppe** (`deckblatt_group`) | Aus API befüllen (z. B. aus `department_name` oder eigenem Feld `grp_code`), optional in collectFormData + Backend aufnehmen, wenn Gruppe abweichend von Abteilung gepflegt werden soll. |
| Deckblatt | **Letzter Login** | Entweder aus Auth/Session-Log anbinden oder als Platzhalter „—“ belassen. |

Alle übrigen sichtbaren Eingabefelder sind an Speichern bzw. CRUD angebunden.
