# Inventur-Update Phase 4D (Runtime-Sicht)

Datum: 2026-03-25

## Was wurde jetzt anders gemacht?

- Klassifizierung nicht mehr nur nach Dateinamen, sondern nach **Server-Betriebssicht**:
  - Dienste laufen (`greiner-portal`, `greiner-test`, `celery-worker`, `celery-beat` aktiv)
  - Keine relevanten Timer/Crons als Laufzeitquelle gefunden
  - Untracked-Dateien in 4 Klassen einsortiert

## Ergebnis (aktueller Restbestand)

- `AKTIV_RUNTIME`: **0**
- `AKTIV_CODE_PFAD`: **33**
- `MANUELL_NUETZLICH`: **321**
- `LEGACY`: **9**

## Artefakte

- Voll-Manifest (JSON):
  - `backups/legacy-manifests/phase4_runtime_orientierte_klassifizierung_20260325_084413.json`
- Lesefassung (MD):
  - `backups/legacy-manifests/phase4_runtime_orientierte_klassifizierung_20260325_084413.md`

## Einfache Lesart

- **Runtime-kritisch** ist aktuell nichts von den untracked Dateien.
- Es gibt aber **33 Dateien im App-Code-Pfad** (z. B. `api/`, `routes/`, `templates/`, `static/`), die vor Bereinigung fachlich entschieden werden muessen.
- Der groesste Block ist **manuell nuetzlich** (Doku, Skripte, Migrationsdateien, Cleanup-Manifeste).
- **Legacy** sind jetzt vor allem bereits in `docs/archive/legacy-review/...` verschobene Altartefakte.

## Nächster Schritt (klar und risikoarm)

1. Die 33 `AKTIV_CODE_PFAD` Dateien als **behalten / integrieren / verwerfen** markieren.
2. Erst danach gezielte technische Bereinigung.

