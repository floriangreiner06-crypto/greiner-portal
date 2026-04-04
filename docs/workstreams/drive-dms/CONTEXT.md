# Workstream: DRIVE-DMS (Neues Dealer Management System)

## Vision

DRIVE wird schrittweise zu einem vollwertigen DMS als SaaS-Produkt ausgebaut. Erster Baustein: Werkstatt-DMS mit Werkstattplaner, das GUDAT + Locosoft-SOAP im Werkstattbereich ersetzt.

## Strategie

1. **Phase: Greiner autark** - Werkstatt-DMS neben DRIVE, ersetzt GUDAT + Locosoft-SOAP
2. **Phase: SaaS** - Multi-Tenant fuer andere Autohaeuser

## Infrastruktur

| Komponente | Detail |
|---|---|
| **Repo** | `/opt/drive-dms/` auf Hetzner-Server 49.13.93.35 |
| **Tech-Stack** | FastAPI + Next.js 14 + React 18 + PostgreSQL 16 + Redis |
| **Frontend** | http://49.13.93.35:3000 |
| **Gateway API** | http://49.13.93.35:8000 |
| **Docker** | 5 Container (db, redis, gateway, workshop, frontend) |
| **Dev-Login** | `dev-admin` / beliebiges Passwort |
| **Tests** | 57 Backend-Tests (Pytest), TypeScript-Check |

## Aktueller Stand (2026-04-04)

### Phase 0 (Fundament) - FERTIG
- Docker Compose mit PostgreSQL, Redis, Gateway, Workshop, Frontend
- Gateway Service: JWT Auth + LDAP (Dual-Mode) + Tenant Middleware + Proxy
- Workshop Service: Resource CRUD, DB-Setup, Alembic Migrations
- Frontend: Next.js mit Login, Auth Store, Sidebar, Header
- CI/CD: GitHub Actions Workflow

### Phase 1 (Auftragsmanagement) - FERTIG
- WorkshopOrder + Position Models mit Status-Machine (8 Status)
- Orders + Positions CRUD API (57 Tests)
- Frontend: Auftragsliste, Auftragsdetail, Neuer Auftrag, Kanban-Board, Ressourcen
- GUDAT-Datenimport: 443 Tasks anonymisiert, 159 Orders + 10 Monteure importiert

### Phase 2 (Werkstattplaner) - IN ARBEIT
- Planner API: GET /planner/day + PATCH /planner/assign
- Timeline-Komponente mit Monteur-Zeilen, Zeitachse 07:00-17:00
- Unassigned Panel mit Zuweisungs-Funktion
- Datums-Navigation, Standort-Wahl

## Offene Aufgaben

### Phase 2 (noch offen)
- [ ] Stempelzeiten (Clock-in/Clock-out API + Monteur-Terminal UI)
- [ ] Serviceberater-Cockpit (Echtzeit-Dashboard)
- [ ] WebSocket fuer Live-Updates
- [ ] Kapazitaetsansicht (Wochen/Monat)

### Phase 3 (Check-in/Check-out + Teile)
- [ ] SB Check-in: Fotos, digitale Unterschrift
- [ ] Teile-Warenkorb pro Auftrag
- [ ] Nacharbeit/Upselling-Flow
- [ ] Tjekvik API-Anbindung

### Phase 4 (Go-Live Greiner)
- [ ] Multi-Standort (DEG Opel, DEG Hyundai, Landau)
- [ ] Reporting (Auslastung, Durchlaufzeiten)
- [ ] Daten-Migration aus GUDAT/Locosoft

## Wichtige Dateien

| Datei | Zweck |
|---|---|
| `docs/superpowers/specs/2026-04-04-drive-dms-werkstatt-design.md` | Design-Spec |
| `docs/superpowers/plans/2026-04-04-drive-dms-phase0-phase1.md` | Implementierungsplan Phase 0+1 |
| `/opt/drive-dms/` (Hetzner 49.13.93.35) | Das neue Repo |

## GUDAT-Vergleich

DRIVE-DMS ersetzt GUDAT mit: Monteur-Level-Planung (statt Team), vollem Auftrags-Lifecycle (8 statt 4 Status), integrierten Stempelzeiten, Teile-Warenkorb, Check-in/Check-out. GUDAT-DA-API Credentials (deggendorf/landau) geben 401 - muessen evtl. erneuert werden. KIC-Login (florian.greiner@auto-greiner.de) funktioniert.

## Naechste Session

Einstiegspunkt: Phase 2 fortsetzen - Stempelzeiten + Monteur-Terminal
- Backend: Time Entry Model + Clock-in/Clock-out API
- Frontend: Tablet-optimierte Monteur-Ansicht
- WebSocket fuer Live-Updates im Planner + Cockpit
