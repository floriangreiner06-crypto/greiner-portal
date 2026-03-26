# Gudat API – Funktionsumfang mit echter API & Center/Standort

**Stand:** 2026-03-12  
**Workstream:** werkstatt

---

## 1. Landau neu – Center/Standort beachten

**Bisher:** In unserer Schnittstelle (Werkstatt Live, Kapazität, Arbeitskarte, GraphQL) war **nur Deggendorf** angebunden – eine feste KIC-URL: `https://werkstattplanung.net/greiner/deggendorf/kic`. Landau war **nicht** integriert.

**Jetzt:** Über die **DA REST API** (OAuth) haben wir Zugriff auf **beide Center**: `deggendorf` und `landau` (group=greiner, center=deggendorf bzw. landau). Landau ist damit erstmals in unserer API-Anbindung nutzbar.

**Konsequenz für DRIVE:**

- Wo wir Gudat-Daten anzeigen oder auswerten, müssen wir **künftig ggf. nach Center/Standort unterscheiden oder filterbar machen** (z. B. „nur Deggendorf“, „nur Landau“, „beide“).
- Technisch: Jeder Aufruf an die echte API benötigt den Header **center** (deggendorf oder landau); die Credentials liegen pro Center in `config/credentials.json` unter `gudat.centers`.
- Bestehende KIC-Nutzung (Werkstatt Live, Kapazität, GraphQL) bleibt vorerst **nur Deggendorf**, solange wir die KIC-URL nicht pro Center umschalten. Sobald wir die **REST API** für Landau-Daten nutzen, ist die Center-Unterscheidung ohnehin mit abgebildet.

---

## 2. Was können wir mit der echten API jetzt umsetzen?

Die **DA REST API** (`https://api.werkstattplanung.net/da/v1`) ist mit OAuth (Token) und Header **group** + **center** nutzbar. Folgender Funktionsumfang ist laut Doku/OpenAPI verfügbar und **mit der aktuellen Einrichtung umsetzbar** (ohne weitere Freischaltung):

| Bereich | Endpoints / Funktionen | Was wir damit umsetzen können |
|--------|------------------------|-------------------------------|
| **Orders** | GET (Liste, Filter), GET (einzelner Auftrag nach order_number), PATCH (Update), POST (Create) | Auftragsliste pro Center, Einzelauftrag lesen/aktualisieren, ggf. Anmerkung/Status aus DRIVE zurückschreiben. |
| **Documents** | Upload/Attach an Dossier, Get Content | Dokumente (z. B. DSE-PDF) an Dossier hängen, Dokumentinhalt abrufen. |
| **Service Events / Termine** | Service Events (Liste, Einzel, Create, Update, Cancel), Slots, States, Workshop Tasks, Resources, Event Types, Booking Configuration | Termine/Kapazitäten pro Center auswerten oder steuern; Abgleich mit unserem bisherigen GraphQL-Appointments-/workshopTasks-Zugriff. |
| **Customers** | CRUD | Kundenstammdaten lesen/schreiben (z. B. wenn Fahrzeuganlage „auch in Gudat anlegen“ gewünscht). |
| **Vehicles** | CRUD | Fahrzeugstammdaten lesen/schreiben. |
| **Archive** | Archive documents | Archiv-Dokumente abrufen. |
| **Status** | status_triggers | Status-Trigger (z. B. Kamera/Scanner) – für spätere Automatisierung. |

**Wichtig:** Alle Aufrufe laufen **pro Center** (Header `center=deggendorf` oder `center=landau`). Für Landau können wir damit dieselben Funktionen wie für Deggendorf nutzen – vorher war Landau in unserer Schnittstelle nicht abgebildet.

**Einschränkung:** Die genauen Pfade und Request/Response-Schemas stehen in der **OpenAPI-Spezifikation** der DA API V1 (Referenz: werkstattplanung.net/.../kic/da/docs). Bei der Umsetzung die offizielle Doku bzw. OpenAPI zu Rate ziehen.

---

## 3. Was geht mehr als bisher?

| Aspekt | Bisher (nur KIC, Deggendorf) | Mit echter API (OAuth, beide Center) |
|--------|------------------------------|--------------------------------------|
| **Center/Standort** | Nur Deggendorf (feste KIC-URL) | **Deggendorf + Landau** – explizit wählbar pro Request (Header `center`). |
| **Stabilität/Auth** | Session (XSRF, laravel_token, /ack); instanzspezifisch, nicht in DA-Doku beschrieben | **OAuth2** (Token, Refresh) – offiziell dokumentiert, gleicher Mechanismus für beide Center. |
| **Dokumente** | Kein Upload aus DRIVE in Gudat dokumentiert | **Documents:** Upload/Attach an Dossier, Get Content – z. B. DSE-PDF von DRIVE in Gudat anhängen. |
| **Orders** | Über GraphQL (Dossier/Orders) | **REST:** GET/PATCH/POST – standardisierte CRUD-Operationen, ggf. Filter, Update von Anmerkung/Status. |
| **Termine/Service** | GraphQL (appointments, workshopTasks) | **REST:** Service Events, Slots, States, Workshop Tasks, Booking Configuration – gleiche Daten evtl. über einheitliche REST-API, pro Center. |
| **Stammdaten** | Nicht über unsere Integration genutzt | **Customers/Vehicles** (CRUD) – wenn gewünscht: Stammdaten in DA lesen/schreiben (z. B. Fahrzeuganlage). |

**Kurz:** Mit der echten API können wir **beide Standorte** bedienen, **offiziell dokumentierte** Endpoints nutzen und **mehr Funktionen** (Dokument-Upload, Orders REST, Service Events, Stammdaten) umsetzen. Die bestehende KIC-Nutzung (Werkstatt Live, Kapazität, GraphQL) deckt weiterhin **nur Deggendorf** ab – Erweiterung auf Landau oder Umstellung auf REST pro Center ist ein nächster Schritt.

---

## 4. Nächste Schritte (Empfehlung)

1. **Center/Standort in DRIVE:** Wo Gudat-Daten angezeigt oder gefiltert werden, Option „Center/Standort“ (Deggendorf / Landau / beide) vorsehen – Konzept oder Umsetzung je nach Modul.
2. **Token-Schicht:** Zentrale Funktion/Modul, das pro Center den OAuth-Token lädt (oder aus Cache nutzt), bei 401 Refresh/Neuanforderung durchführt und alle Aufrufe an `api.werkstattplanung.net/da/v1` mit group/center versieht.
3. **Erste Use-Cases mit REST:** Z. B. Orders pro Center abfragen oder Service Events – dann OpenAPI/Referenz für exakte Pfade und Parameter nutzen.
4. **Optional:** KIC weiter nur Deggendorf lassen oder schrittweise Teile (z. B. Kapazität Landau) über die REST API abdecken, um ein einheitliches Modell (Center-Parameter) zu haben.

---

**Referenzen:**  
- `GUDAT_API_EINRICHTUNG_PLAN.md` – Einrichtung, zwei Wege (KIC vs. REST)  
- `GUDAT_ZUGRIFFE_PLAN_DOKU_ERWEITERUNG.md` – Endpoints, OAuth, Erweiterungen  
- DA API V1 Reference (OpenAPI): werkstattplanung.net/.../kic/da/docs
