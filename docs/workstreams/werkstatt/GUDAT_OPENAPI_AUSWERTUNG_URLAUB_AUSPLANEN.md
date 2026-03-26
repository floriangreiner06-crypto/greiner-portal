# Gudat DA API OpenAPI – Auswertung „Urlaub ausplanen“

**Stand:** 2026-03-12  
**Quelle:** `docs/workstreams/werkstatt/da-api-v1-openapi.json` (aus Windows-Sync übernommen)

---

## 1. OpenAPI-Spec

- **Datei:** `da-api-v1-openapi.json` im Werkstatt-Workstream
- **Basis-URL:** `https://api.werkstattplanung.net/da/v1`
- **Auth:** OAuth2 (Password Grant), Header `group`, `center`

---

## 2. Gibt es einen „Absence“- oder „Abwesenheit“-Endpoint?

**Nein.** In der OpenAPI kommt kein Endpoint mit „absence“, „abwesenheit“, „availability“ oder „block“ vor. Abwesenheiten werden in der **KIC**-Antwort (`workload_week_summary`) als `absence_workload` **berechnet** angezeigt; ein eigener Schreib-Endpoint dafür ist in der DA REST API **nicht** definiert.

---

## 3. Relevante Endpoints für „Mechaniker ausplanen“

| Endpoint | Methode | Zweck |
|----------|--------|--------|
| **/resources** | GET | Liste der **Ressourcen** (Mechaniker/Teams) inkl. `id`, `name`, `staff_id`, `is_visible_in_calendar`. Wird benötigt, um DRIVE-Mitarbeiter einer **Gudat-Ressourcen-ID** zuzuordnen. |
| **/event_types** | GET | Liste der **Event-Typen** (z. B. Service, Abholung, …). Ob ein Typ „Urlaub“ oder „Abwesenheit“ existiert, muss pro Instanz abgefragt werden (`GET /event_types`). |
| **/service_events** | POST | **Neues Service Event anlegen.** Ein Event blockiert eine **Ressource** (`resource_id`) für einen Zeitraum (`start_date_time`, `end_date_time`). |
| **/service_events/{id}** | PATCH, DELETE | Event ändern oder **löschen** (z. B. wenn Urlaub storniert wird). |

---

## 4. POST /service_events – minimale Nutzung für „Urlaub“

Laut Schema **ServiceEvent** / **ServiceEventWithoutDates**:

- **Pflichtfelder** nur: `start_date_time`, `end_date_time` (Format `Y-m-d H:i:s`).
- **Optional** u. a.: `resource_id`, `event_type_id`, `note`, Kunden-/Fahrzeugdaten, `workshop_tasks`, `statables`, `attachments`.

**Schlussfolgerung:** Theoretisch kann ein **minimales** Service Event mit z. B.  
`start_date_time`, `end_date_time`, `resource_id` (Mechaniker), `event_type_id` (falls „Urlaub“/„Abwesenheit“ vorhanden), `note`: „Urlaub (DRIVE)“  
angelegt werden. Das blockiert die Ressource in dem Zeitraum und reduziert die verfügbare Kapazität (analog zu Abwesenheit).

**Offen:** Ob die API ein Service Event **ohne** Kunden-/Fahrzeugdaten und ohne `workshop_tasks` akzeptiert, steht in der OpenAPI nicht explizit; die Beispiele in der Doku zeigen volle Buchungen. Ein **Pilotaufruf** (minimaler POST) in der Greiner-Instanz oder Rückfrage beim Gudat Support wird empfohlen.

---

## 5. Ablauf „Urlaub genehmigt → in Gudat ausplanen“ (Vorschlag)

1. **Urlaub in DRIVE genehmigt** (bestehender Flow: `approve` / `approve-batch`).
2. **Mitarbeiter + Datumsbereich** aus `vacation_bookings` + `employees` (inkl. Standort/Center).
3. **Mapping:** DRIVE-Mitarbeiter (employee_id / Locosoft-ID / Name) → **Gudat `resource_id`** (über GET /resources pro Center; ggf. Tabelle oder Konfiguration pflegen).
4. **Event-Typ:** GET /event_types für Center ausführen; prüfen, ob ein Typ „Urlaub“ oder „Abwesenheit“ existiert; dessen `id` für den POST verwenden (oder ohne `event_type_id` testen).
5. **Pro Urlaubstag (oder zusammenhängender Block):**  
   `POST /service_events` mit `group`, `center`, Body:  
   `start_date_time`, `end_date_time` (z. B. 08:00–17:00), `resource_id`, optional `event_type_id`, `note`: „Urlaub (DRIVE)“.
6. **Bei Stornierung/Abweisung** des Urlaubs: entsprechendes Service Event per `DELETE /service_events/{id}` entfernen (dafür muss die angelegte `service_event_id` pro Buchung gespeichert werden).

---

## 6. Nächste Schritte

1. **Ressourcen abrufen:** `GET /resources` (pro Center) ausführen und Liste mit Mechaniker-Namen/IDs dokumentieren; Zuordnung DRIVE ↔ `resource_id` anlegen.
2. **Event-Typen prüfen:** `GET /event_types` – ob „Urlaub“/„Abwesenheit“ vorhanden; wenn ja, ID notieren.
3. **Pilot-POST:** Ein minimales Service Event (nur start/end, resource_id, ggf. event_type_id, note) anlegen und prüfen, ob die API es akzeptiert und die Kapazität angepasst wird.
4. **Integration:** Nach Genehmigung in `vacation_api` (approve/approve-batch) Aufruf einer neuen Funktion (z. B. Celery-Task) einbauen, die pro Center und Mitarbeiter die Gudat-Resource-ID ermittelt und POST /service_events ausführt; bei Storno DELETE.

---

**Referenzen:**  
- OpenAPI: `docs/workstreams/werkstatt/da-api-v1-openapi.json`  
- Machbarkeit: `GUDAT_URLAUB_AUSPLANEN_MACHBARKEIT.md`
