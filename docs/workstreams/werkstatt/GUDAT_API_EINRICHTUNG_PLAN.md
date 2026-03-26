# Gudat API – Einrichtungsplan und Funktionsumfang

**Workstream:** werkstatt  
**Stand:** 2026-03-12  
**Kein Code in diesem Dokument – nur Planung.**

---

## 1. Ausgangslage: Mail vom Gudat-Support

Zitat Support:

> Sehr geehrter Herr Greiner,
>
> vielen Dank für die Beauftragung. Im Anhang erhalten Sie die verschlüsselte Datei mit den API-Zugangsdaten. Das Passwort hierfür erhalten Sie in einer separaten E-Mail. **In ihrem Center müssen Sie noch einen Benutzer für die API-Nutzung erstellen.**
>
> Bei Rückfragen stehen wir Ihnen gerne zur Verfügung!

**Folgerungen:**

| Schritt | Beschreibung |
|--------|--------------|
| 1 | **Verschlüsselte Datei** aus dem E-Mail-Anhang mit dem Passwort aus der **separaten E-Mail** entschlüsseln → Inhalt sind die API-Zugangsdaten. |
| 2 | **Im Center** (Gudat/DA-Verwaltung, z. B. werkstattplanung.net → greiner/deggendorf) einen **Benutzer für die API-Nutzung anlegen**. |
| 3 | Die Zugangsdaten (je nach Inhalt der Datei: Nutzer + Passwort und/oder OAuth Client ID/Secret) in DRIVE konfigurieren. |

Ob die Zugangsdaten für **KIC/Session-Login** (bisheriger Weg) oder für die **offizielle DA REST API** (OAuth2, api.werkstattplanung.net) gelten, steht erst nach dem Öffnen der Datei fest. Beides ist in Abschnitt 2 und 3 berücksichtigt.

### 1a. Tatsächlich erhaltene Zugangsdaten (Stand 2026-03-12)

Die entschlüsselte Datei enthält **OAuth Client ID und Client Secret pro Center** – also Zugang zur **DA REST API (Weg B)**. Pro Standort ein eigener Client:

| Center     | Anzeigename                         | Credentials                    |
|-----------|--------------------------------------|--------------------------------|
| **Landau**   | Autohaus Greiner GmbH - Landau     | Client ID, Client Secret       |
| **Deggendorf** | Autohaus Greiner GmbH - Deggendorf | Client ID, Client Secret       |

Es gibt **keine** separaten „Client Name“-Felder in der Datei; der Name ist die Bezeichnung des Standorts. Für OAuth (Password Grant) werden zusätzlich **Instanz-User** (E-Mail + Passwort) pro Center oder ein gemeinsamer API-Benutzer benötigt – den müsst ihr wie vom Support gefordert **im Center anlegen**.

**Stand 12.03.2026:** Im Gudat Center wurden zwei API-Benutzer angelegt (Landau: admin@auto-greiner.de; Deggendorf: **admin@opel-greiner.de** – E-Mail geändert, da pro Gudat nur einmal verwendbar). Passwörter wurden **per E-Mail von Gudat** zugestellt. Pro Center in `credentials.json`: username (E-Mail), password (von Gudat), client_id, client_secret. Details: `GUDAT_API_EINRICHTUNG_ANLEITUNG_SERVER.md`.

---

## 2. Zwei Wege der Gudat-API (Überblick)

In der Doku und im Projekt werden **zwei** Zugangswege unterschieden. Beide können für DRIVE relevant sein.

### Weg A: KIC / Instanz-URL (aktuell im Einsatz)

| Aspekt | Inhalt |
|--------|--------|
| **Basis-URL** | `https://werkstattplanung.net/greiner/deggendorf/kic` (ggf. plus Center „landau“) |
| **Auth** | Session: GET kic → POST `/login` (username, password) → GET `/ack` → Cookie `laravel_token`. Kein OAuth. |
| **REST (auf KIC)** | `GET /api/v1/workload_week_summary`, `GET /api/v1/user`, `GET /api/v1/config` |
| **GraphQL (auf KIC)** | `POST /graphql` – z. B. appointments, dossiers, orders, workshopTasks |
| **In der DA-Doku** | KIC/Instanz wird für Browser und Deeplinks erwähnt; **nicht** alle KIC-Endpoints (z. B. workload_week_summary) sind in der DA API V1 Reference beschrieben. |
| **Credentials heute** | `config/credentials.json` → `external_systems.gudat` → `username`, `password` |

Wenn die verschlüsselte Datei **nur** „API-Benutzer“ (E-Mail + Passwort) enthält, dann ist das der **gleiche** Zugang wie bisher, nur mit einem **dedizierten API-Benutzer** statt eines Personalkontos. Einrichtung = neuen User im Center anlegen, dann username/password in `credentials.json` eintragen.

