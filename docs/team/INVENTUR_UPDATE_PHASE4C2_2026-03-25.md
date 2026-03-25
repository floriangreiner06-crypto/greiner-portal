# Inventur-Update Phase 4C2 (scripts Reorg Paket 2)

Datum: 2026-03-25

## Durchgefuehrter Schritt

- Konservatives Skript-Paket verschoben (nur `check_`, `export_`, `vergleiche_` Einmal-/Analyse-Skripte).
- Ziel:
  - `scripts/archive/legacy-review/20260325_083950/`
- Manifest:
  - `backups/legacy-manifests/phase4c_scripts_move_checks_exports_20260325_083950.json`

## Verschobene Dateien (11)

- `scripts/check_eautoseller_credentials.py`
- `scripts/check_hilfe_registry.py`
- `scripts/check_liquiditaet_locosoft_daten.py`
- `scripts/check_tek_743002_aktiv.py`
- `scripts/check_tek_heute_fakturierung.py`
- `scripts/export_bewertungskatalog.py`
- `scripts/export_doc_to_pdf.py`
- `scripts/export_liquiditaet_fahrzeug_auftraege_rechnungen.py`
- `scripts/export_locosoft_fahrzeugbestand_liste.py`
- `scripts/export_locosoft_mitarbeiter_excel.py`
- `scripts/vergleiche_tek_locosoft_vs_portal_feb2026.py`

## Effekt

- Untracked-Count: `312 -> 301`

## Sicherheitsstatus

- Nur reversible Verschiebungen in archivierten Review-Pfad.
- Keine Aenderungen an produktiven API-/Route-/Template-Dateien.

