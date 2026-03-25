# Inventurbericht Phase 2 (Legacy-Backup)

Datum: 2026-03-25  
Modus: Sicherung ohne Bereinigung (keine Loeschungen/Umbenennungen)

## Ziel

- Verwaiste High-Confidence-Artefakte sichern, bevor in spaeteren Phasen bereinigt wird.
- Risiken fuer Datenverlust minimieren.

## Kurzfazit

- Legacy-Snapshot erstellt: `backups/legacy/20260325_082648`
- Gesichert wurden **19** High-Confidence-Kandidaten (`*.bak*`, `*.old`, `*.tmp`, `*~`).
- **Keine** Datei im Arbeitsbaum geloescht oder verschoben.

## Gesicherte Kandidaten (High Confidence)

- `api/admin_api.py.bak_tag219`
- `api/bankenspiegel_api.py.bak_tag219`
- `api/kalkulation_helpers.py.bak`
- `api/vacation_api.py.bak_tag219`
- `api/verkauf_api.py.bak_tag219`
- `api/werkstatt_api.py.bak_20251210`
- `api/werkstatt_live_api.py.bak_awpreis`
- `api/zins_optimierung_api.py.bak_tag219`
- `celery_app/tasks.py.bak_dup`
- `config/credentials.json.bak`
- `config/credentials.json.bak.20260312`
- `config/credentials.json.bak.20260323_101456`
- `templates/aftersales/werkstatt_stempeluhr.html.bak`
- `templates/aftersales/werkstatt_uebersicht.html.bak_20251210`
- `templates/base.html.bak_leasys`
- `templates/base.html.bak_tag80`
- `templates/base.html.bak_vor_jahrespraemie`
- `templates/sb/werkstatt_stempeluhr.html.bak`
- `templates/sb/werkstatt_uebersicht.html.bak_20251210`

## Wichtiger Hinweis zu Phase 2

- Dieses Backup deckt nur **eindeutig verwaiste Backup-Artefakte** ab.
- Grosse Mengen an untracked Dateien (z. B. `docs/`, `scripts/`, `migrations/`, `.venv/`) sind **noch nicht** in Legacy kategorisiert.
- Diese Positionen gehen in Phase 3 in eine differenzierte Klassifikation: `AKTIV`, `UNKLAR`, `LEGACY`.

## Offene Risiken

- Hoher untracked-Bestand kann weiterhin zu Drift zwischen Server, Sync und Git fuehren.
- Ohne Branch-/PR-Hygiene bleibt die Deploybarkeit schwer nachvollziehbar.

## Naechster Schritt (Phase 3 Vorbereitung)

1. Untracked-Bestand in Kategorien aufteilen (`AKTIV`/`UNKLAR`/`LEGACY`).
2. Fuer `LEGACY`-Kandidaten zweite Backup-Welle mit Manifest bauen.
3. Erst danach gezielte Bereinigung mit Freigabe.

