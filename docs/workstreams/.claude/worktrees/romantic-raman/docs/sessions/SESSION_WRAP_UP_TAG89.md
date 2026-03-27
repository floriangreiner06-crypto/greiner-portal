# SESSION WRAP-UP TAG 89

**Datum:** 2025-12-04  
**Fokus:** Job-Scheduler Reparatur - Separater Service

---

## 🎯 HAUPTERGEBNIS

Der APScheduler funktioniert jetzt stabil als **separater Systemd-Service**, nachdem er in der Gunicorn Multi-Worker-Umgebung nicht zuverlässig lief.

---

## 🔧 ÄNDERUNGEN

### 1. Neue Architektur: Separater Scheduler-Service

```
┌─────────────────────────────────────────────────────────────┐
│  greiner-portal.service     │  greiner-scheduler.service   │
│  (Gunicorn, 9 Worker)       │  (Standalone Python)         │
│  ─────────────────────────  │  ─────────────────────────   │
│  • Web-UI & API             │  • APScheduler               │
│  • /admin/jobs/ (Dashboard) │  • Führt geplante Jobs aus   │
│  • Manueller Job-Start      │  • Läuft 24/7 im Hintergrund │
└─────────────────────────────────────────────────────────────┘
```

### 2. Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `scheduler_standalone.py` | Standalone-Scheduler-Prozess |
| `config/greiner-scheduler.service` | Systemd Service-Definition |

### 3. Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `scheduler/job_manager.py` | `run_script()` mit `args` Parameter, `run_shell()` mit PATH |
| `scheduler/job_definitions.py` | MT940 mit Pfad-Argument, HVB mit korrekten Args |
| `scheduler/routes.py` | Direkte Job-Ausführung + pause/resume Routes |
| `app.py` | Scheduler-Start-Code entfernt (nur UI-Blueprint) |
| `CLAUDE.md` | Aktualisiert auf TAG 89 mit neuer Scheduler-Doku |

### 4. Behobene Probleme

| Problem | Lösung |
|---------|--------|
| Scheduler startet/stoppt sofort in Gunicorn | Separater Service |
| Jobs nicht gefunden bei manuellem Start | `JOB_FUNCTIONS` Dict in routes.py |
| Shell-Befehle (`date`, `cp`) nicht gefunden | PATH in `run_shell()` |
| MT940 "directory argument required" | `args=[mt940_dir]` Parameter |
| HVB "can't open file" | Args getrennt vom Script-Pfad |
| pause/resume Routes fehlen | Neu implementiert in routes.py |

---

## 📊 AKTUELLER STATUS

### Job-Scheduler
- **30 Jobs** registriert und aktiv
- **Kostenstellen:** controlling (13), aftersales (12), verkauf (5)
- **Web-UI:** `/admin/jobs/` funktioniert
- **Manueller Start:** Sicher, keine Doppelausführung

### Heutige Imports (alle erfolgreich)
| Import | Zeit | Datensätze |
|--------|------|------------|
| Stellantis (EKF) | 08:22:02 | 99 Fahrzeuge, 2,76 Mio € |
| Hyundai Finance | 09:00:00 | 46 Fahrzeuge |
| Santander | 08:11:30 | 51 Fahrzeuge |
| MT940 | 08:10:28 | - |
| HVB PDF | 08:09:29 | - |

---

## 🛠️ SERVICE-BEFEHLE

```bash
# Scheduler-Status
sudo systemctl status greiner-scheduler

# Scheduler-Logs
journalctl -u greiner-scheduler -f

# Scheduler neu starten
sudo systemctl restart greiner-scheduler

# Portal neu starten
sudo systemctl restart greiner-portal
```

---

## 📝 OFFENE PUNKTE FÜR TAG 90

1. **Script-Umbenennung nach Funktion** (siehe Vorschlag)
   - `import_stellantis.py` → `import_einkaufsfinanzierung_stellantis.py`
   - Strukturierte Ordner: `banktransaktionen/`, `einkaufsfinanzierung/`, `teile/`

2. **fstab Parse-Errors** (Zeile 14-15) - optional prüfen

3. **ServiceBox Scraper** - Chrome/ChromeDriver Architektur-Problem

---

## 📁 SYNC-BEFEHLE (falls nötig)

```bash
# Alle Scheduler-Dateien syncen
cp /mnt/greiner-portal-sync/scheduler_standalone.py /opt/greiner-portal/
cp /mnt/greiner-portal-sync/scheduler/job_manager.py /opt/greiner-portal/scheduler/
cp /mnt/greiner-portal-sync/scheduler/job_definitions.py /opt/greiner-portal/scheduler/
cp /mnt/greiner-portal-sync/scheduler/routes.py /opt/greiner-portal/scheduler/
cp /mnt/greiner-portal-sync/app.py /opt/greiner-portal/
cp /mnt/greiner-portal-sync/CLAUDE.md /opt/greiner-portal/

# Services neu starten
sudo systemctl restart greiner-scheduler
sudo systemctl restart greiner-portal
```

---

*Session beendet: 2025-12-04 ~09:30*