### Weg B: DA REST API (api.werkstattplanung.net)

| Aspekt | Inhalt |
|--------|--------|
| **Basis-URL** | `https://api.werkstattplanung.net/da/v1` |
| **Auth** | **OAuth2** (Password Grant). Pro Request Header: `group`, `center`. Client ID/Name/Secret von Gudat. |
| **Dokumentation** | DA API V1 Reference (inkl. OpenAPI/Swagger-Spezifikation openapi.json). |
| **Credentials** | Client ID, Client Name, Client Secret (von Gudat); zusätzlich Instanz-User (E-Mail + Passwort) für Token. |
| **Im Projekt** | Bisher **nicht** genutzt; keine OAuth-Credentials in `credentials.json`. |

Wenn die verschlüsselte Datei **OAuth-Client-Daten** (Client ID, Secret o. Ä.) enthält, dann geht es um **diesen** Weg. Dann braucht DRIVE zusätzlich Konfiguration für Token-URL, group/center und ggf. Token-Speicherung/Refresh.

---

## 3. Funktionsumfang aus der API-Dokumentation (Swagger / OpenAPI)

Die **DA API V1 Reference** (und die darin referenzierte OpenAPI-Spezifikation) beschreiben die **offizielle REST API** unter `api.werkstattplanung.net/da/v1`. Die folgende Übersicht basiert auf der bestehenden Projekt-Doku (`GUDAT_ZUGRIFFE_PLAN_DOKU_ERWEITERUNG.md`, `GUDAT_API_INTEGRATION.md`, `GUDAT_ANFRAGE_OAUTH_CLIENT_MAIL.md`).

### 3.1 Authentifizierung (laut Doku)

- **OAuth2** (Password Grant).
- Endpoint: `/oauth/token` (Basis api.werkstattplanung.net/da/v1).
- Benötigt: **Client ID**, **Client Name**, **Client Secret** (von Gudat); User = E-Mail + Passwort der Instanz.
- Access Token (lange gültig, z. B. 1 Jahr), Refresh Token (z. B. +30 Tage).
- Bei 401: zuerst Refresh, bei erneutem 401 neuer Login.
- Pro Request: Header **`group`** und **`center`** (z. B. group=greiner, center=deggendorf bzw. center=landau).

### 3.2 Endpoints (aus Doku / OpenAPI)

| Bereich | Endpoints / Funktionen | Kurzbeschreibung |
|--------|------------------------|------------------|
| **Customers** | CRUD | Kundenstammdaten lesen/schreiben. |
| **Vehicles** | CRUD | Fahrzeugstammdaten lesen/schreiben. |
| **Orders** | GET (Liste, Filter), GET (einzelner Auftrag nach order_number), PATCH (Update), POST (Create) | Aufträge aus DA lesen und ggf. aktualisieren/anlegen. |
| **Documents** | Upload/Attach an Dossier, Get Content | Dokumente an Dossiers hängen, Dokumentinhalt abrufen (z. B. für DSE-PDF). |
| **Online Booking / Service** | Service Events (Liste, Einzel, Create, Update, Cancel), Slots, States, Workshop Tasks, Resources, Event Types, Booking Configuration | Termine, Kapazitäten, Workshop-Tasks, Buchungskonfiguration. |
| **Archive** | Archive documents | Archiv-Dokumente. |
| **Status** | status_triggers | Status-Trigger (z. B. Kamera/Scanner). |

Die **genaue** Pfadliste und Parameter stehen in der **OpenAPI-Datei** (openapi.json), die zur DA API V1 Reference gehört. Sobald die verschlüsselte Datei geöffnet ist und/oder die Referenz im Browser verfügbar ist, sollte die OpenAPI-Spec (z. B. unter .../da/docs/ oder als Download) abgeglichen werden, um alle Pfade und Request/Response-Schemas zu erfassen.

### 3.3 KIC-spezifische Endpoints (nicht zwingend in OpenAPI)

Diese nutzt DRIVE heute über **Weg A** (Session auf der Instanz-URL):

| Endpoint | Methode | Verwendung in DRIVE |
|----------|--------|----------------------|
| `/login` | POST | Session-Login. |
| `/ack` | GET | Setzt Cookie `laravel_token`. |
| `/api/v1/workload_week_summary` | GET | Kapazität/Kapazitätsplanung. |
| `/api/v1/user` | GET | Benutzerinfo. |
| `/api/v1/config` | GET | Mandanten-Konfiguration. |
| `/graphql` | POST | appointments, dossiers, orders, workshopTasks, dossier.note, states, etc. |

