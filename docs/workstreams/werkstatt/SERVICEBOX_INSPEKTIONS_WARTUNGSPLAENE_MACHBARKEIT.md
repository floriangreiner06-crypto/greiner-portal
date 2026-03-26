# ServiceBox: Inspektions- und Wartungspläne scrapen und in der DB nutzbar machen

**Workstream:** Werkstatt  
**Datum:** 2026-03-10  
**Ausgangslage:** ServiceBox (Stellantis) ist für Mitarbeiter langsam und komplex. Ziel: Inspektions- und Wartungspläne regelmäßig scrapen und im DRIVE-Portal anwendbar machen.

---

## Kurzantwort: Ja, machbar – mit klaren Grenzen

- **Technisch:** Es gibt bereits funktionsfähige Wartungsplan-Scraper (Selenium, VIN-basiert). Sie schreiben derzeit nur in JSON/Logs, nicht in die DB.
- **„Alle“ Pläne:** ServiceBox bietet **keine** zentrale Übersicht „alle Inspektionspläne pro Modell“. Die Pläne sind **pro VIN** abrufbar (Alter/km für Anzeige nötig). „Alle“ bedeutet daher: für eine definierte Menge VINs scrapen (z. B. aus Locosoft).
- **Skalierung:** Vollscrape aller ~58k Locosoft-Fahrzeuge ist unrealistisch (Rate-Limits, Laufzeit). Sinnvoll: **priorisierte Teilmenge** (z. B. aktive Aufträge, nächste Inspektion fällig, On-Demand pro Auftrag).

---

## Ist-Stand im Projekt

### Bereits vorhanden

| Komponente | Beschreibung |
|------------|--------------|
| **Wartungsplan-Scraper** | `tools/scrapers/servicebox_wartungsplan_scraper.py` – Login, Tech-Doc, VIN-Suche, typdoc.do?doc=16 (Wartungspläne), Formular (Alter/km), PE-Dokument, Extraktion (Intervalle km/Jahre, Arbeiten, Tabellen). Nutzt Locosoft für EZ/km falls nicht übergeben. |
| **Varianten** | `servicebox_wartungsplan_complete.py`, `servicebox_wartungsplan_pdf.py`, `servicebox_wartungsplan_explorer.py`, `servicebox_optimized_scraper.py` – Erkundung/Alternativextraktion. |
| **Output** | JSON in `logs/servicebox_wartungsplaene/wartungsplan_{VIN}.json` – **keine** DB-Anbindung. |
| **ServiceBox-Bestellungen** | Bereits im Einsatz: `servicebox_api_scraper.py` (3× täglich), Matcher, Import → `stellantis_bestellungen`, `stellantis_positionen`, `teile_lieferscheine`. |

### In ServiceBox (Stellantis)

- **Wartungspläne:** `typdoc.do?doc=16` → Formular (VIN-Kontext, Alter, km) → PE-Dokument (Plan d’Entretien). Daten VIN-spezifisch.
- **Kein sichtbarer Katalog** „Modell/Motor → alle Intervalle“ ohne VIN; Explorer-Skripte haben keinen solchen Endpoint gefunden.

---

## Optionen für „regelmäßig scrapen und anwendbar machen“

### Option A: On-Demand pro VIN (geringster Aufwand)

- Beim Aufruf eines Auftrags / Werkstatt-Live / Arbeitskarte: VIN aus Locosoft → einmalig (oder gecacht) Wartungsplan-Scraper aufrufen → Ergebnis in DB speichern und in der UI anzeigen (z. B. „Nächste Inspektion laut ServiceBox: 90.000 km“, „Intervalle: …“).
- **Vorteil:** Nur bei Bedarf, keine Massenabfragen.  
- **Nachteil:** Erster Abruf pro VIN langsam (Selenium), Nutzer wartet oder bekommt „wird geladen“.

### Option B: Batch-Task mit priorisierten VINs (empfohlen für „regelmäßig“)

- **Celery-Task** (z. B. nachts oder 1× täglich):  
  - VIN-Liste aus Locosoft ermitteln, **priorisiert**, z. B.:  
    - Aufträge der letzten 7–30 Tage (VINs aus `orders`/`loco_orders`), oder  
    - Fahrzeuge mit „nächste Inspektion“ in den nächsten 90 Tagen (falls `next_general_inspection_date` / next_service_km in Locosoft gepflegt), oder  
    - Obergrenze z. B. 100–200 VINs/Tag.  
  - Pro VIN: vorhandenen Wartungsplan-Scraper aufrufen → Ergebnis in DB schreiben (upsert nach VIN).  
- **Vorteil:** Daten liegen vor, wenn der Mitarbeiter den Auftrag öffnet; Last verteilt.  
- **Nachteil:** Begrenzte Menge pro Lauf; ältere/ungenutzte VINs seltener oder nie aktualisiert.

### Option C: Vollscrape aller Stellantis-VINs

