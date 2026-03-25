# CONTEXT Infrastruktur

## Letzte Aktualisierung
2026-03-25

## Fokus
- Git- und Delivery-Baseline stabilisieren.
- Einheitliche Cursor-Umgebung fuer Teamarbeit.
- Portability fuer weitere Haendler vorbereiten.

## Aktueller Stand
- PR-Split-Reihenfolge abgeschlossen (Migrations, Backend, Frontend, Scripts).
- Team-Baseline fuer Cursor ueber `.vscode/extensions.json` und `.vscode/settings.json` angelegt.
- `develop` auf aktuellen `main`-Stand gebracht und nach `origin/develop` gepusht.
- Onboarding und Portability-Dokumente erstellt:
  - `DEV_ONBOARDING_CURSOR.md`
  - `DEALER_PORTABILITY_GIT_BASELINE.md`
  - `MERGE_ROLLOUT_PLAN_SANE_DRIVE_PRs.md`
  - `TEAM_WORKFLOW_PROD_DEV.md`
  - `HOTFIX_CHECKLIST.md`

## Naechste Schritte
- Teambriefing auf Rollenaufteilung (Florian=Prod, Vanessa=Dev).
- Dev-Service auf `:5002` technisch pruefen (Start/Logs/Restart) und 1x gemeinsam durchlaufen.
