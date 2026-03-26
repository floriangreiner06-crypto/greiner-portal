# Entwurf: Hilfe-Modul für DRIVE Portal

**Stand:** 2026-02-24  
**Basis:** CURSOR_PROMPT_HILFE_SYSTEM.md (inhaltlich), hier **angepasst an den aktuellen DRIVE-Stand und die Projekt-Arbeitsweise**. Noch keine Implementierung – reiner Entwicklungsvorschlag.

---

## 1. DRIVE-Stand und Arbeitsweise (Korrekturen zum Original-Prompt)

Der ursprüngliche Claude-Prompt ging von älterem Stand aus. Für die Umsetzung gilt:

| Thema | Original-Prompt | DRIVE-Realität |
|-------|-----------------|----------------|
| **Datenbank** | SQLite, `greiner_controlling.db` | **PostgreSQL** `drive_portal` (seit TAG 135). Alle neuen Tabellen in dieser DB. |
| **DB-Zugriff** | Eigenes SQLite-Handling | `api/db_connection.py` → `get_db()`; Platzhalter `%s`; Schema in `docs/DB_SCHEMA_POSTGRESQL.md`. |
| **Frontend** | Bootstrap 4 | **Bootstrap 5** (laut CLAUDE.md). |
| **Navigation** | In base.html / Sidebar | **DB-basiert:** Menüpunkte aus Tabelle `navigation_items`. Neue Einträge nur per **Migration** (`migrations/add_navigation_*.sql`) + Ausführung. Siehe CLAUDE.md Abschnitt „Navigation“. |
| **Deployment** | „Manuell kopieren, dann systemctl“ | **Server = Master.** Entwicklung auf `/opt/greiner-portal/`. Sync (`/mnt/greiner-portal-sync/`) ist Backup. Nach Migration: Agent führt Migration aus; nach Python-Änderungen: Agent startet `greiner-portal` neu. |
| **Volltextsuche** | SQLite FTS5 | **PostgreSQL:** `to_tsvector`, `tsquery`, GIN-Index auf `hilfe_artikel`. Kein FTS5. |
| **SQL-Syntax** | SQLite (`datetime('now')`, `INTEGER` für Boolean) | **PostgreSQL:** `NOW()`, `CURRENT_TIMESTAMP`, `boolean`, `SERIAL` statt AUTOINCREMENT. |
| **Auth** | @require_auth / @require_role | Unverändert; Decorators aus `decorators/auth_decorators.py`. |

Weitere Regeln: **SSOT** (keine doppelten DB-Helfer, zentrale Utils nutzen), **Redundanzen vermeiden**, Konsistenz (PostgreSQL-kompatibel, einheitliches Error-Handling, `logging.getLogger(__name__)`).

---

## 2. Phase 0: Codebase-Analyse (vor Implementierung)

Vor dem ersten Code:

1. **Projektstruktur:** `app.py` (Blueprints), `routes/`, `api/`, `templates/`, `templates/base.html`, `static/`, `decorators/auth_decorators.py`.
2. **Module inventarisieren:** Alle sichtbaren Module mit Haupt-Route(s), Template(s), Kurzbeschreibung, Zielgruppe/Rollen – als Grundlage für Hilfe-Kategorien und Starter-Artikel.
3. **Navigation:** Wie `navigation_items` und `api/navigation_utils.py` die Menüpunkte liefern; wo ein Eintrag „Hilfe“ sinnvoll hängt (eigenes Top-Level oder Unterpunkt).
4. **Auth:** Rollen, `current_user.can_access_feature(...)`, Pattern für geschützte Bereiche.

---

## 3. Architektur-Vorschlag

### 3.1 Dateien

```
/opt/greiner-portal/
├── api/
│   └── hilfe_api.py              ← REST-API für Hilfe
├── routes/
│   └── hilfe_routes.py           ← HTML-Routes
├── templates/
│   └── hilfe/
│       ├── hilfe_uebersicht.html
│       ├── hilfe_kategorie.html
│       ├── hilfe_artikel.html
│       └── hilfe_suche.html
├── static/
│   ├── css/
│   │   └── hilfe.css
│   └── js/
│       └── hilfe.js
├── migrations/
│   ├── add_hilfe_tables.sql      ← PostgreSQL
│   └── add_navigation_hilfe.sql  ← Navi-Eintrag
```

