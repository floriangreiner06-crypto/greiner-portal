# Provisionslogik aus Excel-Tool (Provisionsabrechnung_V0.11.xlsm)

**Stand:** 2026-02-17 | Auswertung der Arbeitsmappen-Struktur und Formeln (ohne VBA-Makros).

**Hinweis:** Verkaufsleiter (Anton Süß) hat ein eigenes Provisionssystem. Als **Test-/Beispiel-Verkäufer** für die hier beschriebene Logik gelten **Rafael Kraus** und **Roland Schmid**.

---

## 1. Tabellen und Ablauf im Excel-Tool

| Blatt | Rolle |
|-------|--------|
| **Start** | Monat (Dropdown `n_monat`), Verkäufer (Dropdown aus Optionen E52:E66), Button „Datenimport“ (Makro). |
| **Import_Verkaufsdaten** | Rohdaten aus CSV (Spalten wie in Locosoft-Export). Filterbereich E10:EK150. Spalte **C** = Suchkriterium (Verkäufer-Code + Fz.-Art, z. B. 2002N, 2002D, 2002G, 2002T, 2002V). |
| **Optionen** | Verkäuferliste (E52:G66), Monatsliste (B52:B183), **Provisionssätze** (J52, J53, J54, J60, J61), Pfade Import/Export, „Nicht importieren wenn &lt;“ (n_nichtimportieren). |
| **Fahrzeugverkaeufe** | Pro Verkäufer gefilterte Verkäufe: Zeilen aus Import, gruppiert nach **I. Neuwagen**, **II. Testwagen/VFW**, **III. Gebrauchtwagen**, **IV. GW aus Bestand**. Spalten: Käufer, Fahrzeug, Erlös (Rg.Netto), DB, Prov.Satz, Provision. |
| **Provisionabrechnung** | Zusammenfassung pro Verkäufer (Summen der vier Blöcke), Button „PDFdatei_Export“. |

Datenfluss: **CSV → Import_Verkaufsdaten** (per Makro). **Optionen** liefern Sätze und Verkäuferliste. **Fahrzeugverkaeufe** liest per MATCH/VLOOKUP aus Import (gefiltert nach Verkäufer-Code + Fz.-Art). **Provisionabrechnung** summiert die vier Kategorien und erzeugt PDF.

---

## 2. Verkäufer- und Art-Zuordnung

- **Verkäuferliste:** `Optionen!$E$52:$G$66` (Name in E, VKB-Code in Spalte 2 des Bereichs).
- **Suchkriterium in Import:** Spalte C = Verkäufer-Code + **Buchstabe Fz.-Art**:
  - **N** = Neuwagen
  - **D** = Direkt(verkauf?)
  - **G** = Gebrauchtwagen
  - **T** = Testwagen
  - **V** = Vorführwagen
- Formel im Tool: `VLOOKUP(Start!C12; Optionen!$E$52:$G$66; 2; 0) & "N"` → z. B. **2002N** für Neuwagen des Verkäufers mit Code 2002. Entsprechend 2002D, 2002G, 2002T, 2002V.
- **Import Spalte C** muss diese Werte enthalten (vermutlich aus **verk. VKB** + **Fz.-Art** in der CSV abgeleitet oder vom Makro gesetzt).

Daraus folgt: **Verkäufer ↔ VKB** steht in Optionen E52:G66; **Fz.-Art** (N/D/G/T/V) trennt die vier Bereiche der Abrechnung.

---

## 3. Die vier Provisionsblöcke (Regeln)

### I. Neuwagen

- **Maßgröße:** Deckungsbeitrag (Spalte **AF** im Import = „Deckungsbeitrag“).
- **Prov.Satz:** `Optionen!$J$52` → **12 %** (0,12).
- **Formel:** `Provision = Erlös (DB) × 0,12` je Zeile; zusätzlich **Fix 50 € pro Stück** (E11×50), wobei E11 auf 0–15 begrenzt ist (Stückzahl manuell oder aus Anzahl Neuwagenzeilen).
- **Keine** Min/Max-Grenzen für die Prozentprovision („NW: Keine mindest oder Max-Grenzen“ in sharedStrings).

### II. Testwagen / Vorführwagen (VFW)

- **Maßgröße:** **Rg.Netto** (Erlös, Import Spalte R).
- **Prov.Satz:** `Optionen!$J$53` → **1 %** (0,01).
- **Grenzen:** **min 103 €, max 500 €** pro Position.  
  Formel: `WENN(Erlös*Satz < 103; 103; WENN(Erlös*Satz > 500; 500; Erlös*Satz))`.
- In sharedStrings: „VW: Provision mind 103€, max. 205 €“ – im aktuellen Sheet wurde 500 als Maximum verwendet; 205 könnte ältere Version oder anderer Block sein.

### III. Gebrauchtwagen-Verkäufe

- **Maßgröße:** **Rg.Netto** (Erlös).
- **Prov.Satz:** `Optionen!$J$53` → **1 %**.
- **Grenzen:** **min 103 €, max 500 €** (gleiche Formel wie II).  
  sharedStrings: „GW: Provision mind 103€, max. 205 €“ – wieder ggf. historisch; im Sheet Formel mit 500.

