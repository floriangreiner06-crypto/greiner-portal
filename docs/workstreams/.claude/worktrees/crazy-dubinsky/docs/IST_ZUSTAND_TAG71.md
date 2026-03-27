# 📋 GREINER PORTAL - IST-ZUSTAND DOKUMENTATION TAG71

**Erstellt:** 21. November 2025, 10:45 Uhr  
**Branch:** develop  
**Letzter Commit:** ba3b1d9 (TAG70 - Stellantis ServiceBox Pagination-Scraper)  
**Status:** Service läuft (9 Worker, 198MB RAM), Git chaotisch

---

## 🎯 EXECUTIVE SUMMARY

**Was funktioniert:**
- ✅ Core-System (Flask, Auth, DBs) läuft stabil
- ✅ Controlling/Bankenspiegel produktiv (im letzten Chat gefixt)
- ✅ Import-System (MT940 + PDF für HypoVereinsbank)
- ✅ Stellantis Scraper produktiv (TAG70)

**Was in Testing:**
- 🧪 Urlaubsplaner V2 (Testing & Bugfix ausständig)

**Was auf Eis:**
- ❄️ FinTS-Integration (zu komplex, nicht weiterverfolgen)

**Was chaotisch:**
- 🔥 17 uncommitted Changes
- 🔥 45 untracked Files
- 🔥 Viele .bak/.broken-Files

---

## ✅ PRODUKTIVE FEATURES (LIVE & FUNKTIONIERT)

### **1. Core-System**
```
Status: ✅ PRODUKTIV
Version: Flask 3.x, Python 3.12
Uptime: Seit 10:09 (21.11.2025)

Komponenten:
├── Flask-App (Gunicorn, 9 Worker, 198MB RAM)
├── SQLite-DB (27MB)
│   ├── 12 Konten
│   ├── 14.311 Transaktionen
│   ├── 549.224 Fibu-Buchungen
│   └── 4.912 Sales
├── LDAP-Auth (Security-Bug gefixt)
├── PostgreSQL-Sync (Locosoft extern)
└── Apache Reverse Proxy (Port 80 → 5000)

Server: 10.80.80.20 (srvlinux01)
User: ag-admin
Path: /opt/greiner-portal
```

### **2. Controlling / Bankenspiegel** 💰
```
Status: ✅ PRODUKTIV (im letzten Chat gefixt)
Commit: 301320f + uncommitted fixes

Features:
├── Dashboard (Executive Phase 1 komplett)
│   ├── Multi-Entity Support
│   ├── Gesellschafter-Toggle (TAG67-68)
│   ├── KPIs: Liquidität, Kreditlinien, Zinsen
│   ├── Auto-Refresh (60s)
│   └── Währungs-Formatierung
├── Konten-Übersicht (12 aktive Konten)
├── Transaktions-Import
├── Zinsverfolgung
├── Einkaufsfinanzierung (199 Fahrzeuge, 5,36 Mio. EUR)
└── Fahrzeugfinanzierungen (3 Banken)

Files:
├── api/bankenspiegel_api.py (modified, fix uncommitted)
├── routes/controlling_routes.py (modified, fix uncommitted)
├── templates/controlling/dashboard.html (modified)
└── static/js/controlling/dashboard.js (modified)

Action Required: Uncommitted changes committen!
```

### **3. Import-System** 📥
```
Status: ✅ PRODUKTIV

MT940-Import (Sparkasse, VR Bank, Genobank):
├── sparkasse_online_parser.py (TAG60/63)
├── genobank_universal_parser.py (2 Formate)
├── vrbank_parser.py (TAG40)
└── parser_factory.py (IBAN-basierte Auswahl v1.2)

PDF-Import (HypoVereinsbank):
├── hypovereinsbank_parser.py (funktioniert)
└── Spezial-Logik für HVB (keine MT940)

Locosoft-Sync (PostgreSQL extern):
├── Fibu-Buchungen (549.224 Einträge)
├── Sales-Daten (4.912 Einträge)
└── Mitarbeiter-Daten

Letzter Import: TAG64 (Komplett-Import 2025)
Import-Status November: Teilweise (prüfen!)
```

### **4. Parser-System** 📄
```
Status: ✅ PRODUKTIV

Parser (alle funktionsfähig):
├── base_parser.py (Basis-Klasse)
├── sparkasse_online_parser.py (MT940)
├── genobank_universal_parser.py (MT940, 2 Formate)
├── hypovereinsbank_parser.py (PDF)
├── vrbank_parser.py (MT940)
├── santander_parser.py (Snapshots für Darlehen)
└── parser_factory.py (IBAN-Factory v1.2)

Besonderheiten:
- Genobank: 2 Formate automatisch erkannt
- HypoVereinsbank: PDF statt MT940
- Santander: Snapshot-System (keine Transaktionen)

Action Required: sparkasse_online_parser.py hat uncommitted changes
```

