# eAutoSeller Swagger – BWA Evaluation (mobile.de Platzierung) Prüfung

**Stand:** März 2026 · Für Support-Anfrage

---

## 1. Was wir im Swagger gefunden haben

**Quelle:** `scripts/tests/eAutoseller.json` (OpenAPI 3.0.2, eAutoseller DMS API Version 2.0.37)

### BWA-Endpoint (einziger Eintrag unter BWA)

| Eigenschaft | Inhalt |
|-------------|--------|
| **Pfad** | `POST /bwa/evaluation` |
| **Methode** | **Nur POST** – es gibt **keinen GET**-Eintrag für `/bwa/evaluation` in der Swagger-Datei. |
| **Request** | `requestBody` **required**, `Content-Type: application/json`, Schema: **VehicleDetails** (vollständiges Fahrzeugdetail-Objekt). |
| **Parameter** | Zusätzlich Header `system-id` (Referenz: `#/components/parameters/systemId`, max. 15 Zeichen). |
| **Response 201** | Body mit u. a. `valuation` (Array) mit `setupName`, `targetPosition`, `totalHits`, `mobileUrl`, `pricing.retailGross` usw. |
| **Response 401/403/404** | Unauthorized, Forbidden, NotFound. |

### Authentifizierung (laut Swagger)

- **ApiKey:** Header `X-API-Key`
- **ClientSecret:** Header `X-CLIENT-KEY`
- Beide werden von uns gesendet (aus `config/credentials.json` bzw. Umgebungsvariablen).
- Zusätzlich: Header **`system-id`** (wir senden `DRIVE-Portal`, Länge 12).

---

## 2. Unser Aufruf (entspricht Swagger)

1. **GET** `https://api.eautoseller.de/dms/vehicles?vin={vin}`  
   → Liefert Fahrzeugliste, wir entnehmen die **Fahrzeug-ID** (`id`).

2. **GET** `https://api.eautoseller.de/dms/vehicle/{id}/details?withAdditionalInformation=false&resolveEquipments=false`  
   → Liefert das **VehicleDetails**-Objekt.

3. **POST** `https://api.eautoseller.de/bwa/evaluation`  
   - Header: `X-API-Key`, `X-CLIENT-KEY`, `Content-Type: application/json`, `Accept: application/json`, `system-id: DRIVE-Portal`  
   - Body: das komplette JSON aus Schritt 2 (unverändert).

---

## 3. Tatsächliches Verhalten beim Test

| Aufruf | Ergebnis |
|--------|----------|
| **GET** `/bwa/evaluation?vehicleId={id}` | **405** – „Die angeforderte Ressource unterstützt die HTTP-Methode GET nicht.“ (GET ist im Swagger nicht definiert.) |
| **POST** `/bwa/evaluation` (mit VehicleDetails-Body) | **401** – „Fehlerhafte Authorisierung! Bitte melden Sie sich bei Ihrem Admin!“ |
| **GET** `/dms/vehicles?vin=...` und **GET** `/dms/vehicle/{id}/details` | **200** – mit denselben Headern (X-API-Key, X-CLIENT-KEY, system-id) erfolgreich. |

→ Derselbe API-Key funktioniert also für DMS (Fahrzeuge, Details), für BWA aber kommt 401.

---

## 4. Fazit für den Support

- **Swagger:** Es ist **nur POST** `/bwa/evaluation` mit JSON-Body (VehicleDetails) dokumentiert; **kein GET** für BWA-Evaluation.
- **Implementierung:** Unser Aufruf entspricht dieser Spezifikation (POST, Body, Header).
- **GET:** Ein GET für die mobile.de-Platzierung wäre aus unserer Sicht wünschenswert (z. B. `GET /bwa/evaluation?vehicleId=...`), ist aber in der vorliegenden Swagger-Datei **nicht** beschrieben.
- **401 bei POST:** Vermutung: Der verwendete API-Key hat **keine Berechtigung** für den BWA-Endpoint. Bitte prüfen, ob für unseren Zugang (X-API-Key / X-CLIENT-KEY) die Berechtigung für **BWA / Evaluation** aktiviert werden muss.

---

## 5. Referenzen im Projekt

- Swagger-Datei: `scripts/tests/eAutoseller.json` (Pfad `/bwa/evaluation` ab Zeile 1990)
- Client-Code: `lib/eautoseller_client.py` → `get_bwa_market_placement()`
- Analyse-Script: `scripts/analyse_eautoseller_swagger.py`
