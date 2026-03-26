# ecoDMS API — Plan und Test

**Stand:** 2026-03-10  
**Workstream:** Controlling (Bankenspiegel / Belege zur Kategorisierung)  
**Ziel:** Belege zur Bankenspiegel-Kategorisierung in ecoDMS suchen (Button „Beleg suchen“). Später ggf. weitere Nutzung (VFW/UPE, Garantieakte).

---

## 1. Handbuch-Kurzfassung (aus CONTEXT.md + VFW_UPE + Test-Skript)

### Was im Projekt bereits steht

| Quelle | Inhalt |
|--------|--------|
| **CONTEXT.md** (Controlling, ecoDMS) | Ziel: pro Buchung in Kategorisierung optional Belege in ecoDMS suchen. Backend `api/ecodms_api.py`, Ordner/Felder, Portal-UI Button „Beleg suchen“, Credentials aus `.env`. |
| **VFW_UPE_ANREICHERUNG_ECODMS.md** | API-Basics, Such-Request-Beispiel, Feld-Mapping pro Archiv, Anwendungsfall Werksrechnungen/UPE. |
| **scripts/test_ecodms_api.py** | Verbindung (`GET /api/test`), OpenAPI (`GET /v3/api-docs`), Dokumentensuche `POST /api/searchDocumentsExtv2` mit Basic Auth. Ordner `1.2` (Kontoauszüge), FIELD_MAP für Bank/IBAN/BIC/Datum/Belegdatum/Endsaldo. |

### API-Fakten (SSOT für Implementierung)

| Item | Wert |
|------|------|
| **Base URL** | `http://10.80.80.3:8180` |
| **Auth** | Basic Auth; User/Passwort aus `config/.env`: `ECODMS_USER`, `ECODMS_PASSWORD` (nicht versioniert). |
| **Verbindungstest** | `GET /api/test` (ohne Auth) |
| **OpenAPI** | `GET /v3/api-docs` (mit Auth; kann 404 liefern) |
| **Dokumentensuche** | `POST /api/searchDocumentsExtv2` (mit Auth), Body: `searchFilter` (Array), `maxDocumentCount` |
| **Suchfilter-Beispiel** | `classifyAttribute: "folderonly"`, `searchValue: "1.2"`, `searchOperator: "="` |
| **Antwort Suche** | JSON-Array mit Objekten: `docId`, `clDocId`, `archiveName`, `classifyAttributes` (Feld-IDs je Archiv) |
| **Bekannte Feld-IDs (Ordner 1.2)** | Siehe `FIELD_MAP` in `scripts/test_ecodms_api.py` (z. B. `belegdatum`: `dyn_0_1517843102084`) |

### Beleg-Download / Anzeige (aus Swagger-Doku und get-dms-doc)

