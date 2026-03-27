# VERZEICHNISSTRUKTUR - GREINER PORTAL

**Datum:** 07.11.2025  
**Version:** 2.0 (nach Reorganisation)

---

## 🎯 ZIELSETZUNG

Diese Reorganisation schafft eine **saubere, wartbare Struktur** mit klarer Trennung von:
- Produktivem Code
- Utility-Scripts
- Tests
- Dokumentation
- Logs & Backups

---

## 📁 NEUE STRUKTUR

```
/opt/greiner-portal/
│
├── 🔷 PRODUKTIV-CODE (Framework & Core)
│   ├── api/                      Flask-API-Routen
│   ├── app/                      Frontend/Web-App
│   ├── config/                   Konfigurationsdateien
│   ├── migrations/               Datenbank-Migrationen
│   ├── parsers/                  PDF-Parser (Sparkasse, VRBank, Hypo)
│   ├── routes/                   Flask-Routes
│   ├── static/                   CSS, JS, Images
│   ├── templates/                HTML-Templates (Jinja2)
│   ├── venv/                     Python Virtual Environment
│   │
│   ├── app.py                    ✅ Haupt-App (Flask)
│   ├── bankenspiegel_api.py      ✅ Bankenspiegel-API
│   ├── transaction_manager.py    ✅ DB-Transaktions-Manager
│   └── requirements.txt          ✅ Python-Dependencies
│
├── 📦 SCRIPTS (Utility & Automation)
│   ├── analysis/                 Analyse-Scripts
│   │   ├── analyze_employees.py
│   │   ├── analyze_locosoft_absence.py
│   │   ├── check_db_status.py
│   │   └── show_departments.py
│   │
│   ├── imports/                  Import-Scripts ✅ WICHTIG
│   │   ├── import_bank_pdfs.py              # Allgemeiner PDF-Import
│   │   ├── import_november_all_accounts_v2.py  # ✅ PRODUKTIV (IBAN-basiert)
│   │   ├── import_stellantis.py             # ✅ PRODUKTIV (ZIP-Import)
│   │   ├── pdf_importer.py                  # Import-Manager
│   │   └── genobank_universal_parser.py     # ✅ PRODUKTIV (Universal-Parser)
│   │
│   ├── tests/                    Test-Scripts
│   │   ├── test_bankenspiegel_api.sh
│   │   ├── test_locosoft.py
│   │   └── test_vacation_api.py
│   │
│   ├── setup/                    Setup & Installation
│   │   ├── install.sh
│   │   ├── phase1_tag1_setup.sh
│   │   └── setup_vacation_*.py
│   │
│   ├── fixes/                    Bug-Fix-Scripts
│   │   ├── fix_app_py.py
│   │   └── fix_vacation_views.py
│   │
│   ├── patches/                  API-Patches
│   │   └── patch_api_interne_transfers.py
│   │
│   ├── checks/                   Validierungs-Scripts
│   │   ├── check_locosoft_arbeitszeitkonto.py
│   │   └── check_locosoft_vacation.py
│   │
│   ├── validate_salden.sh        ✅ PRODUKTIV (Salden-Check)
│   └── README.md                 Script-Dokumentation
│
├── 📚 DOCS (Dokumentation)
│   ├── sessions/                 Session Wrap-Ups
│   │   ├── SESSION_WRAP_UP_TAG02.md
│   │   ├── SESSION_WRAP_UP_TAG03.md
│   │   ├── SESSION_WRAP_UP_TAG13.md
│   │   ├── SESSION_WRAP_UP_TAG14.md
│   │   └── SESSION_WRAP_UP_TAG15.md (neu)
│   │
│   ├── README_BANKENSPIEGEL_API.md
│   ├── README_NOVEMBER_IMPORT.md
│   ├── INSTALLATION_ANLEITUNG.md
│   ├── BUG_FIX_REPORT_TAG14.md
│   └── README.md                 Docs-Index
│
├── 📝 LOGS (Log-Dateien)
│   ├── imports/                  Import-Logs
│   │   ├── november_import.log
│   │   ├── bank_import.log
│   │   └── import_*.log
│   └── (weitere Logs)
│
├── 💾 BACKUPS (Backup-Dateien)
│   ├── reorganization_*/         Reorganisations-Backups
│   └── *.backup                  Datei-Backups
│
├── 💽 DATA (Datenbanken & Daten)
│   └── greiner_controlling.db    ✅ Haupt-Datenbank (49.781 Trans.)
│
├── 🔗 SYMLINKS (Kompatibilität)
│   ├── import_november_all_accounts_v2.py → scripts/imports/
│   ├── import_stellantis.py → scripts/imports/
│   └── validate_salden.sh → scripts/
│
└── 📄 ROOT-DATEIEN
    ├── README.md                 ✅ Haupt-README
    └── .gitignore
```

---

## 🎯 VORTEILE DER NEUEN STRUKTUR

### 1. Klarheit
- ✅ Produktiv-Code vs. Scripts getrennt
- ✅ Scripts nach Funktion organisiert
- ✅ Dokumentation zentralisiert

### 2. Wartbarkeit
- ✅ Einfaches Auffinden von Scripts
- ✅ Neue Scripts haben klaren Platz
- ✅ Logs & Backups getrennt

### 3. Kompatibilität
- ✅ Symlinks erhalten alte Pfade
- ✅ Keine Code-Änderungen nötig
- ✅ Cronjobs funktionieren weiter

### 4. Professionalität
- ✅ Best-Practice Struktur
- ✅ Git-freundlich
- ✅ Team-ready

---

## 🔄 MIGRATION