Optional später: Hilfe-Widget (z. B. `templates/components/hilfe_widget.html`), Chat-Tabelle für KI-Vorbereitung.

### 3.2 Datenbank (PostgreSQL drive_portal)

- **hilfe_kategorien:** id (SERIAL), name, slug (UNIQUE), beschreibung, icon, sort_order, modul_route, aktiv (boolean), created_at, updated_at (beide TIMESTAMP mit NOW()).
- **hilfe_artikel:** id (SERIAL), kategorie_id (FK), titel, slug, inhalt (TEXT), inhalt_format ('markdown'|'html'), tags (TEXT), sort_order, sichtbar_fuer_rollen (TEXT, nullable), aufrufe, hilfreich_ja, hilfreich_nein, aktiv (boolean), erstellt_von, created_at, updated_at.
- **Volltextsuche:** Spalte z. B. `tsv tsvector GENERATED ALWAYS AS (to_tsvector('german', coalesce(titel,'') || ' ' || coalesce(inhalt,'') || ' ' || coalesce(tags,''))) STORED` + GIN-Index auf `tsv`. Suche mit `to_tsquery('german', ...)` und `tsv @@ ...`.
- **hilfe_feedback:** id, artikel_id, user_id, hilfreich (boolean), kommentar (TEXT), created_at.
- Optional **hilfe_chat_verlauf** für spätere KI-Integration (session_id, user_id, nachricht, rolle, kontext_modul, kontext_seite, created_at).

Alle Timestamps: `DEFAULT NOW()` bzw. `CURRENT_TIMESTAMP`. Kein SQLite-spezifisches Schema.

### 3.3 API (Blueprint `/api/hilfe`)

- `GET /api/hilfe/kategorien` — aktive Kategorien inkl. Artikelanzahl  
- `GET /api/hilfe/kategorie/<slug>` — Kategorie + Artikel  
- `GET /api/hilfe/artikel/<id>` — Einzelartikel (aufrufe erhöhen)  
- `GET /api/hilfe/suche?q=...` — Volltextsuche (PostgreSQL tsvector/tsquery)  
- `POST /api/hilfe/artikel/<id>/feedback` — Body: hilfreich, optional kommentar  
- `GET /api/hilfe/beliebt` — z. B. Top 10 nach aufrufe  
- `GET /api/hilfe/health` — optional Health-Check  

Auth: mindestens `@require_auth` für alle Lese-Endpoints; Admin-Routen (falls API für Admin-UI) mit `@require_role('admin')`.

### 3.4 HTML-Routes

- `GET /hilfe` — Übersicht Kategorien  
- `GET /hilfe/<kategorie_slug>` — Artikel einer Kategorie  
- `GET /hilfe/artikel/<id>` — Einzelartikel  
- `GET /hilfe/suche?q=...` — Suchergebnisse  
- Admin (nur mit Admin-Rolle): `/hilfe/admin`, `/hilfe/admin/neu`, `/hilfe/admin/bearbeiten/<id>`, `POST /hilfe/admin/speichern`

### 3.5 Navigation

- Eintrag in `navigation_items` per Migration (`add_navigation_hilfe.sql`): parent_id passend setzen (z. B. null für Top-Level oder ID eines bestehenden Menüpunkts), label z. B. „Hilfe“, url `/hilfe`, icon, order_index, requires_feature/role_restriction nach Bedarf. Nach Anlegen der Migration: **Migration ausführen** (Agent: `PGPASSWORD=... psql ... -f migrations/add_navigation_hilfe.sql`).

---

## 4. Frontend (Vorschlag)

