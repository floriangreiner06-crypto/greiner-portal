# Plan: Liquiditätsplanung – Kategorisierung & Tilgungsmuster

**Workstream:** Controlling  
**Stand:** 2026-02-28  
**Ziel:** Belastbare Liquiditätsplanung durch (1) kategorisierte Einnahmen/Ausgaben im Bankenspiegel und (2) erkennbare Muster bei Abschlags- und Tilgungszahlungen der Autobanken (Stellantis, Santander, Hyundai Finance).

---

## Ausgangslage

| Modul | Status | Relevanz Liquidität |
|-------|--------|---------------------|
| **Kontenübersicht** | ✅ | Salden live aus Locosoft (070101/071101) |
| **Bankenspiegel Dashboard** | ✅ | Einnahmen/Ausgaben letzte 30 Tage, aktueller Monat; **keine Kategorien** |
| **OPOS** | 🔧 Noch nicht final | Offene Posten Fahrzeugverkauf – eher Debitoren, nicht direkt Bank |
| **Einkaufsfinanzierung** | ✅ | Bestandslisten Stellantis/Santander/Hyundai (Saldo, Zinsen, Endfälligkeit) |

**Datenbank (PostgreSQL):**
- `transaktionen`: `konto_id`, `buchungsdatum`, `betrag`, `verwendungszweck`, `buchungstext`, `gegenkonto_name`, `gegenkonto_iban`, **`kategorie`**, **`unterkategorie`** (vorhanden, aktuell ungenutzt)
- `tilgungen`: Fälligkeiten + Beträge pro Finanzinstitut (u. a. aus Hyundai-Tilgungen-Import)
- Tabelle `kategorien` (Stammdaten für Kategorienamen) existiert in PostgreSQL **nicht** (war nur in Phase1 SQLite geplant)

**KI:** LM Studio (RZ) in `api/ai_api.py` – Modell z. B. `mistralai/magistral-small-2509` für Klassifikation/JSON-Antworten bereits im Einsatz (Arbeitskarten, Hilfe). Use Case „Transaktions-Kategorisierung“ ist in `docs/KI_USE_CASES_GREINER_AUTOHAUS_TAG195.md` (Priorität 3) beschrieben.

---

## Teil 1: Einnahmen/Ausgaben im Bankenspiegel kategorisieren

### 1.1 Sinnvolle Kategorisierung

**Zweck:** Im Dashboard und in Auswertungen Einnahmen/Ausgaben nach Kategorie (z. B. Gehalt, Miete, Steuern, Einkaufsfinanzierung Tilgung, Lieferanten, Sonstiges) darstellen → bessere Liquiditätsplanung und Soll-Ist-Abgleich.

**Mögliche Kategorien (Vorschlag, anpassbar):**
- **Einnahmen:** Kunden (Verkauf/Service), Erstattungen, Zinsen/Guthaben, Sonstige Einnahmen
- **Ausgaben:** Einkaufsfinanzierung (Stellantis/Santander/Hyundai), Gehälter, Miete, Versicherung, Steuern, Lieferanten, Kraftstoff/Energie, Sonstige Ausgaben
- **Intern:** Interne Umbuchungen (bereits im Dashboard separiert)

**Datenbasis pro Buchung:** `verwendungszweck`, `buchungstext`, `gegenkonto_name`, `gegenkonto_iban`, `betrag`, `konto_id` (Kontotyp/Name aus `konten`).

### 1.2 Option A: Regelbasierte Kategorisierung (ohne KI)

- **Vorteil:** Deterministisch, keine Abhängigkeit von LM Studio, schnell umsetzbar.
- **Umsetzung:** Mapping-Tabelle (z. B. `transaktion_kategorien_regeln`: Suchbegriffe im Verwendungszweck/Buchungstext/Gegenkonto, zugeordnete `kategorie`/`unterkategorie`). Beim MT940/PDF-Import oder per Nachtlauf: neue Transaktionen ohne Kategorie durchlaufen die Regeln und werden aktualisiert.
- **Nachteil:** Pflege der Regeln; unbekannte Buchungen bleiben „Sonstiges“.

