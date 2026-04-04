# DRIVE-DMS: Werkstatt-DMS als SaaS-Prototyp

**Datum:** 2026-04-04
**Status:** Entwurf
**Autor:** Florian Greiner + Claude

---

## 1. Vision & Strategie

### Ziel

DRIVE (Greiner Portal) wird schrittweise zu einem vollwertigen Dealer Management System (DMS) ausgebaut und als SaaS-Produkt angeboten. Der erste Baustein ist ein eigenständiges **Werkstatt-DMS** mit integriertem Werkstattplaner.

### Stufenplan

1. **Phase: Greiner autark** — Werkstatt-DMS ersetzt GUDAT + Locosoft-SOAP im Werkstattbereich. DRIVE läuft parallel weiter für alle anderen Module.
2. **Phase: SaaS** — Wenn das Werkstatt-DMS bei Greiner produktiv läuft, wird es als Multi-Tenant-SaaS für andere Autohäuser angeboten. Weitere Module (Verkauf, Controlling, FiBu) folgen stufenweise.

### Abgrenzung (vorerst nicht im Scope)

- Keine eigene FiBu (bleibt Locosoft, wird später ein eigenes Modul)
- Kein Verkauf/Auftragseingang (bleibt DRIVE)
- Kein Urlaubsplaner, Bankenspiegel, Controlling (bleibt DRIVE)
- Kein eigenes Teile-Lager (Bridge zu DRIVE-PostgreSQL, später eigen)

---

## 2. Ansatz: Greenfield neben DRIVE

Neues Repo (`drive-dms`), neuer Tech-Stack, sauberer Start. DRIVE läuft unverändert weiter und wird auch weiterentwickelt. Das neue DMS wächst daneben ohne Migrationsdruck.

**Begründung:** DRIVE hat ~246.000 Zeilen gewachsenen Code mit tiefer Locosoft-Kopplung (165+ Dateien). Aushöhlen wäre teurer als neu bauen. Ein Greenfield-Repo gibt saubere Container-Architektur von Tag 1, kein SOAP-Altlast, Multi-Tenant in der DNA.

**Brücke zu DRIVE:** Ein Bridge-Service synchronisiert Stammdaten (Kunden, Fahrzeuge, Teile) aus DRIVEs PostgreSQL in das neue DMS. Locosoft bleibt als Datenquelle für FiBu/Stammdaten über die bestehenden DRIVE-Sync-Scripts.

---

## 3. Architektur

### 3.1 Hybrid-Container-Architektur

Kern bleibt ein Service (Gateway mit Auth, Tenant-Routing). Große Module werden eigene Services. Alles containerisiert.

### 3.2 Projektstruktur

```
drive-dms/
├── docker-compose.yml              # Lokale Entwicklung
├── docker-compose.prod.yml         # Produktion
│
├── services/
│   ├── gateway/                    # API Gateway (FastAPI)
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py             # Routing, CORS, Rate-Limiting
│   │       ├── auth/               # JWT + LDAP-Auth (Dual-Mode)
│   │       ├── tenant/             # Tenant-Erkennung (Subdomain/Header)
│   │       └── middleware/         # Logging, Metrics
│   │
│   ├── workshop/                   # Werkstatt-DMS (FastAPI)
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── models/             # SQLAlchemy Models
│   │       ├── services/           # Business-Logik
│   │       ├── api/                # REST Endpoints
│   │       └── events/             # Event-Publishing (Redis Streams)
│   │
│   └── bridge/                     # DRIVE-Brücke
│       ├── Dockerfile
│       └── app/                    # Sync: DRIVE-PG -> DMS-PG
│           ├── sync_customers.py
│           ├── sync_vehicles.py
│           └── sync_parts.py
│
├── frontend/                       # Next.js React App
│   ├── Dockerfile
│   └── src/
│       ├── app/                    # Next.js App Router
│       ├── components/
│       │   ├── planner/            # Werkstattplaner (DnD Timeline)
│       │   ├── orders/             # Auftragsmanagement
│       │   ├── cockpit/            # Serviceberater-Cockpit
│       │   └── shared/             # UI-Bibliothek
│       ├── hooks/
│       ├── stores/                 # Zustand State Management
│       └── api/                    # API Client (OpenAPI generated)
│
├── database/
│   ├── migrations/                 # Alembic Migrations
│   └── seeds/                      # Testdaten
│
└── infrastructure/
    ├── hetzner/                    # Terraform fuer Dev-Server
    └── scripts/                    # Deploy-Scripts
```

