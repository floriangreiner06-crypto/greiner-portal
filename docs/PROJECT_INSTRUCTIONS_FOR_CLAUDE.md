# 🎯 PROJECT INSTRUCTIONS FÜR CLAUDE (Greiner Portal DRIVE)

## KRITISCHE REGEL - IMMER BEFOLGEN!

**Bei Session-Start mit "TAG XX: ... Lies TODO..." oder ähnlichem:**

1. **SOFORT** `Filesystem:read_text_file` auf das Sync-Verzeichnis ausführen:
   - Pfad: `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md`

2. **NIEMALS** `project_knowledge_search` für Session-Docs nutzen!
   - Project Knowledge ist oft veraltet
   - Das Sync-Verzeichnis ist immer aktuell

3. Bei Bedarf auch lesen:
   - `\\Srvrdb01\...\Server\CLAUDE.md` (Projekt-Kontext)
   - `\\Srvrdb01\...\Server\WORKFLOW.md` (Arbeitsregeln)
   - `\\Srvrdb01\...\Server\docs\DB_SCHEMA_SQLITE.md` (bei DB-Arbeit)

---

## PROJEKT-KONTEXT

**Greiner Portal DRIVE** ist ein Flask-basiertes ERP-System für ein Autohaus.

### Server
- **IP:** 10.80.80.20
- **Projekt-Pfad:** `/opt/greiner-portal/`
- **Web-URL:** https://auto-greiner.de/

### Sync-Verzeichnis (Windows ↔ Server)
```
Windows (Claude-Zugriff):  \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
Server Mount:              /mnt/greiner-portal-sync/
```

### Wichtige Pfade im Sync-Verzeichnis
```
Server\
├── WORKFLOW.md              ← Arbeitsregeln
├── CLAUDE.md                ← Projekt-Kontext
├── docs\
│   ├── TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md
│   ├── SESSION_WRAP_UP_TAG[XX].md
│   ├── DB_SCHEMA_SQLITE.md
│   └── DB_SCHEMA_LOCOSOFT.md
├── scripts\
│   ├── imports\             ← Import-Scripts
│   ├── sync\                ← Locosoft-Sync
│   ├── scrapers\            ← Web-Scraper
│   └── analysis\            ← Analysen
└── scheduler\
    └── job_definitions.py   ← 30 aktive Jobs
```

---

## SESSION-WORKFLOW

### Start:
1. User sagt: `TAG XX: [Aufgabe]. Lies docs/TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md`
2. Claude liest SOFORT aus Sync-Verzeichnis (Filesystem-Tool!)
3. Claude fasst Kontext zusammen und legt los

### Ende:
1. Claude erstellt `docs/SESSION_WRAP_UP_TAG[XX].md`
2. Claude erstellt `docs/TODO_FOR_CLAUDE_SESSION_START_TAG[XX+1].md`
3. Claude gibt Git-Befehle für User

---

## TECHNISCHE DETAILS

### Datenbanken
- **SQLite:** `/opt/greiner-portal/data/greiner_controlling.db` (99 Tabellen)
- **PostgreSQL:** Locosoft auf 10.80.80.8:5432 (102 Tabellen)

### Services
```bash
sudo systemctl status greiner-portal      # Web-App
sudo systemctl status greiner-scheduler   # Job-Scheduler (30 Jobs)
```

### Nach Code-Änderungen
```bash
sudo systemctl restart greiner-portal
sudo systemctl restart greiner-scheduler  # nur bei Job-Änderungen
```

---

## AKTUELLE VERSION

**TAG 90** (2025-12-04):
- WORKFLOW.md erstellt
- Scripts logisch umbenannt
- 30 Jobs im Scheduler
- DB-Schema Generator verfügbar
