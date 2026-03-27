# HOTFIX Checklist (main -> develop)

## Ziel
Sicherstellen, dass jeder Produktions-Hotfix aus `main` direkt wieder in `develop` landet.

## Wann nutzen?
- Immer wenn ein Fix direkt auf `main` gemacht wurde (z. B. akuter Prod-Fehler).

## 1) Hotfix auf main sauber abschliessen
- Fix committen und pushen:
  - `git checkout main`
  - `git pull --ff-only`
  - `git add <dateien>`
  - `git commit -m "fix(<bereich>): <kurzbeschreibung>"`
  - `git push origin main`

## 2) Back-Merge nach develop (Pflicht)
- Direkt im Anschluss:
  - `git checkout develop`
  - `git pull --ff-only`
  - `git merge --ff-only main`
  - `git push origin develop`

Wenn `--ff-only` nicht geht:
- `git merge main`
- Konflikte loesen
- `git push origin develop`

## 3) Kurzvalidierung
- `git rev-list --left-right --count origin/develop...origin/main`
- Erwartung: linke Zahl = `0` (develop haengt nicht hinter main).

## 4) Team-Notiz (30 Sekunden)
- Kurz in PR/Chat dokumentieren:
  - Hotfix-Commit auf `main`
  - Back-Merge nach `develop` erledigt

## 5) Merksatz
- Kein Hotfix ist fertig, bevor `develop` denselben Stand hat.