### 3.3 Container-Topologie

```
+-------------------------------------------------+
|                   Traefik                        |
|              (Reverse Proxy, SSL)                |
+--------+----------+----------+------------------+
|        |          |          |                   |
| frontend:3000  gateway:8000 |                   |
| (Next.js)      (FastAPI)    |                   |
|                    |        |                   |
|             workshop:8001  bridge:8002           |
|             (FastAPI)      (Sync)               |
|                    |        |                   |
+--------------------+--------+-------------------+
|         PostgreSQL 16        Redis              |
|     (Schema-per-Tenant)    (Cache + Events)     |
+-------------------------------------------------+
```

### 3.4 Tech-Stack

| Schicht | Technologie | Begründung |
|---------|-------------|------------|
| Frontend | Next.js 14, React 18, TypeScript | SaaS-Standard, bestes AI-Tooling |
| UI | Tailwind CSS, Lucide Icons | Schnell, konsistent, themebar |
| Drag&Drop | @dnd-kit | Performanter als Alternativen, React-nativ |
| State | Zustand + React Query | Leichtgewichtig, API-Cache eingebaut |
| Charts | Recharts | React-nativ, gute Kapazitaetsvisualisierung |
| Backend | FastAPI, Python 3.12 | Async, OpenAPI-Docs, modern |
| ORM | SQLAlchemy 2.0 + Alembic | Typisiert, Migrations eingebaut |
| Validation | Pydantic v2 | FastAPI-nativ, schnell |
| WebSocket | Socket.io | Rooms/Channels, Reconnect, Fallback |
| Background | Celery + Redis | Bewährt, kennt das Team aus DRIVE |
| Reverse Proxy | Traefik | Auto-SSL, Container-Discovery |
| DB | PostgreSQL 16 | Schema-per-Tenant, Migration zu DB-per-Tenant möglich |
| Cache/Events | Redis 7 | Pub/Sub für Echtzeit, Caching |
| CI/CD | GitHub Actions | Build + Deploy auf Hetzner/Bayernwasser |
| Tests | Pytest, Playwright | Backend + E2E Frontend |
| Linting | Ruff, ESLint, Prettier | Schnell, konsistent |

---

## 4. Datenmodell

### 4.1 Workshop Order (Werkstattauftrag)

```
Workshop Order
├── id (UUID)
├── tenant_id
├── order_number (auto-generiert, z.B. WA-2026-0412)
├── status: ENUM
│   ├── APPOINTMENT     (Termin angelegt)
│   ├── PREPARED        (Positionen + Teile geplant)
│   ├── DISPATCHED      (Werkstattmeister hat disponiert)
│   ├── CHECKED_IN      (Kunde da, unterschrieben)
│   ├── IN_PROGRESS     (Monteur arbeitet)
│   ├── QA              (Qualitaetskontrolle)
│   ├── COMPLETED       (fertig, Kunde kann abholen)
│   └── PICKED_UP       (abgeholt)
├── customer_id, vehicle_id (aus Bridge/Stammdaten)
├── scheduled_date, scheduled_time
├── advisor_id (Serviceberater)
├── location_id (Standort: DEG Opel, DEG Hyundai, Landau)
├── checkin_type: ENUM(SERVICE_ADVISOR, SELF_SERVICE)
├── checkin_signature (Base64, digitale Unterschrift)
├── checkin_photos[] (Fahrzeug-Zustandsfotos)
├── notes, priority
├── created_at, updated_at
```

### 4.2 Position (Arbeitsposition)

```
Position
├── id (UUID)
├── order_id (FK)
├── type: ENUM(LABOR, PARTS, SUBLET)
├── description
├── target_minutes (Soll-Zeit)
├── assigned_resource_id (Monteur)
├── assigned_lift_id (Hebebuehne)
├── scheduled_start, scheduled_end
├── status (analog zum Auftrag, eigener Lifecycle)
├── is_upsell (boolean, Nacharbeit/Zusatzarbeit)
├── upsell_approved_at, upsell_approved_by
├── sort_order
```

### 4.3 Time Entry (Stempelzeit)

```
Time Entry
├── id (UUID)
├── position_id (FK)
├── resource_id (FK, Monteur)
├── clock_in (timestamp)
├── clock_out (timestamp, nullable)
├── duration_minutes (berechnet)
├── corrected_by (nullable, SB der korrigiert hat)
├── correction_reason
```

