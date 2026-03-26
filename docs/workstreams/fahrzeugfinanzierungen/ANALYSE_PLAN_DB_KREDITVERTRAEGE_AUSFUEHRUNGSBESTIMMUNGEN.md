# Analyse & Plan: DB für Kreditverträge und Ausführungsbestimmungen

**Stand:** 2026-03  
**Workstreams:** Fahrzeugfinanzierungen, Controlling (Liquidität/Zinsen), Verkauf (Kalkulation/Verkaufsprogramme)  
**Auslöser:** Santander-Modalitäten werden geliefert; Zinsfreiheit Neuwagen Stellantis etc. stehen in Ausführungsbestimmungen – sollen abfragbar sein.

---

## 1. Ausgangslage und Ziel

### 1.1 Problem

- **Zinsfreiheit, Tilgungsregeln, Sonderkonditionen** (z. B. Neuwagen Stellantis, Santander, Hyundai) stehen heute in:
  - **Ausführungsbestimmungen** (PDF/Dokumente der Banken/Hersteller),
  - **Verkaufsprogrammen** (Rundschreiben, z. B. „0 %-Finanzierung BEV“, „Zinsfreiheit 90 Tage“),
  - **Excel/CSV-Imports** (Stellantis: Spalte „Zinsfreiheit (Tage)“ pro Fahrzeug; Santander: kein Zinsfreiheitsfeld).
- Es gibt **keine zentrale, durchsuchbare Quelle** für „Welche Modalitäten gelten für Vertrag X?“ oder „Zinsfreiheit Neuwagen Stellantis?“ – die Logik steckt in Doku und Code verteilt.

### 1.2 Ziel

- **Eine DB** (bzw. ein zusammenhängendes Modell) für:
  - **Kreditvertragstypen / Rahmenbedingungen** (Anbieter, Produkt, Gültigkeit),
  - **Ausführungsbestimmungen / Modalitäten** (regelhafte Bedingungen: Zinsfreiheit, Tilgung, Zinssatz, Sonderregeln),
- aus der wir **intelligent Daten herausholen** können: z. B. „Zinsfreiheit für EK-Finanzierung Neuwagen Stellantis?“ → „90 Tage ab Vertragsbeginn“, oder „Santander: Tilgungsmodalitäten?“ → strukturierte Treffer + Verweis auf Quelle.

### 1.3 Bezug zu bestehenden Daten

| Was wir schon haben | Rolle |
|--------------------|--------|
| **fahrzeugfinanzierungen** | **Einzelverträge pro VIN** (Saldo, Zinsen, zinsfreiheit_tage, vertragsbeginn, finanzinstitut). Keine „Regelwerke“. |
| **Verkaufsprogramme (Regelwerk_*.json)** | **Verkaufsboni** (Prämien, 0%-Finanzierung BEV etc.) aus PDFs per KI; liegen im Ordner `docs/workstreams/verkauf/Kalkulationstool/` (inkl. vp-13 Stellantis, Hyundai Q1). Teilweise **Finanzierungs-Konditionen** (z. B. 0 % BEV), aber keine vollständigen Ausführungsbestimmungen. |
| **ZINSFREIHEIT_STELLANTIS_HYUNDAI.md** | Beschreibt, **woher** wir Zinsfreiheit heute nehmen (Excel-Spalte, CSV Zinsbeginn); nicht die **Regel** „wie viele Tage für welches Produkt“. |
| **Santander-Modalitäten** | Werden von euch nachgeliefert – sollen in dieselbe Logik (Modalitäten-DB) passen. |

---

## 2. Analyse: Was soll abfragbar sein?

### 2.1 Typische Fragen (Beispiele)

- **Zinsfreiheit:** „Wie viele Tage Zinsfreiheit hat EK-Finanzierung Neuwagen Stellantis?“ (heute: pro Fahrzeug aus Excel; die **Regel** „90 Tage“ o. Ä. steht in Ausführungsbestimmungen.)
- **Santander:** „Welche Modalitäten gelten für Santander EK-Finanzierung?“ (Laufzeit, Zinsbeginn, Tilgung, Sonderkonditionen – sobald Dokument geliefert ist.)
- **Hyundai:** „Zinsfreiheit Hyundai Finance?“ (bisher: Zinsbeginn aus CSV; Regelwerk optional aus Vertriebsprogramm.)
- **Verkaufsprogramm ↔ Finanzierung:** „0 %-Finanzierung BEV – unter welchen Bedingungen?“ (Schnittmenge Verkaufsprogramm + Ausführungsbestimmungen.)

### 2.2 Datenquellen (heute und geplant)

