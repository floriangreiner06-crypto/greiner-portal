# Startseite mit Badges pro Rolle editierbar – Analyse und Vorschlag

**Stand:** 2026-02-28  
**Auslöser:** Badges auf der Startseite (/dashboard) pro Rolle konfigurierbar machen; bestehende Badges/Funktionen erfassen.

---

## 1. Aktueller Zustand

### 1.1 Wo liegt die Startseite?

- **URL:** `/dashboard` (Route in `app.py`, Template `templates/dashboard.html`).
- **Login-Weiterleitung:** Nach Login geht der User entweder auf eine **individuell konfigurierte Ziel-URL** (`user_dashboard_config.target_url`, z. B. /bankenspiegel, /verkauf/auftragseingang) oder auf die **rollenbasierte Weiterleitung** (z. B. Serviceberater → mein_bereich, sonst → `/dashboard`). Die **Badges** gibt es nur auf der Seite **/dashboard**; wer als Startseite z. B. /bankenspiegel hat, sieht die Badges gar nicht.

### 1.2 Welche „Badges“ gibt es heute? (fest im Template)

Alle Nutzer, die `/dashboard` sehen, bekommen **dieselben** Karten. Es gibt **keine** Konfiguration pro Rolle oder pro User.

#### A) KPI-Badges (oberer Bereich, mit Live-Wert + Link)

| # | Badge / Funktion           | Link/Ziel                          | Datenquelle (API)                                      | Sinnvolle Sichtbarkeit |
|---|----------------------------|------------------------------------|--------------------------------------------------------|-------------------------|
| 1 | Werkstatt heute (Leistungsgrad) | /werkstatt/stempeluhr              | `/api/werkstatt/live/leistung?zeitraum=heute`           | Werkstatt, Admin        |
| 2 | Werkstatt Auslastung       | /aftersales/kapazitaet             | `/api/werkstatt/live/kapazitaet`                       | Werkstatt, Admin        |
| 3 | Finanzierte Fahrzeuge      | /bankenspiegel/fahrzeugfinanzierungen | `/api/bankenspiegel/einkaufsfinanzierung`           | Bankenspiegel, Admin    |
| 4 | Offene Urlaubsanträge      | /urlaubsplaner/v2                  | `/api/vacation/pending-count`                          | Urlaub, Vorgesetzte, Admin |
| 5 | Aufträge / Auslieferungen (Monat) | /verkauf/auftragseingang        | `/api/verkauf/auftragseingang/summary`, `.../auslieferung/summary` | Verkauf, Admin          |

#### B) Modul-Karten („Ihre Module“, unterer Bereich)

| # | Modul             | Bedingung aktuell                          | Links (Beispiele)                                      |
|---|-------------------|---------------------------------------------|--------------------------------------------------------|
| 1 | Bankenspiegel     | `can_access_feature('bankenspiegel')`       | Dashboard, Kontenübersicht, Transaktionen              |
| 2 | Urlaubsplaner     | **immer** (kein Feature-Check)              | Mein Urlaub, ggf. Chef-Übersicht (admin/GL)           |
| 3 | Verkauf & Aufträge| `can_access_feature('auftragseingang')`     | Auftragseingang, Auslieferungen                        |
| 4 | After Sales       | `can_access_feature('teilebestellungen')`    | Kapazitätsplanung, Stempeluhr LIVE, Cockpit            |

**Fazit:** KPI-Badges sind **nicht** feature-gefiltert (alle 5 für alle). Modul-Karten sind **teilweise** feature-gefiltert (3 von 4); Urlaubsplaner immer sichtbar. **Keine** Rolle-/User-spezifische Konfiguration für „welche Badges anzeigen“.

### 1.3 Bestehende Konfiguration (TAG 190)

- **user_dashboard_config:** Pro User eine **Ziel-URL** als Startseite (redirect). Enthält außerdem `widget_config` und `layout_config` (JSONB), die derzeit für die **Badge-Auswahl auf /dashboard nicht genutzt** werden.
- **available_dashboards:** Liste der wählbaren **Ziel-Seiten** (z. B. „Allgemeines Dashboard“, „Bankenspiegel“, „Auftragseingang“); steuert nur die **Weiterleitung nach Login**, nicht die Badges auf /dashboard.

