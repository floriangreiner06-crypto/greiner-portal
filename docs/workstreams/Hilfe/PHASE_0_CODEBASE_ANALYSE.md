# Phase 0: Codebase-Analyse — Hilfe-Modul

**Erstellt:** 2026-02-24  
**Zweck:** Vor der Implementierung des Hilfe-Moduls die bestehende Projektstruktur, Module, Navigation und Auth dokumentieren.

---

## 1. Projektstruktur

### 1.1 Entry Point & Blueprints

- **App:** `app.py` — Flask-App, Konfiguration, Context-Processor für Navigation (`inject_navigation`) und Static-Version, Login/Logout, Dashboard/Start.
- **Blueprints** werden in `app.py` registriert (teils in try/except, optional geladen).

### 1.2 Routes

| Datei / Ort | Inhalt |
|-------------|--------|
| `app.py` | Direkte Routes: `/`, `/start`, `/dashboard`, `/login`, `/logout`, `/urlaubsplaner`, `/urlaubsplaner/v2`, `/urlaubsplaner/chef`, `/urlaubsplaner/admin`, `/admin/mitarbeiterverwaltung`, `/admin/organigramm`, `/mein-bereich`, `/test/ersatzwagen`, `/health`, `/debug/navigation`, … |
| `routes/admin_routes.py` | Admin-Bereich (admin_routes) |
| `routes/bankenspiegel_routes.py` | `/bankenspiegel/` |
| `routes/controlling_routes.py` | `/controlling/` (controlling_bp) |
| `routes/afa_routes.py` | `/controlling/` (afa_bp) |
| `routes/verkauf_routes.py` | `/verkauf/` (verkauf_bp) |
| `routes/provision_routes.py` | `/provision/` (provision_bp) |
| `routes/werkstatt_routes.py` | Werkstatt (werkstatt_routes) |
| `routes/whatsapp_routes.py` | `/whatsapp/` (whatsapp_bp) |
| `routes/marketing_routes.py` | Marketing (marketing_bp) |
| `routes/planung_routes.py` | Planung |
| `routes/gewinnplanung_v2_routes.py` | Planung V2 |
| `routes/aftersales/teile_routes.py` | Aftersales Teile (bp) |
| `routes/aftersales/serviceberater_routes.py` | Serviceberater (bp) |
| `routes/aftersales/garantie_routes.py` | Garantie (bp) |
| `routes/jahrespraemie_routes.py` | Jahresprämie (jahrespraemie_bp) |
| `celery_app/routes.py` | `/admin/celery/` (celery_bp) |

### 1.3 API-Layer (`api/`)

Über 40 Blueprints, u. a.:

- **Urlaub:** vacation_api, vacation_chef_api, vacation_admin_api, employee_management_api  
- **Finanzen:** bankenspiegel_api, controlling_api, finanzreporting_api, kontenmapping_api, afa_api, opos_api, zins_optimierung_api  
- **Verkauf:** verkauf_api, profitabilitaet_api, parts_api, gewinnplanung_v2_gw_api, provision_api, verkaeufer_zielplanung_api, budget_api, unternehmensplan_api, kst_ziele_api  
- **Werkstatt/Aftersales:** werkstatt_api, werkstatt_live_api, fahrzeuganlage_api, serviceberater_api, kundenzentrale_api, garantie_soap_api, garantie_auftraege_api, unfall_wissensbasis_api, unfall_rechnungspruefung_api, arbeitskarte_api, werkstatt_soap_api, mobis_teilebezug_api, reparaturpotenzial_api, ml_api, ai_api  
- **Teile/Lager:** teile_api, teile_status_bp, renner_penner_bp  
- **Organisation:** organization_api, admin_api  
- **Integration:** eautoseller_api, mail_api, leasys_api, whatsapp (über whatsapp_routes)  
- **Marketing:** marketing_potenzial_api  
- **Jahresprämie:** jahrespraemie_api  
- **Planung:** planung_bp (abteilungsleiter_planung_api), gudat_api, gudat_locosoft_sync_api, ersatzwagen_bp  

### 1.4 Templates

- **Struktur:** `templates/` mit Unterordnern: `admin/`, `aftersales/`, `sb/`, `controlling/`, `planung/`, `provision/`, `whatsapp/`, `jahrespraemie/`, `marketing/`, `components/`, `macros/`, `test/`.
- **Base:** `base.html` — Bootstrap 5, Bootstrap Icons (`bi`), Chart.js, eigenes `navbar.css`, Makro `macros/navigation.html` für DB-Navigation.
- **Anzahl:** ca. 150+ HTML-Dateien (inkl. Backups/Placeholder).

