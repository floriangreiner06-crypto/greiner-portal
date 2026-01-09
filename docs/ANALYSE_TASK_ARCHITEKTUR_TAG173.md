# Analyse: Task-Architektur und Bug-Fix TAG 173

**Datum:** 2026-01-08  
**Status:** 🔴 KRITISCH - Tasks laufen nicht, manueller Start fehlgeschlagen

---

## 🎯 Executive Summary

**Hauptproblem:** Die Celery Task-Architektur ist unvollständig implementiert. Die meisten Tasks sind in der Konfiguration (`celery_app/__init__.py`) definiert, aber nicht in `celery_app/tasks.py` implementiert. Dies führt zu 500-Fehlern beim manuellen Start über die UI.

**Weitere Probleme:**
- Redundanz zwischen altem System (`scheduler/routes.py`) und neuem System (`celery_app/routes.py`)
- Keine Übersicht über gelaufene Jobs
- Ein Script verwendet noch SQLite statt PostgreSQL

---

## 📊 Architektur-Übersicht

### Aktuelle Komponenten

1. **Celery Task Queue** (NEU - seit TAG 110)
   - **Broker:** Redis (localhost:6379)
   - **Worker:** `celery-worker` Service
   - **Beat:** `celery-beat` Service (Scheduler)
   - **Flower:** Web-UI auf Port 5555
   - **Config:** `celery_app/__init__.py`
   - **Tasks:** `celery_app/tasks.py` ⚠️ **UNVOLLSTÄNDIG**
   - **Routes:** `celery_app/routes.py` (UI: `/admin/celery/`)

2. **Alter Scheduler** (ALT - Legacy)
   - **Routes:** `scheduler/routes.py` (UI: `/admin/jobs/`)
   - **Logs:** SQLite (`data/scheduler_logs.db`)
   - **Status:** ⚠️ **REDUNDANT**, sollte entfernt werden

### Task-Definitionen

#### ✅ Implementierte Tasks (in `celery_app/tasks.py`)

| Task | Name | Status |
|------|------|--------|
| `benachrichtige_serviceberater_ueberschreitungen` | Serviceberater-Benachrichtigungen | ✅ |
| `servicebox_scraper` | ServiceBox Scraper | ✅ |
| `servicebox_matcher` | ServiceBox Matcher | ✅ |
| `servicebox_import` | ServiceBox Import | ✅ |
| `servicebox_master` | ServiceBox Master | ✅ |

**Gesamt: 5 Tasks implementiert**

#### ❌ Fehlende Tasks (in Config, aber NICHT implementiert)

| Task | Name | Schedule | Queue |
|------|------|----------|-------|
| `import_mt940` | MT940 Import | 3x täglich (08:00, 12:00, 17:00) | controlling |
| `import_hvb_pdf` | HypoVereinsbank PDF | Täglich 08:30 | controlling |
| `import_santander` | Santander Import | Täglich 08:15 | controlling |
| `import_hyundai` | Hyundai Finance Import | Täglich 09:00 | controlling |
| `scrape_hyundai` | Hyundai Scraper | Täglich 08:45 | controlling |
| `leasys_cache_refresh` | Leasys Cache | Alle 30 Min (7-18 Uhr) | controlling |
| `umsatz_bereinigung` | Umsatz-Bereinigung | Täglich 09:30 | controlling |
| `bwa_berechnung` | BWA Berechnung | Täglich 19:30 | controlling |
| `sync_employees` | Mitarbeiter Sync | Täglich 06:00 | controlling |
| `sync_locosoft_employees` | Locosoft Employees | Täglich 06:15 | controlling |
| `sync_ad_departments` | AD Abteilungen | Täglich 06:20 | controlling |
| `email_auftragseingang` | E-Mail Auftragseingang | Täglich 17:15 | controlling |
| `db_backup` | DB Backup | Täglich 03:00 | controlling |
| `cleanup_backups` | Backup Cleanup | Täglich 03:30 | controlling |
| `sync_teile` | Teile Sync | Alle 30 Min | aftersales |
| `import_teile` | Teile Import | Alle 2 Stunden | aftersales |
| `werkstatt_leistung` | Werkstatt Leistung | Täglich 19:15 | aftersales |
| `email_werkstatt_tagesbericht` | Werkstatt E-Mail | Täglich 17:30 | aftersales |
| `sync_charge_types` | Charge Types Sync | Täglich 06:05 | aftersales |
| `ml_retrain` | ML Training | Täglich 03:15 | aftersales |
| `sync_sales` | Verkauf Sync | Stündlich (7-18 Uhr) | verkauf |
| `import_stellantis` | Stellantis Import | Täglich 07:30 | verkauf |
| `sync_stammdaten` | Stammdaten Sync | Täglich 09:30 | verkauf |
| `locosoft_mirror` | Locosoft Mirror | Täglich 19:00 | verkauf |
| `update_penner_marktpreise` | Penner Marktpreise | Täglich 03:00 | aftersales |
| `email_penner_weekly` | Penner Wochenreport | Montag 07:00 | aftersales |
| `sync_eautoseller_data` | eAutoseller Sync | Alle 15 Min (7-18 Uhr) | verkauf |

