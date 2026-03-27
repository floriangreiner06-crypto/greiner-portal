# /logs - Server-Logs anzeigen

Zeigt Logs direkt via journalctl -- kein SSH noetig.

## Optionen

Den User fragen welche Logs benoetigt werden, oder direkt die passende Option auswaehlen basierend auf der Anfrage.

### Option 1: Production (greiner-portal)

```bash
sudo -n /usr/bin/journalctl -u greiner-portal --since "30 minutes ago" --no-pager | tail -50
```

### Option 2: Develop (greiner-test)

```bash
sudo -n /usr/bin/journalctl -u greiner-test --since "30 minutes ago" --no-pager | tail -50
```

### Option 3: Celery Worker

```bash
sudo -n /usr/bin/journalctl -u celery-worker --since "30 minutes ago" --no-pager | tail -50
```

### Option 4: Celery Beat (Scheduler)

```bash
sudo -n /usr/bin/journalctl -u celery-beat --since "30 minutes ago" --no-pager | tail -30
```

### Option 5: Nur Fehler (Production)

```bash
sudo -n /usr/bin/journalctl -u greiner-portal --since "1 hour ago" --no-pager | grep -i "error\|exception\|traceback\|critical" | tail -50
```

### Option 6: Nur Fehler (Develop)

```bash
sudo -n /usr/bin/journalctl -u greiner-test --since "1 hour ago" --no-pager | grep -i "error\|exception\|traceback\|critical" | tail -50
```

### Option 7: Live Follow (Production)

```bash
sudo -n /usr/bin/journalctl -u greiner-portal -f --no-pager
```

Hinweis: Live-Follow laeuft bis Strg+C gedrueckt wird. Claude Code kann dies im Terminal ausfuehren.

### Option 8: Live Follow (Develop)

```bash
sudo -n /usr/bin/journalctl -u greiner-test -f --no-pager
```

## Zeitraum anpassen

Zeitraum kann in der Anfrage angegeben werden:
- "logs letzte stunde" -- `--since "1 hour ago"`
- "logs seit heute morgen" -- `--since "today"`
- "logs letzte 5 minuten" -- `--since "5 minutes ago"`
- "logs seit neustart" -- `--boot`

## Automatische Log-Analyse

Nach dem Abrufen der Logs:
1. Fehler und Exceptions hervorheben
2. Haeufig wiederholte Fehler zaehlen
3. Wenn Traceback gefunden: betroffene Datei und Zeile nennen
4. Bei offensichtlichem Problem: `/fix` anbieten