### 4.4 Resource (Monteur / Hebebuehne)

```
Resource
├── id (UUID)
├── tenant_id
├── type: ENUM(MECHANIC, LIFT)
├── name
├── qualifications[] (z.B. "HV-Schein", "Klima", "Getriebe")
├── location_id (Standort)
├── working_hours (JSON: Mo-Fr 7-16 Uhr etc.)
├── color (fuer Planer-Visualisierung)
├── active (boolean)
```

### 4.5 Parts Cart (Teile-Warenkorb)

```
Parts Cart Item
├── id (UUID)
├── order_id (FK)
├── position_id (FK, optional)
├── part_number
├── part_name
├── quantity
├── source: ENUM(STOCK, ORDERED)
├── stock_reserved (boolean)
├── order_eta (nullable, bei Bestellung)
├── consumed (boolean, nach Einbau)
```

---

## 5. Auftrags-Workflow (vollstaendig)

### 5.1 Phasen

```
PHASE 1: KONTAKT & TERMIN
  Kunde kontaktiert (Anruf, E-Mail, WhatsApp, Online)
  -> Termin wird im System angelegt
  -> Phase 0-5: manuelle Erfassung durch SB (Kunde ruft an, SB legt Termin an)
  -> Spaeter: Online-Buchungsportal, WhatsApp-Bot, E-Mail-Parsing
  -> Status: APPOINTMENT

PHASE 2: VORBEREITUNG
  Aus Termin wird Vorab-Auftrag:
  - Positionen anlegen (Inspektion, Klima, Bremse...)
  - Teile pruefen: Lager -> Warenkorb reservieren, oder bestellen
  - Rueckruf-Aktionen / Herstellerkampagnen pruefen
  -> Status: PREPARED

PHASE 3: DISPOSITION (Tag vorher)
  Werkstattmeister plant im Planner:
  - Auftraege auf Monteure zuweisen
  - Hebebuehnen reservieren
  - Zeitslots festlegen
  - Teile-Verfuegbarkeit pruefen (Warnung wenn Teile fehlen)
  -> Status: DISPATCHED

PHASE 4: CHECK-IN (Kunde kommt)
  Zwei Wege:
  a) MIT Serviceberater:
     - Auftrag durchsprechen, Zusatzarbeiten?
     - Fotos (Schaeden, Zustand)
     - Digitale Unterschrift
     - Schluesseluebergabe
  b) SELF-SERVICE (Tjekvik-Kiosk):
     - Auftrag bestaetigen am Terminal/QR
     - Schluesselabgabe
     - Digitale Unterschrift
     - Fotos (optional)
  -> Status: CHECKED_IN

PHASE 5: AUSFUEHRUNG
  - Monteur stempelt ein (Tablet/Terminal)
  - Arbeiten ausfuehren
  - Zusatzarbeit entdeckt? -> SB informieren -> Kunde kontaktieren
    -> Freigabe -> Position hinzufuegen (is_upsell=true)
  - Teile aus Warenkorb verbrauchen
  - Monteur stempelt aus
  -> Status: IN_PROGRESS -> QA

PHASE 6: CHECK-OUT
  Zwei Wege:
  a) MIT Serviceberater: Arbeiten erklaeren, Rechnung, Schluessel
  b) SELF-SERVICE (Tjekvik): Rechnung anzeigen, Bezahlung, Schluessel
  -> Status: COMPLETED -> PICKED_UP
```

### 5.2 Nacharbeit / Upselling Flow

```
Monteur entdeckt Zusatzarbeit
  -> POST /api/v1/workshop/orders/:id/upsell-request
     { description, estimated_minutes, parts_needed[] }
  -> Push-Notification an Serviceberater (WebSocket + optional WhatsApp)
  -> SB kontaktiert Kunde (Telefon/WhatsApp)
  -> Kunde gibt frei oder lehnt ab
  -> PATCH /api/v1/workshop/orders/:id/upsell-request/:rid/approve
  -> Neue Position wird angelegt, Monteur/Buehne zugewiesen
  -> Teile bestellt/reserviert
```

---

## 6. API-Design

### 6.1 REST Endpoints