Ob diese in der **offiziellen** OpenAPI-Spec vorkommen oder nur instanzseitig verfügbar sind, ist in der Doku unterschiedlich beschrieben; für die Einrichtung reicht die Trennung: **Weg A = KIC**, **Weg B = api.werkstattplanung.net/da/v1**.

---

## 4. Was wir brauchen (Checkliste)

### 4.1 Sofort (unabhängig vom Inhalt der Zugangsdaten)

| Nr | Aufgabe | Verantwortung |
|----|---------|---------------|
| 1 | Verschlüsselte Datei mit dem Passwort aus der zweiten E-Mail öffnen und Inhalt sichten. | Greiner |
| 2 | **Im Center** (Gudat/DA) einen **Benutzer für die API-Nutzung** anlegen, wie vom Support gefordert. | Greiner (Admin im Center) |
| 3 | Klären: Enthält die Datei nur **User + Passwort** (für KIC) oder zusätzlich **OAuth Client ID/Secret** (für DA REST API)? | Auswertung der Datei |

### 4.2 Falls nur KIC-Zugang (User + Passwort)

| Nr | Aufgabe | Wo |
|----|---------|-----|
| 1 | API-Benutzer (E-Mail + Passwort) in `config/credentials.json` unter `external_systems.gudat` eintragen (`username`, `password`). | credentials.json |
| 2 | Bestehende Nutzer von `gudat_data.py`, `gudat_client.py`, `arbeitskarte_api.py`, `werkstatt_live_api.py` verwenden bereits diese Config; kein Code nötig, nur Werte anpassen. | – |
| 3 | Kurz testen: Login (GET kic → POST login → GET ack), dann z. B. workload_week_summary oder GraphQL-Aufruf. | Manuell oder kleines Testskript |

### 4.3 OAuth-Zugang (DA REST API) – vorliegende Credentials

Die Zugangsdaten liegen vor: **pro Center** je **Client ID** und **Client Secret**. Vorschlag Konfiguration:

| Nr | Aufgabe | Wo / Anmerkung |
|----|---------|----------------|
| 1 | OAuth-Credentials pro Center in `config/credentials.json` ablegen. Vorschlag Struktur (siehe unten). | `external_systems.gudat` um `oauth_centers` bzw. pro Center erweitern |
| 2 | **group** = `greiner`, **center** = `deggendorf` bzw. `landau` – fest in Config oder Konstante. | Keine echten Geheimnisse in Doku |
| 3 | **Instanz-User:** API-Benutzer im Center anlegen (Support-Hinweis); E-Mail + Passwort für OAuth Password Grant. Entweder ein User pro Center oder klären, ob ein User für beide reicht. | credentials.json oder eigener Block |
| 4 | Konzept: Token-URL (z. B. `https://api.werkstattplanung.net/da/v1/oauth/token`), Token-Anforderung (Password Grant), Speicherung nur Backend, Refresh bei 401. | Doku, kein Code |
| 5 | Entscheidung: Welche DRIVE-Funktionen künftig über DA REST API laufen, welche weiter über KIC (Weg A). | Plan, Priorisierung |

**Vorschlag Struktur `credentials.json` (nur Struktur, keine echten Werte):**

```json
{
  "external_systems": {
    "gudat": {
      "username": "...",
      "password": "...",
      "api_base_url": "https://api.werkstattplanung.net/da/v1",
      "group": "greiner",
      "centers": {
        "deggendorf": {
          "client_id": "<Client ID Deggendorf>",
          "client_secret": "<Client Secret Deggendorf>"
        },
        "landau": {
          "client_id": "<Client ID Landau>",
          "client_secret": "<Client Secret Landau>"
        }
      }
    }
  }
}
```

`username`/`password` = der im Center angelegte API-Benutzer (für OAuth Password Grant). Ob ein gemeinsamer User für beide Center reicht oder pro Center einer nötig ist, ggf. mit Gudat klären.

---

## 5. Was wir nutzen können (Funktionsumfang für DRIVE)

### 5.1 Bereits in DRIVE genutzt (Weg A – KIC)

- **Live-Board / Werkstatt-Übersicht:** Wer arbeitet an was? (GraphQL: workshopTasks, ggf. appointments.)
- **Kapazitätsplanung:** workload_week_summary (REST auf KIC).
- **Arbeitskarte:** Dossier, Orders, Note, States, Diagnose (GraphQL).
- **Auftragsdetail im Portal:** Gudat-Daten zu einem Auftrag (Dossier, Tasks).
- **Gudat-Fakturierungsstatus:** Dossier states (ergänzend zu Locosoft).

