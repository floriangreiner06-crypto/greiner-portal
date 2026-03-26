# Gudat: Migration auf neue API & Verbesserungen

**Stand:** 2026-03-12  
**Workstream:** werkstatt

---

## 1. Bisherige Funktionen in DRIVE (KIC/Session)

| Funktion | Wo genutzt | Technik aktuell | Daten |
|----------|------------|-----------------|------|
| **Kapazität/Workload** | Werkstatt Live, Kapazitätsplanung, gudat_data.get_kapazitaet() | KIC: GET `/api/v1/workload_week_summary` | base_workload, planned, absent, free pro Team/Tag |
| **Wochenübersicht** | Frontend Kapazität, mit_teams | KIC: gleicher Endpoint, 7 Tage | Tägliche Summen, optional teams_per_day |
| **Disposition (wer arbeitet wann an was)** | Werkstatt Live-Board, Gantt, gudat_data.get_disposition() | KIC: GraphQL `workshopTasks` | Mechaniker → Liste Tasks (Auftrag, Kennzeichen, Start, Vorgabe-AW) |
| **Arbeitskarte (Dossier/Orders/Tasks)** | arbeitskarte_api, PDF | KIC: Session + GraphQL (dossier, orders, workshopTasks) + ggf. REST | Diagnose, Anhänge, Terminblatt |
| **Gudat-Termine zu Aufträgen** | werkstatt_live_api (Auftragsliste mit_gudat) | KIC: GraphQL/Appointments pro Auftrag | termin_start, termin_ende, typ |
| **Health** | /api/gudat/health | KIC: Login-Status | logged_in |

**Einschränkung heute:** Alles läuft nur für **Deggendorf** (feste URL `werkstattplanung.net/greiner/deggendorf/kic`). **Landau** ist in diesen Flows nicht integriert. Auth: **Session** (Login + /ack für laravel_token, XSRF) – bei jedem neuen Prozess/Request ggf. erneuter Login.

---

## 2. Neue API (DA REST, OAuth) – was sie bietet

- **OAuth2** (Token pro Center), Header `group` + `center` → **beide Center** (deggendorf, landau) nutzbar.
- Endpoints u. a.: `/resources`, `/service_events`, `/orders`, `/documents`, `/free_slots`, `/event_types`, `/workshop_tasks`, …
- **Kein** Endpoint `workload_week_summary` in der DA REST API – der existiert nur im **KIC** (instanzspezifisch).

---

## 3. Migrations-Strategie (empfohlen)

### 3.1 Gemeinsame Token-Schicht (neu, sofort sinnvoll)

- **Ziel:** Ein Modul, das für jedes Center den OAuth-Token lädt, **cacht** (z. B. TTL 50 Min) und bei 401 Refresh/Neuanforderung auslöst.
- **Vorteil:** Weniger Roundtrips, stabilere Auth, eine Stelle für alle DA-REST-Calls.
- **Umsetzung:** z. B. `api/gudat_da_client.py` oder `tools/gudat_da_client.py`:
  - `get_token(center)` → aus Cache oder `POST /oauth/token` mit Credentials aus `credentials.json` (gudat.centers[center]).
  - `request(method, path, center, **kwargs)` → setzt `Authorization: Bearer <token>`, `group`, `center`; bei 401 Token invalidieren und einmalig retry.
- **Nutzer:** Alle künftigen DA-REST-Aufrufe (Ressourcen, Service Events, Urlaub ausplanen, ggf. Orders/Documents) gehen über diese Schicht.

### 3.2 Workload / Kapazität (Tages- & Wochenübersicht)

- **Befund:** `workload_week_summary` gibt es nur im **KIC**, nicht in der DA REST API.
- **Option A (pragmatisch):** Workload vorerst **unverändert über KIC** lassen (weiter `GudatClient` + `/api/v1/workload_week_summary`). Keine Migration für diesen Teil.
- **Option B (Landau sichtbar):** Falls Landau im KIC erreichbar ist (`https://werkstattplanung.net/greiner/landau/kic`), `GudatClient` um **Center-Parameter** erweitern (BASE_URL pro Center), gleiche Credentials-Struktur wie bei OAuth (centers.deggendorf / centers.landau). Dann Kapazitäts-API um `?center=deggendorf|landau` erweitern.
- **Option C (Rückfrage Gudat):** Beim Anbieter anfragen, ob ein **Workload-/Kapazitäts-Endpoint in der DA REST API** geplant ist. Wenn ja, langfristig dorthin migrieren.

**Empfehlung:** A jetzt, B wenn gewünscht (Landau-Kapazität im Portal), C parallel als Ausblick.

### 3.3 Disposition (wer arbeitet wann an was)

- **Aktuell:** GraphQL `workshopTasks` (KIC), gruppiert nach `resource.name` → Mechaniker → Liste Tasks.
- **Mit DA REST:**  
  - **GET /service_events** mit `filter[inRange]=<date>,<date>` und `include=resource` liefert Termine/Events pro Tag.  
  - Nach `resource_id` / `resource.name` gruppieren → ähnliche Struktur wie heute („Mechaniker → Liste Einsätze“).  
  - Zusätzlich: **resource_id** ist direkt verfügbar (für „Urlaub ausplanen“ und künftige Automatisierung).
- **Vorteil REST:** Einheitliche Auth (Token), **beide Center** abdeckbar, gleiche Datenbasis wie für Service Events (z. B. Urlaub blocken).
- **Migration:**
  1. Neue Funktion z. B. `get_disposition_via_rest(center, date)` die GET /service_events aufruft und in das bestehende Format (Dict[MechanikerName, List[Task]]) transformiert. Optional: `resource_id` in jedem Task mitspeichern.
  2. In `gudat_data.get_disposition()` (und werkstatt_live_api): Konfiguration oder Feature-Flag „Disposition über REST (DA API)“; wenn an, REST für gewähltes Center nutzen, sonst KIC GraphQL wie bisher.
  3. Für **Landau:** Nur über REST möglich (KIC dort ggf. nicht angebunden). Für Deggendorf: wahlweise KIC oder REST (REST empfohlen, um ein Modell zu haben).

