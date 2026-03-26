# Hilfe-Modul — Arbeitskontext

## Status: Aktiv (Phase 1 + Freigabe umgesetzt)
## Letzte Aktualisierung: 2026-02-24

## Beschreibung

Das **Hilfe-Modul** soll allen DRIVE-Nutzern kontextbezogene Hilfe zu den Portal-Modulen bieten: kategorisierte Artikel, Volltextsuche, optional ein schwebendes Hilfe-Widget und perspektivisch KI-Chat auf Basis der Hilfe-Inhalte.

## Projektkontext

- Workstream wurde am 2026-02-24 angelegt.
- Grundlage: Ein von Claude (claude.ai) erstellter Prompt liegt im Windows-Sync unter `docs/workstreams/Hilfe/CURSOR_PROMPT_HILFE_SYSTEM.md`. Dieser Prompt kennt **nicht** den aktuellen DRIVE-Stand (PostgreSQL, Bootstrap 5, DB-Navigation, Server=Master, SSOT). Daher existiert im Repo der **DRIVE-adaptierte Entwurf**: `ENTWURF_HILFE_MODUL.md` in diesem Ordner.
- Phase 1 (Migrationen, API, Routes, Templates, Seed) und **Freigabe-Prozess** sind umgesetzt. Nächste Schritte: KI (Bedrock), Schulung nach Rolle (siehe KONZEPT_KI_FREIGABE_SCHULUNG.md).

## Geplante Module & Dateien (nach Entwurf)

### APIs
- `api/hilfe_api.py` — REST-API für Kategorien, Artikel, Suche, Feedback

### Routes
- `routes/hilfe_routes.py` — HTML-Routes (/hilfe, /hilfe/artikel/…, /hilfe/admin)

### Templates
- `templates/hilfe/` — hilfe_uebersicht.html, hilfe_kategorie.html, hilfe_artikel.html, hilfe_suche.html
- Optional: Hilfe-Widget als Jinja2-Include für base.html

### DB (PostgreSQL drive_portal)
- Tabellen: `hilfe_kategorien`, `hilfe_artikel`, `hilfe_feedback`, ggf. `hilfe_chat_verlauf` (für spätere KI-Vorbereitung)
- Volltextsuche: PostgreSQL `tsvector`/`to_tsvector`. **Freigabe:** `hilfe_artikel.freigabe_status` (entwurf/freigegeben), `freigegeben_am`, `freigegeben_von`; nur freigegebene Artikel in der öffentlichen Hilfe.

### Navigation
- Neuer Menüpunkt über **DB-Navigation** (`navigation_items`), nicht hardcoded in base.html. Migration `migrations/add_navigation_hilfe.sql` anlegen und ausführen.

## Abhängigkeiten

- **Auth (auth-ldap):** `@require_auth`, `@require_role('admin')` für Admin-Bereich; Sichtbarkeit von Artikeln optional nach Rolle (`sichtbar_fuer_rollen`).
- **Bestehende Module:** Hilfe-Inhalte orientieren sich an den tatsächlich vorhandenen Modulen (Routes, Features) — Phase 0 im Entwurf: Codebase analysieren.

## Wichtige Dateien in diesem Workstream

| Datei | Zweck |
|-------|--------|
| `CONTEXT.md` | Dieser Arbeitskontext |
| `ENTWURF_HILFE_MODUL.md` | Entwicklungsvorschlag, an DRIVE-Stand und Arbeitsweise angepasst |
| `PHASE_0_CODEBASE_ANALYSE.md` | Phase-0-Analyse: Projektstruktur, Modul-Inventar, Navigation, Auth (2026-02-24) |
| `CURSOR_PROMPT_HILFE_SYSTEM.md` | Original-Prompt (von Claude/claude.ai); technisch veraltet (SQLite, Bootstrap 4), inhaltlich Referenz. **Umsetzung:** ENTWURF_HILFE_MODUL.md |
| `KONZEPT_KI_KONTEXT_INJECTION.md` | Kontext-Injection: KI kann fehlende Berechnungsdetails (z. B. Breakeven) ergänzen, wenn SSOT-Kontext aus Registry mitgesendet wird. |
| `hilfe_ki_kontext_registry.md` | Registry: pro Thema (z. B. TEK/Breakeven) Schlüsselwörter + „Kontext für KI“ (fachliche SSOT-Beschreibung) für „Mit KI erweitern“. |
| `REGISTRY_AKTUELL_HALTEN.md` | **Prozess:** Wie die Kontext-Registry aktuell bleibt (Quellen-Zuordnung Code → Eintrag, Checkliste bei fachlichen Änderungen). |

## Nächste Schritte (nach Freigabe des Entwurfs)

1. ~~Phase 0: Codebase-Analyse (Module, Routes, Navi, Auth).~~ → **Erledigt:** siehe `PHASE_0_CODEBASE_ANALYSE.md`.
2. Migration für Hilfe-Tabellen (PostgreSQL-Syntax) anlegen und ausführen.
3. API + Routes + Templates implementieren (Blueprint-Pattern wie bestehende Module).
4. Navigation-Eintrag „Hilfe“ per Migration anlegen.
5. Initiale Hilfe-Artikel (pro Modul 3–5 Starter-Artikel) anlegen.
6. Optional: Hilfe-Widget (kontextbezogen, ohne KI zunächst FTS-basierte Vorschläge).

## Offen / Nächste Umsetzung

- **„Mit KI erweitern“** (Bedrock): Button im Hilfe-Admin; bei Aufruf **Kontext aus Registry** (z. B. Tags `tek`/`breakeven` → TEK/Breakeven-Snippet aus `hilfe_ki_kontext_registry.md`) an Prompt anhängen, damit die KI Berechnungsdetails (rollierend, Werktage, BWA-Kosten) korrekt ergänzt.
- Schulung nach Rolle (Route „Meine Schulung“, Filter nach Rolle, optional „Als gelesen“).

## Offene Entscheidungen

- Wo soll der Hilfe-Menüpunkt liegen (eigenes Top-Level oder unter einem bestehenden Menü)?
- Soll das schwebende Widget in Phase 1 mit rein oder erst später?