**Gesamt: 28 Tasks fehlen!**

---

## 🐛 Bug-Analyse

### Problem 1: 500 Error beim manuellen Task-Start

**Symptom:**
```
Failed celery/start/import_mt940:1 to load resource: 
the server responded with a status of 500 (INTERNAL SERVER ERROR)
```

**Ursache:**
```python
# celery_app/routes.py Zeile 263-271
from celery_app.tasks import (
    import_mt940, import_hvb_pdf, import_santander, import_hyundai,
    scrape_hyundai, ...
)
# ❌ ImportError: cannot import name 'import_mt940' from 'celery_app.tasks'
```

**Lösung:** Alle fehlenden Tasks in `celery_app/tasks.py` implementieren.

### Problem 2: Redundanz zwischen altem und neuem System

**Altes System (`scheduler/routes.py`):**
- Verwendet `JOB_FUNCTIONS` Dict
- Startet Scripts direkt via `run_script()`
- Logs in SQLite (`data/scheduler_logs.db`)
- UI: `/admin/jobs/`

**Neues System (`celery_app/routes.py`):**
- Verwendet Celery Tasks
- Startet Tasks via `task.delay()`
- Logs in Redis/Flower
- UI: `/admin/celery/`

**Problem:** Beide Systeme existieren parallel, verwirrend für User.

**Lösung:** Altes System entfernen oder klar dokumentieren.

### Problem 3: Keine Übersicht über gelaufene Jobs

**Aktuell:**
- Flower Dashboard zeigt nur aktive Tasks
- Keine Historie über erfolgreich/fehlgeschlagene Jobs
- Keine Übersicht wann Jobs zuletzt gelaufen sind

**Lösung:** 
- Flower Events für Historie nutzen
- Oder: Eigene Task-History-Tabelle in PostgreSQL

### Problem 4: SQLite-Script noch vorhanden

**Gefunden:**
- `scripts/imports/sync_charge_types.py` verwendet noch SQLite
- Alle anderen Import-Scripts verwenden PostgreSQL

**Status:**
- ✅ `import_stellantis.py` → PostgreSQL (`get_db()`)
- ✅ `import_hyundai_finance.py` → PostgreSQL (`get_db()`)
- ✅ `import_mt940.py` → PostgreSQL (vermutlich)
- ❌ `sync_charge_types.py` → SQLite (`get_sqlite_connection()`)

**Lösung:** `sync_charge_types.py` auf PostgreSQL migrieren.

---

## 📋 Task-Implementierungs-Plan

### Phase 1: Kritische Import-Tasks (Controlling)

1. **`import_mt940`**
   - Script: `scripts/imports/import_mt940.py`
   - Args: `/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/`
   - Timeout: 120s

