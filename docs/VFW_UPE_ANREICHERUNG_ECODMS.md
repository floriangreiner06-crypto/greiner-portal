# VFW UPE-Anreicherung aus ecoDMS (Werksrechnungen)

**Datum:** 2026-02-10  
**Kontext:** Bei vielen Vorführwagen fehlt die UPE in Locosoft; Original-Werksrechnungen liegen im ecoDMS-Archiv.  
**Frage:** Können wir die VFW-Liste über die ecoDMS-API mit UPE/Listenpreis aus den Rechnungen anreichern?

---

## 1. Bisheriger ecoDMS-Kontext im Projekt

### Erforschung (TAG 53 / 175 / 176)
- **Skript:** `scripts/test_ecodms_api.py`
- **Zweck:** Verbindungstest, OpenAPI-Abruf, Dokumentensuche (ursprünglich für Kontoauszüge/Folder `1.2`).
- **Entscheidung TAG 175/176:** Rechnungen später aus eigenem Archiv (ecoDMS) über API holen – z. B. für Garantieakte; `api/ecodms_api.py` war geplant, aber **noch nicht umgesetzt**.

### API-Grundlagen (aus Test-Skript)
| Item | Wert |
|------|------|
| **Base URL** | `http://10.80.80.3:8180` |
| **Auth (temporär)** | User `api-greiner-drive`, PW in `config/.env` (ECODMS_USER/ECODMS_PASSWORD). Nach erfolgreichem Test auf Server mit nano neues PW setzen. |
| **Verbindungstest** | `GET /api/test` |
| **OpenAPI** | `GET /v3/api-docs` |
| **Dokumentensuche** | `POST /api/searchDocumentsExtv2` |

### Such-Request (Beispiel aus Test)
```json
{
  "searchFilter": [{
    "classifyAttribute": "folderonly",
    "searchValue": "1.2",
    "searchOperator": "="
  }],
  "maxDocumentCount": 10
}
```
- **Ergebnis:** Liste von Dokumenten mit `docId`, `clDocId`, `archiveName`, **`classifyAttributes`** (benutzerdefinierte Felder, z. B. `dyn_4_1763372371642` = Bank, IBAN, Datum, Endsaldo usw.).
- Die **Klassifizierungsfelder** sind pro ecoDMS-Archiv/Folder konfigurierbar – für Werksrechnungen müssten die tatsächlichen Feld-IDs (z. B. Listenpreis, FIN, Rechnungsnummer) bekannt sein.

---

## 2. Anwendungsfall: UPE für VFW

- **Quelle:** Werksrechnungen (Original) in ecoDMS.
- **Ziel:** Fehlende UPE in der VFW-Liste (CSV/Excel) ergänzen.
- **Matching:** VFW aus Locosoft identifizierbar über z. B. **FIN** (`vehicles.vin`), **dealer_vehicle_number**, Kennzeichen, Modell + EZ. In ecoDMS müsste ein Dokument pro Fahrzeug/Rechnung auffindbar sein (z. B. über FIN oder Rechnungsnummer in den Metadaten).

---

## 3. Einschätzung: Ist Anreicherung über ecoDMS machbar?

### Ja, unter folgenden Bedingungen

1. **Ordner/Archiv für Werksrechnungen**
   - In ecoDMS existiert ein (oder mehrere) Ordner/Archiv, in dem Werksrechnungen abgelegt sind.
   - Die Ordner-ID(s) oder Suchkriterien (z. B. Dokumenttyp „Werksrechnung“) sind bekannt oder können ermittelt werden.

2. **UPE/Listenpreis in Metadaten**
   - **Idealfall:** Listenpreis/UPE ist als **Klassifizierungsattribut** (classifyAttribute) erfasst → dann reicht die API-Suche, keine PDF-Verarbeitung nötig.
   - **Alternativ:** UPE steht nur im PDF-Text → dann müsste pro Dokument das PDF per API geladen und per Textextraktion (z. B. pdfplumber) ausgewertet werden (aufwendiger, fehleranfälliger).

