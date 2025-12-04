# CLAUDE.md - Greiner Portal DRIVE Projekt-Kontext

**Letzte Aktualisierung:** 2025-12-04 (TAG 89)

---

## 🔧 ARBEITSUMGEBUNG

### Server
- **IP:** 10.80.80.20
- **Hostname:** srvlinux01.auto-greiner.de
- **User:** ag-admin
- **Projekt-Pfad:** `/opt/greiner-portal/`
- **Web-URL:** https://auto-greiner.de/ (intern: http://drive/)

### Sync-Verzeichnis (Windows ↔ Server)
```
Windows (Claude):  \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
Server Mount:      /mnt/greiner-portal-sync/
```

⚠️ **WICHTIG:** Claude editiert Dateien im Windows-Pfad. Diese sind auf dem Server unter `/mnt/greiner-portal-sync/` gemountet!

---

## 🔄 WORKFLOW: Dateien syncen

### Einzelne Datei:
```bash
cp /mnt/greiner-portal-sync/pfad/datei.py /opt/greiner-portal/pfad/
```

### Ordner syncen:
```bash
rsync -av /mnt/greiner-portal-sync/scheduler/ /opt/greiner-portal/scheduler/
rsync -av /mnt/greiner-portal-sync/templates/ /opt/greiner-portal/templates/
```

### Nach Python-Änderungen:
```bash
sudo systemctl restart greiner-portal
```

### Nach Scheduler-Job-Änderungen:
```bash
sudo systemctl restart greiner-scheduler
```

---

## ⏰ JOB-SCHEDULER (NEU: Separater Service!)

### Architektur (seit TAG 89)
```
┌─────────────────────────────────────────────────────────────┐
│                    GREINER PORTAL                           │
├─────────────────────────────────────────────────────────────┤
│  greiner-portal.service     │  greiner-scheduler.service   │
│  (Gunicorn, 9 Worker)       │  (Standalone Python)         │
│  ─────────────────────────  │  ─────────────────────────   │
│  • Web-UI & API             │  • APScheduler               │
│  • /admin/jobs/ (Dashboard) │  • Führt geplante Jobs aus   │
│  • Manueller Job-Start      │  • Läuft 24/7 im Hintergrund │
└─────────────────────────────────────────────────────────────┘
```

### Warum separater Service?
- Gunicorn mit 9+ Workern verursachte Race-Conditions
- APScheduler startete mehrfach und wurde sofort beendet
- Separater Prozess = stabil und zuverlässig

### Service-Befehle
```bash
# Status prüfen
sudo systemctl status greiner-scheduler

# Logs anzeigen
journalctl -u greiner-scheduler -f

# Neu starten (nach Job-Änderungen)
sudo systemctl restart greiner-scheduler

# Aktivieren beim Booten
sudo systemctl enable greiner-scheduler
```

### Job-Definitionen ändern
1. Datei editieren: `scheduler/job_definitions.py`
2. Syncen: `cp /mnt/greiner-portal-sync/scheduler/job_definitions.py /opt/greiner-portal/scheduler/`
3. **Beide Services** neu starten:
   ```bash
   sudo systemctl restart greiner-scheduler
   sudo systemctl restart greiner-portal
   ```

### Manueller Job-Start
- **Web-UI:** `/admin/jobs/` → Play-Button klicken
- **curl:** `curl -X POST "http://localhost:5000/admin/jobs/run/JOB_ID"`
- **Sicher:** Jobs haben `max_instances=1`, keine Doppelausführung möglich

### Wichtige Dateien
```
scheduler/
├── __init__.py              # Modul-Exports
├── job_manager.py           # APScheduler + run_script/run_shell
├── job_definitions.py       # Alle Job-Definitionen
└── routes.py                # Web-UI Routes

scheduler_standalone.py      # Standalone-Scheduler (vom Service gestartet)
config/greiner-scheduler.service  # Systemd Service-Definition
```

### Kostenstellen-Übersicht
| Kostenstelle | Jobs | Beispiele |
|--------------|------|-----------|
| **controlling** | 13 | MT940, HVB PDF, Santander, Hyundai, Backup |
| **aftersales** | 12 | ServiceBox (Scraper/Matcher/Import), Teile |
| **verkauf** | 5 | Sales Sync, Stellantis, Stammdaten, BWA |

---

## 🏦 BANK-IMPORT ÜBERSICHT

| Bank | Format | Script | Zeitplan |
|------|--------|--------|----------|
| Genobank (3 Konten) | MT940 | `import_mt940.py` | 08:00, 12:00, 17:00 |
| Sparkasse | MT940 | `import_mt940.py` | 08:00, 12:00, 17:00 |
| VR Bank Landau | MT940 | `import_mt940.py` | 08:00, 12:00, 17:00 |
| **HypoVereinsbank** | **PDF** | `import_all_bank_pdfs.py --bank hvb` | 08:30 |

