# OPOS-Modul: Rollen- und Rechtekonzept (Anbindung an DRIVE)

**Stand:** 2026-02-19  
**Workstream:** Controlling

## 1. Bestehendes Rollen- und Rechtekonzept in DRIVE (Kurzüberblick)

### 1.1 Rollen (Portal-Rollen)

- **Quelle:** LDAP-Titel → Portal-Rolle über `config/roles_config.py` (`TITLE_TO_ROLE`, `get_role_from_title()`).
- **User-Objekt:** `current_user.portal_role` (z. B. `admin`, `buchhaltung`, `verkauf_leitung`, `verkauf`, `werkstatt_leitung`, …).
- **Admin-Override:** Nutzer mit DB-Rolle `admin` (user_roles) erhalten `portal_role = 'admin'` und Zugriff auf alle Features.

### 1.2 Feature-Zugriff

- **Konfiguration:** `config/roles_config.py` → `FEATURE_ACCESS`: pro Feature eine Liste erlaubter Rollen (oder `['*']` = alle).
- **Prüfung:** `current_user.can_access_feature('featurename')` (User.allowed_features wird beim Login aus Portal-Rolle abgeleitet).
- **Navigation:** DB-Tabelle `navigation_items` mit `requires_feature` und optional `role_restriction` (kommasep. Rollen). Nur Einträge, auf die der User Feature- und Rollen-Zugriff hat, werden angezeigt.
- **Fallback-Navigation:** `templates/base.html` zeigt z. B. Controlling nur, wenn `current_user.can_access_feature('bankenspiegel')` oder andere Controlling-Features.

### 1.3 Relevante Features für Controlling

| Feature           | Rollen (Auszug)                    |
|-------------------|------------------------------------|
| `controlling`     | admin, buchhaltung                  |
| `bankenspiegel`   | admin, buchhaltung                  |
| `zinsen`          | admin, buchhaltung, verkauf_leitung, disposition |

Controlling-Routen nutzen aktuell nur `@login_required`; die sichtbare Navigation wird über Feature-Zugriff gesteuert. Ein direkter Aufruf von `/controlling/tek` ist ohne Feature-Check möglich – bei Bedarf kann pro Route zusätzlich `can_access_feature('controlling')` geprüft werden (wie bei AfA in base.html: nur mit `controlling` oder `admin`).

### 1.4 User ↔ Mitarbeiter (für „nur eigene Posten“)

- **Tabelle:** `ldap_employee_mapping`: `ldap_username` → `employee_id` (Portal), `locosoft_id` (Locosoft-Mitarbeiternummer).
- **Nutzung:** z. B. Urlaubsplaner (`api/vacation_api.get_employee_from_session()`): aktueller User → ldap_username → employee_id, locosoft_id.
- **OPOS-Daten:** Die SQL-Abfrage liefert `verkaufer_nr` (= Locosoft-Mitarbeiternummer: aus `sales.salesman_number` oder FIBU `employee_number`). Filter „nur meine Posten“ = `verkaufer_nr = current_user's locosoft_id`.

---

## 2. Vorschlag: OPOS-Anbindung an Rollen und Rechte

### 2.1 Neues Feature: `opos`

- **Eintrag in `FEATURE_ACCESS`** (in `config/roles_config.py` und ggf. in DB, falls feature_access dort verwaltet wird):

```python
'opos': ['admin', 'buchhaltung', 'verkauf_leitung', 'verkauf'],
```

- **Bedeutung:** Admin und Buchhaltung sehen das Modul immer; Verkaufsleitung und Verkäufer ebenfalls (Verkäufer mit Einschränkung auf eigene Posten, siehe unten).

### 2.2 Sichtbarkeit der Menüpunkte

- **Navigation:** Eintrag „Offene Posten (OPOS)“ unter Controlling mit `requires_feature = 'opos'` (und optional `role_restriction` leer oder z. B. `admin,buchhaltung,verkauf_leitung,verkauf`).
- Damit erscheint der Link nur für Nutzer mit Feature `opos` (und ggf. passender Rolle).

### 2.3 Zugriff auf die Route/API

- **Route:** z. B. `/controlling/opos` und API z. B. `GET /api/controlling/opos` mit:
  - `@login_required`
  - Zusätzlich: `if not current_user.can_access_feature('opos'): redirect/403` (oder Flash + Redirect), damit kein direkter URL-Zugriff ohne Berechtigung.

### 2.4 Daten-Sichtbarkeit (wer sieht welche Posten?)

