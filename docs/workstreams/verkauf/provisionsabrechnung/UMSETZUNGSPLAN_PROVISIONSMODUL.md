# Umsetzungsplan – Provisionsmodul DRIVE

**Grundlage:** `PROVISIONSMODUL_KONZEPT.md` (Claude/Florian, 2026-02-18)  
**Stand:** 2026-02-18

Dieser Plan zerlegt das Konzept in konkrete Aufgaben, angepasst an die DRIVE-Architektur (PostgreSQL, bestehende `sales`-Tabelle, Auth-System).

---

## Anpassungen zum Konzept

| Konzept | DRIVE-Realität |
|---------|-----------------|
| SQLite | **PostgreSQL** (drive_portal auf 127.0.0.1). DDL: `SERIAL` statt `AUTOINCREMENT`, `BOOLEAN`, `TIMESTAMP`, `TEXT`. |
| „SQLite (lokal), PostgreSQL (Locosoft extern)“ | **PostgreSQL** ist Haupt-DB; `sales` liegt in drive_portal (Sync aus Locosoft via `scripts/sync/sync_sales.py`). |
| `verkaufer_id` (Text) | Verkäufer = **VKB-Code** (integer, z. B. 2007) wie in `sales.salesman_number`; Anzeigename über `employees` (locosoft_id ↔ VKB). |
| Auth „@require_auth“ | Nutzen: `@login_required` + `@role_required(['admin', 'geschaeftsfuehrung'])` oder Feature-Permission `can_access_feature('provision')` (falls Feature in DB-Navigation/Rollen hinterlegt). |

---

## Phase 1: Fundament (Berechnung + Live-Preview)

**Ziel:** Verkäufer sieht Live-Berechnung seines Monats; keine DB-Läufe, nur Echtzeit aus `sales`.

### 1.1 Datenbank-Schema (PostgreSQL)

- **Datei:** `scripts/migrations/provision_schema_postgres.sql` (neu)
- **Inhalt:** CREATE TABLE für:
  - `provision_config` (SERIAL, BOOLEAN, DATE, TIMESTAMP; UNIQUE(kategorie, gueltig_ab))
  - `provision_laeufe` (SERIAL, status, Beträge, Timestamps, pdf_vorlauf/pdf_endlauf TEXT)
  - `provision_positionen` (SERIAL, lauf_id INTEGER REFERENCES provision_laeufe(id), einspruch_flag BOOLEAN DEFAULT false, …)
  - `provision_zusatzleistungen` (SERIAL, lauf_id INTEGER REFERENCES …)
  - `provision_audit_log` (SERIAL, lauf_id/position_id/zusatzleistung_id INTEGER)
- **Default-Daten:** INSERT für provision_config (Kat. I–V wie im Konzept); J60/J61 für Kat. IV vorerst NULL.
- **Ausführung:** Manuell oder Migrations-Script; danach in `docs/DB_SCHEMA_POSTGRESQL.md` ergänzen.

### 1.2 Berechnungslogik (SSOT)

- **Datei:** `api/provision_service.py` (neu) oder `api/provision_data.py` (Namenskonvention wie verkauf_data)
- **Funktionen (aus Konzept Kap. 3):**
  - `calc_neuwagen(db_betrag, stueck_gesamt_monat)` → 12 % DB + min(stueck, 15)*50
  - `calc_testwagen(rg_netto)` / `calc_vfw(rg_netto)` → 1 %, clamp 103–500 (oder 300 für VFW, konfigurierbar)
  - `calc_gebrauchtwagen(rg_netto)` → 1 %, clamp 103–500
  - `calc_gw_bestand(db_betrag, j60, j61)` → (DB - (DB*j60+j61)) * 0.12
- **Konfiguration:** Beim Aufruf aus `provision_config` lesen (für Monat gueltig_ab <= monat, gueltig_bis IS NULL oder >= monat).
- **Zuordnung out_sale_type → Kategorie:** F→I, L/T/V→II, B→III; IV nur wenn Kennung „GW aus Bestand“ (offen, siehe Konzept §11). V vorerst nur manuell.

### 1.3 Rohdaten für einen Monat

- **Quelle:** Tabelle `sales` (PostgreSQL drive_portal). Filter: `out_invoice_date` im Monat, `salesman_number` = VKB.
- **Optional:** Wie L744PR-Filter (VKB 1003–9001, Verkaufsart B–U) aus `L744PR_ABFRAGE_ABGLEICH.md` – ggf. in Service übernehmen.
- **Funktion:** z. B. `get_sales_for_provision(vkb: int, monat: str) -> list[dict]` (vin, out_invoice_number, out_sale_type, model_description, netto_vk_preis, deckungsbeitrag, …).

### 1.4 API: Live-Preview

