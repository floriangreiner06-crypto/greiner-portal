# Kein SQLite – verbindliche Regel

**Stand:** 2026-02-25  
**Gültig für:** Alle neuen und geänderten Scripts und API-Module.

---

## Regel

- **SQLite darf nicht verwendet werden.** Weder `import sqlite3` noch Zugriffe auf `data/greiner_controlling.db` oder andere .db-Dateien für Portal-Daten.
- **Portal-Datenbank = PostgreSQL** (drive_portal auf 127.0.0.1). Alle Lese-/Schreibzugriffe auf diese DB ausschließlich über:
  - **API/Anwendung:** `api.db_utils.db_session()` oder `api.db_connection.get_db()`
  - **Scripts:** Ebenfalls `db_session()` / `get_db()` aus api; Projekt-Root für Imports: `sys.path.insert(0, '/opt/greiner-portal')` dann `from api.db_utils import db_session` etc.
- **Locosoft:** Unverändert `api.db_utils.get_locosoft_connection()` (PostgreSQL extern).
- **PostgreSQL-Syntax:** Platzhalter `%s`, Boolean `true`/`false`, `CURRENT_DATE`/`NOW()`, Tabellenprüfung über `information_schema.tables`. Siehe CLAUDE.md „SQL-Unterschiede“.

---

## Begründung

- Die Migration auf PostgreSQL (TAG 135) ist abgeschlossen. Die App nutzt nur noch PostgreSQL.
- Scripts, die weiterhin in SQLite schrieben, haben die App nicht gefüttert (z. B. Lieferscheine, Abteilungen, Caches). Das war eine Lücke der Migration.
- Einheitliche DB = eine Quelle der Wahrheit, weniger Fehler, keine versteckten „zwei Welten“.

---

## Umsetzung

- Bestehende Scripts, die noch sqlite3 nutzten, wurden bzw. werden auf PostgreSQL umgestellt (db_session/get_db, PostgreSQL-Syntax).
- Neue Scripts: Von vornherein nur PostgreSQL über api.db_connection / api.db_utils.
- Code-Reviews und Qualitätschecks: Kein neuer sqlite3-Code.

---

## Referenzen

- CLAUDE.md (Abschnitt „Kein SQLite“)
- .cursorrules (Haupt-Datenbank)
- docs/SQLITE_VERWEISE_AUDIT.md (Audit und Liste umgestellter Scripts)
