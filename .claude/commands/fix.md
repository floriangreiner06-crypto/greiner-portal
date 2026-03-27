# /fix - Bug analysieren und beheben

Analysiert einen Bug und behebt ihn. Erkennt automatisch die Umgebung und waehlt den richtigen Workflow.

## Umgebung erkennen

```bash
pwd && git branch --show-current
```

| Branch | Workflow |
|--------|----------|
| main | Hotfix-Workflow -- Aenderung geht direkt in Production |
| develop | Normaler Fix -- Aenderung geht in Develop, dann via /deploy |
| feature/* | Feature-Fix -- Aenderung bleibt im Feature-Branch |

Wenn auf `main`: den User darauf hinweisen dass dies ein Hotfix wird und nachfragen ob das gewuenscht ist.

## Bug-Beschreibung sammeln

Falls nicht bereits bekannt:
- Was ist das erwartete Verhalten?
- Was passiert stattdessen?
- Wann und wo tritt es auf (welche Seite, welcher User)?
- Gibt es eine Fehlermeldung oder einen HTTP-Fehlercode?

## Logs pruefen

### Develop:

```bash
sudo -n /usr/bin/journalctl -u greiner-test --since "1 hour ago" --no-pager | grep -i "error\|exception\|traceback" | tail -30
```

### Production:

```bash
sudo -n /usr/bin/journalctl -u greiner-portal --since "1 hour ago" --no-pager | grep -i "error\|exception\|traceback" | tail -30
```

Bei Traceback: die genannte Datei und Zeile direkt lesen und analysieren.

## Code-Analyse

1. Betroffene Datei(en) lesen
2. Fehlerquelle identifizieren
3. Verwandte Funktionen pruefen (werden dieselben Daten woanders verwendet?)
4. SSOT pruefen: Gibt es eine zentrale Funktion, die korrekt verwendet werden sollte?

## Fix implementieren

Grundregeln:
- Minimale Aenderung bevorzugen
- Keine unnoetige Refaktorierung waehrend eines Fixes
- SSOT nicht brechen -- keine parallele Logik einfuehren
- PostgreSQL-Syntax beachten (`%s`, `true`, `CURRENT_DATE`, `EXTRACT`)

## Nach dem Fix: Neustart und Verifizierung

```bash
# Develop:
sudo -n /usr/bin/systemctl restart greiner-test
sudo -n /usr/bin/journalctl -u greiner-test --since "30 seconds ago" --no-pager | tail -20

# Production (nur bei Hotfix):
sudo -n /usr/bin/systemctl restart greiner-portal
sudo -n /usr/bin/journalctl -u greiner-portal --since "30 seconds ago" --no-pager | tail -20
```

Kein Neustart noetig bei reinen Template-Aenderungen (.html) -- Browser-Refresh genuegt.

## Naechste Schritte vorschlagen

- Auf develop: `/commit` anbieten, danach `/deploy` wenn deploy-bereit
- Auf main: `/hotfix` anbieten (committed, pushed, in develop gemergt)

## Zusammenfassung

Am Ende ausgeben:
- Problem: [was war der Bug]
- Ursache: [warum ist er aufgetreten]
- Loesung: [was wurde geaendert, welche Datei(en)]
- Getestet: [wie wurde verifiziert]
