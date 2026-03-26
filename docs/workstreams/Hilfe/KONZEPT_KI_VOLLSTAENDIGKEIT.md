# Konzept: Hilfe-Vollständigkeit gegen Code matchen (KI)

**Stand:** 2026-02-24  
**Workstream:** Hilfe

---

## Ziel

Die **Vollständigkeit der Hilfe** soll gegen den **tatsächlichen Code/Features** des Portals abgeglichen werden: Wo fehlen Artikel? Welche Module oder Funktionen haben keine oder zu wenig Abdeckung? Die **KI (Bedrock)** erhält eine strukturierte Gegenüberstellung (Code-Seite vs. Hilfe-Seite) und schlägt **Lücken und konkrete Artikelvorschläge** vor.

---

## Ablauf (High-Level)

1. **Code-Seite erfassen:** Liste der Module, Haupt-Routen, Features (aus Phase-0-Analyse oder aus Code-Scan).
2. **Hilfe-Seite erfassen:** Aus der DB: Kategorien + Artikel (Titel, Kategorie, ggf. Tags).
3. **KI-Aufgabe:** Beides an Bedrock senden mit Prompt: „Vergleiche. Nenne Lücken: Module/Features ohne oder mit schwacher Hilfe. Schlage konkrete Artikel-Titel und zugehörige Kategorie vor. Priorisiere nach Wichtigkeit.“
4. **Ergebnis:** Strukturierter Report (Lücken, Vorschläge) – als Script-Ausgabe, als Datei oder in der Admin-UI.

---

## Datenquellen

### Code-Seite (was das Portal „kann“)

- **Basis:** Das **Modul-Inventar** aus der Phase-0-Analyse (`PHASE_0_CODEBASE_ANALYSE.md`): Modulname, Haupt-Route(s), Kurzbeschreibung, Zielgruppe.
- Optional erweiterbar: automatischer Scan von `app.py` + `routes/*.py` (Registrierung von Blueprints/Routen), um neue Einträge zu entdecken. Für die erste Version reicht eine **gepflegte Liste** (z. B. in einer JSON- oder Markdown-Datei im Workstream), die aus der Phase-0 abgeleitet und bei Bedarf manuell ergänzt wird.

### Hilfe-Seite (was dokumentiert ist)

- Aus **PostgreSQL:** `hilfe_kategorien` (name, slug), `hilfe_artikel` (titel, slug, kategorie_id → Kategoriename, tags). Nur freigegebene Artikel oder alle – je nach Fragestellung („Was sehen User?“ vs. „Was ist in Arbeit?“).

---

## KI-Prompt (Struktur)

**Eingabe (Text/JSON):**

- Block 1: „**Portal-Module (aus Code):** [Liste Modul | Route | Kurzbeschreibung]“
- Block 2: „**Aktuelle Hilfe:** Kategorien: [ … ]. Artikel: [ Kategorie: Titel, Titel, … ].“

**Auftrag:**

- Vergleiche die beiden Listen.
- Nenne **Lücken:** Module oder konkrete Funktionen, die in der Hilfe fehlen oder nur sehr knapp (ein Titel ohne erkennbaren Bezug) abgedeckt sind.
- Schlage für jede Lücke **konkrete Hilfe-Artikel** vor: Titel (als Frage oder „Wie …?“), empfohlene Kategorie (aus der bestehenden Hilfe-Kategorienliste).
- Priorisiere (z. B. „wichtig für viele User“ vs. „nice-to-have“).
- Ausgabe: strukturiert (z. B. Markdown mit Überschriften „Lücken“, „Vorschläge“, „Priorität“) oder JSON.

Die Antwort wird **nur als Vorschlag** genutzt; ein Mensch entscheidet, welche Artikel angelegt werden.

---

## Umsetzungsoptionen

### A) Script (empfohlen für den Start)