- Alle VINs aus Locosoft (Filter: Marke Opel/Stellantis) durchlaufen.  
- **Nachteil:** Bei zehntausenden Fahrzeugen inakzeptabel (Dauer, Rate-Limits, Last auf ServiceBox). Nur sinnvoll, wenn Stellantis eine **API oder Export** für Wartungspläne anbietet (derzeit nicht im Code/Explorer vorhanden).

---

## DB und Anwendung

### Neue Tabelle (Vorschlag)

In **PostgreSQL drive_portal**:

```sql
-- servicebox_wartungsplaene: ein Datensatz pro VIN, letzter Scrape-Stand
CREATE TABLE IF NOT EXISTS servicebox_wartungsplaene (
  id SERIAL PRIMARY KEY,
  vin VARCHAR(17) NOT NULL UNIQUE,
  -- Optional: Verknüpfung Locosoft
  vehicle_number_locosoft INTEGER,
  -- Extraktion aus Scraper (JSON flexibel für Intervalle, Arbeiten, Tabellen)
  intervalle_km INTEGER[],
  intervalle_monate INTEGER[],
  arbeiten TEXT[],
  raw_intervalle JSONB,
  raw_arbeiten JSONB,
  raw_tables JSONB,
  scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  success BOOLEAN NOT NULL DEFAULT true,
  error_message TEXT
);

CREATE INDEX idx_servicebox_wartungsplaene_vin ON servicebox_wartungsplaene(vin);
CREATE INDEX idx_servicebox_wartungsplaene_scraped_at ON servicebox_wartungsplaene(scraped_at);
```

- Ein **Import-Script** (analog zu ServiceBox-Bestellungen): liest Scraper-Output (JSON) und schreibt in `servicebox_wartungsplaene` (upsert nach `vin`).
- **API:** z. B. `GET /api/werkstatt/wartungsplan?vin=...` liefert den Eintrag für die VIN (für Werkstatt-Live, Arbeitskarte, Serviceberater).

### Wo im Portal nutzbar

- **Werkstatt-Live / Auftragsdetail:** Badge oder Bereich „ServiceBox Wartungsplan“ mit nächsten Intervallen / empfohlenen Arbeiten.
- **Arbeitskarte / Serviceberater:** gleiche Infos bei VIN-Kontext.
- Optional: Liste „Zuletzt aktualisierte Wartungspläne“ im Admin oder Werkstatt-Cockpit.

---

## Abgrenzung: Stellantis vs. Hyundai

- **ServiceBox** = Stellantis (Opel, Peugeot, Citroën, …).  
- **Hyundai** hat eigenes System (CCC/GWMS). Für „alle Inspektions-/Wartungspläne“ aller Marken bräuchte es einen **zusätzlichen** Katalog oder Scraper für Hyundai (und ggf. andere Marken), sofern gewünscht.

---

## Empfohlene nächste Schritte

1. **Fachlich klären:**  
   - Reicht „priorisierte VINs“ (Option B) oder soll On-Demand (Option A) im Vordergrund stehen?  
   - Welche konkreten Felder aus dem Wartungsplan sollen in der UI erscheinen (nur nächste Inspektion km/Jahr, oder auch Einzelarbeiten)?

2. **Technisch:**  
   - Migration für `servicebox_wartungsplaene` anlegen und ausführen.  
   - Import-Script: JSON-Output des bestehenden Wartungsplan-Scrapers → DB (upsert).  
   - Optional: Celery-Task für Batch (VIN-Liste aus Locosoft, Obergrenze, Priorisierung).  
   - API-Route + Einbindung in bestehende Werkstatt-Seiten (Werkstatt-Live, Arbeitskarte).

3. **Scraper anpassen:**  
   - Der bestehende Scraper kann unverändert JSON liefern; das Import-Script mappt auf die neue Tabelle. Falls nötig: kleine Anpassung, damit ein einheitliches JSON-Schema für DB-Import ausgegeben wird.

---

## Zusammenfassung

| Frage | Antwort |
|-------|---------|
| Können wir Inspektions-/Wartungspläne mit unseren Scrapern holen? | **Ja** – Wartungsplan-Scraper (VIN-basiert) existieren. |
| „Alle“ Pläne? | Nur über **alle relevanten VINs** (aus Locosoft); kein zentraler Katalog in ServiceBox. |
| Regelmäßig? | **Ja** – z. B. Celery-Batch mit priorisierten VINs (Aufträge der letzten Tage / nächste Inspektion fällig), Obergrenze pro Lauf. |
| In der DB anwendbar? | **Ja** – neue Tabelle `servicebox_wartungsplaene`, Import aus Scraper-JSON, API + Einbindung in Werkstatt-UI. |

Damit lässt sich die ServiceBox für Wartungs-/Inspektionspläne entlasten: Die Mitarbeiter sehen die Pläne direkt im DRIVE (Werkstatt-Live, Arbeitskarte), ohne in der ServiceBox zu suchen.