### 3.4 Arbeitskarte (Dossier, Orders, Documents)

- **Aktuell:** KIC-Session + GraphQL (dossier, orders, workshopTasks) + ggf. REST für Anhänge/Downloads.
- **DA REST:** `/orders` (GET/PATCH), `/documents` (Upload, Get Content). Ob „Dossier“ 1:1 als Order abgebildet ist, muss anhand der OpenAPI/Response geprüft werden.
- **Migration:** Optionaler späterer Schritt: Dossier-Zugriff über GET /orders (Filter order_number?) + /documents ersetzen, sofern fachlich äquivalent. Dann Arbeitskarte schrittweise auf Token-Schicht umstellen (kein Session-Login mehr für diesen Teil).

### 3.5 Gudat-Termine zu Aufträgen (mit_gudat)

- Heute: KIC-spezifisch (Deggendorf), Abgleich Auftrag ↔ Gudat-Termin.
- Mit REST: GET /service_events mit Filter (z. B. Kennzeichen oder Auftragsnummer, falls in API abfragbar) → gleiche Anzeige „hat_gudat_termin“, „gudat_termin“, „gudat_termin_ende“. Landau kann mit abgedeckt werden, wenn wir pro Center abfragen.

---

## 4. Was wir verbessern können (mehr Infos, schneller)

| Aspekt | Heute | Mit Migration / Erweiterung |
|--------|------|-----------------------------|
| **Schneller** | Pro Request/Prozess ggf. KIC-Login (GET /kic, POST /login, GET /ack). Kein Token-Cache. | **OAuth-Token einmal pro Center cachen** (z. B. 50 Min). Alle DA-REST-Calls ohne erneuten Login. Weniger Latenz bei Kapazität/Disposition wenn auf REST umgestellt. |
| **Mehr Infos** | Disposition nur Name + Task-Daten (Auftrag, Kennzeichen, Start, Vorgabe). | Mit REST: **resource_id** in jedem Eintrag → Zuordnung zu GET /resources, Nutzung für Urlaub ausplanen (POST /service_events). **event_type_id** für Typ (Reparatur vs. Urlaub/Abwesenheit). Optional **event_types** abrufen und anzeigen. |
| **Landau** | Nicht integriert. | **Beide Center** über DA REST (und ggf. KIC für Workload Landau, falls URL verfügbar). Kapazität/Disposition/Werkstatt Live filterbar nach Standort. |
| **Stabilität** | Session kann ablaufen; XSRF/laravel_token fehleranfällig bei parallelen Aufrufen. | OAuth standardisiert; Token-Refresh bei 401 in einer zentralen Schicht. |
| **Einheitliches Modell** | KIC (Session) + teils eigene Credentials (nur ein User). | **Eine Credential-Struktur** (gudat.centers.{deggendorf|landau}) für OAuth; KIC nur noch dort, wo REST keine Alternative hat (workload_week_summary). |

---

## 5. Konkrete nächste Schritte (Priorität)

1. **Token-Schicht bauen**  
   - Modul `get_token(center)`, Cache, 401-Retry.  
   - Alle neuen DA-REST-Aufrufe (z. B. Ressourcen, Service Events) darüber laufen lassen.

2. **Disposition über REST anbieten**  
   - GET /service_events mit `filter[inRange]` + `include=resource` für ein Datum.  
   - Response in bestehendes Format (Mechaniker → Tasks) transformieren, inkl. `resource_id`.  
   - In `gudat_data` / Werkstatt Live optional aktivierbar (z. B. pro Center oder global „REST für Disposition“).

3. **Workload weiter KIC**  
   - Keine Umstellung, solange kein Workload-Endpoint in DA REST existiert.  
   - Optional: KIC-URL pro Center (Landau), falls gewünscht und von Gudat angeboten.

4. **Landau in der UI**  
   - Wo Kapazität/Disposition angezeigt wird: Auswahl oder Filter **Center/Standort** (Deggendorf / Landau).  
   - Backend: Für Landau nur REST nutzen (Disposition + ggf. Ressourcen); für Deggendorf KIC oder REST (siehe oben).

5. **Urlaub ausplanen**  
   - Wie in `GUDAT_OPENAPI_AUSWERTUNG_URLAUB_AUSPLANEN.md`: Mapping Mitarbeiter ↔ resource_id (aus GET /resources), dann POST /service_events für Abwesenheitszeitraum.  
   - Nutzt dieselbe Token-Schicht und dieselben Ressourcen-Listen.

---

## 6. Kurzfassung

- **Migration:** Schrittweise. Zuerst **gemeinsame OAuth-Token-Schicht**, dann **Disposition über GET /service_events** (mehr Infos, z. B. resource_id; beide Center). Workload vorerst **weiter KIC** (evtl. KIC-URL pro Center für Landau).
- **Verbesserungen:** Schneller durch Token-Cache, mehr Infos (resource_id, event_type), Landau integrierbar, stabilere Auth.
- **Risiko minimieren:** KIC parallel weiter nutzbar lassen; REST optional per Konfiguration/Feature aktivieren.

Referenzen:  
- `GUDAT_API_FUNKTIONSUMFANG_UND_CENTER.md`  
- `GUDAT_OPENAPI_AUSWERTUNG_URLAUB_AUSPLANEN.md`  
- `da-api-v1-openapi.json`