### **5. Verkauf** 📊
```
Status: ✅ PRODUKTIV

Daten:
├── 4.912 Sales-Einträge
├── Auftragseingang-Tracking
├── Auslieferungs-Tracking
└── Verkäufer-Performance

Integration:
├── Locosoft-Sync (täglich?)
└── Dashboard-KPIs (noch statisch)

Action Required: Status-Check ob Sync läuft
```

### **6. Stellantis ServiceBox Scraper** 🚗
```
Status: ✅ PRODUKTIV (TAG70 komplett)

Features:
├── Pagination-Scraper (100 Bestellungen getestet)
├── 2-Phasen-Scraper (Phase 1: URLs sammeln, Phase 2: Details)
├── Button-Validierung ("Mehr Bestellungen anzeigen")
├── Detail-Extraktion (Teilenummern, Preise, etc.)
├── JSON-Export
├── Duplikat-Entfernung
├── Progress-Speicherung
└── Screenshot-Debugging

Dateien:
├── tools/scrapers/servicebox_detail_scraper_pagination_final.py (PRODUKTIV)
├── logs/servicebox_bestellungen_details_complete.json (Output)
└── logs/servicebox_scraper_progress.json (Progress)

Ergebnis TAG70: 100 Bestellungen, 181 Positionen, 0 Fehler
Potenzial: 1315 Bestellungen total (MAX_PAGES = 150)

Action Required: Alle 1315 Bestellungen scrapen? (Option C)
```

---

## 🧪 IN TESTING (FUNKTIONIERT, ABER BUGFIX NÖTIG)

### **7. Urlaubsplaner V2** 📅
```
Status: 🧪 TESTING (v2 ist aktuell, v1 deprecated)
Version: V2 (neu entwickelt)
Entwicklung: TAG66-69

Features (geplant):
├── Urlaubsanträge stellen
├── Genehmigungsprozess
├── Team-Übersicht (für Manager)
├── Urlaubsguthaben-Anzeige
├── Feiertage
└── Audit-Log

Dateien:
├── api/vacation_api.py (modified, uncommitted)
├── static/js/vacation_manager.js (modified, uncommitted)
├── templates/base.html (modified für Navigation)
└── vacation_v2/ (neues Modul)

Backup-Files vorhanden:
├── api/vacation_api.py.bak_tag69
├── static/js/vacation_manager.js.bak_tag69
└── templates/base.html.bak_tag69

Action Required:
1. Testing durchführen (alle Funktionen prüfen)
2. Bugs identifizieren und fixen
3. Changes committen
4. V1 deprecaten/löschen
5. Dokumentation schreiben

Zeitaufwand: 2-3 Stunden
```

---

## ❄️ ON HOLD (NICHT WEITERVERFOLGEN)

### **8. FinTS-Integration** 🏦
```
Status: ❄️ ON HOLD
Grund: Zu komplex, MT940 + PDF-Parser reichen aus
Decision: Auf Eis gelegt, nicht löschen (für später)

Dateien:
├── fints-package/ (komplettes Modul)
├── api/fints_connector.py
├── scripts/imports/import_fints_daily.py
├── scripts/checks/check_fints_health.sh
└── migrations/008-013*.sql (FinTS-related, 6 Migrations)

Warum erstellt?
- Sollte automatische Bank-Abfragen ermöglichen
- Zu viele Edge-Cases, zu instabil
- MT940-Export + PDF-Parser funktionieren besser

Action Required:
1. Ordner behalten (für später)
2. Aus Git entfernen (untracked lassen)
3. Nach backups/experimental/fints/ verschieben
4. In EXPERIMENTAL_FEATURES.md dokumentieren

Zeitaufwand: 10 Minuten
```

---

## 🗑️ DEPRECATED (KANN WEG)

### **9. Alte Versionen / Backups**

#### **Backup-Files (können gelöscht werden):**
```bash
# Core-Backups (Bugs gefixt)
api/bankenspiegel_api.py.broken_tag71      # ← Gefixt im letzten Chat
auth/auth_manager.py.bak_SECURITY_BUG      # ← Security-Bug ist gefixt

# Controlling-Backups (TAG67-68)
routes/controlling_routes.py.bak_tag67
routes/controlling_routes.py.bak_tag68_vor_bereinigung

# Urlaubsplaner-Backups (TAG69)
api/vacation_api.py.bak_tag69
static/js/vacation_manager.js.bak_tag69
templates/base.html.bak_tag69
```