---

## 2. Anforderungen (aus Nutzerwunsch)

- **Pro Rolle** (oder pro User) die **Startseite mit Badges editierbar** machen.
- Konkret: Welche **KPI-Badges** und welche **Modul-Karten** auf `/dashboard` angezeigt werden, soll konfigurierbar sein (nicht mehr fest für alle).

---

## 3. Vorschlag: Zwei Ebenen

### Option A: Konfiguration **pro Rolle** (empfohlen für den Einstieg)

- **Neue Konfiguration:** z. B. Tabelle `dashboard_role_badges` (oder Erweiterung einer bestehenden Config):
  - `role_name` (z. B. admin, verkauf, werkstatt, mitarbeiter)
  - `badge_key` (eindeutiger Schlüssel pro Badge/Modul, s. u.)
  - `display_order` (Reihenfolge)
  - Optional: `visible` (boolean)
- **Badge-Katalog (feste IDs):** Alle möglichen Badges einmal definieren (Key, Label, Link, API, requires_feature-Mindestvoraussetzung). Die **Sichtbarkeit** pro Rolle ergibt sich aus:
  - Eintrag in `dashboard_role_badges` **oder**
  - Fallback: nur anzeigen, wenn User das zugehörige **Feature** hat (wie heute bei Modul-Karten).
- **Rechteverwaltung:** Neuer Bereich (z. B. Tab oder Unterpunkt) „Startseiten-Badges“: Rolle wählen → Liste aller Badges mit Checkbox „Anzeigen“ + Reihenfolge (Drag & Drop oder Nummer). Speichern schreibt in `dashboard_role_badges`.
- **Template /dashboard:** Statt fester HTML-Blöcke: Liste der für `current_user.portal_role` erlaubten Badges aus DB/Config laden und rendern (KPI-Badges + Modul-Karten einheitlich als „Badge-Liste“ mit Typ KPI vs. Modul).

**Vorteil:** Einmal pro Rolle konfigurieren, alle User der Rolle haben dieselbe Startseiten-Ansicht. Klar und wartbar.

### Option B: Konfiguration **pro User** (individuell)

- Pro User speichern, welche Badges er auf der Startseite sieht (z. B. in `user_dashboard_config.widget_config` oder neuer Tabelle).
- UI: z. B. unter „Meine Startseite“ oder in der Rechteverwaltung bei „User & Rollen“ pro User „Badges anpassen“.

**Vorteil:** Maximal flexibel. **Nachteil:** Mehr Aufwand für Admins und mehr Komplexität; sinnvoll erst nach Option A.

### Empfehlung

- **Zuerst Option A (pro Rolle)** umsetzen: Badge-Katalog definieren, `dashboard_role_badges` (oder äquivalent) pro Rolle befüllen, `/dashboard` danach rendern.
- **Optional später:** Option B ergänzen (User-Override: „Für diese Rolle standardmäßig X, für User Y zusätzlich Z ausblenden“).

---

## 4. Vorschlag: Badge-Katalog (welche Badges für welche Funktion)

Alle **bereits vorhandenen** Badges/Module aus dem aktuellen Dashboard werden mit einem festen **badge_key** versehen. Neue Badges (später) können ergänzt werden.

### 4.1 KPI-Badges (mit Wert + Link)

