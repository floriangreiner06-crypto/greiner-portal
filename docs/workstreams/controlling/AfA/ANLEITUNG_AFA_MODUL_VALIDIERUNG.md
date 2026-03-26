# AfA-Modul Vorführwagen / Mietwagen — Benutzeranleitung und Validierung

**Stand:** 2026-02-17 (ergänzt für Test-Weitergabe)  
**Ziel:** Nutzung des Tools beschreiben und Anweisungen zur Prüfung von Beständen und Werten geben.

---

## 1. Zugang und Navigation

- **Menü:** Controlling → **AfA Vorführwagen / Mietwagen**
- **URL (intern):** http://drive/controlling/afa (bzw. über Route AfA-Dashboard)
- **Berechtigung:** Feature `controlling` oder `admin`

---

## 2. Übersicht: KPI-Karten und Filter

Oben auf der Seite stehen **Kennzahlen** und **Filter**:

| KPI | Bedeutung |
|-----|-----------|
| **Aktive VFW** | Anzahl aktiver Vorführwagen (ohne Tageszulassungen) |
| **Aktive Mietwagen** | Anzahl aktiver Mietwagen |
| **Restbuchwert gesamt** | Summe Restbuchwerte aller aktiven, AfA-pflichtigen Fahrzeuge |
| **AfA pro Monat** | Summe der monatlichen Abschreibungsbeträge (für Buchung) |
| **Ø Haltedauer (Monate)** | Durchschnittliche Haltedauer der aktiven Fahrzeuge |

**Filter für die Fahrzeugtabelle:**
- **Bestand:** Geschäftsjahr (z. B. 2025/26) oder „Alle Geschäftsjahre“
- **Art:** VFW / MIETWAGEN / Alle
- **Marke:** aus den vorhandenen Daten
- **Betrieb:** 1 (DEG Opel), 2 (HYU), 3 (LAN)

---

## 3. Fahrzeugliste und Detail

### 3.1 Tabelle (Fahrzeugliste)

- Zeigt alle Fahrzeuge (aktiv und verkauft je nach Filter).
- Spalten: **Kennzeichen**, **VIN**, Modell/Bezeichnung, **Art** (VFW/Mietwagen), **Tageszul. (nicht AfA-pflichtig)** (Badge „Tageszul.“ oder „-“), Anschaffung, EK netto, Monatl. AfA, Restbuchwert, Status, **Detail**.
- Fahrzeuge mit gesetztem Tageszulassungs-Flag werden **nach unten sortiert** (am Ende der Liste).

### 3.2 Detail und Bearbeiten

- **Detail** (Button in der Zeile) öffnet ein Modal mit: EK, monatl. AfA, Restbuchwert, Verlauf (Buchungen), optional Buchgewinn/Buchverlust bei Abgang.
- **Tageszulassung:** Im Detail-Modal Checkbox **„Tageszulassung (nicht AfA-pflichtig)“** und Button **Speichern**.  
  - Wenn gesetzt: Fahrzeug erscheint nicht in Monatsberechnung/Buchungsliste und nicht in den AfA-Summen. In der Listenansicht wird es nach unten sortiert.

### 3.3 Löschen (versehentlicher Import)

- Im **Detail-Modal** unten: Button **„Fahrzeug löschen“**.
- Löscht das Fahrzeug und **alle zugehörigen AfA-Buchungen** endgültig (z. B. wenn versehentlich aus Locosoft importiert).
- Vor dem Löschen erscheint eine Bestätigungsabfrage. Die Aktion ist nicht rückgängig zu machen.

### 3.4 Neuanlage (manuell)

- Über API möglich (POST `/api/afa/fahrzeug`). In der UI aktuell über **Import aus Locosoft** (siehe unten) oder spätere Erweiterung „Fahrzeug anlegen“.

---

## 4. Aus Locosoft importieren

