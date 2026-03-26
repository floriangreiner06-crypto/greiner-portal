# eAutoSeller in DRIVE – Was ist umgesetzt, was fehlt?

Stand: 2026-03-19 (nach API-Verbesserung OpenAPI 2.0.40)

---

## Bereits für DRIVE umgesetzt

| Bereich | Status | Beschreibung |
|--------|--------|--------------|
| **API-Filter-Logik** | ✅ | `/dms/vehicles` nur mit `status=1` + offerReference/vin/changedSince; alle anderen Filter im Backend (marke, modell, preis, km, kraftstoff, getriebe, farbe, zustand, ez_von/ez_bis, min_kw/max_kw, standort, standzeit, sort). |
| **Feld-Mapping (Liste)** | ✅ | Client mappt priceGross, mileage, stockEntrance, transmissionType, fuel, exteriorColor, conditionType, pointOfSale etc.; Standzeit aus stockEntrance. |
| **Standzeit-Logik** | ✅ | < 30 = ok, 30–60 = warning, > 60 = critical; Badge-Texte („Neu im Bestand“, „X Tage – Jetzt anfragen!“). |
| **GET /api/eautoseller/vehicles** | ✅ | Backend-Filter, neues Response-Format (preis_formatiert, standzeit_badge, …), Statistics. |
| **GET /api/eautoseller/vehicles/filter-options** | ✅ | Liefert marken, kraftstoffe, farben, standorte, preis_min/max, km_max aus Bestand. |
| **GET /api/eautoseller/vehicle/<id>** | ✅ | Einzelfahrzeug inkl. Details (withAdditionalInformation, resolveEquipments); highlights/co2_wltp/verbrauch_wltp wenn vorhanden. |
| **POST/DELETE /api/eautoseller/vehicle/<id>/reserve** | ✅ | Reservierung setzen/löschen (Backend). |
| **Publications** | ✅ | get_publications_swagger(); Preis-Bewertung (priceRating 1–5) und mobile/AS24-Links in vehicles-Response. |
| **Pending** | ✅ | get_vehicles_pending_swagger() im Client (noch nicht in DRIVE-UI genutzt). |
| **Frontend Bestand** | ✅ | Filter an Backend übergeben; Preis-Badge-Spalte; Standzeit-Badge; Excel/PDF-Export. |

---

## Für DRIVE noch offen / fehlend

### 1. Caching (Plan §9) – **erledigt**

- **Umsetzung:** In-Memory-Cache in `api/eautoseller_api.py`: `vehicles_raw` 15 Min, `vehicle_detail:{id}` 30 Min, `publications` 60 Min, `filter_options` 15 Min. Bei API-Fehler wird Cache genutzt (falls vorhanden); Response enthält `from_cache` bzw. `is_mock` wenn zutreffend.

### 2. Filter-Options im Frontend nutzen – **erledigt**

- **Umsetzung:** Beim Seitenload wird `/api/eautoseller/vehicles/filter-options` aufgerufen; Dropdowns für Marke, Kraftstoff und Standort werden befüllt. „Filter anwenden“ übergibt die Werte ans Backend; clientseitige Filterung (applyFilters) nutzt dieselben Felder.

### 3. Zusätzliche Backend-Filter (Plan §1)

- **tueren:** Im Plan vorgesehen, im Backend noch nicht gefiltert (Feld `doors`/tueren kommt aus Details, nicht aus der Liste – ohne Detail-Abruf pro Fahrzeug nicht verfügbar).
- **unfallfrei:** Im Plan vorgesehen (`condition.hadAccident=false`); kommt nur aus Details. Ohne Detail-Abruf für alle Fahrzeuge nicht in der Liste filterbar. Optional: nur in **Detailansicht** anzeigen („Unfallfrei: ja/nein“).

### 4. Detailansicht im Frontend (Modal oder eigene Seite)

- **Fehlt:** Keine DRIVE-UI für Einzelfahrzeug-Details.
- **API:** GET `/api/eautoseller/vehicle/<id>` liefert Basis + ggf. highlights, co2_wltp, verbrauch_wltp.
- **Umsetzung:** In der Tabelle z.B. Link/Button „Details“ → Modal oder Seite `/verkauf/eautoseller-bestand/<id>`; Anzeige von Highlights, CO2/Verbrauch (EnVKV), 360°-Bilder, Ausstattung, Statistiken (Leads, Aufrufe), mobile/AS24-Link, „Unfallfrei“, Lieferzeit etc., sofern die API das in der Detail-Response liefert.

### 5. Detail-Response im Client erweitern