| badge_key        | Label (Kurz)                | Link | API (Datenquelle) | Empfohlene Rollen (Fallback) |
|------------------|-----------------------------|------|-------------------|-------------------------------|
| werkstatt_heute  | Werkstatt heute (Leistungsgrad) | /werkstatt/stempeluhr | /api/werkstatt/live/leistung | werkstatt, admin |
| werkstatt_auslastung | Werkstatt Auslastung   | /aftersales/kapazitaet | /api/werkstatt/live/kapazitaet | werkstatt, admin |
| fahrzeuge_finanziert | Finanzierte Fahrzeuge | /bankenspiegel/fahrzeugfinanzierungen | /api/bankenspiegel/einkaufsfinanzierung | bankenspiegel, admin |
| urlaub_offen     | Offene Urlaubsanträge    | /urlaubsplaner/v2 | /api/vacation/pending-count | urlaubsplaner, admin, Rollen mit Genehmiger |
| verkauf_auftraege_auslieferungen | Aufträge / Auslieferungen (Monat) | /verkauf/auftragseingang | /api/verkauf/auftragseingang/summary, auslieferung/summary | auftragseingang, admin |

### 4.2 Modul-Karten („Ihre Module“)

| badge_key     | Modul-Name      | Links (Beispiele) | Empfohlene Rollen (Feature) |
|---------------|-----------------|--------------------|-----------------------------|
| modul_bankenspiegel | Bankenspiegel | Dashboard, Konten, Transaktionen | bankenspiegel |
| modul_urlaubsplaner | Urlaubsplaner | Mein Urlaub, Chef-Übersicht (je nach Rolle) | urlaubsplaner (alle) |
| modul_verkauf | Verkauf & Aufträge | Auftragseingang, Auslieferungen | auftragseingang |
| modul_aftersales | After Sales | Kapazität, Stempeluhr, Cockpit | teilebestellungen |

Optional erweiterbar um z. B. **modul_controlling**, **modul_opos**, **modul_provision** usw., sobald gewünscht.

### 4.3 Weitere sinnvolle Badges (Features/Codeteile)

Aus Durchsicht der Features und APIs – **Kandidaten für spätere Erweiterung** (nicht im ersten Badge-Set zwingend, aber technisch möglich):

#### A) Weitere KPI-Badges (mit Wert + Link)

| badge_key | Label (Vorschlag) | Link | Datenquelle / Anmerkung | Feature |
|-----------|-------------------|------|--------------------------|---------|
| **opos_offen** | Offene Posten (OPOS) | /controlling/opos | GET `/api/controlling/opos` liefert `anzahl`, `gesamt_eur` (bei Default-Datum). Leichter Endpoint z. B. `/api/controlling/opos/summary?von=&bis=` nur Count/Summe wäre sinnvoll. | opos |
| **garantie_offen** | Offene Garantieaufträge | /aftersales/garantie/auftraege | GET `/api/garantie/auftraege/offen` liefert Liste; Count = Länge. KPI: „X offen“. | aftersales / garantie |
| **provision_offen** | Provisions-Läufe offen (VKL) | /provision/dashboard | `provision_service.get_dashboard_daten(monat)` enthält `offen` (Anzahl Läufe). API `/api/provision/dashboard?monat=YYYY-MM` bereits vorhanden. | provision_vkl |
| **provision_meine** | Meine Provision (Monat) | /provision/meine | Aktuell keine „ein Zeichen“-API; Live-Berechnung pro Verkäufer. Optional: kleines Endpoint „Meine Provision aktueller Monat – Summe“ für Badge-Wert. | provision |
| **qa_bugs_offen** | Offene QA-Bugs | /qa/bugs | GET `/api/qa/bugs?status=open` (oder Filter); Count für Badge. Für Rolle mit qa_dashboard. | qa_dashboard |
| **tek_heute** | TEK DB1 / Umsatz heute | /controlling (oder TEK-Seite) | `get_tek_data(heute)` ist aufwendig; optional schlanker Endpoint „TEK-Kennzahl heute“ (z. B. DB1 oder Umsatz) für Controlling-Rollen. | controlling |

#### B) Weitere Modul-Karten („Ihre Module“)