- **ecoDMS Swagger UI** auf der Instanz lieferte 404; Quelle: [get-dms-doc](https://codeberg.org/tomas-jakobs/get-dms-doc) (FreeBASIC-Quellcode) und ecoDMS-API-Doku.
- **Download-URL:** `GET {BASE_URL}/api/document/{docId}` mit **Basic Auth** → Antwort ist die Datei (z. B. `Content-Type: application/pdf`).
- **Im Portal:** Proxy unter Transaktionen-API: `GET /api/bankenspiegel/transaktionen/ecodms/document/<docId>/download`. Die Suche liefert pro Treffer `viewUrl` = dieser Pfad (Transaktions-URLs sind zusammengefasst).

### Filter: Auf welche Attribute können wir filtern? (vernünftige Treffer)

Die Suche nutzt **`POST /api/searchDocumentsExtv2`** mit Body:

- **`searchFilter`:** Array von Objekten `{ "classifyAttribute": "<id>", "searchValue": "<wert>", "searchOperator": "<op>" }`
- **`maxDocumentCount`:** Max. Anzahl Treffer (im Portal z. B. 20, API akzeptiert bis 50).

**Filterbare Attribute (classifyAttribute):**

| Attribut | Wert im Request | Verwendung / Hinweis |
|----------|------------------|----------------------|
| **folderonly** | Ordner-ID (z. B. `"1.2"`) | Immer gesetzt; begrenzt auf Belege-Ordner. |
| **Belegdatum** | `dyn_0_1517843102084` | Exaktes Datum (YYYY-MM-DD); wird bereits genutzt. |
| **Kreditor** | `dyn_0_1517927104726` | Wenn in ecoDMS gepflegt: exakter Kreditor-Name → weniger Treffer, bessere Relevanz. |
| **Bemerkung** | z. B. über `ECODMS_FIELD_BEMERKUNG` | Belegnummer/Referenz (z. B. Rechnung_DE…); für Teil-/Volltext je nach Operator. |
| Weitere dyn_* | Alle im Archiv definierten Feld-IDs | Bank, IBAN, BIC, Datum, Endsaldo etc. – IDs je Archiv in ecoDMS unter Klassifizierung sichtbar. |

**Was die API hergibt (Response):**

- Pro Treffer: **`docId`**, **`clDocId`**, **`archiveName`**, **`classifyAttributes`** (Map: Feld-ID → Wert, z. B. `dyn_0_1517927104726` → „Hauptzollamt Regensburg“).
- Kein Volltext-Suchparameter in diesem Endpoint; Referenz/Kreditor nur über Klassifizierungsfelder filterbar (oder nachträglich im Portal gegen `classifyAttributes` matchen).

**Operatoren:** Im Projekt wird nur **`searchOperator: "="** (exakter Vergleich) verwendet. Ob ecoDMS z. B. `CONTAINS`/`LIKE` für Teilstring-Suche unterstützt, steht in der Swagger-Doku der Instanz (`GET /v3/api-docs`).

**Praktische Empfehlung für bessere Treffer:**

1. **Belegdatum** beibehalten (bereits umgesetzt).
2. **Kreditor-Filter (umgesetzt):** Wenn aus dem Transaktionstext ein Kreditor erkannt wird (`kreditor_vermutet`), sendet `search_belege` automatisch einen zusätzlichen Filter mit Feld-ID Kreditor (Default `dyn_0_1517927104726`, überschreibbar per Env `ECODMS_FIELD_KREDITOR`). Die API liefert dann nur Belege mit diesem Kreditor (sofern in ecoDMS gesetzt) – Zuordnung wird einfacher.
3. **Rechnungsnummer/Belegnummer-Filter (umgesetzt):** Die Belegnummer (z. B. DE2600038886) ist in ecoDMS als Klassifizierungsattribut „Rechnungsnummer“ vorhanden. Wenn in `config/.env` **`ECODMS_FIELD_RECHNUNGSNUMMER`** auf die entsprechende dyn_*-Feld-ID gesetzt ist, wird aus dem Verwendungszweck eine Nummer extrahiert (DE… oder längere Ziffernfolge) und als zusätzlicher API-Filter gesendet – dann liefert die Suche nur Belege mit dieser Rechnungsnummer. Die dyn_*-ID ist in ecoDMS unter Klassifizierung/Spalte „Rechnungsnummer“ zu finden.

### Swagger/OpenAPI ordentlich einbinden

- **Spec-URL:** In `config/.env` kann **`ECODMS_OPENAPI_SPEC_URL`** gesetzt werden (vollständige URL oder Pfad relativ zu BASE_URL). Dann wird nur diese Spec geladen – kein 404-Raten mehr, wenn Swagger bei euch unter anderem Pfad liegt.
- **Discovery:** Ohne gesetzte URL versucht das Portal mehrere Standard-Pfade (`/v3/api-docs`, `/v2/api-docs`, `/swagger-resources`, …). Details: **`docs/workstreams/controlling/ecodms/ECODMS_SWAGGER_EINBINDUNG.md`**.
- **Diagnose:** `GET /api/bankenspiegel/transaktionen/ecodms/openapi-status` (eingeloggt) zeigt, ob eine Spec geladen wurde und welche Pfade darin vorkommen.

### Ordner-ID per API auslesen

- **`get_folders()`** in `api/ecodms_api.py` liest die Ordnerstruktur von ecoDMS (GET `/api/folders`, `/api/archive/folders` oder OpenAPI-Spec). Rückgabe: `{ "success", "folders": [ {"id", "name"}, ... ] }`.
- **`resolve_folder_id(config)`:** Wenn `ECODMS_FOLDER_BELEGE` eine **ID** ist (z. B. `1.2`, `5`), wird sie unverändert genutzt. Ist es ein **Name** (z. B. `Buchhaltung`), wird die Ordnerliste per API geholt und die ID zum passenden Namen ermittelt. So kann in `.env` z. B. `ECODMS_FOLDER_BELEGE=Buchhaltung` stehen.
- **Endpoint:** `GET /api/bankenspiegel/transaktionen/ecodms/folders` (eingeloggt) liefert die Ordnerliste und die aktuell aufgelöste Ordner-ID (für Diagnose/Konfiguration).

### Offene Klärung (optional)

- **Felder für Belege:** Welche Klassifizierungsfelder gibt es im gewählten Ordner?
- **Suchoperatoren:** In Swagger (`/v3/api-docs`) prüfen, ob z. B. CONTAINS/LIKE für Teilstring-Filter verfügbar sind.

---

## 2. Plan (Phasen)

### Phase 0: Voraussetzungen (bereits erledigt / manuell)

- [x] Test-Skript vorhanden: `scripts/test_ecodms_api.py`
- [x] Credentials in `config/.env`: `ECODMS_USER`, `ECODMS_PASSWORD`
- [x] **Test ausführen** (siehe Abschnitt 3) und grün haben (2026-03-10)
- [ ] **Optional:** Mit ecoDMS-Verantwortlichen klären: Ordner für „Belege zu Bankbuchungen“, Feld-IDs, Viewer-URL

### Phase 1: Backend-Modul (ohne UI)

- [x] Modul `api/ecodms_api.py` anlegen/erweitern:
  - Suche nach Belegen: Parameter Buchungsdatum (optional Betrag, Referenz)
  - Aufruf `searchDocumentsExtv2` mit konfigurierbarem Ordner (z. B. Env `ECODMS_FOLDER_BELEGE`)
  - Rückgabe: Liste mit `docId`, `viewUrl` (sobald Viewer-URL bekannt), ggf. `classifyAttributes`
- [x] Credentials und Test erfolgreich

### Phase 2: API-Endpoint für Kategorisierung

- [x] Endpoint `GET /api/bankenspiegel/transaktionen/ecodms/belege?datum=...&betrag=...&referenz=...`
- [x] Ruft `api.ecodms_api.search_belege(...)` auf, gibt JSON `{ success, documents, error }` zurück
- [x] Nur für eingeloggte Nutzer (`@login_required`)

### Phase 3: Portal-UI (Kategorisierung) — umgesetzt

- [x] Button „Beleg suchen“ pro Transaktionszeile (Datum/Betrag/Verwendungszweck aus Zeile übergeben)
- [x] Aufruf Endpoint → Anzeige Treffer (Modal), Links „Beleg anzeigen“ (viewUrl/Download)
- [x] Filter: Belegdatum, optional Kreditor, optional Rechnungsnummer; Fallback bei 0 Treffern; Ordner per API (`/api/folders`) auflösbar

### Phase 4: Weitere ecoDMS-Nutzung (später)

- VFW/UPE-Anreicherung (Werksrechnungen): siehe `docs/VFW_UPE_ANREICHERUNG_ECODMS.md`
- Garantieakte/Rechnungen: erwähnt in SESSION_WRAP_UP TAG 175/176

---

## 3. Test (ecoDMS API)

### 3.1 Manueller Ablauf („Handbuch-Test“)

1. **Credentials prüfen**  
   In `config/.env` (nicht versioniert) müssen stehen:
   - `ECODMS_USER=...` (z. B. `api-greiner-drive`)
   - `ECODMS_PASSWORD=...`

2. **Test-Skript ausführen** (auf dem Server bzw. Rechner mit Zugriff auf 10.80.80.3:8180):
   ```bash
   cd /opt/greiner-portal
   python3 scripts/test_ecodms_api.py
   ```
   Alternativ mit expliziten Zugangsdaten:
   ```bash
   python3 scripts/test_ecodms_api.py --user api-greiner-drive --password <PW>
   ```

3. **Erwartung:**
   - **Test 1 (Connection):** Status 200, kurze Response von ecoDMS
   - **Test 2 (OpenAPI):** Kann 404 sein (laut Session-Wrap-up) – nicht kritisch
   - **Test 3 (Document Search):** Status 200, Liste von Dokumenten (mind. 0), Ausgabe mit docId/IBAN/Datum/Endsaldo

4. **Bei 401 (Unauthorized):** Zugangsdaten in ecoDMS prüfen, Passwort ggf. mit nano in `config/.env` anpassen.

5. **Bei Verbindungsfehler:** Netzwerk/Firewall (Port 8180), ecoDMS-Service, IP-Whitelist prüfen.

### 3.2 Kurz-Checkliste vor Implementierung

| Schritt | Aktion | Ergebnis |
|--------|--------|----------|
| 1 | `config/.env` hat ECODMS_USER und ECODMS_PASSWORD | ☐ |
| 2 | `python3 scripts/test_ecodms_api.py` läuft durch | ☐ |
| 3 | Document Search liefert 200 und JSON-Array | ☐ |
| 4 | (Optional) Ordner/Felder für „Belege“ mit ecoDMS geklärt | ☐ |
| 5 | (Optional) Viewer-URL für docId notiert | ☐ |

### 3.3 Später: automatisierbarer Test

- Optional: pytest/Unittest für `api/ecodms_api.py` (z. B. `check_connection()`, `search_belege()` mit Mock oder nur bei gesetzten Env-Variablen).
- Test-Skript bleibt Referenz für manuelle Prüfung und für neue Umgebungen.

---

## 4. Referenzen

- **CONTEXT.md** (Workstream Controlling) — Abschnitt „ecoDMS (Bankenspiegel Belegsuche)“
- **docs/VFW_UPE_ANREICHERUNG_ECODMS.md** — API-Grundlagen, Werksrechnungen/UPE
- **scripts/test_ecodms_api.py** — Verbindung, OpenAPI, searchDocumentsExtv2, FIELD_MAP
- Kategorisierung: `routes/bankenspiegel_routes.py`, `api/bankenspiegel_api.py`, `templates/bankenspiegel_*.html`, `static/js/bankenspiegel_transaktionen_combined.js`
