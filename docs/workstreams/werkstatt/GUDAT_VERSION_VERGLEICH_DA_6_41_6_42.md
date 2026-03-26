# Gudat/DA/ – Versionsvergleich mit Update 6.41 & 6.42

**Stand:** 2026-03-10  
**Workstream:** werkstatt  
**Quelle DA/ Updates:** [DA/ Version 6.41 & 6.42](https://www.digitalesautohaus.de/blog/updates/da-version-6-41-6-42/)

## Ziel

Prüfen, ob die bei Greiner genutzte Gudat-Instanz (werkstattplanung.net) dem Stand der angekündigten DA/ Versionen 6.41 und 6.42 entspricht. Die **Produktversion** (6.41/6.42) wird von der Gudat-API **nicht** ausgeliefert; ein Abgleich ist nur über unterstützte API-Felder und optional Rückfrage beim Anbieter möglich.

---

## Unsere Gudat-Nutzung (DRIVE)

### Zugriff

| Komponente | URL / Endpoint | Verwendung |
|------------|----------------|------------|
| Basis-URL | `https://werkstattplanung.net/greiner/deggendorf/kic` | Login, GraphQL, REST |
| REST | `GET /api/v1/workload_week_summary`, `GET /api/v1/user` | Kapazität, User (z. B. `tools/gudat_client.py`) |
| GraphQL | `POST .../graphql` | Disposition, Dossier, Arbeitskarte, Anhänge |

### Genutzte GraphQL-Felder (Auswahl)

- **workshopTasks:** `id`, `start_date`, `work_load`, `work_state`, `description`, `workshopService`, `resource`, `dossier { id, vehicle, orders }`
- **dossier:** `id`, **`note`**, **`orders { id, number, note }`**, **`states { id, name }`**, `comments`, `workshopTasks`, `workshopTaskPackages`, `documents`

Die Arbeitskarte (Diagnose-Text) nutzt bewusst **`dossier.note`** und **`orders.note`** als Fallback, wenn `workshopTask.description` leer ist (siehe CONTEXT.md, Garantie/Arbeitskarte 2026-03-10).

---

## DA/ 6.41 & 6.42 – Relevanz für unsere Integration

### Direkt API-relevant

| Feature (Website) | API-Feld / Technik | Unser Stand |
|-------------------|---------------------|-------------|
| **Neues Anmerkungsfeld im Auftrag** | Auftrag-Anmerkung unter „Aufträge“ | Wir fragen **`orders.note`** in der Dossier-Query ab und nutzen es für die Arbeitskarte (Diagnose-Fallback). **Wenn diese Abfrage bei euch fehlerfrei läuft und Werte liefert, spricht das für 6.41+.** |
| **Anmerkungen in PDF Platzhaltern** | Platzhalter „Anmerkungen“ im Auftrag | Dieselbe fachliche Quelle wie `orders.note`; für uns nur relevant, falls wir PDF-Export aus DA/ nutzen. |
| **Vorgangsstatus (Fakturierung)** | `dossier.states` | Wir fragen **`dossier.states`** ab; falls die Instanz das Feld nicht unterstützt, nutzen wir einen Fallback **ohne** `states` (siehe `arbeitskarte_api.py`: „Gudat-API unterstützt states nicht“). **Ältere Instanzen können ohne `states` sein.** |

### Überwiegend UI/Planung (kein API-Versionstest)

- Entwürfe nach Nutzergruppen, Mercedes me Zeitraster, Breite des Eingangs, Termintypen ↔ Mitarbeiterkategorien  
- Verbesserte Suche (Telefon, FIN mit `*` + letzte 6 Stellen), filterbare Menüstruktur  
- Vorgänge wiederherstellen, Suchkriterium „Kontakt“, Reifen/Räder in Stammdaten, Pflichtfelder hervorheben  

Diese Punkte verbessern die Bedienung in DA/, sind für unsere REST/GraphQL-Anbindung aber **kein Indikator** für die API-Version.

---

## Wie prüfen, ob die Instanz „aktuell“ ist?

1. **Pragmatischer Test (bereits im Einsatz)**  
   - Arbeitskarte für einen Auftrag mit ausgefüllter **Auftrags-Anmerkung** in Gudat öffnen.  
   - Wenn die Diagnose/Anmerkung aus **GUDAT Auftrag** bzw. **GUDAT Dossier** im PDF erscheint, werden `orders.note` und/oder `dossier.note` von der API geliefert – **damit ist die für uns relevante Funktionalität von 6.41 (Anmerkungsfeld) vorhanden.**

2. **GraphQL-Fehler auswerten**  
   - Wenn in Logs **kein** Fallback wegen `states` („Gudat-API unterstützt states nicht“) vorkommt, liefert die Instanz `dossier.states` – konsistent mit neueren Versionen.  
   - Wenn **Fallback ohne `states`** genutzt wird, kann die Instanz älter sein (oder ein eingeschränktes Schema haben).

3. **Version beim Anbieter erfragen**  
   - **Empfehlung:** Bei Gudat/DA Support (z. B. [digitalesautohaus.de/kontakt](https://www.digitalesautohaus.de/kontakt/)) konkret nach der **Produktversion** der Instanz **werkstattplanung.net/greiner/deggendorf** fragen (z. B. „Welche DA/ Version (6.41 / 6.42) läuft auf unserer Instanz?“).  
   - Die API liefert unter den uns bekannten Endpoints (**/api/v1/***, **/graphql**) **keine** Versionsnummer in Response oder Header.

---

## Kurzfassung

- **DA/ 6.41 & 6.42** bringen u. a. das **Anmerkungsfeld im Auftrag** (`orders.note`) und verbesserte Suche/UI; für unsere Integration sind vor allem **`orders.note`** und **`dossier.states`** relevant.  
- **DRIVE** nutzt **`dossier.note`** und **`orders.note`** bereits; wenn diese Felder in der Praxis befüllt werden und in der Arbeitskarte ankommen, ist die für uns relevante 6.41-Funktion vorhanden.  
- Eine **exakte Versionszuordnung** (6.41 vs. 6.42) ist über die API **nicht** möglich – nur über Verhalten (Felder vorhanden/fehlen) und **Rückfrage beim Anbieter**.

---

**Referenzen:**  
`api/gudat_data.py`, `api/arbeitskarte_api.py`, `tools/gudat_client.py`, `docs/workstreams/werkstatt/GUDAT_FAKTUR_STATUS_MACHBARKEIT.md`, `docs/workstreams/werkstatt/CONTEXT.md`.  
**Offizielle API-Doku:** [DA API V1 Reference](https://werkstattplanung.net/greiner/deggendorf/kic/da/docs/index.html) (inkl. Changelog 1.0–1.9).
