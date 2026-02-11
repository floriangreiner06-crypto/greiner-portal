# Projekt-Inventur GREINER DRIVE – Workstream-Migration

**Erstellt:** 11.02.2026  
**Zweck:** Vollständige Bestandsaufnahme für Workstream-Migration

---

## 1. Aktueller TAG-Stand und Wrap-Ups

**Neueste Wrap-Ups (nach Änderungsdatum):**
- docs/SESSION_WRAP_UP_TAG112.md
- docs/SESSION_WRAP_UP_TAG110.md
- docs/SESSION_WRAP_UP_TAG109.md
- docs/SESSION_WRAP_UP_TAG104.md
- docs/SESSION_WRAP_UP_TAG102.md

**Hinweis:** Letzter dokumentierter Wrap-Up in docs/ ist TAG 112. Git-Commits reichen bis TAG 215 – Session-Doku hinkt der Entwicklung hinterher.

---

## 2. API-Module

**Anzahl:** 82 Python-Dateien unter api/

**Auswahl:** abteilungsleiter_planung_api.py, abteilungsleiter_planung_data.py, admin_api.py, ai_api.py, arbeitskarte_api.py, bankenspiegel_api.py, budget_api.py, controlling_api.py, controlling_data.py, db_connection.py, db_utils.py, fahrzeug_data.py, fahrzeug_api.py, profitabilitaet_api.py, profitabilitaet_data.py, kalkulation_helpers.py, pdf_generator.py, vacation_api.py, vacation_admin_api.py, vacation_chef_api.py, verkauf_api.py, verkauf_data.py, werkstatt_api.py, werkstatt_data.py, werkstatt_live_api.py, whatsapp_api.py, teile_api.py, teile_data.py, teile_status_api.py, parts_api.py, leasys_api.py, organization_api.py, gudat_api.py, garantie_auftraege_api.py, ml_api.py, renner_penner_api.py, ersatzwagen_api.py, unternehmensplan_api.py, kst_ziele_api.py, jahrespraemie_api.py, finanzreporting_api.py, kontenmapping_api.py, gewinnplanung_v2_gw_api.py, stundensatz_kalkulation_api.py, eautoseller_api.py, mail_api.py, zins_optimierung_api.py, …

**Registrierte Blueprints (app.py):** vacation_api, chef_api, vacation_admin_api, employee_management_api, bankenspiegel_api, bankenspiegel_bp, verkauf_api, profitabilitaet_api, parts_api, admin_api, teile_api, zins_api, gewinnplanung_v2_gw_api, verkauf_bp, controlling_bp, werkstatt_routes, whatsapp_bp, controlling_api, finanzreporting_api, kontenmapping_api, jahrespraemie_api, celery_bp, teile_routes, serviceberater_routes, garantie_routes, admin_routes, arbeitskarte_bp, werkstatt_soap_bp, garantie_soap_api, garantie_auftraege_api, mobis_teilebezug_api, serviceberater_api, kundenzentrale_api, werkstatt_api, werkstatt_live_bp, gudat_locosoft_sync_bp, planung_bp, planung_routes, gewinnplanung_v2_routes, reparaturpotenzial_api, ml_api, ai_api, teile_status_bp, portal_name_survey_bp, renner_penner_bp, organization_api, ersatzwagen_bp, budget_bp, unternehmensplan_bp, kst_ziele_bp. Auskommentiert: qa_api, qa_routes.

---

## 3. Templates

**Anzahl:** 140 HTML-Dateien

**Bereiche:** admin/ (celery_tasks, mitarbeiterverwaltung, rechte_verwaltung, user_dashboard_config), aftersales/ (werkstatt_*, garantie_*, serviceberater, teilebestellungen, renner_penner, …), bankenspiegel_*, controlling/ (bwa, dashboard, finanzreporting_cube, kontenmapping, kst_ziele, tek_dashboard, …), jahrespraemie/, planung/, verkauf_* (auftragseingang, budget, profitabilitaet, …), urlaubsplaner*, sb/, whatsapp/, base.html, login, dashboard, organigramm, leasys_*, zinsen_analyse, zeiterfassung, werkstatt_intelligence, qa, test, macros, components.

---

## 4. Data-Module (api/*_data.py)

- api/abteilungsleiter_planung_data.py
- api/budget_data.py
- api/controlling_data.py
- api/fahrzeug_data.py
- api/gewinnplanung_v2_gw_data.py
- api/gudat_data.py
- api/profitabilitaet_data.py
- api/serviceberater_data.py
- api/teile_data.py
- api/unternehmensplan_data.py
- api/verkauf_data.py
- api/werkstatt_data.py

Ordner data_modules/ existiert nicht.

---

## 5. Celery Tasks (Namen)

