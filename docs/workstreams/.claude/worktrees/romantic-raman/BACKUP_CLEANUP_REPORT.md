# Backup-Dateien Analyse - Greiner Portal

**Datum:** 2025-12-12
**Aktueller TAG:** 116+

---

## Gesamtübersicht

| Kategorie | Anzahl | Größe |
|-----------|--------|-------|
| **Backup-Extensions (.backup, .bak, .old)** | 57 | 0.6 MB |
| **Dateien mit _tag[Nummer]** | 198 | 1.46 MB |
| **Dateien mit Datum _202[0-9]** | 128 | 6.32 MB |
| **Dateien mit Version _v[Nummer]** | 86 | 8.12 MB |
| **Gesamtes backups/ Verzeichnis** | 456 | **57.09 MB** |
| **Verstreute Backups (außerhalb backups/)** | 136 | 1.61 MB |

**GESAMT: ~59 MB an Backup-Dateien**

---

## Backup-Verzeichnisse (backups/)

| Verzeichnis | Dateien | Größe | Status |
|-------------|---------|-------|--------|
| `cleanup_root_20251114_133046` | 108 | 0.73 MB | ✅ SICHER ZU LÖSCHEN |
| `cleanup_root_20251114_133153` | 107 | 0.73 MB | ✅ SICHER ZU LÖSCHEN |
| `cleanup_root_20251212` | 5 | 0.03 MB | ✅ SICHER ZU LÖSCHEN |
| `cleanup_tag82_20251125_081746` | 161 | 1.73 MB | ✅ SICHER ZU LÖSCHEN (jetzt TAG 116+) |
| `parsers_backup_tag59_end_20251118_163659` | 21 | 0.18 MB | ✅ SICHER ZU LÖSCHEN (jetzt TAG 116+) |
| `urlaubsplaner_v2` | 1 | 5.11 MB | ⚠️ DB-Backup vor V2 Migration - BEHALTEN |
| `app_backups` | 11 | 0.04 MB | ⚠️ PRÜFEN |
| `experimental` | 17 | 0.10 MB | ⚠️ PRÜFEN |
| `old_docs` | 2 | 0.02 MB | ✅ KANN WEG |
| `vacation_v2_old` | 2 | 0.01 MB | ✅ KANN WEG |
| Leere Verzeichnisse | 0 | 0 MB | ✅ KANN WEG |

---

## Verstreute Backup-Dateien (außerhalb backups/)

### Nach Verzeichnis sortiert:

| Verzeichnis | Anzahl | Größe | Empfehlung |
|-------------|--------|-------|------------|
| `templates/` | 31 | 0.42 MB | ✅ Alle löschen |
| `scripts/imports/` | 24 | 0.27 MB | ✅ Alle löschen |
| `api/` | 23 | 0.42 MB | ⚠️ `werkstatt_live_api.py.bak_awpreis` prüfen, Rest löschen |
| `parsers/` | 18 | 0.15 MB | ✅ Alle löschen |
| `tools/scrapers/` | 6 | 0.08 MB | ✅ Alle löschen |
| `routes/` | 6 | 0.02 MB | ✅ Alle löschen |
| `config/` | 5 | 0.01 MB | ⚠️ `credentials.json.bak` prüfen, Rest löschen |
| `static/js/` | 5 | 0.06 MB | ✅ Alle löschen |
| `parsers/old_parsers_do_not_use/` | 5 | 0.05 MB | ✅ Ganzes Verzeichnis löschen |
| `scripts/sync/` | 3 | 0.04 MB | ✅ Alle löschen |
| `auth/` | 2 | 0.03 MB | ✅ Alle löschen |
| `static/css/` | 2 | 0.01 MB | ✅ Alle löschen |
| Weitere | 6 | 0.05 MB | ✅ Alle löschen |

---

## Empfohlene Lösch-Aktionen

### 🟢 SEHR SICHER - Sofort löschen (4.9 MB):

```bash
# 1. Alte Cleanup-Verzeichnisse
rm -rf backups/cleanup_root_20251114_133046
rm -rf backups/cleanup_root_20251114_133153
rm -rf backups/cleanup_root_20251212
rm -rf backups/cleanup_tag82_20251125_081746
rm -rf backups/parsers_backup_tag59_end_20251118_163659
rm -rf backups/old_docs
rm -rf backups/vacation_v2_old
rm -rf backups/app.UNUSED_TAG24
rm -rf backups/cleanup_20251114_133243
rm -rf backups/reorganization_20251107_212246
```

