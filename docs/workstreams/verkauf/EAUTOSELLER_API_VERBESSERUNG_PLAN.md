# eAutoseller API Verbesserung – Plan (OpenAPI 2.0.40)

## Übersicht

Korrektur und Erweiterung der eAutoseller-Integration gemäß offizieller OpenAPI-Dokumentation.  
**Wichtigste Änderung:** Filter-Logik – die API `/dms/vehicles` unterstützt nur wenige Query-Parameter; alle weiteren Filter werden im Backend (Python) nach dem Abruf angewendet.

---

## 1. Filter-Logik (KORREKTUR)

### API-seitig erlaubt (nur diese!)

- `offerReference`, `vin`, `mobileAdId`, `as24AdId`, `changedSince`, **`status`** (1=Aktiv, 99=Gesperrt, 199=Archiviert)
- **Immer** `status=1` (Verkaufsbestand) abrufen.

### Backend-seitig (in Python nach Abruf)

Alle anderen Filter in `api/eautoseller_api.py` implementieren:

- `marke`, `modell`, `min_preis`, `max_preis`, `min_km`, `max_km`
- `kraftstoff` (gegen `fuel.wording`), `getriebe` (transmissionType.id: 0=Manuell, 1=Automatik, 2=Halbautomatik)
- `farbe` (exteriorColor.base), `zustand` (conditionType)
- `ez_von`, `ez_bis` (firstRegistrationDate Jahr)
- `min_kw`, `max_kw`, `tueren`, `unfallfrei` (condition.hadAccident=false, aus Details)
- `standort` (pointOfSale.name)
- `sort`: preis_asc|preis_desc|km_asc|standzeit_asc|neueste

---

## 2. Felder aus /dms/vehicles (Client-Mapping)

`lib/eautoseller_client.py` – Response pro Fahrzeug korrekt mappen:

- **Basis:** id, vin, offerReference  
- **Make/Model:** make (name), makeId, model (name), modelId, type, category  
- **Preis:** priceGross (Brutto), professionalPriceGross (Händlerpreis)  
- **Laufleistung:** mileage  
- **Datum:** firstRegistrationDate, **stockEntrance** (date-time → Standzeit = heute - stockEntrance.date())  
- **Getriebe:** transmissionType.id, transmissionType.wording  
- **Kraftstoff:** fuel.id, fuel.wording, fuel.e10, fuel.biodiesel, fuel.hasParticleFilter  
- **Leistung:** power (kW)  
- **Farbe:** exteriorColor.base, exteriorColor.wording, exteriorColor.isMetallic, exteriorColor.isMatte  
- **Zustand:** conditionType (NEW|DEMO|DAILY|USED|…)  
- **Status:** status.id, status.wording  
- **Standort:** pointOfSale.id, pointOfSale.name, pointOfSale.city  
- **Sonstiges:** licensePlate, lastChange, lastPriceChange, lastPictureChange, lastFileChange  

Standzeit: **nur** aus `stockEntrance` berechnen, kein separater Call.

---

## 3. Standzeit-Logik

- **Berechnung:** Standzeit (Tage) = heute - stockEntrance.date()
- **Status:**
  - &lt; 30 Tage → `status="ok"` → „Neu im Bestand“
  - 30–60 Tage → `status="warning"` → „{n} Tage im Bestand“
  - &gt; 60 Tage → `status="critical"` → „{n} Tage – Jetzt anfragen!“

---

## 4. Fahrzeugdetails /dms/vehicle/{id}/details

- Immer aufrufen mit: `?withAdditionalInformation=true&resolveEquipments=true`
- Zusätzliche Felder für Detail-Response: images360, highlights, modelSeries, trimLine, hsn/tsn, powerMax, productionYear, modelYear, doors, seats, gears, cylinders, displacement, weight, numberOfOwners, condition.* (valuation, hadAccident, isRoadworthy, …), previousUsageType, availability.*, emissions.wltp.*, emissions.emissionClass, emissions.emissionSticker, Ausstattung (resolveEquipments).

---

## 5. Publikationsstatistiken

- **Endpoint:** `GET /dms/publications/vehicles/publicated?statistics=true`
- Liefert pro Fahrzeug: mobilePublication (adId, link), autoscout24Publication (listingId, link), statistics (leadsTotal, leadsOpen, lastLeadDate, mobileStatistic: clicks, favorites, calls, emails, **priceRating** 1–5, priceRatingRanges), autoscout24Statistic.
- **priceRating** im Frontend als Badge: 1=„Sehr guter Preis“, 2=„Guter Preis“, 3=„Fairer Preis“, 4=„Erhöhter Preis“, 5=„Hoher Preis“.

---

## 6. Weitere Endpoints

- `GET /dms/vehicles/pending` – Fahrzeuge mit unvollständigen Daten (Dashboard)
- `POST /dms/vehicle/{id}/reservation` – Reservierung setzen  
- `DELETE /dms/vehicle/{id}/reservation` – Reservierung löschen  

