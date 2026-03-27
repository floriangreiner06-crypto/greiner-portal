# TODO FOR CLAUDE SESSION START TAG91

**Datum:** 2025-12-04  
**Vorgänger:** TAG90 (Workflow-Optimierung + Script-Umbenennung)

---

## 🎯 KONTEXT TAG 90

TAG90 war ein **großer Cleanup-Tag**:

### 1. Workflow-Optimierung
- `WORKFLOW.md` mit verbindlichen Regeln erstellt
- Session-Docs nach `docs/` konsolidiert
- DB-Schema Generator (`scripts/utils/export_db_schema.py`)
- 62 alte Backup-Dateien aufgeräumt

### 2. Script-Umbenennung
- Neue Struktur `scripts/scrapers/` für Web-Scraper
- 13 Scripts logisch umbenannt
- `job_definitions.py` aktualisiert
- Scheduler läuft mit 30 Jobs

---

## 📁 NEUE SCRIPT-STRUKTUR (TAG 90)

```
scripts/
├── imports/          ← Daten importieren
│   ├── import_mt940.py
│   ├── import_hvb_pdf.py
│   ├── import_santander.py
│   ├── import_hyundai.py
│   ├── import_stellantis.py
│   ├── import_servicebox.py
│   └── import_teile.py
│
├── sync/             ← Locosoft synchronisieren
│   ├── sync_sales.py
│   ├── sync_employees.py
│   ├── sync_stammdaten.py
│   ├── sync_teile.py
│   ├── locosoft_mirror.py
│   └── bwa_berechnung.py
│
├── scrapers/         ← Web-Scraper (NEU!)
│   ├── scrape_hyundai.py
│   ├── scrape_servicebox.py
│   ├── scrape_servicebox_full.py
│   └── match_servicebox.py
│
└── analysis/
    └── umsatz_bereinigung.py
```

---

## 📋 OFFENE PUNKTE / IDEEN

### Technisch
- [ ] `tools/scrapers/` aufräumen (viele alte Test-Dateien noch vorhanden)
- [ ] `scripts/sync/` aufräumen (alte sync_fibu_v2.x Versionen)
- [ ] Alte Dateien im Projekt-Root aufräumen (test_*.py, etc.)

### Features (aus Backlog)
- [ ] BWA Global Cube Bericht nachbauen (mehrfach versucht)
- [ ] Werkstattplanung.net GraphQL Integration
- [ ] Dashboard KPIs erweitern

### Nice-to-have
- [ ] Git Hook für pre-commit aktivieren
- [ ] Automatische Schema-Generierung nach Migrationen

---

## 🔧 SCHNELLSTART

```bash
cd /opt/greiner-portal
source venv/bin/activate

# Server Status
sudo systemctl status greiner-portal
sudo systemctl status greiner-scheduler

# Job-Übersicht im Browser
# https://auto-greiner.de/admin/jobs/

# DB-Schema aktualisieren (bei DB-Arbeit)
python3 scripts/utils/export_db_schema.py --all
```

---

## ⚠️ WICHTIG FÜR CLAUDE

**Neue Regeln aus WORKFLOW.md:**
1. Session-Docs IMMER aus Sync-Verzeichnis lesen: `\\Srvrdb01\...\Server\docs\`
2. NIEMALS `project_knowledge_search` für Session-Docs
3. Bei DB-Arbeit: `docs/DB_SCHEMA_*.md` lesen
4. Scripts jetzt in neuer Struktur (`scripts/scrapers/`, etc.)

---

## 📊 AKTUELLER STAND

| Bereich | Status |
|---------|--------|
| Workflow | ✅ WORKFLOW.md |
| DB-Schemas | ✅ Auto-generiert |
| Scripts | ✅ Logisch strukturiert |
| Job-Scheduler | ✅ 30 Jobs aktiv |
| Cleanup | ✅ 75+ Dateien aufgeräumt |

---

**Erstellt:** 2025-12-04  
**Von:** Claude (TAG 90)
