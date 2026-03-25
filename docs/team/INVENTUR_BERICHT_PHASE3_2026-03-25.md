# Inventurbericht Phase 3 (Klassifizierung + Legacy-Welle 2)

Datum: 2026-03-25  
Modus: Klassifizierung ohne Loeschung im Projektbaum

## Ergebnis

- Untracked-Bestand wurde automatisch in `AKTIV / UNKLAR / LEGACY` klassifiziert.
- Manifest erzeugt:
  - `backups/legacy-manifests/phase3_klassifizierung_20260325_082811.json`
  - `backups/legacy-manifests/phase3_klassifizierung_20260325_082811.md`
- Zweite Legacy-Backup-Welle erstellt:
  - `backups/legacy/phase3_20260325_082815`

## Kennzahlen

- `AKTIV`: 366
- `UNKLAR`: 3176
- `LEGACY`: 7

Hinweis: Die sehr hohe `UNKLAR`-Menge entsteht primaer durch lokale Tooling-/Umgebungsartefakte (insbesondere `.venv`) und weitere untracked Dokumente/Ordner.

## In Wave 2 gesicherte Legacy-Dateien (7)

- `api/admin_api.py.bak_tag219`
- `api/bankenspiegel_api.py.bak_tag219`
- `api/vacation_api.py.bak_tag219`
- `api/verkauf_api.py.bak_tag219`
- `api/zins_optimierung_api.py.bak_tag219`
- `config/credentials.json.bak.20260312`
- `config/credentials.json.bak.20260323_101456`

## Empfohlene Cleanup-Reihenfolge (Phase 4)

1. `.venv` aus Repo-Sicht entschlacken (`.gitignore` und Arbeitskonventionen pruefen).
2. `docs/` untracked in `AKTIV` vs `ARCHIV` trennen (inkl. Namenskonvention fuer Legacy-Doku).
3. `scripts/` und `migrations/` untracked einzeln fachlich freigeben (behalten oder archivieren).
4. Danach erst gezielte Loesch-/Verschiebeaktionen (nur aus `LEGACY` und freigegebenen `ARCHIV`-Kandidaten).

## Sicherheitsstatus

- Bis jetzt wurden nur Sicherungen erzeugt und Berichte geschrieben.
- Es gab keine destruktiven Git-Operationen und keine Bereinigung im Live-Arbeitsbaum.

