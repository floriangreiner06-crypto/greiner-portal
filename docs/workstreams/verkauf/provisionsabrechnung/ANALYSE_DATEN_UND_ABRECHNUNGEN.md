# Analyse: Rohdaten, Excel-Tool und Abrechnungs-PDFs

**Stand:** 2026-02-17 | Workstream: verkauf

---

## 1. Überblick Ablauf (heute manuell)

1. **Locosoft:** Export „ausgelieferte Fahrzeuge“ (Rechnungen/Auslieferungen) → **eine CSV pro Monat** (z. B. `0126.csv`, `0625.csv`).
2. **Excel-Tool** `Provisionsabrechnung_V0.11.xlsm`: Lädt CSV, **filtert und sortiert**, berechnet Provisionen.
3. **Output:**
   - **Pro Verkäufer:** eine **PDF-Einzelabrechnung** → wird **manuell an den jeweiligen Verkäufer versendet**.
   - **Für Lohnbuchhaltung:** Sammel-PDFs (Kürzel AS, DF, EP, FP, ML, MP, RK, RS ggf. MP ZEP).
   - **Verkaufsleiter:** separates System (Anton Süß) – eigene XLSX/PDF, andere Logik. Für Beispiele/Tests der Verkäufer-Logik: Kraus Rafael, Schmid Roland.

---

## 2. Rohdaten (CSV/Excel aus Locosoft)

### 2.1 Herkunft: Locosoft L744PR

- Die CSV/Excel-Dateien sind **Original-Exporte aus Locosoft**, Report **L744PR: Fahrzeug Verkauf-Analyse & Verkauf-Nachweis**.
- Funktion im Report: **„Verkaufsnachweisliste drucken“** mit Option **„Ausgabe als Microsoft® Excel ® Blatt“**.
- **Filter im Locosoft-Dialog:** Zeitraum nach **Rechnungsdatum** (z. B. 01.01.26–31.01.26 für Januar), Verkaufsberater (z. B. 1003–9001), Fahrzeugart/Kom-Nr. (z. B. D–V), verkaufender Betrieb usw. Es gibt **keinen sichtbaren Filter „Leistungsdatum“** im Report-Dialog – der Monatsfilter ist das Rechnungsdatum.
- „Leistungsdatum“ (Spalte C) ist eine **Spalte im Export**, nicht das Filterkriterium in L744PR.

### 2.2 Wo liegen die Dateien?

- **Monats-CSVs/Excel** im Ordner `provisionsabrechnung/`:  
  `0126.csv`, `0126.xls`, `0625.csv`, … (Format MMYY bzw. MYY).
- Pro Monat typisch **ca. 90–170 Zeilen** (Rechnungspositionen/Fahrzeuge); Trennzeichen **Tabulator**, Dezimaltrenner **Komma**, Datum **TT.MM.JJJJ**.

### 2.3 Wichtige Spalten (für Filter/Provisionslogik)

| Spalte | Bedeutung (aus Kopfzeile/Stichprobe) | Beispielwerte |
|--------|--------------------------------------|----------------|
| **Rg-Datum** | Rechnungsdatum | 02.01.2026 |
| **Leistungsdatum** | Leistungsdatum | 02.01.2026 |
| **verk. Betrieb** | Verkaufs-Betrieb (Standort) | 1, 2, 3 (DEG, HYU, LAN) |
| **verk. VKB** | Verkäufer-Kennung (VKB) | 2007, 2006, 2005, 9001, 1003, 2001, … |
| **Fz.-Art** | Fahrzeugart | D, G, N, V, T (z. B. D=Direkt, G=Gebraucht, N=Neuwagen, …) |
| **Rg-Typ** | Rechnungstyp | H (Haupt), Z (Zusatz/Storno) |
| **Buchungsstatus** | Buchungsstatus | Eingebucht, Umgebucht |
| **EK-Betrieb** | Einkaufs-Betrieb (Standort) | 1, 2, 3 |
| **Kostenträger** | Kostenträger (evtl. für Sammel-PDFs) | (Werte aus Excel/Export prüfen) |
| Rg.Netto, Rg.Brutto, Deckungsbeitrag, DB % | Beträge / DB | für Provisionsberechnung |
| Fahrgestellnr., Modell-Bez., Käufer-Name, … | Fahrzeug-/Kundeninfos | für Abrechnungsinhalt |

**Vermutung:** Die **Zuordnung Verkäufer ↔ PDF** läuft über **verk. VKB** (oder Kombination mit Betrieb). Die Kürzel **AS, DF, EP, FP, ML, MP, RK, RS** sind vermutlich Kostenträger- oder Standort-/Abteilungsbezeichnungen für die Lohnbuchhaltung; genaue Definition sollte aus dem Excel-Tool oder Locosoft-Stammdaten kommen.

