# Merge Rollout Plan Sane DRIVE PRs

## Zweck
Sicherer Merge- und Rollout-Ablauf fuer aufgeteilte, grosse Aenderungspakete.

## Reihenfolge
1. Migrations-PR
2. Backend-PR
3. Frontend-PR
4. Scripts-PR

## Vor jedem Merge
- PR ist `MERGEABLE` und in sauberem Zustand.
- Kritische Bugbot-Hinweise (High/Medium) behoben.
- Diffs stichprobenartig gegen Anforderungen geprueft.

## Nach jedem Merge
- `main` aktualisieren.
- Kurzer Smoke-Check der betroffenen Kernseiten/Funktionen.
- Bei Backend/Python-Aenderungen Service-Neustarts einplanen.

## Rollback-Grundsatz
- Kein Force-Push auf `main`.
- Ruecknahme per sauberem Revert-Commit.
- Ursache dokumentieren und erst danach neu ausrollen.

## Ergebnis
Nach Abschluss ist `main` konsolidiert und deploybar, mit nachvollziehbarer Historie und klaren Themengrenzen.
