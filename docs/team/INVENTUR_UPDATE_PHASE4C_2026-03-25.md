# Inventur-Update Phase 4C (scripts Reorg Paket 1)

Datum: 2026-03-25

## Durchgefuehrter Schritt

- Explorative/Einmal-Skripte in `scripts/archive/legacy-review/...` verschoben.
- Archivpfad in `.gitignore` aufgenommen:
  - `scripts/archive/legacy-review/`
- Manifest erstellt:
  - `backups/legacy-manifests/phase4c_scripts_move_explorative_20260325_083859.json`

## Verschobene Skripte (6)

- `scripts/motocost_network_probe.py`
- `scripts/veact_explore_api.py`
- `scripts/veact_explore_login.py`
- `scripts/locosoft_wsdl_explore_preis.py`
- `scripts/locosoft_wsdl_introspect.py`
- `scripts/provisions_januar_filter_test.py`

## Effekt

- Untracked-Count: `318 -> 312`

## Sicherheitsstatus

- Nur reversible Verschiebungen.
- Kein Eingriff in aktive API-/Route-/Template-Dateien.