2. **`import_hvb_pdf`**
   - Script: `scripts/imports/import_all_bank_pdfs.py`
   - Args: `--bank hvb --days 3`
   - Timeout: 120s

3. **`import_santander`**
   - Script: `scripts/imports/import_santander_bestand.py`
   - Timeout: 300s

4. **`import_hyundai`**
   - Script: `scripts/imports/import_hyundai_finance.py`
   - Timeout: 300s

5. **`scrape_hyundai`**
   - Script: `tools/scrapers/hyundai_bestandsliste_scraper.py`
   - Timeout: 180s

### Phase 2: Sync-Tasks

6. **`sync_employees`**
   - Script: `scripts/sync/sync_employees.py`

7. **`sync_locosoft_employees`**
   - Script: `scripts/sync/sync_locosoft_employees.py` (vermutlich)

8. **`sync_ad_departments`**
   - Script: `scripts/sync/sync_ad_departments.py` (vermutlich)

9. **`sync_sales`**
   - Script: `scripts/sync/sync_sales.py`

10. **`sync_stammdaten`**
    - Script: `scripts/sync/sync_stammdaten.py` (vermutlich)

11. **`sync_teile`**
    - Script: `scripts/sync/sync_teile.py` (vermutlich)

12. **`sync_charge_types`**
    - Script: `scripts/imports/sync_charge_types.py` ⚠️ **SQLite → PostgreSQL migrieren**

13. **`locosoft_mirror`**
    - Script: `scripts/sync/locosoft_mirror.py`

### Phase 3: Weitere Tasks

14. **`import_stellantis`**
    - Script: `scripts/imports/import_stellantis.py`

15. **`leasys_cache_refresh`**
    - Script: `scripts/update_leasys_cache.py`

16. **`umsatz_bereinigung`**
    - Script: `scripts/analysis/umsatz_bereinigung_production.py`

17. **`bwa_berechnung`**
    - Script: `scripts/sync/bwa_berechnung.py`

18. **`werkstatt_leistung`**
    - Script: `scripts/sync/sync_werkstatt_zeiten.py` (vermutlich)

19. **`import_teile`**
    - Script: `scripts/imports/import_teile.py` (vermutlich)

20. **`email_auftragseingang`**
    - Script: `scripts/send_daily_auftragseingang.py`

21. **`email_werkstatt_tagesbericht`**
    - Script: `scripts/send_daily_werkstatt_tagesbericht.py` (vermutlich)

22. **`db_backup`**
    - Script: `scripts/backup/db_backup.py` (vermutlich)

23. **`cleanup_backups`**
    - Script: `scripts/backup/cleanup_backups.py` (vermutlich)

24. **`ml_retrain`**
    - Script: `scripts/ml/retrain.py` (vermutlich)

25. **`update_penner_marktpreise`**
    - Script: `scripts/penner/update_marktpreise.py` (vermutlich)

26. **`email_penner_weekly`**
    - Script: `scripts/send_weekly_penner_report.py`

27. **`sync_eautoseller_data`**
    - Script: `scripts/sync/sync_eautoseller.py` (vermutlich)

---

## 🔍 Script-Analyse: SQLite vs PostgreSQL

### ✅ PostgreSQL (korrekt)

| Script | DB-Verbindung | Status |
|-------|--------------|--------|
| `import_stellantis.py` | `get_db()` | ✅ |
| `import_hyundai_finance.py` | `get_db()` | ✅ |
| `import_mt940.py` | `get_db()` (vermutlich) | ✅ |
| `import_santander_bestand.py` | `get_db()` (vermutlich) | ✅ |

### ❌ SQLite (muss migriert werden)

| Script | DB-Verbindung | Status |
|--------|---------------|--------|
| `sync_charge_types.py` | `get_sqlite_connection()` | ❌ |

### 📝 Migration nötig