(Reservierung optional: „Reservieren“-Button mit Name, Telefon, Dauer 1–7 Tage.)

---

## 7. Backend-API (Flask)

### GET /api/eautoseller/vehicles

- Aufruf eAutoseller **nur** mit `status=1` (ggf. offerReference/vin/changedSince wenn übergeben).
- **Alle** weiteren Filter (siehe Abschnitt 1) in Python anwenden.
- Response-Format wie unten (vehicles-Array, total, filter_angewendet, timestamp).

### GET /api/eautoseller/vehicles/filter-options

- Aus der (gecachten) Fahrzeugliste ableiten: marken, kraftstoffe, farben, preis_min/max, km_max, standorte.

### GET /api/eautoseller/vehicle/{id}

- Einzelfahrzeug inkl. Details (withAdditionalInformation, resolveEquipments) und optional Publikationsstatistiken.
- Response-Format wie unten (Vehicle-Detail).

### POST/DELETE /api/eautoseller/vehicle/{id}/reserve

- Reservierung setzen/löschen (optional).

---

## 8. Response-Formate

### Vehicles (Liste)

- Pro Fahrzeug: id, vin, offerReference, marke, modell, typ, kategorie, preis, preis_formatiert, haendlerpreis, km, km_formatiert, ez, ez_formatiert, ez_jahr, kraftstoff, kraftstoff_id, getriebe, getriebe_id, leistung_kw, leistung_ps, farbe_basis, farbe_wording, ist_metallic, zustand, zustand_wording, standzeit_tage, standzeit_status, standzeit_badge, lagereingang, standort, bilder, hauptbild, preis_bewertung, preis_bewertung_text, mobile_link, as24_link, status.
- Top-Level: vehicles, total, filter_angewendet, timestamp, ggf. is_mock.

### Vehicle-Detail

- Alle Listenfelder plus: highlights, modellreihe, ausstattungslinie, baujahr, tueren, sitze, vorbesitzer, hubraum, zylinder, getriebe_gaenge, gewicht_kg, zustand_bewertung, hatte_unfall, ist_fahrtuechtig, schadensinfo, lieferzeit_tage, verfuegbar_ab, co2_wltp, verbrauch_wltp, elektro_reichweite_km, euro_norm, feinstaubplakette, bilder_360_aussen, bild_360_innen, ausstattung (gruppiert), statistiken (Leads, Aufrufe, Vormerkungen, etc.).

---

## 9. Caching

- vehicles_list: 15 Min (pro dealer/context)
- vehicle_detail: 30 Min (pro vehicle_id)
- publications: 60 Min
- filter_options: 15 Min (aus vehicles_list abgeleitet)
- Cache-Key-Schema: z. B. `eautoseller:{endpoint}:{params_hash}`

Bei API-Fehler/Timeout: aus Cache liefern falls vorhanden, sonst Mock mit `is_mock=true` und Fehler loggen (nicht an Frontend durchreichen).

---

## 10. DSGVO / EnVKV

- CO2 (wltp.co2Combined) und Verbrauch (wltp.consumptionCombined) in Detailansicht anzeigen, wenn vorhanden (EnVKV-Pflicht bei Neufahrzeugen).

---

## 11. Zu ändernde Dateien (Projekt Greiner Portal)

| Datei | Änderungen |
|------|------------|
| **lib/eautoseller_client.py** | get_vehicles_swagger nur status=1 (+ optionale API-Parameter); _convert_swagger_vehicle vollständig (alle OpenAPI-Felder); get_vehicle_details_swagger mit withAdditionalInformation=true, resolveEquipments=true; get_publications_swagger(); get_vehicles_pending_swagger(); reservation POST/DELETE. |
| **api/eautoseller_api.py** | get_vehicles: nur status=1 an Client, alle Filter in Python; neues Response-Format; GET filter-options; GET vehicle/{id}; POST/DELETE reserve; Fehlerbehandlung + optional Cache. |
| **templates/verkauf_eautoseller_bestand.html** | Filter-Parameter an /api/eautoseller/vehicles übergeben; Filter-Options laden (optional); Preis-Badge (priceRating); JS-Bug data: { active_only, fetch_hereinnahme } korrigieren. |

---

## 12. Umsetzungsreihenfolge

1. **Client:** Filter auf status=1 beschränken, Feld-Mapping in _convert_swagger_vehicle ergänzen, stockEntrance für Standzeit.
2. **Client:** get_publications_swagger, Details-Parameter, pending, reservation.
3. **API:** Backend-Filter in get_vehicles, Response-Format, filter-options, vehicle/{id}, reserve, Fehler/Cache.
4. **Frontend:** Filter an Backend, Preis-Badge, kleine Fixes (data-Bug).

---

*Stand: 2026-03-19, basierend auf OpenAPI 2.0.40.*