### Dateipfade
```
MT940: /mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/
PDF:   /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Hypovereinsbank/
```

---

## 📁 WICHTIGE PFADE

| Was | Server-Pfad |
|-----|-------------|
| Flask-App | `/opt/greiner-portal/app.py` |
| APIs | `/opt/greiner-portal/api/` |
| Routes | `/opt/greiner-portal/routes/` |
| Templates | `/opt/greiner-portal/templates/` |
| Scheduler | `/opt/greiner-portal/scheduler/` |
| SQLite DB | `/opt/greiner-portal/data/greiner_controlling.db` |
| Scheduler-Logs DB | `/opt/greiner-portal/data/scheduler_logs.db` |
| Credentials | `/opt/greiner-portal/config/.env` |
| Logs | `/opt/greiner-portal/logs/` |

### Mount-Pfade
| Mount | Pfad |
|-------|------|
| **Sync-Verzeichnis** | `/mnt/greiner-portal-sync/` |
| Buchhaltung | `/mnt/buchhaltung/` |
| GlobalCube | `/mnt/globalcube/` |
| Teilelieferscheine | `/mnt/loco-teilelieferscheine/` |

---

## 🗄️ DATENBANKEN

### SQLite (lokal)
- **Pfad:** `/opt/greiner-portal/data/greiner_controlling.db`
- **WAL-Mode:** Aktiviert
- **Inhalt:** Controlling, Verkauf, Urlaub, Auth, Teile

### Scheduler-DBs
- **Jobs:** `/opt/greiner-portal/data/scheduler_jobs.db` (APScheduler JobStore)
- **Logs:** `/opt/greiner-portal/data/scheduler_logs.db` (History, Definitionen)

### PostgreSQL (Locosoft - extern)
- **Host:** 10.80.80.8:5432
- **Database:** loco_auswertung_db
- **User:** loco_auswertung_benutzer

---

## 🚀 DEPLOYMENT-BEFEHLE

```bash
# Portal-Status
sudo systemctl status greiner-portal

# Scheduler-Status
sudo systemctl status greiner-scheduler

# Portal neu starten
sudo systemctl restart greiner-portal

# Scheduler neu starten
sudo systemctl restart greiner-scheduler

# Logs live (Portal)
journalctl -u greiner-portal -f

# Logs live (Scheduler)
journalctl -u greiner-scheduler -f
```

---

## 📋 SESSION-DOKUMENTATION

### Bei Session-Start:
1. Diese Datei (`CLAUDE.md`) lesen
2. `SESSION_WRAP_UP_TAG[X-1].md` lesen
3. `TODO_FOR_CLAUDE_SESSION_START_TAG[X].md` (falls vorhanden)

### Bei Session-Ende:
1. `SESSION_WRAP_UP_TAG[X].md` erstellen
2. Git commit auf Server

---

## 🔗 AKTUELLE MODULE

| Modul | API | Routes | UI |
|-------|-----|--------|-----|
| Bankenspiegel | `bankenspiegel_api.py` | `bankenspiegel_routes.py` | `/bankenspiegel/` |
| Verkauf | `verkauf_api.py` | `verkauf_routes.py` | `/verkauf/` |
| Controlling | `controlling_api.py` | `controlling_routes.py` | `/controlling/` |
| Urlaubsplaner | `vacation_api.py` | in `app.py` | `/urlaubsplaner/v2` |
| Teile/Aftersales | `teile_api.py` | `teile_routes.py` | `/aftersales/teile/` |
| **Job-Scheduler** | - | `scheduler/routes.py` | `/admin/jobs/` |
| Leasys | `leasys_api.py` | in `app.py` | `/verkauf/leasys-programmfinder` |

---

## ⚠️ WICHTIGE HINWEISE

1. **Sync-Verzeichnis ≠ Live-Server** - Nach Änderungen immer `cp` oder `rsync`!
2. **Templates:** Kein Restart nötig - nur Browser-Refresh (Strg+F5)
3. **Python-Änderungen:** `sudo systemctl restart greiner-portal`
4. **Job-Änderungen:** `sudo systemctl restart greiner-scheduler`
5. **Manueller Job-Start:** Sicher über UI - keine Doppelausführung möglich

---

## 🏷️ VERSIONSHISTORIE

| TAG | Datum | Highlights |
|-----|-------|------------|
| **89** | **04.12.2025** | **Job-Scheduler Fix: Separater Service, run_script args, PATH für Shell** |
| 88 | 02.12.2025 | APScheduler Migration, Job-Scheduler UI |
| 87 | 01.12.2025 | Cron → APScheduler Umstellung |
| 86 | 30.11.2025 | Leasys Kalkulator |
| 85 | 29.11.2025 | Dashboard KPIs, Rebranding zu DRIVE |

---

*Diese Datei wird von Claude bei jeder Session gelesen.*
*Pfade und Workflows hier sind verbindlich!*