| Quelle | Inhalt | Heute | Geplant |
|--------|--------|--------|---------|
| **Stellantis Excel** | Zinsfreiheit (Tage) **pro Fahrzeug** | Import → `fahrzeugfinanzierungen.zinsfreiheit_tage` | Unverändert; **Regel** (z. B. „NW 90 Tage“) in Ausführungsbestimmungen-DB. |
| **Stellantis Ausführungsbestimmungen** | Allgemeine Vertrags-/Zinsregeln | Nicht in DB | PDF/Dokument → Extraktion (KI/manuell) → DB. |
| **Santander CSV** | Bestand, Zins Startdatum, Zinsen | Import → `fahrzeugfinanzierungen` | Unverändert. |
| **Santander Modalitäten** | Vertrags- und Tilgungsmodalitäten | — | Nach Lieferung: in gleiche DB-Struktur (Dokument + strukturierte Regeln). |
| **Hyundai Vertriebsprogramm / Finance** | Zinsbeginn pro Fahrzeug, ggf. Regeln | CSV → zins_startdatum; Verkaufsprogramm als Regelwerk_*.json | Optional: Zinsfreiheits-**Regel** in Ausführungsbestimmungen-DB. |
| **Verkaufsprogramme NW (Kalkulationstool)** | Boni, 0%-Finanzierung BEV, etc. | Regelwerk_Stellantis.json, Regelwerk_Hyundai.json (PDF → KI) | Bleiben; können auf **Vertrags-/Modalitäten-DB** verweisen, wo gleiche Kondition (z. B. 0 % BEV) als „Regel“ hinterlegt ist. |

---

## 3. Vorschlag: DB-Modell (Kreditverträge + Ausführungsbestimmungen)

### 3.1 Idee: Zwei Ebenen

1. **Vertrags-/Produktebene** („Welcher Anbieter, welches Produkt, von wann bis wann?“)  
   → Tabellen für Anbieter, Vertragsart/Produkt, Gültigkeit, optional Verweis auf Dokument.
2. **Regel-/Modalitätenebene** („Was gilt konkret?“)  
   → Ausführungsbestimmungen als **strukturierte Einzelregeln** (z. B. Zinsfreiheit_Tage = 90, Produkt = EK-Finanzierung NW Stellantis) plus optional **Volltext** (Absatz aus PDF) für Suche und Nachweis.

So können wir sowohl **programmatisch** (z. B. Zinsberechnung, Liquiditätsvorschau) als auch **nutzerorientiert** („Zeig mir die Modalitäten Santander“) darauf zugreifen.

### 3.2 Tabellen (Vorschlag)

#### A) Anbieter / Vertragsarten (Referenz)

- **kredit_anbieter**  
  - id, name (z. B. „Santander“, „Stellantis“, „Hyundai Finance“, „Genobank“), kuerzel, aktiv.
- **kredit_vertragsart**  
  - id, anbieter_id, bezeichnung (z. B. „EK-Finanzierung Neuwagen“, „EK-Finanzierung Gebrauchtwagen“, „Leasing“), produkt_code (optional), gueltig_von, gueltig_bis (optional).

(Damit können wir später „Santander EK-Finanzierung NW“ von „Stellantis EK-Finanzierung NW“ trennen und pro Vertragsart Regeln hinterlegen.)

#### B) Dokumente (Quelle der Regeln)

- **kredit_dokumente**  
  - id, anbieter_id (optional), titel (z. B. „Santander Modalitäten 2026“, „Stellantis Ausführungsbestimmungen EK-Finanzierung“), dokument_typ („Ausführungsbestimmung“, „Modalität“, „Verkaufsprogramm-Auszug“), dateipfad oder url (optional), eingang_am, bemerkung.  
  - Ermöglicht: „Diese Regel stammt aus Dokument X.“

#### C) Ausführungsbestimmungen / Modalitäten (strukturiert + Suchtext)

- **kredit_ausfuehrungsbestimmungen**  
  - id, vertragsart_id (FK → kredit_vertragsart), dokument_id (FK → kredit_dokumente, optional),  
  - **regel_typ** (z. B. „zinsfreiheit_tage“, „zinssatz_pct“, „tilgungsart“, „laufzeit_max“, „sonderkondition“),  
  - **regel_key** (maschinenlesbar, z. B. „zinsfreiheit_tage“), **regel_wert** (z. B. 90 oder „90“), einheit („Tage“, „Prozent“, „Euro“),  
  - **bedingung** (optional, z. B. „nur Neuwagen“, „nur BEV“),  
  - **volltext** (optional: Absatz aus PDF für Volltextsuche und Nachweis),  
  - gueltig_von, gueltig_bis (optional),  
  - sortierung, aktiv.

