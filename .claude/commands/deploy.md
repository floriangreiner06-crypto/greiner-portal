# /deploy - Develop nach Production mergen

Merged den develop-Branch in main und startet Production neu.

## Sicherheitspruefungen

Vor dem Deployment diese Checks ausfuehren:

1. Sicherstellen dass das aktuelle Verzeichnis `/opt/greiner-test/` ist (develop-Umgebung)
2. Git-Branch pruefen: muss `develop` sein
3. Uncommittete Aenderungen pruefen: `git status` -- wenn Aenderungen vorhanden, zuerst committen oder /commit ausfuehren

```bash
cd /opt/greiner-test && git status && git branch --show-current
```

Wenn nicht auf `develop` oder Aenderungen vorhanden: abbrechen und den User informieren.

## Deployment-Schritte

### Schritt 1: develop pushen

```bash
cd /opt/greiner-test && git push origin develop
```

### Schritt 2: In Production wechseln und mergen

```bash
cd /opt/greiner-portal && git fetch origin && git checkout main && git merge origin/develop
```

Konflikt-Check: Wenn Merge-Konflikte auftreten, abbrechen und Konflikte benennen.

### Schritt 3: Production neustarten

```bash
sudo -n /usr/bin/systemctl restart greiner-portal
```

Kurz warten, dann Status pruefen:

```bash
sudo -n /usr/bin/systemctl status greiner-portal --no-pager
```

### Schritt 4: main pushen

```bash
cd /opt/greiner-portal && git push origin main
```

### Schritt 5: Verifizierung

```bash
curl -s http://localhost:5000/api/admin/health | python3 -m json.tool
sudo -n /usr/bin/journalctl -u greiner-portal --since "1 minute ago" --no-pager | tail -20
```

## Ergebnis

Zusammenfassung ausgeben:
- Welche Commits wurden gemerged (git log main --oneline -10)
- Service-Status
- Etwaige Fehler in den Logs

## Umgebungen

| Umgebung | Verzeichnis | Branch | Port |
|----------|-------------|--------|------|
| Production | /opt/greiner-portal/ | main | 5000 |
| Develop | /opt/greiner-test/ | develop | 5001 (extern: 5002) |