Diese Funktionen bleiben unverändert nutzbar, sobald der **neue API-Benutzer** (User + Passwort) im Center angelegt und in `credentials.json` eingetragen ist.

### 5.2 Mit offizieller DA REST API (Weg B) möglich

| Nutzen | Endpoint / Bereich | Priorität / Anmerkung |
|--------|--------------------|------------------------|
| Service Events / Termine standardisiert | Service Events, Slots, States | Optional; heute über GraphQL auf KIC. |
| Dokumente an Dossier hängen | documents (Upload/Attach) | z. B. DSE-PDF von DRIVE nach Gudat; abhängig von OAuth-Einrichtung. |
| Orders lesen/aktualisieren | orders (GET/PATCH/POST) | Kann GraphQL ergänzen; Use-Cases und Priorität klären. |
| Kunden/Fahrzeuge (Stammdaten) | customers, vehicles | Nur relevant, wenn DRIVE Stammdaten in DA schreiben soll (z. B. Fahrzeuganlage). |
| Status-Trigger | status_triggers | Optional, für spätere Automatisierung. |

Priorisierung und konkrete Use-Cases sollten **nach** der Einrichtung (und nach Klärung, ob OAuth-Daten geliefert wurden) in einer eigenen Backlog-Liste erfolgen.

### 5.3 Einschränkung in der Greiner-Instanz

In der AGD-Verwaltung sind für die Schnittstelle „DA“ u. a. aktiviert: Auftrag erstellen, Stammdaten lesen/schreiben, Ersatzfahrzeug, Fahrzeug-/Kunden-Informationen. Nur diese Bereiche sind für die API-Nutzung freigegeben; die genannten Endpoints (orders, customers, vehicles, documents, service_events, …) sind in dem Rahmen nutzbar, den die Instanz-Freigabe zulässt.

---

## 6. Nächste Schritte (empfohlen)

1. **Datei öffnen:** Verschlüsselte Anlage mit dem Passwort aus der separaten E-Mail entschlüsseln und Inhalt dokumentieren (welche Felder: username/password und/oder client_id, client_secret, Token-URL, etc.).
2. **API-Benutzer anlegen:** Im Gudat/DA Center (greiner/deggendorf, ggf. landau) den vom Support verlangten Benutzer für die API-Nutzung anlegen.
3. **Entscheidung:** Nur KIC (Weg A) → Credentials in `credentials.json` eintragen und testen. Falls OAuth (Weg B) → Konfigurationsstruktur und Token-Handling in Doku festhalten, dann ggf. Backlog für OAuth-Integration und Nutzung der REST-Endpoints anlegen.
4. **Doku abgleichen:** Sobald die DA API V1 Reference (oder openapi.json) wieder zugänglich ist: unsere Übersicht (Abschnitt 3) mit der Swagger/OpenAPI-Spec abgleichen und fehlende Pfade/Parameter ergänzen.
5. **CONTEXT.md Werkstatt:** Nach der Einrichtung kurzen Eintrag hinzufügen (z. B. „Gudat API-Zugangsdaten von Support erhalten; API-Benutzer im Center angelegt; Credentials in credentials.json eingetragen; ggf. OAuth geplant.“).

---

## 7. Referenzen

| Dokument | Inhalt |
|----------|--------|
| `docs/GUDAT_API_INTEGRATION.md` | Technische Doku Login, REST, GraphQL (KIC). |
| `docs/workstreams/werkstatt/GUDAT_ZUGRIFFE_PLAN_DOKU_ERWEITERUNG.md` | Zwei Wege (KIC vs. DA REST API), OAuth, Erweiterungen. |
| `docs/workstreams/werkstatt/GUDAT_ANFRAGE_OAUTH_CLIENT_MAIL.md` | Mail-Entwurf für OAuth-Client-Anfrage. |
| `docs/workstreams/werkstatt/CONTEXT.md` | Gudat-Credentials (SSOT credentials.json), aktuelle Nutzung. |
| DA API V1 Reference | https://werkstattplanung.net/greiner/deggendorf/kic/da/docs/index.html (inkl. OpenAPI/Swagger). |

---

**Zusammenfassung:** Zuerst verschlüsselte Datei öffnen und API-Benutzer im Center anlegen. Dann je nach Inhalt der Zugangsdaten (nur User/Passwort vs. OAuth) die Konfiguration in DRIVE anpassen. Funktionsumfang aus der API-Doku (Swagger/OpenAPI) ist oben zusammengefasst; was wir konkret brauchen und nutzen können, ist in Abschnitt 4 und 5 beschrieben. Kein Code in diesem Plan – nur Einrichtungs- und Nutzungsplanung.
