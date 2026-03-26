# Vorführwagen-Vermarktung (VFW) — Implementierungsplan

**Stand:** 2026-03-01  
**Workstream:** Verkauf  
**Zielgruppe:** Verkauf, Geschäftsleitung  
**Referenz:** Excel Kalkulation_V0.03.xlsm, Hersteller-Rundschreiben (Stellantis/Hyundai/Leapmotor)

---

## 1. Einordnung im aktuellen Entwicklungsstand

### 1.1 Korrekturen zum Claude-Entwurf

| Annahme im Entwurf | Aktueller Stand im Portal |
|--------------------|---------------------------|
| **fahrzeugfinanzierungen in SQLite** | **PostgreSQL** (drive_portal, seit TAG 135). Alle Zugriffe über `api.db_connection` / `api.db_utils`. |
| **VFW-Bestand „neu“** | **Bereits vorhanden:** `api/fahrzeug_data.py` → `get_vfw_bestand()` (Locosoft direkt, Filter `dealer_vehicle_type = 'D'`). Hinweis: In AfA/Provisionslogik gilt **V** = Vorführwagen, **D** = Demo; fachlich klären ob VFW-Bestand V+D oder nur eine Sorte umfassen soll. |
| **Locosoft „Sync-Script“ für Bestand** | VFW-Daten werden **direkt aus Locosoft** gelesen (kein lokaler Spiegel `vfw_bestand` nötig für Phase 1). Optional: Cache-Tabelle für Performance/Dashboard. |
| **loco_dealer_vehicles** | Tabelle in PostgreSQL dokumentiert, Nutzung im Code eher Locosoft-Direktzugriff (`api.db_utils.locosoft_session()`). |

### 1.2 Was bereits existiert und genutzt wird

- **VFW/Mietwagen AfA-Modul** (Controlling): `api/afa_api.py`, `api/afa_data.py`, Tabellen `afa_anlagevermoegen`, `afa_buchungen`. Klassifikation: **V** = VFW, **G + Jw-Kz M** = Mietwagen (Locosoft).
- **Fahrzeugfinanzierungen:** PostgreSQL-Tabelle `fahrzeugfinanzierungen` (VIN, Modell, Salden, Zinsfreiheit, Kennzeichen, etc.); Sync aus Stellantis ZIP, Santander CSV, Hyundai CSV; Anreicherung Modell/Kennzeichen aus Locosoft.
- **VFW-Bestand (FahrzeugData):** `FahrzeugData.get_vfw_bestand(standort)` — Locosoft `dealer_vehicles` mit `dealer_vehicle_type = 'D'`, `out_invoice_date IS NULL`.
- **Provisionslogik:** VFW/Testwagen Block II (1 % Rg.Netto, min 103 €, max 300 €); `out_sale_type` L → II_testwagen; Typen N/T/V/D/G aus Locosoft.
- **Verkauf:** `api/verkauf_api.py`, `api/verkauf_data.py`, `routes/verkauf_routes.py`, Templates `verkauf_*.html`; Filter-Modus (nur eigene / alle) über Feature/ Rolle.
- **Standort-Mapping:** 1 = DEG, 2 = HYU, 3 = LAN; `api/standort_utils.build_locosoft_filter_*`.

### 1.3 Begriffe und Typen (Locosoft)

- **V** = Vorführwagen (AfA, Bankenspiegel, Verkauf)
- **D** = Demo (teilweise synonym zu VFW; in `fahrzeug_data.get_vfw_bestand` aktuell nur **D**)
- **T** = Tageszulassung
- **Mietwagen** = `is_rental_or_school_vehicle = true` oder (G + pre_owned_car_code = 'M')

Das neue Modul soll **Vorführwagen, Tageszulassungen und Mietwagen** abdecken (Vermarktung + Kalkulation).

---

## 2. Phase 1: Datenbasis & VFW-Bestand

**Ziel:** Einheitliche Datenbasis für VFW/Tageszulassung/Mietwagen mit Standzeit, Marge, optional Finanzierungsdaten; einfaches Dashboard mit Ampelsystem.

### 2.1 DB-Schema

