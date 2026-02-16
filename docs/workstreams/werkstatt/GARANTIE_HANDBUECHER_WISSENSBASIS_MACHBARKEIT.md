# Garantie-Handbücher als Wissensdatenbank & Referenz zur Auftragskontrolle

**Workstream:** Werkstatt  
**Stand:** 2026-02-16  
**Status:** Machbarkeitsprüfung & Vorschlag (noch keine Implementierung)

---

## 1. Ziel

Die Garantie-Handbücher (Opel, Hyundai, Leapmotor sowie Garantie-Richtlinien) als **Wissensdatenbank und Referenz zur Auftragskontrolle** im Garantiemodul einbinden – **analog zum Unfallschaden-Modul** (M4 Wissensdatenbank + M1 Vollständigkeitscheck).

**Genannte Dokumente (Anhang):**

| Dokument | Vermutliche Marke/Verwendung |
|----------|------------------------------|
| Garantie-Richtlinie Stand 01-2026.pdf | Allgemein / übergreifend |
| Garantie-Richtlinie Hyundai Stand 02-2024.pdf | Hyundai |
| Garantie-Handbuch Opel Stand Mai 2025.pdf | Opel / Stellantis |
| Garantiehandbuch Leapmotor.pdf | Leapmotor |

**Hinweis:** Die PDFs liegen aktuell auf dem Windows-Rechner (`c:\Users\...\AppData\Local\Temp\26\`). Für eine Umsetzung im Portal müssen sie auf dem Server (z. B. unter `/opt/greiner-portal/` oder einem gemounteten Laufwerk) bereitgestellt werden.

---

## 2. Referenz: Unfallschaden-Modul (wie machen wir es dort?)

### 2.1 M4 – Wissensdatenbank

- **DB:** `unfall_checkliste_positionen`, `unfall_urteile`, `unfall_urteile_checkliste`, `unfall_textbausteine`, `unfall_textbausteine_positionen`
- **API:** `api/unfall_wissensbasis_api.py`  
  - Checkliste (typische Kürzungspositionen), Urteile, Zuordnung Urteil ↔ Position  
  - Textbausteine (UE IWW, gescrapt), externe Quellen (Links)
- **UI:** `templates/aftersales/unfall_wissensdatenbank.html`  
  - Zwei Spalten: links Checkliste, rechts Rechtsprechung/Urteile; Suche; externe Referenzquellen
- **Inhalt:** Strukturierte Einträge (Aktenzeichen, Kurzfassung, Kategorie) + Verknüpfung zu Checklisten-Positionen

### 2.2 M1 – Auftragskontrolle (Vollständigkeitscheck)

- **API:** `api/unfall_rechnungspruefung_api.py`  
  - Aufträge aus Locosoft (Versicherung als Zahler), pro Auftrag: **Check gegen Checkliste** (Ebene 1: Gutachten-Positionen vs. Rechnung, Ebene 2: 12 Standard-Positionen)
- **Logik:** Mapping von `text_line` (loco_labours) zu Checklisten-IDs; Ampelsystem (Grün/Gelb/Rot), Warnung bei fehlenden berechtigten Positionen

**Kernidee für Garantie:** Dieselbe Zweiteilung – (1) **Wissensdatenbank** zum Nachschlagen und (2) **Auftragskontrolle** (Checkliste/Regeln gegen Garantieauftrag), mit Referenz auf die Handbücher.

---

## 3. Ist-Zustand Garantie-Modul

- **API:** `api/garantie_auftraege_api.py` – offene Garantieaufträge aus Locosoft, Garantieakte-Status (Ordner, Metadaten)
- **Routes:** `routes/aftersales/garantie_routes.py` – Übersicht Garantieaufträge, Live-Dashboard (Mockup)
- **UI:** `garantie_auftraege_uebersicht.html` – Tabelle Aufträge, Filter Marke (Opel/Hyundai), Garantieakte anlegen/öffnen
- **Keine** Wissensdatenbank, **keine** Prüfung von Aufträgen gegen Handbuch-Regeln

---

## 4. Machbarkeitsoptionen

### Option A: Handbücher nur als Referenz (Links/Downloads)

**Inhalt:**  
PDFs in einem geschützten Bereich ablegen (z. B. `static/garantie/handbuecher/` oder Netzlaufwerk), im Garantie-Bereich Links anzeigen: „Handbuch Opel“, „Handbuch Hyundai“, „Handbuch Leapmotor“, „Garantie-Richtlinie“.

**Auftragskontrolle:** Keine automatische Prüfung; Nutzer schlägt bei Bedarf im Handbuch nach.

| Kriterium | Bewertung |
|-----------|-----------|
| Machbarkeit | ✅ Sehr hoch |
| Aufwand | Gering (Ablage + Seite mit Links, ggf. Berechtigung) |
| Nutzen für „Auftragskontrolle“ | Nur indirekt (manuelles Nachschlagen) |
| Analog zu Unfall M4 | Nur teilweise (keine strukturierte Wissensbasis, keine Suche) |

---

### Option B: PDF-Text extrahieren, durchsuchbar machen (Wissensdatenbank light)

**Inhalt:**  
Text aus den PDFs mit z. B. PyMuPDF oder pdfplumber extrahieren und in der DB speichern (z. B. Tabelle `garantie_handbuch_abschnitte`: marke, kapitel, titel, text, seite, pdf_dateiname).  
API: Suche über Text (ILIKE oder PostgreSQL Full-Text Search).  
UI: Suchfeld „Garantie-Handbücher“, Trefferliste mit Marke, Kapitel, Ausschnitt; optional Link „PDF öffnen (Seite X)“.

**Auftragskontrolle:** Indirekt – User sucht z. B. „Rost“, „Kilometerstand“, „Dokumentation“ und erhält relevante Handbuch-Stellen.

| Kriterium | Bewertung |
|-----------|-----------|
| Machbarkeit | ✅ Machbar |
| Aufwand | Mittel (PDF-Parsing, evtl. Kapitelstruktur, Pflege bei neuen PDF-Versionen) |
| Nutzen | Hoch für Nachschlagen und schnelles Finden von Regeln |
| Analog zu Unfall M4 | Ja (durchsuchbare Referenz), aber ohne vordefinierte „Checkliste“ |

**Risiken:** PDF-Layout (Tabellen, Spalten) kann Extraktion erschweren; Rechtslage zu Vervielfältigung der Hersteller-PDFs prüfen (interner Gebrauch meist unkritisch).

---

### Option C: Strukturierte Garantie-Checkliste (wie Unfall-Checkliste) + Handbuch-Referenz

**Inhalt:**  
Aus den Handbüchern werden Themen/Prüfpunkte abgeleitet (manuell oder halbautomatisch), z. B.:  
„Dokumentation vollständig“, „Kilometerstand erfasst“, „Teileeinordnung korrekt“, „Rückruf geprüft“, „Fristen eingehalten“.  
DB analog zu Unfall: z. B. `garantie_checkliste_positionen` (bezeichnung, marke, handbuch_ref, seite/kapitel).  
Pro Eintrag Verweis auf Handbuch (Marke, Abschnitt/Seite).  
UI: Checkliste pro Marke, bei Klick auf einen Punkt: Anzeige des zugehörigen Handbuch-Abschnitts (aus Option B) oder direkter Link ins PDF.

**Auftragskontrolle:** Beim Durchgehen eines Garantieauftrags kann die Checkliste abgearbeitet werden; jede Position verweist auf die passende Handbuch-Stelle.

| Kriterium | Bewertung |
|-----------|-----------|
| Machbarkeit | ✅ Machbar |
| Aufwand | Mittel bis hoch (inhaltliche Aufbereitung, Pflege) |
| Nutzen | Sehr hoch für einheitliche Auftragskontrolle und Schulung |
| Analog zu Unfall M4 | Sehr gut (Checkliste + Referenz wie Urteile/Textbausteine) |

---

### Option D: Vollständige Auftragskontrolle (M1-ähnlich)

**Inhalt:**  
Wie Unfall M1: Garantieauftrag aus Locosoft laden, **automatisch** gegen Regeln aus den Handbüchern prüfen (z. B. Pflichtangaben, Dokumentationspflichten, Fristen).  
Dafür müssten die Regeln aus den PDFs **strukturiert** vorliegen (manuell abgeleitet oder per Extraktion/LLM – mit fachlicher Freigabe).

| Kriterium | Bewertung |
|-----------|-----------|
| Machbarkeit | ⚠️ Nur mit strukturierten Regeln |
| Aufwand | Hoch (Regelwerk definieren, an Locosoft-Daten anbinden) |
| Nutzen | Sehr hoch, wenn Regelwerk passt |
| Analog zu Unfall M1 | Ja |

**Empfehlung:** Erst nach Option B/C umsetzen; M1-artige Automatik als Ausbau (Phase 2).

---

## 5. Übersicht und Empfehlung

| Option | Aufwand | Nutzen Auftragskontrolle | Analog Unfall |
|--------|---------|---------------------------|---------------|
| A – Nur Links | Gering | Nur manuell | Teilweise |
| B – PDF durchsuchbar | Mittel | Indirekt (Suche) | Wissensbasis light |
| C – Checkliste + Handbuch-Ref | Mittel–hoch | Direkt (Checkliste) | M4 sehr nah |
| D – M1-artige Auto-Prüfung | Hoch | Automatisch | M1 |

**Vorschlag (Phasen):**

1. **Phase 1 – Referenz & Durchsuchbarkeit**  
   - Option A umsetzen: Handbücher ablegen, feste Links im Garantie-Bereich („Garantie – Handbücher & Richtlinien“).  
   - Optional direkt Option B: PDF-Text extrahieren, Tabelle + Suche, neue Seite „Garantie – Wissensdatenbank“ (analog Unfall-Wissensdatenbank, aber mit Handbuch-Abschnitten statt Urteilen).

2. **Phase 2 – Checkliste (Option C)**  
   - Garantie-Checkliste (pro Marke) mit Verweisen auf Handbuch-Kapitel/Seiten.  
   - Integration in Garantieaufträge-Übersicht oder eigene Seite „Auftragskontrolle Garantie“ mit Checkliste + Links zu den Handbücher-Treffern.

3. **Phase 3 – Automatische Prüfung (Option D)**  
   - Nur wenn gewünscht und Regelwerk aus Handbüchern definiert ist; Anbindung an Locosoft-Daten wie bei Unfall M1.

**Technische Anknüpfpunkte:**

- **Unfall:** `unfall_wissensbasis_api.py`, `unfall_wissensdatenbank.html`, Tabellen `unfall_checkliste_positionen`, `unfall_urteile`, …  
- **Garantie:** Neue API `garantie_wissensbasis_api.py` (oder Erweiterung bestehender Garantie-API), neue Tabellen z. B. `garantie_handbuch_abschnitte`, `garantie_checkliste_positionen`; neues Template „Garantie – Wissensdatenbank“ bzw. Erweiterung `garantie_auftraege_uebersicht.html` um Bereich „Handbücher / Checkliste“.

**PDF-Bereitstellung:**  
Die vier Handbücher müssen für den Server zugänglich sein (z. B. nach `/opt/greiner-portal/data/garantie_handbuecher/` kopieren oder auf ein Netzlaufwerk legen, das der App erreichbar ist). Rechtsfragen (Nutzung Hersteller-PDFs nur intern) sollten einmalig geklärt werden.

---

## 6. Nächste Schritte (ohne Code)

1. **Entscheidung:** Welche Phase (nur A, A+B, A+B+C) soll zuerst umgesetzt werden?
2. **PDFs:** Handbücher auf Server/Netzlaufwerk bereitstellen; Dateinamen und Marken-Zuordnung festlegen.
3. **Inhalt Option C:** Falls Checkliste gewünscht – welche Prüfpunkte pro Marke (Opel, Hyundai, Leapmotor) sollen aus den Handbüchern abgeleitet werden?
4. **Navigation:** Wissensdatenbank/Handbücher unter „Service → Werkstatt“ bzw. „Garantie“ verlinken (analog Unfall-Rechnungsprüfung & Wissensdatenbank).

Damit ist die Einbindung der Garantie-Handbücher als Wissensdatenbank und Referenz zur Auftragskontrolle **machbar** und an das Unfallschaden-Modul anlehnbar umsetzbar; empfohlen wird ein stufenweiser Aufbau (zuerst Referenz/Durchsuchbarkeit, dann Checkliste, optional automatische Prüfung).