| badge_key | Modul-Name | Haupt-Link / Anmerkung | Feature |
|-----------|-------------|------------------------|---------|
| **modul_controlling** | Controlling | /controlling | TEK, BWA, Berichte. | controlling |
| **modul_opos** | Offene Posten (OPOS) | /controlling/opos | Bereits eigener Menüpunkt. | opos |
| **modul_provision** | Provision | /provision/meine bzw. /provision/dashboard | „Meine Provision“ / „Provisions-Dashboard (VKL)“. | provision / provision_vkl |
| **modul_verkaeufer_zielplanung** | Verkäufer-Zielplanung | /verkauf/zielplanung | Für VKL/GF. | verkaeufer_zielplanung |
| **modul_planung** | Planung / Budget | /verkauf/budget, Lieferforecast | Budget-Planung, Lieferforecast. | planung |
| **modul_whatsapp** | WhatsApp | /whatsapp/verkauf/chat (oder Übersicht) | Chat/Verkauf. | whatsapp_verkauf |
| **modul_eautoseller** | eAutoseller | /verkauf/eautoseller-bestand | Bestand. | eautoseller |
| **modul_qa** | QA / Bug-Übersicht | /qa/bugs | Für interne QA-Rolle. | qa_dashboard |
| **modul_garantie** | Garantieaufträge | /aftersales/garantie/auftraege | Offene Garantie. | aftersales |
| **modul_hilfe** | Hilfe | /hilfe | Zentrale Hilfe. | (alle) |

#### C) Kurz: Wo der Code liegt

- **OPOS:** `api/opos_api.py` – Liste mit `anzahl`, `gesamt_eur`; ggf. Lightweight-Summary-Endpoint für Badge.
- **Garantie offen:** `api/garantie_auftraege_api.py` – Route `/offen`, Rückgabe Liste → Count im Frontend oder neuer Endpoint `/offen/count`.
- **Provision:** `api/provision_service.get_dashboard_daten`, `api/provision_api.py` – `/dashboard`; „offen“ bereits vorhanden.
- **QA Bugs:** `api/qa_api.py` – `/api/qa/bugs`; Filter z. B. `status=open`; Count für Badge.
- **TEK:** `api/controlling_data.get_tek_data` – eher schwer; optional schlanker Endpoint nur für eine Kennzahl „heute“.

Für die **erste Umsetzung** (Abschnitt 7) reichen die 5 KPI- + 4 Modul-Badges. Die Tabelle hier dient als **Backlog** für spätere Badges und für die Badge-Registry (diese Keys bei Bedarf in `dashboard_badge_registry` nachziehen).

### 4.4 Abgleich mit Rechten

- Jeder Badge kann ein **Mindest-Feature** haben (z. B. `werkstatt_heute` → Feature `werkstatt_live`). Wenn der User das Feature nicht hat, wird der Badge **nicht** angezeigt (auch wenn für seine Rolle aktiviert).
- **Rollen-Konfiguration** legt fest: „Rolle Verkauf: nur diese Badges auf der Startseite“ (z. B. nur `verkauf_auftraege_auslieferungen`, `urlaub_offen`, `modul_urlaubsplaner`, `modul_verkauf`). Admin kann alle haben.

---

## 5. Technische Schritte (kurz, ohne Code)

1. **Badge-Registry:** Zentrale Liste (Config oder DB-Tabelle) aller `badge_key` mit Metadaten (Label, Link, API, optional requires_feature).
2. **Tabelle für Rollen-Konfiguration:** z. B. `dashboard_role_badges(role_name, badge_key, display_order)` (nur Einträge = sichtbar für Rolle). Oder eine JSON/JSONB-Spalte pro Rolle.
3. **API:** Endpoints zum Lesen/Schreiben der Badge-Konfiguration pro Rolle (Admin); Endpoint für das Frontend: „Badges für aktuelle User-Rolle“ (für Rendering /dashboard).
4. **Template dashboard.html:** Badges nicht mehr fest rendern, sondern aus der für `current_user.portal_role` gültigen Konfiguration + Badge-Registry generieren (KPI-Badges: weiterhin API-Call pro Typ; Modul-Karten: gleiche Logik wie heute, nur gefiltert nach erlaubten badge_keys).
5. **Rechteverwaltung UI:** Neuer Bereich „Startseiten-Badges“ (oder Tab): Rolle wählen, Checkboxen/Liste der verfügbaren Badges (aus Registry), Reihenfolge, Speichern.