**Option A (empfohlen):** Keine neue Tabelle; View oder erweiterte API auf Locosoft + `fahrzeugfinanzierungen`.  
**Option B:** Cache-Tabelle `vfw_bestand_snapshot` für Dashboard/Performance (täglich oder bei Aufruf befüllt).

```sql
-- migrations/add_vfw_bestand_snapshot.sql (nur bei Option B)
CREATE TABLE IF NOT EXISTS vfw_bestand_snapshot (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    dealer_vehicle_type VARCHAR(1) NOT NULL,
    dealer_vehicle_number INTEGER NOT NULL,
    vin VARCHAR(17),
    license_plate VARCHAR(20),
    model_description TEXT,
    in_subsidiary INTEGER,
    in_arrival_date DATE,
    first_registration_date DATE,
    standzeit_tage INTEGER,
    mileage_km INTEGER,
    in_buy_list_price NUMERIC(12,2),
    out_recommended_retail_price NUMERIC(12,2),
    art VARCHAR(20),  -- 'VFW' | 'TAGESZULASSUNG' | 'MIETWAGEN'
    UNIQUE(snapshot_date, dealer_vehicle_type, dealer_vehicle_number)
);
CREATE INDEX idx_vfw_snapshot_date ON vfw_bestand_snapshot(snapshot_date);
CREATE INDEX idx_vfw_snapshot_vin ON vfw_bestand_snapshot(vin);
```

Verknüpfung zu Finanzierung: VIN-Match mit `fahrzeugfinanzierungen` (bereits vorhanden; VIN in Locosoft/Portal).

### 2.2 Locosoft-Identifikation VFW / Tageszul. / Mietwagen

- **VFW:** `dealer_vehicle_type = 'V'` UND (`is_rental_or_school_vehicle` IS NULL OR false) — wie in AfA.
- **Demo (D):** `dealer_vehicle_type = 'D'` (falls ihr D zusätzlich als VFW führt).
- **Tageszulassung:** `dealer_vehicle_type = 'T'`; ggf. Abgrenzung über Erstzulassung + Standzeit (z. B. ≤ 1 Jahr = Tageszul.).
- **Mietwagen:** wie AfA: `is_rental_or_school_vehicle = true` ODER (dealer_vehicle_type = 'G' AND pre_owned_car_code = 'M').

**Offen:** Einheitliche Definition „VFW-Bestand“ (nur V, oder V+D, oder inkl. T?) und ob Tageszulassungen im gleichen Dashboard geführt werden.

### 2.3 Sync-Script (optional)

- **Datei:** `scripts/sync/sync_vfw_bestand.py`  
- **Funktion:** Bei Option B: Locosoft abfragen (gleiche Logik wie AfA-Kandidaten + Typ T), in `vfw_bestand_snapshot` schreiben (snapshot_date = heute).  
- **Celery:** Optional Task `sync_vfw_bestand` (täglich), oder einmalig beim Aufruf des Dashboards.

### 2.4 Verknüpfung fahrzeugfinanzierungen

- **Bereits möglich:** JOIN/SELECT auf `fahrzeugfinanzierungen` per VIN (VIN in Locosoft `vehicles.vin`; in Portal ggf. gekürzt — siehe bankenspiegel_api: „VINs können gekürzt sein“).  
- **API:** Pro Fahrzeug optional `get_finanzierung_for_vin(vin)` oder in Bestandsliste erweiterte Felder (aktueller_saldo, zinsfreiheit_tage, finanzinstitut).

### 2.5 Konkrete Dateien Phase 1

| Art | Datei |
|-----|-------|
| Migration (nur Option B) | `migrations/add_vfw_bestand_snapshot.sql` |
| API (Datenlogik) | `api/vfw_api.py` oder Erweiterung `api/fahrzeug_data.py` (z. B. `get_vfw_vermarktung_bestand()`) |
| API (Flask-Endpoints) | in `api/vfw_api.py`: `GET /api/vfw/bestand`, `GET /api/vfw/bestand/<vin>/finanzierung` |
| Routes | `routes/verkauf_routes.py` oder `routes/vfw_routes.py`: z. B. `/verkauf/vfw` |
| Template | `templates/verkauf/vfw_dashboard.html` (oder `templates/vfw_dashboard.html`) |
| JS | `static/js/vfw_dashboard.js` (Tabelle, Filter Standort/Art, Ampeln Standzeit/Marge) |
| Sync (optional) | `scripts/sync/sync_vfw_bestand.py` + ggf. Celery-Task in `celery_app/tasks.py` |