```
Gateway (gateway:8000)

/api/v1/auth/
  POST   /login                 JWT via LDAP oder Local Auth
  POST   /refresh               Token Refresh
  GET    /me                    User + Tenant + Permissions

/api/v1/workshop/ (-> workshop:8001)

  Orders:
  GET    /orders                         Liste, Filter, Pagination
  POST   /orders                         Neuer Auftrag (aus Termin oder manuell)
  GET    /orders/:id                     Detail mit Positionen + Warenkorb
  PATCH  /orders/:id                     Status/Zuweisung aendern
  GET    /orders/:id/history             Audit-Log
  POST   /orders/:id/upsell-request      Nacharbeit melden
  PATCH  /orders/:id/upsell-request/:rid/approve   Nacharbeit freigeben

  Positions:
  POST   /orders/:id/positions           Position hinzufuegen
  PATCH  /orders/:id/positions/:pid      Bearbeiten
  DELETE /orders/:id/positions/:pid      Entfernen

  Time Entries:
  POST   /time-entries/clock-in          Einstempeln
  POST   /time-entries/clock-out         Ausstempeln
  GET    /time-entries?resource=X&date=Y Tagesuebersicht
  PATCH  /time-entries/:id               Korrektur durch SB

  Resources:
  GET    /resources                      Monteure + Buehnen
  GET    /resources/:id/schedule?date=Y  Tagesplan
  GET    /resources/capacity?from=&to=   Kapazitaetsansicht

  Planner:
  GET    /planner/day?date=Y             Tages-Timeline komplett
  PATCH  /planner/assign                 Drag&Drop: Position -> Ressource+Zeit
  GET    /planner/conflicts              Aktuelle Konflikte

  Parts Cart:
  GET    /orders/:id/parts               Warenkorb
  POST   /orders/:id/parts               Teil hinzufuegen
  PATCH  /orders/:id/parts/:pid          Menge/Status aendern
  DELETE /orders/:id/parts/:pid          Entfernen

  Check-in:
  POST   /orders/:id/checkin             Check-in (Signatur, Fotos, Typ)
  POST   /orders/:id/checkout            Check-out

/api/v1/master-data/ (-> Bridge oder eigene Stammdaten)
  GET    /customers/:id
  GET    /customers?search=
  GET    /vehicles/:id
  GET    /vehicles?vin=&plate=
```

### 6.2 WebSocket Channels

```
/ws
  planner:{tenant}:{location}     Planer-Updates (alle SB + Meister)
  cockpit:{tenant}:{location}     Cockpit Live-Feed
  mechanic:{resource_id}          Monteur-Terminal
```

### 6.3 Event-Flow Beispiele

**Serviceberater erstellt Auftrag:**
```
POST /orders -> DB Insert -> Event "order.created"
  -> WS Push: Planner (neuer Block), Cockpit (Zaehler +1)
```

**Drag&Drop im Planner:**
```
PATCH /planner/assign -> Konfliktpruefung -> DB Update -> Event "position.assigned"
  -> WS Push: alle Planner-Clients, Monteur-Terminal
  -> Bei Konflikt: 409 + Konflikt-Details
```

**Monteur stempelt ein:**
```
POST /time-entries/clock-in -> Auto-Clockout laufende -> DB Insert
  -> Events: "time.clocked_in", "order.status_changed"
  -> WS Push: Planner (blau), Cockpit (Feed + Status), Kapazitaet
```

---

## 7. UI-Konzepte

### 7.1 Werkstattplaner (Timeline-Ansicht, Hauptansicht)

Inspiration: awork.com Team-Planner, adaptiert fuer Werkstatt.

- Y-Achse: Monteure + Hebebuehnen als Zeilen
- X-Achse: Zeitachse (07:00-17:00, konfigurierbar)
- Bloecke: Arbeitspositionen mit Farbe nach Status
  - Grau = geplant, Blau = in Arbeit, Gruen = fertig, Rot = ueberzogen
- Drag&Drop: Bloecke auf andere Monteure/Zeiten ziehen
- Resize: Zeitblock verlaengern/verkuerzen
- Hover-Tooltip: Auftragsdetails, Kunde, Fahrzeug
- Konflikterkennung: Warnung bei Doppelbelegung
- Tagesnavigation: Vor/Zurueck, Datepicker, "Heute"

### 7.2 Kanban-Ansicht (Tagesuebersicht)

- Spalten: TERMINIERT -> ANGENOMMEN -> IN ARBEIT -> QS -> FERTIG
- Karten: Auftrag mit Fahrzeug, Arbeiten, Monteur, Fortschrittsbalken
- Drag zwischen Spalten = Status-Aenderung

