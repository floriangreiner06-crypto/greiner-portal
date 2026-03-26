# Gudat: Neue API (OAuth) vs. KIC (User-Login) – Plan & Übersicht

**Stand:** 2026-03-12  
**Workstream:** werkstatt  
**Ziel:** Klarheit, ob wir die neue Gudat-API (client_id/client_secret) nutzen oder uns mit User einloggen – und was eine Umstellung bringt.

---

## 1. Aktueller Stand: Zwei Wege parallel

| | **KIC (User-Login)** | **Neue Gudat API (DA REST, OAuth)** |
|--|------------------------|--------------------------------------|
| **Auth** | Username + Passwort, Session (GET /kic, POST /login, GET /ack, Cookies/XSRF) | **Client_id + Client_secret + Username + Passwort** (OAuth2 Password Grant), Token pro Center |
| **Wo genutzt** | Kapazität/Workload, Disposition (Fallback), Arbeitskarte, Termine zu Aufträgen, Health | Disposition (primär), künftig z. B. Ressourcen, Service Events, Documents |
| **URL** | `werkstattplanung.net/greiner/<center>/kic` | `api.werkstattplanung.net/da/v1` (oder in credentials: api_base_url) |
| **Center** | Deggendorf (fest), Landau (KIC-URL separat) | Beide Center über Header `center=deggendorf|landau` |
| **Credentials** | `gudat.username`, `gudat.password` bzw. `gudat.centers.<center>.username/password` | `gudat.centers.<center>.client_id`, `client_secret`, `username`, `password` |

**Antwort auf die Frage:**  
- **Kapazität/Workload:** Wir loggen uns weiter mit **einem User** ein (KIC, Session).  
- **Disposition (und künftig mehr):** Wir nutzen die **neue API mit client_id/client_secret** – aber im OAuth **Password Grant** braucht sie **zusätzlich** Username + Passwort (also beides: Client-Credentials + User).

---

## 2. Nutzen wir die neue API (client_id/client_secret) oder nur User?

- **Ja, die neue API mit client_id/client_secret nutzen wir bereits** für die Disposition (DA REST, OAuth-Token in `api/gudat_da_client.py`).  
- Dort wird **OAuth2 Password Grant** verwendet: Es werden **sowohl** client_id/client_secret **als auch** username/password benötigt. Es ist also keine reine „App-Login ohne User“, sondern „App + User“.
- **KIC (nur User, keine client_id/secret)** nutzen wir weiter für alles, was die DA REST API **nicht** anbietet – vor allem **workload_week_summary** (Kapazität/Tages- und Wochenübersicht). Diesen Endpoint gibt es nur im KIC, nicht in der DA REST API.

**Kurz:**  
- **Neue API (client_id + client_secret + User):** ja, für Disposition und künftige DA-REST-Features.  
- **User-Login (KIC):** ja, für Kapazität/Workload und Fallbacks, solange es keinen Workload-Endpoint in der DA API gibt.

---

## 3. Was bringt eine Umstellung auf die Gudat-API (mehr Nutzung von DA REST)?

| Aspekt | Heute (KIC / gemischt) | Mit mehr Umstellung auf Gudat API (DA REST) |
|--------|------------------------|---------------------------------------------|
| **Auth** | Session (XSRF, /ack), pro Prozess/Request ggf. Login | Ein OAuth-Token pro Center, gecacht (z. B. 50 Min), weniger Roundtrips, standardisiert |
| **Stabilität** | Session kann ablaufen, 401 → Re-Login nötig | Token-Refresh/Neuanforderung zentral (z. B. bei 401), einheitliches Verhalten |
| **Landau** | KIC nur Deggendorf (bzw. zweite KIC-URL für Landau); Disposition bereits per REST für beide | Alle umgestellten Funktionen **beide Center** (deggendorf, landau) ohne zweiten Login-Flow |
| **Kapazität/Workload** | Nur KIC: `workload_week_summary` | **Kein Workload-Endpoint in DA REST** – Umstellung nur möglich, wenn Gudat einen anbietet (Rückfrage beim Anbieter) |
| **Disposition** | Bereits optional über DA REST; Fallback KIC | Vollständig über REST; KIC-Fallback entbehrlich |
| **Arbeitskarte / Dossier** | KIC GraphQL | Könnte auf DA REST `/orders`, `/documents` umgestellt werden (Aufwand, Abgleich Schema) |
| **Termine zu Aufträgen** | KIC | Könnte auf GET `/service_events` (Filter) umgestellt werden, beide Center |
| **Neue Funktionen** | KIC teils undokumentiert, instanzspezifisch | Ressourcen, Service Events, Event Types, Booking – offiziell dokumentiert (OpenAPI), pro Center |

