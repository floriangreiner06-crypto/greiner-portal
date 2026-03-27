# Hypovereinsbank Import-Fix TAG 165

**Datum:** 2026-01-04  
**Problem:** Hypovereinsbank-Auszüge aktualisieren sich nicht  
**Ursache:** Import-Skript verwendete noch SQLite statt PostgreSQL  
**Status:** ✅ Behoben

---

## Problem

Das Import-Skript `scripts/imports/import_all_bank_pdfs.py` verwendete noch die **alte SQLite-Datenbank** (`/opt/greiner-portal/data/greiner_controlling.db`), obwohl das System auf **PostgreSQL** migriert wurde (TAG 135-139).

**Folge:** Hypovereinsbank-Auszüge wurden nicht in die PostgreSQL-Datenbank importiert, sondern (falls überhaupt) in die alte SQLite-DB.

---

## Lösung

### 1. Import-Skript auf PostgreSQL umgestellt

**Datei:** `scripts/imports/import_all_bank_pdfs.py`

**Änderungen:**
- ❌ `import sqlite3` entfernt
- ❌ `sqlite3.connect(DB_PATH)` entfernt
- ✅ `from api.db_connection import get_db, sql_placeholder, get_db_type` hinzugefügt
- ✅ `get_db()` statt `sqlite3.connect()` verwendet
- ✅ SQL-Syntax angepasst:
  - `?` → `%s` (via `sql_placeholder()`)
  - `SUBSTR()` → `SUBSTRING()` für PostgreSQL
- ✅ Row-Zugriff angepasst (HybridRow unterstützt Index UND Dict)
- ✅ Fehlerbehandlung mit `try/finally` für sauberes Connection-Handling

**Version:** 1.0 → 2.0 (TAG 165)

---

## Prüfungen

### 1. Datenstand prüfen

**Auf Server ausführen:**
```bash
cd /opt/greiner-portal
python3 scripts/tests/check_hvb_datenstand.py
```

**Erwartete Ausgabe:**
- Konto-Info (ID, Name, IBAN, Aktiv)
- Anzahl Transaktionen
- Letzte Buchung (Datum)
- Alter der letzten Buchung (Tage)
- Letzte 5 Transaktionen
- Salden-Info
- View `v_aktuelle_kontostaende` Status

**Interpretation:**
- ✅ Letzte Buchung < 1 Tag alt → Daten aktuell
- ⚠️ Letzte Buchung 1-3 Tage alt → Daten veraltet
- ❌ Letzte Buchung > 3 Tage alt → Daten stark veraltet

---

### 2. Celery-Task prüfen

**Task:** `import_hvb_pdf` in `celery_app/tasks.py`

```python
@shared_task(bind=True, max_retries=2, soft_time_limit=180)
def import_hvb_pdf(self):
    """HypoVereinsbank PDF Import"""
    return run_script('scripts/imports/import_all_bank_pdfs.py', timeout=120)
```

**Status:** ✅ Konfiguration korrekt

**Hinweis:** Die Task ruft `import_all_bank_pdfs.py` auf, welches jetzt PostgreSQL verwendet.

---

### 3. Manueller Test-Import

**Auf Server ausführen:**
```bash
cd /opt/greiner-portal
python3 scripts/imports/import_all_bank_pdfs.py --bank hvb --days 30
```

**Optionen:**
- `--bank hvb` - Nur Hypovereinsbank
- `--days 30` - Letzte 30 Tage
- `--today` - Nur heutige/gestrige PDFs

**Erwartete Ausgabe:**
```
======================================================================
📁 Hypovereinsbank
======================================================================
   📋 X PDFs der letzten 30 Tage

  📄 HV_Kontoauszug_XX.XX.XX.pdf
     ✅ 15 TX | 2 skip | Saldo -76.333,42€

   📊 Gesamt: 15 importiert, 2 übersprungen
```

---

## Nächste Schritte

### 1. Sofort (nach Deployment)

1. **Datenstand prüfen:**
   ```bash
   python3 scripts/tests/check_hvb_datenstand.py
   ```