### 2.6 Abhängigkeiten

- `api.db_utils.locosoft_session`, `get_db`/`db_session`
- `api/standort_utils` (Standortfilter)
- `api/bankenspiegel_api` oder direkte Abfrage `fahrzeugfinanzierungen` für Zinsdaten
- Auth: `@login_required`, `current_user.can_access_feature('vfw_vermarktung')` (neues Feature in Rechteverwaltung)

### 2.7 Offene Fragen Phase 1

1. VFW-Definition: nur **V**, oder **V + D**, oder inkl. **T** (Tageszulassung) im selben Bestand?
2. Soll ein **Snapshot** in PostgreSQL (Option B) oder ausschließlich **Live-Locosoft** (Option A) genutzt werden?
3. Ampelschwellen: Standzeit (z. B. grün &lt; 60, gelb 60–90, rot &gt; 90 Tage) und Marge — Werte aus Excel/BWL bestätigen.

---

## 3. Phase 2: Rundschreiben-Manager

**Ziel:** Hersteller-Verkaufsprogramme (Rundschreiben) und Konditionen verwalten, zeitlich begrenzt (quartalsweise Stellantis, monatlich Hyundai), mit Historisierung.

### 3.1 DB-Schema

```sql
-- migrations/add_vfw_verkaufsprogramme.sql
CREATE TABLE vfw_verkaufsprogramme (
    id SERIAL PRIMARY KEY,
    hersteller VARCHAR(50) NOT NULL,  -- 'Stellantis' | 'Hyundai' | 'Leapmotor'
    bezeichnung VARCHAR(255),
    von_datum DATE NOT NULL,
    bis_datum DATE NOT NULL,
    aktiv BOOLEAN DEFAULT true,
    notiz TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vfw_programm_konditionen (
    id SERIAL PRIMARY KEY,
    programm_id INTEGER NOT NULL REFERENCES vfw_verkaufsprogramme(id) ON DELETE CASCADE,
    aktionstyp VARCHAR(50) NOT NULL,  -- 'VFW gef.', 'VFW n. gef.', 'TW', 'Netprice', 'OR', ...
    modell_pattern VARCHAR(255),      -- optional: Modell/Reihe für Zuordnung
    vfw_bonus_pct NUMERIC(6,4),       -- % auf UPE
    kap_pct NUMERIC(6,4),
    reg_budget_pct NUMERIC(6,4),
    slot4_pct NUMERIC(6,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(programm_id, aktionstyp, COALESCE(modell_pattern, ''))
);

CREATE TABLE vfw_leistungsboni (
    id SERIAL PRIMARY KEY,
    programm_id INTEGER NOT NULL REFERENCES vfw_verkaufsprogramme(id) ON DELETE CASCADE,
    bonustyp VARCHAR(50) NOT NULL,     -- 'LBO' | 'CSI' | ...
    beschreibung TEXT,
    zielwert NUMERIC(12,4),
    bonus_pct NUMERIC(6,4),
    einheit VARCHAR(20),               -- 'pct' | 'abs'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vfw_prog_zeitraum ON vfw_verkaufsprogramme(von_datum, bis_datum);
CREATE INDEX idx_vfw_kond_programm ON vfw_programm_konditionen(programm_id);
```

### 3.2 Admin-UI

- **Route:** z. B. `/verkauf/vfw/programme` (Rolle: Verkaufsleitung/Admin).
- **Funktionen:** CRUD Verkaufsprogramme (von/bis, Hersteller, Bezeichnung); CRUD Konditionen (Aktionstyp, VFW%, KAP%, Reg.Budget%, Slot4); optional CRUD Leistungsboni (LBO/CSI).
- **Templates:** `templates/verkauf/vfw_programme_list.html`, `vfw_programme_edit.html` (oder ein Tab-basiertes Formular).