**Konkrete Vorteile einer weiteren Umstellung:**  
- Weniger Abhängigkeit von KIC-Session und /ack.  
- Ein Credential-Modell pro Center (client_id, client_secret, username, password in `gudat.centers.*`).  
- Beide Standorte (Deggendorf + Landau) überall nutzbar, wo auf REST umgestellt.  
- Bessere Grundlage für Erweiterungen (z. B. Urlaub in Gudat ausplanen, Dokumente anhängen).

**Einschränkung:**  
- **Kapazität/Workload** kann erst dann auf die API „umgestellt“ werden, wenn Gudat einen entsprechenden Endpoint in der DA REST API bereitstellt. Bis dahin: weiter KIC (User-Login).

---

## 4. Empfohlener Plan (ohne Code, nur Plan)

1. **Beides beibehalten (wie jetzt)**  
   - **DA REST (OAuth, client_id/client_secret + User):** für Disposition und alle neuen Features, die die DA API hergibt.  
   - **KIC (nur User):** für Kapazität/Workload und ggf. Arbeitskarte/GraphQL, solange kein DA-Äquivalent existiert.

2. **Schrittweise mehr auf die Gudat-API umstellen**  
   - Disposition: bereits auf REST; KIC-Fallback langfristig optional machen oder entfernen.  
   - Termine zu Aufträgen: Konzept prüfen – Ablösung durch GET `/service_events` (Filter), dann Umstellung.  
   - Arbeitskarte/Dossier: prüfen, ob `/orders` und `/documents` fachlich reichen; wenn ja, schrittweise von KIC GraphQL auf REST umstellen.

3. **Kapazität/Workload**  
   - **Nicht** umstellbar, solange es keinen Workload-Endpoint in der DA REST API gibt.  
   - Optional: Bei Gudat anfragen, ob ein solcher Endpoint geplant ist. Wenn ja, langfristig dorthin migrieren; wenn nein, KIC (User-Login) dauerhaft für Kapazität beibehalten.

4. **Credentials**  
   - Pro Center eine einheitliche Struktur in `credentials.json`:  
     - Für DA REST: `client_id`, `client_secret`, `username`, `password` (wie heute).  
     - Für KIC (weiter): `username`, `password` (kann dieselbe User-Kennung sein wie bei OAuth).

5. **Dokumentation**  
   - In CONTEXT.md oder eigener Doku festhalten: „Kapazität = KIC (User); Disposition und Neues = DA REST (client_id/client_secret + User). Umstellung auf mehr API bringt Stabilität, beide Center, weniger KIC-Abhängigkeit; Kapazität erst umstellbar, wenn Gudat Workload in der API anbietet.“

---

## 5. Kurzfassung

- **Nutzen wir die neue Gudat-API mit client_id/client_secret?**  
  **Ja** – für Disposition und künftige DA-REST-Features (OAuth Password Grant: client_id + client_secret + username + password).

- **Loggen wir uns mit einem User ein?**  
  **Ja** – beim KIC (Kapazität/Workload) nur User; bei der neuen API zusätzlich zum Client (client_id/secret) ein User (username/password) für den Token.

- **Was bringt die Umstellung auf die Gudat-API?**  
  Stabilität (Token statt Session), beide Center, offizielle Doku, Erweiterbarkeit (Ressourcen, Service Events, Documents). Kapazität kann erst umgestellt werden, wenn Gudat einen Workload-Endpoint in der DA API anbietet.

- **Plan:** Zwei Wege beibehalten; schrittweise mehr auf DA REST umstellen (Disposition, ggf. Termine, Arbeitskarte); Kapazität bei KIC lassen, bis die API ein Äquivalent hat.

---

## 6. Swagger/OpenAPI geprüft: Workload-Endpoint in der DA REST API?

**Quelle:** `docs/workstreams/werkstatt/da-api-v1-openapi.json` (DA API V1 Reference)

