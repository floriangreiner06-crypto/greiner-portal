# Verkäufer-Zielplanung Kalenderjahr – Konzeptvorschlag & Machbarkeit

**Stand:** 2026-02  
**Auslöser:** Ziele der Verkäufer auf Kalenderjahr (nicht GJ), da Hersteller-NW-Ziele ebenfalls Kalenderjahr. Gesamtziele 2026: 630 NW, 900 GW; Verteilung nach historischer Verkaufsleistung 2025.

---

## 1. Zielbild

- **Planungshorizont:** Kalenderjahr (z. B. 2026).
- **Konzernziele:** 630 NW, 900 GW.
- **Abzug Handelsgeschäft:** Verkäufe durch Verkaufsleitung (Anton) und Filialleitung (Rolf) werden als „Handelsgeschäft“ aus dem Verteilungspool herausgenommen (nicht an „normale“ Verkäufer verteilt).
- **Verteilung:** Der verbleibende Ziel-Pool (630 − NW_Handelsgeschäft, 900 − GW_Handelsgeschäft) wird auf die übrigen Verkäufer nach **historischer Leistung 2025** (Anteil NW/GW pro Verkäufer) verteilt.

---

## 2. Machbarkeit – Datenbasis Locosoft

### 2.1 Verkäufe nach Verkäufer (2025)

**Quelle:** Locosoft-Tabelle `dealer_vehicles`.

| Spalte | Bedeutung |
|--------|-----------|
| `out_invoice_date` | Rechnungsdatum → Filter Kalenderjahr 2025 |
| `out_salesman_number_1` | Verkäufer-Nr. (Hauptverkäufer) |
| `out_salesman_number_2` | optional zweiter Verkäufer |
| `dealer_vehicle_type` | N, V = Neuwagen; D, G = Gebrauchtwagen |
| `out_sale_price` | Umsatz (optional für Gewichtung) |
| `out_subsidiary` | Standort (1=DEG, 2=HYU, 3=LAN) |

**Bereits vorhanden:** Im Projekt existiert die Logik bereits:
- **`api/budget_api.py`** – Route `GET /api/budget/verkaufer/<jahr>`: liefert pro Kalenderjahr je Verkäufer (`out_salesman_number_1`) Stück und Umsatz getrennt nach NW und GW (aus `dealer_vehicles`, `dealer_vehicle_type IN ('N','V','D','G')`).  
→ **Verwendung:** Diese Abfrage (oder eine angepasste Variante) als Basis für „Verkäufe 2025 pro Verkäufer (NW/GW)“ nutzen.

**Fazit:** Verkäufe nach Verkäufer für 2025 aus Locosoft sind **machbar** und teils schon angebunden.

### 2.2 Zuordnung Namen (Anton, Rolf)

**Quelle:** Locosoft `employees_history` (oder vergleichbare Mitarbeiter-Tabelle) mit `employee_number`, `first_name`, `family_name`; Join über `out_salesman_number_1 = employee_number`.

- **Anton (Verkaufsleitung)** und **Rolf (Filialleitung)** können über Namen oder eine feste Liste von Mitarbeiternummern („Handelsgeschäft“) identifiziert werden.
- **Empfehlung:** Konfigurierbare Liste (z. B. Locosoft-Mitarbeiternummern oder Namen) für „Handelsgeschäft / von Zielverteilung ausnehmen“, damit Änderungen (Rollen, neue Personen) ohne Code-Anpassung möglich sind.

**Fazit:** Identifikation von Anton/Rolf über Locosoft-Mitarbeiterdaten ist **machbar**; sauberer mit konfigurierbarer Liste.

### 2.3 Abgrenzung Handelsgeschäft

- **Option A:** Alle Verkäufe von Anton und Rolf in 2025 als Maß für „Handelsgeschäft 2025“. Für 2026: Plan Handelsgeschäft = diese Stückzahlen (oder leicht angepasst), Rest = 630 − NW_Handel, 900 − GW_Handel zur Verteilung.
- **Option B:** Fester Plan für Handelsgeschäft 2026 (z. B. X NW, Y GW); Rest verteilen.

**Empfehlung:** Option A für die erste Version (2025-Ist als Plan Handelsgeschäft 2026), optional später Option B (manuelle Festlegung).

---

## 3. Vorschlag Ablauf (Logik)

1. **Verkäufe 2025 aus Locosoft**
   - Pro Verkäufer (über `out_salesman_number_1`): NW-Stück, GW-Stück (ggf. Umsatz für spätere Erweiterungen).
   - Gesamt 2025: NW_gesamt, GW_gesamt.