### 7.3 Kapazitaetsansicht (Wochen/Monat)

- Matrix: Monteure x Tage
- Zellen: Auslastung in % mit Farbcodierung (gruen <70%, gelb 70-90%, rot >90%)
- Klick auf Zelle: springt zur Tages-Timeline

### 7.4 Monteur-Terminal

- Tablet-optimiert, grosse Touch-Targets
- Aktiver Auftrag prominent, Ein-/Ausstempel-Button
- Naechste Auftraege als Liste
- Tagesfortschritt (Ist-Stunden / Soll-Stunden)
- Optional: Barcode/QR-Scan auf Auftragskarte

### 7.5 Serviceberater-Cockpit

- Echtzeit-Dashboard, kein manueller Refresh
- Oben: Tages-KPIs (Auftraege, Fortschritt, Alerts)
- Mitte links: Warnungen (Zeitueberschreitung, fehlende Teile)
- Mitte rechts: Live-Feed (Stempelungen, Status-Aenderungen)
- Unten: Auftragstabelle mit Filter/Sortierung
- Quick-Actions: Neuer Auftrag, zum Planner, Kapazitaet

### 7.6 Check-in UI

- SB-Modus: Tablet-App mit Kamera fuer Fotos, Canvas fuer Unterschrift
- Self-Service: Tjekvik-Integration per API (Phase 1), eigenes Terminal spaeter

---

## 8. Auth & Multi-Tenancy

### 8.1 Auth Dual-Mode

```
Phase 1 (Greiner): LDAP/Active Directory
  Gateway -> LDAP-Verify -> JWT mit Tenant + Rollen

Phase 2 (SaaS): Local Auth + optional LDAP
  Tenant-Admin kann LDAP konfigurieren oder lokale User verwalten
```

### 8.2 JWT Payload

```json
{
  "sub": "mueller",
  "tenant": "greiner",
  "location": "deggendorf-opel",
  "roles": ["mechanic"],
  "permissions": ["workshop.view", "workshop.clock"]
}
```

### 8.3 Rollen

| Rolle | Rechte |
|-------|--------|
| mechanic | Ein-/Ausstempeln, eigene Auftraege sehen, Nacharbeit melden |
| service_advisor | Auftraege CRUD, Planner, Zeiten korrigieren, Check-in/out |
| workshop_lead | Alles + Kapazitaetsplanung, Disposition, Reports |
| location_admin | Alles + Ressourcen verwalten, Standort-Konfiguration |
| tenant_admin | Alles + User-Verwaltung, LDAP-Config, Billing (SaaS) |

### 8.4 Multi-Tenancy: Schema-per-Tenant

- Jeder Tenant bekommt ein eigenes PostgreSQL-Schema (z.B. `greiner.*`, `autohaus_maier.*`)
- Shared Schema fuer Tenant-Registry und globale Config
- Connection-Logik: `get_tenant_connection(tenant_id)` setzt `search_path`
- Migrationspfad zu DB-per-Tenant spaeter moeglich (kein Code-Umbau, nur Ops)
- Kein Cross-Schema-JOIN im Code

---

## 9. Hosting & Deployment

### 9.1 Infrastruktur

| Umgebung | Hoster | Zweck |
|----------|--------|-------|
| Entwicklung | Hetzner Cloud (CX32, ~15 EUR/Monat) | Docker-Dev-Stack, CI/CD Target |
| Staging | Hetzner oder Bayernwasser | Pre-Production Testing |
| Produktion | Bayernwasser | Greiner = erster Tenant |
| SaaS-Kunden | Bayernwasser oder Cloud | Je nach Kundenwunsch |

### 9.2 CI/CD Pipeline

```
GitHub Push -> GitHub Actions:
  1. Lint + Tests (Pytest, ESLint, Playwright)
  2. Docker Build (Multi-Stage)
  3. Push Images -> Container Registry
  4. Deploy Dev: Hetzner (automatisch bei develop)
  5. Deploy Prod: Bayernwasser (manuell bei main)
```

### 9.3 Tjekvik-Strategie

```
Phase 1: API-Anbindung an Tjekvik-Kiosk
  - DMS sendet Termine an Tjekvik
  - Tjekvik meldet Check-in zurueck -> Status-Update
  - Standard-DMS-Integration

Phase 2 (optional, spaeter): Eigenes Self-Service-Terminal
  - Alternative zu Tjekvik fuer SaaS-Kunden
  - Keine Tjekvik-Lizenzkosten
```

