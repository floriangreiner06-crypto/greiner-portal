# DEV Onboarding (Cursor) - Einheitliches Setup

## Ziel

Vanessa und Florian arbeiten in Cursor mit identischer Basis:

- gleiche Extensions
- gleiche Workspace-Settings
- gleiche Rules und Workstream-Logik
- gleiche Start- und End-Routinen

## Verbindliche Quellen im Repo

- Projektregeln: `.cursorrules`
- Architektur/SSOT/Betrieb: `CLAUDE.md`
- Workstream-Kontext: `docs/workstreams/<workstream>/CONTEXT.md`
- Workspace-Settings: `.vscode/settings.json`
- Extension-Empfehlungen: `.vscode/extensions.json`

## Einmalige Einrichtung pro Entwickler

1. Repo auf dem Server nutzen (`/opt/greiner-portal`) oder synchronen Mirror.
2. Cursor im Projektordner oeffnen.
3. Empfohlene Extensions aus `.vscode/extensions.json` installieren.
4. Python-Interpreter auf `${workspaceFolder}/.venv/bin/python` pruefen.
5. Sicherstellen, dass lokale User-Settings die Workspace-Settings nicht widersprechen.

## Session-Standard (immer gleich)

1. Session-Start nach `.cursor/commands/session-start.md`
2. Relevanten Workstream nennen und `CONTEXT.md` lesen/aktualisieren
3. Bei API-Fetch-Endpunkten: immer JSON-Fehlerpfad beachten (nie HTML-Fehlerseite)
4. Bei Backend- und Celery-Aenderungen: korrekte Service-Restarts einplanen
5. Session-Ende nach `.cursor/commands/session-end.md`

## Einheitliche Git-Disziplin

- Keine Force-Pushes auf geschuetzte Branches.
- Keine ungeplanten Mega-PRs; stattdessen fachliche Pakete.
- Merge-Reihenfolge und Rollout immer dokumentieren.
- Doku-Aenderungen unter `docs/` immer in den Sync spiegeln.

## Definition of Done fuer "gleiches Setup"

- Beide sehen dieselben empfohlenen Extensions im Workspace.
- Beide nutzen denselben Interpreterpfad fuer Python.
- Beide arbeiten nach denselben Regeln (`.cursorrules`, `CLAUDE.md`, Workstream-CONTEXT).
- PRs folgen demselben Paket-/Rollout-Pattern.
