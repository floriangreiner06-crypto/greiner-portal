# Inventur-Update Phase 4C4 (scripts Klassifizierung Restbestand)

Datum: 2026-03-25

## Durchgefuehrter Schritt

- Verbleibende untracked `scripts/*` **nur klassifiziert**, ohne Verschiebung/Loeschung.
- Manifest erstellt:
  - `backups/legacy-manifests/phase4c_scripts_classification_20260325_084119.json`

## Ergebnis

- Restbestand geprueft: **25** Dateien
- `KEEP_ACTIVE`: **19**
- `REVIEW_LATER`: **6**

## Kandidaten `REVIEW_LATER`

- `scripts/afa_abgleich_excel_locosoft.py`
- `scripts/afa_datev_pdf_anfangsbestand_locosoft.py`
- `scripts/afa_restbuchwert_nach_konto.py`
- `scripts/ecodms_api_folders_call.py`
- `scripts/ecodms_find_swagger_url.py`
- `scripts/marketing_locosoft_potenzial_analyse.py`

## Sicherheitsstatus

- Keine Datei verschoben oder geloescht.
- Reiner Klassifizierungs- und Dokumentationsschritt.

## Naechster Schritt

- Entweder:
  1. `REVIEW_LATER` ebenfalls in `scripts/archive/legacy-review/` verschieben (reversibel), oder
  2. als aktiv bestaetigen und im Repo behalten.

