# Inventur-Update Phase 4C3 (scripts Reorg Paket 3)

Datum: 2026-03-25

## Durchgefuehrter Schritt

- Fachanalyse-Einmalskripte (`planung_*`, `provisions_*`, `stueckzahl_analyse_*`) in Review-Archiv verschoben.
- Ziel:
  - `scripts/archive/legacy-review/20260325_084033/`
- Manifest:
  - `backups/legacy-manifests/phase4c_scripts_move_domain_analysis_20260325_084033.json`

## Verschobene Dateien (15)

- `scripts/planung_eintragen_abteilungsleiter.py`
- `scripts/planung_ergebnis_aus_aktuellen_daten.py`
- `scripts/planung_finde_zinskosten_konten.py`
- `scripts/planung_freigeben_2025_26.py`
- `scripts/planung_gewinnzone_standzeit_vorschlag.py`
- `scripts/planung_pragmatisch_2025_26.py`
- `scripts/planung_standort_anteile_vorjahr.py`
- `scripts/planung_szenario_gw_1000.py`
- `scripts/planung_szenario_landau_schliessung.py`
- `scripts/planung_vorschlag_belastbar.py`
- `scripts/provisions_analyse_doppelte_vin.py`
- `scripts/provisions_berechnung_kraus_jan2026.py`
- `scripts/provisions_vergleiche_db_mit_csv.py`
- `scripts/verkauf/stueckzahl_analyse_2025_nach_mitarbeiter.py`
- `scripts/verkauf/stueckzahl_analyse_nach_mitarbeiter.py`

## Effekt

- Untracked-Count: `301 -> 288`

## Sicherheitsstatus

- Nur reversible Verschiebungen in `scripts/archive/legacy-review`.
- Keine produktiven Kernmodule geaendert.

