# Installationsanleitung Vanessa (Windows RDP + Cursor)

## Ziel
Vanessa arbeitet mit derselben Cursor-Baseline wie Florian, aber in der Dev-Linie (`develop`, Test auf `:5002`).

## 1) Voraussetzungen (Windows/RDP)
- Zugriff auf die Windows-RDP-Session sicherstellen.
- Git fuer Windows installiert (`git --version` in PowerShell testen).
- Cursor installiert und startbar.
- SSH-Zugriff auf den Linux-Server vorhanden (falls Remote-Arbeit ueber SSH genutzt wird).

## 2) Repository einrichten
Es gibt zwei saubere Wege. Empfohlen ist **A**.

### A) Serverseitiger Worktree (empfohlen)
- Dev-Worktree fuer Vanessa: `/home/ag-admin/greiner-portal-develop` (Branch `develop`).
- Main-Worktree fuer Produktion: `/home/ag-admin/greiner-portal-clean` (Branch `main`).
- In Cursor fuer Vanessa immer den Dev-Pfad oeffnen.

### B) Lokaler Git-Checkout in Windows
- Repo klonen.
- Auf `develop` wechseln.
- Nie auf `main` entwickeln.

## 3) Cursor-Setup (gleich wie Team)
Im geoeffneten Projekt:
- Extension-Empfehlungen installieren aus `.vscode/extensions.json`.
- Workspace-Settings aus `.vscode/settings.json` aktiv lassen.
- Python-Interpreter auf `${workspaceFolder}/.venv/bin/python` setzen (Remote/Linux) bzw. passendes venv lokal.

## 4) Verbindlicher Arbeitsmodus
- Vanessa entwickelt auf `develop` oder `feature/*` (Basis: `develop`).
- Tests laufen auf der Dev-Instanz (`:5002`).
- Merge-Ziel fuer normale Arbeit: `develop`.
- Produktions-Hotfixes auf `main` muessen danach nach `develop` zurueckgemerged werden (siehe `HOTFIX_CHECKLIST.md`).

## 5) Tages-Workflow (kurz)
1. `git checkout develop`
2. `git pull --ff-only`
3. `git checkout -b feature/<thema>`
4. Entwickeln + testen auf `:5002`
5. `git add` + `git commit`
6. `git push -u origin feature/<thema>`
7. PR nach `develop`

## 6) Schnelltest "Ist gleich"
- Branch ist `develop`.
- Extensions-Empfehlungen sichtbar/installiert.
- `formatOnSave` aktiv.
- Ruff als Python-Formatter aktiv.
- Testseite/Funktion laeuft auf `:5002`.

## 7) Troubleshooting
- Falscher Branch: zurueck auf `develop`, dann neuen Feature-Branch erstellen.
- Merge-Konflikt: nicht aufloesen "auf gut Glueck", kurz Ruecksprache.
- Fehlende Extensions/Settings: Projekt neu oeffnen und `.vscode/*` pruefen.
- Dev-Instanz nicht erreichbar: Service/Port/Logs pruefen (infrastrukturseitig).

## Referenzen
- `docs/workstreams/infrastruktur/DEV_ONBOARDING_CURSOR.md`
- `docs/workstreams/infrastruktur/TEAM_WORKFLOW_PROD_DEV.md`
- `docs/workstreams/infrastruktur/HOTFIX_CHECKLIST.md`
