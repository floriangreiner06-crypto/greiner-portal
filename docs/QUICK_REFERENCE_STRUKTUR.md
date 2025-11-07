# QUICK REFERENCE - NEUE VERZEICHNISSTRUKTUR

**Datum:** 07.11.2025

---

## 🎯 HÄUFIG GENUTZTE BEFEHLE

### Import-Scripts
```bash
# November-Import (V2 - IBAN-basiert) ✅ PRODUKTIV
python3 scripts/imports/import_november_all_accounts_v2.py

# Stellantis-Import ✅ PRODUKTIV
python3 scripts/imports/import_stellantis.py

# Bank-PDFs importieren
python3 scripts/imports/import_bank_pdfs.py import /pfad/zu/pdfs
```

### Analyse & Status
```bash
# Datenbank-Status
python3 scripts/analysis/check_db_status.py

# November-Status (TAG 15 - NEU)
python3 scripts/analysis/check_november_status.py

# Sparkasse November-Import (TAG 15 - NEU)
python3 scripts/imports/import_sparkasse_november.py
```

### Validierung
```bash
# Salden validieren
./validate_salden.sh
# oder: scripts/validate_salden.sh
```

### Logs anschauen
```bash
# Import-Logs
tail -f logs/imports/november_import.log
tail -f logs/imports/bank_import.log

# Alle Import-Logs
ls -lh logs/imports/
```

### Dokumentation
```bash
# Session Wrap-Ups
less docs/sessions/SESSION_WRAP_UP_TAG14.md
less docs/sessions/SESSION_WRAP_UP_TAG15.md

# API-Dokumentation
less docs/README_BANKENSPIEGEL_API.md

# Verzeichnisstruktur
less docs/VERZEICHNISSTRUKTUR.md
```

---

## 📁 WO FINDE ICH WAS?

| Was?                  | Wo?                           |
|-----------------------|-------------------------------|
| Import-Scripts        | `scripts/imports/`            |
| Analyse-Scripts       | `scripts/analysis/`           |
| Test-Scripts          | `scripts/tests/`              |
| Session-Dokumentation | `docs/sessions/`              |
| API-Dokumentation     | `docs/README_*.md`            |
| Import-Logs           | `logs/imports/`               |
| Backups               | `backups/`                    |
| Datenbank             | `data/greiner_controlling.db` |

---

## 🔧 NEUE SCRIPTS HINZUFÜGEN

### Import-Script
```bash
# Erstellen
nano scripts/imports/mein_import.py

# Testen
python3 scripts/imports/mein_import.py --dry-run

# Produktiv nutzen
python3 scripts/imports/mein_import.py
```

### Analyse-Script
```bash
# Erstellen
nano scripts/analysis/meine_analyse.py

# Ausführen
python3 scripts/analysis/meine_analyse.py
```

### Dokumentation
```bash
# Session Wrap-Up
nano docs/sessions/SESSION_WRAP_UP_TAG16.md

# Feature-Doku
nano docs/README_MEIN_FEATURE.md
```

---

## 🔗 SYMLINKS (für Kompatibilität)

Diese alten Pfade funktionieren noch:
```bash
# Alt (funktioniert)
./import_november_all_accounts_v2.py

# Neu (empfohlen)
python3 scripts/imports/import_november_all_accounts_v2.py
```

**Warum?** Symlink im Root zeigt auf `scripts/imports/`

---

## 🚨 TROUBLESHOOTING

### "Script nicht gefunden"
```bash
# Prüfe, ob Script existiert
ls -lh scripts/imports/import_*.py

# Prüfe Symlinks
ls -la | grep "^l"
```

### "Import-Fehler in Python"
```bash
# Virtual Environment aktivieren
cd /opt/greiner-portal
source venv/bin/activate

# Dependencies prüfen
pip list | grep pdfplumber
```

### "Datei verschwunden nach Reorganisation"
```bash
# Suche in neuer Struktur
find /opt/greiner-portal -name "mein_script.py"

# Backup prüfen
ls -lh backups/reorganization_*/
```

---

## 📊 VERGLEICH ALT/NEU

| Alt (Root)                          | Neu (organisiert)                                |
|-------------------------------------|--------------------------------------------------|
| `import_stellantis.py`              | `scripts/imports/import_stellantis.py`           |
| `analyze_employees.py`              | `scripts/analysis/analyze_employees.py`          |
| `test_locosoft.py`                  | `scripts/tests/test_locosoft.py`                 |
| `SESSION_WRAP_UP_TAG13.md`          | `docs/sessions/SESSION_WRAP_UP_TAG13.md`         |
| `november_import.log`               | `logs/imports/november_import.log`               |
| `app.py.backup_20251107_111258`     | `backups/app.py.backup_20251107_111258`          |

---

## ✅ CHECKLISTE FÜR TÄGLICHE ARBEIT

### Morgens (Status-Check)
- [ ] `python3 scripts/analysis/check_db_status.py`
- [ ] `tail -20 logs/imports/november_import.log`
- [ ] `./validate_salden.sh`

### Import durchführen
- [ ] `python3 scripts/imports/import_november_all_accounts_v2.py --dry-run`
- [ ] `python3 scripts/imports/import_november_all_accounts_v2.py`
- [ ] `./validate_salden.sh`

### Abends (Dokumentation)
- [ ] Logs prüfen: `ls -lh logs/imports/`
- [ ] Git-Status: `git status`
- [ ] Ggf. Session Wrap-Up aktualisieren

---

## 🎓 TIPS & TRICKS

### 1. Aliase einrichten
```bash
# In ~/.bashrc
alias greiner='cd /opt/greiner-portal && source venv/bin/activate'
alias nov-import='python3 scripts/imports/import_november_all_accounts_v2.py'
alias db-status='python3 scripts/analysis/check_db_status.py'
alias salden='./validate_salden.sh'
```

### 2. Tab-Completion nutzen
```bash
# Einfach tippen und TAB drücken
python3 scripts/im<TAB>
# → Zeigt alle Scripts in scripts/imports/
```

### 3. Scripts als ausführbar markieren
```bash
chmod +x scripts/imports/*.py
chmod +x scripts/analysis/*.py
```

---

## 📚 WEITERFÜHRENDE DOKU

- **Vollständige Struktur:** `docs/VERZEICHNISSTRUKTUR.md`
- **Reorganisations-Script:** `reorganize_structure.sh`
- **Session Wrap-Ups:** `docs/sessions/SESSION_WRAP_UP_TAG*.md`

---

**Hinweis:** Diese Quick Reference ist für die tägliche Arbeit gedacht. Für Details siehe die vollständige Dokumentation in `docs/`.
