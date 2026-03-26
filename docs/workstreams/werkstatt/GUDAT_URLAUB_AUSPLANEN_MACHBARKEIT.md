# Machbarkeit: Mechaniker aus Gudat-Kapazität „ausplanen“ bei genehmigtem Urlaub (DRIVE)

**Stand:** 2026-03-12  
**Workstream:** werkstatt (Schnittstelle zu urlaubsplaner)

---

## Ziel

Wenn im **Urlaubsplaner DRIVE** ein Urlaubsantrag **genehmigt** wird, soll der betroffene **Mechaniker in der Gudat-Kapazität** für die betreffenden Tage „ausgeplant“ werden – d. h. in Gudat als abwesend gelten, damit die Kapazitätsanzeige (z. B. „frei“, „absence_workload“) stimmt und keine Doppelplanung entsteht.

**Kurz:** Urlaub genehmigt in DRIVE → Abwesenheit in Gudat setzen (pro Person + Datum).

---

## Ausgangslage

### DRIVE Urlaubsplaner

- **Genehmigung:** `POST /api/vacation/approve` (booking_id); Status wird auf `approved` gesetzt, E-Mails gehen raus, ggf. Kalender-Update.
- **Daten:** `vacation_bookings` (employee_id, booking_date, day_part, status, vacation_type_id); Verknüpfung zum Mitarbeiter über `employees` (inkl. Locosoft-/Abteilungsdaten).
- Es gibt **keine** bestehende Anbindung „bei Genehmigung → Gudat informieren“.

### Gudat Kapazität

- **Aktuell:** Wir **lesen** nur: `GET /api/v1/workload_week_summary` (KIC) liefert pro Team/Tag u. a. `base_workload`, `planned_workload`, **`absence_workload`**, `free_workload`, `members` (mit pro Member u. a. `absence_workload`).
- Gudat **berechnet** die Kapazität also unter Berücksichtigung von Abwesenheiten. Woher Gudat diese Abwesenheiten bekommt (manuell in Gudat gepflegt, oder API), ist aus unserer Doku nicht eindeutig.
- **Wichtig:** Wir haben derzeit **keinen** Aufruf, der **Abwesenheit in Gudat anlegt oder ändert**.

### Zuordnung Mechaniker DRIVE ↔ Gudat

- In **gudat_data.py** gibt es `match_mechaniker_name(locosoft_name, gudat_names)` und `create_mechaniker_mapping` – also eine **Namenszuordnung** Locosoft/DRIVE ↔ Gudat (Gudat liefert teils „Unknown“, was das Mapping erschwert).
- Mitarbeiter in DRIVE: `employees` (mit Locosoft-Bezug über `ldap_employee_mapping.locosoft_id` o. Ä.); Urlaub: `vacation_bookings.employee_id` + Datum.

---

## Was fehlt für die Umsetzung?

### 1. Gudat-Seite: Abwesenheit schreiben

- **KIC (bisherige Nutzung):** Es ist **nicht** dokumentiert, dass wir über die KIC-URL Abwesenheiten **anlegen** können. Die Doku beschreibt nur **Lesen** (workload_week_summary, GraphQL).
- **DA REST API (OpenAPI geprüft, Stand 2026-03-12):** Es gibt **keinen** eigenen Endpoint „Absence“ oder „Resource block“. **Möglicher Weg:** **POST /service_events** mit minimalem Body: `start_date_time`, `end_date_time`, `resource_id` (Mechaniker), optional `event_type_id` (falls in der Instanz ein Typ „Urlaub“/„Abwesenheit“ existiert), `note`: „Urlaub (DRIVE)“ – blockiert die Ressource im Kalender und reduziert die Kapazität. Details und nächste Schritte: **`GUDAT_OPENAPI_AUSWERTUNG_URLAUB_AUSPLANEN.md`**.
- **Ressourcen- und Event-Typ-Abfrage:** GET **/resources** liefert die Liste der Mechaniker (inkl. `id`) pro Center; GET **/event_types** die verfügbaren Event-Typen – ob „Urlaub“ dabei ist, pro Instanz prüfen. Ein Pilot-POST (minimales Event ohne Kunde/Fahrzeug) sollte getestet werden.

### 2. Zuordnung Person DRIVE → Gudat-Ressource

