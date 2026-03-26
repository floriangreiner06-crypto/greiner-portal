# Gudat Connector Setup – Analyse

**Stand:** 2026-02-19  
**Datei:** `Gudat.Connector-3.0.60.0-Setup.exe`  
**Ort:** Sync-Ordner `docs/workstreams/werkstatt/` (auf dem Server: `/mnt/greiner-portal-sync/docs/workstreams/werkstatt/`), ca. 58 MB

**Kontext:** Der Gudat Connector für **Locosoft ist bereits im Einsatz** (Locosoft ↔ Gudat Sync). Diese Analyse klärt, ob der Connector ein **Ersatz oder eine Verbesserung** für die DRIVE-Web-API-Anbindung an Gudat sein kann.

---

## 1. Was ist die Datei?

- **Name:** Gudat Connector, Version **3.0.60.0**, Windows-Installer (`.exe`).
- **Zweck:** Offizielles Gudat-Tool zur **Synchronisation** zwischen DMS (Locosoft) und „Digitale Autohaus“ (werkstattplanung.net) – z. B. Auftragsstatus, Reparaturbeginn, Fertigstellung, Fahrzeugübergabe.
- **Status bei Greiner:** Connector für Locosoft **bereits im Einsatz** (Sync Locosoft ↔ Gudat).

---

## 2. Connector vs. DRIVE Web-API – kein Ersatz

**Frage:** Kann der Connector die direkte Gudat-Web-API-Anbindung in DRIVE ersetzen oder verbessern?

**Antwort: Nein.** Beide haben unterschiedliche Aufgaben:

| | Gudat Connector (bereits im Einsatz) | DRIVE Gudat-Integration (Web-API) |
|---|--------------------------------------|-----------------------------------|
| **Läuft wo?** | Windows-PC (Locosoft-Umgebung) | Linux-Server (Portal) |
| **Aufgabe** | **Sync** Locosoft ↔ Gudat (z. B. Status, Termine) | **Lesen** von Gudat-Daten fürs Portal (Live-Board, Kapazität, Arbeitskarte) |
| **Schnittstelle** | Locosoft ↔ Gudat (kein HTTP-API für Drittsysteme) | Direkt gegen Gudat: REST + GraphQL (werkstattplanung.net) |
| **Ersetzbar?** | — | **Nicht durch den Connector** – der Connector stellt keine API bereit, die DRIVE aufrufen könnte |

- Der Connector **synchronisiert** zwei Systeme (Locosoft und Gudat). Er ist **kein** Dienst, von dem DRIVE Daten abrufen könnte. Das Portal braucht **Echtzeit-Abfragen** (Workload, workshopTasks, Dossiers, Termine) – dazu bleibt die **direkte Gudat-Web-API** nötig.
- **Fazit:** Der Connector ist **kein Ersatz und keine Verbesserung** für die DRIVE-Web-API. DRIVE nutzt weiter `gudat_client.py` und die Gudat REST/GraphQL-API; der Connector bleibt für Locosoft-Sync zuständig.

---

## 3. Aktuelle DRIVE-Integration (Web-API, unverändert)

- **Authentifizierung:** Login gegen `https://werkstattplanung.net/greiner/deggendorf/kic` (XSRF, Session, `/ack` für `laravel_token`).
- **REST:** z. B. `GET /api/v1/workload_week_summary` (Kapazität/Teams).
- **GraphQL:** z. B. `workshopTasks`, `dossiers`, `orders`, `appointments`.
- **Credentials:** `config/credentials.json` → `external_systems.gudat` (Username/Passwort).
- **Verwendung:** Werkstatt Live-Board, Kapazitätsplanung, Arbeitskarte (Dossiers/Tasks), Gudat-Termine in Auftragslisten.

Dokumentation: `docs/GUDAT_API_INTEGRATION.md`, Implementierung: `tools/gudat_client.py`, `api/gudat_api.py`, `api/gudat_data.py`.

---

## 4. Was der Connector (bereits im Einsatz) macht

- **Zweck:** Offizielle **Zweirichtungs-Synchronisation** Locosoft ↔ Gudat (Auftragsstatus, Reparaturbeginn, Fertigstellung, Fahrzeugübergabe usw.).
- **Effekt:** Locosoft und Gudat bleiben abgeglichen; DRIVE profitiert indirekt, weil die Daten in Gudat aktuell sind. Die **Anzeige** dieser Daten im Portal (Live-Board, Kapazität, Arbeitskarte) erfolgt weiter über die **direkte Gudat-Web-API** – der Connector ersetzt sie nicht.

---

## 5. Kurzfassung

| Frage | Antwort |
|------|--------|
| Connector für Locosoft im Einsatz? | Ja, bereits im Einsatz. |
| Ersatz / Verbesserung für DRIVE Web-API? | **Nein.** Der Connector macht Locosoft↔Gudat-Sync und stellt keine API für DRIVE bereit. |
| Was macht DRIVE weiterhin? | Direkte Anbindung an Gudat per Web-API (REST + GraphQL) mit `gudat_client.py` – unverändert. |
| Änderung am Portal nötig? | Nein. |