#### **Alte Scraper-Versionen (deprecated):**
```bash
# Entwicklungs-Versionen TAG69-70
tools/scrapers/servicebox_detail_scraper.py              # ← Veraltet
tools/scrapers/servicebox_detail_scraper.py.old          # ← Backup
tools/scrapers/servicebox_detail_scraper_debug.py        # ← Debug-Version
tools/scrapers/servicebox_detail_scraper_2phase.py.bak_tag70_v1
tools/scrapers/servicebox_detail_scraper_2phase_v1.py
tools/scrapers/servicebox_detail_scraper_2phase_v2.py
tools/scrapers/servicebox_detail_scraper_2phase_v2_fixed.py
tools/scrapers/servicebox_detail_scraper_final.py.bak_tag69
tools/scrapers/servicebox_detail_scraper_with_pagination.py
tools/scrapers/servicebox_detail_scraper_with_pagination.py.bak
tools/scrapers/servicebox_test_scraper.py
tools/scrapers/servicebox_test_scraper_v3.py

# Produktive Version (behalten!):
tools/scrapers/servicebox_detail_scraper_pagination_final.py  # ← PRODUKTIV
```

#### **Alte Stellantis-Importer (deprecated):**
```bash
scripts/imports/import_stellantis_v2_backup.py
scripts/imports/import_stellantis_v3.py
scripts/imports/import_stellantis_v3_fixed.py

# Welche Version ist produktiv? Prüfen!
```

#### **Alte Session-Docs (archivieren):**
```bash
SESSION_WRAP_UP_TAG63.md                    # ← Veraltet (jetzt TAG71)
TODO_FOR_CLAUDE_SESSION_START_TAG66.md     # ← Veraltet

# Action: Nach docs/sessions/ verschieben
```

#### **Test-Scripts (löschen):**
```bash
install_hvb_parser.py      # ← War ein Test-Script
debug_vacation_api.py      # ← Debug-Script
```

---

## 📊 GIT-STATUS DETAILANALYSE

### **Modified Files (17) - Kategorisierung**

#### **✅ WICHTIG - COMMITTEN:**
```bash
# Controlling-Fixes (letzter Chat)
api/bankenspiegel_api.py                    # ← Dashboard-Fix
routes/controlling_routes.py               # ← Multi-Entity-Fix
static/js/controlling/dashboard.js         # ← Frontend-Fix
templates/controlling/dashboard.html       # ← Frontend-Fix

# Urlaubsplaner V2 (Testing)
api/vacation_api.py                        # ← V2 Testing-Version
static/js/vacation_manager.js              # ← V2 Frontend
templates/base.html                        # ← Navigation für V2

# Parser-Improvements
parsers/sparkasse_online_parser.py         # ← MT940 Verbesserungen

# Auth-Fix
auth/auth_manager.py                       # ← Security-Bug gefixt

# App-Core
app.py                                     # ← Core-Updates
```

#### **⚠️ PRÜFEN - EVTL. COMMITTEN:**
```bash
# Import-Scripts (unklar welche Version aktuell ist)
scripts/imports/import_2025_v2_with_genobank.py
scripts/imports/import_complete_2025.py

# Stellantis Scraper (wahrscheinlich produktiv)
tools/scrapers/servicebox_detail_scraper_pagination_final.py
```

#### **🗑️ LÖSCHEN - NICHT WICHTIG:**
```bash
# Git möchte diese Files löschen (bestätigen)
deleted: =                                  # ← Datei "=" (?)
deleted: L394PR-ALTERNATIVKONTEN-OPEL-01-001.csv  # ← Alte CSV
deleted: SERVER_STATUS.txt                  # ← Alte Status-Datei
deleted: cron_backup_tag43.txt              # ← Alter Cron-Backup
deleted: server_status_check.sh             # ← Altes Script (neu in scripts/maintenance/)
```

### **Untracked Files (45) - Kategorisierung**

#### **✅ COMMITTEN:**
```bash
# Migrations (wichtig!)
migrations/tag67_schema_migration.sql       # ← Multi-Entity Schema
migrations/tag67_update_konten_daten.sql    # ← Konten-Kategorisierung

# Maintenance-Script
scripts/maintenance/server_status_check.sh  # ← Neues Script (gut!)

# Cron-Config
crontab_final_tag65.txt                     # ← Dokumentation

# Session-Docs (archivieren, nicht committen)
SESSION_WRAP_UP_TAG63.md                    # ← In docs/sessions/ verschieben
TODO_FOR_CLAUDE_SESSION_START_TAG66.md     # ← In docs/sessions/ verschieben
```

