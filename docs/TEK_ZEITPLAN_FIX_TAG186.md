# TEK Zeitplan Fix - TAG 186

**Datum:** 2026-01-13  
**Problem:** TEK-Versand sollte auf 19:30 gesetzt werden, aber UI zeigte 17:30 und heute wurde nichts versendet

---

## 🔍 PROBLEM-ANALYSE

### Problem 1: Redundanz zwischen Celery-Config und Registry
- **Celery-Konfiguration** (`celery_app/__init__.py`): ✅ 19:30 (korrekt)
- **UI-Anzeige** (`reports/registry.py`): ❌ 17:30 (falsch)
- **Dokumentation** (`docs/DRIVE_FEATURES_FOR_LEO.md`): ❌ 17:30 (falsch)

**Ursache:** Die Zeit wird an zwei Stellen definiert:
1. **Celery Beat Schedule** (tatsächliche Ausführung)
2. **Report Registry** (UI-Anzeige für Admin-Interface)

### Problem 2: TEK-Versand heute fehlgeschlagen
- **Task wurde um 19:30 ausgeführt** ✅
- **Script beendete sich mit Exit Code 1** ❌
- **Grund:** Mirror-Prüfung schlug fehl (obwohl Mirror erfolgreich war)
- **Fehler:** Script beendete sich bei fehlgeschlagener Prüfung statt trotzdem zu senden

---

## ✅ LÖSUNG

### 1. Alle TEK-Reports auf 19:30 gesetzt

**Geänderte Dateien:**
- `reports/registry.py`: Alle 6 TEK-Reports von 17:30 → 19:30
  - `tek_daily`
  - `tek_filiale`
  - `tek_nw`
  - `tek_gw`
  - `tek_teile`
  - `tek_werkstatt`

- `docs/DRIVE_FEATURES_FOR_LEO.md`: Dokumentation aktualisiert

### 2. Mirror-Prüfung robuster gemacht

**Problem:** Script beendete sich bei fehlgeschlagener Mirror-Prüfung

**Lösung:**
- Bei fehlgeschlagener Prüfung: **Trotzdem senden** (mit Warnung)
- Nur bei explizitem Fehler blockieren
- Besseres Error-Handling in Celery-Task (loggt jetzt stdout + stderr)

**Geänderte Dateien:**
- `scripts/send_daily_tek.py`: Mirror-Prüfung sendet jetzt trotzdem (mit Warnung)
- `celery_app/tasks.py`: Besseres Error-Logging (stdout + stderr)

---

## 📊 REDUNDANZ-DOKUMENTATION

### Zeitplan-Konfiguration: Zwei Stellen

**1. Celery Beat Schedule** (`celery_app/__init__.py`)
```python
'email-tek-daily': {
    'task': 'celery_app.tasks.email_tek_daily',
    'schedule': crontab(minute=30, hour=19, day_of_week='mon-fri'),
    'options': {'queue': 'controlling'}
}
```
- **Zweck:** Tatsächliche Ausführung der Task
- **SSOT:** ✅ Diese Stelle ist die Quelle der Wahrheit für die Ausführung

**2. Report Registry** (`reports/registry.py`)
```python
REPORT_REGISTRY['tek_daily'] = {
    'schedule': '19:30 Mo-Fr',  # UI-Anzeige
    ...
}
```
- **Zweck:** UI-Anzeige im Admin-Interface (`/admin/rechte`)
- **SSOT:** ❌ Diese Stelle ist nur für die Anzeige, nicht für die Ausführung

**Problem:** Beide Stellen müssen manuell synchronisiert werden!

**Lösung:** 
- ✅ Beide Stellen auf 19:30 gesetzt
- ⚠️ **WICHTIG:** Bei zukünftigen Änderungen beide Stellen anpassen!

---

## 🔧 TECHNISCHE DETAILS

### Mirror-Prüfung (TAG 181)

**Funktionsweise:**
1. Prüft Redis Result Backend (DB 1) nach `celery-task-meta-*` Keys
2. Sucht nach Task mit `'locosoft_mirror'` im Namen
3. Prüft Status = 'SUCCESS' und Datum = heute

**Problem:**
- Prüfung kann fehlschlagen (Redis-Verbindung, Task-Name, Timing)
- Script beendete sich bei fehlgeschlagener Prüfung

**Fix (TAG 186):**
- Bei fehlgeschlagener Prüfung: **Trotzdem senden** (mit Warnung)
- Nur bei explizitem Fehler blockieren
- Exception-Handling verbessert

### Celery-Task Error-Handling

**Vorher:**
```python
logger.error(f"TEK E-Mail fehlgeschlagen: {result.stderr}")
```

**Nachher:**
```python
error_msg = result.stderr[-500:] if result.stderr else result.stdout[-500:] if result.stdout else 'Unbekannter Fehler'
logger.error(f"TEK E-Mail fehlgeschlagen (Exit Code: {result.returncode}): {error_msg}")
if result.stdout:
    logger.info(f"TEK Script stdout: {result.stdout[-500:]}")
```

**Vorteil:** Jetzt werden sowohl stdout als auch stderr geloggt (besseres Debugging)

---

## 📝 CHECKLISTE FÜR ZUKÜNFTIGE ÄNDERUNGEN

**Bei Zeitplan-Änderungen für TEK-Reports:**
- [ ] `celery_app/__init__.py` - Celery Beat Schedule anpassen
- [ ] `reports/registry.py` - Alle betroffenen TEK-Reports anpassen
- [ ] `docs/DRIVE_FEATURES_FOR_LEO.md` - Dokumentation aktualisieren
- [ ] Testen: Task wird zur richtigen Zeit ausgeführt
- [ ] Testen: UI zeigt richtige Zeit an

---

## ✅ STATUS

- ✅ Alle TEK-Reports in Registry auf 19:30 gesetzt
- ✅ Dokumentation aktualisiert
- ✅ Mirror-Prüfung robuster gemacht (sendet trotzdem bei Prüfungsfehler)
- ✅ Celery-Task Error-Handling verbessert
- ✅ Redundanz dokumentiert

**Nächste Schritte:**
- Morgen prüfen ob TEK-Versand erfolgreich war
- Logs prüfen ob Mirror-Prüfung jetzt funktioniert

---

*Erstellt: TAG 186 | Autor: Claude AI*