benachrichtige_serviceberater_ueberschreitungen, servicebox_scraper, servicebox_matcher, servicebox_import, servicebox_master, import_mt940, import_hvb_pdf, import_santander, import_hyundai, scrape_hyundai, leasys_cache_refresh, umsatz_bereinigung, sync_employees, sync_locosoft_employees, sync_ad_departments, sync_sales, sync_stammdaten, locosoft_mirror, sync_teile, sync_charge_types, import_stellantis, import_teile, werkstatt_leistung, email_auftragseingang, email_werkstatt_tagesbericht, email_tek_daily, email_daily_logins, refresh_finanzreporting_cube, bwa_berechnung, db_backup, cleanup_backups, ml_retrain, update_penner_marktpreise, email_penner_weekly, sync_eautoseller_data, send_whatsapp_message

Beat-Schedule: u.a. MT940 8/12/17 Uhr, sync_employees 6:00, email_tek_daily 19:30, db_backup 3:00, servicebox mehrmals täglich, sync_teile alle 30 Min, sync_sales 7–18 Uhr, locosoft_mirror 19:00, bwa_berechnung 19:30.

---

## 6. Scripts und Tools

**scripts/:** Sehr viele Python-Dateien (analyse_*, check_*, test_*, update_*, send_daily_tek.py, tek_api_helper.py, scripts/mcp/server.py, scripts/mcp/start.sh, Unterordner analysis/, archive/, tests/, utils/).

**tools/:** analyse_locosoft_teile.py, gudat_*.py, locosoft_soap_client.py, tools/scrapers/ (Servicebox, Hyundai, Leasys, Repdoc, Schaeferbarthold, Dello, Stellantis, …).

---

## 7. Datenbanken

**PostgreSQL DRIVE Portal (Haupt-DB):** 127.0.0.1, drive_portal, drive_user. Laut CLAUDE.md 161 Tabellen (konten, transaktionen, banken, employees, vacation_*, fahrzeugfinanzierungen, users, budget_plan, …). Verbindung getestet: OK.

**SQLite (data/greiner_controlling.db):** Vorhanden, viele Tabellen (banken, konten, transaktionen, loco_*, vacation_*, employees, bwa_monatswerte, sales, werkstatt_leistung_daily, …). Hinweis: Haupt-DB ist seit TAG 135 PostgreSQL.

**PostgreSQL Locosoft (10.80.80.8):** Verbindung fehlgeschlagen (Passwort-Authentifizierung loco_auswertung_benutzer). .env/Netzwerk prüfen.

---

## 8. Git

**Branch:** feature/tag112-onwards (laut Status „ahead 35“)

**Letzte Commits (Auszug):** a3d7f66 fix(TEK) drei_monate_vorher, 6603036 TAG215 TEK E-Mail Stück/PDF, 916a0e7 TAG214 Hypovereinsbank, 9e4d8d4 TAG213 Kontenübersicht 071101, 76c9682 TAG213 Werkstatt LIVE Performance, d300ef0 TAG212 Garantieakte, e77fe2f TAG211 Stempelzeiten-Deduplizierung, 01f6586 TAG210 Task Historie, 0431a41 tag207 Task-Dashboard/ML/ServiceBox, eb3a8c5 TAG202 VIN/Zinsberechnung.

---

## 9. Systemd-Services

| Service         | Status        |
|-----------------|---------------|
| greiner-portal  | active        |
| celery-worker   | active        |
| celery-beat     | active        |
| flower          | inactive      |
| redis-server    | active        |
| metabase        | active        |

(Ein Eintrag: „nicht gefunden“ – ggf. anderer Unit-Name.)

---

## 10. Docs

**docs/ (maxdepth 2, *.md):** Viele ANALYSE_*, ANLEITUNG_*, BWA/TEK/Globalcube-Docs, DB/Stempelzeiten/Locosoft, Garantie, Metabase, mockups/, sessions/ (SESSION_WRAP_UP, TODO_FOR_CLAUDE), Implementierungspläne. Unterordner: archiv/, globalcube_analysis/, hyundai/, mockups/, sql/, stellantis/, claude/, DA_Screenshots/, reports/, status/, reklamationen/, sessions/.

---

## Kurzfassung für Workstream-Migration

- **Stand:** Branch feature/tag112-onwards, Commits bis TAG 215; letzter dokumentierter Wrap-Up TAG 112.
- **Backend:** 82 API-Dateien, Blueprints in app.py klar zugeordnet.
- **Frontend:** 140 Templates (Admin, Aftersales, Bankenspiegel, Controlling, Verkauf, Urlaub, Planung, WhatsApp, …).
- **Daten:** PostgreSQL drive_portal = Haupt-DB; SQLite-Datei existiert noch; Locosoft-PostgreSQL von dieser Umgebung nicht angebunden.
- **Jobs:** Celery Tasks/Beat für Controlling, Aftersales, Verkauf, E-Mails, Sync, Backup, ML, Renner-Penner, WhatsApp.
- **Scripts/Tools:** Viele Analyse-, Test-, Sync-Skripte und Scraper (Servicebox, Gudat, Locosoft, Hyundai, …).
- **Services:** Portal, Celery, Redis, Metabase aktiv; Flower inaktiv.
- **Doku:** Umfangreich unter docs/ (Analysen, Sessions, Mockups, SQL, Schemas).
