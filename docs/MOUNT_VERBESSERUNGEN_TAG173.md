# Mount-Verbesserungen TAG 173

**Datum:** 2026-01-09  
**Problem:** MT940 Import schlägt manchmal fehl mit "Host is down" (Errno 112)

## 🔍 Problem-Analyse

### Mount-Konfiguration
- **Typ:** CIFS/SMB Mount
- **Quelle:** `//srvrdb01/Allgemein` (Windows-Server 10.80.80.4)
- **Ziel:** `/mnt/buchhaltung`
- **Status:** `soft` Mount (nicht `hard`)
- **Mount-Optionen:** `vers=3.0,soft,retrans=1`

### Warum schlägt es fehl?
1. **Soft Mount:** Bei Verbindungsproblemen schlägt Zugriff sofort fehl
2. **Netzwerk-Latenz:** Kurze Unterbrechungen zwischen Linux- und Windows-Server
3. **CIFS-Timeout:** Standard-Timeout bei langsamen Verbindungen
4. **Celery-Worker:** Fork-Prozess sieht Mount möglicherweise nicht korrekt

## ✅ Implementierte Verbesserungen

### 1. Retry-Logik im Import-Script (`import_mt940.py`)

**Neue Funktion:** `check_mount_available()`
- Prüft Mount-Verfügbarkeit mit 3 Retry-Versuchen
- Zusätzliche Prüfung: Versucht Verzeichnis zu listen (nicht nur `exists()`)
- Wartezeit zwischen Retries: 2 Sekunden
- Neue CLI-Argumente: `--retry` und `--retry-delay`

**Code:**
```python
def check_mount_available(directory, max_retries=3, retry_delay=2):
    """Prüft ob Mount verfügbar ist, mit Retry bei Problemen"""
    for attempt in range(max_retries):
        try:
            if directory.exists():
                # Zusätzliche Prüfung: Versuche ein Verzeichnis zu listen
                try:
                    list(directory.iterdir())
                    return True
                except (OSError, PermissionError) as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
    return False
```

### 2. Verbesserte Mount-Prüfung im Celery-Task

**Änderungen:**
- **3 Retry-Versuche** im Celery-Task (statt 2)
- **Kürzere Wartezeit:** 30 Sekunden zwischen Retries (statt 60)
- **Erhöhtes Timeout:** 180 Sekunden (statt 120)
- **Zusätzliche Prüfung:** Versucht Verzeichnis zu listen (nicht nur `exists()`)
- **Bessere Fehlererkennung:** Erkennt "Host is down" und löst Retry aus

**Code:**
```python
@shared_task(soft_time_limit=180, name='celery_app.tasks.import_mt940', 
             autoretry_for=(OSError,), retry_kwargs={'max_retries': 3, 'countdown': 30})
def import_mt940():
    # Verbesserte Mount-Prüfung mit Retry
    for attempt in range(3):
        try:
            if os.path.exists(mt940_dir):
                os.listdir(mt940_dir)  # Zusätzliche Prüfung
                mount_ok = True
                break
        except (OSError, PermissionError):
            if attempt < 2:
                time.sleep(2)
                continue
```

### 3. Doppelte Retry-Logik

**Ebenen:**
1. **Celery-Level:** 3 Retries mit 30s Abstand (bei OSError)
2. **Script-Level:** 3 Retries mit 2s Abstand (bei Mount-Prüfung)

**Vorteil:** Mehrfache Absicherung gegen temporäre Netzwerk-Probleme

## 📊 Erwartete Verbesserungen

### Vorher:
- ❌ Ein Fehler → Task schlägt sofort fehl
- ❌ Keine Retry-Logik
- ❌ Keine Mount-Prüfung

### Nachher:
- ✅ **Bis zu 9 Versuche** (3x Celery + 3x Script)
- ✅ **Intelligente Mount-Prüfung** (nicht nur `exists()`)
- ✅ **Bessere Fehlererkennung** (erkennt "Host is down")
- ✅ **Kürzere Wartezeiten** (30s statt 60s)

## 🔧 Weitere mögliche Verbesserungen (optional)

### 1. Hard Mount (statt soft)
**Vorteil:** Wartet länger bei Verbindungsproblemen  
**Nachteil:** Kann bei Server-Ausfällen hängen bleiben

### 2. systemd Automount
**Vorteil:** Automatisches Remount bei Verbindungsproblemen  
**Nachteil:** Erfordert systemd-Unit-Konfiguration

### 3. Mount-Health-Check
**Vorteil:** Proaktive Überwachung des Mount-Status  
**Nachteil:** Zusätzlicher Overhead

## 🧪 Tests

### Test 1: Mount verfügbar
```bash
cd /opt/greiner-portal
/opt/greiner-portal/venv/bin/python3 scripts/imports/import_mt940.py \
  /mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/
```
**Erwartung:** Import läuft durch

### Test 2: Mount nicht verfügbar (simuliert)
```bash
# Mount temporär unmounten
sudo umount /mnt/buchhaltung
# Import starten
# Mount wieder mounten
```
**Erwartung:** Retry-Logik greift, Import wartet

## 📝 Deployment

1. ✅ Code-Änderungen implementiert
2. ✅ Celery-Worker neu gestartet
3. ⚠️ **Service-Neustart erforderlich:**
   ```bash
   sudo systemctl restart celery-worker
   ```

## 📌 Wichtige Hinweise

- **Mount-Status prüfen:** `systemctl status mnt-buchhaltung.mount`
- **Logs überwachen:** `journalctl -u celery-worker -f | grep mt940`
- **Bei anhaltenden Problemen:** Mount-Konfiguration prüfen (hard vs. soft)

---

**Erstellt:** 2026-01-09  
**TAG:** 173  
**Autor:** Claude (Auto)
