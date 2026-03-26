# Fahrzeuganlage-Modul — Vorschlag: Wie es weitergeht

**Erstellt:** 2026-02-20  
**Grundlage:** CONTEXT.md (Werkstatt), CLAUDE.md, FAHRZEUGANLAGE_UMSETZBARKEITSPLAN_v2.md, CURSOR_PROMPT_FAHRZEUGANLAGE.md  
**Status:** Vorschlag, noch kein Code

---

## 1. Kurzfassung der Vorarbeit

- **Ziel:** Neukunden + Fahrzeuge nicht mehr manuell abtippen (5–8 Min/Anlage, ~15 % Fehlerrate), sondern Fahrzeugschein fotografieren → KI-OCR (AWS Bedrock, Claude, Frankfurt) → Prüfen & Copy nach Locosoft.
- **Phase 0:** AWS Bedrock ist eingerichtet (Account, eu-central-1, IAM User, Anthropic freigeschaltet). Offen: `boto3` auf dem Server, Credentials in `config/credentials.json`, Connectivity-Test.
- **Phase 1 (MVP):** Scan & Copy – Upload, OCR, editierbare Maske, Dublettencheck, Copy-to-Clipboard, Scan-Archiv. Geplante Laufzeit: 2–3 TAGs.
- **Phase 2:** Klärung Locosoft-API / DAT für spätere Anbindung.

