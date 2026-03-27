# /commit - Git Commit erstellen

Erstellt einen strukturierten Git Commit mit korrektem Format.

## Kontext anzeigen

```bash
pwd && git branch --show-current
```

Umgebung ausgeben:
- `/opt/greiner-portal/` + `main` = Production
- `/opt/greiner-test/` + `develop` = Develop

## Status und Diff pruefen

```bash
git status
```

```bash
git diff --stat
```

```bash
git diff
```

Analysieren: Welche Dateien wurden geaendert und was ist der Hauptzweck der Aenderungen?

## Commit-Message Format

```
<type>(<workstream>): <Kurzbeschreibung auf Deutsch>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

### Types

| Type | Verwendung |
|------|-----------|
| `feat` | Neues Feature oder neue Funktionalitaet |
| `fix` | Bugfix |
| `docs` | Nur Dokumentation |
| `refactor` | Code-Umstrukturierung ohne Funktionsaenderung |
| `chore` | Maintenance, Dependencies, Konfiguration |

### Workstream-Bezeichnungen

`verkauf`, `controlling`, `werkstatt`, `urlaubsplaner`, `hr`, `teile`, `finanzierungen`, `infrastruktur`, `auth`, `marketing`, `verguetung`, `planung`

Beispiele:
- `feat(verkauf): Auslieferungen nach Marke aufgeschluesselt`
- `fix(urlaubsplaner): Genehmiger-Zuweisung bei mehrtaegigen Antraegen korrigiert`
- `refactor(controlling): TEK-Berechnung auf SSOT-Funktion umgestellt`

## Dateien stagen und committen

Spezifische Dateien stagen (nicht `git add -A` oder `git add .`):

```bash
git add [datei1] [datei2] ...
```

Commit erstellen:

```bash
git commit -m "$(cat <<'EOF'
type(workstream): beschreibung

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

## Nach dem Commit

Git-Status pruefen:

```bash
git status && git log --oneline -3
```

Push anbieten:

```bash
git push origin $(git branch --show-current)
```

Den User fragen ob Push gewuenscht ist -- nicht automatisch pushen.

## Hinweise

- Keine Emojis in Commit-Messages
- Beschreibung auf Deutsch, technische Begriffe auf Englisch
- Keine Session-Wrap-Up-Dateien oder TODO-Dateien committen
- `.env` und Passwort-Dateien niemals committen
