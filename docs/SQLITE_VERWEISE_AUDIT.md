# Audit: SQLite-Verweise in Code und Scripts

**Stand:** 2026-02-25  
**Hinweis:** Nur Prüfung, keine Änderungen. Haupt-DB ist seit TAG 135 PostgreSQL (drive_portal). SQLite (data/greiner_controlling.db) ist Legacy.

---

## 1. API / Anwendungscode (Produktion)

### 1.1 Zentrale DB-Schicht (gewollt dual)

- **api/db_connection.py** – Unterstützt SQLite (DB_TYPE=sqlite) und PostgreSQL; Default postgresql. Bewusst so für Fallback/Dev.

### 1.2 SQLite-spezifischer Code

| Datei | Zeile(n) | Befund |
|-------|----------|--------|
| api/organization_api.py | 341 | _substitution_rules_table_exists: SQLite-Zweig nutzt sqlite_master. OK (nur im else). |
| api/organization_api.py | 901-905 | **Behoben 2026-02:** Prüfung auf information_schema.tables (PostgreSQL) umgestellt; SQLite wird in der Anwendung nicht mehr genutzt. |
| api/admin_api.py | 69-70 | GROUP_CONCAT vs STRING_AGG mit get_db_type(). OK. |
| api/vacation_admin_api.py | 106 | Nur Kommentar "2. SQLite Mitarbeiter" – Code nutzt db_session(). Veralteter Kommentar. |

### 1.3 get_db_type / Kompatibilität

Mehrere APIs nutzen get_db_type() == 'postgresql' oder convert_placeholders – korrekt.

---

## 2. Scripts mit direktem SQLite-Zugriff (nicht migriert)

Scripts mit `import sqlite3` und `sqlite3.connect(...)` – nutzen nicht api.db_connection (PostgreSQL).

### MCP / Scheduler

- scripts/mcp/server.py
- scheduler/routes.py (LOGS_DB)
- scheduler/job_manager.py (LOGS_DB)

### Migrationen

- scripts/migrations/refill_empty_tables.py
- scripts/migrations/verify_migration.py
- scripts/migrations/migrate_missing_tables.py
- scripts/migrations/migrate_sqlite_to_pg.py
- scripts/migrations/migrate_bankenspiegel_v2.py

### Sync / Import

- ~~scripts/sync/sync_ad_departments.py~~ → **2026-02-25 auf PostgreSQL umgestellt**
- ~~scripts/sync/sync_stammdaten.py~~, ~~scripts/sync/sync_fahrzeug_stammdaten.py~~ → **2026-02-25 auf PostgreSQL umgestellt**
- scripts/sync/sync_teile.py
- scripts/sync/sync_fibu_buchungen.py, sync_fibu_buchungen_v2.1 bis v2.4, v2.4_SIMPLE, v2.2, v2.3
- scripts/sync/sync_fibu_v2.4_FIXED bis v2.8
- scripts/sync/sync_ldap_employees.py
- scripts/sync_locosoft_employees.py
- scripts/imports/sync_charge_types.py, import_hvb_pdf.py, import_teile.py, import_teile_lieferscheine.py
- scripts/imports/import_hyundai.py, import_hyundai_data.py
- scripts/imports/import_sparkasse_*.py, import_hypovereinsbank_november.py
- scripts/imports/import_november_*.py, import_2025_*.py, import_complete_2025.py
- scripts/imports/import_stellantis_bestellungen.py, transaction_manager.py, sync_teile_locosoft.py
- scripts/import_kontoabrechnungen.py, import_final_test_tag39*.py
- ~~scripts/update_leasys_cache.py~~ → **2026-02-25 auf PostgreSQL umgestellt**; update_snapshots_mit_zinsen.py, update_limits.py, check_limits.py
- scripts/ldap_locosoft_matching_report.py

### Checks / Analyse / Maintenance