2. **Handelsgeschäft abziehen**
   - Verkäufer „Anton“ und „Rolf“ über Mitarbeiternummer(n) oder Namen identifizieren.
   - NW_Handel_2025 = NW von Anton + Rolf; GW_Handel_2025 = GW von Anton + Rolf.
   - Pool für Verteilung:  
     - NW_Pool = 630 − NW_Handel_Plan (z. B. NW_Handel_Plan = NW_Handel_2025).  
     - GW_Pool = 900 − GW_Handel_Plan (z. B. GW_Handel_Plan = GW_Handel_2025).

3. **Verteilung nach historischer Leistung**
   - Nur Verkäufer, die **nicht** als Handelsgeschäft markiert sind.
   - Anteil_NW_VK = (NW_2025 des VK) / (NW_2025_gesamt − NW_Handel_2025), analog GW.
   - Ziel_NW_2026_VK = Anteil_NW_VK × NW_Pool, Ziel_GW_2026_VK = Anteil_GW_VK × GW_Pool.
   - Rundung: Rest-Stück so verteilen, dass Summe exakt 630 NW / 900 GW (bzw. Pool + Handelsgeschäft) ergibt.

4. **Ausgabe**
   - Pro Verkäufer: Name, Ziel NW 2026, Ziel GW 2026 (evtl. Monats- oder Quartalswerte als Ableitung).
   - Handelsgeschäft: Anton, Rolf mit ihren geplanten Stückzahlen (NW/GW) für 2026.

---

## 4. Technische Umsetzung (grober Fahrplan)

| Schritt | Inhalt | Aufwand (grobe Schätzung) |
|---------|--------|----------------------------|
| 1 | Abfrage „Verkäufe 2025 pro Verkäufer (NW/GW)“ aus Locosoft (evtl. Erweiterung von `budget_api.verkaufer_stats` oder neues Modul) inkl. Namen über `employees_history` | klein |
| 2 | Konfiguration „Handelsgeschäft“ (z. B. Liste Mitarbeiternummern oder Namen: Anton, Rolf) – Tabelle/Config in DRIVE oder .env | klein |
| 3 | Berechnung: Pool = 630/900 minus Handelsgeschäft; Verteilung nach 2025-Anteil; Rundungslogik | klein |
| 4 | Speicherung/Anzeige: Ziele 2026 pro Verkäufer (neue Tabelle `verkaufer_ziele` o. ä. mit Kalenderjahr, Verkäufer-ID, ziel_nw, ziel_gw) + kleines UI oder Export (CSV/Excel) | mittel |
| 5 | Optional: Anbindung an bestehende Planung/Reporting (z. B. KST-Ziele, Budget) | nach Bedarf |

---

## 5. Pool Handelsgeschäft (festgelegt 2026-02)

**Mitarbeiternummern:** 9001 (Greiner, Florian – Geschäftsleitung), 1003 (Sterr, Rolf – Filialleitung), 2000 (Süß, Anton – Verkaufsleitung).

→ Details und 2025-Referenz: `docs/workstreams/verkauf/VERKAEUFER_HANDELSGESCHAEFT_POOL.md`

---

## 6. Offene Punkte / Klärung

1. ~~**Anton / Rolf:**~~ Erledigt: Pool = 9001, 1003, 2000.
2. **Handelsgeschäft 2026:** Soll der Plan für 9001/1003/2000 genau den 2025-Verkäufen entsprechen oder manuell vorgegeben werden?
3. **Zweitverkäufer:** Soll `out_salesman_number_2` einbezogen werden (z. B. 50/50 Aufteilung), oder reicht Verteilung nur nach `out_salesman_number_1`?
4. **Standorte:** Sollen Ziele standortbezogen (DEG/HYU/LAN) geplant werden oder nur konzernweit pro Verkäufer?
5. **Verkäufer ohne 2025-Verkäufe:** Neue Verkäufer oder solche ohne Absatz 2025 – Sollwert 0 oder Mindestziel/Quote?

---

## 7. Kurzfassung Machbarkeit

- **Daten:** Verkäufe 2025 nach Verkäufer (NW/GW) aus Locosoft `dealer_vehicles` sind vorhanden; bestehende Route in `budget_api` kann genutzt/erweitert werden.
- **Handelsgeschäft:** Abzug von Anton/Rolf über Mitarbeiternummern/Namen aus Locosoft ist umsetzbar; konfigurierbare Liste empfohlen.
- **Verteilung:** Formel „Pool nach Anteilen 2025“ ist einfach umsetzbar; Rundung und Sonderfälle (neue Verkäufer, 0-Stück 2025) müssen einmalig festgelegt werden.

**Fazit:** Konzept ist **machbar**; nächster sinnvoller Schritt ist die Klärung der offenen Punkte (insb. Anton/Rolf-Identifikation und Handelsgeschäft-Plan 2026) und danach die technische Umsetzung (Schritte 1–4).