### 1.3 Option B: KI-gestützte Kategorisierung (LM Studio)

- **Vorteil:** Auch unbekannte Verwendungszwecke werden vorgeschlagen; weniger manuelle Regeln.
- **Umsetzung:** Neuer Endpoint z. B. `POST /api/ai/kategorisiere/transaktion` (wie in KI_USE_CASES beschrieben). Input: `verwendungszweck`, `buchungstext`, `gegenkonto_name`, `betrag`. Output: `kategorie`, `unterkategorie` aus festem Satz Kategorien (JSON). Optional: Batch für unkategorisierte Transaktionen (z. B. 50 pro Aufruf).
- **Nachteil:** Abhängigkeit von LM Studio (Verfügbarkeit/Timeout); Kosten/Latenz bei großen Mengen; Ergebnis ggf. manuell prüfbar/überarbeitbar.

### 1.4 Option C: Hybrid (empfohlen)

1. **Regeln zuerst:** Feste Muster (z. B. „Stellantis“, „Santander“, „Hyundai“, „Gehalt“, „Miete“, interne Umbuchungen) regelbasiert zuordnen.
2. **KI für Rest:** Alle Transaktionen ohne Treffer an LM Studio senden (Batch), Vorschlag speichern.
3. **Manuelle Korrektur + Lernen:** Wo Nutzer Korrekturen vornehmen, optional als neue Regeln speichern (später).

**Machbarkeit:** ✅ **hoch**. Spalten `kategorie`/`unterkategorie` vorhanden; KI-API und Use Case bereits beschrieben; Dashboard kann nach Kategorie filtern/aggregieren.

**Empfehlung:** Zuerst kleines Set Regeln (Einkaufsfinanzierung, Gehalt, Miete, Interne Umbuchungen), dann KI für „Sonstiges“ ergänzen und im Dashboard „Einnahmen/Ausgaben nach Kategorie“ (z. B. Chart/Tabelle) anzeigen.

---

## Teil 2: Muster bei Abschlags- und Tilgungszahlungen (Autobanken)

### 2.1 Wo liegen die Daten?

| Quelle | Inhalt | Abschlags-/Tilgungsinfo |
|--------|--------|---------------------------|
| **Santander CSV** | Bestandsliste (Saldo, Finanzierungssumme, Endfälligkeit, Zins Startdatum, Zinsen letzte Periode/Gesamt) | ❌ Keine einzelnen Raten/Tilgungszahlungen; nur Stichtag-Saldo |
| **Hyundai Finance CSV** | Bestandsliste (VIN, Saldo, Finanz.-Betrag, Rechnungsdatum, Finanzierungsbeginn/-ende, Zinsbeginn) | ❌ Keine einzelnen Raten/Tilgungszahlungen |
| **Hyundai Tilgungen** | Eigenes CSV aus Portal-Scraper (`hyundai_tilgungen_scraper.py`) → `tilgungen` | ✅ **Ja:** Fällig am, Betrag, VIN, Finanzierungsnr., Status, Lastschrift Referenz |
| **Stellantis** | Excel aus ZIP (Bestandsdaten pro RRDI) | ❌ In den Imports nur Bestand, keine Ratenliste |
| **Bank (MT940/PDF)** | Alle Kontobewegungen in `transaktionen` | ✅ **Ja:** Tatsächliche Abbuchungen (Betrag, Datum, Verwendungszweck, Gegenkonto) |

**Fazit:** Die **tatsächlichen** Tilgungs-/Abschlagszahlungen erscheinen als normale Lastschriften auf den Hausbankkonten. Die **geplanten** Tilgungen sind nur für Hyundai (und ggf. weitere, wenn Tilgungen-Export vorhanden) in der Tabelle `tilgungen` abgebildet.

### 2.2 Was steht in den CSVs? (Kurzüberblick)

