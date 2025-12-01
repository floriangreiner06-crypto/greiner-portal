# CLAUDE.md - Greiner Portal DRIVE Projekt-Kontext

**Letzte Aktualisierung:** 2025-12-01 (TAG 87)

---

## 🔧 ARBEITSUMGEBUNG

### Server
- **IP:** 10.80.80.20
- **Hostname:** srvlinux01.auto-greiner.de
- **User:** ag-admin
- **Projekt-Pfad:** `/opt/greiner-portal/`

### Sync-Verzeichnis (Windows ↔ Server)
```
Windows:  \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
Server:   /mnt/greiner-portal-sync/
```

⚠️ **WICHTIG:** Der Mount-Pfad ist `/mnt/greiner-portal-sync/` (NICHT `/mnt/greiner-sync/`)!

---

## 🔄 SYNC-WORKFLOW

### ⚠️ KRITISCH: Server = Single Source of Truth

**Änderungen werden IMMER auf dem Server gemacht!** Das Sync-Verzeichnis ist nur für Claude-Zugriff.

### Vor dem Sync - Git sauber machen (Putty):
```bash
cd /opt/greiner-portal

# Status prüfen
git status

# Falls uncommitted changes:
git add .
git commit -m "feat/fix: Beschreibung"
git push origin feature/tag82-onwards
```

### Sync Server → Windows (Putty):
```bash
# Variante 1: rsync (kann bei CIFS Probleme machen)
rsync -av --progress \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='logs/*.log' \
  --exclude='data/*.db' \
  --exclude='.git' \
  /opt/greiner-portal/ /mnt/greiner-portal-sync/

# Variante 2: tar (wenn rsync Berechtigungsprobleme hat)
cd /opt/greiner-portal
tar --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs/*.log' \
    --exclude='data/*.db' \
    --exclude='.git' \
    -cvzf /tmp/greiner-portal-backup.tar.gz .

cp /tmp/greiner-portal-backup.tar.gz /mnt/greiner-portal-sync/
cd /mnt/greiner-portal-sync/
tar --exclude='./data' -xvzf greiner-portal-backup.tar.gz
rm greiner-portal-backup.tar.gz
```

### Nach Claude-Änderungen - Sync Windows → Server (Putty):
```bash
rsync -av --progress \
  --exclude='.git' \
  --exclude='*.tar.gz' \
  /mnt/greiner-portal-sync/ /opt/greiner-portal/

# Service neu starten (bei Python-Änderungen)
sudo systemctl restart greiner-portal
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
| Credentials | `/opt/greiner-portal/config/.env` |
| Logs | `/opt/greiner-portal/logs/` |
| Scripts | `/opt/greiner-portal/scripts/` |

### Mount-Pfade auf Server
| Mount | Pfad |
|-------|------|
| **Sync-Verzeichnis** | `/mnt/greiner-portal-sync/` |
| Buchhaltung | `/mnt/buchhaltung/` |
| GlobalCube | `/mnt/globalcube/` |
| Loco Teilelieferscheine | `/mnt/loco-teilelieferscheine/` |

---

## 🗄️ DATENBANKEN

### SQLite (lokal)
- **Pfad:** `/opt/greiner-portal/data/greiner_controlling.db`
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

# Git-Status prüfen
cd /opt/greiner-portal
git status
git log --oneline -5
```

---

## 📋 SESSION-DOKUMENTATION

### Bei Session-Start:
1. `CLAUDE.md` lesen (diese Datei!)
2. `TODO_FOR_CLAUDE_SESSION_START_TAG[X].md` lesen
3. `SESSION_WRAP_UP_TAG[X-1].md` lesen

### Bei Session-Ende:
1. `SESSION_WRAP_UP_TAG[X].md` erstellen
2. `TODO_FOR_CLAUDE_SESSION_START_TAG[X+1].md` erstellen

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
| Leasys | `api/leasys_api.py` | in `app.py` | `templates/leasys_*.html` |
| Zins-Optimierung | `api/zins_optimierung_api.py` | - | - |
| Mail (Graph) | `api/mail_api.py` | - | - |

---

## ⚠️ WICHTIGE HINWEISE

1. **Server = Source of Truth** - Niemals nur im Sync-Verzeichnis arbeiten ohne zurück zu synchen!
2. **Git vor Sync** - Immer erst `git status` prüfen und committen
3. **Mount-Pfad:** `/mnt/greiner-portal-sync/` (NICHT `/mnt/greiner-sync/`)
4. **Templates brauchen keinen Restart** - nur Browser-Refresh (Strg+F5)
5. **Python-Änderungen brauchen Restart:** `sudo systemctl restart greiner-portal`
6. **Bei DB-Schema-Änderungen:** Migration in `migrations/` dokumentieren!
7. **Backup vor großen Änderungen:** `cp datei.py datei.py.bak_tagXX`

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
- **Letzter Commit:** `31bf01b` (01.12.2025)
- **Remote:** `github.com:floriangreiner06-crypto/greiner-portal.git`

---

## 🏷️ VERSIONSHISTORIE

| TAG | Datum | Highlights |
|-----|-------|------------|
| 87 | 01.12.2025 | Sync-Workflow bereinigt, CLAUDE.md aktualisiert |
| 86 | 30.11.2025 | Leasys Kalkulator |
| 85 | 29.11.2025 | Dashboard KPIs, Rebranding zu DRIVE |
| 84 | 28.11.2025 | BWA Dashboard, GlobalCube Mapping |
| 83 | 26.11.2025 | Hyundai Scraper |
| 82 | 25.11.2025 | Admin Dashboard, VIN-Filter, Zinsen-Berechtigungen |

---

*Diese Datei wird von Claude bei jeder Session gelesen.*
*Pfade und Workflows hier sind verbindlich!*
