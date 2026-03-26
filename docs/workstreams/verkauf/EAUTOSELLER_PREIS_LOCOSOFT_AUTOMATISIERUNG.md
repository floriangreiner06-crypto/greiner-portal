# eAutoSeller Preisänderungen → DRIVE → Locosoft: Automatisierung

**Workstream:** Verkauf  
**Stand:** 2026-03-11

## Ausgangslage

- **Führendes Preismanagement:** eAutoSeller (VKL ändert Preise dort).
- **Aktueller Ablauf:** VKL ändert Preis in eAutoSeller → eAutoSeller schickt E-Mail mit Änderungsinfo an Dispo-Verteiler → Dispo kopiert VIN, sucht Fahrzeug in Locosoft, tippt Preis ein.
- **Ziel:** eAutoSeller stellt ein JSON mit den Änderungen bereit → wir ermöglichen Automatisierung (weniger manuelle Schritte, weniger Fehler).

**Einschränkung (aus Test 2026-03-11):** Locosoft-Preise können von DRIVE aus **nicht** per SOAP geschrieben werden (`writeVehicleDetails` hat keine Preisfelder; Locosoft-PostgreSQL ist read-only). Siehe `LOCOSOFT_FAHRZEUGPREIS_SOAP_TEST.md`.

---

## Zielbild

1. **eAutoSeller** liefert Preisänderungen als JSON (Push-Webhook oder Pull-Endpoint).
2. **DRIVE** empfängt bzw. holt die Änderungen, speichert sie in einer Warteschlange.
3. **Dispo** arbeitet die Warteschlange ab:  
   - **Option A (aktuell machbar):** Liste in DRIVE mit VIN + neuem Preis, „In Locosoft übernehmen“ = manuell (VIN/Preis kopieren, in Locosoft eintragen), in DRIVE „Erledigt“ markieren.  
   - **Option B (später):** Wenn Loco-Soft eine API für Verkaufspreis-Updates anbietet → DRIVE ruft diese API auf und übernimmt automatisch.

---

## 1. Aufnahme der Änderungen in DRIVE

### Variante A: Webhook (eAutoSeller push)

- eAutoSeller sendet bei jeder Preisänderung einen **HTTP POST** an eine DRIVE-URL (z. B. `https://auto-greiner.de/api/verkauf/eautoseller-price-changes`).
- **Payload (Beispiel):**  
  `{ "changes": [ { "vin": "KMHKR81EFPU172712", "priceGross": 37000, "changedAt": "2026-03-11T10:00:00Z" } ] }`  
  (exaktes Format mit eAutoSeller abstimmen.)
- DRIVE: Route mit API-Key/Secret prüfen, JSON parsen, pro Eintrag einen Datensatz in der Warteschlangen-Tabelle anlegen.

**Vorteil:** Echtzeit, kein Polling.  
**Voraussetzung:** eAutoSeller unterstützt Webhook/Callback-URL und Payload-Format.

### Variante B: Polling (DRIVE pull)

- DRIVE ruft periodisch (z. B. alle 15 Min, wie `sync_eautoseller_data`) einen eAutoSeller-Endpoint auf, der **nur geänderte Preise** liefert (z. B. `GET /dms/vehicles/prices?from=<lastRun>` oder `GET /dms/vehicles?changedSince=<timestamp>`).
- Bereits vorhanden im Client: `get_vehicle_prices_swagger(from_date=...)`, `get_vehicles_swagger(changed_since=...)`.
- DRIVE vergleicht mit letztem Stand (oder Locosoft-Abfrage) und schreibt **neue** Änderungen in die Warteschlangen-Tabelle.

**Vorteil:** Keine Änderung bei eAutoSeller nötig, wenn der Endpoint bereits „changed since“/„from“ unterstützt.  
**Nachteil:** Verzögerung bis zum nächsten Lauf.

### Empfehlung

- **Kurzfristig:** Polling nutzen, falls eAutoSeller `changedSince`/`from` für Preise liefert – dann sofort umsetzbar.
- **Mittelfristig:** Mit eAutoSeller klären, ob ein **Webhook für Preisänderungen** möglich ist; wenn ja, zusätzlich Webhook-Route in DRIVE einbauen und Einträge in dieselbe Warteschlange schreiben.

---

## 2. DRIVE: Warteschlange und API

### Tabelle (PostgreSQL drive_portal)

```sql
-- Vorschlag
CREATE TABLE eautoseller_preis_uebernahme (
  id SERIAL PRIMARY KEY,
  vin VARCHAR(17) NOT NULL,
  preis_neu_eur NUMERIC(12,2) NOT NULL,
  preis_alt_eur NUMERIC(12,2),           -- optional, aus Locosoft beim Anzeigen
  geaendert_am TIMESTAMPTZ,               -- von eAutoSeller
  empfangen_am TIMESTAMPTZ DEFAULT NOW(),
  status VARCHAR(20) DEFAULT 'offen',     -- offen | erledigt | fehler | ignoriert
  erledigt_am TIMESTAMPTZ,
  erledigt_von VARCHAR(255),              -- z.B. LDAP-User
  quelle VARCHAR(20) DEFAULT 'polling',   -- webhook | polling
  UNIQUE (vin)                            -- oder pro VIN nur letzter offener Eintrag
);
```

