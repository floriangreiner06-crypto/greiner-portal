# Phase 5 Umsetzungsplan nach Checkliste (2026-03-25)

Quelle:
- `docs/team/CHECKLISTE_AKTIV_CODE_PFAD_2026-03-25.md`
- Manifest: `backups/legacy-manifests/phase5_checkliste_decisions_20260325_091608.json`

## Entscheidungsstand

- `behalten`: 22
- `integrieren`: 9
- `parken/pruefen spaeter`: 2
- `verwerfen/archiv`: 0
- `fehlend/konflikt`: 0

## Bereits umgesetzt in dieser Session

- Integrationspaket A (Fahrzeuganlage) technisch abgesichert:
  - Feature-Check in `routes/werkstatt_routes.py`
  - JSON-Guard in `api/fahrzeuganlage_api.py` (401/403 als JSON)
- Integrationspaket B (Cashflow/Garantie/Gudat/PDF) geprüft:
  - `doc_to_pdf` robust gemacht (lazy import, klare Fehlermeldung bei fehlendem `reportlab`)

## Parken-Regel (ab sofort verbindlich)

Folgende Dateien werden aktuell nicht weiterentwickelt und nicht bereinigt:

- `static/css/hilfe.css`
- `api/whatsapp_inbound.py`

Umsetzung:
- Keine Refactors/Entfernung ohne neue Freigabe.
- Bei betroffenen Tickets zuerst Entscheidung revalidieren (`parken` -> `behalten` oder `integrieren`).

## Nächste konkrete Schritte (klein und sicher)

1. **BEHALTEN-Set final markieren** (nur Doku/Manifest, keine Codeänderung).
2. **Integrationsänderungen bündeln** (A + B) und optional als separaten Commit vorbereiten.
3. **Cleanup-Restbestand**: untracked außerhalb Code-Pfad mit derselben Methodik weiter reduzieren.

## Abschlusskriterium für diese Cleanup-Phase

- Entscheidungen sind vollständig dokumentiert.
- Integrationskandidaten A/B sind technisch stabil.
- Parken-Kandidaten sind klar abgegrenzt.
- Danach kann das Setup-Paket (Rules/Skills/Arbeitsplätze) auf sauberer Basis gebaut werden.

