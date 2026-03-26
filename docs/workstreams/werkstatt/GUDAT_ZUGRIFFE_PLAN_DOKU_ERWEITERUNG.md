# Plan: Gudat-Zugriffe mit offizieller Doku verbessern und erweitern

**Stand:** 2026-03-10  
**Workstream:** werkstatt  
**Referenz Doku:** [DA API V1 Reference](https://werkstattplanung.net/greiner/deggendorf/kic/da/docs/index.html)  
**Kein Code in diesem Dokument – nur Planung.**

---

## 1. Ausgangslage

### Was wir heute nutzen

| Zugriff | Basis | Auth | Verwendung |
|--------|--------|------|------------|
| **KIC (Instanz-URL)** | `https://werkstattplanung.net/greiner/deggendorf/kic` | Session (GET kic → POST /login → GET /ack → laravel_token) | Login, alle unsere Gudat-Calls |
| **REST (auf KIC)** | gleiche URL + `/api/v1/...` | Session-Cookies | `workload_week_summary`, `user` |
| **GraphQL (auf KIC)** | gleiche URL + `/graphql` | Session-Cookies | workshopTasks, dossier (note, orders.note, states, comments, documents), appointments |

**Dateien:** `tools/gudat_client.py`, `api/gudat_data.py`, `api/gudat_api.py`, `api/arbeitskarte_api.py`, `api/werkstatt_live_api.py`.

### Was die offizielle Doku beschreibt

- **DA REST API (separat):** Basis `https://api.werkstattplanung.net/da/v1`, Auth **OAuth2** (Password Grant), Header `group` + `center`. Endpoints: customers, vehicles, **documents** (Upload/Attach an Dossier, Get Content), **orders** (Get/Patch/Post), online booking (Service Events, Workshop Tasks, Statables, Slots, …), archive documents, status trigger.
- **KIC/Instanz:** In der Doku erwähnt für Zugriff im Browser (`.../group/center/kic`) und für **Deeplinks** (z. B. neues Dossier, Dossier mit Kundennummer öffnen). Die Doku erklärt **nicht** explizit unser GraphQL bzw. `/api/v1/workload_week_summary` auf der Instanz-URL – das sind vermutlich instanzlokale APIs.

**Wichtig:** Wir nutzen aktuell **nur** die Instanz-URL (KIC + Session). Die „echte“ DA REST API (api.werkstattplanung.net, OAuth2) nutzen wir **nicht**. Verbesserungen und Erweiterungen müssen diese zwei Wege trennen.

---

## 2. Ziele (ohne Code)

- **Bestehende Zugriffe** an der Doku spiegeln: klären, was davon in der Doku vorkommt, was nicht; Lücken und Risiken benennen.
- **Stabilität und Wartbarkeit** erhöhen: Auth- und Fehlerverhalten an Empfehlungen der Doku anlehnen (z. B. 401 → Refresh/Re-Login).
- **Optional erweitern:** Wo es Mehrwert bringt, Nutzung der **offiziellen DA REST API** (OAuth2) prüfen – z. B. Dokument-Upload, Orders lesen/schreiben, Service Events – und dafür einen klaren Entscheidungs- und Umsetzungsplan haben.

---

## 3. Verbesserungen (an Doku anlehnen)

### 3.1 Dokumentation unserer aktuellen Schnittstelle

- **Tabelle anlegen:** „Was wir aufrufen“ ↔ „Wo (falls überhaupt) in der Doku beschrieben“.
  - Beispiele: `POST .../graphql` (workshopTasks, dossier) – in der Doku eher indirekt (Beispiele, Service Events); `GET .../api/v1/workload_week_summary` – vermutlich **nicht** in der DA-V1-Referenz (instanzspezifisch?). Klarstellen und in unserer Doku (z. B. `GUDAT_API_INTEGRATION.md` oder Werkstatt-CONTEXT) festhalten.
- **Changelog nutzen:** Doku enthält API Changelog (1.0–1.9). Bei neuen Features oder Fehlern: prüfen, ob Änderungen in 1.6–1.9 unsere Aufrufe (z. B. GraphQL-Felder, REST-Pfade) betreffen; Erkenntnisse kurz in einer „Gudat-API-Versionen“-Notiz festhalten.

### 3.2 Auth und Fehlerbehandlung

- **Doku-Empfehlung (Token):** Bei 401 zuerst Refresh versuchen, bei erneutem 401 neuer Login. Wir haben **keinen** OAuth-Token, sondern Session (laravel_token, XSRF).
- **Plan:** Unser Verhalten an gleiche **Logik** anpassen (ohne sofort OAuth einzubauen): z. B. bei 401/403 auf Gudat-Calls **einmal** Re-Login (Session neu aufbauen) und Request wiederholen; nur bei erneutem Fehler Fehler zurückgeben. Wo das heute fehlt, gezielt einplanen (welche Aufrufer, welche Schicht).
- **Optional:** In Doku oder Kontakt mit Gudat klären: Ist `workload_week_summary` / unser GraphQL langfristig stabil oder perspektivisch durch api.werkstattplanung.net/da/v1 ersetzt? Das beeinflusst, ob wir mittelfristig auf OAuth umstellen wollen.

### 3.3 Einheitliche Gudat-Schicht

- **Zustand:** Mehrere Stellen rufen Gudat direkt auf (arbeitskarte_api, werkstatt_live_api, gudat_data, gudat_client), teils mit duplizierter Config/Login-Logik.
- **Plan:** Konzept für **eine** zentrale Gudat-Zugriffsschicht (z. B. „Gudat-KIC-Client“: Session, GraphQL, REST workload) definieren. Alle Aufrufe laufen darüber; Auth/Re-Login/Fehlerbehandlung nur dort. Kein Code, nur: welche Module sollen nur noch über diese Schicht gehen, welche Endpoints/Funktionen sie anbieten soll. Später: Refactoring-Schritte ableiten.

### 3.4 Deeplinks (laut Doku)

- **Doku:** Deeplinks für „neues Dossier“, „Dossier mit Kundennummer“, „Dossier mit caseData“ etc. über `.../kic/da/index.html#/views/?...`.
- **Plan:** Wenn wir in DRIVE Links „In Gudat öffnen“ anbieten wollen (z. B. von Auftrag oder Arbeitskarte): Deeplink-URL-Schema aus der Doku übernehmen und in unserer Doku (eine Seite „Gudat-Deeplinks“) festhalten – Parameter, Beispiele, Einschränkungen. Kein Code, nur Spezifikation für spätere Implementierung.

---

## 4. Können wir die DA REST API nutzen?

**Kurz: Ja – technisch ist die Nutzung möglich, aber nur mit Zugang von Gudat.**

Laut offizieller Doku gilt:

- **OAuth2-Pflicht:** Die REST API unter `https://api.werkstattplanung.net/da/v1` erfordert OAuth2 (Password Grant). Pro Request müssen die Header `group` und `center` die Zielinstanz bezeichnen (z. B. Greiner Deggendorf).
- **Client-Credentials:** Client ID, Client Name und Client Secret werden **von Gudat Solutions an „registered developers“ vergeben**. Ohne diese Credentials ist die REST API nicht nutzbar.
- **Instanz-User:** Zusätzlich braucht ihr weiterhin einen Benutzer (E-Mail + Passwort) in der Zielinstanz – z. B. den gleichen System-Account wie heute für die KIC-Session.
- **Freischaltung in der Instanz:** „An individual authorization in each instance by the end customers administrator is still mandatory.“ Der Kunde (Greiner) muss die Nutzung der API in seiner DA-Instanz ggf. freigeben.

**Aktueller Stand im Projekt:** Es gibt **keine** OAuth-Client-Credentials für Gudat (kein `client_id`/`client_secret` für api.werkstattplanung.net in `config/credentials.json`). Es sind nur die KIC-Login-Daten (username/password) hinterlegt.

**Nächster Schritt, um die REST API zu nutzen:**  
Bei Gudat anfragen (z. B. [developer@digitalesautohaus.de](mailto:developer@digitalesautohaus.de)): Registrierung als Developer und Ausstellung der OAuth-Client-Credentials (Client ID, Name, Secret) für die Nutzung der DA REST API; optional Klärung, ob die Greiner-Instanz (group/center) bereits für API-Zugriff freigegeben ist oder ob der Kunden-Admin etwas freischalten muss.

---

## 4a. In der Greiner-Verwaltung gefundene Konfiguration (UI)

In der AGD-Verwaltung (werkstattplanung.net) sind zwei relevante Bereiche sichtbar:

### Schnittstellen verwalten (Interfaces)

- **Digitales Autohaus** ist als Schnittstelle mit **ID `da`** angelegt.
- **Aktivierte Funktionen** (laut UI):
  - Auftrag erstellen  
  - Stammdaten lesen  
  - Stammdaten schreiben  
  - Ersatzfahrzeug  
  - Fahrzeug Informationen  
  - Kunden Informationen  

Das entspricht der **instanzseitigen Freigabe**: Für die Schnittstelle „DA“ sind genau diese Aktionen erlaubt. Beim Einsatz der REST API (oder von Connectors) sollten nur diese Bereiche genutzt werden; sie können der Doku (customers, vehicles, orders, …) zugeordnet werden.

### Connectoren verwalten (Connectors)

- **URL:** `https://werkstattplanung.net/greiner/deggendorf/lic/da/#/imports/connectors` (Bereich **lic** = Verwaltung).
- Connector mit Beschreibung **`da_gudat`** (Name in der Liste z. B. `da_greiner_1191`):
  - Installiert ✓  
  - Systemstatus ✓  
  - Aktiver Connector ✓  
  - **Token:** Spalte mit Bearbeiten-Icon (Stift) – es gibt also eine **Token-Verwaltung** für diesen Connector.

**Bedeutung für uns:**  
- Die **Schnittstellen-Freigabe** (Auftrag, Stammdaten, Fahrzeug, Kunde) ist bereits gesetzt – die „individual authorization in each instance“ aus der Doku ist für diese Funktionen offenbar umgesetzt.  
- Der **Token** beim Connector `da_gudat` könnte ein API-/OAuth-Token für die Kommunikation mit DA sein (z. B. für den Gudat-Connector Locosoft↔DA). Ob dieser Token für die **öffentlich dokumentierte REST API** (api.werkstattplanung.net/da/v1) nutzbar ist oder nur für den Connector-Backend, müsste in der Doku oder bei Gudat geklärt werden. Wenn ihr den Token kopieren/anzeigen könnt, lohnt sich der Abgleich mit der Doku (Bearer Token, OAuth, etc.).

---

## 5. Mögliche Erweiterungen (DA REST API)

Diese Schritte setzen voraus, dass ihr die **DA REST API** (api.werkstattplanung.net/da/v1) nutzt – also OAuth2 und Client-Credentials von Gudat (siehe Abschnitt 4).

### 5.1 OAuth2-Anbindung (Voraussetzung)

- **Laut Doku:** OAuth2 Password Grant, Client ID/Name/Secret von Gudat, User = E-Mail + Passwort der Instanz; Access Token 1 Jahr, Refresh Token +30 Tage; bei 401 zuerst Refresh, dann ggf. neuer Login.
- **Plan:** Entscheidung dokumentieren: Bleiben wir nur bei KIC/Session oder wollen wir die REST API nutzen? Wenn ja: Anforderung an Gudat (Client-Credentials, ggf. Demo-Instanz group/center für Tests) klären; Konzept für Token-Speicherung (z. B. credentials.json oder DB, nur für Backend) und Refresh-Logik skizzieren. Kein Code.

### 5.2 Dokument an Dossier hängen

- **Doku:** „documents – post: Upload and attach a document to a dossier“.
- **Nutzen:** z. B. DSE-PDF oder anderes PDF aus DRIVE in Gudat am Dossier sichtbar machen (siehe DSE-Machbarkeit).
- **Plan:** In Doku festhalten: Endpoint und Parameter aus der Doku (inkl. dossier_id, Datei, ggf. Metadaten); Abgleich mit unserer Dossier-ID (GraphQL). Entscheidung: Nur lesen (weiter nur Download) oder auch schreiben (Upload)? Wenn Upload gewünscht: Priorität und Abhängigkeit (OAuth2 zuerst) festlegen.

### 5.3 Orders (Lesen/Patchen)

- **Doku:** orders – get (Liste, Filter), get nach order_number, patch (Update), post (Create).
- **Nutzen:** Auftragsdaten aus DA konsistent lesen; ggf. Anmerkung/Status aus DRIVE nach Gudat zurückschreiben (falls gewünscht).
- **Plan:** Use-Cases aufschreiben (z. B. „Auftragsliste für Datum“, „Einzelauftrag aktualisieren“). Prüfen, ob das unsere bestehenden GraphQL-Dossier/Orders-Abfragen ergänzt oder ersetzt. Wenn Ergänzung: welche Felder aus REST nutzen; Priorität (niedrig/mittel/hoch) festlegen.

### 5.4 Service Events / Termine (online booking)

- **Doku:** Service Events (get list, get one, create, update, cancel), free Slots, states, workshop tasks, resources, event types, booking configuration.
- **Nutzen:** Termine und Kapazitäten evtl. über standardisierte REST-API statt nur GraphQL; Anbindung an Buchungsportale oder DRIVE-Terminübersichten.
- **Plan:** Nur als Option notieren: Wenn wir Termine künftig stärker aus DA heraus steuern oder auswerten wollen, Service-Events-API aus der Doku als Kandidat führen; Abgrenzung zu unserem heutigen GraphQL-Appointments-/workshopTasks-Zugriff kurz beschreiben. Keine Umsetzung ohne konkreten Use-Case.

### 5.5 Customers / Vehicles (REST)

- **Doku:** customers und vehicles (CRUD).
- **Nutzen:** Nur relevant, wenn DRIVE Stammdaten in DA anlegen oder ändern soll (z. B. bei Fahrzeuganlage „auch in Gudat anlegen“).
- **Plan:** Aktuell zurückstellen; nur in einer Zeile festhalten: „Falls künftig Stammdaten-Sync DRIVE → DA gewünscht, REST customers/vehicles nutzbar.“ Keine Priorität ohne Anforderung.

---

## 6. Priorisierung (Vorschlag)

| Priorität | Inhalt | Abhängigkeit |
|-----------|--------|--------------|
| **P1** | Doku-Tabelle „Unsere Aufrufe ↔ Doku“; Auth/401-Re-Login-Konzept; zentrale Gudat-Schicht (Konzept) | – |
| **P2** | Changelog-Auge behalten; Deeplink-Spezifikation für „In Gudat öffnen“ | – |
| **P3** | Entscheid: OAuth2/REST API ja/nein; wenn ja: OAuth2-Konzept, dann documents-Upload (Spez) | Gudat Client-Credentials |
| **P4** | Orders REST (Use-Cases, Priorität); Service Events nur als Option notiert | OAuth2 |
| **P5** | Customers/Vehicles nur Vermerk | – |

---

## 7. Nächste Schritte (empfohlen)

1. **Kurz:** In `docs/workstreams/werkstatt/` oder `docs/` eine feste „Gudat-API-Übersicht“ anlegen (eine Seite): unsere Endpoints (KIC + GraphQL + workload), Abgleich mit DA-Doku, Hinweis auf zwei Wege (KIC vs. api.werkstattplanung.net).
2. **Backlog:** Die Punkte aus Abschnitt 3 (Verbesserungen) und 4 (Erweiterungen) als klare Aufgaben/Tickets formulieren (ohne Code), mit Priorität und Abhängigkeiten.
3. **Kontakt:** Bei Gudat (developer@digitalesautohaus.de) ggf. anfragen: Stellen workload_week_summary und GraphQL unter .../kic Teil der langfristig unterstützten API dar, oder sollen wir auf api.werkstattplanung.net/da/v1 (OAuth2) migrieren? Antwort in der Übersicht dokumentieren.

---

**Referenzen:**  
`docs/GUDAT_API_INTEGRATION.md`, `docs/workstreams/werkstatt/CONTEXT.md`, `GUDAT_VERSION_VERGLEICH_DA_6_41_6_42.md`, `DSE_EINWILLIGUNG_LOCOSOFT_GUDAT_MACHBARKEIT.md`, [DA API V1 Reference](https://werkstattplanung.net/greiner/deggendorf/kic/da/docs/index.html).
