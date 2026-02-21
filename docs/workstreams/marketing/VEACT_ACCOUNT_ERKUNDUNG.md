# Veact Account – Erkundung (ohne Login)

**Stand:** 2026-02-21  
**Hinweis:** Kein automatischer Login möglich (keine Browser-Automation im Projekt). Öffentliche Infos und URL-Struktur dokumentiert.

---

## 1. Login-URL (OAuth2)

- **Auth-Host:** `https://accounts.veact.net`
- **Beispiel-URL:**  
  `https://accounts.veact.net/v1/oauth2/auth?client_id=asmc.4385903485&redirect_uri=/organisation/646c5ffae49ebe10c9e40ef0/cm/campaign/692104c8ce852d663e422c83/review`

### Erkennbare Parameter

| Parameter       | Wert (Beispiel) | Bedeutung                    |
|----------------|------------------|------------------------------|
| `client_id`    | `asmc.4385903485`| OAuth2-Client (Veact/ASMC)   |
| `redirect_uri` | `/organisation/…/cm/campaign/…/review` | Nach Login: Weiterleitung in die App |

### Organisation / Kampagne (aus redirect_uri)

- **Organisation-ID:** `646c5ffae49ebe10c9e40ef0`
- **Campaign-ID (Beispiel):** `692104c8ce852d663e422c83`
- **Pfad:** `cm/campaign/…/review` → vermutlich „Campaign Management“, Kampagne, Review-Schritt

---

## 2. Login-Seite (Inhalt)

- Titel: **Login - VEACT GmbH**
- Texte: „Welcome“, „Please log in to get started“
- Felder: **Email**, **Password**
- Links: „Lost password?“ → `https://accounts.veact.net/lost-password`
- Hinweis: „By clicking Log in, you agree to our Privacy policy“ (Link zu Veact/Atlassian)

---

## 3. Veact-Plattform (Recherche)

- **Veact** = Automotive Marketing Plattform (Europa), datengesteuerte Sales-/Aftersales-/Marketing-Tools.
- **Customer Hub:** Datenqualität, 360°-Kundenprofile.
- **Auto Journey:** Marketing-Automatisierung, Workflow-/Journey-Builder.
- **DataHub:** Schnittstelle DMS ↔ Partner-Apps; „Dealer Data Key“ für Zugriff.
- **Partner Connect API:** Anbindung zertifizierter Partner-Apps (Lead, Call, Loyalty, Fleet).  
  → Für DRIVE-Integration (z. B. Listen für HU/Inspektion) ggf. Veact anfragen (API-Dokumentation, Anbindung DataHub).

