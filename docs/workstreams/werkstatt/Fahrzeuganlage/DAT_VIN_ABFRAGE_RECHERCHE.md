# DAT VIN-Abfrage – Recherche REST-API / Schnittstelle

**Stand:** 2026-02-20  
**Ziel:** VIN nach OCR per DAT prüfen bzw. anreichern, um OCR-Fehler zu kompensieren (kritisch für Neuanlage). Locosoft hat VIN-Abfrage nur, wenn Fahrzeug in DAT als „Aktenzeichen“ bereits vorhanden ist.

---

## 1. Öffentliche REST-API?

**Ergebnis: Nein.** DAT stellt **keine öffentlich dokumentierte REST-API** für Endkunden bereit.

- **Daten via Schnittstelle:** [www.dat.de/schnittstellen](https://www.dat.de/schnittstellen)  
  Die Schnittstellenbeschreibung zu **SilverDAT** wird an **Softwareanbieter / DMS** (Schnittstellenpartner) vergeben, nicht als offenes API-Dokument.
- **VIN-Abfrage:** [www.dat.de/vin-abfrage](https://www.dat.de/vin-abfrage)  
  SilverDAT-Funktion; Abrechnung z. B. ab 1,65 € zzgl. MwSt. pro Abruf. Technische Abfrage „per Schnittstelle“ wird nicht öffentlich spezifiziert.
- **Technische Details:** Laut Recherche für REST-API-Implementierung der VIN-Abfrage: **DAT Service kontaktieren** (+49 711 4503-130) oder **Schnittstellenpartnerschaft** anfragen.

---

## 2. Schnittstellenpartnerschaft (für Softwareanbieter)

- [www.dat.de/schnittstellenpartnerschaft](https://www.dat.de/schnittstellenpartnerschaft)  
- Zielgruppe: DMS-Hersteller, Werkstatt-Software, IT-Firmen im Automotive-Bereich (nicht primär einzelne Autohäuser).
- Es gibt ein **Anfrageformular** mit u. a.:
  - **DAT-Kundennummer** (Bestandskunden können anfragen)
  - Auswahl „**Fahrzeugidentifikation per VIN: SilverDAT VIN-Abfrage**“
  - Produkt/Anwendung (z. B. „Eigenentwicklung Portal DRIVE, VIN nach Fahrzeugschein-OCR validieren“)
- Aussage DAT: *„DAT-Kunden haben die Möglichkeit, einzelne SilverDAT-Funktionen über Schnittstelle in die eigenen Applikationen einzubauen.“*
- **Schnittstellen-Workshop** und Liste **zertifizierter Schnittstellenpartner** (u. a. Locosoft) sind auf der Seite verlinkt.

---

## 3. Relevanz für Greiner / DRIVE

| Thema | Befund |
|--------|--------|
| **DAT-Zugang** | Kunden-Login in `config/.env`: DAT_URL, DAT_CUSTOMER_NUMBER, DAT_USER, DAT_PASSWORD. Web-Login für SilverDAT/Portal, nicht zwingend API-Zugang. |
| **REST-API** | Kein Hinweis auf eine „einfache“ REST-API für Bestandskunden auf der Website. Ob DAT nach Anfrage API-Zugang (REST/SOAP/anderes) gewährt, muss beim Service erfragt werden. |
| **Locosoft** | Locosoft ist Schnittstellenpartner; VIN-Abfrage in Locosoft funktioniert nur, wenn das Fahrzeug in DAT bereits als „Aktenzeichen“ geführt wird. Für **beliebige** VIN (z. B. nach OCR) braucht es ggf. einen direkten DAT-Zugang oder eine erweiterte Locosoft-Funktion. |

---

## 4. Empfohlene nächste Schritte

1. **DAT Service anrufen:** +49 711 4503-130  
   - Konkret fragen: „Wir sind DAT-Kunde (Kundennummer aus .env) und möchten in unserem eigenen Portal (DRIVE) nach dem Scannen eines Fahrzeugscheins die erkannte VIN gegen DAT prüfen bzw. Fahrzeugdaten abrufen. Gibt es dafür eine Schnittstelle (REST, SOAP, sonstige) für Bestandskunden?“  
   - Falls ja: Anforderung (Authentifizierung, Endpunkt, Format) und ggf. Vertrag/Kosten klären.

2. **Optional: Schnittstellen-Anfrage per Formular**  
   - [Schnittstellenpartnerschaft – Formular](https://www.dat.de/schnittstellenpartnerschaft/) ausfüllen:  
     - DAT-Kundennummer angeben,  
     - „Fahrzeugidentifikation per VIN: SilverDAT VIN-Abfrage“ ankreuzen,  
     - Anwendung: z. B. „Internes Portal DRIVE – VIN-Validierung nach Fahrzeugschein-OCR“.

3. **Parallel: Locosoft anfragen**  
   - Ob Locosoft für Bestandskunden eine **allgemeine VIN-Abfrage** (nicht nur Aktenzeichen) anbietet – z. B. als Aufruf aus dem DMS heraus, den wir per SOAP oder anderer Locosoft-Schnittstelle anbinden könnten.

---

## 5. Credentials

- **DAT Kunden-Login:** `config/.env` (DAT_URL, DAT_CUSTOMER_NUMBER, DAT_USER, DAT_PASSWORD). Datei ist nicht versioniert (gitignored).
- **Falls** DAT einen API-Zugang bereitstellt: Zusätzliche API-Daten (API-Key, Token, Base-URL) in `config/credentials.json` unter z. B. `dat_vin` ablegen – analog zu `aws_bedrock`.

---

## 6. Links (Kurz)

| Seite | URL |
|--------|-----|
| Startseite | https://www.dat.de/ |
| SilverDAT Produkte | https://www.dat.de/silverdat/ |
| Schnittstellen Übersicht | https://www.dat.de/schnittstellen |
| VIN-Abfrage | https://www.dat.de/vin-abfrage |
| Schnittstellenpartnerschaft / Anfrage | https://www.dat.de/schnittstellenpartnerschaft/ |
| Schnittstellenpartner (u. a. Locosoft) | https://www.dat.de/schnittstellenpartner/ |
| DAT Service | +49 711 4503-130 |

**Hinweis:** Kunden-Login erfolgt über „Kunden Login“ auf der Seite (Cookie-Einwilligung nötig); eine direkte URL wie `/kunden-login/` existiert nicht (404). Login vermutlich im geschützten Bereich nach Cookie-Aktivierung.

---

## 7. myClaim (SilverDAT) – entdeckte VIN-API-Endpoints (intern)

**Stand:** 2026-02-20  
**Quelle:** Netzwerk-Mitschnitt beim VIN-Lookup in der SilverDAT-myClaim-Oberfläche (Browser DevTools). Es handelt sich um die **interne Frontend-API** von myClaim – **nicht öffentlich dokumentiert**. Eine programmatische Nutzung setzt Session-Cookies und gültige Authentifizierung voraus.

### 7.1 VIN-Lookup – erfolgreicher Test

Beispiel-Ergebnis einer VIN-Abfrage (VIN wurde aufgelöst zu):

- **Fahrzeug:** Opel Mokka (2020→), Enjoy  
- **Motor:** 1.2 Ltr. - 100 kW, Benzin, Frontantrieb  
- **DAT Europa-Code:** 01 650 161 026 0002 DE002 6477  
- **KBA:** 1889/AFH, 1889/AGU, 2525/AAV  

(Hinweis: Testabruf kostet ca. 1 € pro Lookup.)

### 7.2 Dispatcher-Pattern (Base-URL myClaim)

Alle Aufrufe laufen über das Dispatcher-Pattern:

- **Basis-Pfad:** `/myClaim/dispatcher--/call/{component}/{action}`
- **Methode:** POST  
- **Authentifizierung:** Session-Cookies nach Login (DAT-Kunden-Login).

### 7.3 Kern-Endpoints (VIN-Lookup und Nachfolge-Calls)

| Endpoint (POST) | Zweck |
|-----------------|--------|
| `.../vehicleSelection.modelPanelGroup/doVinRequest` | **VIN-Lookup** – VIN eingeben, DAT löst auf (Hauptendpoint). |
| `.../vehicleSelection.modelPanelGroup/onSelectECode` | ECode-Auswahl nach VIN-Ergebnis. |
| `.../vehicleSelection.msiComponent/readVehicleTypeKeys` | KBA-Schlüssel (HSN/TSN) lesen. |
| `.../vehicleSelection.msiComponent/readMultiProposalsAndCountAndVehicles` | Fahrzeug-Vorschläge / -Liste. |
| `.../vehicleSelection.msiComponent/readHtucvItemData` | Detail-Daten (HTUCV-Items). |

Bilder/Assets werden über einen weiteren Endpoint mit Query-Parametern (group, type) geladen.

### 7.4 Implikationen für DRIVE

- **Technisch:** Wenn Session-Cookies und Auth nachgebildet werden können, ließen sich diese Endpoints **programmatisch** von DRIVE aus aufrufen (z. B. nach Login mit DAT_USER/DAT_PASSWORD, Session speichern, dann `doVinRequest` mit VIN).
- **Rechtlich/Nutzungsbedingungen:** Unklar, ob DAT die automatisierte Nutzung der Web-UI-API erlaubt. Vor Implementierung: **Rücksprache mit DAT Service** (siehe Abschnitt 4) bzw. Schnittstellen-Anfrage – ggf. offizielle API oder Freigabe für „eigenes Portal mit VIN-Check“ einholen.
- **Kosten:** Pro VIN-Abfrage fallen Kosten an (z. B. ~1 €); bei vielen Scans relevant.

### 7.5 DRIVE-Integration (Fahrzeuganlage)

- **Implementierung:** `api/dat_vin_client.py` (Login + `doVinRequest`), Route `GET/POST /api/fahrzeuganlage/dat-vin-lookup?vin=...`, Button „DAT“ neben dem FIN-Feld in der Fahrzeuganlage.
- **Konfiguration:** In `config/.env`: `DAT_URL` (Basis-URL der myClaim-Oberfläche, z. B. `https://myclaim.silverdat.de`), `DAT_USER`, `DAT_PASSWORD`; optional `DAT_CUSTOMER_NUMBER`. Alternativ/Override in `config/credentials.json` unter `dat_vin` oder `dat`.
- **Ablauf:** User gibt FIN ein (oder nach Scan), klickt „DAT“ → Portal ruft DAT auf, bei Erfolg werden Marke, Handelsbezeichnung, HSN, TSN und ggf. weitere Felder übernommen.
- **Falls Abfrage fehlschlägt:** Login-Pfad und Request-Body von `doVinRequest` sind ohne offizielle Doku geraten. Bei HTTP 200 aber leerer/ungültiger Antwort: Im Browser (DevTools → Network) beim manuellen VIN-Lookup den genauen **Request** (URL, Method, Headers, Request Payload) und die **Response** festhalten und in `dat_vin_client.py` (Login-URLs, Payload-Varianten, Response-Parsing) anpassen.

### 7.6 HAR-Auswertung: myClaim-Login per JWT (2026-02-20)

Aus der HAR-Datei `www.dat.de.har` (Sync: `docs/workstreams/werkstatt/Fahrzeuganlage/`) wurde der **myClaim-Login** ausgewertet:

- **Login ist tokenbasiert:** Es wird **kein** Benutzername/Passwort direkt an myClaim gesendet, sondern ein **JWT** (JSON Web Token). Der JWT wird zuvor beim Login im **AuthorizationManager** (https://www.dat.de/AuthorizationManager/authMgr/dashboard/...) erzeugt und dann an myClaim übergeben.
- **myClaim-Login-Request (aus HAR):**
  - **URL:** `POST https://www.dat.de/myClaim/json/security/Login?fabrikat=DAT&r=<timestamp_ms>`
  - **Content-Type:** `application/x-www-form-urlencoded`
  - **Body:** `token=<JWT>&fabrikat=DAT&product=myClaim`
- **JWT-Inhalt (Beispiel, Base64-decodiert):** `{"iss":"dat","iat":<timestamp>,"clnt":"1039075","user":"greiflor","org":"DE"}` – also Kundennummer, User, Organisation.

**Umsetzung in DRIVE:** In `api/dat_vin_client.py` ist implementiert:
  - **Token beim Aufruf erzeugen (zwei Wege):**
    1. **Requests:** Typische Login-Pfade mit User/Passwort werden per HTTP ausprobiert; Response wird nach JWT durchsucht (`_fetch_token_with_credentials`).
    2. **Scraping (Selenium):** Headless Chrome öffnet die DAT-Login-Seite, füllt User/Passwort in erkannte Formularfelder aus, sendet ab und liest den Token aus Page Source, localStorage/sessionStorage oder aus dem Network-Request zu `json/security/Login` (Performance-Log). So kann der Token wie im echten Browser erzeugt werden, sofern die Login-Seite von unseren Selektoren (z. B. `input[name='j_username']`, `input[name='password']`) gefunden wird.
  - Wenn ein Token (aus 1 oder 2) vorliegt, wird damit der myClaim-Login (`/myClaim/json/security/Login`) ausgeführt.
  - **Optional fester Token:** In der Config kann **`token`** (JWT) gesetzt werden; dann wird dieser zuerst verwendet.
  - **Falls Login weiter fehlschlägt:** DAT-Login-Seite kann abweichende Struktur haben (andere Feldnamen, andere URL). Dann: HAR vom kompletten Login aufzeichnen oder Selektoren/URLs in `_fetch_token_with_selenium` / `_fetch_token_with_credentials` an die reale Seite anpassen.

**Befund Selenium/Headless (2026-02-20):** Beim Klick auf „Kunden Login“ (Button `button.tLogin`) erscheint auf www.dat.de **kein** Login-Formular (Kundennummer, Benutzer, Passwort) im DOM – nur Such- und Newsletter-Felder. Direktaufrufe von `/AuthorizationManager/` und `/myClaim/` liefern 403. **Empfehlung:** Token manuell aus dem Browser (nach Login) in `config/credentials.json` unter `dat_vin.token` eintragen oder DAT Service (+49 711 4503-130) nach API-/Token-Zugang für Bestandskunden fragen.

**Token in credentials.json eintragen (zum Testen):**
```json
"dat_vin": {
  "base_url": "https://www.dat.de/myClaim",
  "username": "greiflor",
  "password": "...",
  "customer_number": "1039075",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...."
}
```
Frischen Token aus dem Browser (nach Login bei DAT) aus dem POST zu `myClaim/json/security/Login` im Tab „Payload“ kopieren.

---

## 8. DAT-Webseite – Erkundung (Kurz)

- **Startseite (dat.de):** Service-Telefon, Branchen (Autohaus/Werkstatt, Kfz-Sachverständige, Branchenpartner), Produkte (SilverDAT, Schnittstellen, VIN-Abfrage, Reparaturkosten, Schaden, Bewertung), Kunden-Login-Hinweis (Cookies aktivieren).
- **SilverDAT (dat.de/silverdat):** Zentrale Produktseite; Module u. a. Gebrauchtwagenbewertung, Reparaturkostenkalkulation, **VIN-Abfrage**, Schadenabwicklung, Schnittstellen, webScan, Restwert E-Auto; „Schnittstellen: Via individueller Schnittstellen Zugriff auf die DAT-Daten“; kein öffentlicher API-Endpunkt oder technische Doku sichtbar.
- **Relevante Unterseiten:** VIN-Abfrage, Daten via Schnittstelle abfragen, Schnittstellenpartnerschaft (Formular für Anfrage).
