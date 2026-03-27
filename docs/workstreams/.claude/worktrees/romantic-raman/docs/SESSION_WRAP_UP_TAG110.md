# SESSION WRAP-UP TAG 110
## Datum: 2025-12-09 (Mo)
## Dauer: ~3 Stunden (21:30 - 23:00)

---

## 🎯 HAUPTTHEMEN

### 1. Werkstatt Dashboard Times-Bug (KRITISCH)
### 2. APScheduler → Celery + RedBeat Migration (MAJOR)
### 3. Task Manager UI mit editierbaren Zeitplänen (NEW)

---

## 🔧 TEIL 1: WERKSTATT DASHBOARD TIMES-BUG

### Problem
- Werkstatt Dashboard zeigte **keine Daten** für "Heute" und "Diese Woche"
- "Dieser Monat" funktionierte (84% Leistungsgrad, 12 Mechaniker)

### Root Cause Analyse
```sql
-- loco_times letzte Daten: 5 Tage alt!
SELECT MAX(date(start_time)) FROM loco_times;
-- Result: 2025-12-04 ❌

-- PostgreSQL hatte aktuelle Daten
SELECT date(start_time), COUNT(*) FROM times WHERE start_time >= '2025-12-05';
-- 2025-12-09: 480 Einträge ✅
```

### ROOT CAUSE GEFUNDEN
```sql
-- times ist eine VIEW, keine TABLE!
SELECT table_name, table_type FROM information_schema.tables WHERE table_name = 'times';
-- Result: times | VIEW

-- locosoft_mirror.py filterte nur BASE TABLEs
-- VIEWs wurden komplett übersprungen!
```

### Fix: locosoft_mirror.py
```python
# Neue Konstante hinzugefügt
INCLUDE_VIEWS = [
    'times',      # Stempelzeiten - KRITISCH für Werkstatt!
    'employees',  # Mitarbeiter - KRITISCH für Urlaubsplaner!
]

# get_all_tables() erweitert um VIEWs
def get_all_tables(pg_conn):
    # ... BASE TABLEs holen ...
    
    # VIEWs hinzufügen
    for view_name in INCLUDE_VIEWS:
        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
        row_count = cursor.fetchone()[0]
        tables.append({'name': view_name, 'rows': row_count, 'is_view': True})
```

### Ergebnis nach Fix
```bash
python scripts/sync/locosoft_mirror.py --tables times,employees
# OK: 188,275 Zeilen (times)
# OK: 114 Zeilen (employees)

# Werkstatt-Daten neu berechnet
python scripts/sync/sync_werkstatt_zeiten.py
# ✓ Aufträge: 10775, Durchschnitt: 117.0%
# ✓ Mechaniker: 16, Durchschnitt: 89.4%
```

---

## 🔧 TEIL 2: CELERY + REDBEAT MIGRATION

### Ausgangslage: APScheduler Probleme
- Jobs meldeten "success" obwohl fehlerhaft (times-Bug lief 5 Tage unbemerkt)
- Zwei Dateien synchron halten (job_definitions.py + routes.py)
- Debugging schwierig
- Manueller Job-Start buggy
- Keine professionelle UI

### Entscheidung: Celery + Beat + RedBeat
- **Celery**: Battle-tested Task Queue (Instagram, Mozilla, etc.)
- **Beat**: Scheduler-Komponente
- **RedBeat**: Schedules in Redis → editierbar via UI
- **Flower**: Professionelles Web-Dashboard out-of-the-box

### Installation
```bash
# Redis (Message Broker)
sudo apt install redis-server -y
sudo systemctl enable redis-server

# Celery + Flower + RedBeat
pip install celery[redis] flower celery-redbeat
```

### Neue Dateien erstellt

#### celery_app/__init__.py
- Celery App Konfiguration
- RedBeat Integration (Redis DB 2)
- Beat Schedule mit 35+ Jobs
- Queues: controlling, aftersales, verkauf

#### celery_app/tasks.py
- Alle Jobs als Celery Tasks
- Retry-Logik für Netzwerk-Fehler
- Timeouts pro Task
- run_script() Helper

#### celery_app/routes.py
- Flask Blueprint für Task Manager UI
- Schedule CRUD (Create, Read, Update, Delete)
- RedBeat Integration
- Cron → lesbare Beschreibung Konvertierung

#### templates/admin/celery_tasks.html
- Tab 1: Manuell starten (Start-Buttons pro Task)
- Tab 2: Zeitpläne (alle Schedules mit Edit-Modal)
- Live Status-Updates
- Schnellauswahl für Cron-Ausdrücke

### Systemd Services

#### /etc/systemd/system/celery-worker.service
```ini
ExecStart=/opt/greiner-portal/venv/bin/celery -A celery_app worker 
          --loglevel=info -E -Q celery,controlling,aftersales,verkauf
```

#### /etc/systemd/system/celery-beat.service
```ini
ExecStart=/opt/greiner-portal/venv/bin/celery -A celery_app beat 
          --loglevel=info -S redbeat.RedBeatScheduler
```

#### /etc/systemd/system/celery-flower.service
```ini
ExecStart=/opt/greiner-portal/venv/bin/celery -A celery_app flower 
          --port=5555 --basic_auth=admin:greiner2025
```

### Alter Scheduler deaktiviert
```bash
sudo systemctl stop greiner-scheduler
sudo systemctl disable greiner-scheduler
```

