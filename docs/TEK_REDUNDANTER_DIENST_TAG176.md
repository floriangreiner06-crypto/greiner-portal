# TEK Redundanter Dienst - Problem gefunden (TAG 176)

**Datum:** 2026-01-09  
**Problem:** TEK Email wurde um 17:30 Uhr versendet, obwohl auskommentiert

---

## 🔍 PROBLEM-ANALYSE

### Ursache gefunden: Falscher Fallback in `email_werkstatt_tagesbericht`

Die Task `email_werkstatt_tagesbericht` (läuft um 17:30 Uhr) hatte einen **falschen Fallback** auf `send_daily_tek.py`:

```python
# VORHER (FEHLERHAFT):
script_paths = [
    '/opt/greiner-portal/scripts/send_daily_werkstatt_tagesbericht.py',
    '/opt/greiner-portal/scripts/send_daily_tek.py'  # ❌ FALSCHER FALLBACK!
]
```

**Was passierte:**
1. Um 17:30 Uhr startet `email_werkstatt_tagesbericht` (korrekt)
2. Script sucht nach `send_daily_werkstatt_tagesbericht.py`
3. Falls nicht gefunden → **Fallback auf `send_daily_tek.py`** ❌
4. TEK-Script wird ausgeführt → **TEK Emails werden versendet!**

**Logs zeigen:**
```
Jan 09 17:30:01 celery-worker: Starte Werkstatt E-Mail...
Jan 09 17:30:01 celery-worker: File "/opt/greiner-portal/scripts/send_daily_tek.py", line 579
Jan 09 17:30:01 celery-worker: Werkstatt E-Mail fehlgeschlagen: ... send_gesamt_reports
```

---

## ✅ LÖSUNG (TAG 176)

### Fallback entfernt

```python
# NACHHER (KORRIGIERT):
script_path = '/opt/greiner-portal/scripts/send_daily_werkstatt_tagesbericht.py'

if not os.path.exists(script_path):
    logger.error(f"Werkstatt E-Mail-Script nicht gefunden: {script_path}")
    return {'success': False, 'error': f'Script nicht gefunden: {script_path}'}
```

**Änderungen:**
- ❌ Fallback auf `send_daily_tek.py` **entfernt**
- ✅ Klare Fehlermeldung wenn Script fehlt
- ✅ Keine versehentliche Ausführung des TEK-Scripts mehr

---

## 📊 ZUSAMMENFASSUNG

**Problem:**
- TEK Email wurde um 17:30 Uhr versendet (obwohl auskommentiert)
- Ursache: Falscher Fallback in `email_werkstatt_tagesbericht`

**Lösung:**
- ✅ Fallback entfernt
- ✅ TEK Email läuft jetzt nur um 19:30 Uhr (korrekt)
- ✅ Werkstatt Email läuft um 17:30 Uhr (korrekt)

**Status:** ✅ **BEHOBEN** (TAG 176)

---

**Dateien geändert:**
- `celery_app/tasks.py` - Fallback entfernt
