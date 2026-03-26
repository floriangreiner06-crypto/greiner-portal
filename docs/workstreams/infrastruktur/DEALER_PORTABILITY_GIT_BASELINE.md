# Dealer Portability - Git Baseline fuer gleiche Infrastruktur

## Zielbild

Greiner DRIVE soll auf mehreren Haendler-Instanzen mit gleicher Infrastruktur ausrollbar sein, ohne den Master-Stand zu zerbrechen.

## Baseline-Prinzipien

- Produktive Basis bleibt `main`.
- Feature-Entwicklung immer in separaten Branches.
- Integration nur ueber reviewbare PR-Pakete (Schema -> Backend -> Frontend -> Scripts).
- Keine haendlerspezifischen Secrets im Repo.

## Branch- und PR-Strategie

- `main`: stabiler produktiver Referenzstand
- `feature/*`: fachliche Features
- `fix/*`: Hotfixes
- Grosse Aenderungen immer in kleine PR-Pakete schneiden:
  1. `migrations/`
  2. Backend (`app.py`, `api/`, `routes/`, ...)
  3. Frontend (`templates/`, `static/`)
  4. `scripts/`

Referenz-Runbook: `docs/workstreams/infrastruktur/MERGE_ROLLOUT_PLAN_SANE_DRIVE_PRs.md`

## Konfigurations-Trennung (wichtig fuer Multi-Dealer)

- Dealer-spezifische Werte nur ueber Environment/DB-Konfiguration.
- Keine hardcodierten Hostnamen, IDs oder Zugangsdaten im Code.
- Navigation weiterhin DB-basiert (`navigation_items`) statt Template-Hardcoding.

## Rollout-Mindeststandard pro Dealer

1. Migrationen ausfuehren
2. Backend deployen und Services restarten
3. Frontend deployen, Browser-Cache erneuern
4. optionale Scripts getrennt freigeben
5. kurzer Smoke-Check mit Kernseiten und API-Endpunkten

## Governance fuer saubere Wiederverwendung

- Jede neue Funktion braucht:
  - SSOT-Quelle
  - kurze Doku im passenden Workstream
  - PR mit klarer Rollout-Notiz
- Kein Direktarbeiten auf `main`.
- Keine gemischten "Alles-in-einem"-PRs fuer produktive Rollouts.