- **Eindeutigkeit:** Pro VIN entweder nur **einen** offenen Eintrag (bei neuem Update: bestehenden aktualisieren) oder Historie mit `status`.
- **API:**  
  - `GET /api/verkauf/eautoseller-preis-uebernahme` → Liste offener Einträge (für Dispo-UI).  
  - Optional: `POST /api/verkauf/eautoseller-preis-uebernahme` (Webhook von eAutoSeller).  
  - `PATCH /api/verkauf/eautoseller-preis-uebernahme/<id>` → `status: erledigt` setzen (Dispo hat in Locosoft eingetragen).

### Dispo-UI (Verkauf)

- **Seite z. B.** `/verkauf/preis-uebernahme` (oder unter „Verkauf“ als Unterpunkt).
- **Inhalt:** Tabelle mit Spalten VIN, Preis alt (aus Locosoft, read-only), Preis neu (aus eAutoSeller), Datum, Aktionen:
  - **„VIN kopieren“** / **„Preis kopieren“** (Copy-to-Clipboard).
  - **„Als erledigt markieren“** → PATCH setzt `status=erledigt`, Eintrag verschwindet aus der offenen Liste.
- Optional: Link „In Locosoft öffnen“ (wenn Locosoft eine Such-URL mit VIN hat).
- Rechte: Feature z. B. `verkauf_preis_uebernahme` oder bestehende Rolle Dispo/VKL.

---

## 3. Locosoft-Anbindung (Stand heute)

- **Schreiben:** Nicht möglich – weder PostgreSQL noch SOAP `writeVehicleDetails` bieten Verkaufspreis-Felder. Siehe `LOCOSOFT_FAHRZEUGPREIS_SOAP_TEST.md`.
- **Lesen:** Unverändert – Locosoft-PostgreSQL (read-only) für „Preis alt“ in der Dispo-Liste nutzbar.
- **Später:** Wenn Loco-Soft eine API zum Setzen von `dealer_vehicles.out_sale_price` (o. ä.) bereitstellt, kann DRIVE einen Button „In Locosoft übernehmen“ anbieten, der diese API aufruft und danach den Eintrag automatisch auf „erledigt“ setzt.

---

## 4. Ablauf im Überblick

| Schritt | Verantwortung | Technik |
|--------|---------------|---------|
| 1. Preis ändern | VKL | eAutoSeller (wie bisher) |
| 2. Änderung an DRIVE | eAutoSeller → DRIVE | Webhook (POST) oder DRIVE-Polling (GET prices/changedSince) |
| 3. Speichern | DRIVE | Tabelle `eautoseller_preis_uebernahme` |
| 4. Abarbeiten | Dispo | DRIVE-UI: Liste, VIN/Preis kopieren, in Locosoft eintragen, „Erledigt“ |
| 5. (später) Auto-Übernahme | DRIVE | Nur wenn Locosoft Preis-API anbietet |

---

## 5. Nächste Schritte

1. **eAutoSeller klären:**  
   - Wird ein **Webhook** für Preisänderungen angeboten? (URL, Auth, JSON-Format.)  
   - Falls nicht: Liefert `GET /dms/vehicles/prices?from=<date>` oder `GET /dms/vehicles?changedSince=<date>` nur **geänderte** Fahrzeuge mit Preis?
2. **DRIVE:**  
   - Migration für `eautoseller_preis_uebernahme` anlegen und ausführen.  
   - API: Liste abrufen, Webhook-Endpoint (falls gewünscht), „Erledigt“ setzen.  
   - Celery: Optionalen Task für Polling (z. B. in `sync_eautoseller_data` integrieren) bauen.  
   - Dispo-Seite mit Tabelle und Aktionen (Kopieren, Erledigt) umsetzen.
3. **Kommunikation:** E-Mail an Dispo kann beibehalten werden oder durch Hinweis „Preisübernahmen in DRIVE unter Verkauf → Preisübernahme“ ersetzt/ergänzt werden.

---

## Referenzen

- `LOCOSOFT_FAHRZEUGPREIS_SOAP_TEST.md` – Locosoft-Preis-Schreiben nicht möglich
- `docs/workstreams/werkstatt/Fahrzeuganlage/LOCOSOFT_ANLAGE_SOAP.md` – PostgreSQL read-only, SOAP nur Stammdaten
- `lib/eautoseller_client.py` – `get_vehicle_prices_swagger(from_date)`, `get_vehicles_swagger(changed_since)`
- `api/eautoseller_api.py` – bestehende eAutoSeller-Anbindung