---

## 6. Kurzfassung

- **Bestehende Badges:** 5 KPI-Badges (Werkstatt heute, Werkstatt Auslastung, Finanzierte Fahrzeuge, Urlaub offen, Aufträge/Auslieferungen) + 4 Modul-Karten (Bankenspiegel, Urlaubsplaner, Verkauf & Aufträge, After Sales). Alle KPI-Badges sind derzeit für alle sichtbar; 3 von 4 Modul-Karten sind feature-abhängig.
- **Lücke:** Keine Konfiguration „welche Badges für welche Rolle“; keine Editierbarkeit in der Rechteverwaltung.
- **Vorschlag:** Badge-Katalog mit festen Keys einführen, Sichtbarkeit und Reihenfolge **pro Rolle** in DB speichern, `/dashboard` danach dynamisch rendern und in der Rechteverwaltung „Startseiten-Badges“ pro Rolle editierbar machen. Optional später pro User verfeinern.

---

## 7. Implementierungsplan (Spezifikation)

### 7.1 Datenbank

**Tabelle `dashboard_badge_registry`** (Katalog aller Badges, einmalig befüllt)

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| badge_key | VARCHAR(80) PK | Eindeutiger Schlüssel (z. B. werkstatt_heute, modul_bankenspiegel) |
| badge_type | VARCHAR(20) | 'kpi' oder 'modul' |
| label | VARCHAR(200) | Anzeigename |
| url | VARCHAR(255) | Ziel-Link (bei KPI und Modul) |
| api_url | VARCHAR(255) NULL | Nur bei KPI: API für Wert (z. B. /api/werkstatt/live/leistung) |
| requires_feature | VARCHAR(100) NULL | Mindest-Feature; wenn User es nicht hat, Badge nie anzeigen |
| icon_class | VARCHAR(50) | Bootstrap-Icon (z. B. bi-wrench-adjustable) |
| display_order | INT | Standard-Reihenfolge im Katalog |

**Tabelle `dashboard_role_badges`** (welche Badges pro Rolle sichtbar + Reihenfolge)

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| role_name | VARCHAR(50) | Portal-Rolle (admin, verkauf, mitarbeiter, …) |
| badge_key | VARCHAR(80) | FK auf dashboard_badge_registry.badge_key |
| display_order | INT | Reihenfolge auf der Startseite (klein = oben/links) |
| PRIMARY KEY (role_name, badge_key) | | |

- **Fallback:** Wenn für eine Rolle **kein** Eintrag in `dashboard_role_badges` existiert, entweder: (a) alle Badges anzeigen, deren `requires_feature` der User hat, oder (b) einen Default-Satz pro Rolle in einer Migration anlegen. Empfehlung: (b) – Migration legt für jede Rolle einen sinnvollen Start-Satz an (z. B. Verkauf: nur verkauf_auftraege_auslieferungen, urlaub_offen, modul_* die passen).

### 7.2 Backend (Python)

- **Modul** `api/dashboard_badges.py` (oder in `api/admin_api.py` + Route in `app.py`):
  - **GET `/api/dashboard/badges`** (login_required): Liefert für aktuellen User (anhand `portal_role`) die Liste der erlaubten Badges aus `dashboard_role_badges` + `dashboard_badge_registry`, gefiltert nach `can_access_feature(requires_feature)`. Sortierung: `display_order` aus `dashboard_role_badges`. Rückgabe: Liste von Objekten `{ badge_key, badge_type, label, url, api_url, icon_class, display_order }`.
  - **GET `/api/admin/dashboard-badges/registry`** (admin_required): Gibt komplette Registry zurück (für Rechteverwaltung UI).
  - **GET `/api/admin/dashboard-badges/role/<role_name>`** (admin_required): Gibt konfigurierte Badges für Rolle zurück (role_name, badge_key, display_order).
  - **POST `/api/admin/dashboard-badges/role/<role_name>`** (admin_required): Body `{ "badges": [ { "badge_key": "...", "display_order": n }, ... ] }`. Schreibt `dashboard_role_badges` für diese Rolle (DELETE + INSERT).