### 2.4 Typische Filter (zu verifizieren)

- **Zeitraum:** Leistungsdatum oder Rg-Datum im Abrechnungsmonat.
- **Rg-Typ = H** (nur Hauptrechnungen, keine Zusatz-/Stornoposten)?
- **Buchungsstatus** (z. B. nur „Eingebucht“ oder auch „Umgebucht“)?
- **Fz.-Art:** welche Arten zählen zur Provision (z. B. nur bestimmte Neuwagen/Direktverkäufe)?

Exakte Regeln müssen aus dem **Excel-Tool (Makros/Filter)** oder von euch übernommen werden.

---

## 3. Ordnerstruktur (Monatsunterordner)

- Pro Abrechnungsmonat ein Ordner: **`MM_YY`** (z. B. `01_26`, `06_25`, `12_25`).
- Zeitraum in den Daten: **10_24** bis **01_26** (Oktober 2024 – Januar 2026).

In jedem Monatsordner liegen:

- **Verkäufer-PDFs:** Einzelabrechnungen, **manuell an den jeweiligen Verkäufer zu versenden**.
- **Sammel-PDFs für Lohnbuchhaltung:** AS, DF, EP, FP, ML, MP, RK, RS (teilweise **MP ZEP**, **RK Nachzahlung**, **RK TW Prämie**).
- **Verkaufsleiter:** `Süß Anton_MMYY.xlsx` und ggf. `Kopie von Süß Anton_…` (eigenes Provisionssystem).
- Gelegentlich weitere Arbeitslisten (z. B. **Kopie von GW-Ablieferungsliste.xlsx**).

---

## 4. PDFs in den Unterordnern

### 4.1 Verkäufer-Einzelabrechnungen (Versand an Verkäufer)

- **Namensschema:**  
  `Nachname, Vorname_Monat Jahr_YYYYMMDD.pdf`  
  (teilweise ohne Leerzeichen nach dem Komma: `Nachname,Vorname_…`)
- **Beispiele (Test-Verkäufer):**  
  `Kraus, Rafael_Jan 2026_20260202.pdf`,  
  `Schmid, Roland_Jun 2025_20250630.pdf`  
  (weitere: Fialkowski, Löbel, Pellkofer, Penn, Punzmann.)
- **Bedeutung:** Eine PDF pro Verkäufer und Monat = **monatliche Provisionsabrechnung**, die ihr **manuell an den jeweiligen Verkäufer versendet**.

**Vorkommende Verkäufer (aus Dateinamen):**

- Fialkowski Daniel  
- **Kraus Rafael** (Beispiel/Test)  
- Löbel Marius  
- Pellkofer Florian  
- Penn Michael  
- Punzmann Edeltraud  
- **Schmid Roland** (Beispiel/Test)  

(Plus ggf. weitere in älteren Monaten. Verkaufsleiter Anton Süß: eigenes System, siehe Abschnitt Verkaufsleiter.)

### 4.2 Sammel-PDFs für Lohnbuchhaltung

- **Kürzel-PDFs** (immer wiederkehrend):  
  **AS.pdf**, **DF.pdf**, **EP.pdf**, **FP.pdf**, **ML.pdf**, **MP.pdf**, **RK.pdf**, **RS.pdf**
- **Sonderformen:**  
  **MP ZEP.pdf**, **RK Nachzahlung.pdf**, **RK TW Prämie.pdf**
- **Bedeutung:** Aggregationen (z. B. pro Kostenträger/Standort/Abteilung) für die **Lohnbuchhaltung**, nicht für den Einzelversand an Verkäufer.

### 4.3 Verkaufsleiter und Sonderfälle

- **Anton Süß (Verkaufsleiter):**  
  - `Süß Anton_MMYY.xlsx` (Arbeitsmappe), vereinzelt `Süß Anton_0425.pdf`.  
  - Eigenes **Provisionssystem Verkaufsleiter**, getrennt von der Verkäufer-Provisionslogik. Für Verkäufer-Tests/Beispiele siehe Kraus Rafael, Schmid Roland.
- **Weitere Sonder-PDFs:**  
  z. B. **Pellkofer GW aus Bestand.pdf**, **Fialkowski GW Bestand Nachzahlung.PNG** – thematisch Nachzahlungen/Sonderfälle.

### 4.4 Mengen

- **PDFs gesamt** in `provisionsabrechnung/` (inkl. Unterordner): **ca. 211**.
- Pro Monat typisch: **7–9 Verkäufer-PDFs** + **5–8 Sammel-PDFs** + Verkaufsleiter-XLSX.

