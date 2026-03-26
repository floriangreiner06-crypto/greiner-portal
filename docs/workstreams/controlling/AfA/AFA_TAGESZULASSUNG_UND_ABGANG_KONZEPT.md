# AfA: Tageszulassung + Abgang mit Locosoft-Verifikation

**Stand:** 2026-02-17  
**Status:** Konzept (noch nicht implementiert)

---

## 1. Tageszulassung (Sonderfall)

### Sachverhalt
- **Tageszulassung** = Vorführwagen-Zulassungen, die **nicht gefahren** werden (nicht benutzt).
- Diese unterliegen **nicht der AfA**.
- Die **Entscheidung** (AfA-pflichtig ja/nein) soll die **Buchhaltung in der UI** treffen können.

### Geplante Umsetzung
- **DB:** Neue Spalte in `afa_anlagevermoegen`, z. B.  
  `tageszulassung BOOLEAN DEFAULT false`  
  oder alternativ `afa_pflichtig BOOLEAN DEFAULT true`.
- **Bedeutung:**  
  - `tageszulassung = true` (bzw. `afa_pflichtig = false`) → Fahrzeug wird **nicht** in monatlicher AfA-Berechnung, Monatsübersicht und Buchungsliste berücksichtigt.  
  - Nur Stammdaten bleiben sichtbar (z. B. in der Fahrzeugliste mit Filter „Alle / Nur AfA-pflichtige“).
- **UI:**  
  - Im AfA-Dashboard: pro Fahrzeug (Detail oder Tabelle) ein **Schalter/Checkbox „Tageszulassung (nicht AfA-pflichtig)“**.  
  - Nur für Berechtigung Buchhaltung/Controlling editierbar (optional).
- **Keine AfA-Buchungen** für Tageszulassungen; keine Aufnahme in CSV-Export der Buchungsliste.

---

## 2. AfA-Ende mit Verkauf + Locosoft-Verifikation

### Anforderung
- AfA endet mit **Verkauf** des Fahrzeugs (bereits heute: Abgang in DRIVE mit Restbuchwert/Buchgewinn).
- **Vorschlag:**  
  - In **Locosoft**: **VIN auf Faktura prüfen** (Verkauf = Rechnung vorhanden, z. B. `out_invoice_date`).  
  - **Zur Kontrolle:** Abgang von Bestandskonto in Locosoft verifizieren.

### Geplante Umsetzung (stufbar)

**Option A – Kontrollreport (ohne Auto-Abgang)**  
- Report/Seite „Abgangs-Kontrolle“:  
  - **DRIVE status = aktiv**, aber in **Locosoft** `out_invoice_date IS NOT NULL` (VIN-Match) → Hinweis: „Verkauf in Locosoft erkannt – bitte Abgang in DRIVE prüfen.“  
  - **DRIVE status = verkauft** (Abgang), dazu Locosoft-Abfrage: VIN, `out_invoice_date`, ggf. Bestandskonto-Bewegung → Anzeige zur Kontrolle („Abgang in Locosoft bestätigt“ / „Noch nicht in Locosoft abgegangen“).

**Option B – Halbautomatik**  
- Gleicher Report wie A; zusätzlich Button „Abgang aus Locosoft übernehmen“: für ausgewählte Fahrzeuge, bei denen in Locosoft `out_invoice_date` gesetzt ist, wird in DRIVE der Abgang (Datum = `out_invoice_date`, Restbuchwert aus DRIVE-Berechnung) vorgeschlagen bzw. angelegt (Buchhaltung bestätigt).

**Option C – Verifikation „Abgang Bestandskonto“ in Locosoft**  
- Falls in Locosoft ein klares Signal für „Abgang von Bestandskonto“ existiert (z. B. Buchungstyp, Konto, Bewegungsart): dieses in der Kontrollansicht anzeigen („In Locosoft am … vom Bestandskonto abgegangen“).  
- Abhängig von Locosoft-Schnittstelle/Stammdaten; ggf. in zweiter Phase.

**Empfehlung:** Zuerst **Option A** umsetzen (VIN auf Faktura = `out_invoice_date` in Locosoft prüfen, Kontrollliste DRIVE vs. Locosoft). Option B/C bei Bedarf darauf aufbauen.

---

## 3. Datenquellen Locosoft

- **Verkauf/Faktura:** `dealer_vehicles.out_invoice_date` (Rechnungsdatum), ggf. `out_invoice_number`; Join über `vehicles.vin` bzw. `dealer_vehicles` + `vehicles`.
- **Abgang Bestand:** Über FIBU/Locosoft-Buchungen auf Bestandskonten (090xxx) – je nach Verfügbarkeit in der Locosoft-DB (journal_accountings o. ä.) in Phase 2 nutzbar.

---

## 4. Anfangsbestände 01.09. aus DATEV-PDFs

- **Script:** `scripts/afa_datev_pdf_anfangsbestand_locosoft.py`
- **Funktion:** Liest alle `Afa_*.pdf` aus dem AfA-Ordner (Server oder Sync), extrahiert pro Position: Quelle, betrieb, fahrzeugart, kennzeichen, anschaffungsdatum, AHK, Buchwert 01.09.
- **Locosoft-Abgleich:** Mit Option `--locosoft` werden VIN und `out_invoice_date` aus Locosoft zugeordnet (exakter Abgleich nach normalisiertem Kennzeichen). Erster Lauf: **70 Positionen** aus 5 PDFs, **44 in Locosoft zugeordnet**; 26 ohne Treffer (anderes Kennzeichenformat oder nicht mehr in Locosoft).
- **CSV-Export:** `--csv PATH` schreibt eine CSV (z. B. `docs/workstreams/controlling/AfA/anfangsbestand_0109_2024.csv`) für manuellen Import oder weitere Verarbeitung.
- **Import ins Modul:** Die Aufnahme der Anfangsbestände in `afa_anlagevermoegen` (z. B. per API oder einmaliges Import-Script) ist **noch nicht umgesetzt**; die CSV dient als Vorlage. Buchhaltung prüft ggf. die 26 ohne Locosoft-Match (Kennzeichen in DATEV vs. Locosoft).

---

## 5. Nächste Schritte (nach Freigabe)

1. **Tageszulassung:** Migration (Spalte), API (Filter in Monatsberechnung/Dashboard), UI (Checkbox/Schalter).  
2. **Abgang/Locosoft:** Endpunkt oder Report „Abgangs-Kontrolle“ (VIN, DRIVE status, Locosoft `out_invoice_date`), ggf. Vergleich mit Bestandskonto.  
3. **Anfangsbestand:** Optional Import-Routine (CSV oder API), die extrahierte Positionen in `afa_anlagevermoegen` übernimmt (mit Prüfung Duplikate/VIN).
