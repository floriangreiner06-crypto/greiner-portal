# Provisionsabrechnung_V0.11.xlsm – Was macht das Import-Skript?

**Stand:** 2026-02-18 | Rekonstruktion aus VBA-Fragmenten (vbaProject.bin, `strings`-Auswertung). Der VBA-Code liegt kompiliert vor, daher nur indirekt auslesbar.

---

## Ablauf des Datenimports (Makro „Datenimport“)

Das Skript lädt **Verkaufsdaten aus einer Excel-Datei**, die aus dem **Warenwirtschaftssystem (Locosoft)** exportiert wurde – also die gleichen Daten wie in der L744PR-CSV, typischerweise als **Excel (z. B. .xlsx)** geöffnet oder gespeichert.

### 1. Dateiauswahl

- **Öffnen-Dialog** zur Auswahl der zu importierenden **Basisdatei**.
- **Dateifilter:** `Basis-Datei(*.xl*), *.xl*` → es werden **Excel-Dateien** (.xls, .xlsx, .xlsm) erwartet, keine CSV direkt.
- **Startpfad:** kann aus **Optionen** kommen (z. B. Zelle **E8** = Pfad/Vorgabe).
- Es wird geprüft, ob eine gültige Datei gewählt wurde.

### 2. Vorbereitung

- **Application:** `ScreenUpdating = False`, `Calculation = xlManual`, `Cursor = xlWait` (für Performance).
- **Import-Verkaufsdaten leeren:** Bereich **E11:EK100000** auf dem Blatt **Import_Verkaufsdaten** wird geleert (`.ClearContents` o. ä.).

### 3. Kopieren der Rohdaten

- Die **gewählte Verkaufsdatei** wird geöffnet.
- Aus der Quelldatei wird ein Bereich **A2:EG** (bis zur letzten befüllten Zeile) in das Blatt **Import_Verkaufsdaten** kopiert (Ziel: ab Zelle **A2** bzw. passender Start).
- Die **Quelldatei wird danach wieder geschlossen**.

→ Die Locosoft-Exportdatei (als Excel geöffnet oder gespeichert) hat damit dieselben Spalten A–EG wie die L744PR-CSV (Rg-Datum, Leistungsdatum, verk. Betrieb, verk. VKB, Fz.-Art, Rg.Netto, Deckungsbeitrag, …).

### 4. Importdaten bereinigen

- **Spalte AB löschen:** Ab **6/2025** ist im Export eine zusätzliche Spalte AB vorhanden; sie wird **gelöscht**, damit die restliche Logik (Spaltenbezüge) unverändert bleibt.
- **Nicht-importieren-Regel:**  
  Es wird geprüft, ob **Spalte R (Rg.Netto)** unter einem vorgegebenen Betrag liegt (Schwellwert aus **Optionen**, z. B. `n_nichtimportieren` / Optionen!Q6).  
  Zusätzlich werden **Einträge mit "P1" in Spalte AN (Memo) und "N" in Spalte J (Fz.-Art)** berücksichtigt – vermutlich werden diese Zeilen **nicht importiert** (gelöscht oder übersprungen) oder speziell markiert.
- **Spaltenbreite:** Ab **Spalte F** wird die optimale Spaltenbreite gesetzt (Bereich **F:EG**).

### 5. Nach dem Import

- **Spalten aktualisieren:** Prozedur **Spalten_Aktualisieren** läuft (u. a. **Spalten AA und AB durchlaufen**; **Zeilen in den Spalten AC…** aktualisieren). Das dürfte die **Suchkriterien** in **Spalte C** (Verkäufer-Code + Fz.-Art) und ggf. weitere abgeleitete Spalten (AC, …) setzen, die später auf **Fahrzeugverkaeufe** und **Provisionabrechnung** verwendet werden.
- **Blatt „Fahrzeugverkäufe“** wird aktualisiert (Formeln/Filter beziehen sich auf Import_Verkaufsdaten).
- **Hinweis:** Meldung *„Die Verkaufsdaten wurden erfolgreich importiert und stehen auf dem Blatt 'Import_Verkaufsdaten' zur Verfügung.“*

---

## Kurzfassung

| Schritt | Aktion |
|--------|--------|
| 1 | Dialog: Excel-Basisdatei (*.xl*) wählen (Locosoft-Export, als Excel geöffnet/gespeichert). |
| 2 | Import_Verkaufsdaten E11:EK100000 leeren. |
| 3 | Aus Quelldatei **A2:EG** (bis letzte Zeile) nach **Import_Verkaufsdaten** kopieren, Quelldatei schließen. |
| 4 | Spalte **AB** löschen (ab 6/2025). Zeilen mit **Rg.Netto &lt; Schwellwert** (Optionen) und ggf. **P1 in Memo + N in Fz.-Art** bereinigen. Spaltenbreite F:EG setzen. |
| 5 | **Spalten_Aktualisieren** (u. a. Spalte C = Suchkriterium), **Fahrzeugverkäufe** aktualisieren, Erfolgsmeldung. |

Die **CSV** (z. B. 0126.csv) enthält dieselben Daten wie der Excel-Export; im Tool wird explizit eine **Excel-Datei** eingelesen (CSV müsste zuvor in Excel geöffnet/gespeichert werden oder als .xlsx exportiert werden).