Quelle: [Veact Automotive Marketing Platform](https://veact.com/automotive-marketing-platform/), [Veact Partners](https://veact.com/partners/).

---

## 4. Erkannte API-/OAuth2-Endpunkte (2026-02-21)

Erkundung per Selenium (Login + Chrome Performance-Log). Skript: `scripts/veact_explore_api.py`.

### Erfasste URLs (Network-Log nach Login)

| URL | Bedeutung |
|-----|-----------|
| `https://accounts.veact.net/v1/oauth2/auth` | OAuth2 Authorization Endpoint |
| `https://accounts.veact.net/v1/oauth2/auth?client_id=asmc.4385903485&redirect_uri=...` | Login-Request mit client_id und redirect_uri |
| `https://asmc.veact.net/oauth/callback?code=...&redirect_uri=...` | OAuth2 Callback (bei redirect_uri=app.veact.net) |
| `https://asmc.veact.net/organisation/{org_id}/cm/` | **Kampagnen Manager** (App, redirect_uri=asmc.veact.net) |
| `https://asmc.veact.net/user_mgt/login?target=...` | **User-Management-Login** – asmc leitet hierher, wenn Session fehlt; `target` = Ziel-URL nach Login (z. B. `/organisation/.../cm/`) |

### OAuth2-Flow (beobachtet)

1. **Authorization:** Browser öffnet `accounts.veact.net/v1/oauth2/auth?client_id=asmc.4385903485&redirect_uri=https://app.veact.net/...`
2. **Login:** Nutzer gibt E-Mail/Passwort ein → Submit.
3. **Callback:** Redirect zu `asmc.veact.net/oauth/callback?code=<auth_code>&redirect_uri=...`
4. **App:** Weiterleitung zu `app.veact.net/organisation/<org_id>/cm/campaign/<campaign_id>/review`

Für **API-Zugriff** (z. B. DRIVE → Veact) wäre typisch: Authorization Code oder Client Credentials → Token von einem **Token-Endpoint** (z. B. `accounts.veact.net/v1/oauth2/token` oder `asmc.veact.net/oauth/token`) – nicht im bisherigen Log, müsste von Veact-Doku oder manuell ermittelt werden.

### Einschränkung Server

- **app.veact.net** ist vom Server (10.80.80.20) aus **nicht per DNS erreichbar** („DNS address could not be found“). Daher laden die App-Seiten im Headless-Browser nicht; nur **accounts.veact.net** und **asmc.veact.net** liefern Antworten.
- **In-App-API-Calls** (z. B. `api.veact.net`, REST unter app.veact.net) werden so **nicht** erfasst. Dafür müsste man von einem Rechner mit Außen-DNS (z. B. Arbeits-PC) die App im Browser öffnen und in den **Developer Tools (Network)** die XHR/Fetch-Requests nach dem Login prüfen.

### Mit redirect_uri=asmc.veact.net (Kampagnen Manager)

- **App-URL:** `https://asmc.veact.net/organisation/646c5ffae49ebe10c9e40ef0/cm/` – lädt nach OAuth (inkl. oauth/callback).
- **user_mgt:** `https://asmc.veact.net/user_mgt/login?target=...` – Login-Seite, wenn asmc keine Session hat.
- **Weitere Hosts/APIs aus Log + Page-Source:**
  - **ub.veact.net:** `https://ub.veact.net/api/surveys/?token=...` (Surveys/Analytics, Token phc_…), `https://ub.veact.net/flags/...` (Feature-Flags o.ä.).
  - **mc.veact.net:** in Page-Source referenziert (Subdomain, Rolle unklar).
- Die Kampagnen-Liste wird vermutlich **server-seitig** (Lift/asmc) geliefert – keine separaten XHR für `/api/campaigns` im Log. Für weitere REST-Calls: in der App „Verwalten“, „Kundendaten pflegen“ oder Suche nutzen und in DevTools (Network) die Requests prüfen.

### Gespeicherte Dateien

- `docs/workstreams/marketing/veact_api_endpoints.txt` – API-/App-URLs und Hosts
- `docs/workstreams/marketing/veact_all_requests.txt` – alle erfassten Request-URLs (50+ bei vollem App-Load)

---

## 5. Nächste Schritte (manuell / mit Veact)

1. **Im Browser einloggen** (von Rechner mit Internet-DNS) (z. B. auf dem Server oder lokal):  
   `https://accounts.veact.net/v1/oauth2/auth?client_id=asmc.4385903485&redirect_uri=/organisation/646c5ffae49ebe10c9e40ef0/cm/campaign/692104c8ce852d663e422c83/review`  
   Nach Login landet ihr vermutlich in der Kampagnen-Review-Ansicht (app.veact.net).
2. **Oberfläche erkunden:** Organisation, Kampagnen (cm/campaign), ggf. DataHub/Integrationen, Kundendaten-Quellen.
3. **In-App-API finden:** Nach Login auf app.veact.net **DevTools (F12) → Network** öffnen, XHR/Fetch filtern und alle Request-URLs notieren (z. B. `api.veact.net`, `/graphql`, `/v1/…`). So bekommt ihr die echten App-API-Endpunkte.
4. **API/Integration:** Bei Veact nach **Partner Connect API**, **Token-Endpoint** und **DataHub-Anbindung** für DMS/DRIVE fragen, wenn Exporte aus DRIVE (z. B. Inspektionsfällige) in Veact genutzt werden sollen.

---

## 6. Oberfläche Kampagnen Manager (Screenshot)

**Quelle:** Screenshot VEACT ASMC – Kampagnen Manager, Autohaus Greiner GmbH & Co. KG.

### App-URL (tatsächlich genutzt)

- **Base:** `https://asmc.veact.net`
- **Kampagnen Manager:** `asmc.veact.net/organisation/646c5ffae49ebe10c9e40ef0/cm/`
- **Struktur:** `/organisation/<org_id>/cm/` → **cm** = Kampagnen Manager (Campaign Manager).

Die App läuft damit unter **asmc.veact.net** (nicht app.veact.net im Alltag – redirect_uri kann trotzdem auf app.veact.net zeigen, danach landet der Browser auf asmc).

### Navigation (Menüleiste)

| Menüpunkt        | Vermuteter Bereich / API-Nähe          |
|------------------|----------------------------------------|
| Startseite       | Dashboard                              |
| Marketing Planer | Planung                                |
| Auswertungen     | Reports / Analytics                    |
| **Kampagnen Manager** | Kampagnen-Liste, Erstellen, Verwalten |
| VLP              | Vehicle Lifecycle (?)                  |
| Print Vorlagen   | Druckvorlagen                          |
| Konto            | Account-Einstellungen                  |
| Benutzer         | Benutzerverwaltung                     |

Weitere Funktionen auf der Seite: **Kunden- und Fahrzeugsuche** (Header), **Neue Kampagne erstellen**, **Kundendaten pflegen**, **Kampagnensuche**, pro Kampagne **Verwalten** und Status (Review / Followup).

### Daraus abgeleitete API-Vermutungen (für DevTools-Check)

| Funktion / Ressource     | Mögliche Endpunkte (zu prüfen) |
|--------------------------|---------------------------------|
| Organisation             | `/organisation/{org_id}/…` oder `/api/organisation/{org_id}` |
| Kampagnen-Liste          | `/api/campaigns` oder `/organisation/{org_id}/cm/campaigns` |
| Kampagne anlegen         | `POST` Kampagne („Neue Kampagne erstellen“) |
| Kampagne verwalten       | `GET/PUT /api/campaigns/{campaign_id}` oder `…/cm/campaign/{id}` |
| Kunden-/Fahrzeugsuche    | `/api/customers/search`, `/api/vehicles/search` oder ähnlich |
| Kundendaten pflegen      | `/api/customers` oder `/api/customer-data` |
| Benutzer                 | `/api/users` oder unter Konto/Benutzer |
| Auswertungen             | `/api/reports`, `/api/analytics` |

In den **DevTools (F12) → Network → XHR/Fetch** beim Klicken (Kampagnen laden, Suche, „Verwalten“, „Kundendaten pflegen“) die tatsächlichen Request-URLs und Methoden notieren – dann lassen sich diese Vermutungen durch echte Endpunkte ersetzen.

---

*Keine Zugangsdaten in dieser Datei – nur URL-Struktur und öffentliche Informationen.*