- scripts/checks/check_portal_urlaub_rechte.py, check_db_status.py, check_verkauf_duplikate.py
- scripts/analysis/forecast_endpoint_code.py, umsatz_bereinigung*.py, analyse_fibu_export.py
- scripts/analysis/check_november_status.py, analyse_kontenplan_systematisch.py
- scripts/analysis/analyse_bruttoertrag.py, analyse_modell_felder_v2.py, analyse_susa_vs_sqlite.py, analyse_guv_detailliert.py
- scripts/utils/export_db_schema.py
- scripts/maintenance/update_kontostand_historie.py, add_missing_columns.py, delete_bookings.py
- scripts/imports/fix_salden.py

### Setup / Urlaub / Tests / Archive

- scripts/setup/setup_vacation_calculator.py, setup_vacation_views.py, setup_vacation_entitlements_2025.py
- scripts/setup/setup_vacation_api.py, setup_urlaubsplaner_final.py, setup_urlaubsplaner_complete.py
- scripts/tests/test_all_parser_endsaldo_tag60.py, test_import_oktober_2025.py, test_vacation_api.py
- scripts/archive/liquiditaets_dashboard.py, vacation_api_new.py, bankenspiegel_api_root.py
- scripts/archive/root_cleanup_tag82/*.py, scripts/sync/archive/sync_sales_*backup*.py

### Hardcodierte Pfade zu greiner_controlling.db

- scripts/archive/liquiditaets_dashboard.py
- scripts/setup/setup_vacation_api.py
- scripts/update_limits.py, scripts/check_limits.py
- scripts/archive/bankenspiegel_api_root.py
- scripts/analysis/analyse_bruttoertrag.py, analyse_modell_felder_v2.py, analyse_susa_vs_sqlite.py
- scripts/tests/test_vacation_api.py

---

## 3. Zusammenfassung

**Kritisch (Produktion):** api/organization_api.py Zeile 901-905 – get_capacity_settings() nutzt sqlite_master ohne DB-Type-Check. Unter PostgreSQL schlägt der Endpoint fehl.

**Veraltet:** api/vacation_admin_api.py Zeile 106 – nur Kommentar "SQLite"; Code nutzt db_session().

**Scripts:** Sehr viele Scripts nutzen weiterhin direkt sqlite3.connect(). Bei aktiver Nutzung greifen sie nicht auf PostgreSQL zu. Entweder auf db_connection/db_session umstellen oder als Legacy kennzeichnen.

**Empfehlung (ohne Änderung):** organization_api.py: Tabellen-Prüfung für PostgreSQL (information_schema.tables) ergänzen. Scripts: Liste als Referenz; pro Script entscheiden – Migration auf PostgreSQL oder als Legacy/Archiv kennzeichnen.

---

## 4. Scripts: Funktionsweise und Berührung mit der App

### 4.1 Wo berühren Scripts die App?

Scripts berühren die App nur indirekt:

- **Aufrufer:** Celery (scheduler) startet viele Scripts per `subprocess.run(...)`. Es gibt **keine** direkten Imports von Scripts in api/ oder routes/.
- **Daten:** Die **App** liest/schreibt nur über `get_db()` / `db_session()` → **PostgreSQL**. Ein Script, das **nur** SQLite nutzt, schreibt also in eine **andere** Datenbank als die, die die App nutzt. Es „füttert“ die App nicht.

### 4.2 Von Celery aufgerufene Scripts – Übersicht

| Script (von Celery aufgerufen) | Nutzt SQLite? | Nutzt PostgreSQL? | Bewertung |
|--------------------------------|----------------|-------------------|-----------|
| scripts/sync/sync_ldap_employees_pg.py | nein | ja | Wird zuerst probiert; wenn vorhanden, wird dieses genutzt. |
| scripts/sync/sync_ldap_employees.py | ja | nein | Nur wenn _pg nicht existiert – schreibt dann in SQLite, nicht in App-DB. |
| scripts/sync/sync_employees.py | – | – | Bitte prüfen (nicht in SQLite-Audit). |
| scripts/sync/sync_ad_departments.py | nein | ja (db_session) | **Umgestellt 2026-02-25.** Schreibt in drive_portal. |
| scripts/sync/sync_sales.py | nein | ja (psycopg2) | Ziel ist drive_portal (PostgreSQL). Funktioniert für die App. |
| scripts/sync/sync_stammdaten.py | nein | ja (db_session) | **Umgestellt 2026-02-25.** Locosoft → drive_portal (HSN/TSN). |
| scripts/sync/sync_fahrzeug_stammdaten.py | nein | ja (db_session) | **Umgestellt 2026-02-25.** Wie sync_stammdaten. |
| scripts/sync/locosoft_mirror.py | nein | ja (psycopg2) | Ziel: drive_portal. Funktioniert für die App. |
| scripts/sync/sync_teile.py | ja (Quelle + Ziel) | Locosoft-PG | Liest/schreibt teile_lieferscheine in SQLite. Wenn Tabelle in PG liegt, veraltet. |
| scripts/imports/sync_teile_locosoft.py | ja | nein | SQLite. |
| scripts/imports/sync_charge_types.py | ja (Ziel) | Locosoft-PG (Quelle) | Doku: „Locosoft → SQLite“. Schreibt in SQLite → App sieht die Daten nicht. |
| scripts/imports/import_teile.py | ja | nein | SQLite. |
| scripts/imports/import_teile_lieferscheine.py | ja | nein | SQLite. |
| scripts/imports/import_mt940.py | nein | ja (get_db) | Nutzt api.db_connection → PostgreSQL. Funktioniert für die App. |
| scripts/imports/import_all_bank_pdfs.py | nein | ja (get_db) | Wie import_mt940. |
| scripts/imports/import_stellantis.py | – | – | Bitte prüfen (Celery ruft import_stellantis auf, Liste hat import_stellantis_bestellungen). |
| scripts/update_leasys_cache.py | nein | ja (db_session) | **Umgestellt 2026-02-25.** Schreibt in drive_portal. |
| scripts/analysis/umsatz_bereinigung_production.py | ja | nein | SQLite. Schreibt in Legacy-DB. |
| scripts/send_daily_auftragseingang.py | nein | get_db | Nutzt api.db_connection. OK. |
| scripts/send_daily_tek.py | nein | get_db_type | Kompatibilität; bei DB_TYPE=postgresql OK. |
| scripts/sync/bwa_berechnung.py | – | – | Bitte prüfen. |
| scripts/backup/db_backup.py, scripts/db_backup.py | – | – | Backup-Ziel typisch Datei/PostgreSQL dump. |

### 4.3 Kurzantwort: Funktionieren die Scripts? Welche sind betroffen?

- **Scripts, die PostgreSQL (oder get_db/db_session) nutzen:** Sie funktionieren für die **App**, weil sie in derselben DB schreiben, die die App liest (z. B. sync_sales, locosoft_mirror, import_mt940, import_all_bank_pdfs, send_daily_auftragseingang, send_daily_tek; bei Mitarbeiter-Sync: sync_ldap_employees_pg.py, falls vorhanden).
- **Scripts, die nur SQLite nutzen und von Celery aufgerufen werden:** Sie laufen technisch (wenn die SQLite-Datei existiert), schreiben aber in **data/greiner_controlling.db**. Die App liest **PostgreSQL**. Damit (Stand 2026-02-25; bereits auf PostgreSQL umgestellt: sync_ad_departments, sync_stammdaten, sync_fahrzeug_stammdaten, update_leasys_cache):
  - **sync_ldap_employees.py** (falls _pg nicht genutzt wird) – Mitarbeiter-Sync in SQLite.
  - **sync_teile.py, sync_teile_locosoft.py, import_teile.py, import_teile_lieferscheine.py** – Teile-Daten in SQLite.
  - **sync_charge_types.py** – charge_types in SQLite.
  - **umsatz_bereinigung_production.py** – Bereinigung in SQLite.

**Betroffen** = alle von Celery gestarteten Scripts, die ausschließlich oder zentral SQLite verwenden: Sie „berühren“ die App nur dadurch, dass sie **von** der App (Celery) getriggert werden; ihre **Daten** erreichen die App nicht, weil die App PostgreSQL nutzt.

---
**Änderungen am Code (kein reines Audit mehr):** get_capacity_settings (1.2); Scripts auf PostgreSQL umgestellt: sync_ad_departments, update_leasys_cache, sync_fahrzeug_stammdaten, sync_stammdaten (2026-02-25).