- **Skript:** z. B. `scripts/hilfe_vollstaendigkeit_check.py`
  - Liest Code-Inventar (eingebettet oder aus Datei wie `docs/workstreams/Hilfe/code_inventar.json`).
  - Liest aus DB: Kategorien + Artikel.
  - Baut Prompt, ruft Bedrock auf (gleiche Credentials wie Fahrzeuganlage/Hilfe-KI).
  - Gibt Report auf stdout aus oder schreibt in eine Datei (z. B. `docs/workstreams/Hilfe/VOLLSTAENDIGKEIT_REPORT.md`).
- **Laufzeit:** Manuell (z. B. nach größeren Releases oder monatlich). Optional später: Cron-Job, der den Report ablegt.

### B) Admin-UI „Vollständigkeit prüfen“

- Im Hilfe-Admin eine Schaltfläche **„Vollständigkeit gegen Code prüfen“**.
- Backend: API `POST /api/hilfe/ki/vollstaendigkeit` (oder GET mit längerem Timeout) erzeugt denselben Abgleich (Code-Inventar + DB-Abfrage + Bedrock-Aufruf) und gibt das KI-Ergebnis als JSON zurück.
- Frontend: Zeigt den Report (Lücken, Vorschläge) an; optional „Artikel anlegen“ pro Vorschlag (öffnet „Neuer Artikel“ mit vorausgefülltem Titel/Kategorie).

### C) Kombination

- Script für detaillierte/archivierte Reports und Offline-Nutzung.
- Admin-Button für schnelle Prüfung ohne Server-Shell.

---

## Code-Inventar (Pflege)

- Damit die KI sinnvoll vergleichen kann, muss die **Code-Seite** in einer maschinenlesbaren Form vorliegen.
- **Option 1:** Im Script eine **eingebettete Liste** (Python-Dict/Liste), abgeleitet aus der Phase-0-Tabelle; bei großen Änderungen im Portal wird die Liste im Script angepasst.
- **Option 2:** Datei **`docs/workstreams/Hilfe/code_inventar.json`** (oder .md mit festem Format): Liste der Module mit Name, Route, Kurzbeschreibung, optional Priorität. Wird bei neuen Features ergänzt; das Script liest diese Datei.
- Empfehlung: **Option 1** für die erste Version (weniger Abhängigkeiten), bei Bedarf später auf Option 2 umstellen oder beides (Script-Fallback + optionale JSON-Datei).

---

## Kurzfassung

- **Ja, wir können die Vollständigkeit der Hilfe gegen den Code matchen** – indem wir Code-Inventar und Hilfe-Inhalt sammeln, an die KI (Bedrock) übergeben und Lücken + Artikelvorschläge zurückbekommen.
- **Erste Umsetzung:** Script, das Code-Liste + DB-Abfrage nutzt, Bedrock aufruft und einen Report ausgibt. Optional später: Admin-Button mit gleicher Logik im Backend.

**Umsetzung:** Das Script **`scripts/hilfe_vollstaendigkeit_check.py`** ist angelegt. Siehe unten „So testen“.

---

## So testen (Script)

**Voraussetzung:** `config/credentials.json` mit Abschnitt **aws_bedrock** (region, access_key_id, secret_access_key, optional model_id). Gleiche Credentials wie für die Fahrzeuganlage.

**Aufruf (aus Projektroot `/opt/greiner-portal`):**

```bash
# Nur Abgleich ohne KI (Code-Inventar + Hilfe aus DB auf stdout)
python3 scripts/hilfe_vollstaendigkeit_check.py --no-ki

# Mit KI: Bedrock aufrufen, Report auf stdout
python3 scripts/hilfe_vollstaendigkeit_check.py

# Report in Datei schreiben
python3 scripts/hilfe_vollstaendigkeit_check.py --out docs/workstreams/Hilfe/VOLLSTAENDIGKEIT_REPORT.md
```

Das Script liest die Hilfe aus der **PostgreSQL-DB** (drive_portal). Bei fehlender `aws_bedrock`-Config bricht es mit Hinweis ab. Das Code-Inventar ist im Script eingebettet (aus Phase-0); neue Module können dort ergänzt werden.
