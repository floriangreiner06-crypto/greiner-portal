# Provisionsregeln – System (bekannt & offen)

**Zweck:** Eine zentrale Stelle für alle Provisionsregeln. Hier ergänzen wir bekannte Regeln und tragen offene Punkte ein; DRIVE-Skripte/API richten sich danach. So können wir vergleichen (z. B. Einzelberechnung im Sync) und schrittweise die Abweichungen zur echten Abrechnung klären.

**Stand:** 2026-02-17

---

## 1. Wo steht was

| Was | Wo |
|-----|-----|
| Detaillierte Logik aus Excel | `PROVISIONSLOGIK_AUS_EXCEL.md` (in diesem Ordner) |
| **Abgleich PDF/Excel, BE2-Formel, J60/J61** | **`PROVISION_ABGLEICH_PDF_EXCEL_STELLUNGNAHME.md`** |
| L744PR / Filter / Datenherkunft | `L744PR_ABFRAGE_ABGLEICH.md`, `ANALYSE_DATEN_UND_ABRECHNUNGEN.md` |
| **Bekannte + offene Regeln** | **Dieses Dokument** |
| Einzelberechnung zum Vergleichen | `Einzelberechnung_Kraus_Jan2026.csv` + `_Report.txt` (nach Lauf mit `--sync`) |

---

## 2. Bekannte Regeln (aktuell in DRIVE umgesetzt)

- **Zeitraum:** Rechnungsdatum (`out_invoice_date`) im Abrechnungsmonat.
- **Verkäufer:** VKB = `salesman_number` (z. B. Rafael Kraus = 2007).
- **Mapping out_sale_type → Block:**
  - **F** → Block I Neuwagen  
  - **L** → Block II Testwagen/VFW (1 %, min 103 €, max **300 €**)  
  - **B** → Block III Gebrauchtwagen (1 %, min 103 €, max **500 €**)  
  - **T/V** (falls in DB): aktuell wie Block II (1 %, min 103 €, max 300 €); Abgrenzung zu L offen.
- **Block I (Neuwagen):** DB × 12 % + 50 €/Stück (max 15 Stück).
- **Block II (VFW):** Rg.Netto × 1 %, min 103 €, max 300 € (Optionen J54).
- **Block III (GW):** Rg.Netto × 1 %, min 103 €, max 500 € (Optionen J53).
- **Block IV (GW aus Bestand):** Formel umgesetzt: BE II = (DB×J60)+J61, Provision = (DB−BE II)×12 %. **J60/J61** müssen aus Excel Optionen (Zellen J60, J61) in `provision_config.param_j60` / `param_j61` eingetragen werden; sonst Abweichung zum PDF. „GW aus Bestand“ = Verkäufe mit aktivem Einkäufer (Verkaufsmannschaft); DB2 zusätzlich zur Umsatzprovision.

---

## 3. Offen / zu bestätigen

Diese Punkte sollen hier eingetragen und bei Klärung abgehakt werden.

1. **J60, J61 (GW aus Bestand):** Werte aus Optionen-Blatt? Formel: `(DB × J60) + J61` abziehen, dann 12 % auf Rest.
2. **„GW aus Bestand“:** Welche Zeilen gehören dazu? (Locosoft-Kennung, Spalte, oder eigene Liste?)
3. **L vs. B vs. T/V:** In Locosoft/DB: Welche `out_sale_type`-Werte gibt es genau? Ist **L** immer VFW und **B** immer GW? T/V getrennt oder wie L?
4. **Anzahl Fahrzeuge:** Kraus Jan 2026: DB liefert 15 (6× L, 9× B), PDF 14 (7 VFW + 7 GW). Welches Fahrzeug weicht (VIN/Rg-Nr.) oder welcher Filter fehlt?
5. **Max 205 € vs. 500 € / 300 €:** In Excel-Strings teils „max. 205 €“, in Formeln 500 € (GW) bzw. 300 € (VFW) – was ist fachlich gültig?
6. **Rg-Typ:** Nur **H** (Hauptrechnung), **Z** (Zusatz/Storno) ausschließen oder verrechnen?
7. **„Nicht importieren wenn <“:** Schwellwert (Optionen n_nichtimportieren) – welcher Wert, welche Spalte?
8. **Verkaufsleiter Anton Süß:** Eigenes System – getrennt halten; keine Mischung mit Verkäufer-Provision.

### 3.1 Alternative DB2-Regel nach Art des Geschäfts – **noch nicht definiert**

- **Sachverhalt:** Für Fahrzeuge, die vom Verkaufsteam angetauscht wurden (DB2-Fall, Einkäufer = antauschender VB), gilt je nach **Art des Geschäftes** eine andere Regel:
  - **Standard (aktuell in DRIVE):** (DB − BE II) × 12 % (Block IV).
  - **Alternative für eine bestimmte Art des Geschäftes:** **2 % Erlösprovision** (Bemessungsgrundlage: Erlös/Rg.Netto, nicht DB − BE II), mit **maximaler Grenze** (konkreter Max-Betrag noch zu definieren).
- Die Unterscheidung erfolgt nach der **Art des Geschäftes**, nicht nach einzelnen Personen oder einzelnen Geschäften.
- **Aktuell in DRIVE:** Die alternative Regel (2 % Erlös, max) ist **nicht** umgesetzt. Es gilt einheitlich die Block-IV-Formel für alle DB2-Fälle.
- **Offen:**  
  - Wann genau gilt die alternative Regel? (Welche Kennung/Feld definiert „diese Art des Geschäfts“?)  
  - Konkreter Max-Betrag für die 2‑%‑Erlösprovision.  
  - Gilt die alternative Regel nur für die **Einkäufer**-Provision (DB2) oder auch für den Verkäufer-Anteil?

---

## 4. Einzelberechnung zum Vergleichen (Windows-Sync)

Damit ihr die DRIVE-Berechnung mit der echten Abrechnung vergleichen könnt:

- **CSV:** `Einzelberechnung_Kraus_Jan2026.csv` (Semikolon-getrennt, UTF-8 mit BOM). Spalten: Block, Typ_Locosoft, VIN, Rechnungsnummer, Fahrzeug, Netto_VK, Provision_EUR.
- **Report:** `Einzelberechnung_Kraus_Jan2026_Report.txt` – gleicher Inhalt wie Konsolenausgabe (Summen, Vergleich mit PDF).

Erzeugen (auf dem Server):

```bash
cd /opt/greiner-portal
python3 scripts/provisions_berechnung_kraus_jan2026.py --sync
```

Dateien liegen dann unter:

- **Windows:** `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\verkauf\provisionsabrechnung\`
- **Server:** `/mnt/greiner-portal-sync/docs/workstreams/verkauf/provisionsabrechnung/`

---

## 5. Regeln anpassen

- **Neue/geänderte Regeln:** Hier in Abschnitt 2 eintragen (und ggf. in PROVISIONSLOGIK_AUS_EXCEL.md vermerken).
- **Offene Punkte geklärt:** In Abschnitt 3 abhaken oder streichen, Ergebnis in Abschnitt 2 übernehmen.
- **Code:** Skript `scripts/provisions_berechnung_kraus_jan2026.py` und spätere API/SSOT an diese Regeln anpassen.

Wenn ihr Werte aus dem Excel (z. B. J60, J61, Max 205 vs. 300/500) oder die genaue Zuordnung L/B/T/V bestätigt, können wir die Logik 1:1 in DRIVE übernehmen und die Abweichung Kraus Jan 2026 gezielt nachvollziehen.
