# /session-end - Arbeitssession beenden

Schliesst die Session sauber ab: CONTEXT.md aktualisieren, committen, pushen, Merge-Status pruefen.

## Schritt 1: Was wurde heute gemacht?

Zusammenfassung aus dem Gespraechsverlauf ziehen:
- Welcher Workstream war aktiv?
- Welche Features wurden implementiert?
- Welche Bugs wurden behoben?
- Welche Dateien wurden geaendert?

```bash
cd /opt/greiner-test && git diff --stat HEAD
cd /opt/greiner-test && git log --oneline -5
```

## Schritt 2: Workstream CONTEXT.md aktualisieren

Datei lesen und aktualisieren:

```
/opt/greiner-portal/docs/workstreams/[workstream]/CONTEXT.md
```

Folgende Abschnitte aktualisieren:
- "Letzter Stand" oder "Aktueller Stand" -- was ist jetzt fertig
- "Offene Aufgaben" -- was ist noch offen, was ist erledigt (abhaken oder loeschen)
- "Naechste Schritte" -- konkret, was als naechstes kommt
- "Bekannte Probleme" -- neue Probleme erwaehnen, geloeste entfernen

Keine neuen SESSION_WRAP_UP-Dateien erstellen. Keine TODO_FOR_CLAUDE-Dateien erstellen.

## Schritt 3: Git Status pruefen

```bash
cd /opt/greiner-test && git status
```

Uncommittete Aenderungen aufzeigen. `/commit` anbieten falls noch nicht committed.

## Schritt 4: Push pruefen

```bash
cd /opt/greiner-test && git status -sb
```

Wenn lokale Commits noch nicht gepusht: fragen ob push gewuenscht.

```bash
cd /opt/greiner-test && git push origin develop
```

## Schritt 5: Merge-Status pruefen

Pruefen ob develop hinter main haengt oder umgekehrt:

```bash
cd /opt/greiner-test && git log origin/main..HEAD --oneline | head -10
```

Ausgabe:
- Wenn Commits vorhanden: "Es gibt [X] Commits in develop die noch nicht in main sind. /deploy ausfuehren wenn bereit."
- Wenn leer: "develop und main sind synchron."

Pruefen ob Hotfixes in main vorhanden sind die noch nicht in develop sind:

```bash
cd /opt/greiner-test && git log HEAD..origin/main --oneline | head -5
```

Wenn Commits vorhanden: "Es gibt Commits in main die noch nicht in develop sind. /sync in /opt/greiner-test/ ausfuehren."

## Schritt 6: Abschluss-Zusammenfassung

Kurze Zusammenfassung ausgeben:
- Erledigt heute: [Liste]
- Offen: [Liste]
- Git: committed / gepusht / deploy ausstehend
- Naechste Session: [konkreter Einstiegspunkt]

## Nicht tun

- Keine SESSION_WRAP_UP_TAG[X].md Dateien erstellen
- Keine TODO_FOR_CLAUDE_SESSION_START_TAG[X].md Dateien erstellen
- Diese Dateien sind veraltet -- der Kontext lebt in CONTEXT.md