### IV. Gebrauchtwagen aus Bestand

- **Maßgröße:** **Deckungsbeitrag** (Import AF); es wird eine „Kosten“-Größe abgezogen.
- **Kosten (BE II):** `(DB × Optionen!$J$60) + Optionen!$J$61` (gerundet 2 Dezimalen).  
  J60 = Prozentsatz, J61 = Fixbetrag.
- **Umsatzprovision-Basis:** `DB - BE II` („Umsatzprovision“ = verbleibender DB nach Abzug).
- **Prov.Satz:** **12 %** (0,12) auf diese Basis.
- **Formel:** `Provision = (DB - BE II) × 0,12`.

Vorführwagen-Block (Zeile 81–96 Fahrzeugverkaeufe) nutzt **Optionen!$J$54**, **1 %**, **min 103 €, max 300 €** (Formel mit 300 statt 500). Das kann eine eigene Kategorie „Vorführwagen“ sein (T/V).

---

## 4. Übersicht Provisionssätze und Grenzen (aus Formeln)

| Kategorie | Maßgröße | Satz (Optionen) | Min | Max | Anmerkung |
|-----------|----------|------------------|-----|-----|-----------|
| I. Neuwagen | DB | J52 = 12 % | – | – | + 50 € Fix pro Stück (bis 15 Stück) |
| II. Testwagen/VFW | Rg.Netto | J53 = 1 % | 103 € | 500 € | |
| III. Gebrauchtwagen | Rg.Netto | J53 = 1 % | 103 € | 500 € | |
| IV. GW aus Bestand | DB − (DB×J60+J61) | 12 % | – | – | J60, J61 = Kostenabzug |
| Vorführwagen (T/V) | Rg.Netto | J54 = 1 % | 103 € | 300 € | |

Die **exakten Werte** für J52, J53, J54, J60, J61 stehen in **Optionen** (Zellen J52:J61); in den ausgelesenen Formeln: J52=0,12, J53=0,01, J54=0,01. J60/J61 müssen aus Optionen ausgelesen werden (Formel: ROUND((H*J60)+J61,2)).

---

## 5. Filter- und Zuordnungslogik (für DRIVE)

- **Zeitraum:** Abrechnungsmonat (Leistungsdatum oder Rg-Datum im Monat).
- **Verkäufer:** Spalte **verk. VKB** in der CSV; Mapping VKB → Verkäufername über Tabelle wie Optionen E52:G66.
- **Fz.-Art (Import Spalte C / Kategorie):**
  - **N** → Neuwagen (Block I)
  - **D** → evtl. Direkt/Neuwagen
  - **G** → Gebrauchtwagen (Block III)
  - **T** → Testwagen (Block II)
  - **V** → Vorführwagen (eigener Satz J54, min 103, max 300)
- **GW aus Bestand:** Vermutlich über **Import Spalte B** (andere Suchkriterien AH15, AH16) – z. B. spezielle Kennzeichnung „aus Bestand“ oder bestimmte Fz.-Art. In DRIVE müsste diese Kennung aus Locosoft oder Stammdaten kommen.
- **Rg-Typ:** Nur **H** (Hauptrechnung) verwenden, **Z** (Zusatz/Storno) ggf. ausschließen oder gesondert verrechnen – im Excel wird das vermutlich im Import/Makro gefiltert.
- **Nicht importieren:** `n_nichtimportieren` (Optionen!Q6) – „Nicht importieren, wenn &lt;“ (z. B. Betrag unter Schwellwert). Muss mit euch abgeglichen werden.

---

## 6. Summen und PDF

- **Gesamtprovision** = Summe Block I + II + III + IV (inkl. Fix 50€ und ggf. Vorführwagen-Block).
- **Provisionabrechnung-Blatt** zeigt für den gewählten Verkäufer (Start!C12) und Monat (Start!C10) die Summen; Button **PDFdatei_Export** erzeugt die PDF (Makro – Inhalt/Seitenaufteilung nicht aus XML ableitbar).

---

## 7. Was für DRIVE noch offen ist

1. **Optionen J60, J61** exakt (Kostenabzug GW Bestand) – aus Optionen-Blatt oder von euch vorgeben.
2. **Abgrenzung „GW aus Bestand“** (welche Zeilen aus Import Spalte B / welche Kennung in Locosoft).
3. **Kostenträger** (AS, DF, EP, FP, ML, MP, RK, RS) – ob aus gleichen Daten für Sammel-PDFs oder eigener Logik.
4. **VBA-Makros:** Datenimport (CSV einlesen, Spalte C setzen), PDF-Export – Logik nur durch Öffnen des Makros oder Nachbau in Python/DRIVE abbildbar.
5. **205 € vs. 500 €:** Doku im Sheet nennt teils „max. 205 €“, Formeln nutzen 500 € (und 300 € bei VFW) – fachlich bestätigen.

Wenn ihr die Werte aus **Optionen** (J52, J53, J54, J60, J61) und die Regel „GW aus Bestand“ bestätigt, kann die obige Logik 1:1 in DRIVE (API + Abrechnungs-PDF) übernommen werden.