- DRIVE: `employee_id` (employees), ggf. Locosoft-ID, Name, Standort/Abteilung.
- Gudat: In `workload_week_summary` kommen **members** mit Namen (oder „Unknown“); in der REST API vermutlich **Resources** mit IDs. Für „Mechaniker ausplanen“ brauchen wir eine **stabile Zuordnung** DRIVE-Mitarbeiter ↔ Gudat-Ressource (ID oder eindeutiger Bezeichner).
- **Vorgehen:** Mapping-Tabelle oder Logik (z. B. Name, Locosoft-ID, Standort) nutzen; ggf. in Gudat prüfen, ob Ressourcen/User-IDs oder -Namen konsistent sind. Das bestehende `match_mechaniker_name` ist ein erster Anhaltspunkt; für **Schreiben** braucht man vermutlich eine **Gudat-Ressourcen-ID** pro Mitarbeiter.

### 3. Center/Standort

- Urlaubsplaner kann mit **Standort/Abteilung** arbeiten; Gudat hat **Center** (deggendorf, landau). Nur Mechaniker des **richtigen Center** in Gudat ausplanen (z. B. Landau-MA nur in Gudat Landau).

---

## Bewertung

| Aspekt | Status | Nächster Schritt |
|--------|--------|-------------------|
| **Abwesenheit in Gudat schreiben** | Unklar | **OpenAPI/DA API V1** prüfen: Endpoint für Absence / Resource-Block / Service-Event-Typ „Urlaub“; ggf. Gudat Support (developer@digitalesautohaus.de) fragen. |
| **Zuordnung Mechaniker → Gudat** | Teilweise vorhanden (Name-Matching) | Für Schreiben: Gudat-Ressourcen-IDs pro Mitarbeiter klären; ggf. Abfrage „Resources“ oder Konfiguration. |
| **Trigger „Urlaub genehmigt“** | In DRIVE vorhanden | Nach Genehmigung (approve/approve-batch) einen Aufruf an eine neue „Gudat-Abwesenheit“-Funktion anbinden (synchrone API oder Celery-Task). |
| **Center-Zuordnung** | Noch nicht umgesetzt | Mitarbeiter ↔ Center (deggendorf/landau) zuordnen; nur für passendes Center an Gudat senden. |

**Fazit:**  
**Grundsätzlich machbar**, sofern Gudat eine **Schreib-API für Abwesenheit** (oder ein gleichwertiges Mittel, z. B. Service Event „Urlaub“) anbietet. Der Ablauf „Urlaub genehmigt → Aufruf DRIVE → Gudat-API“ und die Zuordnung Mitarbeiter ↔ Gudat-Ressource sind in DRIVE umsetzbar; die **kritische Abhängigkeit** ist die **Dokumentation bzw. Freigabe** des passenden Gudat-Endpoints (und der nötigen Ressourcen-IDs).

---

## Empfohlene nächste Schritte

1. **OpenAPI ausgewertet:** Siehe **`GUDAT_OPENAPI_AUSWERTUNG_URLAUB_AUSPLANEN.md`**. Kurz: Kein Absence-Endpoint; **POST /service_events** mit `resource_id` + Zeitraum als Blockierung nutzbar; GET /resources und GET /event_types für Mapping und Event-Typ „Urlaub“.
2. **Pilot:** Minimales Service Event (nur start/end, resource_id, note) anlegen und prüfen, ob die API es akzeptiert; GET /event_types prüfen, ob „Urlaub“/„Abwesenheit“ existiert.
3. **Integration:** Nach Genehmigung in vacation_api Aufruf einbauen (z. B. Celery-Task), Mapping Mitarbeiter ↔ Gudat resource_id + Center pflegen; bei Storno DELETE /service_events/{id}.

---

**Referenzen:**  
- Urlaub genehmigen: `api/vacation_api.py` (approve, approve-batch)  
- Gudat Kapazität: `api/gudat_api.py`, `tools/gudat_client.py`, `docs/GUDAT_API_INTEGRATION.md`  
- Mechaniker-Mapping: `api/gudat_data.py` (match_mechaniker_name, create_mechaniker_mapping)  
- DA REST API: `docs/workstreams/werkstatt/GUDAT_API_FUNKTIONSUMFANG_UND_CENTER.md`