### 3.3 Konkrete Dateien Phase 2

| Art | Datei |
|-----|-------|
| Migration | `migrations/add_vfw_verkaufsprogramme.sql` |
| API | `api/vfw_api.py`: CRUD Programme, Konditionen, Boni; `get_aktive_programme(hersteller, stichtag)` |
| Routes | `routes/verkauf_routes.py` oder `vfw_routes.py`: `/verkauf/vfw/programme`, `/verkauf/vfw/programme/<id>` |
| Templates | `templates/verkauf/vfw_programme_*.html` |
| JS | `static/js/vfw_programme.js` (Datumsprüfung, Duplikat-Check) |

### 3.4 Abhängigkeiten

- Auth/Feature `vfw_vermarktung` oder `vfw_programme_admin`
- Keine Abhängigkeit von Phase 1 (kann parallel entwickelt werden)

### 3.5 Verkaufsprogramme aus PDF per KI aufbereiten

**Frage:** Wenn die Verkaufsprogramme als PDF vorliegen, können wir sie mit KI so in die DB bringen, dass die Logik (gültige Programme, Konditionen pro Aktion/Modell) erkennbar ist?

**Antwort:** Ja. Vorgehen: PDF → AWS Textract (Text + Tabellen) → AWS Bedrock (Struktur/Vorschlag) → Admin prüft und übernimmt → Speicherung in `vfw_verkaufsprogramme` / `vfw_programm_konditionen`. Details: **`Kalkulationstool/VERKAUFSPROGRAMME_PDF_KI_AUFBEREITUNG.md`**.

### 3.6 Offene Fragen Phase 2

1. Sollen **Leistungsboni** (LBO, CSI) schon in Phase 2 erfasst werden oder erst in Phase 3 (nur LBO/CSI-Logik in Kalkulation)?
2. **Aktionstypen** aus Excel (VFW gef., VFW n. gef., TW, Netprice, OR) — vollständige Liste und Hersteller-Mapping?

---

## 4. Phase 3: Kalkulationsengine

**Ziel:** Automatisches Matching Fahrzeug ↔ Programm; Kalkulation wie Excel inkl. LBO, CSI, Standkosten, Zinsen; UI mit Live-Berechnung; DB1-Ziel; PDF-Export.

### 4.1 Logik (Excel-äquivalent + Erweiterungen)

- **Eingaben:** Aktion, Modell, VIN, VH netto (EK), UPE netto, Überführung, Bonus-% (VFW, KAP, Reg.Budget, Slot4), Händlermarge %, Aktionspreis (brutto).
- **Berechnung:**
  - Zwischensumme = VH netto − (VFW%×UPE) − (KAP%×UPE) − (Reg.Budget%×UPE) − (Slot4%×UPE)
  - Summe vor St. = Zwischensumme + Marge%×UPE
  - Brutto intern = Summe vor St. × 1,19
  - Listenpreis: UPE netto → +19 % → + Überführung → Gesamtpreis
  - Ersparnis = Gesamtpreis − Aktionspreis (absolut + %)
- **Zusätzlich (Phase 3):**
  - **LBO:** aus Zielerreichung (z. B. aus Planung/Verkauf) → Prozentsatz anwenden.
  - **CSI:** aus aktuellen Scores (Quelle klären: Umfragen/CRM?) → Bonus anwenden.
  - **Standkosten:** kalkulatorisch (z. B. 150 €/Monat × Standzeit).
  - **Zinskosten:** aus `fahrzeugfinanzierungen` (aktueller_saldo, Zinsen, zinsfreiheit_tage).
  - **Aufbereitung/Zulassung:** Pauschalen oder aus Konfiguration.

### 4.2 Matching VFW ↔ Programm

- **Regel:** Hersteller (aus Modell/Marke), Modellreihe (optional), Datum im Gültigkeitszeitraum (`von_datum`–`bis_datum`).
- **API:** `find_programm_for_fahrzeug(vin, stichtag)` → bestes passendes Programm + Konditionen.

### 4.3 SSOT Kalkulation

