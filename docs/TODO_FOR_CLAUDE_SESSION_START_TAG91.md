# TODO FOR CLAUDE SESSION START TAG91

**Datum:** 2025-12-04  
**Vorgänger:** TAG90 (Workflow-Optimierung + Cleanup)

---

## 🎯 KONTEXT

TAG90 hat den **Workflow optimiert**:
- `WORKFLOW.md` mit verbindlichen Regeln
- Auto-generierte DB-Schemas (`DB_SCHEMA_SQLITE.md`, `DB_SCHEMA_LOCOSOFT.md`)
- 62 alte Backup-Dateien aufgeräumt
- Session-Docs nach `docs/` konsolidiert

---

## 📋 OFFENE PUNKTE (aus TAG90)

### Prio 1: Monitoring & Stabilität

1. **ServiceBox Scraper Lock-File testen**
   - Mechanismus aus TAG88 prüfen
   - Sollte nur 1x pro Zeitplan laufen
   - Log: `journalctl -u greiner-scheduler | grep -i servicebox`

2. **Leasys Cache Timeout erhöhen**
   - Aktuell: 300s (5min)
   - Problem: Große Requests dauern länger
   - Fix: Timeout auf 600-900s erhöhen
   - Datei: `api/leasys_api.py`

### Prio 2: UI/UX

3. **Login-Seite deployen**
   - Mockup B wurde ausgewählt
   - Template: `templates/login_mockup_b.html` → `login.html`
   - CSS anpassen

4. **Admin-Navigation nur für Admins**
   - In `base.html` einbauen
   - `{% if current_user.portal_role == 'admin' %}`
   - URL: `/admin/system-status`

---

## 🗂️ WICHTIGE DATEIEN

```
# Workflow (NEU - LESEN!)
WORKFLOW.md                              ← Verbindliche Regeln

# DB-Schemas (NEU)
docs/DB_SCHEMA_SQLITE.md                 ← 99 Tabellen
docs/DB_SCHEMA_LOCOSOFT.md               ← 102 Tabellen

# Schema-Generator
scripts/utils/export_db_schema.py        ← Bei DB-Änderungen ausführen

# Leasys (Timeout)
api/leasys_api.py                        ← Cache-Timeout erhöhen

# Login
templates/login.html                     ← Aktuell
templates/login_mockup_b.html            ← Neues Design

# Navigation
templates/base.html                      ← Admin-Link einbauen
```

---

## 🔧 SCHNELLSTART

```bash
cd /opt/greiner-portal
source venv/bin/activate

# Server Status
sudo systemctl status greiner-portal
sudo systemctl status greiner-scheduler

# ServiceBox Lock-File prüfen
ls -la /tmp/greiner_*.lock

# Scheduler Logs
journalctl -u greiner-scheduler -f
```

---

## 📊 AKTUELLER STAND

| Modul | Status | Info |
|-------|--------|------|
| Workflow | ✅ | WORKFLOW.md erstellt |
| DB-Schemas | ✅ | Auto-generiert |
| Cleanup | ✅ | 62 Dateien aufgeräumt |
| ServiceBox Lock | ⏳ | Testen |
| Leasys Timeout | ⏳ | Erhöhen |
| Login-Seite | ⏳ | Mockup B deployen |
| Admin-Nav | ⏳ | Einbauen |

---

## ⚠️ WICHTIG FÜR CLAUDE

**Neue Regeln aus WORKFLOW.md:**
1. Session-Docs IMMER aus Sync-Verzeichnis lesen: `\\Srvrdb01\...\Server\docs\`
2. NIEMALS `project_knowledge_search` für Session-Docs
3. Bei DB-Arbeit: `docs/DB_SCHEMA_*.md` lesen

---

**Erstellt:** 2025-12-04  
**Von:** Claude (TAG 90)
