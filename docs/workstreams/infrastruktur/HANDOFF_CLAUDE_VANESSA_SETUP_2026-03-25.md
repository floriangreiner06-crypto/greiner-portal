# Handoff fuer Claude: Vanessa Setup und Team-Workflow

Stand: 2026-03-25

## Zielbild
- Einheitliche Cursor-Baseline fuer Florian und Vanessa.
- Saubere Trennung zwischen Produktion (`main`) und Entwicklung (`develop` auf Dev-Umgebung `:5002`).
- Nachvollziehbarer Git-Flow mit Rueckfuehrung von Hotfixes nach `develop`.

## Erreicht
- PR-Block abgeschlossen und gemerged: #2, #3, #4, #5.
- `main` und `develop` sind auf gleichem Stand (Fast-Forward-Sync durchgefuehrt).
- Team-Baseline versioniert:
  - `.vscode/extensions.json`
  - `.vscode/settings.json`
  - `.gitignore` angepasst, damit genau diese zwei `.vscode`-Dateien getrackt werden.

## Worktrees / Arbeitsorte
- Produktion/maintainer: `/home/ag-admin/greiner-portal-clean` (Branch `main`)
- Entwicklung/Vanessa: `/home/ag-admin/greiner-portal-develop` (Branch `develop`)
- Hinweis: `/opt/greiner-portal-develop` konnte wegen Berechtigungen nicht angelegt werden.

## Dokumente (Infrastruktur)
- `docs/workstreams/infrastruktur/DEV_ONBOARDING_CURSOR.md`
- `docs/workstreams/infrastruktur/DEALER_PORTABILITY_GIT_BASELINE.md`
- `docs/workstreams/infrastruktur/MERGE_ROLLOUT_PLAN_SANE_DRIVE_PRs.md`
- `docs/workstreams/infrastruktur/TEAM_WORKFLOW_PROD_DEV.md`
- `docs/workstreams/infrastruktur/HOTFIX_CHECKLIST.md`
- `docs/workstreams/infrastruktur/INSTALLATION_ANLEITUNG_VANESSA_WINDOWS_RDP_CURSOR.md`

## Vanessa-Setup Status
- GitHub-Collaborator-Einladung angenommen.
- Cursor mit eigenem Account empfohlen (nicht Shared-Account).
- Remote-Arbeit auf Linux-Server im Dev-Worktree vorgesehen.
- `.venv` im Dev-Worktree wurde serverseitig erstellt:
  - Pfad: `/home/ag-admin/greiner-portal-develop/.venv/bin/python`
  - `requirements.txt` installiert.

## Verbindliche Arbeitsregeln
- Vanessa entwickelt nur auf `develop` / `feature/*`, testet auf `:5002`.
- Florian arbeitet produktionsnah auf `main`.
- Jeder Hotfix auf `main` muss direkt nach `develop` zurueckgemerged werden (siehe `HOTFIX_CHECKLIST.md`).

## Offene/naechste Schritte fuer Claude
1. Optionalen End-to-End-Test mit Vanessa begleiten:
   - `develop` -> `feature/<thema>` -> Push -> PR nach `develop`.
2. Bei Bedarf Dev-Service (`:5002`) gemeinsam pruefen (Start/Logs/Restart).
3. Optional: Team-Kurzbefehle fuer Workstream-Start versioniert bereitstellen.

## Schnell-Kommandos
```bash
# main clean check
git -C /home/ag-admin/greiner-portal-clean status -sb

# develop clean check
git -C /home/ag-admin/greiner-portal-develop status -sb

# Divergenz check
git -C /home/ag-admin/greiner-portal-clean rev-list --left-right --count origin/develop...origin/main
```