#### **📦 VERSCHIEBEN NACH backups/experimental/:**
```bash
# FinTS (on hold)
fints-package/                              # ← Komplettes Modul
api/fints_connector.py
scripts/imports/import_fints_daily.py
scripts/checks/check_fints_health.sh
migrations/008_add_finanzinstitut_compat.sql
migrations/009_add_missing_import_columns.sql
migrations/010_add_all_import_columns.sql
migrations/011_remove_finanzbank_id_constraint.sql
migrations/012_fix_trigger_and_constraints.sql
migrations/013_emergency_recreate_table.sql

# Debugging (temporary)
debug_vacation_api.py
```

#### **🗑️ LÖSCHEN:**
```bash
# Backup-Files (deprecated)
api/bankenspiegel_api.py.broken_tag71
auth/auth_manager.py.bak_SECURITY_BUG
routes/controlling_routes.py.bak_tag67
routes/controlling_routes.py.bak_tag68_vor_bereinigung
api/vacation_api.py.bak_tag69
static/js/vacation_manager.js.bak_tag69
templates/base.html.bak_tag69

# Alte Scraper-Versionen (12 Dateien)
tools/scrapers/servicebox_detail_scraper.py
tools/scrapers/servicebox_detail_scraper.py.old
tools/scrapers/servicebox_detail_scraper_2phase.py.bak_tag70_v1
tools/scrapers/servicebox_detail_scraper_2phase_v1.py
tools/scrapers/servicebox_detail_scraper_2phase_v2.py
tools/scrapers/servicebox_detail_scraper_2phase_v2_fixed.py
tools/scrapers/servicebox_detail_scraper_debug.py
tools/scrapers/servicebox_detail_scraper_final.py.bak_tag69
tools/scrapers/servicebox_detail_scraper_with_pagination.py
tools/scrapers/servicebox_detail_scraper_with_pagination.py.bak
tools/scrapers/servicebox_test_scraper.py
tools/scrapers/servicebox_test_scraper_v3.py

# Alte Stellantis-Importer (3 Dateien)
scripts/imports/import_stellantis_v2_backup.py
scripts/imports/import_stellantis_v3.py
scripts/imports/import_stellantis_v3_fixed.py

# Test-Scripts
install_hvb_parser.py
```

---

## 🎯 EMPFOHLENE ACTIONS

### **SOFORT (vor weiterer Entwicklung):**

1. ✅ **BACKUP ERSTELLEN** (5 Min)
2. ✅ **CLEANUP DURCHFÜHREN** (20 Min)
3. ✅ **GIT COMMITTEN** (10 Min)
4. ✅ **STATUS DOKUMENTIEREN** (Diese Datei!)

### **DANN ENTSCHEIDEN:**

**Option A:** Urlaubsplaner V2 fertigmachen (2-3 Std)  
**Option B:** Controlling weiter ausbauen (2-3 Std)  
**Option C:** Stellantis komplett importieren (4-5 Std)  
**Option D:** Dokumentation vervollständigen (1-2 Std)

---

## 📋 ZUSAMMENFASSUNG

### **✅ Was läuft gut:**
- Core-System stabil
- Controlling produktiv
- Import-System funktioniert
- Stellantis Scraper produktiv

### **⚠️ Was chaotisch ist:**
- Git-Status (62 uncommitted/untracked files)
- Viele Backup-Files
- Unklare Versionen

### **🎯 Was zu tun ist:**
1. Cleanup (diese Dokumentation + CLEANUP_COMMANDS_TAG71.sh)
2. Committen (sauberer Stand)
3. Entscheiden (nächster Feature-Focus)

---

## 📞 SUPPORT

**Bei Fragen zu dieser Dokumentation:**
- Siehe: CLEANUP_COMMANDS_TAG71.sh (Schritt-für-Schritt)
- Siehe: DECISION_TREE_TAG71.md (Was als nächstes?)
- Oder: Neuen Claude-Chat starten mit dieser Datei

---

**Erstellt:** 21. November 2025  
**Von:** Claude (TAG71)  
**Status:** ✅ KOMPLETT

---

*Diese Dokumentation ist der aktuelle IST-ZUSTAND des Greiner Portals.  
Sie dient als Basis für alle weiteren Entwicklungen und Entscheidungen.*
