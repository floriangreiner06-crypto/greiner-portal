# ecoDMS API — Plan und Test

**Stand:** 2026-03-10  
**Workstream:** Integrationen  
**Ziel:** Belege zur Bankenspiegel-Kategorisierung in ecoDMS suchen (Button „Beleg suchen“). Später ggf. weitere Nutzung (VFW/UPE, Garantieakte).

---

## 1. Handbuch-Kurzfassung (aus CONTEXT.md + VFW_UPE + Test-Skript)

### Was im Projekt bereits steht

| Quelle | Inhalt |
|--------|--------|
| **CONTEXT.md** (ecoDMS-Abschnitt) | Ziel: pro Buchung in Kategorisierung optional Belege in ecoDMS suchen. Geplant: Backend `api/ecodms_api.py`, Ordner/Felder klären, Portal-UI Button, Credentials aus `.env`. |
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

### Offene Klärung (vor produktiver Nutzung)

- **Ordner für Belege zu Bankbuchungen:** Welche Ordner-ID nutzen? (Aktuell nur `1.2` Kontoauszüge bekannt.)
- **Felder für Belege:** Welche Klassifizierungsfelder (Belegdatum, Betrag, Referenz/Verwendungszweck, IBAN?) gibt es in dem gewählten Ordner?
- **Viewer-URL:** Wie öffnet man ein Dokument in ecoDMS per docId? (z. B. `/web/viewer?docId=...` – vor Ort prüfen.)

---

## 2. Plan (Phasen)

### Phase 0: Voraussetzungen (bereits erledigt / manuell)

- [x] Test-Skript vorhanden: `scripts/test_ecodms_api.py`
- [ ] Credentials in `config/.env`: `ECODMS_USER`, `ECODMS_PASSWORD`
- [ ] **Test ausführen** (siehe Abschnitt 3) und grün haben
- [ ] **Optional:** Mit ecoDMS-Verantwortlichen klären: Ordner für „Belege zu Bankbuchungen“, Feld-IDs, Viewer-URL

### Phase 1: Backend-Modul (ohne UI)

- [ ] Modul `api/ecodms_api.py` anlegen/erweitern:
  - Suche nach Belegen: Parameter Buchungsdatum (optional Betrag, Referenz)
  - Aufruf `searchDocumentsExtv2` mit konfigurierbarem Ordner (z. B. Env `ECODMS_FOLDER_BELEGE`)
  - Rückgabe: Liste mit `docId`, `viewUrl` (sobald Viewer-URL bekannt), ggf. `classifyAttributes`
- [ ] Kein produktiver Endpoint, bis Phase 0-Test und ggf. Ordner/Felder geklärt sind

### Phase 2: API-Endpoint für Kategorisierung

- [ ] Endpoint z. B. `GET /api/bankenspiegel/ecodms/belege?datum=...&betrag=...&referenz=...`
- [ ] Ruft `api/ecodms_api.search_belege(...)` auf, gibt JSON `{ success, documents, error }` zurück
- [ ] Nur für eingeloggte Nutzer (`@login_required`), Feature-Zugriff Bankenspiegel

### Phase 3: Portal-UI (Kategorisierung)

- [ ] Button „Beleg suchen“ pro Transaktionszeile (Datum/Betrag/Verwendungszweck aus Zeile übergeben)
- [ ] Aufruf Endpoint → Anzeige Treffer (z. B. Modal): „X Treffer“, Links „In ecoDMS öffnen“ (viewUrl)
- [ ] Falls Viewer-URL noch unbekannt: nur Trefferanzahl und docId anzeigen, Link später nachrüsten

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

- **CONTEXT.md** (dieser Ordner) — Abschnitt „ecoDMS — Belege zur Kategorisierung“
- **docs/VFW_UPE_ANREICHERUNG_ECODMS.md** — API-Grundlagen, Werksrechnungen/UPE
- **scripts/test_ecodms_api.py** — Verbindung, OpenAPI, searchDocumentsExtv2, FIELD_MAP
- Kategorisierung: `routes/bankenspiegel_routes.py`, `api/bankenspiegel_api.py`, `templates/bankenspiegel_kategorisierung.html`