---

## 🔧 TEIL 3: TASK MANAGER UI

### Features
- **Manuell starten**: Alle Tasks mit Start-Button, Live-Status
- **Zeitpläne**: 36 Jobs mit lesbaren Zeiten
- **Editierbar**: Modal zum Ändern von Zeitplänen
- **Redis-Badge**: Zeigt Quelle (Redis vs Config)
- **Schnellauswahl**: Mo-Fr 8:00, Tägl. 6:00, Alle 30m, etc.
- **Flower-Link**: Direkter Zugang zum Dashboard

### Navigation
- Menü: Florian → Administration → Task Manager
- Menü: Florian → Administration → Flower Dashboard
- URLs:
  - `/admin/celery/` - Task Manager
  - `:5555` - Flower Dashboard

---

## 📁 GEÄNDERTE/NEUE DATEIEN

### Neue Dateien
```
celery_app/
├── __init__.py          # Celery App + Config + Beat Schedule
├── tasks.py             # Alle Tasks als Celery Tasks
└── routes.py            # Flask Blueprint für UI

templates/admin/
└── celery_tasks.html    # Task Manager UI

config/systemd/
├── celery-worker.service
├── celery-beat.service
└── celery-flower.service
```

### Geänderte Dateien
```
scripts/sync/locosoft_mirror.py   # VIEWs hinzugefügt
app.py                            # Celery Blueprint registriert
templates/base.html               # Menü: Job-Scheduler → Task Manager
```

---

## 🚀 DEPLOYMENT-ZUSAMMENFASSUNG

```bash
# 1. Redis
sudo apt install redis-server -y

# 2. Python Packages
pip install celery[redis] flower celery-redbeat

# 3. Celery App kopieren
cp -r /mnt/greiner-portal-sync/celery_app /opt/greiner-portal/

# 4. Templates kopieren
cp /mnt/greiner-portal-sync/templates/admin/celery_tasks.html /opt/greiner-portal/templates/admin/

# 5. app.py + base.html kopieren
cp /mnt/greiner-portal-sync/app.py /opt/greiner-portal/
cp /mnt/greiner-portal-sync/templates/base.html /opt/greiner-portal/templates/

# 6. locosoft_mirror.py kopieren
cp /mnt/greiner-portal-sync/scripts/sync/locosoft_mirror.py /opt/greiner-portal/scripts/sync/

# 7. Systemd Services
sudo cp /mnt/greiner-portal-sync/config/systemd/celery-*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 8. Alter Scheduler deaktivieren
sudo systemctl stop greiner-scheduler
sudo systemctl disable greiner-scheduler

# 9. Neue Services starten
sudo systemctl enable celery-worker celery-beat celery-flower
sudo systemctl start celery-worker celery-beat celery-flower
sudo systemctl restart greiner-portal
```

---

## ✅ STATUS NACH SESSION

### Services
| Service | Status | Port |
|---------|--------|------|
| Redis | ✅ Active | 6379 |
| Celery Worker | ✅ Active | - |
| Celery Beat (RedBeat) | ✅ Active | - |
| Flower | ✅ Active | 5555 |
| greiner-portal | ✅ Active | 5000 |
| greiner-scheduler | ❌ Disabled | - |

### Funktionen
| Feature | Status |
|---------|--------|
| Werkstatt Dashboard (heute/woche) | ✅ Daten vorhanden |
| Task Manager UI | ✅ Funktioniert |
| Manueller Task-Start | ✅ Funktioniert |
| Editierbare Schedules | ✅ In Redis |
| Flower Monitoring | ✅ Erreichbar |

---

## 🐛 BEKANNTE ISSUES

### Minor: Wochentag-Anzeige
- Alle Jobs zeigen "(Täglich)" statt "(Mo-Fr)"
- Ursache: cron_to_readable() verliert day_of_week bei RedBeat
- Priorität: Niedrig (kosmetisch)

---

## 📚 LESSONS LEARNED

### 1. PostgreSQL VIEWs vs TABLEs
- VIEWs erscheinen nicht in `pg_stat_user_tables`
- Mirror-Scripts müssen VIEWs explizit behandeln
- INCLUDE_VIEWS Liste für kritische VIEWs pflegen

### 2. Job-Scheduler Komplexität
- APScheduler war zu fehleranfällig für Produktion
- Celery + RedBeat bietet:
  - Automatische Retries
  - Professionelles UI (Flower)
  - Editierbare Schedules
  - Besseres Logging

### 3. Redis für Celery
- DB 0: Celery Broker (Task Queue)
- DB 1: Celery Results
- DB 2: RedBeat Schedules

### 4. Sync-Workflow wichtig
- Immer erst diff Server vs Sync prüfen
- Dann im Sync bearbeiten
- Dann deployen

---

## 🔜 NÄCHSTE SCHRITTE

1. **Monitoring**: Morgen früh prüfen ob Jobs um 03:00, 06:00 gelaufen sind
2. **Wochentag-Fix**: cron_to_readable() korrigieren (kosmetisch)
3. **Dokumentation**: CLAUDE.md aktualisieren mit Celery-Infos
4. **Cleanup**: Alte scheduler/ Dateien können später entfernt werden

---

**Session beendet: 2025-12-09 23:15**
**Nächste Session: Monitoring der Nacht-Jobs prüfen**
