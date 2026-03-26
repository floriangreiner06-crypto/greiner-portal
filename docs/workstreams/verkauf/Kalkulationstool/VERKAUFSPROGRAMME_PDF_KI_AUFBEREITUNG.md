# Verkaufsprogramme aus PDF per KI in die Datenbank aufbereiten

**Stand:** 2026-03-01  
**Kontext:** VFW-Vermarktung — gültige Verkaufsprogramme im Tool anzeigen und pro Fahrzeug die passenden Konditionen ermitteln.

---

## 1. Kurzantwort

**Ja.** Wenn ihr die Verkaufsprogramme (Rundschreiben) als **PDF zur Verfügung stellt**, können wir sie mit **KI** so aufbereiten, dass die **Logik erkennbar** wird und in der **Datenbank** landet. Dafür könnt ihr **LM Studio** (eure lokale KI im RZ) oder **AWS Textract + Bedrock** nutzen – beides ist möglich. Darauf aufbauend kann das Kalkulationstool:

- **gültige Programme** (Hersteller, Zeitraum) anzeigen und
- **pro Fahrzeug** (Marke, Modell, Aktionstyp, Stichtag) die **richtigen Konditionen** heraussuchen.

Wichtig: Die KI liefert einen **Vorschlag**; ein **menschlicher Prüfschritt** (Freigabe/Korrektur) ist sinnvoll, bevor die Daten für die Kalkulation genutzt werden.

---

## 2. Was wir aus den PDFs brauchen („Logik erkennen“)

Damit die Kalkulation die richtigen Boni findet, müssen aus dem Rundschreiben mindestens diese **strukturierten Informationen** werden:

| Information | Beispiel | Verwendung |
|-------------|----------|------------|
| **Hersteller** | Stellantis, Hyundai, Leapmotor | Programm zuordnen, Filter im Tool |
| **Gültig von / bis** | 01.01.2026 – 31.03.2026 | Nur Programme anzeigen, die zum Stichtag gelten |
| **Programm-Bezeichnung** | „VFW Q1/2026“, „TW-Aktion März“ | Anzeige, Auswahl |
| **Aktionstyp / Aktionscode** | VFW gef., VFW n. gef., TW, Netprice, OR, … | Matching „Fahrzeug ↔ Programm“ |
| **Modell-/Reihenzuordnung** | Modellname, Modellcode, Baureihe | Optional: Kondition nur für bestimmte Modelle |
| **Bonus-Positionen** | Bezeichnung + **Prozent (auf UPE)** und/oder **fester Betrag (€)** | Exakte Kalkulation (wie heute in Excel) |

Typische Elemente in den PDFs:

- **Texte:** Programmname, Gültigkeit, Aktionstyp, Bedingungen.
- **Tabellen:** z. B. Zeilen = Aktionstyp/Modell, Spalten = VFW‑%, KAP‑%, Reg.-Budget, Endkundenprämie (€), etc.

Die „Logik“, die wir erkennen wollen, ist im Kern: **Für welche Aktion/Modell/Zeitraum gelten welche Boni (%, €)?** Genau das soll in den Tabellen `vfw_verkaufsprogramme` und `vfw_programm_konditionen` (Phase 2 des Implementierungsplans) abgebildet werden.

---

## 3. Vorgehen: PDF → KI → Datenbank

### 3.1 Grober Ablauf

1. **PDF bereitstellen**  
   Verkaufsleitung/Admin lädt das Rundschreiben-PDF hoch (z. B. im VFW-Modul unter „Rundschreiben / Verkaufsprogramme“).

2. **Texte und Tabellen extrahieren**  
   - **Variante A:** **pdfplumber** (oder PyMuPDF) liest aus dem PDF **Text** und ggf. Tabellen – wie bereits bei der **Unfall-Gutachten-Extraktion** im Einsatz. Kein AWS nötig.  
   - **Variante B:** **AWS Textract** liest Text und Tabellen (bei gescannten PDFs ohne Textlayer oft genauer, erfordert AWS).