- **Fehlt:** `_convert_swagger_vehicle` und/oder die Detail-Route werten die **nested** Felder der eAutoseller-Detail-API oft noch nicht aus (z.B. `emissions.wltp.co2Combined`, `condition.hadAccident`, `images360`, `availability.deliveryDays`, Ausstattung).
- **Umsetzung:** Wenn die genaue JSON-Struktur der eAutoseller-Detail-Response bekannt ist, im Client oder in der API-Route diese Felder auslesen und ins DRIVE-Response-Format mappen (co2_wltp, verbrauch_wltp, hatte_unfall, bilder_360_aussen, lieferzeit_tage, ausstattung etc.).

### 6. Reservierung in der UI

- **Fehlt:** Kein „Reservieren“-Button und kein Formular (Name, Telefon, Dauer 1–7 Tage) in der Bestandsseite.
- **Umsetzung:** Pro Zeile (oder in der Detailansicht) Button „Reservieren“ → Modal mit Name, Telefon, Dauer → POST `/api/eautoseller/vehicle/<id>/reserve`; optional „Reservierung löschen“ → DELETE.

### 7. Sortierung im Frontend – **erledigt**

- **Umsetzung:** Sortier-Dropdown (Standzeit, Preis auf/ab, Km auf/ab) in der Filter-Leiste; Wert wird bei „Filter anwenden“/Refresh an die API übergeben (`sort`). Clientseitige Filterung (applyFilters) wendet die gewählte Sortierung auf die gefilterte Liste an.

### 8. Fehlerbehandlung / Mock-Flag (Plan §9) – **erledigt**

- **Umsetzung:** Response enthält `from_cache: true` bzw. `is_mock: true` wenn zutreffend. Frontend zeigt bei „Letzte Aktualisierung“ optional Badge „Cache“ oder „Demo-Daten“.

### 9. Pending-Fahrzeuge (unvollständige Daten)

- **Backend:** `get_vehicles_pending_swagger()` im Client vorhanden.
- **Fehlt:** Kein DRIVE-Endpoint und keine UI (z.B. Kachel „X Fahrzeuge mit unvollständigen Daten“ oder Liste).
- **Umsetzung:** Optional GET `/api/eautoseller/vehicles/pending` und auf der Bestandsseite einen Hinweis oder Tab „Unvollständig“.

---

## Priorisierung für DRIVE

| Priorität | Thema | Aufwand (grob) | Nutzen | Status |
|-----------|--------|-----------------|--------|--------|
| **Hoch** | Caching (API-Entlastung, Stabilität bei Ausfall) | Mittel | Weniger Last auf eAutoseller, bessere UX bei Fehlern. | ✅ umgesetzt |
| **Hoch** | Filter-Options in der UI (Dropdowns) | Gering | Bessere UX, weniger Tippfehler. | ✅ umgesetzt |
| **Mittel** | Sortierung im Frontend (Dropdown + API-Parameter) | Gering | Nutzer können Liste nach Preis/km/Standzeit sortieren. | ✅ umgesetzt |
| **Mittel** | Detailansicht (Modal/Seite + CO2/Verbrauch/Highlights) | Mittel | EnVKV, Transparenz, Links zu mobile/AS24. | offen |
| **Mittel** | Detail-Response-Mapping (emissions, condition, 360°, Ausstattung) | Mittel | Nur sinnvoll zusammen mit Detailansicht. | offen |
| **Niedrig** | Reservierungs-Button + Modal | Gering | Direkte Nutzung der Reserve-API. | offen |
| **Niedrig** | `is_mock` + einheitliche Fehler-/Cache-Strategie | Gering | Klarheit für Support und Debugging. | ✅ umgesetzt |
| **Optional** | Pending-Fahrzeuge (Endpoint + UI) | Gering | Nützlich für Händler-Admin. | offen |
| **Optional** | Filter „unfallfrei“ / „Türen“ | Nur mit Detail-Daten oder separatem Datenmodell sinnvoll. | offen |

---

## Kurzfassung

- **Bereits gut abgedeckt:** API-Korrektur (Filter, Felder, Standzeit), Backend-Filter, filter-options und vehicle-Detail-Endpoints, Reservierung (API), Publications/Preis-Bewertung, Frontend Filter + Preis-Badge.
- **Wichtigste Lücken für DRIVE:** Caching, Nutzung der Filter-Options in der UI, Sortier-UI, eine echte Detailansicht (Modal/Seite) inkl. CO2/Verbrauch und ggf. 360°/Reservierung, sowie vollständiges Mapping der eAutoseller-Detail-Response.

Wenn du willst, können wir als Nächstes z.B. **Caching** oder **Filter-Options + Sortierung im Frontend** konkret ausarbeiten (inkl. Code-Vorschläge).