**Beispiel-Zeilen:**

| vertragsart_id | regel_typ        | regel_key           | regel_wert | einheit | bedingung   | volltext (Auszug)                    |
|----------------|------------------|---------------------|------------|---------|-------------|--------------------------------------|
| Stellantis EK NW | zinsfreiheit_tage | zinsfreiheit_tage   | 90         | Tage    | Neuwagen    | „Die Zinsfreiheit beträgt 90 Tage …“ |
| Santander EK  | tilgungsart      | tilgung             | endfaellig | —       | —           | „Endfällige Darlehen …“              |
| Santander EK  | zins_start       | zins_start          | aus_csv    | —       | —           | „Zinsbeginn siehe …“                 |

So können wir:
- **Strukturiert abfragen:** „Alle Regeln mit regel_key = 'zinsfreiheit_tage' für Anbieter Stellantis“.
- **Volltextsuche:** „Zinsfreiheit“ in `volltext` suchen und Treffer mit Vertragsart + Dokument anzeigen.
- **Santander:** Sobald Modalitäten vorliegen, pro Vertragsart Zeilen anlegen (regel_typ/regel_key/regel_wert/volltext).

#### D) Optional: Verknüpfung Verkaufsprogramm ↔ Vertragsart

- In **vfw_verkaufsprogramme** / **vfw_programm_konditionen** (VFW-Implementierungsplan Phase 2) könnte ein optionales Feld **vertragsart_id** oder **kredit_regel_id** stehen, wenn eine Kondition (z. B. „0 %-Finanzierung BEV“) derselben fachlichen Regel wie in der Modalitäten-DB entspricht. Dann: eine Stelle für die „Wahrheit“, mehrere Nutzer (Kalkulation, Liquidität, EK-Übersicht).

### 3.3 Volltextsuche

- **PostgreSQL:** Spalte `volltext` in `kredit_ausfuehrungsbestimmungen` mit **tsvector**-Index (Full-Text Search), damit Suchen wie „Zinsfreiheit Neuwagen“ oder „Tilgung Santander“ schnell gehen.
- **API:** z. B. `GET /api/fahrzeugfinanzierungen/modalitaeten?q=zinsfreiheit&anbieter=Stellantis` → strukturierte Regeln + Treffer mit Volltext-Auszug.

---

## 4. Datenfluss und Pflege

### 4.1 Ersteinrichtung

1. **Anbieter** anlegen: Santander, Stellantis, Hyundai Finance, Genobank (ggf. weitere).
2. **Vertragsarten** anlegen: z. B. „Stellantis EK-Finanzierung NW“, „Stellantis EK-Finanzierung GW“, „Santander EK-Finanzierung“, „Hyundai Finance EK“.
3. **Dokumente** anlegen: z. B. „Stellantis Ausführungsbestimmungen“ (PDF/Link), „Santander Modalitäten 2026“ (sobald geliefert).
4. **Ausführungsbestimmungen** befüllen:
   - **Stellantis:** Zinsfreiheit 90 Tage (oder der in den AB genannte Wert) aus bestehender Doku/Excel-Logik + optional Absatz aus PDF; Zinssatz 9,03 % p.a.
   - **Santander:** Sobald Modalitäten da sind – Extraktion (KI oder manuell) in regel_typ/regel_key/regel_wert/volltext.
   - **Hyundai:** Optional Zinsfreiheitsregel aus Vertriebsprogramm oder AB.

### 4.2 Verkaufsprogramme (NW) – Einordnung

- **Ordner:** `docs/workstreams/verkauf/Kalkulationstool/` (inkl. vp-13 Stellantis, Hyundai Q1, Regelwerk_*.json) bleibt die Quelle für **Verkaufsboni** (Prämien, 0%-Finanzierung BEV etc.).
- **Schnittstelle:** Wo eine Verkaufsprogramm-Kondition **dieselbe** fachliche Regel wie die Ausführungsbestimmungen betrifft (z. B. 0 % Finanzierung BEV), kann ein Eintrag in `kredit_ausfuehrungsbestimmungen` angelegt werden mit Verweis auf Vertragsart; das Kalkulationstool kann dann optional aus der **Modalitäten-DB** lesen (einheitliche Quelle) oder weiter aus dem Regelwerk_*.json (Phase 1).
- **KI-Pipeline:** Bereits im Einsatz (vfw_rundschreiben_regelwerk_ki.py, merge_regelwerk.py). Für **reine** Ausführungsbestimmungen (nur Modalitäten, keine Boni) könnte ein ähnlicher Lauf genutzt werden: PDF → Text → LM Studio (Struktur: regel_typ, regel_wert, bedingung) → Vorschlag → Prüfung → Speicherung in `kredit_ausfuehrungsbestimmungen`.

