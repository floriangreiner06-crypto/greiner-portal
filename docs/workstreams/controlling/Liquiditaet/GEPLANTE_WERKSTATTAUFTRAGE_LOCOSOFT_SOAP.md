# Geplante Werkstattaufträge – Locosoft PostgreSQL und SOAP

**Workstream:** Controlling / Werkstatt  
**Stand:** 2026-02  
**Frage:** Können wir geplante Werkstattaufträge in Locosoft erkennen (für Liquiditätsvorschau „Erwartete Einnahmen Werkstatt“)?

---

## Kurzantwort: **Ja – über PostgreSQL und zusätzlich über SOAP**

Geplante (offene) Werkstattaufträge werden in DRIVE bereits genutzt und sind über **zwei Wege** in Locosoft erkennbar:

1. **Locosoft PostgreSQL** (direkte DB) – **heute schon SSOT in DRIVE**
2. **Locosoft SOAP** – alternative/ergänzende Erkennung

---

## 1. PostgreSQL (orders + labours) – bereits in DRIVE genutzt

### Datenquelle

- **orders:** Werkstattaufträge mit `order_date`, `has_open_positions`, `estimated_inbound_time`, `estimated_outbound_time`, `subsidiary`
- **labours:** Arbeitspositionen mit `order_number`, `time_units` (AW), `net_price_in_order`, `is_invoiced`

### Wo wir das nutzen

- **WerkstattData.get_offene_auftraege()** (`api/werkstatt_data.py`): Holt offene Aufträge mit Vorgabe-AW aus `orders` + `labours`, Filter z. B. `has_open_positions = true`, `order_date` der letzten X Tage.
- Werkstatt Live, Gudat-Disposition, Stempelzeiten-Verteilung etc. bauen auf derselben Locosoft-DB (orders/labours) auf.

### Für Liquiditätsvorschau

- **Offene Aufträge** (noch nicht fakturiert): `orders` mit `has_open_positions = true` + `labours` mit `is_invoiced = false` → Betrag = Summe `labours.net_price_in_order` (ggf. + Teile aus `parts`).
- **Erwartetes Datum:** z. B. `estimated_outbound_time` oder `order_date` + Puffer + Zahlungsziel.
- Daten sind in Locosoft vorhanden; Anbindung an die Liquiditätsvorschau noch nicht umgesetzt.

---

## 2. SOAP – Erkennung geplanter/offener Aufträge

### Verfügbare Methoden (Locosoft SOAP, 10.80.80.7:8086)

| Methode | Beschreibung | Verwendung in DRIVE |
|--------|----------------------|----------------------|
| **listOpenWorkOrders()** | Liste aller **offenen** Werkstattaufträge | `tools/locosoft_soap_client.py` → `list_open_work_orders()` |
| **readWorkOrderDetails(orderNumber)** | Auftragsdetails inkl. Positionen | `read_work_order_details()`; genutzt u. a. in Garantie-SOAP, Gudat-Sync, Mobis Teilebezug |

Konfiguration: `config/locosoft_soap_config.py`; Client: `tools/locosoft_soap_client.py`.

### Erkenntnisse aus Tests (u. a. TAG 195)

- **listOpenWorkOrders()** liefert die offenen Aufträge (z. B. number, status, customer, vehicle).
- **readWorkOrderDetails(orderNumber):** Bei einem **bereits fakturierten** Auftrag (Status `INVOICED_EMPTY`) war das Feld `line` (Positionen) **leer**. Für **offene** Aufträge ist zu erwarten, dass Positionen geliefert werden – wurde im Projekt bisher nicht gezielt getestet.
- Zusätzlich existieren **readLaborInformation** und **readLaborAndPartInformation** (laut SOAP-Test-Doku); Parameter und Rückgabe für Arbeits-/Teilepositionen müssten bei Bedarf aus WSDL/Test ermittelt werden.

### Fazit SOAP

- **Erkennung „welche Aufträge sind offen/geplant“:** ✅ Über **listOpenWorkOrders()** möglich; entspricht konzeptionell der Abfrage auf `orders` mit `has_open_positions = true`.
- **Details pro Auftrag (Positionen, Netto):** Über **readWorkOrderDetails** bei offenen Aufträgen plausibel, aber in DRIVE bisher nur bei bereits fakturierten Aufträgen getestet (dort `line` leer). Für belastbare Umsatz-/Netto-Werte für die Liquiditätsvorschau ist die **PostgreSQL-Quelle** (orders + labours mit `net_price_in_order`) derzeit die sichere Wahl; SOAP könnte bei Bedarf ergänzend oder für Systeme ohne DB-Zugriff genutzt werden.

---

## 3. Empfehlung für Liquiditätsvorschau „Erwartete Einnahmen Werkstatt“

1. **Primär:** Offene/geplante Werkstattaufträge und Beträge aus **Locosoft PostgreSQL** (orders + labours, ggf. parts/invoices) wie in `LIQUIDITAET_ERWARTETE_EINNAHMEN_LOCOSOFT.md` Abschnitt 2 beschrieben auswerten und in die Vorschau einbauen.
2. **Optional:** SOAP **listOpenWorkOrders()** nutzen, wenn eine reine „Liste offener Aufträge“ ohne direkten DB-Zugriff benötigt wird; für Beträge pro Auftrag **readWorkOrderDetails** bei offenen Aufträgen testen oder weiterhin PostgreSQL verwenden.

---

**Erstellt:** 2026-02  
**Referenzen:** `api/werkstatt_data.py` (get_offene_auftraege), `tools/locosoft_soap_client.py`, `config/locosoft_soap_config.py`, `docs/SOAP_TEST_ERGEBNISSE_TAG195.md`, `docs/workstreams/controlling/LIQUIDITAET_ERWARTETE_EINNAHMEN_LOCOSOFT.md`
