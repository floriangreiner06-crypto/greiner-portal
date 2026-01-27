# e-autoseller Swagger API Analyse

**Erstellt:** 2026-01-21 15:29:09
**Quelle:** eAutoseller.json

---

## 📋 API Information

- **Title:** eAutoseller DMS API
- **Version:** 2.0.37
- **Description:** <p>Documentation to connect to the new DMS API services of ITKrebs GmbH &amp; Co. KG</p><p><b>Please note</b><br>At least the APIKey and the ClientSecret are required for authentication, all other required information are documented for the responding endpoints. If you don't have yet authentication data, please contact <a href='mailto:support@eautoseller.de'>support@eautoseller.de</a>.</p>

## 🌐 Servers

- https://api.eautoseller.de

## 🔐 Authentication

**Schemes:** ApiKey, ClientSecret

**Default Security:** [{'ApiKey': [], 'ClientSecret': []}]

## 📊 Summary

- **Total Endpoints:** 33
- **Methods:** {'GET': 18, 'POST': 10, 'PATCH': 1, 'DELETE': 4}
- **Tags:** BWA, Branches / Point of Sale, Market export, Publications, References, Vehicle Exports/Prints, Vehicle Files, Vehicle Images, Vehicle Statistics, Vehicle prices, Vehicles
- **Has Authentication:** True

## 🔗 Endpoints

### BWA

#### POST /bwa/evaluation

**Summary:** Create a new evaluation for a given vehicle

**Responses:**

- **201:** Created
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### Branches / Point of Sale

#### GET /dms/branches

**Summary:** Get a list of all branches

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### Market export

#### GET /markets/export

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| Authorization | header | False | string |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A
- **429:** Interval for retrieval was not maintained

---

### Publications

#### GET /dms/publications/vehicles/publicated

**Summary:** Get all vehicles which are already publicated to any market

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| statistics | query | False | boolean |
| Accept-Language | header | False | string |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A

---

#### GET /dms/publications/vehicles/errenous

**Summary:** Get all vehicles which have publication errors of any market

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| checkPOS | query | False | boolean |
| Accept-Language | header | False | string |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A

---

#### GET /dms/publications/markets

**Summary:** Get a list of all publication markets

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### References

#### GET /references/makes

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### Vehicle Exports/Prints

#### GET /dms/vehicles/exports

**Summary:** Get a list of possible exports for vehicles

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### POST /dms/vehicle/{id}/export/{exportId}

**Summary:** Generate and receive an export for the specific vehicle

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |
| exportId | path | True | string |

**Responses:**

- **200:** Ok
  - Content Types: application/pdf
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### Vehicle Files

#### GET /dms/vehicle/{id}/files

**Summary:** Get a list of files for a specific vehicle

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### POST /dms/vehicle/{id}/files

**Summary:** Upload an attachment file for a specific vehicle

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |
| type | query | True | VehicleFileType |

**Responses:**

- **201:** Created
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### DELETE /dms/vehicle/{id}/files/{fileId}

**Summary:** Delete an attached file of a vehicle

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |
| fileId | path | True | integer |

**Responses:**

- **200:** N/A
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### Vehicle Images

#### POST /dms/vehicle/{id}/images

**Summary:** Upload vehicle images for specific vehicle

**Description:** Allowed formats: image/jpg, image/jpeg<br>Min. measurements: 600x450 px<br>Max. measurements: 1920x1440 px

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### DELETE /dms/vehicle/{id}/images

**Summary:** Delete vehicle images for specific vehicle

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** N/A
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### Vehicle Statistics

#### GET /dms/vehicle/{id}/statistics

**Summary:** [Beta] Get vehicle statistics by id

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### POST /dms/vehicle/{id}/statistics

**Summary:** [Beta] Set vehicle statistics by id

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### Vehicle prices

#### GET /dms/vehicles/prices

**Summary:** Get all active vehicles with prices and timestamps of the last changes

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| from | query | False | string |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A

---

#### GET /dms/vehicles/prices/suggestions

**Summary:** Get all active vehicles with price suggestion

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A

---

#### POST /dms/vehicle/{id}/prices

**Summary:** Update vehicle prices by vehicle id

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** N/A
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### POST /dms/vehicle/reference/{offerReference}/prices

**Summary:** Update vehicle prices by vehicles reference number

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| offerReference | path | True | string |

**Responses:**

- **200:** N/A
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### POST /dms/vehicle/vin/{vin}/prices

**Summary:** Update vehicle prices by vehicles VIN

**Responses:**

- **200:** N/A
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

### Vehicles

#### GET /dms/vehicles

**Summary:** List vehicles

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| offerReference | query | False | string |
| vin | query | False | string |
| mobileAdId | query | False | integer |
| as24AdId | query | False | string |
| changedSince | query | False | string |
| status | query | False | string |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### GET /dms/vehicles/pending

**Summary:** Get all active vehicles with uncompleted data

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A

---

#### POST /dms/vehicle/import

**Summary:** Create or update a single vehicle

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| datReferenceNumber | query | False | string |

**Responses:**

- **200:** Ok, vehicle is updated
  - Content Types: application/json
- **201:** Ok, new vehicle is created
  - Content Types: application/json
- **400:** Bad request, Vehicle cannot be saved
  - Content Types: application/json

---

#### PATCH /dms/vehicle/import/{id}

**Summary:** [Beta] Update a single vehicle partially

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** Ok, vehicle is updated
  - Content Types: application/json
- **400:** Bad request, Vehicle cannot be saved
  - Content Types: application/json

---

#### GET /dms/vehicle/{id}

**Summary:** Get a vehicle by id

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### DELETE /dms/vehicle/{id}

**Summary:** Delete or deactivate a vehicle

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** Ok, vehicle is deactivated
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### GET /dms/vehicle/vin/{vin}

**Summary:** Get a vehicle by VIN

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### GET /dms/vehicle/reference/{reference}

**Summary:** Get a vehicle by offer reference

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| reference | path | True | string |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### GET /dms/vehicle/{id}/overview

**Summary:** Get vehicle overview by vehicle id

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### GET /dms/vehicle/{id}/details

**Summary:** Get vehicle details by vehicle id

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |
| withAdditionalInformation | query | False | boolean |
| resolveEquipments | query | False | boolean |

**Responses:**

- **200:** Ok
  - Content Types: application/json
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### POST /dms/vehicle/{id}/reservation

**Summary:** Set vehicle reservation

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** N/A
- **201:** N/A
- **401:** N/A
- **403:** N/A
- **404:** N/A

---

#### DELETE /dms/vehicle/{id}/reservation

**Summary:** Delete vehicle reservation

**Parameters:**

| Name | In | Required | Type |
|------|----|----------|------|
| id | path | True | integer |

**Responses:**

- **200:** N/A
- **401:** N/A
- **403:** N/A
- **404:** N/A

---


**Letzte Aktualisierung:** 2026-01-21 15:29:09