- **Route `/dashboard`** (app.py): Wie bisher `render_template('dashboard.html', now=...)`. Zusätzlich: Liste der für User sichtbaren Badges laden (z. B. im View oder per Template-Include) und an Template übergeben: `dashboard_badges = get_badges_for_role(current_user.portal_role)`.

### 7.3 Frontend

- **Template `templates/dashboard.html`:**
  - Oberer Block „Info-Badges“: Statt fester fünf `<div class="col-lg-4">` eine Schleife über `dashboard_badges`, die `badge_type == 'kpi'` haben. Pro KPI-Badge: gleiches HTML wie heute (badge-icon, badge-content, badge-value mit id z. B. `badge-{{ badge_key }}`), Link aus `url`, Label aus `label`.
  - Unterer Block „Ihre Module“: Schleife über `dashboard_badges` mit `badge_type == 'modul'`. Pro Modul: Karte wie heute (icon, Titel, Links); Links können in Registry pro Modul hinterlegt sein oder weiterhin fest im Template je badge_key (z. B. if badge_key == 'modul_bankenspiegel' dann Links Bankenspiegel).
  - **JavaScript:** `loadDashboardData()` weiterhin pro KPI-Badge die bekannte API aufrufen; API-URL aus Datenattribut oder aus einer kleinen Map badge_key → api_url (aus Template übergeben). So bleiben die bestehenden APIs unverändert.

- **Rechteverwaltung** (`templates/admin/rechte_verwaltung.html`):
  - Neuer Tab oder neuer Bereich unter einem bestehenden Tab: **„Startseiten-Badges“**. Rolle-Dropdown (wie bei Feature-Zugriff). Liste aller Einträge aus `/api/admin/dashboard-badges/registry`; pro Zeile: Checkbox „Anzeigen“, Badge-Key, Label, Typ (KPI/Modul), optional Reihenfolge (Nummer oder Drag & Drop). „Speichern“ sendet POST an `/api/admin/dashboard-badges/role/<role>`. Optional: Voreinstellung „Aus Rolle übernehmen“ (z. B. von mitarbeiter) als Start für neue Rollen.

### 7.4 Migrationen

1. **Migration 1:** `CREATE TABLE dashboard_badge_registry (...); CREATE TABLE dashboard_role_badges (...);` + INSERT der 9 Badges (5 KPI + 4 Modul) in die Registry.
2. **Migration 2:** INSERT in `dashboard_role_badges` für jede Rolle einen sinnvollen Default (z. B. admin = alle; verkauf = nur verkauf_auftraege_auslieferungen, urlaub_offen, modul_urlaubsplaner, modul_verkauf; mitarbeiter = urlaub_offen, modul_urlaubsplaner; werkstatt = werkstatt_heute, werkstatt_auslastung, urlaub_offen, modul_aftersales; etc.).

### 7.5 Reihenfolge der Umsetzung

1. Migration 1 (Tabellen + Registry) ausführen.
2. Migration 2 (Default pro Rolle) ausführen.
3. Backend: `dashboard_badges.py` + GET `/api/dashboard/badges`, GET/POST Admin-Endpoints; in app.py Route `/dashboard` erweitern (Badges laden, an Template übergeben).
4. Template `dashboard.html` umbauen: Badges dynamisch aus Variable rendern; JS anpassen (Werte nur für gerenderte KPI-Badges laden).
5. Rechteverwaltung: Tab/Bereich „Startseiten-Badges“ + UI (Rolle wählen, Checkboxen, Speichern).
6. Optional: Modul-Karten-Links pro badge_key in Registry oder in Config hinterlegen, damit neue Module ohne Template-Änderung hinzukommen können.

---

**Ende der Planung.** Bei Umsetzung: zuerst DB, dann API, dann Template, dann Rechteverwaltung.