- **Eine** zentrale Funktion z. B. in `api/vfw_kalkulation_service.py`: `berechne_vfw_kalkulation(eingaben, programm_konditionen, optionen)` → Dict mit allen Zwischenwerten, DB1, Preisvorschlag.  
- Nutzer: Portal-UI, PDF-Export, ggf. später E-Mail/Report.

### 4.4 DB (nur falls Speicherung gewünscht)

- **Option:** Tabelle `vfw_kalkulationen` (Projekt-ID, VIN, Benutzer, Zeitstempel, Eingabe-JSON, Ergebnis-JSON, PDF-Pfad).  
- Oder nur Live-Berechnung ohne Persistenz (wie Excel).

### 4.5 Konkrete Dateien Phase 3

| Art | Datei |
|-----|-------|
| Service (SSOT) | `api/vfw_kalkulation_service.py`: `berechne_vfw_kalkulation()`, `find_programm_for_fahrzeug()` |
| API | `api/vfw_api.py`: `POST /api/vfw/kalkulation`, `GET /api/vfw/programm-fuer-fahrzeug?vin=...` |
| Routes | `/verkauf/vfw/kalkulation` |
| Template | `templates/verkauf/vfw_kalkulation.html` (Eingaben + Live-Ergebnis) |
| JS | `static/js/vfw_kalkulation.js` (Eingaben, API-Call, Anzeige Ersparnis/DB1) |
| PDF | `api/vfw_pdf.py` (reportlab oder wie provision_pdf), Export mit VIN im Dateinamen |
| Migration (optional) | `migrations/add_vfw_kalkulationen.sql` |

### 4.6 Abhängigkeiten

- Phase 1 (Bestand/VIN), Phase 2 (Programme/Konditionen)
- `fahrzeugfinanzierungen` für Zinsen
- Zielerreichung für LBO: z. B. `api/verkaeufer_zielplanung_api` oder Planungs-KST — **offen:** wo liegt LBO-Zielerreichung?
- CSI: **offen** — Datenquelle (Umfrage-Tool, manuell?)

### 4.7 Offene Fragen Phase 3

1. **LBO-Zielerreichung:** Aus welchem Modul (Planung, Verkauf, Konzern)? Quartalsbezug?
2. **CSI-Daten:** Welche Quelle (NPS, Fachkompetenz, Kontakt, Google-Sterne) ist im Haus verfügbar?
3. **Standkosten:** Pauschale 150 €/Monat oder konfigurierbar pro Standort/Modell?
4. **PDF-Export:** Nur Netzwerkshare (wie Excel VBA) oder auch Download im Portal?

---

## 5. Phase 4: KI & Automatisierung (perspektivisch)

**Ziel:** Rundschreiben-PDF parsen (AWS Bedrock/Textract), Bonus-Tabellen vorschlagen; Alerts (Standzeit &gt; 90 Tage, Programm-Ende, Zinsfreiheit-Ende).

### 5.1 PDF-Parsing

- **Tool:** AWS Textract oder Bedrock (Document Understanding); bereits AWS eu-central-1 im Einsatz (Hilfe/Bedrock).
- **Flow:** Upload Rundschreiben-PDF → Extraktion Tabellen/Text → Vorschlag für `vfw_programm_konditionen` → Bestätigung durch User → Speichern.

### 5.2 Alerts

- **Standzeit &gt; 90 Tage:** aus VFW-Bestand (Phase 1); Celery-Task oder Dashboard-Hinweis.
- **Programm läuft aus:** Abfrage `vfw_verkaufsprogramme.bis_datum` nahe aktuelles Datum.
- **Zinsfreiheit endet:** aus `fahrzeugfinanzierungen.zinsfreiheit_tage` / Vertragsbeginn.

### 5.3 Konkrete Dateien Phase 4

| Art | Datei |
|-----|-------|
| API | Erweiterung `api/vfw_api.py`: `POST /api/vfw/parse-rundschreiben` (Upload, Aufruf Textract/Bedrock) |
| KI/Integration | `api/ai_api.py` oder eigenes Modul für Document-Understanding (Rundschreiben-Struktur) |
| Celery | `celery_app/tasks.py`: `vfw_alert_standzeit`, `vfw_alert_programm_ende`, `vfw_alert_zinsfreiheit` |
| Frontend | Optional: Alert-Badges im VFW-Dashboard, E-Mail-Benachrichtigung (wie BWA/Alarm) |