### Schritt 1: Backup erstellen
```bash
cd /opt/greiner-portal
tar -czf ~/greiner_portal_backup_$(date +%Y%m%d).tar.gz .
```

### Schritt 2: Reorganisations-Script ausführen
```bash
chmod +x reorganize_structure.sh
./reorganize_structure.sh
```

### Schritt 3: Tests durchführen
```bash
# Status prüfen
python3 scripts/analysis/check_db_status.py

# Import testen
python3 scripts/imports/import_november_all_accounts_v2.py --dry-run

# Salden validieren
./validate_salden.sh  # Symlink funktioniert noch!
```

### Schritt 4: Git-Commit
```bash
git status
git add .
git commit -m "chore: Reorganize directory structure for better maintainability"
```

---

## 📖 WICHTIGE PFADE

### Produktiv-Scripts (täglich genutzt)
```bash
# November-Import (IBAN-basiert)
python3 scripts/imports/import_november_all_accounts_v2.py

# Stellantis-Import
python3 scripts/imports/import_stellantis.py

# Salden validieren
./validate_salden.sh  # oder: scripts/validate_salden.sh

# DB-Status prüfen
python3 scripts/analysis/check_db_status.py
```

### Dokumentation
```bash
# Session Wrap-Ups
docs/sessions/SESSION_WRAP_UP_TAG*.md

# API-Doku
docs/README_BANKENSPIEGEL_API.md

# Installation
docs/INSTALLATION_ANLEITUNG.md
```

### Logs
```bash
# Import-Logs
tail -f logs/imports/november_import.log

# Alle Logs
ls -lh logs/imports/
```

---

## 🔗 SYMLINKS FÜR KOMPATIBILITÄT

Um bestehende Cronjobs und Scripts nicht zu brechen, wurden Symlinks erstellt:

```bash
/opt/greiner-portal/import_november_all_accounts_v2.py
    → scripts/imports/import_november_all_accounts_v2.py

/opt/greiner-portal/import_stellantis.py
    → scripts/imports/import_stellantis.py

/opt/greiner-portal/validate_salden.sh
    → scripts/validate_salden.sh
```

**Bedeutet:** Alte Befehle funktionieren weiterhin!

---

## ⚠️ WICHTIGE HINWEISE

### 1. Cronjobs anpassen (Optional)
Falls Cronjobs existieren, können diese auf neue Pfade umgestellt werden:

**Alt:**
```cron
0 8 * * * /opt/greiner-portal/import_november_all_accounts_v2.py
```

**Neu (empfohlen):**
```cron
0 8 * * * /opt/greiner-portal/scripts/imports/import_november_all_accounts_v2.py
```

### 2. Code-Imports anpassen
Falls Python-Scripts andere Scripts importieren:

**Alt:**
```python
from import_stellantis import StellantisImporter
```

**Neu:**
```python
from scripts.imports.import_stellantis import StellantisImporter
```

**ABER:** Durch Symlinks funktioniert beides!

### 3. Backup-Wiederherstellung
Falls Probleme auftreten:

```bash
cd /opt/greiner-portal
# Alle Dateien löschen (außer Backup)
rm -rf scripts/ docs/ logs/

# Backup zurückspielen
tar -xzf ~/greiner_portal_backup_YYYYMMDD.tar.gz
```

---

## 📊 VORHER/NACHHER

### Vorher (Chaos)
```
/opt/greiner-portal/
├── analyze_employees.py          ❌ Durcheinander
├── import_bank_pdfs.py           ❌ Durcheinander
├── test_locosoft.py              ❌ Durcheinander
├── SESSION_WRAP_UP_TAG13.md      ❌ Durcheinander
├── november_import.log           ❌ Durcheinander
├── app.py.backup_20251107_111258 ❌ Durcheinander
└── ... (100+ Dateien im Root)
```

### Nachher (Ordnung)
```
/opt/greiner-portal/
├── api/                          ✅ Framework-Code
├── scripts/                      ✅ Alle Scripts organisiert
│   ├── analysis/                 ✅ Analyse
│   ├── imports/                  ✅ Imports
│   └── tests/                    ✅ Tests
├── docs/                         ✅ Dokumentation
├── logs/                         ✅ Logs
├── backups/                      ✅ Backups
└── data/                         ✅ Datenbanken
```

---

## ✅ CHECKLISTE NACH REORGANISATION

- [ ] Reorganisations-Script ausgeführt
- [ ] Git-Status geprüft
- [ ] Wichtigste Scripts getestet
- [ ] Symlinks funktionieren
- [ ] Logs im richtigen Verzeichnis
- [ ] Dokumentation gefunden
- [ ] Backup erstellt
- [ ] Git-Commit durchgeführt

---

## 🚀 NÄCHSTE SCHRITTE

Nach erfolgreicher Reorganisation:

1. **Tag 15 Scripts** in korrekte Verzeichnisse:
   - `import_sparkasse_november.py` → `scripts/imports/`
   - `import_hypovereinsbank_november.py` → `scripts/imports/`
   - `check_november_status.py` → `scripts/analysis/`

2. **Neue Session-Dokumentation**:
   - `SESSION_WRAP_UP_TAG15.md` → `docs/sessions/`

3. **Git-Workflow**:
   ```bash
   git add scripts/ docs/ logs/
   git commit -m "feat(tag15): Add November import scripts for Sparkasse & Hypo"
   git push
   ```

---

## 📞 SUPPORT

Bei Fragen oder Problemen:
1. Prüfen Sie die README-Dateien in den Unterverzeichnissen
2. Schauen Sie in `docs/sessions/` für historischen Kontext
3. Prüfen Sie Symlinks: `ls -la | grep "^l"`

---

**Stand:** 07.11.2025 - Bereitet vor für Tag 15 ✨
