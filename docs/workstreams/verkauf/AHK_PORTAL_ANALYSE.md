# AHK-Portal (Die Autohauskenner) – Analyse & Integrationseinschätzung

**Datum:** 2026-02-12  
**Portal-URL:** https://autohauskenner.de/portal/login  
**Zweck:** Kundenbewertungsportal (Autohauskenner) inkl. AHK FIN Check.

---

## 1. Durchgesehene Portal-Struktur (nach Login)

| Menüpunkt | URL | Inhalt |
|-----------|-----|--------|
| Bewertungsübersicht | `/portal/client/dashboard` | KPIs Gesamtbewertung, Bewertungen, Rating-Skala; Filter Gruppe/Standort; Tabelle Kanäle (Autohauskenner, Google, Facebook, mobile.de, AutoScout24) |
| Standorte | `/portal/client/locations` | Standortverwaltung (z. B. 13773, 17968) |
| Kunden/Gruppen | `/portal/client/customers` | Kunden- und Gruppenzuordnung |
| Bewertungen | `/portal/client/user/ratings` | Einzelbewertungen, Bearbeitung |
| Plus Reporte | `/portal/client/monthly/report` | Monatliche Reporte |
| Unique Link erstellen | `/portal/client/unique/link/create/show` | Erstellung individueller Bewertungslinks |
| **AHK FIN Check** | **`/portal/cardentity`** | FIN-Eingabe, Report in Popup, Tabelle „Reporte“ (Erstellt am, Benutzer, FIN, Status, Reporte) |

Technik: Laravel (Session, XSRF), jQuery, DataTables, Bootstrap; `<base href="/portal">`.

---

## 2. API / REST-API

- **Keine öffentliche REST-API:**  
  `/api/`, `/api/v1`, `/portal/api`, `/portal/api/user` → alle **404**.

- **Gefundene JSON-fähige Endpunkte (nur für Portal-UI):**
  - `GET /portal/shared/customer/suggestion?query=...` → JSON `{"query":"customer","suggestions":[]}` (Autocomplete Kunde)
  - `GET /portal/shared/location/suggestion?query=...` → JSON (Autocomplete Standort)

  Diese sind reine Hilfsendpunkte für das Portal, keine dokumentierte oder für Drittsysteme gedachte API.

- **AHK FIN Check:**
  - Formular: `GET /portal/cardentity/vin?vin=...&location=...&_token=...`
  - Antwort: **HTML** (Report-Seite), wird im Portal in einem Popup geöffnet.
  - Mit `Accept: application/json` wird weiterhin HTML zurückgegeben → **kein REST-API-Modus** für FIN-Check.
  - PDF: `/portal/cardentity/report/{reportId}/pdf/create` (Popup).

**Fazit:** Es existiert **keine** für Drive nutzbare REST- oder Web-API (weder für Bewertungen noch für FIN Check). Das Portal ist webbasiert, session-basiert, ohne offengelegte API.

---

## 3. Sollten wir integrieren? (Einschätzung)

### Was möglich ist (ohne API)

- **Link aus Drive:**  
  Link „AHK Portal“ / „FIN Check (AHK)“ → `https://autohauskenner.de/portal/login` oder (nach Login) `https://autohauskenner.de/portal/cardentity`.  
  Nutzer müssen sich im AHK-Portal anmelden; kein Single-Sign-On, kein automatischer Datenaustausch.

- **Deep-Link FIN (theoretisch):**  
  `https://autohauskenner.de/portal/cardentity/vin?vin=XXX&location=13773` setzt VIN und Standort.  
  Funktioniert nur, wenn der Nutzer bei Autohauskenner bereits eingeloggt ist (Session). Ohne Login führt der Link zur Login-Seite; danach ggf. Redirect – aber kein garantiertes „Report sofort sichtbar“ ohne Prüfung durch AHK.  
  Für Drive: Link mit VIN aus Locosoft/eAutoSeller vorbelegen → **nur Komfort**, keine echte Integration.

### Was nicht möglich ist (ohne API)

- Kein automatischer Abruf von Bewertungs-KPIs in Drive.
- Kein automatischer FIN-Check aus Drive (kein Server-zu-Server).
- Kein Einbinden von Bewertungsdaten in Drive-Dashboards ohne manuellen Export/Abgleich.

### Empfehlung

- **Kurzfristig:** In Drive einen **einfachen Link** (z. B. im Verkauf-/GW-Bereich) zu „Autohauskenner Portal“ bzw. „AHK FIN Check“ setzen (`https://autohauskenner.de/portal/cardentity`). Optional: Deep-Link mit VIN, sofern gewünscht und getestet (Login-Zustand beachten).
- **Echte Integration (Daten in Drive):** Nur sinnvoll, wenn Die Autohauskenner eine **offizielle API** (REST/JSON) anbieten und für Händler freigeben. Dafür: **Anfrage an AHK (Support/Vertrieb)** – ob API existiert, ob für Greiner nutzbar, Dokumentation, Preise.
- **Bewertungsdaten im Drive:** Erst prüfen, wenn API verfügbar ist; dann Nutzen (z. B. Kennzahlen im Verkaufs-Dashboard) vs. Aufwand und Lizenz bewerten.

---

## 4. Referenz

- Login: https://autohauskenner.de/portal/login  
- Nach Login: Bewertungsübersicht, Standorte, Bewertungen, Plus Reporte, Unique Link, **AHK FIN Check** (`/portal/cardentity`).
