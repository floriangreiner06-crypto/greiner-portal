# eAutoseller Celery Task - Dokumentation

**Datum:** 2025-12-29  
**Status:** ✅ Task erstellt und registriert

---

## ✅ IMPLEMENTIERT

### Celery Task: `sync_eautoseller_data`

**Datei:** `celery_app/tasks.py`

**Funktion:**
- Synchronisiert eAutoseller-Daten (KPIs und Fahrzeugliste)
- Login zu eAutoseller
- Abruf von Dashboard-KPIs (startdata.asp)
- Abruf von Fahrzeugliste (kfzuebersicht.asp)

**Schedule:**
- **Frequenz:** Alle 15 Minuten
- **Zeit:** 7:00 - 18:00 Uhr
- **Tage:** Montag - Freitag
- **Queue:** `verkauf`

**Konfiguration:**
```python
'sync-eautoseller-data': {
    'task': 'celery_app.tasks.sync_eautoseller_data',
    'schedule': crontab(minute='*/15', hour='7-18', day_of_week='mon-fri'),
    'options': {'queue': 'verkauf'}
}
```

---

## 🔧 FEATURES

### Task-Locking
- Verhindert parallele Ausführung
- File-basiertes Locking
- Überspringt Task wenn bereits läuft

### Retry-Logik
- Max. 2 Retries
- Retry bei Netzwerk-Fehlern (timeout, connection)
- 60 Sekunden Wartezeit zwischen Retries

### Timeout
- Soft Time Limit: 300 Sekunden (5 Minuten)
- Verhindert hängende Tasks

---

## 📊 TASK-AUSGABE

**Erfolg:**
```json
{
    "status": "success",
    "kpis_count": 16,
    "vehicles_count": 0,
    "duration": 2.5
}
```

**Fehler:**
```json
{
    "status": "error",
    "error": "Fehlermeldung",
    "duration": 1.2
}
```

**Übersprungen (läuft bereits):**
```json
{
    "status": "skipped",
    "reason": "already running"
}
```

---

## 🧪 TESTEN

### Manuell testen:
```bash
cd /opt/greiner-portal
source venv/bin/activate
python3 scripts/test_eautoseller_task.py
```

### Über Celery:
```bash
celery -A celery_app call celery_app.tasks.sync_eautoseller_data
```

---

## 📋 CREDENTIALS

**Environment Variables:**
- `EAUTOSELLER_USERNAME` (default: fGreiner)
- `EAUTOSELLER_PASSWORD` (default: fGreiner12)
- `EAUTOSELLER_LOGINBEREICH` (default: kfz)

**Oder in `config/credentials.json`:**
```json
{
    "eautoseller": {
        "username": "fGreiner",
        "password": "fGreiner12",
        "loginbereich": "kfz"
    }
}
```

---

## 🔄 NÄCHSTE SCHRITTE

1. ✅ Task erstellt
2. ✅ Im beat_schedule registriert
3. ⏳ Celery Beat neu starten (damit Schedule aktiv wird)
4. ⏳ Task testen
5. ⏳ Monitoring einrichten (Flower)

---

**Status:** ✅ Task implementiert, ⏳ Celery Beat muss neu gestartet werden

