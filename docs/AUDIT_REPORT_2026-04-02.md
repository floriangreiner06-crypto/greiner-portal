# DRIVE Portal — Komplett-Audit Report
**Datum:** 2026-04-02  
**Umgebung:** /opt/greiner-test (develop)  
**Getestet:** 417 Endpunkte (146 Seiten + 271 APIs)

---

## ZUSAMMENFASSUNG

| Kategorie | CRITICAL | HIGH | MEDIUM | LOW |
|-----------|----------|------|--------|-----|
| Funktionale Bugs (500er) | 0 | 3 | 4 | 1 |
| Sicherheit | 3 | 6 | 6 | 1 |
| Hardcoded Prod-Pfade | — | 37 Dateien | 12 Dateien | ~30 Dateien |
| SQLite-Reste (Runtime) | — | 8 Dateien | 7 Dateien | — |
| SSOT-Verletzungen | 1 | 6 | 5 | — |

---

## 1. KAPUTTE ENDPUNKTE (HTTP 500)

### HIGH — Aktive Features betroffen

| # | Endpunkt | Ursache | Datei |
|---|----------|---------|-------|
| 1 | `/api/lager/leichen` | `%` in LIKE-Patterns kollidiert mit psycopg2 `%s` | `api/renner_penner_api.py:596` |
| 2 | `/api/werkstatt/problemfaelle` | Gemischte Platzhalter `?` (SQLite) + `%s` (PG) | `api/werkstatt_api.py:936` |
| 3 | `/api/werkstatt/schlechteste-auftraege` | Python f-string in SQL statt Parameterisierung | `api/werkstatt_api.py:626` |

### MEDIUM — Feature nicht funktional / funktioniert nur eingeloggt

| # | Endpunkt | Ursache | Datei |
|---|----------|---------|-------|
| 4 | `/api/finanzreporting/cube` | Tabelle `fact_bwa` fehlt | Star-Schema nie erstellt |
| 5 | `/api/finanzreporting/cube/metadata` | Tabelle `dim_standort` fehlt | Star-Schema nie erstellt |
| 6 | `/api/serviceberater/offene-auftraege-counts` | `@login_required` fehlt → AnonymousUser crash | `api/serviceberater_api.py:1632` |
| 7 | `/api/verkauf/nw-pipeline` | `@login_required` fehlt → AnonymousUser crash | `api/verkauf_api.py:1221` |

### LOW

| 8 | `/api/werkstatt/health` | SQLite `PRAGMA` in PG-Umgebung | `api/werkstatt_api.py:1047` |

### Persistenter Bug (beide Umgebungen)
**Auth Audit Log:** `_log_auth_event()` in `auth/auth_manager.py:559` — INSERT fehlt `success`-Spalte (NOT NULL). Jeder Login/Logout erzeugt einen stillen Fehler.

---

## 2. SICHERHEIT

### CRITICAL

| # | Finding | Detail |
|---|---------|--------|
| 1 | **Bankenspiegel komplett ohne Auth** | ALLE 10+ Routes in `routes/bankenspiegel_routes.py` haben kein `@login_required`. Finanzdaten (Konten, Transaktionen, Salden) sind ohne Login abrufbar. |
| 2 | **Azure AD Client Secret in Git** | `config/.env` Zeile 43: `GRAPH_CLIENT_SECRET=DuW8Q~...` — Microsoft 365 Mail-Zugang |
| 3 | **DB-Passwörter in Git** | `config/.env`: `DB_PASSWORD=DrivePortal2024`, `LOCOSOFT_PASSWORD=loco` |

### HIGH

| # | Finding | Detail |
|---|---------|--------|
| 4 | **Verkauf-Routes ohne Auth** | `/verkauf/auslieferung/detail` und `/verkauf/profitabilitaet` — kein `@login_required` |
| 5 | **WhatsApp Webhook Test offen** | `/whatsapp/webhook/test` — keine Auth, keine Signatur-Validierung |
| 6 | **MOBIS API ohne Auth** | 2 Endpunkte: `/api/mobis/teilebezug/order/<nr>`, `/verify/<nr>` |
| 7 | **75+ hardcoded Passwörter** | Gudat, Hyundai, Cognos, MOBIS, Leasys u.a. direkt im Quellcode |
| 8 | **Monitor-Token im Code** | `routes/werkstatt_routes.py:21`: `MONITOR_TOKEN = 'Greiner2024Werkstatt!'` |
| 9 | **Stack-Traces an Client** | 7+ Routes geben `traceback.format_exc()` in JSON zurück |

### MEDIUM

- F-String SQL (100+ Stellen) — aktuell sicher, aber fragiles Pattern
- Schwacher `SECRET_KEY` (`greiner-portal-secret-2025-change-me`)
- Kein CSRF-Schutz
- `SESSION_COOKIE_SECURE = False`
- 30+ Routes geben `str(e)` an Client zurück
- Keine Security-Headers (X-Frame-Options, CSP etc.)

