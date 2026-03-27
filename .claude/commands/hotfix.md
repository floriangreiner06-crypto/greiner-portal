# /hotfix - Hotfix auf main committen und in develop mergen

Fuer dringende Fixes direkt auf main. Committed auf main, startet Production neu, mergt in develop, startet Test neu, pusht beide Branches.

## Sicherheitspruefungen

1. Aktuelles Verzeichnis und Branch pruefen:

```bash
cd /opt/greiner-portal && git branch --show-current
```

Muss auf `main` sein. Wenn nicht auf main: abbrechen und den User informieren -- normaler Fix geht ueber `/fix` auf develop.

2. Uncommittete Aenderungen pruefen:

```bash
cd /opt/greiner-portal && git status
```

Wenn keine Aenderungen vorhanden: den User fragen was gefixt werden soll, dann erst fortfahren.

## Hotfix-Schritte

### Schritt 1: Fix auf main committen

Staged Aenderungen committen (falls nicht already staged, vorher fragen):

```bash
cd /opt/greiner-portal && git add -p
```

Commit erstellen mit Format `fix(bereich): beschreibung`:

```bash
cd /opt/greiner-portal && git commit -m "$(cat <<'EOF'
fix(bereich): kurze beschreibung des fixes

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Schritt 2: Production neustarten

```bash
sudo -n /usr/bin/systemctl restart greiner-portal
```

Status pruefen:

```bash
sudo -n /usr/bin/systemctl status greiner-portal --no-pager
sudo -n /usr/bin/journalctl -u greiner-portal --since "1 minute ago" --no-pager | tail -15
```

### Schritt 3: main pushen

```bash
cd /opt/greiner-portal && git push origin main
```

### Schritt 4: Fix in develop mergen

```bash
cd /opt/greiner-test && git fetch origin && git merge origin/main
```

Konflikt-Check: Wenn Konflikte auftreten, benennen und manuell loesen lassen.

### Schritt 5: Test-Umgebung neustarten

```bash
sudo -n /usr/bin/systemctl restart greiner-test
```

Status pruefen:

```bash
sudo -n /usr/bin/systemctl status greiner-test --no-pager
```

### Schritt 6: develop pushen

```bash
cd /opt/greiner-test && git push origin develop
```

## Ergebnis

Zusammenfassung:
- Commit-Hash des Hotfixes
- Production-Status
- Test-Status
- Beide Branches aktuell auf remote

## Wann Hotfix vs. normaler Fix

| Situation | Workflow |
|-----------|----------|
| Bug in Production, sofort beheben | /hotfix (auf main) |
| Bug in develop entdeckt | /fix (auf develop, dann /deploy) |
| Neues Feature | /feature (auf develop) |
