# 🚀 CLAUDE SESSION-ANLEITUNG - GREINER PORTAL DRIVE

**Stand:** 2025-12-12 (TAG 115)  
**Diese Datei ersetzt:** CLAUDE.md, PROJECT_INSTRUCTIONS.txt, docs/claude/*.md

---

## ⚡ WICHTIGSTE ÄNDERUNGEN (2025-12)

### 1. Claude hat DIREKTEN ZUGRIFF auf das Sync-Verzeichnis!

```
Windows-Pfad:  \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
Claude-Tool:   Filesystem:read_file, Filesystem:write_file, etc.
```

### 2. TEST-UMGEBUNG VERFÜGBAR (NEU TAG 115!)

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVER 10.80.80.20                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────┐        │
│  │     PRODUKTIV       │    │        TEST         │        │
│  │  /opt/greiner-portal│    │  /opt/greiner-test  │        │
│  │  Port 5000          │    │  Port 5001          │        │
│  │  ✅ Stabil          │    │  🔧 Experimente     │        │
│  └─────────────────────┘    └─────────────────────┘        │
│           │                          │                      │
│           ▼                          ▼                      │
│   http://10.80.80.20:5000    http://10.80.80.20:5001       │
└─────────────────────────────────────────────────────────────┘
```

⚠️ **NIEMALS rsync oder Massen-Sync verwenden - Gefahr zu groß!**

---

## 🎯 SESSION-START: 3 SCHRITTE

### **Schritt 1: Aktuellsten Stand lesen**

```
Filesystem:read_file auf:
\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\SESSION_WRAP_UP_TAG[HÖCHSTE_NUMMER].md
```

**NICHT** project_knowledge_search verwenden - oft veraltet!

### **Schritt 2: Aktuelle TODOs prüfen (falls vorhanden)**

```
Filesystem:list_directory auf:
\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\
```
→ Nach `TODO_FOR_CLAUDE_SESSION_START_TAG*.md` suchen

### **Schritt 3: User fragen**

- "Was ist das Ziel heute?"
- "Gibt es akute Probleme?"
- "Welches Feature/Modul?"

---

## 🔄 ENTWICKLUNGS-WORKFLOW (NEU MIT TEST-UMGEBUNG!)

### **Empfohlener Workflow:**

```
1. Claude erstellt/ändert Dateien im Sync-Verzeichnis
           ↓
2. User kopiert nach TEST (/opt/greiner-test/)
           ↓
3. User testet auf Port 5001
           ↓
4. Funktioniert? → Kopiere nach PRODUKTIV (/opt/greiner-portal/)
           ↓
5. Produktiv auf Port 5000 ✅
```

### **User-Befehle für TEST:**

```bash
# 1. Datei nach TEST kopieren
cp /mnt/greiner-portal-sync/api/xyz.py /opt/greiner-test/api/

# 2. Test-Service neustarten (nur bei Python-Änderungen)
sudo systemctl restart greiner-test

# 3. Testen auf: http://10.80.80.20:5001

# 4. Logs prüfen
journalctl -u greiner-test -f
```

### **User-Befehle für PRODUKTIV (nach erfolgreichem Test!):**

```bash
# 1. Datei nach PRODUKTIV kopieren
cp /opt/greiner-test/api/xyz.py /opt/greiner-portal/api/

# 2. Produktiv-Service neustarten (nur bei Python-Änderungen)
sudo systemctl restart greiner-portal

# 3. Testen auf: http://10.80.80.20:5000
```

### **Deploy-Helper Script (optional):**

```bash
# Alles in einem Befehl:
bash /opt/greiner-portal/scripts/deploy.sh test api/xyz.py    # Sync → Test
bash /opt/greiner-portal/scripts/deploy.sh prod api/xyz.py    # Test → Produktiv
bash /opt/greiner-portal/scripts/deploy.sh status             # Status beider Services
bash /opt/greiner-portal/scripts/deploy.sh sync-db            # Produktiv-DB → Test-DB
```

### **Templates brauchen KEINEN Restart!**
→ Nur Browser-Refresh (Strg+F5)

---

## 🖥️ UMGEBUNGEN ÜBERSICHT

| Umgebung | Port | URL | Verzeichnis | Service |
|----------|------|-----|-------------|---------|
| **PRODUKTIV** | 5000 | http://10.80.80.20:5000 | `/opt/greiner-portal/` | `greiner-portal` |
| **TEST** | 5001 | http://10.80.80.20:5001 | `/opt/greiner-test/` → `/data/greiner-test/` | `greiner-test` |

### **Service-Befehle:**

```bash
# PRODUKTIV
sudo systemctl status greiner-portal
sudo systemctl restart greiner-portal
journalctl -u greiner-portal -f

# TEST
sudo systemctl status greiner-test
sudo systemctl restart greiner-test
journalctl -u greiner-test -f
```

### **Test-DB aktualisieren (mit frischen Produktiv-Daten):**

```bash
sudo systemctl stop greiner-test
cp /opt/greiner-portal/data/greiner_controlling.db /opt/greiner-test/data/greiner_controlling.db
sudo systemctl start greiner-test
```

---

## 🗄️ DATENBANK-DOKUMENTATION

### Schema-Dateien (auto-generiert):

| Datei | Beschreibung |
|-------|-------------|
| `docs/DB_SCHEMA_SQLITE.md` | SQLite-Schema: **155 Tabellen**, Views, Indizes |
| `docs/DB_SCHEMA_LOCOSOFT.md` | PostgreSQL-Schema: 102 Tabellen |

**Stand:** 2025-12-12 (auto-generiert mit `python scripts/utils/export_db_schema.py --all`)

### Wichtige SQLite-Tabellen:

| Tabelle | Zeilen | Beschreibung |
|---------|--------|-------------|
| `loco_journal_accountings` | 599k | Journal-Buchungen (Locosoft) |
| `fibu_buchungen` | 549k | FiBu-Buchungen aus Locosoft |
| `loco_labours` | 281k | Arbeitsleistungen |
| `loco_parts` | 142k | Teile-Stammdaten |
| `loco_customers_suppliers` | 53k | Kunden/Lieferanten |
| `loco_orders` | 41k | Aufträge |
| `vacation_bookings` | 1.4k | Urlaubsbuchungen |
| `fahrzeugfinanzierungen` | 192 | Fahrzeug-Finanzierungen |
| `employees` | 76 | Mitarbeiter |
| `konten` | 12 | Bankkonten |

### Wichtige Views:

- `v_aktuelle_kontostaende` - Aktuelle Kontosalden
- `v_cashflow_kategorien` - Cashflow nach Kategorien
- `v_fahrzeugfinanzierungen_aktuell` - Aktive Finanzierungen
- `fahrzeuge_mit_zinsen` - Fahrzeuge mit Zinsstatus
- `v_vacation_balance_2025` - Urlaubssalden 2025

---

## 🔐 CREDENTIALS

**Datei:** `config/.env`

```bash
# Locosoft PostgreSQL
LOCOSOFT_HOST=10.80.80.8
LOCOSOFT_PORT=5432
LOCOSOFT_DATABASE=loco_auswertung_db
LOCOSOFT_USER=loco_auswertung_benutzer
LOCOSOFT_PASSWORD=loco

# SQLite
SQLITE_DATABASE=/opt/greiner-portal/data/greiner_controlling.db

# Microsoft Graph API (Office 365)
GRAPH_TENANT_ID=...
GRAPH_CLIENT_ID=...
GRAPH_CLIENT_SECRET=...
```

⚠️ **LDAP-Credentials:** Siehe `config/ldap_credentials.env`

---

## 📁 VERZEICHNISSTRUKTUR

### Claude hat Zugriff auf (Sync-Verzeichnis):

```
\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\
├── Server\                      ← HAUPTVERZEICHNIS
│   ├── app.py                   ← Flask-Hauptanwendung
│   ├── api\                     ← REST-APIs (25+ Module)
│   ├── routes\                  ← Flask-Routes (HTML-Views)
│   ├── templates\               ← Jinja2-Templates
│   ├── static\                  ← CSS, JS, Images
│   ├── scripts\                 ← Import/Sync/Maintenance Scripts
│   │   ├── imports\
│   │   ├── sync\
│   │   ├── setup\               ← Setup-Scripts (Test-Umgebung etc.)
│   │   └── deploy.sh            ← Deploy-Helper
│   ├── data\                    ← Datenbank (SQLite)
│   ├── config\                  ← Konfiguration
│   └── docs\                    ← Dokumentation
│       ├── claude\              ← Claude-spezifische Docs
│       ├── sessions\            ← Ältere Session-Wrap-Ups
│       └── SESSION_WRAP_UP_TAG*.md
```

### Server-Struktur:

```
/opt/greiner-portal/             ← PRODUKTIV
/opt/greiner-test/               ← TEST (Symlink zu /data/greiner-test/)
/mnt/greiner-portal-sync/        ← Sync-Mount zum Windows-Share
```

---

## 📊 AKTUELLE MODULE (TAG 115)

### Kern-Module (stabil):

| Modul | API | Template | Status |
|-------|-----|----------|--------|
| Bankenspiegel | `bankenspiegel_api.py` | `bankenspiegel_*.html` | ✅ Stabil |
| Verkauf | `verkauf_api.py` | `verkauf_*.html` | ✅ Stabil |
| Urlaubsplaner | `vacation_api.py` | `urlaubsplaner_v2.html` | ✅ Stabil |
| Urlaub-Admin | `vacation_admin_api.py` | - | ✅ Stabil |
| Urlaub-Chef | `vacation_chef_api.py` | - | ✅ Stabil |
| Controlling | `controlling_api.py` | `controlling_*.html` | ✅ Stabil |
| Organigramm | `organization_api.py` | `organigramm.html` | ✅ NEU (TAG113) |
| Admin | `admin_api.py` | `admin_*.html` | ✅ Stabil |

### Aftersales/Werkstatt:

| Modul | API | Template | Status |
|-------|-----|----------|--------|
| Werkstatt | `werkstatt_api.py` | `werkstatt_*.html` | 🔄 In Arbeit |
| Werkstatt-Live | `werkstatt_live_api.py` | `aftersales/live*.html` | 🔄 In Arbeit |
| Teile | `teile_api.py` | `teile_*.html` | 🔄 In Arbeit |
| Teile-Status | `teile_status_api.py` | - | 🔄 In Arbeit |
| Parts/Stellantis | `parts_api.py` | `aftersales/*.html` | 🔄 In Arbeit |
| Serviceberater | `serviceberater_api.py` | - | 🔄 In Arbeit |

### Spezial-Module:

| Modul | API | Beschreibung |
|-------|-----|-------------|
| Jahresprämie | `jahrespraemie_api.py` | Jahresprämien-Berechnung |
| Leasys | `leasys_api.py` | Leasys-Kalkulator |
| Gudat | `gudat_api.py` | Gudat-Integration |
| Mail | `mail_api.py` | E-Mail-Versand |
| Graph-Mail | `graph_mail_connector.py` | Office 365 Integration |
| PDF-Generator | `pdf_generator.py` | PDF-Erstellung |
| Zins-Optimierung | `zins_optimierung_api.py` | Zins-Berechnungen |
| ML | `ml_api.py` | Machine Learning (experimentell) |

---

## 📝 SESSION-DOKUMENTATION

### **Bei Session-Ende:**

1. **SESSION_WRAP_UP erstellen:**
```
\\Srvrdb01\...\Server\docs\SESSION_WRAP_UP_TAG[X].md
```

Inhalt:
- Datum, Dauer, Fokus
- Erreichte Ziele
- Geänderte Dateien
- Behobene Bugs
- Git Commits
- Offene Punkte

2. **Optional: TODO für nächste Session:**
```
\\Srvrdb01\...\Server\docs\TODO_FOR_CLAUDE_SESSION_START_TAG[X+1].md
```

---

## ⚠️ WICHTIGE REGELN

### ✅ DO:

- Immer aktuellstes SESSION_WRAP_UP lesen
- Dateien im Sync-Verzeichnis lesen/schreiben
- **Zuerst nach TEST deployen, dann nach PRODUKTIV**
- Backup vor größeren Änderungen: `datei.py` → `datei.py.bak_tagXX`
- Session-Wrap-Up am Ende erstellen
- User um Server-Befehle bitten (restart, git, etc.)

### ❌ DON'T:

- Project Knowledge für Session-Docs nutzen (veraltet!)
- rsync oder Massen-Sync vorschlagen (zu gefährlich!)
- Direkt auf Server zugreifen wollen (kein SSH möglich)
- SQLite-DB modifizieren ohne Backup
- Credentials in Code/Docs schreiben
- **Direkt nach PRODUKTIV deployen ohne Test!**

---

## 🛠️ TYPISCHE AUFGABEN

### **Bug fixen:**
1. User beschreibt Problem
2. Claude liest relevante Dateien
3. Claude analysiert und schlägt Fix vor
4. Claude schreibt geänderte Datei ins Sync-Verzeichnis
5. User kopiert nach **TEST** → testet → kopiert nach **PRODUKTIV**

### **Neues Feature:**
1. User beschreibt Anforderung
2. Claude liest bestehende Struktur
3. Claude erstellt neue Dateien (API, Template, etc.)
4. User kopiert nach **TEST** → testet iterativ
5. Wenn stabil → nach **PRODUKTIV**

### **Daten analysieren:**
1. User führt SQL-Query am Server aus
2. User postet Ergebnis
3. Claude analysiert und gibt Empfehlungen

### **Import-Script erstellen:**
1. Claude liest bestehende Parser/Scripts
2. Claude erstellt neues Script
3. User führt **am TEST-Server** aus (wenn riskant)
4. Validierung der Ergebnisse
5. Wenn OK → auf PRODUKTIV ausführen

---

## 📞 SCHNELLE REFERENZ

### Dateien lesen:
```
Filesystem:read_file
Pfad: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\[PFAD]
```

### Dateien schreiben:
```
Filesystem:write_file
Pfad: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\[PFAD]
Content: [INHALT]
```

### Verzeichnis listen:
```
Filesystem:list_directory
Pfad: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\[PFAD]
```

### Datei suchen:
```
Filesystem:search_files
Pfad: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
Pattern: [SUCHBEGRIFF]
```

---

## 🎯 ZUSAMMENFASSUNG

1. **Claude hat direkten Filesystem-Zugriff** auf das Sync-Verzeichnis
2. **NIEMALS rsync!** User kopiert einzelne Dateien mit `cp`
3. **TEST → PRODUKTIV Workflow:** Immer erst auf Port 5001 testen!
4. **Immer aktuellste Docs vom Sync-Verzeichnis lesen** (nicht Project Knowledge)
5. **SESSION_WRAP_UP am Ende jeder Session erstellen**
6. **Server-Befehle gibt User ein** (restart, git, SQL, cp)

---

*Aktualisiert: 2025-12-12 TAG 115 | Test-Umgebung hinzugefügt*