| Rolle              | Sichtbarkeit                                      | Umsetzung |
|--------------------|---------------------------------------------------|-----------|
| **admin**          | Alle offenen Posten (kein Filter nach Verkäufer)  | Kein Filter auf `verkaufer_nr`. |
| **buchhaltung**    | Alle offenen Posten                               | Kein Filter auf `verkaufer_nr`. |
| **verkauf_leitung**| Alle offenen Posten (Überblick Verkauf)           | Kein Filter auf `verkaufer_nr`. |
| **verkauf**        | Nur Posten, die **dem eigenen Verkäufer** zugeordnet sind | Filter: `verkaufer_nr = locosoft_id` des aktuellen Users. |

- **Ermittlung „eigene Verkäufer-Nummer“:**  
  - Über `ldap_employee_mapping`: `current_user.username` → `locosoft_id`.  
  - Wenn kein Mapping existiert: Verkäufer sieht **leere Liste** (oder eine Meldung „Kein Mitarbeiter-Mapping vorhanden“), kein Fallback auf „alle Posten“.

- **Filter in der API:**  
  - Wenn `portal_role == 'verkauf'` und nicht (admin oder buchhaltung oder verkauf_leitung):  
    - Zusätzlicher WHERE-Filter in der OPOS-Abfrage: `mv.verkaufer_nr = :current_user_locosoft_id` (Parameter aus ldap_employee_mapping).  
  - Optional: Filter „nur Fahrzeugverkauf“ / „nur mit Verkäufer“ etc. wie im Konzept weiter anwendbar; der Rollen-Filter schränkt die **Grundmenge** ein.

### 2.5 Filter-UI (Verkäufer-Dropdown)

- **Admin / Buchhaltung / Verkaufsleitung:** Verkäufer-Dropdown wie geplant (alle Verkäufer mit offenen Posten oder aus employees).
- **Verkäufer (Rolle `verkauf`):** Verkäufer-Dropdown ausblenden oder auf einen festen Eintrag „Meine Posten“ setzen (keine Auswahl anderer Verkäufer), da die API ohnehin nur eigene Posten liefert.

---

## 3. Kurz-Checkliste Implementierung

1. **Feature:** In `config/roles_config.py` bei `FEATURE_ACCESS`: `'opos': ['admin', 'buchhaltung', 'verkauf_leitung', 'verkauf']` (und ggf. DB-Feature-Tabelle pflegen, falls verwendet).
2. **Navigation:** Eintrag „Offene Posten (OPOS)“ unter Controlling mit `requires_feature = 'opos'`.
3. **Route `/controlling/opos`:** `@login_required` + Prüfung `current_user.can_access_feature('opos')`; bei Fehlen → Redirect/403.
4. **API `/api/controlling/opos`:**  
   - `current_user.can_access_feature('opos')` prüfen.  
   - Wenn Rolle = Verkäufer (und nicht admin/buchhaltung/verkauf_leitung): `locosoft_id` aus `ldap_employee_mapping` für `current_user.username` holen und OPOS-Query auf `verkaufer_nr = locosoft_id` einschränken.  
   - Sonst: alle Posten (optional mit Filter-Parametern Verkäufer, Zeitraum, …).
5. **Hilfsfunktion:** z. B. in `api/opos_api.py` oder `api/controlling_data.py`: `get_current_user_locosoft_id()` (über ldap_employee_mapping), für Verkäufer-Filter nutzen.
6. **Frontend:** Verkäufer-Dropdown nur anzeigen, wenn User nicht ausschließlich „nur eigene Posten“ sieht (z. B. nicht bei Rolle `verkauf` mit erzwungenem Eigenfilter).

---

## 4. Optionale Verschärfung (Route-Ebene)

Falls gewünscht, können alle Controlling-Routen einheitlich abgesichert werden (nicht nur Navigation verstecken):

- Blueprint `controlling_bp`: `@controlling_bp.before_request` mit Prüfung, ob User mindestens eines der Features `controlling`, `bankenspiegel`, `opos`, … hat; sonst Redirect/403.  
- Für OPOS reicht die eigene Route-Prüfung `can_access_feature('opos')` wie unter 3. und 4.

---

**Fazit:** Das bestehende Konzept (Portal-Rollen, `FEATURE_ACCESS`, `can_access_feature`, `ldap_employee_mapping`) wird um ein Feature `opos` und eine rollenabhängige Datenfilterung (Verkäufer = nur eigene Posten über `locosoft_id`) ergänzt. Navigation, Route und API werden konsistent daran angebunden.