**Gespart: ~4.9 MB**

### 🟡 SICHER - Nach kurzer Prüfung löschen (1.6 MB):

```bash
# 2. Alle verstreuten .backup/.bak/.old Dateien
find . -type f \( -name "*.backup" -o -name "*.bak" -o -name "*.old" \) \
  ! -path "./backups/*" \
  ! -path "./venv/*" \
  ! -name "credentials.json.bak" \
  ! -name "werkstatt_live_api.py.bak_awpreis" \
  -delete

# 3. Alte Template-Backups
rm templates/base.html.backup_*
rm templates/verkauf_*.backup_*
rm templates/dashboard_backup_tag116.html
rm templates/_backup_fahrzeugfinanzierungen_alt_tag116.html

# 4. API-Backups (außer die zwei geprüften)
rm api/bankenspiegel_api.py.backup*
rm api/verkauf_api.py.backup*
rm api/organization_api.py.backup*
rm api/stellantis_api.py.backup*
rm api/vacation_api.py.backup

# 5. Parser-Backups
rm parsers/*.backup*
rm -rf parsers/old_parsers_do_not_use

# 6. Scripts-Backups
rm scripts/imports/*.backup*
rm scripts/sync/*.backup*
```

**Gespart: ~1.6 MB**

### ⚠️ PRÜFEN ERFORDERLICH:

Diese Dateien vor dem Löschen prüfen:

1. **`api/werkstatt_live_api.py.bak_awpreis`** (59 KB)
   - Enthält möglicherweise wichtige AW-Preis-Logik
   - **Empfehlung:** Backup in `backups/app_backups/` verschieben

2. **`config/credentials.json.bak`** (2.7 KB)
   - Sensible Zugangsdaten
   - **Empfehlung:** Prüfen ob identisch mit aktueller Version, dann sicher löschen

3. **`templates/base.html.bak_leasys`** (13 KB)
   - Leasys-spezifische Anpassungen
   - **Empfehlung:** Falls Leasys-Modul noch aktiv ist, in backups/ verschieben

4. **`celery_app/tasks.py.bak_dup`** (11 KB)
   - Duplikat-Fix Backup
   - **Empfehlung:** Falls Celery stabil läuft, löschen

5. **`scheduler/job_definitions.py.broken_tag91`** (16.7 KB)
   - Kaputte Version aus TAG 91
   - **Empfehlung:** Löschen (jetzt TAG 116+)

---

## Dateien mit TAG/Datum-Suffixen (NICHT löschen)

Diese Dateien sind **KEINE Backups**, sondern aktive Scripts/Docs:

### Aktive Scripts:
- `scripts/cleanup_tag*.sh` - Cleanup-Scripts
- `scripts/import_*_tag*.py` - Import-Scripts für bestimmte TAGs
- `scripts/sync/sync_fibu_v2.*.py` - Versionierte Sync-Scripts
- `deploy_tag116.sh` - Aktuelles Deployment-Script

### Dokumentation (behalten):
- `docs/SESSION_WRAP_UP_TAG*.md` - Session-Zusammenfassungen
- `docs/TODO_FOR_CLAUDE_SESSION_START_TAG*.md` - Session-TODOs
- `docs/sessions/*.md` - Session-History

**Diese NICHT löschen - sind Teil der Projekt-Historie!**

---

## Zusammenfassung: Speicherplatz-Einsparung

| Aktion | Dateien | Speicherplatz |
|--------|---------|---------------|
| Sehr sicher löschen | ~300 | ~4.9 MB |
| Sicher löschen | ~130 | ~1.6 MB |
| Nach Prüfung löschen | ~20 | ~0.2 MB |
| **GESAMT** | **~450** | **~6.7 MB** |

**Verbleibend nach Cleanup:**
- Wichtige DB-Backups (urlaubsplaner_v2): 5.1 MB
- Experimentelle Backups: 0.1 MB
- Aktive Versionsskripts/Docs: ~50 MB (behalten!)

---

## Cleanup-Script

Ein fertiges Cleanup-Script finden Sie in:
```
scripts/maintenance/cleanup_all_backups.sh
```

**WICHTIG:** Vor Ausführung immer ein Gesamt-Backup erstellen:
```bash
cd /opt/greiner-portal
tar -czf /tmp/portal_backup_before_cleanup_$(date +%Y%m%d).tar.gz \
  --exclude='venv' --exclude='node_modules' --exclude='logs/*.log' .
```

---

**Ende des Reports**