- **Nutzungsdauer** (z. B. 72 Monate) einstellen, dann **„Bestand laden“** (lädt den verfügbaren Bestand aus Locosoft).
- Es erscheinen **VFW (Typ V)** und **eigene Mietwagen** (Jw-Kz **M** bzw. Fz.-Art G mit Jw-Kz M) aus Locosoft, die noch **nicht** in AfA sind und **noch nicht verkauft** (ohne Rechnungsdatum).
- **Spalten der Tabelle:** Checkbox, Kennzeichen, **VIN**, Bezeichnung, Art, Anschaffung, EK netto, **Detail** (Button).
- **Locosoft-Details:** Klick auf **„Detail“** in einer Zeile öffnet ein Modal **„Fahrzeugdetails (Locosoft)“** mit strukturierten Daten aus Locosoft: Identifikation (VIN, Kennzeichen, Typ, Kom.Nr.), Fahrzeug (Modell, Erstzulassung), Kalkulation (Ankunft, Grundgebühr, Zubehör, Einsatzerhöhungen, Abschreibung), Sonstiges (Mietwagen-Flag, Jw-Kz, Standort), EK netto (berechnet).
- **EK netto** in der Liste = Einsatzwert-Formel (inkl. Einsatzerhöhung) wie in der Buchhaltung/DB1.
- Fahrzeuge auswählen (Checkbox), dann **„Ausgewählte importieren“**. Die **Art** (VFW/Mietwagen) wird aus Locosoft abgeleitet (inkl. Typ G + Jw-Kz M = Mietwagen).

---

## 5. Monatsübersicht und Buchungsliste

- **Monat** wählen (z. B. 2026-02).
- **„Berechnen“:** Legt fehlende AfA-Buchungen für den Monat an (nur für aktive, AfA-pflichtige Fahrzeuge; Tageszulassungen ausgenommen).
- Tabelle zeigt pro Fahrzeug: Kennzeichen, Bezeichnung, Art, **Soll**, **Haben**, AfA-Betrag.  
  **Summe** = Betrag für die Monatsbuchung.
- **„CSV exportieren“:** Export einer Zeilenliste (Soll/Haben-Konten, Beträge) für die Buchhaltung.

### Konten (Buchhaltung, Stand 2026-02)

| Bereich | Soll (Abschreibung) | Haben (Bestand/Abschreibungspool) |
|---------|----------------------|-----------------------------------|
| Mietwagen DEG | 450001 | 022501 |
| Mietwagen LAN | 450002 | 022502 |
| Mietwagen HYU | 450001 | 022501 |
| VFW DEG | 450001 | 318001 |
| VFW LAN | 450002 | 318002 |
| VFW HYU | 450001 | 318001 |
| VFW Leapmotor | 450001 | 318201 |

Buchung Abschreibung Leapmotor wie VFW Opel: **450001 an 090401** (im Tool: Haben **318201** für Marke/Bezeichnung „Leapmotor“).

---

## 6. Abgangs-Kontrolle (DRIVE vs. Locosoft)

- Card **„Abgangs-Kontrolle“** → **„Aktualisieren“**.
- **„Bitte Abgang in DRIVE prüfen“:** Fahrzeuge, die in DRIVE noch **aktiv** sind, in Locosoft aber bereits **verkauft** (Rechnungsdatum gesetzt). → Abgang in DRIVE prüfen und ggf. erfassen.
- **„Abgang in DRIVE“:** Bereits in DRIVE als verkauft geführt, mit Locosoft-Rechnungsdatum zur Kontrolle.

---

## 7. Validierung: Bestände und Werte prüfen

### 7.1 Abgleich mit Buchhaltung/DATEV

1. **Summen pro Monat**  
   - Im Modul: Monatsübersicht → **Summe** für den gewählten Monat.  
   - In DATEV/Buchhaltung: AfA-Betrag des Monats (z. B. Summe Liste abzüglich Vormonat).  
   - **Prüfung:** Summe DRIVE ≈ Summe Buchhaltung (gleicher Buchungsmonat).