---

## 10. Entwicklungsphasen

### Phase 0: Fundament (2-3 Wochen)

- Repo aufsetzen (drive-dms)
- Docker Compose: PostgreSQL, Redis, Traefik
- Gateway-Service: Auth (JWT + LDAP), Tenant-Routing
- Workshop-Service: Grundgeruest, DB-Migrations
- Frontend: Next.js Skeleton, Auth-Flow, Layout
- CI/CD Pipeline: GitHub -> Hetzner Dev-Server
- **Ergebnis:** Login funktioniert, leere Shell steht

### Phase 1: Auftragsmanagement (3-4 Wochen)

- Datenmodell: Orders, Positions, Resources
- CRUD API: Auftraege anlegen/bearbeiten/Status
- Termin -> Vorab-Auftrag Workflow
- Auftrags-Liste + Detail-Ansicht (React)
- Kanban-Board (Status-Workflow)
- Bridge-Service: Kunden + Fahrzeuge aus DRIVE-PG
- **Ergebnis:** SB kann Auftraege komplett verwalten

### Phase 2: Werkstattplaner (3-4 Wochen)

- Timeline-Komponente (dnd-kit + Custom)
- Ressourcen-Verwaltung (Monteure, Buehnen)
- Drag&Drop Zuweisung + Konfliktpruefung
- Kapazitaetsansicht (Wochen/Monat)
- WebSocket: Live-Updates
- **Ergebnis:** Werkstattmeister kann Tage disponieren

### Phase 3: Stempelzeiten + Cockpit (2-3 Wochen)

- Monteur-Terminal UI (Tablet-optimiert)
- Clock-in/Clock-out API + Logik
- Serviceberater-Cockpit (Echtzeit-Dashboard)
- Alerts (Zeitueberschreitung, fehlende Teile)
- Live-Feed via WebSocket
- **Ergebnis:** Werkstatt laeuft digital, alles live

### Phase 4: Check-in/Check-out + Teile (3-4 Wochen)

- SB Check-in: Fotos, digitale Unterschrift
- Teile-Warenkorb pro Auftrag
- Teile-Verfuegbarkeit (aus Bridge/DRIVE)
- Nacharbeit/Upselling-Flow (Monteur -> SB -> Kunde)
- Tjekvik API-Anbindung (Check-in/Check-out)
- PDF: Auftragsbestaetigung, Rechnung
- **Ergebnis:** Kompletter Workflow von Termin bis Abholung

### Phase 5: Polish + Go-Live Greiner (2-3 Wochen)

- Multi-Standort (DEG Opel, DEG Hyundai, Landau)
- Reporting (Auslastung, Durchlaufzeiten, Produktivitaet)
- Berechtigungs-Feintuning
- Daten-Migration aus GUDAT/Locosoft
- Schulung, Bugfixes, Feinschliff
- **Ergebnis:** Greiner Werkstatt laeuft auf drive-dms

**Gesamtdauer Phase 0-5: ca. 13-17 Wochen**

### Danach (SaaS-Ausbau)

- Phase 6: Tenant-Management + Onboarding-Flow
- Phase 7: Eigene Stammdaten (kein Bridge mehr noetig)
- Phase 8: Weitere Module (Verkauf, Controlling, FiBu...)
- Phase 9: Self-Service-Terminal (Tjekvik-Alternative)

---

## 11. Beziehung zu DRIVE (bestehendes Portal)

DRIVE (/opt/greiner-test/) wird parallel weiterentwickelt. Es gibt keinen Big-Bang-Umstieg:

- **DRIVE bleibt fuer:** Verkauf, Controlling, Bankenspiegel, Urlaubsplaner, HR, Marketing, Teile-Lager
- **drive-dms uebernimmt:** Werkstatt-Auftraege, Werkstattplaner, Stempelzeiten, Serviceberater-Cockpit
- **Bridge:** Kunden- und Fahrzeug-Stammdaten fliessen von DRIVE -> drive-dms
- **Locosoft:** Bleibt fuer FiBu, Stammdaten-Sync via bestehende DRIVE-Scripts
- **GUDAT:** Wird durch den neuen Werkstattplaner ersetzt
- **Locosoft SOAP (Werkstatt):** Wird durch das neue Werkstatt-DMS ersetzt
