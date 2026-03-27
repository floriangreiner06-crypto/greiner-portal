# /sync - Git Pull auf aktuellem Branch

Zieht den aktuellen Branch vom Remote und startet den Service neu falls Python-Dateien geaendert wurden.

## Vorpruefungen

### Schritt 1: Umgebung erkennen

Aktuelles Verzeichnis bestimmen und entsprechende Werte setzen:

| Verzeichnis | Branch | Service | DB |
|-------------|--------|---------|-----|
| /opt/greiner-portal/ | main | greiner-portal | drive_portal |
| /opt/greiner-test/ | develop | greiner-test | drive_portal_dev |

```bash
pwd && git branch --show-current
```

### Schritt 2: Uncommittete Aenderungen pruefen

```bash
git status --short
```

Wenn uncommittete Aenderungen vorhanden: den User fragen ob committen (`/commit`) oder stashen (`git stash`) bevor pull ausgefuehrt wird. Nicht einfach fortfahren.

## Pull ausfuehren

```bash
git pull origin $(git branch --show-current)
```

Ausgabe pruefen:
- "Already up to date." -- nichts zu tun, melden
- Dateien aufgelistet -- merken welche Typen geaendert wurden

## Neustart-Entscheidung

Python-Dateien pruefen die geaendert wurden:

```bash
git diff HEAD@{1} --name-only | grep -E '\.(py)$'
```

**Python-Aenderungen vorhanden:** Service neustarten

```bash
# Production:
sudo -n /usr/bin/systemctl restart greiner-portal

# Develop:
sudo -n /usr/bin/systemctl restart greiner-test
```

**Nur Templates (.html), CSS, JS:** Kein Neustart noetig -- Browser-Refresh genuegt (Strg+F5).

**Nur Docs/Migration-Dateien:** Nichts tun.

## Status nach Pull

```bash
sudo -n /usr/bin/systemctl status greiner-portal --no-pager
# oder fuer develop:
sudo -n /usr/bin/systemctl status greiner-test --no-pager
```

Kurze Fehlerpruefung:

```bash
sudo -n /usr/bin/journalctl -u greiner-portal --since "30 seconds ago" --no-pager | grep -i "error\|exception\|traceback"
```

## Ergebnis

Zusammenfassung:
- Welche Commits neu gezogen wurden (`git log HEAD@{1}..HEAD --oneline`)
- Ob Neustart ausgefuehrt wurde
- Service-Status
