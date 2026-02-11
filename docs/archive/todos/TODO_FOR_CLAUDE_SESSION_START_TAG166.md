# TODO für Claude - Session Start TAG 166

**Erstellt:** 2026-01-04  
**Nächste Session:** TAG 166

---

## 📋 PRIORITÄTEN

### 🔴 HOCH: Offene Aufgaben

1. **Hypovereinsbank Import - Monitoring**
   - [ ] Celery-Task `import_hvb_pdf` regelmäßig prüfen
   - [ ] Logs überwachen auf Fehler
   - [ ] Datenstand wöchentlich prüfen (via `check_hvb_datenstand.py`)
   - [ ] Falls Daten >3 Tage alt: Manuellen Import durchführen

2. **Weitere Banken prüfen**
   - [ ] Prüfen ob andere Banken auch betroffen sind
   - [ ] Alle Import-Skripte auf PostgreSQL-Kompatibilität prüfen
   - [ ] `scripts/imports/` durchsuchen nach SQLite-Referenzen

3. **Import-Automatisierung**
   - [ ] Cron-Job prüfen (falls vorhanden)
   - [ ] Celery-Beat Schedule prüfen
   - [ ] Dokumentation aktualisieren falls nötig

---

### 🟡 MITTEL: Verbesserungen

4. **Import-Skripte konsolidieren**
   - [ ] Alle Bank-Import-Skripte auf PostgreSQL umstellen
   - [ ] Gemeinsame DB-Connection-Logik verwenden
   - [ ] Fehlerbehandlung standardisieren

5. **Diagnose-Tools erweitern**
   - [ ] Diagnose-Skript für alle Banken erweitern
   - [ ] Automatische Warnung bei veralteten Daten
   - [ ] Dashboard für Import-Status

6. **Dokumentation**
   - [ ] Import-Prozess dokumentieren
   - [ ] Troubleshooting-Guide erstellen
   - [ ] FAQ für häufige Probleme

---

### 🟢 NIEDRIG: Nice-to-Have

7. **Monitoring & Alerts**
   - [ ] Email-Benachrichtigung bei veralteten Daten
   - [ ] Dashboard für Import-Status
   - [ ] Metriken sammeln (Import-Zeit, Erfolgsrate)

8. **Performance-Optimierung**
   - [ ] Import-Geschwindigkeit messen
   - [ ] Batch-Import optimieren
   - [ ] Duplikat-Check optimieren

---

## 🔍 WICHTIGE HINWEISE

### Hypovereinsbank Import

**Status:** ✅ Fix implementiert und getestet

**Wichtig:**
- Skript muss mit `venv/bin/python3` aufgerufen werden
- Celery-Task verwendet bereits `VENV_PYTHON` (automatisch)
- Manueller Aufruf: `venv/bin/python3 scripts/imports/import_all_bank_pdfs.py --bank hvb --days 30`

**Monitoring:**
- Datenstand prüfen: `venv/bin/python3 scripts/tests/check_hvb_datenstand.py`
- Logs: `journalctl -u celery-worker -f`
- Flower: http://10.80.80.20:5555

### PostgreSQL-Migration

**Hinweis:** Nach TAG 135-139 Migration sollten alle Skripte PostgreSQL verwenden.

**Prüfen:**
- Alle Import-Skripte in `scripts/imports/`
- Alle Analyse-Skripte in `scripts/analysis/`
- Alle Sync-Skripte in `scripts/sync/`

**Pattern:**
- ❌ `import sqlite3`
- ❌ `sqlite3.connect()`
- ✅ `from api.db_connection import get_db`
- ✅ `get_db()` verwenden

---

## 🐛 BEKANNTE ISSUES

1. **Hypovereinsbank Import**
   - ✅ Behoben: Skript verwendet jetzt PostgreSQL
   - ⚠️ Monitoring: Datenstand regelmäßig prüfen

2. **Weitere Banken**
   - ⚠️ Status unbekannt: Andere Banken könnten betroffen sein
   - 📋 Action: Alle Import-Skripte prüfen

---

## 📚 DOKUMENTATION

**Erstellt in TAG 165:**
- `docs/HYPOVEREINSBANK_FIX_TAG165.md` - Fix-Dokumentation
- `scripts/tests/check_hvb_datenstand.py` - Diagnose-Skript

**Zu erstellen:**
- Import-Prozess-Dokumentation
- Troubleshooting-Guide
- FAQ für häufige Probleme

---

## 🔄 CODE-ÄNDERUNGEN (TAG 165)

**Geänderte Dateien:**
- `scripts/imports/import_all_bank_pdfs.py` - PostgreSQL-Migration

**Neue Dateien:**
- `scripts/tests/check_hvb_datenstand.py` - Diagnose-Skript
- `docs/HYPOVEREINSBANK_FIX_TAG165.md` - Dokumentation

**Git Status:**
- ✅ Alle Änderungen lokal
- ✅ Server-Sync: Erfolgreich (via scp)
- ⚠️ Git-Commit: Noch nicht committed

---

## 💡 IDEEN FÜR ZUKUNFT

1. **Zentrales Import-Management**
   - Einheitliche Import-API
   - Status-Tracking
   - Fehlerbehandlung

2. **Automatische Benachrichtigungen**
   - Email bei veralteten Daten
   - Dashboard-Warnungen
   - Slack-Integration (optional)

3. **Import-Historie**
   - Log aller Imports
   - Erfolgsrate-Tracking
   - Performance-Metriken

---

**Nächste Session:** TAG 166  
**Fokus:** Monitoring, weitere Banken prüfen, Import-Skripte konsolidieren