### 5.4 Offene Fragen Phase 4

1. **Rundschreiben-Format:** Stellantis/Hyundai/Leapmotor — einheitliche Struktur oder je Hersteller Parser?
2. **Alert-Empfänger:** E-Mail an Verkaufsleitung/Buchhaltung (wie bei anderen Alarmen)?

---

## 6. Übersicht: Dateien, Migrationen, Endpoints

### 6.1 Neue/geänderte Dateien (kumuliert)

| Phase | API | Routes | Templates | Static JS | Scripts | Migrationen |
|-------|-----|--------|-----------|-----------|---------|-------------|
| 1 | `vfw_api.py` (Bestand, Finanzierung) | verkauf_routes / vfw_routes | vfw_dashboard.html | vfw_dashboard.js | sync_vfw_bestand.py (opt.) | add_vfw_bestand_snapshot.sql (opt.) |
| 2 | + Programme/Konditionen CRUD | + /vfw/programme | vfw_programme_*.html | vfw_programme.js | — | add_vfw_verkaufsprogramme.sql |
| 3 | + vfw_kalkulation_service.py, vfw_api (Kalkulation), vfw_pdf.py | + /vfw/kalkulation | vfw_kalkulation.html | vfw_kalkulation.js | — | add_vfw_kalkulationen.sql (opt.) |
| 4 | + Parse-Rundschreiben, Alerts | + Alerts/Upload | (optional) | — | — | — |

### 6.2 API-Endpoints (Vorschlag)

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/api/vfw/bestand` | Bestand VFW/Tageszul./Mietwagen (Standort optional) |
| GET | `/api/vfw/bestand/<vin>/finanzierung` | Finanzierungsdaten aus fahrzeugfinanzierungen |
| GET | `/api/vfw/programme` | Liste aktiver/aller Verkaufsprogramme |
| GET | `/api/vfw/programme/<id>` | Programm inkl. Konditionen/Boni |
| POST | `/api/vfw/programme` | Programm anlegen |
| PUT | `/api/vfw/programme/<id>` | Programm aktualisieren |
| GET | `/api/vfw/programm-fuer-fahrzeug?vin=...` | Matching Programm für VIN/Stichtag |
| POST | `/api/vfw/kalkulation` | Kalkulation berechnen (Body: Eingaben) |
| GET | `/api/vfw/kalkulation/pdf?vin=...&...` | PDF-Export (oder POST mit Parametern) |
| POST | `/api/vfw/parse-rundschreiben` | (Phase 4) PDF hochladen, Vorschlag Konditionen |

### 6.3 Navigation & Rechte

- **Feature:** `vfw_vermarktung` (oder `vfw_kalkulation`) in Rechteverwaltung anlegen; Rolle: Verkauf, Geschäftsleitung, ggf. Admin für Programme.
- **Navi-Punkt:** Unter Verkauf (parent_id = Verkauf) z. B. „VFW-Vermarktung“ oder „Vorführwagen-Kalkulation“; Migration `migrations/add_navigation_vfw_vermarktung.sql`.

---

## 7. Nächste Schritte

1. **Fachlich klären:** VFW-Definition (V/D/T), Ampelschwellen, LBO/CSI-Quellen, Standkosten, Aktionstypen.
2. **Entscheidung:** Option A (nur Live-Locosoft) vs. Option B (Snapshot-Tabelle) für Phase 1.
3. **Reihenfolge:** Phase 1 (Dashboard) → Phase 2 (Programme) → Phase 3 (Kalkulation + PDF); Phase 4 nach Bedarf.
4. **Excel:** Kalkulation_V0.03.xlsm als Referenz behalten; Optionen-Blatt (Dropdown Aktionstyp, Modell) für Dropdown-Daten ggf. in DB übernehmen (Phase 2/3).

Nach Klärung der offenen Fragen kann mit Phase 1 (und ggf. Phase 2 parallel) begonnen werden.