3. **Struktur und Logik ableiten**  
   - Der **Rohtext** (und ggf. tabellarisch aufbereitete Daten) wird an ein **Sprachmodell** übergeben.  
   - **Ihr könnt dafür LM Studio (eure KI im RZ) einsetzen** – derselbe `lm_studio_client` wie bei Hilfe „Mit KI erweitern“, Transaktions-Kategorisierung und Unfall-Gutachten (Text → JSON). Kein Bedrock nötig.  
   - **Alternativ:** AWS Bedrock (Claude) für die strukturierte Extraktion.  
   - Prompt-Beispiel: „Aus dem folgenden Text eines Hersteller-Rundschreibens: Ermittle Programmbezeichnung, Gültigkeitszeitraum, Hersteller. Pro Aktionstyp/Modell: Liste alle Bonus-Positionen mit Bezeichnung, ob Prozent (auf UPE) oder fester Betrag in Euro, und den Wert. Antworte nur mit gültigem JSON.“  
   - Die KI gibt einen **strukturierten Vorschlag** zurück (z. B. JSON), der ins DB-Schema gemappt wird.

4. **Vorschlag in DB-Form bringen**  
   - Backend mappt den KI-Output auf die Felder von **`vfw_verkaufsprogramme`** (Hersteller, Bezeichnung, von_datum, bis_datum) und **`vfw_programm_konditionen`** (aktionstyp, modell_pattern, vfw_bonus_pct, kap_pct, reg_budget_pct, slot4_pct, ggf. feste Beträge falls im Schema vorgesehen).

5. **Menschliche Prüfung**  
   - In der Admin-UI wird der **Vorschlag angezeigt** (z. B. „Neues Programm + X Konditionen aus PDF übernehmen?“).  
   - Verkaufsleitung/Admin prüft und bestätigt oder korrigiert, danach **Speichern** in der Datenbank.

6. **Nutzung im Kalkulationstool**  
   - Das Tool zeigt nur **gültige** Verkaufsprogramme (Filter nach Hersteller + Stichtag).  
   - Pro Fahrzeug (VIN/Modell + gewählter Aktionstyp) wird das **passende Programm** und die zugehörigen **Konditionen** aus der DB geladen und in der Kalkulation verwendet.

### 3.2 Technik – LM Studio oder AWS

**LM Studio (empfohlen, bereits im Einsatz):**

- **LM Studio** (Server z. B. 46.229.10.1:4433) ist bereits produktiv im Portal: Hilfe „Mit KI erweitern“, Transaktions-Kategorisierung (Bankenspiegel), Unfall-Gutachten (PDF-Text → LM Studio → JSON). Gleicher Use-Case: **Text aus PDF → LM Studio → strukturierter Vorschlag (JSON)**.
- **PDF-Text:** Mit **pdfplumber** extrahieren (wie bei Unfall-Gutachten in `unfall_rechnungspruefung_api.py`), dann den Text an `lm_studio_client.chat_completion()` schicken mit Prompt „Rundschreiben auswerten, nur JSON zurückgeben“.
- **Vorteile:** Keine AWS-Abhängigkeit, Daten bleiben im RZ, einheitlich mit bestehenden KI-Funktionen, gleiche Config (`config/credentials.json` → `lm_studio`, Modell z. B. `mistralai/magistral-small-2509` für JSON).

**AWS (optional):**

- **AWS Bedrock** (eu-central-1): für „Rundschreiben verstehen“ nutzbar, falls ihr bewusst Cloud-KI wollt.
- **AWS Textract:** für PDFs ohne Textlayer (gescannte Rundschreiben) sinnvoll; bei normalen PDFs mit Textlayer reicht pdfplumber + LM Studio.

**Datenbank:** Schema aus dem VFW-Implementierungsplan (Phase 2): `vfw_verkaufsprogramme`, `vfw_programm_konditionen` (und optional `vfw_leistungsboni`).

---

## 4. Was die KI gut kann – und wo Grenzen sind

- **Gut:**  
  - Texte aus PDF lesen (über Textract).  
  - Aus Fließtext und Tabellen **Programmname, Zeiträume, Hersteller** und **Bonus-Positionen (Bezeichnung, %, €)** ableiten.  
  - Ein einheitliches **Format** (z. B. JSON) für unsere DB-Felder vorschlagen.