- **Datei:** `api/provision_api.py` (neu)
- **Endpoint:** `GET /api/provision/live-preview?verkaufer_id=<vkb>&monat=YYYY-MM`
- **Auth:** Verkäufer nur eigene VKB (current_user → employees.locosoft_id = salesman_number); VKL/Admin alle.
- **Logik:** Kein DB-Write; aus `sales` lesen → pro Zeile Kategorie + Berechnung → Summen pro Kat. I–V zurückgeben (JSON).
- **Response:** Struktur wie im Konzept (Summen pro Kategorie, Liste Positionen optional).

### 1.5 Route + View „Meine Provision“

- **Datei:** `routes/provision_routes.py` (neu)
- **Route:** `GET /provision/meine` (oder `/verkauf/provision/meine` je nach Menü)
- **Template:** `templates/provision/provision_meine.html` (oder `templates/verkauf/provision_meine.html`)
- **Inhalt:** Monatsauswahl (aktueller Monat Default), Aufruf `/api/provision/live-preview`, Anzeige Tabelle pro Kategorie + Summen (wie Konzept §7.2).
- **Auth:** `@login_required`; Zugriff nur eigene Daten, sofern nicht VKL/Admin.

### 1.6 Anbindung in app.py

- **Blueprint:** `provision_bp` registrieren; URL-Prefix z. B. `/provision`.
- **Navigation:** Link „Meine Provision“ für Verkäufer (Feature `provision` oder Rolle); Dashboard-Link für VKL/Admin später Phase 2.

---

## Phase 2: Vorlauf / Endlauf / PDF

**Ziel:** VKL kann Vorlauf erstellen → Positionen in DB, PDF; Verkäufer kann Einspruch; VKL gibt Endlauf frei.

### 2.1 Vorlauf erstellen

- **Endpoint:** `POST /api/provision/vorlauf-erstellen` Body: `{ "verkaufer_id": 2007, "monat": "2026-01" }`
- **Logik (provision_service):**
  - Prüfen: Kein Lauf für (verkaufer_id, monat) mit Status != ENTWURF (oder kein Lauf vorhanden).
  - Aus `sales` Positionen holen (wie Live-Preview).
  - `provision_laeufe` anlegen (status = 'VORLAUF'), `provision_positionen` für jede Zeile.
  - Summen in provision_laeufe schreiben.
  - PDF generieren (siehe 2.4), Pfad in provision_laeufe speichern.
- **Response:** lauf_id, Link zum Detail.

### 2.2 Einspruch

- **Endpoints:**  
  - `POST /api/provision/einspruch/{position_id}` Body: `{ "text": "..." }` (nur betroffener Verkäufer)  
  - `POST /api/provision/einspruch-bearbeiten/{position_id}` Body: `{ "antwort", "aktion": "akzeptiert"|"abgelehnt", "korrektur_betrag?" }` (VKL/Admin)
- **DB:** provision_positionen: einspruch_flag, einspruch_text, einspruch_am; Bearbeitung: einspruch_bearbeitet, einspruch_antwort, einspruch_bearbeitet_von/am; ggf. provision_final anpassen bei Akzeptanz.

### 2.3 Endlauf freigeben

- **Endpoint:** `POST /api/provision/endlauf-freigeben/{lauf_id}`
- **Bedingung:** Alle Positionen mit einspruch_flag = true haben einspruch_bearbeitet = true.
- **Logik:** Status = 'ENDLAUF'; finales PDF generieren; pdf_endlauf speichern; Status „LOHNBUCHHALTUNG“ optional sofort oder per separatem Schritt.

### 2.4 PDF-Generierung

- **Bibliothek:** reportlab (bereits im Einsatz) oder weasyprint.
- **Datei:** `api/provision_pdf.py` oder in `provision_service`: Funktion `generate_provision_pdf(lauf_id, typ='vorlauf'|'endlauf')`.
- **Layout:** Wie Konzept §8 (Kopf, Blöcke I–V, Summen, Unterschriftenzeile).
- **Speicherort:** z. B. `data/provision_pdf/<jahr>/<monat>/` oder konfigurierbar; Pfad in provision_laeufe.

### 2.5 VKL-Dashboard

- **Route:** `GET /provision/dashboard`
- **Template:** `provision_dashboard.html`
- **API:** `GET /api/provision/dashboard?monat=YYYY-MM` → Liste Verkäufer mit Status, Summen, offene Einsprüche (aus provision_laeufe + positionen).
- **Aktionen:** Buttons „Vorlauf erstellen“, „Detail“, „Endlauf freigeben“ je nach Status.

### 2.6 Detail-View eines Laufs

- **Route:** `GET /provision/detail/<lauf_id>`
- **Template:** `provision_detail.html`
- **Inhalt:** Alle Positionen, Einsprüche bearbeiten, PDF-Download.

---

## Phase 3: Zusatzleistungen (Kat. V) + Lohnbuchhaltung

### 3.1 CRUD Zusatzleistungen