Die zwei .md liegen aktuell nur im **Windows-Sync** unter  
`F:\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\werkstatt\Fahrzeuganlage\`  
(auf dem Server: `/mnt/greiner-portal-sync/docs/workstreams/werkstatt/Fahrzeuganlage/`).  
Im Workspace `/opt/greiner-portal` existiert der Ordner **Fahrzeuganlage** noch nicht – die Doku sollte für eine gemeinsame Basis entweder ins Repo übernommen oder beim Sync mitgeführt werden.

---

## 2. Anpassungen an die bestehende DRIVE-Architektur

Die Vorarbeit ist stimmig, muss aber an drei Stellen an den aktuellen Stand des Portals angepasst werden.

### 2.1 Datenbank: PostgreSQL statt SQLite

- **In den Docs:** Scan-Archiv in SQLite (`fahrzeugschein_scans` in `data/greiner_controlling.db`).
- **Im Projekt:** Seit TAG 135 ist **PostgreSQL** die Haupt-DB (`drive_portal`). SQLite wird nur noch als Legacy geführt (CLAUDE.md, DB_SCHEMA_POSTGRESQL.md).
- **Vorschlag:** Tabelle **`fahrzeugschein_scans`** in **PostgreSQL** anlegen:
  - Neue **Migration:** `migrations/add_fahrzeugschein_scans.sql` mit `CREATE TABLE fahrzeugschein_scans (...)` in PostgreSQL-Syntax (SERIAL, TIMESTAMP, TEXT, INTEGER, REAL, etc.).
  - Laufzeit-Zugriff über `api/db_connection.py` → `get_db()` wie in allen anderen Modulen.
  - Keine Nutzung von `data/greiner_controlling.db` für dieses Modul.

### 2.2 Navigation: DB-basiert, nicht hardcoded in base.html

- **In den Docs:** Neuer Menüpunkt in `base.html` eintragen.
- **Im Projekt:** Menüpunkte kommen aus der Tabelle **`navigation_items`** (CLAUDE.md: „Navigation DB-basiert“). `base.html` enthält nur Fallback, wenn `USE_DB_NAVIGATION=false`.
- **Vorschlag:**
  - **Migration** für Navi-Punkt: z. B. `migrations/add_navigation_fahrzeuganlage.sql` – INSERT in `navigation_items` mit passendem `parent_id` (z. B. unter „Service“ / „Werkstatt“), `url` z. B. `/werkstatt/fahrzeuganlage` oder `/aftersales/fahrzeuganlage`, `requires_feature` z. B. `aftersales` oder eigenes Feature `fahrzeuganlage`.
  - Optional: Eintrag in `scripts/migrate_navigation_items.py` für künftige DB-Neuaufbauten.
  - Nur bei Bedarf Fallback in `base.html` ergänzen.

### 2.3 Scanner-Logik: Wo platzieren?

- **In den Docs:** Neues Verzeichnis `services/fahrzeugschein_scanner.py`.
- **Im Projekt:** Es gibt **kein** `services/`-Verzeichnis; fachliche Logik liegt in `api/` (z. B. `api/werkstatt_live_api.py`, `api/gudat_data.py`).
- **Vorschlag (zwei saubere Optionen):**
  - **Option A:** Scanner-Klasse in **`api/fahrzeuganlage_api.py`** (kompakt, alles an einem Ort), oder
  - **Option B:** Eigene Datei **`api/fahrzeugschein_scanner.py`** (oder `api/fahrzeuganlage_scanner.py`) und von `api/fahrzeuganlage_api.py` importieren – analog zu `gudat_data.py` vs. `gudat_api.py`.

Empfehlung: **Option B**, damit API-Routes schlank bleiben und der Scanner testbar/getrennt wartbar ist.

---

## 3. Dublettencheck Locosoft

- **Quelle:** Read-Only Zugriff auf Locosoft-Daten. Im Portal erfolgt das über **`api/db_utils.get_locosoft_connection()`** bzw. gespiegelte Tabellen in **PostgreSQL** (loco_*), siehe DB_SCHEMA_POSTGRESQL.md.
- **Relevante Tabelle:** `loco_vehicles` (Fahrzeuge) – Abfrage z. B. nach FIN und/oder Kennzeichen (`license_plate`). Ggf. Spaltennamen in Locosoft-Schema prüfen (docs/DB_SCHEMA_LOCOSOFT.md oder vorhandene Nutzung von `loco_vehicles`).
- **Vorschlag:** Dublettencheck in der Fahrzeuganlage-API implementieren: bei vorhandener FIN/Kennzeichen-Angabe Abfrage gegen `loco_vehicles` (oder gegen Portal-PostgreSQL, falls die Locosoft-Spiegel dort bereits die nötigen Felder haben). Kein Schreiben in Locosoft in Phase 1.

---

## 4. Konkrete nächste Schritte (Reihenfolge)

1. **Doku ins Repo/Sync klären**  
   - Ordner `docs/workstreams/werkstatt/Fahrzeuganlage/` im Workspace anlegen und die beiden .md aus dem Sync dorthin kopieren (oder Sync so nutzen, dass dieser Ordner mit ins Repo kommt), damit alle am gleichen Stand arbeiten.

2. **Server-Voraussetzungen Phase 0 abschließen**  
   - Im venv: `pip install boto3`  
   - In `config/credentials.json`: Block **`aws_bedrock`** ergänzen (region, access_key_id, secret_access_key, model_id, max_tokens, temperature).  
   - Kleiner Connectivity-Test (wie im CURSOR_PROMPT beschrieben) ausführen.

3. **PostgreSQL-Migration für Scans**  
   - `migrations/add_fahrzeugschein_scans.sql` anlegen (Schema aus Umsetzbarkeitsplan/Cursor-Prompt in PostgreSQL-Syntax übersetzen: SERIAL, DEFAULT NOW(), Indizes auf fin, kennzeichen, scan_date).  
   - Migration auf drive_portal ausführen.

4. **Navigation**  
   - `migrations/add_navigation_fahrzeuganlage.sql` anlegen und ausführen; ggf. `migrate_navigation_items.py` anpassen.  
   - Feature/Rechte: `config/roles_config.py` prüfen – ob `aftersales` oder neues Feature `fahrzeuganlage` für den Zugriff verwendet wird.

5. **Backend**  
   - **Scanner:** `api/fahrzeugschein_scanner.py` (oder `api/fahrzeuganlage_scanner.py`) mit Klasse aus dem Cursor-Prompt, Credentials aus `credentials.json` (zentral, kein Secret in Code).  
   - **API:** `api/fahrzeuganlage_api.py` – Blueprint mit POST/GET/PUT und GET check-duplicate, GET health; alle Endpoints mit `@require_auth`, ggf. Feature-Check.  
   - **Routes:** `routes/fahrzeuganlage_routes.py` – z. B. eine Route für die Seite `/werkstatt/fahrzeuganlage` (oder gewählte URL aus Navigation).  
   - **App:** In `app.py` Blueprints registrieren.

6. **Frontend**  
   - Template `templates/fahrzeuganlage.html` (von `base.html` erben, Bootstrap 4 + jQuery), Layout und Funktionen wie im Cursor-Prompt (Upload/Kamera, Vorschau, Scannen, editierbare Felder, Confidence, Copy, Dublettenhinweis, Historie).  
   - Upload-Pfad: z. B. `data/uploads/fahrzeugscheine/` – Verzeichnis anlegen, DSGVO-Hinweis (lokale Speicherung, optional Löschfrist) in Doku/Code kommentieren.

7. **CONTEXT.md Werkstatt aktualisieren**  
   - Neues Modul „Fahrzeuganlage“ mit Kurzbeschreibung, Dateien (api, routes, template, migration), Status Phase 1, Verweis auf `docs/workstreams/werkstatt/Fahrzeuganlage/`.

8. **Test & Freigabe**  
   - Manuell: Upload, OCR, Edit, Copy, Dublettencheck, Health.  
   - Danach ggf. Phase 2 (Locosoft/DAT) planen.

---

## 5. Offene Punkte / Entscheidungen

| Thema | Optionen / Hinweis |
|-------|---------------------|
| **URL** | `/werkstatt/fahrzeuganlage` vs. `/aftersales/fahrzeuganlage` – an bestehende Navi-Struktur (Service → Werkstatt / After Sales) anpassen. |
| **Feature/Recht** | Eigenes Feature `fahrzeuganlage` in `roles_config.py` vs. Nutzung von `aftersales` – abhängig davon, wer das Modul nutzen soll (nur Service/Werkstatt). |
| **Bild-Löschung** | DSGVO: Optionale automatische Löschung von Bildern nach X Tagen (Celery-Task oder Cron) – in Phase 1 dokumentieren, Implementierung optional. |
| **Locosoft-Schema** | Für Dublettencheck exakte Spaltennamen in `loco_vehicles` (FIN, Kennzeichen) aus docs oder DB prüfen. |
| **Phase 2** | Kein Code in Phase 1 für Locosoft-Import; nur Klärung, ob Locosoft-API für Stammdaten-Import existiert und ob DAT angebunden werden soll. |

---

## 6. Dateien-Übersicht (angepasst)

**Neu (Vorschlag):**

- `api/fahrzeugschein_scanner.py` (oder `api/fahrzeuganlage_scanner.py`)
- `api/fahrzeuganlage_api.py`
- `routes/fahrzeuganlage_routes.py`
- `templates/fahrzeuganlage.html`
- `migrations/add_fahrzeugschein_scans.sql`
- `migrations/add_navigation_fahrzeuganlage.sql`
- `data/uploads/fahrzeugscheine/` (Verzeichnis)

**Zu ändern:**

- `app.py` – Blueprints registrieren
- `config/credentials.json` – Block `aws_bedrock`
- `config/roles_config.py` – ggf. Feature für Fahrzeuganlage
- `docs/workstreams/werkstatt/CONTEXT.md` – Modul + Status
- Optional: `scripts/migrate_navigation_items.py` – Navi-Eintrag für Fahrzeuganlage
- Optional: `templates/base.html` – Fallback-Navi nur wenn gewünscht

**Nicht:** Keine neue SQLite-Tabelle für dieses Modul; keine Menüpunkte nur in `base.html` ohne DB-Migration. **Kein Schreiben in Locosoft-PostgreSQL** – Stammdaten-Anlage in Locosoft nur per SOAP (Phase 2), siehe `Fahrzeuganlage/LOCOSOFT_ANLAGE_SOAP.md`.

---

Wenn du mit dieser Linie einverstanden bist, kann als Nächstes mit Schritt 1 (Doku) und 2 (Server/Bedrock) gestartet werden, danach Migrationen und dann Backend/Frontend in der genannten Reihenfolge.