**Alle Pfade in der Spec:**  
`/oauth/token`, `/customers`, `/vehicles`, `/archive/documents`, `/booking_configurations/{id}`, `/center_config`, `/documents/attach`, `/documents/{id}/view`, `/event_types`, **`/free_slots`**, `/mobilities`, `/orders`, `/resources`, `/salutations`, `/service_events`, `/service_events/{id}`, `/service_events/{id}/states`, `/state_categories`, `/states`, `/statables`, `/status_triggers`, `/vehicle_types`, `/workshop_services`, `/workshop_services/{id}`, `/workshop_tasks`, `/workshop_tasks/{id}`.

**Befund:**  
- Es gibt **keinen** Pfad wie `/workload_week_summary`, `/workload` oder `/capacity` in der DA REST API (Swagger).  
- **GET /free_slots** ist vorhanden: „Get free Slots for booking a service event“ – Parameter `start_date`, `end_date`, `duration`, optional `resource_ids[]`, `workshop_service_ids[]`, `booking_configuration_id`. Liefert **freie Buchungsslots** (Start/Ende pro Slot, `resource_id`), **nicht** die aggregierte Kapazitätsübersicht (base_workload, planned_workload, free_workload pro Team/Tag in AW) wie der KIC-Endpoint `workload_week_summary`.  
- `work_load` / `default_workload` / `workload_in_minutes` kommen in der Spec nur als **Schema-Felder** (z. B. bei WorkshopTask, WorkshopService/BookingConfiguration) vor, nicht als eigener Kapazitäts-API-Pfad.

**Fazit:**  
Für die **Kapazitätsplanung (AW pro Team/Tag, Auslastung)** liefert die aktuelle DA REST API (laut Swagger) **keinen** direkten Ersatz für den KIC-`workload_week_summary`. **/free_slots** kann für „wann kann ich buchen?“ genutzt werden, ist aber kein 1:1-Ersatz für „Kapazität/geplant/frei pro Team pro Tag“.  
Falls Gudat einen Workload-/Kapazitäts-Endpoint in einer neueren Version oder unter anderem Namen anbietet: OpenAPI-Datei aktualisieren oder bei Gudat (developer@digitalesautohaus.de) nachfragen.

---

## 7. Garantie-Feature (Arbeitskarte, Garantieakte)

**Was das Garantie-Feature von Gudat braucht:**  
- **Dossier-Zentrierung:** Suche nach Dossier anhand Auftragsnummer (oder Kennzeichen/VIN/Datum); Abruf des kompletten Dossiers inkl. `orders`, `workshopTasks`, `documents`, `note`, `states`, `comments`.  
- **Diagnose/Notizen:** `workshopTask.description`, `dossier.note`, `order.note` für Arbeitskarte-PDF und Garantie-Dokumentation.  
- **Anhänge:** Liste der Dokumente am Dossier, Download des Dokumentinhalts (Bilder/PDFs für Garantieakte).

**Technik heute:** KIC-Session + **GraphQL** (z. B. `workshopTasks` mit `dossier.orders`, `dossier(id)` mit `documents`, `workshopTasks`, `orders`, `note`, `states`). Dokument-Download über KIC-Session (URL oder GraphQL/Attachment).

**DA REST API (Swagger):**  
- Es gibt **keinen** Ressourcentyp **„Dossier“** in der DA REST API.  
- Vorhanden: **/orders**, **/orders/{order_number}/documents**, **/documents/{document_id}/view** – also Aufträge und Dokumente **nach Auftragsnummer**, nicht nach Dossier-ID.  
- **/service_events** liefert pro Event stark angereicherte Daten (inkl. dossier-ähnlicher Struktur in der Response), ist aber termin-/event-zentriert, nicht „ein Dossier mit allen Tasks/Orders/Documents“ wie in der KIC-GraphQL-Welt.

**Fazit:**  
Für das **Garantie-Feature** (Arbeitskarte, Garantieakte, Dossier-Suche, Anhänge, Diagnose-Texte) ist unsere **bisherige Abfrage über KIC (User-Login + GraphQL)** ebenfalls **praktisch alternativlos**: Die DA REST API bietet weder ein dossier-zentriertes Modell noch einen 1:1-Ersatz für die genutzten GraphQL-Queries (Dossier mit Orders, WorkshopTasks, Documents, Note, States). Eine Umstellung wäre nur mit erheblichem Aufwand denkbar (z. B. Suche über Orders/Service_events, Zusammenführung von Dokumenten und Tasks aus mehreren Endpoints, andere Datenstruktur) und ist ohne Dossier- oder gleichwertigen Endpoint in der DA API nicht sinnvoll abbildbar.
