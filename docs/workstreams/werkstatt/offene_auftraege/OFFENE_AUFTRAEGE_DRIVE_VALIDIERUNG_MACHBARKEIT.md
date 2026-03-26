# Offene Aufträge im DRIVE – Validierung & Machbarkeit

**Stand:** 2026-02-25  
**Workstream:** werkstatt  
**Kontext:** Serviceassistentin filtert in Locosoft offene Aufträge und legt PDFs im Windows-Sync unter `docs/workstreams/werkstatt/offene_auftraege/` ab (pro Serviceberater, Garantie, Gesamt, Teile bestellt, Teile Rückstand). Soll das Filtern und die Darstellung in DRIVE umgesetzt werden?

---

## 1. Ist-Zustand: PDFs im Sync-Ordner

**Pfad (Windows):** `\\Srvrdb01\...\Server\docs\workstreams\werkstatt\offene_auftraege\`  
**Pfad (Server):** `/mnt/greiner-portal-sync/docs/workstreams/werkstatt/offene_auftraege/`

| Datei | Bedeutung (Annahme) |
|-------|----------------------|
| `alle.pdf` | Alle offenen Aufträge (Gesamt) |
| `Garantie.pdf` | Nur offene Garantieaufträge |
| `Huber.pdf`, `Kraus.pdf`, `Salmansberger.pdf` | Offene Aufträge pro Serviceberater (Name) |
| `Teile bestellt.pdf` | Aufträge mit AVG „Teile bestellt“ (aus Locosoft AVG-Export) |
| `Teile Rückstand.pdf` | Aufträge mit AVG „Teile Rückstand“ (aus Locosoft AVG-Export) |

**Hinweis AVG (Auftragsverzögerungsgrund):** Die Logik für „Teile bestellt“ bzw. „Teile Rückstand“ ergibt sich aus dem Locosoft-**AVG** (Auftragsverzögerungsgrund)-PDF-Export. **Im ersten Schritt** wird AVG / Teile bestellt / Teile Rückstand **nicht** in DRIVE umgesetzt – Fokus Phase 1: Alle / pro Serviceberater / Garantie.

---

## 2. Was DRIVE bereits kann (ohne neue Entwicklung)

### 2.1 Offene Aufträge aus Locosoft – Datenebene

- **`api/werkstatt_data.py`**
  - `WerkstattData.get_offene_auftraege(betrieb, tage_zurueck, nur_offen, limit)`  
  - Liefert offene Aufträge mit **Serviceberater** (`serviceberater_nr`, `serviceberater_name`), Kennzeichen, Kunde, Marke, Vorgabe-AW, etc.  
  - Filter: `has_open_positions = true`, optional `subsidiary`, Zeitfenster.

- **`api/werkstatt_live_api.py`**
  - `get_alle_offene_auftraege(cur_loco, subsidiary, serviceberater_nr, min_alter_tage)` (TAG 200)  
  - **Filter nach Serviceberater-Nummer** bereits vorhanden.  
  - Verwendung u. a. im „Heute“-Endpoint und für CSV-Validierung.

- **API:** `GET /api/werkstatt/live/auftraege?betrieb=…&tage_zurueck=…&nur_offen=…`  
  - Nutzt `WerkstattData.get_offene_auftraege()`; **kein** Query-Parameter für „nur Garantie“ oder „nur Serviceberater XY“.

- **Route:** `/werkstatt/live` → Template `werkstatt_live.html` („Werkstatt Live-Übersicht (offene Aufträge)“).

**Fazit:**  
- **Gesamt (alle offen)** und **pro Serviceberater (nach Nr.)** sind datenseitig abdeckbar; die Live-API hat heute keinen expliziten `serviceberater_nr`-Parameter am HTTP-Endpoint, die interne Funktion schon.  
- **Garantie** ist in einem **eigenen** Modul abgebildet (s. unten).

### 2.2 Garantie – eigenes Modul

- **`api/garantie_auftraege_api.py`**
  - `get_offene_garantieauftraege()`: offene Aufträge, die als **Garantie** erkannt werden (`charge_type = 60` ODER `labour_type IN ('G','GS')` ODER `invoice_type = 6`).  
  - API: `GET /api/garantie/auftraege/offen` (Query: `marke`, `fertig`).  
  - Keine gemeinsame „Offene Aufträge“-Seite mit Werkstatt-Live; Garantie ist eigene Oberfläche/Route.

**Fazit:**  
- **Garantie-Filter** ist in DRIVE fachlich vorhanden; für eine **einheitliche** „Offene Aufträge“-Sicht müsste man entweder die bestehende Garantie-API in eine gemeinsame Sicht integrieren oder eine neue Aggregation bauen.

### 2.3 Andere Workstreams

- **Controlling:** „Offene Posten“ = **Fahrzeugverkauf/Debitoren** (OPOS, `loco_journal_accountings`), nicht Werkstatt-Aufträge.  
- **Verkauf:** `verkauf_api` nutzt `has_open_positions` für **interne Werkstattaufträge zu VINs** (z. B. Ersatzwagen-Kontext), keine Listen nach Serviceberater/Garantie.  
- **Teile-Lager:** Teilebestellungen, Renner/Penner etc. – keine Abbildung derselben „Offene Aufträge“-Filter wie in der Werkstatt.

**Fazit:**  
- Es gibt **keine** andere Workstream-Implementierung, die genau die gewünschte Werkstatt-„Offene Aufträge“-Liste (Serviceberater, Garantie, Gesamt, ggf. Teile) als eigenes Modul abbildet.  
- Die **Bausteine** (Locosoft-Abfragen, Garantie-Logik, Serviceberater-Zuordnung) liegen im Werkstatt-/Garantie-Bereich.

---

## 3. Machbarkeit: Filter im DRIVE abbilden

| Sicht | Datenquelle Locosoft | In DRIVE vorhanden? | Aufwand (nur Bewertung) |
|-------|----------------------|---------------------|--------------------------|
| **Alle (Gesamt)** | `orders.has_open_positions = true` + ggf. Betrieb/Zeitfenster | ✅ Ja (`get_offene_auftraege`, `get_alle_offene_auftraege`) | – |
| **Pro Serviceberater** | wie oben + `order_taking_employee_no = …` | ✅ Ja (intern `serviceberater_nr`); API-Parameter ggf. ergänzen | Gering |
| **Nur Garantie** | wie Garantie-API: charge_type 60, labour_type G/GS, invoice_type 6 | ✅ Ja (`get_offene_garantieauftraege`) | – |
| **Teile bestellt** | Locosoft **AVG** (Auftragsverzögerungsgrund)-Export | ❌ **Erster Schritt: nicht** | Später (AVG-Logik) |
| **Teile Rückstand** | Locosoft **AVG** (Auftragsverzögerungsgrund)-Export | ❌ **Erster Schritt: nicht** | Später (AVG-Logik) |

- **Serviceberater-Namen** (Huber, Kraus, Salmansberger): In Locosoft kommt der Name aus `employees_history.name` bzw. Anzeigename; Zuordnung zu `order_taking_employee_no` ist vorhanden. Filter „pro Serviceberater“ kann über **Mitarbeiternummer** umgesetzt werden; Anzeige „wie PDF“ (z. B. „Huber“) über bestehende Namensfelder.

---

## 4. Validierung – offene Punkte

1. **Exakte Filterlogik der PDFs**  
   Mit Serviceassistentin/Serviceleiter klären:  
   - Welche Locosoft-Reporte/Filter liegen den PDFs zugrunde (für Alle / Garantie / Serviceberater)?  
   - **Teile bestellt / Teile Rückstand:** Logik kommt aus dem Locosoft-**AVG** (Auftragsverzögerungsgrund)-Export; **nicht** im ersten Schritt in DRIVE.

2. **Zeitfenster / Betrieb**  
   - Welches Zeitfenster (z. B. letzte 90 Tage wie in `get_alle_offene_auftraege`) und welche Betriebe sollen für „Offene Aufträge“ gelten?  
   - Soll es mit der bestehenden Logik (z. B. 90 Tage) übereinstimmen?

3. **PDF-Export aus DRIVE**  
   - Soll DRIVE die gefilterten Listen **als PDF** exportieren (Ersatz für manuellen Locosoft-Export)?  
   - Das wäre ein separater Aufwand (Layout, Druck/PDF-Generierung); die **Filter** sind unabhängig davon machbar.

4. **UI-Ziel**  
   - Reicht eine **Portal-Seite** „Offene Aufträge“ mit Dropdown (Alle / Garantie / Serviceberater XY) und Tabelle, **ohne** PDF?  
   - Oder explizit „wie die PDFs“ inkl. Export?

---

## 5. Kurzbewertung

- **Validierung:**  
  - **Gesamt** und **pro Serviceberater** und **Garantie** sind in DRIVE datenseitig abbildbar; Garantie lebt in der Garantie-API.  
  - **Teile bestellt / Teile Rückstand:** Logik stammt aus dem Locosoft-**AVG** (Auftragsverzögerungsgrund)-Export; **im ersten Schritt aus dem Scope** – keine AVG-Umsetzung in Phase 1.

- **Machbarkeit:**  
  - **Ja** für: Offene Aufträge filtern und im DRIVE anzeigen (Alle, pro Serviceberater, Garantie), auf Basis bestehender APIs und Locosoft-Zugriffe.  
  - **Ergänzungen:** API-Parameter `serviceberater_nr` (und ggf. `nur_garantie`) für `/api/werkstatt/live/auftraege` bzw. eine gemeinsame „Offene Aufträge“-Seite mit Filter-Dropdown.  
  - **Optional:** PDF-Export; Aufwand abhängig von gewünschtem Layout.

- **Andere Workstreams:**  
  - Kein bestehendes Modul, das dieselbe „Offene Aufträge (Werkstatt)“-Funktion abdeckt; Controlling „Offene Posten“ ist ein anderes Thema (Fahrzeugverkauf/Debitoren).

---

## 6. Nächste Schritte (Empfehlung)

1. **Fachlich:** Mit Serviceassistentin/Serviceleiter die Filterlogik für **Alle / Garantie / Serviceberater** abstimmen (AVG/Teile bestellt/Rückstand bewusst **nicht** in Phase 1).  
2. **Entscheidung:** Reine Portal-Ansicht mit Filter vs. zusätzlich PDF-Export.  
3. **Technisch (nach Freigabe) – erster Schritt:**  
   - Gemeinsame Seite „Offene Aufträge“ (oder Erweiterung von `/werkstatt/live`) mit Filter: **Alle / Garantie / Serviceberater** (Dropdown).  
   - API erweitern: z. B. `serviceberater_nr`, `nur_garantie` an bestehende Endpoints anbinden.  
   - **AVG (Teile bestellt / Teile Rückstand)** erst in einem späteren Schritt, sofern gewünscht (AVG-Logik aus Locosoft).

---

## 7. Mockup: Einbauorte & kompakte Darstellung (2026-02-25)

- **Mein Bereich** (`/sb/mein-bereich`): Offene Aufträge für den eingeloggten SB; KPIs kompakt nach oben; neuer Block „Meine offenen Aufträge“ (Anzahl + Link).
- **Serviceberater Controlling** (`/aftersales/serviceberater/`): KPIs kompakt oben; Serviceberater in **Tabelle** statt großer Karten untereinander; Spalte **Offene Aufträge** (Anzahl, klickbar → Werkstatt Live gefiltert).
- Badges einheitlich kompakt (z. B. `.badge-mini`).

**Datei:** `offene_auftraege/MOCKUP_offene_auftraege_einbau.html` (im Browser öffnen).

---

*Dieses Dokument dient der Validierung und Machbarkeit; es wurde bewusst noch kein Code geändert.*
