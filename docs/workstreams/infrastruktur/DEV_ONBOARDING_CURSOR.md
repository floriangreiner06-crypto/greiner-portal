# DEV Onboarding Cursor

## Ziel
Einheitliche Entwicklungsumgebung fuer DRIVE, damit Teammitglieder mit den gleichen Empfehlungen, Workflows und Konventionen arbeiten.

## Pflichtschritte
1. Repository klonen und im Projektordner arbeiten.
2. Empfohlene Extensions aus `.vscode/extensions.json` installieren.
3. Workspace-Settings aus `.vscode/settings.json` aktiv lassen.
4. Python-Interpreter auf `${workspaceFolder}/.venv/bin/python` setzen.
5. Vor groesseren Aenderungen `CLAUDE.md` und relevante Workstream-Kontexte lesen.

## Erwartetes Verhalten
- Gleiche Formatierungs- und Such-Defaults im Team.
- Keine lokalen Sonderkonfigurationen im Repo einchecken.
- Fachlogik mit SSOT-Prinzip umsetzen.

## Schnellcheck (Ist-gleich)
- Gleiche empfohlene Extensions sichtbar.
- `editor.formatOnSave = true` im Workspace.
- Python formatter: Ruff.
- Gleiche Excludes fuer `.venv`, `__pycache__`, `.ruff_cache`, `.pytest_cache`.

## Hinweise
- User-Settings bleiben individuell; `.vscode/*` liefert Team-Baseline.
- Bei Abweichungen zuerst Workspace-Dateien pruefen, dann lokale Overrides.
