# Zentrale Konfiguration & Verwaltung (Admin) — Vorschlag

**Stand:** 2026-03-02  
**Auslöser:** Konten-Verwaltung soll unter Admin laufen; Prüfung, ob Konfig-/Verwaltungsseiten zentral darstellbar sind (z. B. wie http://drive/admin/provision-config).

---

## Was es heute schon gibt

Alle unter **/admin/** (Route in `routes/admin_routes.py`), Berechtigung in der Regel **nur Admin** (`@role_required(['admin'])`):

| URL | Beschreibung | Template |
|-----|--------------|----------|
| `/admin/rechte` | Rechteverwaltung (Rollen, Features, Reports, Navigation, Mitarbeiter, Urlaub) | `admin/rechte_verwaltung.html` |
| `/admin/celery/` | Task Manager (Celery) | (eigener Blueprint) |
| `/admin/provision-config` | Provisionsarten (SSOT Vergütung) | `admin/provision_config.html` |
| `/admin/servicebox-zugang` | ServiceBox (Stellantis) Passwort & Ablauf | `admin/servicebox_zugang.html` |
| `/admin/organigramm` | Organigramm (in app.py) | (Organigramm-App) |
| `/admin/meine-startseite` | Individuelle Startseite konfigurieren | `admin/user_dashboard_config.html` |
| `/admin/mitarbeiterverwaltung` | Mitarbeiterverwaltung (Personalakte etc.) | `admin/mitarbeiterverwaltung.html` |

**Navigation:** Im **Admin-Dropdown** (base.html Fallback und teils DB-Navigation) stehen u. a. Task Manager, Flower, Rechteverwaltung, Organigramm, Provisionsarten, Debug User. ServiceBox und Provisionsarten sind per Migration in der DB-Navigation. Es gibt **keine zentrale Übersichtsseite**, die alle Konfig-/Verwaltungsseiten bündelt.

---

## Vorschlag: Zentrale Seite „Konfiguration“

**Neue URL:** `/admin/konfiguration`

**Inhalt:** Eine **Hub-Seite** mit Karten oder Liste, die alle Konfigurations- und Verwaltungsseiten thematisch gruppiert verlinkt:

- **Finanzen & Controlling**
  - **Konten & Banken** → `/admin/konten-verwaltung` (neu, siehe KONTEN_VERWALTUNG_VORSCHLAG.md)
  - (später evtl. Kontenmapping, Stundensatz-Kalkulation, wenn verwaltbar)
- **Vergütung**
  - **Provisionsarten** → `/admin/provision-config`
- **Zugänge & Dienste**
  - **ServiceBox (Stellantis)** → `/admin/servicebox-zugang`
- **Organisation**
  - **Organigramm** → `/admin/organigramm`
  - **Startseiten** → `/admin/meine-startseite`
  - **Mitarbeiterverwaltung** → `/admin/mitarbeiterverwaltung`
- **System** (optional, oder im Dropdown belassen)
  - **Rechteverwaltung** → `/admin/rechte`
  - **Task Manager** → `/admin/celery/`

**Vorteile:**

- Ein Einstiegspunkt für „wo konfiguriere ich was?“ — besonders für neue Admins.
- Neue Konfig-Seiten (z. B. Konten & Banken) werden nur hier und ggf. im Admin-Dropdown ergänzt, das Dropdown bleibt übersichtlich.
- Einheitliches Muster: Konfiguration = unter `/admin/` + Eintrag auf der Hub-Seite.

**Berechtigung:** Wie bisher nur für Admins (oder wie Rechteverwaltung). Route z. B. `@role_required(['admin'])`.

---

## Konten-Verwaltung: Einordnung

- **URL:** `/admin/konten-verwaltung` (statt unter `/bankenspiegel/...`) — damit alle Konfig-Seiten unter `/admin/` gebündelt sind, analog zu provision-config und servicebox-zugang.
- **Verlinkung:**
  - Auf der **zentralen Konfigurationsseite** unter „Finanzen & Controlling“.
  - Im **Admin-Dropdown** als weiterer Punkt (z. B. „Konten & Banken“ unter Organisation oder eigener Gruppe „Konfiguration“).
  - Optional auf der **Bankenspiegel-Kontenübersicht** (`/bankenspiegel/konten`) ein Button „Konten verwalten“ für admin/buchhaltung → führt zu `/admin/konten-verwaltung`.

---

## Technische Umsetzung (Kurzplan)

1. **Route** in `routes/admin_routes.py`:  
   `@admin_routes.route('/admin/konfiguration')` → `render_template('admin/konfiguration.html')`.
2. **Template** `templates/admin/konfiguration.html`:  
   Überschrift „Konfiguration & Verwaltung“, Karten/Liste mit Gruppen (Finanzen, Vergütung, Zugänge, Organisation) und Links zu den bestehenden Seiten + „Konten & Banken“ (neu).
3. **Navigation:**  
   - Im Admin-Dropdown (base.html und/oder DB) einen Eintrag **„Konfiguration“** (Link auf `/admin/konfiguration`) oben oder in einer Gruppe „Konfiguration“ einfügen.  
   - Optional: Unter „Konfiguration“ nur diesen einen Link; die Detail-Links (Provisionsarten, ServiceBox, Konten, …) sind dann vor allem auf der Hub-Seite.
4. **Konten-Verwaltung** wie in KONTEN_VERWALTUNG_VORSCHLAG.md umsetzen, URL `/admin/konten-verwaltung`, und auf der neuen Konfigurationsseite verlinken.

---

## Nächste Schritte

1. Entscheidung: Hub-Seite `/admin/konfiguration` so umsetzen? (Ja/Nein)
2. Wenn ja: Konfigurations-Template anlegen, Route registrieren, Admin-Dropdown um „Konfiguration“ ergänzen (Fallback + ggf. DB-Migration).
3. Konten-Verwaltung unter `/admin/konten-verwaltung` bauen und auf der Konfigurationsseite + im Dropdown verlinken.

Wenn der Hub zunächst weggelassen wird: Konten-Verwaltung trotzdem unter `/admin/konten-verwaltung` anlegen und nur im Admin-Dropdown (und auf der Bankenspiegel-Kontenseite) verlinken; Hub später nachziehen.