2. **Summen nach Konto (Soll/Haben)**  
   - CSV-Export aus der Monatsübersicht enthält pro Zeile Soll- und Haben-Konto.  
   - Optional: Summen pro Konto (022501, 022502, 318001, 318002, 318201) bilden und mit den Buchhaltungs-Belegungen abgleichen.

3. **Stückzahlen und Restbuchwerte**  
   - KPI „Aktive VFW“ / „Aktive Mietwagen“ mit den Listen der Buchhaltung (Excel/DATEV) vergleichen.  
   - Restbuchwert gesamt (KPI) grob mit der Summe der Buchwerte in der Buchhaltung vergleichen (Stichtag beachten).

### 7.2 Abgleich mit Locosoft

1. **Abgangs-Kontrolle**  
   - Regelmäßig **„Aktualisieren“** ausführen.  
   - Wenn Einträge unter „Bitte Abgang in DRIVE prüfen“ erscheinen: in Locosoft ist Verkauf gebucht, in DRIVE noch nicht → Abgang in DRIVE nachziehen.

2. **Bestandsliste (Locosoft)**  
   - „Bestand laden“ mit den Buchhaltungs-Listen (VFW/Mietwagen) abgleichen: Sollten alle buchhalterisch relevanten VFW/Mietwagen entweder bereits in AfA oder in der Liste erscheinen (bei Typ G + Jw-Kz M = Mietwagen).

### 7.3 Plausibilität im Modul

1. **Einzelfahrzeuge**  
   - Detail prüfen: EK netto, Nutzungsdauer, monatl. AfA, Restbuchwert-Verlauf.  
   - AfA linear: monatl. AfA ≈ EK / 72 (bei 72 Monaten).

2. **Tageszulassungen**  
   - Fahrzeuge, die nicht abgeschrieben werden sollen, müssen „Tageszulassung“ gesetzt haben; sie erscheinen nicht in Monatsberechnung und nicht in der Summe.

3. **Abgänge**  
   - Verkaufte Fahrzeuge: Status „verkauft“, Abgangsdatum und ggf. Restbuchwert/Buchgewinn im Detail prüfen.

### 7.4 Checkliste Validierung (kurz)

| Prüfung | Aktion |
|--------|--------|
| Monatssumme DRIVE = Buchhaltung | Monatsübersicht Summe vs. DATEV/Buchung |
| Konten stimmen | CSV-Export Soll/Haben mit Kontenplan (022501, 318001 …) vergleichen |
| Keine „vergessenen“ Abgänge | Abgangs-Kontrolle → „Bitte Abgang prüfen“ leer oder abgearbeitet |
| Stückzahlen VFW/Mietwagen | KPI vs. Excel/DATEV-Listen |
| Tageszulassungen korrekt | Nur nicht genutzte Tageszulassungen mit Haken; alle anderen ohne |

---

## 8. Konten-Referenz (Buchhaltung)

| Bezeichnung | Konto | Hinweis |
|-------------|--------|---------|
| Mietwagen DEG | 022501 | Haben |
| Mietwagen LAN | 022502 | Haben |
| Mietwagen HYU | 022501 | Haben |
| VFW DEG | 318001 | Haben |
| VFW LAN | 318002 | Haben |
| VFW Leapmotor | 318201 | Haben; Buchung wie VFW Opel 450001 an 090401 |
| VFW HYU | 318001 | Haben |
| Auflaufende Abschreibung DEG/HYU | 450001 | Soll |
| Auflaufende Abschreibung LAN | 450002 | Soll |

---

## 9. So testen Sie (Checkliste für Tester)

