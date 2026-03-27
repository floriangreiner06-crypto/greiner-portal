# /status - Status beider Umgebungen anzeigen

Zeigt einen vollstaendigen Ueberblick ueber Production und Develop, alle Services, DB-Konnektivitaet und Disk Space.

## Ausfuehren

Alle Checks direkt ausfuehren -- kein SSH noetig, wir laufen direkt auf dem Server.

### Git-Status: Production

```bash
cd /opt/greiner-portal && echo "=== PRODUCTION ===" && git branch --show-current && git status --short && echo "--- Letzte Commits ---" && git log --oneline -5
```

### Git-Status: Develop

```bash
cd /opt/greiner-test && echo "=== DEVELOP ===" && git branch --show-current && git status --short && echo "--- Letzte Commits ---" && git log --oneline -5
```

### Service-Status

```bash
echo "=== SERVICES ===" && for svc in greiner-portal greiner-test celery-worker celery-beat; do echo "$svc: $(sudo -n /usr/bin/systemctl is-active $svc 2>/dev/null || echo unbekannt)"; done
```

```bash
echo "Redis: $(redis-cli ping 2>/dev/null || echo FEHLER)"
```

### DB-Konnektivitaet

```bash
echo "=== DATENBANKEN ===" && PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT 'drive_portal OK' AS status;" -t 2>&1 | head -3
```

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "SELECT 'drive_portal_dev OK' AS status;" -t 2>&1 | head -3
```

### Letzte Fehler (letzte 10 Minuten)

```bash
echo "=== FEHLER PRODUCTION ===" && sudo -n /usr/bin/journalctl -u greiner-portal --since "10 minutes ago" --no-pager | grep -i "error\|exception\|traceback" | tail -10
```

```bash
echo "=== FEHLER DEVELOP ===" && sudo -n /usr/bin/journalctl -u greiner-test --since "10 minutes ago" --no-pager | grep -i "error\|exception\|traceback" | tail -10
```

### Disk Space

```bash
echo "=== DISK SPACE ===" && df -h /opt/greiner-portal /opt/greiner-test /data 2>/dev/null | head -6
```

## Ausgabe-Format

Tabellarische Zusammenfassung erstellen:

```
PRODUCTION (/opt/greiner-portal, main, Port 5000)
  Git:     [branch] - [X uncommitted files oder "clean"]
  Service: [active/inactive/failed]
  DB:      drive_portal [OK/FEHLER]

DEVELOP (/opt/greiner-test, develop, Port 5001)
  Git:     [branch] - [X uncommitted files oder "clean"]
  Service: [active/inactive/failed]
  DB:      drive_portal_dev [OK/FEHLER]

SERVICES
  celery-worker: [status]
  celery-beat:   [status]
  Redis:         [PONG/FEHLER]

DISK
  /opt: [X]G frei
```

Wenn Fehler oder Warnungen gefunden: diese hervorheben und kurze Diagnose anbieten.