- **Grenzen / Risiken:**  
  - **Layout:** Jeder Hersteller gestaltet Rundschreiben anders; Tabellen können mehrdeutig oder unvollständig sein.  
  - **Zahlen:** Prozent- und Euro-Werte können vertauscht oder falsch zugeordnet werden.  
  - **Aktionstypen:** Bezeichnungen („VFW gef.“, „TW“, „Netprice“) können im PDF anders heißen als in unserem System.

**Deshalb:** Die KI liefert einen **Entwurf**. Die **Freigabe/Korrektur durch einen Menschen** (Verkaufsleitung/Admin) vor dem Speichern in die DB ist fachlich sinnvoll und reduziert Fehler in der Kalkulation.

---

## 5. Konkrete Schritte für die Umsetzung

1. **Phase 2 umsetzen**  
   - DB-Tabellen `vfw_verkaufsprogramme`, `vfw_programm_konditionen` anlegen.  
   - Admin-UI: Verkaufsprogramme und Konditionen **manuell** pflegen können (ohne PDF).  
   - So habt ihr sofort nutzbare Programme und könnt das Kalkulationstool (Phase 3) mit „richtigen Konditionen pro Fahrzeug“ bauen.

2. **PDF-Import vorbereiten**  
   - Ein **Upload** (z. B. „Rundschreiben-PDF hochladen“) in der gleichen Admin-UI.  
   - Backend: PDF mit **pdfplumber** lesen (Text) → Text an **LM Studio** mit festem Prompt → **Vorschlag** (Programm + Konditionen als JSON) erzeugen. Optional: bei Bedarf Textract + Bedrock statt pdfplumber + LM Studio.  
   - Vorschlag in der UI anzeigen, **„Übernehmen“** (ggf. nach Bearbeitung) → Einträge in `vfw_verkaufsprogramme` und `vfw_programm_konditionen` anlegen/aktualisieren.

3. **Kalkulationstool anbinden**  
   - Beim Öffnen der Kalkulation: **gültige Verkaufsprogramme** (z. B. nach Hersteller, aktuellem Datum) aus der DB laden und anzeigen.  
   - Pro Fahrzeug (Modell, Aktionstyp, Stichtag): **passendes Programm** und **Konditionen** aus der DB holen und die Boni in der Kalkulation übernehmen („Logik erkennen“ = diese Zuordnung).

4. **Iterativ verbessern**  
   - Mit echten Rundschreiben-PDFs (Stellantis, Hyundai, ggf. Leapmotor) testen.  
   - Prompt und ggf. Nachbearbeitung (Parsing-Regeln) anpassen, damit Aktionstypen und Boni möglichst zuverlässig erkannt werden.

---

## 6. Zusammenfassung

| Frage | Antwort |
|-------|--------|
| Können wir Verkaufsprogramme als PDF bereitstellen und mit KI in eine DB aufbereiten? | **Ja.** PDF → Text (pdfplumber) → **LM Studio** oder Bedrock (Struktur/Logik als JSON) → Vorschlag → Mensch prüft → Speichern in `vfw_verkaufsprogramme` / `vfw_programm_konditionen`. **LM Studio** ist bereits im Einsatz (Hilfe, Kategorisierung, Unfall-Gutachten) und kann hier genauso genutzt werden. |
| Wird die Logik „erkannt“? | Die **Zuordnung** (Programm, Zeitraum, Aktionstyp, Modell → Boni in % und €) wird aus Text und Tabellen abgeleitet und in der DB abgelegt; das Kalkulationstool nutzt genau diese Daten, um pro Fahrzeug die richtigen Konditionen zu finden. |
| Ohne manuelle Pflege? | Erster Schritt: Programme/Konditionen **manuell** pflegen (Phase 2). Optional danach: PDF-Import mit KI-Vorschlag und **menschlicher Freigabe**, um Aufwand zu reduzieren und trotzdem Fehler zu begrenzen. |

Wenn ihr die Rundschreiben als PDF zur Verfügung stellt, können wir sie mit KI so aufbereiten, dass die Logik in der Datenbank abgebildet wird und im Tool die **gültigen Verkaufsprogramme** sichtbar sind und **pro Fahrzeug die richtigen Konditionen** verwendet werden.