| Nr. | Was testen | Erwartung |
|-----|------------|-----------|
| 1 | **Zugang** | Controlling → AfA Vorführwagen/Mietwagen öffnet die Seite. |
| 2 | **Fahrzeugliste** | Tabelle zeigt Kennzeichen, VIN, Modell, Art, Tageszul., Anschaffung, EK, AfA, Restbuchwert, Status. Tageszulassungen stehen unten. |
| 3 | **Detail (DRIVE)** | Klick auf „Detail“ bei einem Fahrzeug → Modal mit KPIs, Verlauf, Checkbox „Tageszulassung“, Speichern, ggf. „Fahrzeug löschen“. |
| 4 | **Tageszulassung** | Checkbox setzen, Speichern → Fahrzeug erscheint in der Liste mit Badge „Tageszul.“ und wird nach unten sortiert; nicht mehr in Monatsübersicht. |
| 5 | **Bestand laden** | „Bestand laden“ → Tabelle mit Kennzeichen, VIN, Bezeichnung, Art, Anschaffung, EK netto, Detail-Button. |
| 6 | **Locosoft-Detail** | Klick auf „Detail“ in der Locosoft-Tabelle → Modal „Fahrzeugdetails (Locosoft)“ mit Identifikation, Fahrzeug, Kalkulation, Sonstiges, EK netto. |
| 7 | **Import** | Ein oder mehrere Fahrzeuge auswählen, „Ausgewählte importieren“ → Meldung mit Anzahl; Fahrzeuge erscheinen in der Fahrzeugliste oben. |
| 8 | **Löschen** | Bei versehentlich importiertem Fahrzeug: Detail öffnen → „Fahrzeug löschen“ → bestätigen → Fahrzeug und Buchungen weg. |
| 9 | **Monatsübersicht** | Monat wählen → Tabelle mit Soll/Haben-Konten und Summe. „Berechnen“ legt Buchungen an. CSV-Export liefert Zeilen mit Konten (022501, 318001 usw.). |
| 10 | **Abgangs-Kontrolle** | „Aktualisieren“ → Tabellen „Bitte Abgang prüfen“ und „Abgang in DRIVE“ (mit Locosoft-Rechnungsdatum). |

**Hinweis:** Nach Änderungen am Server (z. B. neue Funktionen) ggf. **Portal neustarten** (`sudo systemctl restart greiner-portal`) und Seite im Browser neu laden (Strg+F5).

---

## 10. Abgleich Excel (Buchhaltung) vs. Locosoft-Bestand

Die Excel-Bestandslisten der Buchhaltung (z. B. aus `F:\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\controlling\AfA`) können mit dem Locosoft-Bestand (DRIVE-Abfrage „Bestand laden“) abgeglichen werden:

- **Script:** `scripts/afa_abgleich_excel_locosoft.py`
- **Aufruf (auf dem Server, im Projektroot):**
  ```bash
  cd /opt/greiner-portal
  pip install openpyxl   # falls nötig
  python scripts/afa_abgleich_excel_locosoft.py --dir /mnt/greiner-portal-sync/docs/workstreams/controlling/AfA
  ```
- **Optionen:** `--dir` = Ordner mit den .xlsx-Dateien (Standard: `docs/workstreams/controlling/AfA`). `--csv PFAD` = Ergebnis zusätzlich als CSV schreiben.
- **Ausgabe:** Pro Excel-Datei: Anzahl Zeilen, wie viele in Locosoft gefunden (per VIN, Kom.Nr., Kennzeichen), wie viele nur in Excel (nicht in Locosoft).

Die Excel-Dateien müssen im genannten Ordner liegen (auf dem Server z. B. nach Sync unter `/mnt/greiner-portal-sync/.../AfA`).

---

## 11. Weitere Unterlagen

- **Buchhaltungs-Feedback (Konten, Buchungslogik):** `AFA_BUCHHALTUNG_FEEDBACK.md`
- **DATEV-PDFs / Inventarlisten:** `DATEV_INVENTARLISTEN_ZUORDNUNG.md`
- **Anfangsbestand aus PDFs:** Script `scripts/afa_datev_pdf_anfangsbestand_locosoft.py` (mit `--locosoft`, `--csv`); CSV-Import in AfA optional/später.

---

*Ende der Anleitung*
