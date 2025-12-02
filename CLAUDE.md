# CLAUDE.md - Greiner Portal DRIVE Projekt-Kontext

**Letzte Aktualisierung:** 2025-12-02 (TAG 88)

---

## 🔧 ARBEITSUMGEBUNG

### Server
- **IP:** 10.80.80.20
- **Hostname:** srvlinux01.auto-greiner.de
- **User:** ag-admin
- **Projekt-Pfad:** `/opt/greiner-portal/`
- **Web-URL:** https://auto-greiner.de/

### Sync-Verzeichnis (Windows ↔ Server)
```
Windows:  \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
Server:   /mnt/greiner-portal-sync/
```

⚠️ **WICHTIG:** Der Mount-Pfad ist `/mnt/greiner-portal-sync/` (NICHT `/mnt/greiner-sync/`)!

---

## 🔄 ARBEITSWEISE MIT SYNC

### ⚠️ KRITISCH: Zwei Arbeitsweisen verstehen

**Claude hat zwei Zugänge:**
1. **Filesystem-Tools** → Zugriff auf `\\Srvrdb01\...` (= `/mnt/greiner-portal-sync/` auf Server)
2. **Bash via Putty** → User kopiert Befehle, führt sie auf Server aus

### Typischer Workflow:

1. **Claude liest/editiert Dateien** über Filesystem-Tools im Sync-Verzeichnis
2. **User synct Änderungen zum Server:**
   ```bash
   rsync -av /mnt/greiner-portal-sync/pfad/datei.py /opt/greiner-portal/pfad/
   ```
3. **User startet Service neu (bei Python-Änderungen):**
   ```bash
   sudo systemctl restart greiner-portal
   ```

### ⚠️ WICHTIG für Claude:
- **Filesystem-Tools** arbeiten auf dem **Sync-Verzeichnis**, NICHT direkt auf `/opt/greiner-portal/`
- Nach Änderungen: Immer rsync-Befehl für den User bereitstellen!
- Bash-Befehle für Server-Tests über User ausführen lassen

### Einzelne Datei syncen:
```bash
rsync -av /mnt/greiner-portal-sync/api/beispiel.py /opt/greiner-portal/api/
```

### Mehrere Dateien/Ordner syncen:
```bash
rsync -av /mnt/greiner-portal-sync/api/ /opt/greiner-portal/api/
rsync -av /mnt/greiner-portal-sync/templates/ /opt/greiner-portal/templates/
```

### Komplettes Projekt syncen (selten nötig):
```bash
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='logs/*.log' --exclude='data/*.db' --exclude='.git' \
  /mnt/greiner-portal-sync/ /opt/greiner-portal/
```

---

## 📁 WICHTIGE PFADE

| Was | Server-Pfad |
|-----|-------------|
| Flask-App | `/opt/greiner-portal/app.py` |
| APIs | `/opt/greiner-portal/api/` |
| Routes | `/opt/greiner-portal/routes/` |
| Templates | `/opt/greiner-portal/templates/` |
| SQLite DB | `/opt/greiner-portal/data/greiner_controlling.db` |
| Scheduler | `/opt/greiner-portal/scheduler/` |
| Job-Definitionen | `/opt/greiner-portal/scheduler/job_definitions.py` |
| Credentials | `/opt/greiner-portal/config/.env` |
| Logs | `/opt/greiner-portal/logs/` |
| Scripts | `/opt/greiner-portal/scripts/` |

### Mount-Pfade auf Server
| Mount | Pfad |
|-------|------|
| **Sync-Verzeichnis** | `/mnt/greiner-portal-sync/` |
| Buchhaltung/Kontoauszüge | `/mnt/buchhaltung/Buchhaltung/Kontoauszüge/` |
| GlobalCube | `/mnt/globalcube/` |
| Loco Teilelieferscheine | `/mnt/loco-teilelieferscheine/` |

---

## ⏰ JOB-SCHEDULER (APScheduler)

### Architektur
- **Framework:** APScheduler mit SQLAlchemy JobStore
- **UI:** `/admin/jobs/` (Job-Übersicht, History, manueller Trigger)
- **Lock-File:** `/tmp/greiner_scheduler.lock` (verhindert Multi-Worker-Start!)
- **Logs-DB:** `/opt/greiner-portal/data/scheduler_logs.db`

⚠️ **KRITISCH:** Gunicorn läuft mit ~10 Workern. Lock-File in `app.py` stellt sicher, dass nur EIN Worker den Scheduler startet!

### Kostenstellen-Übersicht
| Kostenstelle | Jobs | Beispiele |
|--------------|------|-----------|
| **controlling** | 12 | MT940/PDF Import, Santander, Hyundai, Leasys, HR, Backup |
| **aftersales** | 12 | ServiceBox (Scraper/Matcher/Import), Teile-Sync |
| **verkauf** | 4 | Sales Sync, Stellantis, Stammdaten, Locosoft Mirror |

### Job-Definitionen ändern:
1. Datei editieren: `scheduler/job_definitions.py`
2. Syncen: `rsync -av /mnt/greiner-portal-sync/scheduler/job_definitions.py /opt/greiner-portal/scheduler/`
3. Scheduler-DB löschen: `rm -f /opt/greiner-portal/data/scheduler_jobs.db`
4. Restart: `sudo systemctl restart greiner-portal`

---

## 🏦 BANK-IMPORT ÜBERSICHT