**`sync_charge_types.py`:**
- Aktuell: Schreibt in SQLite (`data/greiner_controlling.db`)
- Soll: PostgreSQL (`drive_portal`)
- Tabellen: `charge_types_sync`, `charge_type_descriptions_sync`

---

## 🏗️ Empfohlene Task-Implementierung

### Pattern für alle Tasks

```python
@shared_task(soft_time_limit=TIMEOUT, name='celery_app.tasks.TASK_NAME')
def task_name():
    """
    Task-Beschreibung
    Läuft nach Schedule: ...
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/.../script.py'
        if not os.path.exists(script_path):
            logger.error(f"Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Task...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        
        if result.returncode == 0:
            logger.info("Task erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Task fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error(f"Task: Timeout nach {TIMEOUT}s")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Task")
        return {'success': False, 'error': str(e)}
```

---

## 📊 Monitoring & Übersicht

### Aktuell verfügbar

1. **Flower Dashboard** (`http://10.80.80.20:5555`)
   - Zeigt aktive Tasks
   - Zeigt Task-Status (PENDING, STARTED, SUCCESS, FAILURE)
   - Keine Historie

2. **Celery Task Manager UI** (`/admin/celery/`)
   - Zeigt alle Tasks
   - Manueller Start möglich
   - Zeigt Schedules

### Fehlend

1. **Task-Historie**
   - Wann wurde Task zuletzt ausgeführt?
   - War er erfolgreich?
   - Wie lange hat er gedauert?

2. **Job-Übersicht**
   - Welche Jobs sind heute gelaufen?
   - Welche sind fehlgeschlagen?
   - Welche stehen noch aus?

### Empfehlung

**Option 1: Flower Events erweitern**
- Flower Events in PostgreSQL speichern
- Eigene History-Tabelle

**Option 2: Eigene Task-History**
- Nach jedem Task: Ergebnis in PostgreSQL speichern
- Tabelle: `celery_task_history`
- Felder: `task_name`, `task_id`, `status`, `started_at`, `finished_at`, `result`, `error`

---

## ✅ Action Items

### Sofort (Kritisch)

1. ✅ **Alle fehlenden Tasks implementieren** (28 Tasks)
2. ✅ **`sync_charge_types.py` auf PostgreSQL migrieren**
3. ✅ **Task-Start-Fehler beheben** (500 Error)

### Kurzfristig

4. ⚠️ **Redundanz zwischen altem/neuem System klären**
   - Altes System (`/admin/jobs/`) entfernen?
   - Oder: Dokumentieren dass es Legacy ist

5. ⚠️ **Task-Historie implementieren**
   - PostgreSQL-Tabelle für Task-History
   - UI-Erweiterung für Historie-Anzeige

### Mittelfristig

6. 📋 **Monitoring verbessern**
   - E-Mail-Benachrichtigungen bei Task-Fehlern
   - Dashboard für Job-Status

7. 📋 **Dokumentation**
   - Welche Tasks laufen wann?
   - Welche Scripts werden verwendet?
   - Wie funktioniert die Architektur?

---

## 📝 Zusammenfassung

### Status

- **Tasks definiert:** 33 (in `celery_app/__init__.py`)
- **Tasks implementiert:** 5 (in `celery_app/tasks.py`)
- **Tasks fehlen:** 28 ❌
- **SQLite-Scripts:** 1 (`sync_charge_types.py`)
- **PostgreSQL-Scripts:** Alle anderen ✅

### Kritische Probleme

1. 🔴 **Tasks laufen nicht** - Fehlende Implementierungen
2. 🔴 **Manueller Start fehlgeschlagen** - 500 Error
3. 🟡 **Keine Übersicht** - Keine Historie
4. 🟡 **Redundanz** - Altes System noch vorhanden

### Nächste Schritte

1. Alle 28 fehlenden Tasks implementieren
2. `sync_charge_types.py` migrieren
3. Task-Historie implementieren
4. Altes System entfernen oder dokumentieren

---

**Erstellt:** 2026-01-08  
**TAG:** 173  
**Autor:** Claude (Auto)
