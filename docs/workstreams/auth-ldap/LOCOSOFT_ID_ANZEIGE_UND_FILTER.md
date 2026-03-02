# Locosoft-ID: Wo anzeigen und warum Filter „nur eigene“ greift

## Wo sehe ich die Locosoft-ID?

- **Rechteverwaltung** (Admin → Rechteverwaltung) → Tab „Feature-Zugriff“ → bei einem User auf **Stift (Mitarbeiter bearbeiten)** klicken → im Modal **„Mitarbeiter bearbeiten“** steht oben:
  - **Locosoft-ID (für Filter „nur eigene“):** *Wert* oder **nicht gesetzt**
  - Es wird die ID aus `ldap_employee_mapping.locosoft_id` angezeigt (falls vorhanden, sonst `employees.locosoft_id`). Diese ID wird für Auftragseingang, Auslieferungen, OPOS und **Leistungsübersicht Werkstatt** genutzt, wenn die Rolle „nur eigene“ hat.
- **Mitarbeiterverwaltung** (Admin → Rechteverwaltung → Tab mit Iframe „Mitarbeiterverwaltung“, oder direkt Admin → Mitarbeiterverwaltung): Mitarbeiter auswählen → **Sync-Vorschau** → dort wird „Locosoft (ID: …)“ bzw. „Keine Locosoft-ID vorhanden“ angezeigt.

## Warum greift „nur eigene“ nicht?

Damit der Filter „nur eigene“ (z. B. Leistungsübersicht nur für den angemeldeten Mechaniker) greift, müssen **alle** erfüllt sein:

1. **Locosoft-ID gesetzt:** Für den eingeloggten User muss in `ldap_employee_mapping` ein Eintrag mit seiner `ldap_username` existieren und **`locosoft_id`** muss gesetzt sein (z. B. Mechaniker-Nr 5008). Prüfung: Rechteverwaltung → Stift beim User → „Locosoft-ID“ im Modal.
2. **Rolle mit Filter-Modus:** Die **Portal-Rolle** des Users (z. B. „werkstatt“) muss in der Rechteverwaltung unter „Filter-Verhalten für Listen“ für **Leistungsübersicht Werkstatt** auf **„Nur eigene (Filter nicht auflösbar)“** stehen.
3. **Neulogin:** Nach Änderung der Rolle oder des Mappings ggf. **aus- und wieder einloggen**, damit die Session die neue Rolle/Features nutzt.

## Locosoft-ID setzen

- **Über Sync:** Mitarbeiterverwaltung → Mitarbeiter öffnen → „Sync aus Locosoft“ (dann muss die Locosoft-ID bereits im Mapping oder in `employees` bekannt sein; LDAP/AD-Sync überträgt `employees.locosoft_id` ins Mapping).
- **Manuell (DB):**  
  `UPDATE ldap_employee_mapping SET locosoft_id = 5008 WHERE employee_id = <id>;`  
  Optional auch `employees.locosoft_id` setzen, damit es beim nächsten LDAP-Sync ins Mapping übernommen wird.

## Technisch

- Filter nutzt: `api/werkstatt_api._get_current_user_mechaniker_nr()` → liest `lem.locosoft_id` aus `ldap_employee_mapping` per `ldap_username` des aktuellen Users.
- Anzeige im Modal: `api/employee_management_api` GET `/api/employee-management/employee/<id>` liefert `mapping_locosoft_id` (aus `ldap_employee_mapping`).