---

## 5. Excel-Tool

- **Datei:** `Provisionsabrechnung_V0.11.xlsm` (mit Makros).
- **Import-Skript:** Siehe **`EXCEL_IMPORT_SCRIPT_VBA.md`** – was das Makro „Datenimport“ macht (Dateiauswahl Excel, Kopieren A2:EG, Bereinigung Spalte AB, Nicht-importieren-Regel Rg.Netto/P1, Spalten_Aktualisieren).
- **Rolle:** Lädt die Monats-Excel (Locosoft-Export), wendet **Filter und Sortierung** an, berechnet Provisionen und erzeugt:
  - die **Verkäufer-PDFs** (eine pro Person/Monat),
  - die **Sammel-PDFs** (AS, DF, EP, FP, ML, MP, RK, RS, …).
- Die **genauen Filter- und Zuordnungsregeln** (inkl. Verkäufer ↔ verk. VKB, Kostenträger ↔ Kürzel) sollten aus diesem Tool oder aus Locosoft-Stammdaten übernommen werden, um sie in DRIVE oder Locosoft-PostgreSQL nachzubilden.

### Simulation: DB vs. CSV (gleiche Daten/Fahrzeuge?) (2026-02-18)

- **Script:** `scripts/provisions_vergleiche_db_mit_csv.py` – lädt einen Monat aus der DB (Locosoft, Rechnungsdatum) und vergleicht mit der L744PR-CSV (eine Zeile pro VIN, an DB-Netto angepasst). Prüft: gleiche VINs, gleiche Stückzahl, Abweichungen bei Rg-Nr., Netto, VKB.
- **Januar 2026:** 72 Fahrzeuge in DB und 72 VINs in CSV – **gleiche Stückzahl, gleiche Fahrzeuge**. 56 VINs ohne Abweichung bei Rg-Nr./Netto/VKB; 16 mit kleinen Netto- oder Rg-Nr.-Differenzen (u. a. Brutto/Netto oder Rundung). Fz.-Art-Codierung in der DB (B/L/F) weicht von der im Export (D/G/N/V/T) ab.

### Test: Januar-Filter analog Locosoft-Export (2026-02-17)

- **Herkunft der Daten:** Original-Export aus Locosoft L744PR „Verkaufsnachweisliste“; im Report-Dialog wird nach **Rechnungsdatum** gefiltert (z. B. 01.01.26–31.01.26), nicht nach Leistungsdatum. Spalte C „Leistungsdatum“ ist eine Ausgabespalte im Export.
- **Script:** `scripts/provisions_januar_filter_test.py` – für Abgleich mit dem L744PR-Export Filter nach **Rechnungsdatum** verwenden: `--datum rechnung --quelle locosoft` (bzw. Portal). Option `--datum leistung` nutzt `invoices.service_date` (bei Fahrzeugrechnungen in Locosoft oft NULL).
- **Erwartung:** 0126.xls = 1 Überschrift + **93 Rechnungszeilen** (Nutzerangabe). Script mit `--datum rechnung`: **72 Treffer** aus `dealer_vehicles` + `invoices`. Differenz kann durch Filter im L744PR-Dialog entstehen (z. B. „Verkaufender Betrieb“, Verkaufsberater-Range, Fahrzeugarten).

---

## 6. Offene Punkte für DRIVE-Integration

1. **Mapping verk. VKB → Verkäufer (Name/Personal):**  
   Wo liegt die Stammzuordnung (Locosoft, Excel, anderer Katalog)? Soll in DRIVE eine Tabelle „Verkäufer ↔ VKB“ gepflegt werden?
2. **Exakte Filterregeln:**  
   Rg-Typ, Buchungsstatus, Fz.-Art, ggf. Ausschluss Storno – aus Excel oder Fachvorgabe übernehmen und in SQL/API abbilden.
3. **Kostenträger ↔ Kürzel (AS, DF, EP, …):**  
   Eindeutige Liste und Verwendung für Sammel-PDFs/Lohnbuchhaltung.
4. **Verkaufsleiter (Anton Süß):**  
   Getrennt analysieren; evtl. zweiter Schritt nach der Verkäufer-Provisionsintegration.
5. **Versand Verkäufer-PDFs:**  
   Zielzustand: Abrechnungs-PDFs pro Verkäufer aus DRIVE erzeugen und Versand (E-Mail/Versandauftrag) an den jeweiligen Verkäufer abbilden (heute manuell).

---

*Dokument ergänzt um Analyse der PDFs in den Monatsunterordnern und deren Verwendung (manueller Versand an Verkäufer, Sammel-PDFs für Lohnbuchhaltung).*