### 1.5 Static

- `static/css/` (u. a. navbar.css), `static/js/`, `static/images/` (z. B. greiner-logo.svg).
- Cache-Busting über `STATIC_VERSION` in `app.py` und `?v={{ STATIC_VERSION }}` in Templates.

### 1.6 Auth

- **Decorators:** `decorators/auth_decorators.py` — `login_required`, `role_required(roles)`, `permission_required(permission)`, `module_required(module)`, `admin_required`, `ajax_login_required`, `api_key_required`.
- **Auth-Manager:** `auth/auth_manager.py` — User-Klasse (has_role, can_access_feature, can_access_module), AuthManager, LDAP-Anbindung.
- **Rollen-Config:** `config/roles_config.py` — TITLE_TO_ROLE, FEATURE_ACCESS, PORTAL_ROLES_FOR_ADMIN.

---

## 2. Modul-Inventar (für Hilfe-Kategorien)

Liste der sichtbaren Module mit Haupt-Route(n), Template(s), Kurzbeschreibung und Zielgruppe. Reihenfolge orientiert sich an typischer Nutzung/Navigation.

| Modul | Haupt-Route(s) | Template(s) | Kurzbeschreibung | Zielgruppe / Feature |
|-------|----------------|------------|------------------|----------------------|
| **Dashboard / Start** | `/`, `/start`, `/dashboard` | dashboard.html | Startseite, rollenbasierte Weiterleitung | Alle (login_required) |
| **Urlaubsplaner** | `/urlaubsplaner`, `/urlaubsplaner/v2`, `/urlaubsplaner/chef`, `/urlaubsplaner/admin` | urlaubsplaner_v2.html, urlaubsplaner_chef.html, urlaubsplaner_admin.html | Urlaub beantragen, Genehmigung, Chef-Übersicht, Admin | urlaubsplaner [*]; Genehmiger: urlaub_genehmigen |
| **Mitarbeiterverwaltung** | `/admin/mitarbeiterverwaltung` | admin/mitarbeiterverwaltung.html | Digitale Personalakte, Vertrag, Arbeitszeit, Urlaubseinstellungen | admin, buchhaltung |
| **Organigramm** | `/admin/organigramm` | organigramm.html | Vertretungsregeln, Abwesenheitsgrenzen | admin, buchhaltung |
| **Bankenspiegel** | `/bankenspiegel/` (Routes) | bankenspiegel_*.html | Konten, Transaktionen, Zeitverlauf | bankenspiegel |
| **Controlling** | `/controlling/` | controlling/*.html (BWA, TEK, KST, Finanzreporting, AfA, OPOS, Kundenzentrale, Unternehmensplan) | BWA, TEK, KST-Ziele, AfA, OPOS, Cube, Stundensatz | controlling, opos, etc. |
| **Verkauf** | `/verkauf/` | verkauf_*.html | Auftragseingang, Profitabilität, Auslieferung, eAutoSeller, Budget, GW-Dashboard, Leasys | auftragseingang, verkauf_dashboard, fahrzeuge, … |
| **Verkäufer-Zielplanung** | (eigener Navi-Punkt) | verkauf_zielplanung.html, verkauf_zielplanung_detail.html | Zielplanung Kalenderjahr, NW/GW | (Feature aus Navi) |
| **Provision** | `/provision/` | provision/*.html | Provisionsmodul, Meine Übersicht, Config (Admin) | (Feature aus Navi) |
| **Werkstatt** | Werkstatt-Routes | aftersales/*.html, sb/*.html | Stempeluhr, Live, Aufträge, Kapazität, Fahrzeuganlage, Renner/Penner, Teile-Status, Reparaturpotenzial, ML, Unfall | aftersales, fahrzeuganlage, werkstatt_live, teilebestellungen, … |
| **Serviceberater / Mein Bereich** | `/mein-bereich`, `/sb/mein-bereich`, `/aftersales/` | sb/mein_bereich.html, sb/*.html, aftersales/*.html | Persönlicher Bereich, Werkstatt-Übersicht, Stempeluhr, Teile, Garantie | sb_dashboard, service_leitung, serviceberater |
| **Garantie** | `/aftersales/garantie/` | aftersales/garantie_*.html | Garantie-Aufträge, Handbücher, Live-Dashboard | aftersales |
| **Teile / Lager** | Aftersales-Teile-Routes | aftersales/teilebestellungen.html, aftersales/renner_penner.html | Bestellungen, Renner/Penner | teilebestellungen, lager |
| **WhatsApp** | `/whatsapp/` | whatsapp/*.html | Verkauf-Chat, Teile-Nachrichten, Kontakte | whatsapp_verkauf, whatsapp_teile |
| **Fahrzeuganlage** | (Navi) | fahrzeuganlage.html | Fahrzeugschein-OCR, Anlage | fahrzeuganlage |
| **Planung** | Planung-Routes | planung/*.html | Abteilungsleiter-Planung, Gewinnplanung V2, Stundensatz, Freigabe, Gesamtplanung | (Planung-Features) |
| **KST-Ziele** | (API + ggf. Navi) | controlling/kst_ziele.html | Kostenstellen-Ziele | controlling |
| **OPOS** | `/controlling/opos` | controlling/opos.html | Offene Posten | opos |
| **Jahresprämie** | `/jahrespraemie/` | jahrespraemie/*.html | Jahresprämie, Berechnung, Kulanz | (Jahresprämie-Feature) |
| **Marketing Potenzial** | `/marketing/potenzial` | marketing/potenzial.html | Predictive Scoring | marketing_potenzial |
| **Admin** | `/admin/` (admin_routes) | admin/*.html | Rechte, Celery, User-Dashboard-Config, Mitarbeiterverwaltung, Organigramm, Provision-Config, ServiceBox-Zugang | admin |
| **Einkaufsfinanzierung / Zinsen** | (unter Controlling/Finanzen) | einkaufsfinanzierung.html, zinsen_analyse.html | Zinsen, Leasys | zinsen, einkaufsfinanzierung |
| **Ersatzwagen** | (API + Test-UI) | test/ersatzwagen_kalender.html | Ersatzwagen-Kalender (PoC) | (je nach Feature) |

Hinweis: Nicht jedes Modul hat einen eigenen Top-Level-Navi-Punkt; viele hängen unter Controlling, Verkauf, Service oder Admin. Die **Hilfe-Kategorien** können sich an diesen Modulnamen/Funktionen orientieren (z. B. „Urlaubsplaner“, „Controlling & BWA“, „Verkauf“, „Werkstatt & Service“, „Admin & Organisation“).

---

## 3. Navigation & UI

### 3.1 DB-Navigation

- **Aktivierung:** `USE_DB_NAVIGATION=true` (config/.env oder Umgebungsvariable). In Produktion aktiv.
- **Quelle:** Tabelle `navigation_items` (PostgreSQL). Struktur: id, parent_id, label, url, icon, order_index, requires_feature, role_restriction, is_dropdown, is_header, is_divider, active, category.
- **Laden:** `api/navigation_utils.py` → `get_navigation_for_user()`. Lädt alle aktiven Items, filtert in Python nach `current_user.can_access_feature(requires_feature)` und `role_restriction`, baut Baum (parent_id → children). Top-Level-Dropdowns ohne sichtbare Kinder werden ausgeblendet. Ergebnis wird pro Request in `flask.g` gecacht.
- **Rendering:** `templates/base.html` nutzt `navigation_items`; wenn gesetzt, wird `macros/navigation.html` → `render_navigation_item()` für jedes Top-Level-Item aufgerufen. Unterstützt: Top-Level-Link, Top-Level-Dropdown, Sub-Dropdown (dropdown-submenu), Header, Divider.

### 3.2 Icons & Layout

- **Bootstrap 5** (CDN 5.3.0), **Bootstrap Icons** (`bi bi-*`). Kein FontAwesome in base.html.
- Navbar: `navbar-dark bg-primary`, sticky-top. Logo + „DRIVE“, dann Nav-Links/Dropdowns.
- Sub-Dropdowns: Custom-CSS in base.html (dropdown-submenu, Chevron rechts).

### 3.3 Modals / Toasts

- Bootstrap 5 Modal/Toast-Patterns werden in vielen Templates genutzt (z. B. Urlaubsplaner, Admin). Kein globales Hilfe-Widget bisher.

### 3.4 Wo „Hilfe“ einhängen?

- **Option A:** Eigenes **Top-Level-Item** in `navigation_items`: parent_id = NULL, label = „Hilfe“, url = `/hilfe`, icon z. B. `bi-question-circle`, order_index am Ende (z. B. 99). requires_feature = NULL → für alle sichtbar.
- **Option B:** Unter einem bestehenden Menüpunkt (z. B. „Admin“ oder ein neues „?“-Dropdown). Dafür parent_id = ID des betreffenden Eintrags setzen.

**Empfehlung:** Top-Level „Hilfe“ (Option A), damit es von allen Rollen ohne Klick in ein anderes Menü erreichbar ist.

---

## 4. Auth-System

### 4.1 User-Objekt (`auth/auth_manager.py`)

- **User (Flask-Login):** id, username, display_name, email, ou, roles, permissions, title, portal_role, allowed_features, company, standort, standort_subsidiaries.
- **Methoden:** has_role(role), has_permission(permission), can_access_feature(feature), can_access_module(module).  
- `can_access_feature` prüft gegen `allowed_features` (aus config/roles_config.py + DB-Overrides).

### 4.2 Rollen (portal_role)

- Aus `config/roles_config.py`: TITLE_TO_ROLE mappt LDAP-Titel auf Rollen (admin, buchhaltung, verkauf_leitung, verkauf, werkstatt_leitung, werkstatt, service_leitung, serviceberater, service, disposition, lager, marketing, mitarbeiter, …).
- PORTAL_ROLES_FOR_ADMIN listet alle Rollen für die Rechteverwaltung.

### 4.3 Feature-Zugriff (FEATURE_ACCESS)

- Features u. a.: bankenspiegel, controlling, zinsen, einkaufsfinanzierung, fahrzeugfinanzierungen, auftragseingang, auslieferungen, verkauf_dashboard, fahrzeuge, stellantis_bestand, urlaubsplaner, urlaub_genehmigen, teilebestellungen, aftersales, fahrzeuganlage, sb_dashboard, werkstatt_live, whatsapp_teile, whatsapp_verkauf, opos, marketing_potenzial, admin, qa_dashboard, …
- Jedes Feature hat eine Liste erlaubter Rollen (oder `['*']` für alle).

### 4.4 Decorator-Pattern für Hilfe

- **Öffentliche Hilfe-Seiten (lesen):** `@login_required` reicht (alle eingeloggten User).
- **Admin-Bereich (Artikel pflegen):** `@admin_required` oder `@role_required('admin')` aus `decorators/auth_decorators.py`. Bei API: gleicher Decorator; bei JSON-Request gibt admin_required 401/403 als JSON zurück.
- **Artikel sichtbar nach Rolle:** Optional Feld `sichtbar_fuer_rollen` in hilfe_artikel; Backend filtert bei Abfrage nach `current_user.portal_role` oder `can_access_feature`.

---

## 5. Zusammenfassung für das Hilfe-Modul

- **Blueprint-Pattern:** Neues `api/hilfe_api.py` (url_prefix='/api/hilfe') und `routes/hilfe_routes.py` (z. B. url_prefix='/hilfe'), in app.py registrieren.
- **DB:** PostgreSQL drive_portal; Tabellen hilfe_kategorien, hilfe_artikel (mit tsvector für Suche), hilfe_feedback; optional hilfe_chat_verlauf. Kein SQLite, keine FTS5.
- **Navigation:** Neuer Eintrag in `navigation_items` per Migration (parent_id = NULL für Top-Level „Hilfe“, requires_feature = NULL damit alle ihn sehen).
- **Auth:** Lese-Seiten @login_required; Admin-Seiten @admin_required. Optional Artikelfilter nach Rolle in API.
- **UI:** Bootstrap 5 + Bootstrap Icons, konsistent mit base.html und macros/navigation.html. Kontext für Hilfe-Widget später über data-hilfe-modul oder request.path ableitbar.
- **Starter-Artikel:** Pro Modul aus der Tabelle oben 3–5 Artikel anlegen; Kategorien z. B. „Allgemein & Erste Schritte“, „Urlaubsplaner“, „Controlling & Finanzen“, „Verkauf“, „Werkstatt & Service“, „Admin & Organisation“, „WhatsApp & Integration“.

Damit ist Phase 0 abgeschlossen. Nächster Schritt: Phase 1 (Migrationen, API, Routes) gemäß ENTWURF_HILFE_MODUL.md.