### 4.3 Santander-Modalitäten (nach Lieferung)

- Dokument in **kredit_dokumente** anlegen (titel, dokument_typ = „Modalität“, dateipfad falls gespeichert).
- Inhalt: Extraktion (manuell oder per KI) in **kredit_ausfuehrungsbestimmungen** (vertragsart = Santander EK, regel_typ/regel_key/regel_wert/volltext).
- Danach: Abfragen wie „Santander Tilgungsmodalitäten?“ oder „Zinsbeginn Santander?“ aus der DB beantwortbar; Liquiditätsvorschau und EK-Übersicht können darauf aufbauen.

---

## 5. Phasierung (Plan)

| Phase | Inhalt | Aufwand (grober Richtwert) |
|-------|--------|----------------------------|
| **1** | Schema: Tabellen **kredit_anbieter**, **kredit_vertragsart**, **kredit_dokumente**, **kredit_ausfuehrungsbestimmungen** (Migration), Full-Text-Index auf volltext. | 0,5–1 Tag |
| **2** | Stammdaten: Anbieter + Vertragsarten anlegen; erste Ausführungsbestimmungen (Stellantis Zinsfreiheit, Zinssatz 9,03 %; Hyundai/Santander Platzhalter). API: Lesen (Liste, Filter, Volltextsuche). | 1–2 Tage |
| **3** | **Santander-Modalitäten:** Nach Lieferung Dokument erfassen, Regeln extrahieren (KI oder manuell), in DB pflegen. Abfrage „Modalitäten Santander“ aus Portal/API. | abhängig von Umfang des Dokuments |
| **4** | Nutzung in bestehenden Modulen: z. B. EK-Übersicht/Liquidität „Zinsfreiheit aus DB“ anzeigen; Kalkulationstool optional Verknüpfung zu Vertragsart. | 0,5–1 Tag je Modul |
| **5** | Optional: Weitere Dokumente (Stellantis AB, Hyundai Finance AB) per KI extrahieren, Vorschlag → Freigabe → DB. | iterativ |

---

## 6. Kurzfassung

- **Ja**, wir können eine **DB für Kreditverträge und Ausführungsbestimmungen** aufbauen, aus der wir **intelligent** Daten herausholen (Zinsfreiheit, Tilgung, Zinssatz, Sonderkonditionen pro Anbieter/Produkt).
- **Vorschlag:** Vier Tabellen (Anbieter, Vertragsart, Dokument, Ausführungsbestimmungen) mit strukturierten Regeln (regel_typ/regel_key/regel_wert) plus optionalem Volltext für Suche und Nachweis; PostgreSQL Full-Text-Search.
- **Santander-Modalitäten:** Sobald geliefert, in dieselbe Struktur einpflegen (Dokument + strukturierte Regeln).
- **Verkaufsprogramme NW** (Ordner Kalkulationstool, Regelwerk_*.json) bleiben die Quelle für Boni/Prämien; wo dieselbe Regel (z. B. 0 % BEV) auch eine „Vertrags-/Modalitäten-Regel“ ist, kann die Ausführungsbestimmungen-DB die gemeinsame Referenz werden.
- **Nächster Schritt:** Phase 1 (Migration + Schema) umsetzen; parallel Platzhalter für Santander vorbereiten, damit du die Modalitäten nachreichen kannst und wir sie direkt einpflegen.

---

**Umsetzung (2026-03):**  
- **Phase 1+2 umgesetzt:** Migration `migrations/add_kredit_modalitaeten_tables.sql`, Seed `migrations/seed_kredit_modalitaeten.sql`, API `GET /api/bankenspiegel/modalitaeten` und `GET /api/bankenspiegel/modalitaeten/suche?q=...`. Test: `scripts/tests/test_modalitaeten_api.py`.

**Referenzen:**  
- `docs/workstreams/controlling/ZINSFREIHEIT_STELLANTIS_HYUNDAI.md`  
- `docs/workstreams/controlling/SANTANDER_ZINSEN_ABSCHLAEGE_LIQUIDITAET.md`  
- `docs/workstreams/verkauf/Kalkulationstool/VERKAUFSPROGRAMME_PDF_KI_AUFBEREITUNG.md`, `README_REGELWERK_KI.md`  
- `docs/workstreams/verkauf/VFW_VERMARKTUNG_IMPLEMENTIERUNGSPLAN.md` (Phase 2: vfw_verkaufsprogramme, vfw_programm_konditionen)  
- Tabelle `fahrzeugfinanzierungen`: `docs/DB_SCHEMA_POSTGRESQL.md`
