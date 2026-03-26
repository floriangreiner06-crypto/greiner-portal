# Merge- und Rollout-Plan: Sane-Drive PR-Split

## Ziel

Stabile Integration der aufgeteilten Entwicklungsstände in klaren, risikoarmen Schritten auf Basis des aktuell stabil laufenden `main`-Standes.

## Betroffene PRs

1. PR #2: Migrationen (`feature/sane-drive-migrations`)
2. PR #3: Backend (`feature/sane-drive-backend`)
3. PR #4: Frontend (`feature/sane-drive-frontend`)
4. PR #5: Scripts (`feature/sane-drive-scripts`)

PR #1 bleibt Draft/Referenz und wird nicht direkt gemerged.

## Merge-Reihenfolge (verbindlich)

1. PR #2 mergen
2. PR #3 mergen
3. PR #4 mergen
4. PR #5 mergen

## Checkliste pro Schritt

### Nach PR #2 (Migrationen)

- Migrationen aus `migrations/` in der Zielumgebung ausführen.
- Prüfen, ob alle SQL-Skripte ohne Fehler durchlaufen.
- Schema-Sanity-Check auf neue Tabellen/Spalten (insbesondere Navigation, Provision, Urlaub, Verkauf, Hilfe).

### Nach PR #3 (Backend)

- Backend-Service neu starten:
  - `sudo systemctl restart greiner-portal`
- Falls Celery-Tasks betroffen (hier ja), zusätzlich:
  - `sudo systemctl restart celery-worker celery-beat`
- Kurzcheck Logs:
  - `sudo journalctl -u greiner-portal -n 200 --no-pager`

### Nach PR #4 (Frontend)

- Kein Service-Restart notwendig (Template/Static-Änderungen).
- Browser Hard-Reload (Ctrl+F5).
- Sichtprüfung kritischer Bereiche: Controlling, Verkauf, Werkstatt, WhatsApp.

### Nach PR #5 (Scripts)

- Kein sofortiger Produktiv-Effekt ohne manuelle Ausführung.
- Nur betroffene operative Skripte bei Bedarf mit Testdaten prüfen.

## Minimale Smoke-Checks nach #3 und #4

- Login und Startseite laden.
- Kernseiten öffnen: Controlling, Verkauf, Werkstatt.
- 2-3 zentrale API-Aufrufe auf JSON-Antwort prüfen.
- Keine neuen 500er/Tracebacks in Portal-Logs.

## Rollback-Leitplanke

- Bei Problemen jeweils letzten Merge-Revert auf PR-Ebene durchführen.
- Kein Force-Push auf `main`.
- Rollback in gleicher Granularität wie Merge-Reihenfolge.

## Verantwortlichkeit

- Merge-Freigabe: nach kurzer Sichtprüfung der jeweiligen PR.
- Technische Durchführung: Infrastruktur-Flow gemäß obiger Reihenfolge und Checkliste.