- **Santander Bestandsliste:** Finanzierungsnr., VIN, Finanzierungsstatus, Dokumentstatus, Finanzierungssumme, Saldo, Rechnungsbetrag/-nummer/-datum, Aktivierungsdatum, Endfälligkeit, Zins Startdatum, Lieferdatum, Produkt, Herstellername, Modellname, Farbe, HSN/TSN, Zinsen letzte Periode/Gesamt. **Keine Spalte für Raten oder Tilgungsplan.**
- **Hyundai stockList:** VIN, Finanzierungsnr., -status, -betrag, Saldo, Rechnungsdatum, Finanzierungsbeginn/-ende, Zinsbeginn, Modell, Hersteller, Produkt. **Keine Raten/Tilgungen.**
- **Hyundai Tilgungen (separater Export):** Fahrgestellnr., Fällig am, Betrag, Beschreibung, Status, Lastschrift Referenz, OEM Rechnungsnr., Finanzierungsnr. **→ Ideal für Abgleich mit Bankbuchungen (Betrag + Datum + ggf. Referenz).**
- **Stellantis Excel:** Bestandsorientiert (Fahrzeuge, Salden), **keine Ratenliste** in den beschriebenen Imports.

### 2.3 Mustererkennung: Was ist nötig?

**Ziel:** Belastbare Liquiditätsplanung → Vorhersage/Erkennung, wann welche Beträge für Einkaufsfinanzierung abgehen.

**Option 1 – Nutzung der Tabelle `tilgungen` (Hyundai bereits vorhanden):**
- **Hyundai:** Tilgungsplan ist im System (Scraper + Import). Liquiditätsplanung „nächste 7/30 Tage“ pro Institut aus `tilgungen` ist möglich.
- **Santander/Stellantis:** Wenn die Banken/Portale einen Tilgungsplan oder Ratenexport anbieten: analog zu Hyundai Scraper/Import in `tilgungen` übernehmen → dann einheitliche Auswertung „geplante Tilgungen“ für alle drei.

**Option 2 – Rückwärts aus Bankbuchungen (transaktionen):**
- Transaktionen mit bekanntem Gegenkonto/Verwendungszweck (z. B. „Stellantis“, „Santander“, „Hyundai“) filtern und als „Einkaufsfinanzierung Tilgung“ kategorisieren (Teil 1).
- **Muster:** Wiederkehrende Beträge, gleicher Gegenkonto-Name, ähnliches Datum (z. B. monatlich). Daraus können **durchschnittliche/typische** Tilgungsbeträge und -termine abgeleitet werden – aber keine exakten zukünftigen Raten ohne Vertragsdaten.
- **Einschränkung:** Ohne Tilgungsplan von Stellantis/Santander bleibt die „Planung“ eher eine Hochrechnung aus der Vergangenheit (z. B. „Ø Ausgaben Einkaufsfinanzierung pro Monat“).

**Option 3 – Mehr Infos von den Banken:**
- **Santander:** Anforderung an Buchhaltung/Controlling: Gibt es einen Export „Ratenplan“ oder „Tilgungsplan“ (CSV/Excel)? Wenn ja → Import wie bei Hyundai `tilgungen`.
- **Stellantis:** Gleiche Frage (Raten/Tilgungsplan pro Vertrag). Wenn nur Bestandsliste: Option 2 nutzen.

### 2.4 Empfehlung Teil 2

1. **Kurzfristig (ohne weitere CSV-Infos):**
   - Regelbasierte Kategorisierung in `transaktionen` für bekannte Gegenkonten/Verwendungszwecke (Stellantis, Santander, Hyundai) → Auswertung „Ausgaben Einkaufsfinanzierung“ pro Monat und Prognose auf Basis historischer Monatsmittel.
   - Dashboard „Geplante Tilgungen“ aus `tilgungen` (derzeit vor allem Hyundai) anzeigen; sobald Santander/Stellantis Tilgungsdaten liefern, in dieselbe Tabelle importieren.

2. **Mittelfristig:**
   - Bei Santander und Stellantis klären: **Gibt es CSV/Excel mit Fälligkeiten und Beträgen (Tilgungsplan)?** Wenn ja → Parsing und Import in `tilgungen` (analog Hyundai), dann einheitliche Liquiditätsansicht „Tilgungen nächste 30/90 Tage“.