3. **Zuordnung Dokument ↔ Fahrzeug**
   - In den Metadaten der Werksrechnung muss ein **Merkmal** vorkommen, das wir der VFW-Liste zuordnen können, z. B.:
     - **FIN** (Fahrzeug-Identifizierungsnummer), oder
     - **Rechnungsnummer** (wenn in Locosoft gespeichert), oder
     - **Kennzeichen** / Bestellnummer (falls eindeutig).
   - Ohne solches Merkmal ist ein automatisches Matching unsicher.

4. **Zugriff und Stabilität**
   - Der Server, auf dem das VFW-Skript/Anreicherung läuft, kann ecoDMS unter `10.80.80.3:8180` erreichen (Netzwerk/Firewall).
   - ecoDMS-API ist verfügbar und stabil (wie im bestehenden Test).

### Risiken / offene Punkte

- **Metadaten:** Oft sind in DMS nur Stichworte (z. B. „Opel“, „Astra“) erfasst, nicht der Listenpreis. Dann bliebe nur PDF-Parsing.
- **Mehrere Belege pro Fahrzeug:** Mehrere Rechnungen (Anhänger, Sonderausstattung) → Logik nötig, welcher Wert als UPE gilt (z. B. Hauptrechnung, Maximalwert).
- **Struktur:** Wenn Werksrechnungen nicht in einem eigenen Ordner liegen, wird die Suche (z. B. nur nach FIN) evtl. auf viele andere Dokumente ausgeweitet; Performance und Trefferqualität müssen geprüft werden.

---

## 4. Empfohlene nächste Schritte

1. **ecoDMS vor Ort klären**
   - In welchem Ordner/Archiv liegen die **Werksrechnungen** (Neuwagen/Vorführwagen)?
   - Welche **Klassifizierungsfelder** gibt es dort (Feldname + interne ID, z. B. `dyn_*`)? Ist **Listenpreis/UPE** oder **Bruttopreis** dabei?
   - Wird **FIN** (oder Rechnungsnummer/Kennzeichen) erfasst?

2. **OpenAPI/Swagger von ecoDMS auslesen**
   - `GET http://10.80.80.3:8180/v3/api-docs` (wie im Test) aufrufen.
   - Alle Endpoints für **Suche** und **Dokument-Download** notieren (z. B. Download-PDF für spätere Textextraktion).

3. **Kleiner Suchtest**
   - Mit `searchDocumentsExtv2` im Werksrechnungen-Ordner suchen (z. B. `folderonly` = entsprechende ID).
   - Einige Treffer prüfen: Welche `classifyAttributes` sind gesetzt? Enthalten sie Preis, FIN, Rechnungsnummer?

4. **Wenn Metadaten reichen**
   - Modul `api/ecodms_api.py` (oder Skript) für Suche nach FIN/Rechnungsnummer und Abruf Listenpreis.
   - VFW-Pipeline erweitern: Nach Export aus Locosoft für jede Zeile ohne UPE ecoDMS abfragen und UPE-Spalte befüllen (ggf. mit Nachlauf für manuelle Prüfung).

5. **Wenn nur PDF geht**
   - Download-Endpoint in ecoDMS nutzen, PDF mit pdfplumber öffnen, Text nach Preis/Listenpreis/UPE durchsuchen (regex/Heuristik), Wert extrahieren und in VFW-Liste eintragen.

---

## 5. Kurzfassung

| Frage | Antwort |
|-------|--------|
| **Ist die ecoDMS-API im Projekt schon angebunden?** | Teilweise: Verbindung und `searchDocumentsExtv2` im Test-Skript erprobt, kein produktiver API-Client. |
| **Können wir so die UPE-Daten anreichern?** | **Ja, wenn** Werksrechnungen-Ordner bekannt ist, UPE (oder Preis) in Metadaten oder per PDF-Parsing verfügbar ist und ein Matching (z. B. FIN) möglich ist. |
| **Nächster konkreter Schritt** | In ecoDMS die Ordner- und Feldstruktur für Werksrechnungen klären; danach einen gezielten Such-/Abruftest (evtl. mit 1–2 FIN aus der VFW-Liste) durchführen. |

---

**Referenzen im Projekt**
- `scripts/test_ecodms_api.py` – ecoDMS-Verbindung und Dokumentensuche
- `docs/sessions/SESSION_WRAP_UP_TAG175.md`, `TODO_FOR_CLAUDE_SESSION_START_TAG176.md` – ecodms API als geplante Alternative für Rechnungen
