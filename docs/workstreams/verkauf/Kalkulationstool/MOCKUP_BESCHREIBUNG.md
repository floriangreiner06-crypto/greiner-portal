# Mockup: VFW / Tageszulassung Kalkulation

**Stand:** 2026-03-01  
**Dateien:** `MOCKUP_VFW_KALKULATION.html` (interaktiv im Browser), diese Beschreibung.

---

## 1. Analyse der bestehenden Excel-Kalkulationen

Es wurden die **4 Ordner** unter `Kalkulationstool` ausgewertet:

| Ordner | Inhalt | Beispiele |
|--------|--------|-----------|
| **TW Kalkulationen Hyundai** | Tageszulassungen / VFW n.gef. (Hyundai) | i20 Trend 100 PS VFW n.gef. Z550229, Corsa GS TW R4270588 |
| **TW Kalkulationen Opel** | Tageszulassungen (Stellantis/Opel) | Corsa GS 1.2 100 PS TW R4267707, Astra, Grandland, Vivaro-e |
| **Vorführwagen-Kalkulationen Hyundai** | VFW gef./n.gef., teils mit Namen | Tucson Prime VFW Claudia Greiner, IONIQ 5 VFW gef. |
| **Vorführwagen-Kalkulationen Opel** | VFW gefahren, TW, Netprice | Corsa VFW gefahren R4250538, Grandland Electric VFW |

**Gemeinsame Struktur aller Dateien (ein Blatt „Tabelle1“):**

- **Zeilen 1–6:** Kopf  
  - Titel „Kalkulations-Schema“, Datum, **Aktion** (TW, VFW gef., VFW n.gef., VFW Claudia Greiner, …), **Modell**, **Fahrgestellnummer** (VIN).
- **Zeilen 8–12:** Zwei Spalten  
  - **Links:** VH netto (Rechnungspreis), ggf. Spardepot, Zwischensumme.  
  - **Rechts:** UPE netto, + 19 % MwSt., UPE inkl. MwSt., Überführung, **Gesamtpreis** (Listenpreis).
- **Zeilen 13–16:** Bis zu 4 Bonus-Positionen (Abzüge vom EK)  
  - **Opel TW:** z. B. „./. KAB + TW“ (%), „./. Reg.-Budget“ (fester Betrag).  
  - **Opel VFW:** „./. TW + KAP“ (%), „./. Reg.-Budget“ (fester Betrag).  
  - **Hyundai VFW n.gef.:** „./. VFW“ (%), „./. Endkundenprämie“ (fester Betrag).  
  - **Hyundai VFW (andere):** „./. VFW“ (Betrag), „./. Abverkaufsprämie“ (Betrag).
- **Zeilen 17–21:**  
  - Zwischensumme (nach Boni), ./. Marge (Betrag + ggf. %), Summe vor Steuer, + 19 % MwSt., **Gesamtsumme** (brutto intern).
- **Zeilen 22, 24:**  
  - **Aktionspreis** (VK brutto), **Ersparnis** (absolut + Anteil am Listenpreis).
- **Ab Zeile 30:** Referenzliste (z. B. AKB / Modellwerte) — im Mockup weggelassen, später optional.

**Fazit:** Excel wird als **Taschenrechner mit Druckfunktion** genutzt. Die Daten dienen nur zum Verständnis; die Logik ist einheitlich: EK − Boni (% auf UPE oder fest) + Marge → Summe vor St. → + MwSt. → Gesamtsumme; Listenpreis = UPE inkl. MwSt. + Überführung; Ersparnis = Listenpreis − Aktionspreis.

---

## 2. Mockup-Entscheidungen

### 2.1 Ein Bildschirm statt viele Excel-Dateien

- **Eine** Weboberfläche ersetzt die vielen Einzel-Excels.
- **Marke** (Opel/Hyundai/Leapmotor) und **Aktion** (TW, VFW gef., VFW n. gef., Netprice, OR, Freitext) als Dropdowns.
- **4 Bonus-Zeilen** mit je Bezeichnung + **Prozent (auf UPE)** oder **fester Betrag** — deckt alle Varianten (KAB+TW, Reg.-Budget, VFW %, Endkundenprämie, Abverkaufsprämie usw.) ab.

### 2.2 Vorbelegung aus Bestand

- **„Fahrzeug aus Bestand übernehmen“:** Optionales Dropdown (später aus API: VFW-/TW-Bestand aus Locosoft).  
- Beim Auswählen werden Modell, VIN, VH netto, UPE (und ggf. Aktion) vorbelegt — **kein Kopieren von Excel-Dateien** mehr.

### 2.3 Live-Berechnung

- Alle relevanten Eingabefelder lösen sofort eine **Neuberechnung** aus.
- Rechte Spalte zeigt immer die aktuelle **Kalkulation** (Zwischensumme, Marge, Summe vor St., MwSt., Gesamtsumme, Listenpreis, Aktionspreis, Ersparnis).

### 2.4 Drucken & PDF

- **Drucken:** Nur Kalkulationsblock (Eingabefelder im Mockup ausgeblendet beim Druck).
- **PDF:** Im echten Modul Export über Backend (z. B. VIN im Dateinamen wie in der alten Excel-VBA-Logik).

### 2.5 Keine Datenspeicherung im Mockup

- Der Mockup speichert **nichts** in einer Datenbank.  
- Im späteren Modul: Optional Speicherung von Kalkulationen (z. B. für Nachvollziehbarkeit oder Reporting).

---

## 3. Was der Mockup abbildet

| Excel-Element | Mockup |
|---------------|--------|
| Aktion (Text/Dropdown) | Dropdown + Option Freitext |
| Modell, VIN | Textfelder (+ Vorbelegung aus Bestand) |
| VH netto, UPE netto | Zahlfelder € |
| Überführung | Zahlfeld € |
| 4 Bonus-Zeilen (versch. Bezeichnungen, % oder €) | 4 Zeilen: Label + % + € (je Zeile entweder % oder € nutzbar) |
| Marge (€) | Zahlfeld € |
| Aktionspreis (VK brutto) | Zahlfeld € |
| Ersparnis (absolut + %) | Live-Anzeige |
| Listenpreis (UPE inkl. MwSt. + Überführung) | Live-Anzeige |
| Gesamtsumme (brutto intern) | Live-Anzeige |
| Druck/Export | Buttons Drucken / PDF |

---

## 4. Nächste Schritte (Implementierung)

- **Phase 3** des VFW-Implementierungsplans (`VFW_VERMARKTUNG_IMPLEMENTIERUNGSPLAN.md`):  
  Kalkulations-UI als echte Route/Template (z. B. `/verkauf/vfw/kalkulation`) mit Backend-API und SSOT in `api/vfw_kalkulation_service.py`.  
- **Rundschreiben-Manager (Phase 2):** Aktionstypen und Bonus-Labels/Prozente aus Programmen vorbelegen statt nur Freitext.  
- **PDF-Export:** Wie bestehendes `provision_pdf.py` (reportlab), Dateiname z. B. `VFW_Kalkulation_<VIN>.pdf`.

---

## 5. Mockup öffnen

- **Lokal (Windows):**  
  `F:\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\verkauf\Kalkulationstool\MOCKUP_VFW_KALKULATION.html` im Browser öffnen.  
- **Server:**  
  Datei liegt unter `/mnt/greiner-portal-sync/docs/workstreams/verkauf/Kalkulationstool/MOCKUP_VFW_KALKULATION.html`; bei Bedarf nach `/opt/greiner-portal/` kopieren und über einen statischen Pfad oder eine einfache Route ausliefern.