3. **Optional – Abgleich Bank ↔ Plan:**
   - Für Hyundai: Abgleich „Tilgung aus `tilgungen`“ mit „Transaktion in `transaktionen`“ (Betrag + Zeitfenster + ggf. Lastschrift Referenz), um zu markieren, ob geplante Tilgung tatsächlich eingezogen wurde (Status-Update, z. B. „bezahlt“).

---

## Teil 3: Übersicht Machbarkeit

| Maßnahme | Machbarkeit | Aufwand (grob) | Abhängigkeiten |
|----------|-------------|----------------|----------------|
| **1. Kategorisierung regelbasiert** | ✅ Hoch | 1–2 Tage | Keine |
| **2. Kategorisierung KI (LM Studio)** | ✅ Hoch | 1–2 Tage | LM Studio erreichbar |
| **3. Dashboard „Einnahmen/Ausgaben nach Kategorie“** | ✅ Hoch | ~1 Tag | Kategorien in `transaktionen` befüllt |
| **4. Tilgungen Hyundai nutzen (bereits da)** | ✅ Sofort | < 0,5 Tag | Dashboard/API um Anzeige „Tilgungen nächste Tage“ erweitern |
| **5. Tilgungsmuster aus Bankbuchungen (Stellantis/Santander/Hyundai)** | ✅ Hoch | 1–2 Tage | Regeln/Filter für Gegenkonto/Verwendungszweck |
| **6. Santander/Stellantis Tilgungsplan importieren** | 🟡 Bedingt | 1–2 Tage pro Institut | **Mehr Infos nötig:** Liefern die Banken CSV/Excel mit Raten/Fälligkeiten? |
| **7. Abgleich Bankbuchung ↔ Tilgung (Hyundai)** | ✅ Machbar | ~1 Tag | Optional; verbessert Nachvollziehbarkeit |

---

## Nächste Schritte (Vorschlag)

1. **Kategorien-Stammdaten:** Tabelle `kategorien` (oder einfache Konfiguration) für Bankenspiegel-Kategorien anlegen und in CONTEXT.md dokumentieren.
2. **Regelbasierte Kategorisierung:** Feste Muster (Einkaufsfinanzierung, Gehalt, Miete, Interne Umbuchungen) implementieren; bei Import oder per Task `transaktionen.kategorie`/`unterkategorie` setzen.
3. **KI-Endpoint:** `POST /api/ai/kategorisiere/transaktion` implementieren (Input: Verwendungszweck, Buchungstext, Gegenkonto, Betrag → Output: Kategorie). Optional: Batch für Unkategorisierte.
4. **Dashboard:** Im Bankenspiegel Dashboard „Einnahmen/Ausgaben nach Kategorie“ (z. B. Chart/Tabelle für letzten Monat / letzte 30 Tage) anzeigen.
5. **Tilgungen:** Ansicht „Geplante Tilgungen (nächste 30 Tage)“ aus `tilgungen` ins Dashboard oder Einkaufsfinanzierung integrieren; Abklärung mit Buchhaltung: Haben Santander/Stellantis einen Tilgungsplan-Export?
6. **Doku:** In CONTEXT.md (Controlling) und ggf. CLAUDE.md „Liquiditätsplanung / Kategorisierung“ ergänzen.

---

## Referenzen

- CONTEXT.md (Controlling), CLAUDE.md  
- `api/bankenspiegel_api.py` (Dashboard, Transaktionen), `api/ai_api.py` (LM Studio)  
- `scripts/imports/import_mt940.py` (Transaktionen-Struktur), `scripts/imports/import_santander.py`, `import_hyundai_finance.py`, `import_stellantis.py`  
- `scripts/imports/import_hyundai_data.py` (Tilgungen-Import), `tools/scrapers/hyundai_tilgungen_scraper.py`  
- `docs/KI_USE_CASES_GREINER_AUTOHAUS_TAG195.md` (Priorität 3: Transaktions-Kategorisierung)  
- DB: `transaktionen`, `tilgungen`, `fahrzeugfinanzierungen`
