# Stichprobe Provisionsabrechnung: Roland Schmid, Januar 2026

**Stand:** 2026-02  
**Zweck:** Abgleich DRIVE vs. PDF/Excel – Positionen und Summen für Roland, Monat 01/2026.  
**VKB Roland Schmid:** `locosoft_id = 2006`.

---

## 1. DRIVE-Berechnung (Live) – Summen

| Kategorie | Summe (€) | Anmerkung |
|-----------|-----------|-----------|
| I. Neuwagen | 0,00 | 0 Stück |
| II. Testwagen/VFW | 689,92 | 3 Positionen |
| III. Gebrauchtwagen | 1 002,17 | 4 Positionen |
| IV. GW aus Bestand | 152,46 | 1 Position (DB2) |
| **Summe gesamt** | **1 844,55** | |

Keine Neuwagen-Stückprämie (0 Stück).

---

## 2. DRIVE – Positionen im Detail

### II. Testwagen/VFW (Rg.Netto × 1 %, min 103 €, max 300 € in DRIVE)

| Rechnungsnr. | VIN (Auszug) | Rg.Netto (€) | Provision (€) |
|--------------|--------------|--------------|---------------|
| 2101238 | TMAJB8117S | 36 694,17 | 300,00 (Cap) |
| 2101233 | KMHB35113T | 22 568,53 | 225,69 |
| 1101185 | LFZ73AJ58S | 16 422,95 | 164,23 |

**Summe Kat. II:** 689,92 €

### III. Gebrauchtwagen (Rg.Netto × 1 %, min 103 €, max 500 €)

| Rechnungsnr. | VIN (Auszug) | Rg.Netto (€) | Provision (€) |
|--------------|--------------|--------------|---------------|
| 2101188 | KMHYC81A4S | 37 983,20 | 379,83 |
| 2101193 | TMAJD81BHM | 25 224,63 | 252,25 |
| 2101184 | TMAH181D9S | 22 722,58 | 227,23 |
| 2101191 | NLHBN51GAP | 14 285,71 | 142,86 |

**Summe Kat. III:** 1 002,17 €

### IV. GW aus Bestand (DB2 – Formel mit J60/J61)

| Rechnungsnr. | VIN (Auszug) | DB (€) | VK-Kosten BE II (€) | Basis (DB − BE II) | Provision 12 % (€) |
|--------------|--------------|--------|----------------------|---------------------|---------------------|
| 2101184 | TMAH181D9S | 1 460,08 | 189,60 | 1 270,48 | 152,46 |

- **Formel:** VK-Kosten = ROUND(DB × 0,01 + 175; 2) = 189,60 €; Basis = 1 460,08 − 189,60 = 1 270,48 €; Provision = 1 270,48 × 0,12 = 152,46 €.
- Dieselbe Rechnung 2101184 erscheint in **Kat. III** (Umsatzprovision 227,23 €) und **Kat. IV** (DB2 152,46 €), weil Roland hier Verkäufer und Einkäufer ist (antauschender VB).

**Summe Kat. IV:** 152,46 €

---

## 3. Formelprüfung

- **Kat. III (2101188):** 37 983,20 × 1 % = 379,83 € (zwischen 103 und 500) → DRIVE 379,83 € ✓  
- **Kat. IV (2101184):** DB 1 460,08 → BE II = 189,60 € → Basis 1 270,48 € → 12 % = 152,46 € → DRIVE 152,46 € ✓  

Die in PROVISION_ABGLEICH_PDF_EXCEL_STELLUNGNAHME.md beschriebene Formel (J60 = 0,01, J61 = 175) wird in DRIVE korrekt angewendet.

---

## 4. Abgleich mit PDF/Excel

- **Excel-Datei** `Provisionsabrechnung_V0.11.xlsm` zeigt aktuell **Juli 2025** und Verkäufer **Penn, Michael** (VKB 2002). Für einen direkten Abgleich „Roland Januar“ müsste im Excel:
  - der **Abrechnungsmonat** auf **Januar 2026** gestellt werden,
  - ein **Datenimport** (CSV mit Verkäufen 01/2026) durchgeführt werden,
  - der **Verkäufer** auf **Schmid, Roland** (2006) gestellt werden.
- Anschließend können die **Rechnungsnummern**, **Rg.Netto/DB** und **Provisionen** aus dem Blatt **Fahrzeugverkaeufe** (und die Summen aus **Provisionabrechnung**) mit den obigen DRIVE-Tabellen verglichen werden.
- **PDF:** Wenn ein offizielles Provisions-PDF für Roland Januar 2026 vorliegt, Rechnungsnummern und Beträge zeilenweise mit Abschnitt 2 abgleichen.

---

## 5. Datenherkunft DRIVE

- **Berechnung:** `api.provision_service.berechne_live_provision(2006, '2026-01')`.
- **Rohdaten:** Tabelle `sales` (Filter: `salesman_number = 2006`, `out_invoice_date` im Januar 2026).
- **Config:** `provision_config` (u. a. param_j60 = 0,01, param_j61 = 175 für IV_gw_bestand).