2. **Manueller Import (falls nötig):**
   ```bash
   python3 scripts/imports/import_all_bank_pdfs.py --bank hvb --days 60
   ```

3. **Ergebnis prüfen:**
   - Kontenübersicht im Browser öffnen
   - Hypovereinsbank-Konto prüfen
   - Letztes Update-Datum prüfen

### 2. Monitoring

**Celery-Task prüfen:**
- Flower Dashboard: http://10.80.80.20:5555
- Task `import_hvb_pdf` sollte regelmäßig laufen
- Logs prüfen: `journalctl -u celery-worker -f`

**Cron-Job prüfen (falls vorhanden):**
```bash
crontab -l | grep import_all_bank_pdfs
```

**Erwartete Zeiten:**
- 08:00, 12:00, 17:00 (laut Dokumentation)

---

## Deployment

### 1. Dateien auf Server kopieren

```bash
# Auf Server (10.80.80.20)
cd /opt/greiner-portal

# Dateien syncen (von Windows-Sync)
rsync -av --exclude '.git' /mnt/greiner-portal-sync/scripts/imports/import_all_bank_pdfs.py scripts/imports/
rsync -av --exclude '.git' /mnt/greiner-portal-sync/scripts/tests/check_hvb_datenstand.py scripts/tests/
```

### 2. Testen

```bash
# Datenstand prüfen
python3 scripts/tests/check_hvb_datenstand.py

# Test-Import
python3 scripts/imports/import_all_bank_pdfs.py --bank hvb --days 7
```

### 3. Celery Worker neu starten (falls nötig)

```bash
sudo systemctl restart celery-worker
```

**Hinweis:** Normalerweise nicht nötig, da Skripte dynamisch geladen werden.

---

## Bekannte Issues

### 1. PDF-Parser

Falls Import fehlschlägt, Parser prüfen:
- `parsers/hypovereinsbank_parser_v2.py`
- PDF-Format könnte sich geändert haben

### 2. Dateinamen-Pattern

Aktuelles Pattern: `r'HV.*Kontoauszug.*(\d{2}\.\d{2}\.\d{2})\.pdf'`

Falls PDFs nicht erkannt werden, Pattern anpassen.

### 3. Mount-Pfad

PDFs müssen unter `/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Hypovereinsbank/` liegen.

Prüfen:
```bash
ls -la /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Hypovereinsbank/
```

---

## Geänderte Dateien

1. ✅ `scripts/imports/import_all_bank_pdfs.py` - PostgreSQL-Migration
2. ✅ `scripts/tests/check_hvb_datenstand.py` - NEU: Diagnose-Skript
3. ✅ `docs/HYPOVEREINSBANK_FIX_TAG165.md` - NEU: Diese Dokumentation

---

## Validierung

Nach dem Fix sollte:

1. ✅ Hypovereinsbank-Konto in Kontenübersicht aktuell sein
2. ✅ Letztes Update < 1 Tag alt
3. ✅ Neue Transaktionen werden importiert
4. ✅ Celery-Task läuft ohne Fehler

---

**Erstellt:** 2026-01-04  
**Autor:** Claude (TAG 165)  
**Status:** ✅ Fix implementiert und getestet

---

## Test-Ergebnisse (2026-01-04)

### Vorher:
- ❌ Letzte Buchung: 2025-12-23 (12 Tage alt)
- ❌ 2.713 Transaktionen
- ❌ View: -76.333,42 €

### Nachher:
- ✅ Letzte Buchung: 2026-01-02 (2 Tage alt)
- ✅ 2.717 Transaktionen (+4 neue)
- ✅ View: 239.785,24 € (aktualisiert)

### Import-Test:
- ✅ 3 PDFs der letzten 7 Tage gefunden
- ✅ 4 Transaktionen erfolgreich importiert
- ✅ Salden aktualisiert

**Hinweis:** Skript muss mit `venv/bin/python3` aufgerufen werden (Celery-Task macht das automatisch).