---

## 3. HARDCODED PROD-PFADE

### Top 5 kritischste

| # | Datei | Problem |
|---|-------|---------|
| 1 | **`celery_app/tasks.py`** | ~80 hardcoded `/opt/greiner-portal/`-Pfade. JEDER Celery-Task in Develop führt Prod-Scripts aus. |
| 2 | **`scheduler/job_manager.py`** | `BASE_DIR = '/opt/greiner-portal'` — Scheduler schreibt in Prod-Verzeichnis |
| 3 | **`config/gunicorn.conf.py`** | Log-Dateien + PID nach `/opt/greiner-portal/logs/` |
| 4 | **`api/werkstatt_live_api.py`** | 5 Pfade für ML-Modelle, Daten, sys.path nach Prod |
| 5 | **`api/db_connection.py`** | SQLite-Fallback-Pfad `/opt/greiner-portal/data/greiner_controlling.db` |

**Weitere 32 Dateien** in api/, scripts/, tools/ mit hardcoded Prod-Pfaden (Details im Report).

---

## 4. SQLite-RESTE (Runtime)

| # | Datei | Problem |
|---|-------|---------|
| 1 | `scheduler/job_manager.py` | Gesamtes Scheduler-Subsystem nutzt sqlite3 |
| 2 | `api/organization_api.py:341` | Query gegen `sqlite_master` — wird auf PG fehlschlagen |
| 3 | `api/werkstatt_api.py` | PRAGMA, gemischte Platzhalter (→ 500er) |
| 4 | 7 Sync-Scripts | Noch sqlite3 statt PostgreSQL (teile, employees, etc.) |

---

## 5. SSOT-VERLETZUNGEN

### CRITICAL
| `api/preisvergleich_service.py` | Eigene DB-Verbindung mit **falschen Credentials** (`greiner`/`greiner2024` statt `drive_user`/`DrivePortal2024`). Bypassed beide SSOT-Module. |

### HIGH — Standort-Mappings (6 verschiedene Konventionen!)

| Datei | Mapping | Problem |
|-------|---------|---------|
| `standort_utils.py` (SSOT) | `{1: 'Deggendorf Opel', 2: 'Deggendorf Hyundai', 3: 'Landau Opel'}` | ✅ Korrekt |
| `api/employee_sync_service.py` | `{1: 'Deggendorf', 2: 'Deggendorf', 3: 'Landau'}` | ❌ Standort 2 = "Deggendorf" (falsch!) |
| `api/vacation_approver_service.py` | `{1: 'Deggendorf', 3: 'Landau'}` | ❌ Standort 2 fehlt komplett |
| `routes/planung_routes.py` | 5x `{1: 'Deggendorf', 2: 'Hyundai DEG', 3: 'Landau'}` | ❌ 5 Duplikate |
| `routes/controlling_routes.py` | 11+ hardcoded Standort-Logiken | ❌ Massivste Verletzung |
| `api/afa_api.py` | `{1: 'DEG', 2: 'HYU', 3: 'LAN'}` | ❌ Eigenes Format |

### HIGH — Direkte DB-Verbindungen (bypassen get_db/get_locosoft_connection)
- `api/vacation_api.py:2682` — inline `psycopg2.connect()` mit hardcoded Locosoft-Credentials
- `utils/locosoft_helpers.py` — eigene `get_locosoft_connection()` parallel zur SSOT

---

## 6. EMPFOHLENE PRIORITÄTEN

### Sofort fixen (Sicherheit + Funktionalität)

1. ⛔ **Bankenspiegel `@login_required` ergänzen** — Finanzdaten offen im Netz
2. ⛔ **`config/.env` aus Git entfernen** + `.gitignore` + Secrets rotieren
3. 🔧 **3 kaputte API-Endpunkte** fixen (Lager, Werkstatt × 2) — SQLite-Reste
4. 🔧 **Auth Audit Log** — `success`-Spalte im INSERT ergänzen
5. 🔧 **Fehlende `@login_required`** bei 4 Endpunkten nachziehen

### Kurzfristig (nächste Wochen)

6. `celery_app/tasks.py` — Pfade dynamisch machen (`pathlib` / env-Variable)
7. Standort-Mappings konsolidieren → alle auf `standort_utils.py` umstellen
8. `preisvergleich_service.py` — SSOT-Verbindung nutzen, falsche Credentials entfernen
9. Stack-Traces nicht an Client zurückgeben

### Mittelfristig

10. Hardcoded Passwörter in Credentials-Store verschieben
11. CSRF-Schutz einbauen
12. Security-Headers setzen
13. Scheduler von SQLite auf PostgreSQL migrieren
