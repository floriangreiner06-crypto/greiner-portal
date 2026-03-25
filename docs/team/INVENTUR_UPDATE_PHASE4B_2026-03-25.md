# Inventur-Update Phase 4B (docs Reorg Paket 1)

Datum: 2026-03-25

## Ziel

- Untracked-Dokumentation im `docs`-Root reduzieren.
- Nur klar eingrenzbare, reversible Verschiebungen durchfuehren.

## Durchgefuehrter Schritt

- 4 Vanessa-Testanleitungen aus dem `docs`-Root in ein Review-Archiv verschoben:
  - Zielpfad: `docs/archive/legacy-review/vanessa-guides/20260325_083421/`
- Manifest erstellt:
  - `backups/legacy-manifests/phase4b_docs_move_vanessa_20260325_083421.json`

## Verschobene Dateien

- `docs/TESTANLEITUNG_VANESSA.md`
- `docs/TESTANLEITUNG_MITARBEITERVERWALTUNG_UND_URLAUBSPLANER_VANESSA.md`
- `docs/TESTANLEITUNG_VANESSA_URLAUBSPLANER_UND_MITARBEITERVERWALTUNG.md`
- `docs/TESTANLEITUNG_VANESSA_URLAUBSSPERRE_UND_ROLLEN.md`

## Effekt

- Untracked-Count: `326 -> 323`

## Kommentar

- Dieses Paket ist absichtlich klein und reversibel.
- Der grosse Block untracked `docs/workstreams/*` bleibt unberuehrt und wird in weiteren Paketen fachlich getrennt (`aktiv` vs `archiv`).

