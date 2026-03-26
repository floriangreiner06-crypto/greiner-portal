# eAutoSeller API – Abfrage mobile.de Platzierung (BWA/Bewerter)

Kurzbeschreibung für eAutoSeller-Support: Wie das Greiner DRIVE-Portal die API für die **mobile.de Börsenplatzierung** (BWA-Evaluation / Bewerter) abfragt.

---

## 1. Authentifizierung

- **Basis-URL:** `https://api.eautoseller.de` (optional überschreibbar in `config/credentials.json` → `eautoseller.api_base_url`)
- **Methode:** HTTP-Header (Swagger-API)
- **Header:**
  - `X-API-Key`: API-Key (aus `config/credentials.json` → `eautoseller.api_key` oder Umgebungsvariable `EAUTOSELLER_API_KEY`)
  - `X-CLIENT-KEY`: Client-Secret (aus `eautoseller.client_secret` oder `EAUTOSELLER_CLIENT_SECRET`)
  - `Content-Type`: `application/json`
  - `Accept`: `application/json`
  - `system-id`: `DRIVE-Portal` (max. 15 Zeichen, für Anzeige im eAutoSeller)

---

## 2. Ablauf: BWA-Evaluation (mobile.de Platz) pro VIN

Laut **Swagger** (eAutoseller DMS API) gibt es für BWA **nur POST**. Wir führen **drei Schritte** aus:

### Schritt 1: Fahrzeug per VIN suchen

- **Methode:** `GET`
- **URL:** `https://api.eautoseller.de/dms/vehicles`
- **Query-Parameter:** `vin=<17-stellige VIN>`
- **Zweck:** Fahrzeug in eAutoSeller finden und **Fahrzeug-ID** (`id`) aus der Antwort ermitteln.

**Beispiel:**  
`GET https://api.eautoseller.de/dms/vehicles?vin=WF0XXXGXXP1234567`

Antwort: Liste (oder Objekt mit `data`) von Fahrzeugen; wir verwenden `id` des ersten Elements.

---

### Schritt 2: Fahrzeugdetails abrufen

- **Methode:** `GET`
- **URL:** `https://api.eautoseller.de/dms/vehicle/{vehicle_id}/details`
- **Query-Parameter:** `withAdditionalInformation=false`, `resolveEquipments=false`
- **Zweck:** VehicleDetails-JSON für den POST-Body (Swagger: requestBody **required**).

---

### Schritt 3: BWA-Evaluation (mobile.de Platzierung)

- **Methode:** `POST` (laut Swagger einzige Methode für `/bwa/evaluation`)
- **URL:** `https://api.eautoseller.de/bwa/evaluation`
- **Body:** Das komplette JSON aus Schritt 2
- **Zweck:** Bewerter ausführen; Response 201 enthält `valuation` (targetPosition, totalHits, mobileUrl, pricing.retailGross usw.).

**Beispiel:**  
`POST https://api.eautoseller.de/bwa/evaluation` mit Body = VehicleDetails aus Schritt 2.

---

## 3. Auswertung der BWA-Evaluation-Antwort

Wir lesen aus der JSON-Antwort das Feld **`valuation`** (Array). Pro Eintrag („Setup“, z. B. mobile.de/Abverkauf) verwenden wir:

| API-Feld (camelCase / snake_case) | Bedeutung bei uns |
|-----------------------------------|-------------------|
| `targetPosition` / `target_position` | **mobile.de Platz** (Börsenplatz, z. B. 10) |
| `totalHits` / `total_hits` | **Treffer** (Anzahl vergleichbarer Anzeigen) |
| `mobileUrl` / `mobile_url` | Link zur Anzeige auf mobile.de (optional) |
| `setupName` / `setup_name` | Name des Setups (optional) |
| `pricing.retailGross` / `pricing.retail_gross` | Preis Platz 1 brutto (optional) |

Wir nutzen in der Regel **das erste Valuation** im Array (meist mobile.de/Abverkauf) und brechen danach ab.

---

## 4. Nutzung im DRIVE-Portal

- **Live-Abfrage:** API-Route `GET /api/eautoseller/market-placements?vins=VIN1,VIN2,VIN3` (max. 30 VINs pro Aufruf).
- **Hintergrund:** Celery-Task **`sync_eautoseller_data`** ruft regelmäßig (Mo–Fr 7–18 Uhr, alle 15 Min.) für alle **aktiven AfA-VINs** (VFW/Mietwagen) die Platzierungen ab und speichert sie in der Tabelle **`eautoseller_bwa_placement`** (Cache). Die Verkaufsempfehlungen (AfA) und weitere Oberflächen lesen aus diesem Cache, nicht bei jedem Seitenaufruf aus der eAutoSeller-API.
- **Implementierung:** `lib/eautoseller_client.py` → Methode **`get_bwa_market_placement(vin, use_swagger=True)`**; Aufrufer z. B. `api/eautoseller_api.py` → `get_market_placements_for_vins()`.

---

## 5. Credentials prüfen

Script: **`scripts/check_eautoseller_credentials.py`**  
- Liest `config/credentials.json` → Block `eautoseller` (`api_key`, `client_secret`) oder Umgebungsvariablen.  
- Führt einen Test-Request aus: `GET https://api.eautoseller.de/dms/vehicles?vin=...`  
- Keine Ausgabe der Keys, nur OK/Fehler.

---

**Stand:** März 2026 · Projekt: Greiner Portal DRIVE