### Quellen
| Bank | Format | Import |
|------|--------|--------|
| Genobank (57908, 22225, 1501500) | MT940 (.mta) | `import_mt940.py` |
| Sparkasse (760036467) | MT940 (.TXT) | `import_mt940.py` |
| VR Bank Landau (303585) | MT940 (.mta) | `import_mt940.py` |
| **HypoVereinsbank** | **PDF** | `import_all_bank_pdfs.py --bank hvb` |

### Dateipfade
```
MT940: /mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/
PDF:   /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Hypovereinsbank/
```

### Jobs
- MT940 Import: 08:00, 12:00, 17:00 (Mo-Fr)
- HypoVereinsbank PDF: 08:30 (Mo-Fr)

---

## 🗄️ DATENBANKEN

### SQLite (lokal)
- **Pfad:** `/opt/greiner-portal/data/greiner_controlling.db`
- **WAL-Mode:** Aktiviert (bessere Concurrency)
- **Inhalt:** Controlling, Verkauf, Urlaub, Auth, Stellantis

### PostgreSQL (Locosoft - extern)
- **Host:** In `/opt/greiner-portal/config/.env`
- **Inhalt:** Mitarbeiter, Zeiterfassung, Werkstattaufträge, Fahrzeuge

---

## 🚀 DEPLOYMENT-BEFEHLE

```bash
# Service-Status
systemctl status greiner-portal

# Neustart (nach Python-Änderungen)
sudo systemctl restart greiner-portal

# Logs live
journalctl -u greiner-portal -f

# Scheduler-Logs prüfen
journalctl -u greiner-portal --since "10 min ago" | grep -i scheduler

# Git-Status prüfen
cd /opt/greiner-portal
git status
git log --oneline -5
```

---

## 📋 SESSION-DOKUMENTATION

### Bei Session-Start:
1. `CLAUDE.md` lesen (diese Datei!)
2. `docs/SESSION_WRAP_UP_TAG[X-1].md` lesen
3. `docs/TODO_FOR_CLAUDE_SESSION_START_TAG[X].md` lesen (falls vorhanden)

### Bei Session-Ende:
1. `docs/SESSION_WRAP_UP_TAG[X].md` erstellen
2. Git commit (User macht das auf Server)
3. Optional: `TODO_FOR_CLAUDE_SESSION_START_TAG[X+1].md` erstellen

---

## 🔗 AKTUELLE MODULE & BLUEPRINTS

| Modul | API | Routes | Templates |
|-------|-----|--------|-----------|
| Bankenspiegel | `api/bankenspiegel_api.py` | `routes/bankenspiegel_routes.py` | `templates/bankenspiegel_*.html` |
| Verkauf | `api/verkauf_api.py` | `routes/verkauf_routes.py` | `templates/verkauf_*.html` |
| Urlaubsplaner | `api/vacation_api.py` | in `app.py` | `templates/urlaubsplaner_v2.html` |
| Controlling | - | `routes/controlling_routes.py` | `templates/controlling/` |
| After Sales/Teile | `api/teile_api.py`, `api/parts_api.py` | `routes/aftersales/teile_routes.py` | `templates/aftersales/` |
| Admin | `api/admin_api.py` | `routes/admin_routes.py` | `templates/admin/` |
| Scheduler | `scheduler/job_manager.py` | `scheduler/__init__.py` | `templates/admin/jobs.html` |
| Leasys | `api/leasys_api.py` | in `app.py` | `templates/leasys_*.html` |
| Zins-Optimierung | `api/zins_optimierung_api.py` | - | - |
| Mail (Graph) | `api/mail_api.py` | - | - |

---

## ⚠️ WICHTIGE HINWEISE

1. **Sync-Verzeichnis ≠ Live-Server** - Nach Änderungen immer rsync!
2. **Templates brauchen keinen Restart** - nur Browser-Refresh (Strg+F5)
3. **Python-Änderungen brauchen Restart:** `sudo systemctl restart greiner-portal`
4. **Scheduler-Änderungen:** Auch `scheduler_jobs.db` löschen!
5. **Bei DB-Schema-Änderungen:** Migration in `migrations/` dokumentieren!
6. **Backup vor großen Änderungen:** `cp datei.py datei.py.bak_tagXX`

---

## 🎨 FRONTEND-KONVENTIONEN

- **Framework:** Bootstrap 5.3
- **Icons:** Bootstrap Icons (`bi-xxx`)
- **JS:** jQuery 3.7.1
- **Charts:** Chart.js 4.4
- **Berechtigungen:** `current_user.can_access_feature('feature_name')`

---

## 📊 AKTUELLER GIT-STATUS

- **Branch:** `feature/tag82-onwards`
- **Remote:** `github.com:floriangreiner06-crypto/greiner-portal.git`

---

## 🏷️ VERSIONSHISTORIE

| TAG | Datum | Highlights |
|-----|-------|------------|
| 88 | 02.12.2025 | APScheduler Lock-File Fix, Bank-Import vereinfacht, Kostenstellen |
| 87 | 01.12.2025 | APScheduler Migration, Job-Scheduler UI |
| 86 | 30.11.2025 | Leasys Kalkulator |
| 85 | 29.11.2025 | Dashboard KPIs, Rebranding zu DRIVE |
| 84 | 28.11.2025 | BWA Dashboard, GlobalCube Mapping |
| 83 | 26.11.2025 | Hyundai Scraper |
| 82 | 25.11.2025 | Admin Dashboard, VIN-Filter, Zinsen-Berechtigungen |

---

*Diese Datei wird von Claude bei jeder Session gelesen.*
*Pfade und Workflows hier sind verbindlich!*