- **Konsistent** mit DRIVE: Bootstrap 5, bestehendes Layout/Sidebar, gleiche Farben/Icons (z. B. FontAwesome wie im Rest).
- **Übersicht:** Kacheln/Listen pro Kategorie mit Artikelanzahl; prominente Suchleiste.
- **Artikel:** Breadcrumb (Hilfe > Kategorie > Titel), Inhalt (Markdown serverseitig mit z. B. `markdown`-Library oder Frontend mit marked.js – einheitlich mit dem Rest entscheiden). Feedback „War dieser Artikel hilfreich? 👍 👎“.
- **Optional – Hilfe-Widget:** Schwebendes Icon (z. B. unten rechts), zeigt kontextbezogene Artikel je nach aktuellem Modul (z. B. `data-hilfe-modul="urlaubsplaner"` im Body). Erst ohne KI: Suche in Hilfe-Artikeln (FTS) und Anzeige der Treffer; später Platzhalter für KI-Chat.

---

## 5. Initiale Hilfe-Artikel

Nach Phase 0 für **jedes** vorhandene Modul mindestens 3–5 Starter-Artikel anlegen, z. B.:

- **Allgemein:** Login, Aufbau der Navigation, Ansprechpartner bei Problemen.
- **Pro Modul:** Was kann ich hier tun? Die 2–3 häufigsten Aktionen Schritt-für-Schritt; wichtige Begriffe/Kennzahlen.

Artikel als **Migration** (INSERT in `hilfe_artikel`/`hilfe_kategorien`) oder als Seed-Script, damit reproduzierbar. Format der Artikel: z. B. Markdown mit Kurz-Antwort, Schritt-für-Schritt, Hinweise, verwandte Themen.

---

## 6. Optionale Erweiterung: KI-Chat

- Chat-UI vorbereiten, **ohne** KI-Backend: User-Frage → Volltextsuche in Hilfe-Artikeln → Anzeige der besten Treffer als „Antwort“.
- Tabelle `hilfe_chat_verlauf` für spätere Nutzung (z. B. RAG mit Claude/Bedrock). Kein eigener Endpoint für KI in Phase 1.

---

## 7. Technische Vorgaben (DRIVE-konform)

- **DB:** Nur PostgreSQL `drive_portal`, Verbindung über `get_db()` aus `api/db_connection.py`.
- **Auth:** `@require_auth`, `@require_role('admin')` wie in anderen Modulen; keine Änderung am bestehenden Auth-System.
- **Keine neuen Frameworks:** Kein Tailwind, kein React/Vue; Bootstrap 5 + jQuery wie im Rest.
- **Keine externen API-Calls** für die Basis-Funktionalität.
- **Migrationen:** PostgreSQL-Syntax; nach Anlegen vom Agent ausführen. Nach Python-Änderungen: `sudo systemctl restart greiner-portal`.

---

## 8. Vorgeschlagene Reihenfolge

1. **Phase 0:** Codebase lesen, Module/Navi/Auth dokumentieren.  
2. **Migrationen:** `add_hilfe_tables.sql` (PostgreSQL), `add_navigation_hilfe.sql` anlegen und ausführen.  
3. **Backend:** `api/hilfe_api.py`, `routes/hilfe_routes.py`, Blueprint in `app.py` registrieren.  
4. **Frontend:** Templates + CSS/JS, Übersicht/Kategorie/Artikel/Suche.  
5. **Inhalt:** Starter-Artikel pro Modul (Migration oder Seed).  
6. **Optional:** Hilfe-Widget (kontextbezogen, FTS-basiert).  
7. **Test:** Manuell + Logs prüfen, Navi-Eintrag sichtbar.

---

## 9. Offene Punkte (Entscheidung vor Start)

- Position des Hilfe-Menüpunkts (Top-Level vs. Unterpunkt).  
- Ob das schwebende Widget in der ersten Ausbaustufe mit implementiert werden soll.  
- Markdown-Rendering: serverseitig (Python) oder clientseitig (z. B. marked.js) – Abgleich mit anderen DRIVE-Seiten, die bereits Markdown nutzen.

Mit diesem Entwurf ist das Hilfe-Modul an den **aktuellen DRIVE-Stand und die Arbeitsweise** (PostgreSQL, Server=Master, DB-Navigation, SSOT, Agent führt Migrationen/Neustarts aus) angepasst. Nach Freigabe kann die Implementierung schrittweise erfolgen.