- **Endpoints:** GET/POST /api/provision/zusatzleistungen; PUT/DELETE /api/provision/zusatzleistung/<id>
- **Berechtigung:** Erfassen/Bearbeiten nur admin, finance, sales_manager (role_required).
- **Logik:** provision_verkaufer = betrag_gesamt × (anteil_prozent aus provision_config für typ) / 100; abrechnungsmonat, lauf_id bei Vorlauf setzen.

### 3.2 UI Zusatzleistungen erfassen

- **Route:** `GET /provision/zusatzleistungen`
- **Template:** Formular VIN (Autocomplete), Verkäufer, Typ, Betrag, Beleg-Datum/Referenz, Monat; Tabelle mit Filter.

### 3.3 Lohnbuchhaltung-Export

- **Endpoint:** `GET /api/provision/lohnbuchhaltung?monat=YYYY-MM` → Sammel-PDF + CSV (nur Endläufe).
- **Route:** `GET /provision/lohnbuchhaltung` mit Monatsauswahl und Buttons „Sammel-PDF“, „CSV“.

### 3.4 Jahresübersicht

- **Endpoint:** `GET /api/provision/jahresuebersicht?verkaufer_id=&jahr=` (Konzept §6.4).
- **Anzeige:** In „Meine Provision“ Tab/Accordion vergangene Monate + kumulierte Summen.

---

## Phase 4: Konfiguration + VKL-Provision (Anton Süß)

### 4.1 Config-UI (Admin)

- **Route:** `GET/PUT /provision/config` (Konzept §6.4, §7.5).
- **Änderungen:** Neuer Eintrag mit gueltig_ab; alter Eintrag gueltig_bis setzen (kein Überschreiben).

### 4.2 VKL-Provision (getrennt)

- Eigenes Modell/Config für Anton Süß; separate Logik; keine Mischung mit Verkäufer-Provision (Konzept §10 Phase 4, §12).

---

## Abhängigkeiten & Reihenfolge

```
1.1 Schema → 1.2 Service (liest Config) → 1.3 Rohdaten-Funktion → 1.4 API Live-Preview → 1.5 View + 1.6 app.py
2.1 Vorlauf (nutzt 1.2, 1.3) → 2.4 PDF → 2.2 Einspruch → 2.3 Endlauf → 2.5 Dashboard → 2.6 Detail
3.1 Zusatzleistungen API → 3.2 UI → 3.3 Lohnbuchhaltung → 3.4 Jahresübersicht
4.1 Config → 4.2 VKL (optional, später)
```

---

## Offene Punkte (vor/während Implementierung)

Aus Konzept §11 – kurze Zuordnung zu den Phasen:

| # | Thema | Blockiert / Betrifft |
|---|--------|----------------------|
| 1 | J60/J61 (GW Bestand) | Phase 1.2 / 2.1 – Kat. IV; Default NULL, später befüllbar |
| 2 | GW vs. GW Bestand (Locosoft-Feld) | Phase 1.2 – Zuordnung IV; ohne Klärung IV = 0 |
| 3 | Max VFW 205/300/500 | Phase 1.2 – Config max_betrag für II |
| 4 | Rg-Typ H/Z, Storno | Phase 1.3 – Filter in sales-Abfrage |
| 5 | Anteilssätze Kat. V | Phase 3.1 – Default aus Konzept |
| 6 | Geschäftsjahr Sep–Aug | Phase 3.4 – Jahresübersicht |
| 7 | n_nichtimportieren | Phase 1.3 – Schwellwert in Abfrage |
| 8 | VKB-Mapping | Phase 1.4 – employees.locosoft_id ↔ salesman_number |

---

## Projektstruktur (Ziel)

```
api/
  provision_api.py      # REST-Endpoints
  provision_service.py  # Berechnung, Vorlauf/Endlauf, Config-Lesen
  provision_pdf.py      # PDF-Generierung (optional eigenes Modul)
routes/
  provision_routes.py   # HTML-Views
templates/
  provision/
    provision_dashboard.html
    provision_meine.html
    provision_detail.html
    provision_zusatzleistungen.html
    provision_config.html
    provision_lohnbuchhaltung.html
static/
  css/provision.css
  js/provision.js
scripts/
  migrations/
    provision_schema_postgres.sql
docs/workstreams/verkauf/provisionsabrechnung/
  PROVISIONSMODUL_KONZEPT.md
  UMSETZUNGSPLAN_PROVISIONSMODUL.md  # dieses Dokument
  PROVISIONSREGELN_SYSTEM.md
```

---

## Nächster Schritt (Empfehlung)

Mit **Phase 1** starten: Schema anlegen, Berechnungslogik aus bestehendem Script `provisions_berechnung_kraus_jan2026.py` in `provision_service` überführen, Live-Preview-API + View „Meine Provision“. Damit ist die Basis standfest; Vorlauf/PDF und Einspruch bauen darauf auf.
