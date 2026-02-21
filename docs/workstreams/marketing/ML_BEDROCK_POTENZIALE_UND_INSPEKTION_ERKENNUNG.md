# ML, AWS Bedrock und Inspektionserkennung (Opel/Hyundai)

**Stand:** 2026-02-21  
**Kontext:** Werkstattauslastung, Marketing-Potenziale aus Locosoft-Kundenfahrzeugen. HU/AU läuft über **Veact**; Marketing-Modul **Catch (Prof4net)** im Einsatz. Offen: Nutzung von **ML-Modul** und **AWS Bedrock** für Potenzialerkennung sowie die **richtige Inspektion** für Opel- und Hyundai-Fahrzeuge.

---

## 1. Einordnung: Veact & Catch

- **HU/AU-Ansprache:** Wird über **Veact** abgedeckt – keine Doppelung in DRIVE nötig; Potenzialanalyse kann sich auf andere Hebel konzentrieren (Inspektion, Reaktivierung, Reparaturpotenzial, Saison).
- **Catch (Prof4net):** Als Marketing-Modul genutzt. DRIVE könnte **Listen/Exporte** (z. B. „Fahrzeuge mit Inspektion fällig“, „Reaktivierungspotenzial“) bereitstellen, die in Catch für Kampagnen genutzt werden – Anbindung/Format später klären.

---

## 2. ML-Modul – mögliche Erweiterungen für Potenziale

### 2.1 Aktueller Stand

- **Einsatz:** ML dient heute der **Auftragsdauer-Vorhersage** (Auftragsdauer in Minuten aus Vorgabe-AW, Marke, Betrieb, Mechaniker, Dringlichkeit, km, Fahrzeugalter etc.).
- **Technik:** Pickle-Modell (z. B. Random Forest), Features u. a. `marke_encoded`, `vorgabe_aw`, `km_stand`, `fahrzeug_alter_jahre`; API: `api/ml_prediction_api.py`, `api/ml_api.py`; Training: `scripts/ml/train_auftragsdauer_model_v2.py`.

### 2.2 Mögliche Erweiterungen (Potenzialerkennung)

| Idee | Beschreibung | Voraussetzung |
|------|--------------|---------------|
| **Propensity „Termin bucht“** | Modell: „Wahrscheinlichkeit, dass dieses Fahrzeug/Kunde in den nächsten 90 Tagen einen Werkstatt-Termin bucht.“ Nutzung: Priorisierung von Kampagnen (z. B. Catch/Veact) für hohe Propensity. | **Labels** nötig: z. B. aus Vergangenheit „hat in 90 Tagen gebucht“ (ja/nein) pro Fahrzeug/Zeitfenster. Features: Marke, km, Alter, letzter Besuch, Anzahl Besuche, evtl. letzte Art (Inspektion/HU/Reparatur). |
| **Klassifikation Inspektionstyp** | Modell: Eingabe `(Marke, text_line)` → Ausgabe „Inspektion 1“, „Inspektion 2“, „Inspektion 3“, „Hyundai 15k/30k/60k“, „Sonstige“. Nutzung: Historie pro Fahrzeug auswerten → „letzte war Inspektion 2“ → „nächste = Inspektion 3“. | **Labelte Daten:** Entweder manuell oder per **Bedrock** (einmalig) aus `labours.text_line` + Marke Labels erzeugen, dann Modell trainieren. |
| **Potenzial-Score (Regressionsmodell)** | Ein „Potenzial-Score“ pro Fahrzeug (z. B. 0–100), der erwarteten Umsatz oder Buchungswahrscheinlichkeit abbildet. Nutzung: Sortierung/Filter für Listenexport nach Catch. | Definition eines Zielwerts (z. B. Umsatz nächste 12 Monate oder „hat gebucht ja/nein“) und ausreichend historische Daten. |

**Empfehlung:** Zuerst **Inspektionserkennung** (siehe Abschnitt 4) klären – ob regelbasiert, mit Bedrock oder mit ML. Propensity-Modell sinnvoll, sobald ein klares Ziel (z. B. „Buchung in 90 Tagen“) und genug gelabelte Fälle vorhanden sind.

---

## 3. AWS Bedrock – mögliche Nutzung für Potenziale

### 3.1 Bereits im Einsatz

- **Fahrzeuganlage:** Fahrzeugschein-OCR und VIN-Entschlüsselung (Claude, eu-central-1); Referenz: `api/fahrzeugschein_scanner.py`, `api/fahrzeuganlage_api.py`.

### 3.2 Mögliche Erweiterungen (ohne Code, Konzept)

| Anwendung | Eingabe | Ausgabe | Nutzen |
|-----------|---------|---------|--------|
| **text_line → Standardarbeit** | Freitext aus `labours.text_line` (evtl. + Marke) | Vorschlag: Zuordnung zu Standardarbeit/Katalog (z. B. labour_operation_id oder Greiner-Katalog). | Bereits in [KI_CLAUDE_BEDROCK_ANWENDUNGSANALYSE.md](../integrations/KI_CLAUDE_BEDROCK_ANWENDUNGSANALYSE.md) (Werkstatt) genannt; hilft auch bei einheitlicher Benennung von Inspektionen. |
| **Inspektionstyp aus Text klassifizieren** | Ein oder mehrere `text_line`-Texte + Marke (Opel/Hyundai) | Klassifikation: z. B. „Opel Inspektion 1“, „Opel Inspektion 2“, „Hyundai 30.000 km Service“, „HU“, „Sonstige“. | Löst das Problem „richtige Inspektion erkennen“, wenn Locosoft keine eindeutigen Kennzahlen pro Hersteller hat (siehe Abschnitt 4). |
| **Nächste Inspektion vorschlagen** | Fahrzeugstamm (Marke, Modell, EZ, km) + letzte 1–3 Service-Positionen (text_line) | Kurzer Vorschlag: „Nächste Inspektion: Opel Inspektion 2 (30.000 km / 2 Jahre)“ oder „Hyundai 30.000-km-Service“. | Direkt nutzbar für Kampagnen und für Anzeige im Portal („Ihr nächster Service“). |
| **Potenzial-Kurzbeschreibung** | Gleiche Eingabe wie oben + evtl. Reparatur-Regeln (z. B. Bremsen, Batterie) | 2–3 Sätze: „Inspektion fällig; Bremsen-Check empfohlen (km-Stand); Klimaservice sinnvoll (Saison).“ | Unterstützt Serviceberater oder Export-Text für Catch/E-Mail. |

**Hinweis:** Alle Bedrock-Calls mit Kundendaten DSGVO-konform in eu-central-1; nur strukturierte Kontexte (keine Roh-PDFs mit personenbezogenen Massendaten) nötig.

---

## 4. Die „richtige Inspektion“ für Opel und Hyundai – Ansatz

### 4.1 Problem

- Opel und Hyundai haben **unterschiedliche Inspektionssysteme** (z. B. Opel: Inspektion 1/2/3 oder km/jahr; Hyundai: 15.000 / 30.000 / 60.000 km und 12/24/48 … Monate).
- In Locosoft wird aktuell **nur pauschal** über `labours.text_line` gefiltert (z. B. `LIKE '%inspektion%'` oder `LIKE '%wartung%'`), **ohne** Unterscheidung nach Inspektion 1/2/3 oder 15k/30k.
- Für **Potenzial** („welche Inspektion ist als nächstes fällig?“) und für **Kampagnen** („Opel Inspektion 2 in 2 Monaten“) braucht man eine **herstellerabhängige Erkennung**.

### 4.2 Mögliche Ansätze (priorisiert)

#### A) Regelbasiert: Hersteller-Intervalle + Historie

- **Quelle Intervall:**  
  - **Opel:** Modellabhängig (Betriebsanleitung); oft 30.000 km / 2 Jahre oder flexibel; ggf. Locosoft `makes.special_service_2_interval` / `special_service_3_interval` auswerten.  
  - **Hyundai:** Typisch 15.000 km / 12 Monate, dann 30 / 60 / 90 … km und 24 / 48 / 72 … Monate (Hersteller-Wartungsplan).
- **Logik:**  
  - Pro Fahrzeug: `first_registration_date`, `mileage_km`, Marke (aus `vehicles` + `makes`).  
  - Aus **Historie** (letzte Aufträge mit Inspektion): „Letzte erkannte Inspektion“ = Inspektion 1, 2 oder 3 (bzw. 15k/30k/60k). Dafür muss die **letzte** Inspektion klassifiziert werden (siehe B oder C).  
  - Dann: „Nächste Inspektion“ = nächster Schritt (2 nach 1, 3 nach 2; bei Hyundai 30k nach 15k usw.) und Fälligkeit aus Intervall + letztem Datum/km.
- **Vorteil:** Keine KI, nachvollziehbar, gut testbar.  
- **Nachteil:** Abhängig von sauberer Klassifikation der **vergangenen** Inspektion (text_line oder labour_number).

#### B) Bedrock: text_line + Marke → Inspektionstyp

- **Ablauf:**  
  - Für jeden relevanten Auftrag (oder nur die letzten pro Fahrzeug): `labours.text_line` (gefiltert auf Inspektion/Wartung) + Marke (Opel/Hyundai) an einen **einzigen Bedrock-Text-Call** senden.  
  - Prompt: „Klassifiziere die folgende Werkstatt-Position in exakt eine Kategorie: [Opel Inspektion 1, Opel Inspektion 2, Opel Inspektion 3, Hyundai 15.000 km Service, Hyundai 30.000 km Service, Hyundai 60.000 km Service, HU/AU, Sonstige]. Marke: …, text_line: …“.  
  - Antwort strukturiert (z. B. JSON) zurückgeben.
- **Nutzen:**  
  - Einmalig **Historie** pro Fahrzeug anreichern („letzte Inspektion = Opel Inspektion 2“).  
  - Danach mit **regelbasiert** (A) die „nächste Inspektion“ berechnen.  
  - Optional: Dieselbe Logik **live** bei neuem Auftrag nutzen (Vorschlag „Inspektion 2“ für Anzeige/Schnittstelle).
- **Aufwand:** Gering bis mittel (API-Endpoint, Prompt, evtl. Batch-Job für Historie). Kein Training nötig.

#### C) Locosoft labour_number / labour_operation_id prüfen

- In Locosoft haben Hersteller oft **eigene Arbeitsnummern** für Inspektion 1/2/3 (Opel) oder 15k/30k (Hyundai).  
- **Vorgehen:** In `labours` und `labours_master` (evtl. `source` = Hersteller) prüfen, ob es **eindeutige Kennzahlen** pro Inspektionstyp gibt (z. B. Opel 12345 = Inspektion 1, 12346 = Inspektion 2).  
- Wenn **ja:** Regelbasiert nur über `labour_operation_id` / `labour_number` + Marke die Inspektion erkennen – dann keine KI nötig.  
- Wenn **nein oder uneinheitlich:** B (Bedrock) oder D (ML) nutzen.

#### D) ML: Klassifikation Inspektionstyp

- **Modell:** Eingabe (Marke, text_line) → Label (Inspektion 1/2/3, 15k/30k/60k, Sonstige).  
- **Labels:** Z. B. per Bedrock (B) aus Historie erzeugen oder manuell stichprobenweise; danach Modell trainieren (z. B. Random Forest oder kleines Transformer-Modell auf Text).  
- **Vorteil:** Schnell und ohne API-Call pro Anfrage; skaliert gut bei vielen Fahrzeugen.  
- **Nachteil:** Training und Wartung; neue Bezeichnungen (Hersteller-Update) erfordern neue Labels/Retraining.

### 4.3 Empfohlene Reihenfolge

1. **Locosoft prüfen (C):** Ob `labour_operation_id` / `labour_number` (und `source`) herstellerabhängig und eindeutig Inspektion 1/2/3 bzw. 15k/30k abbilden. Wenn ja → regelbasierte Erkennung darauf aufsetzen.  
2. **Parallel oder falls C nicht reicht: Bedrock (B)** für Klassifikation von `text_line` + Marke einführen (einmalig Historie, optional live).  
3. **Regelwerk (A)** für „nächste Inspektion“ definieren (Opel/Hyundai-Intervalle aus Herstellerangaben + ggf. `makes.special_service_*`).  
4. **Optional später:** ML (D) für Inspektionstyp, wenn viele Daten gelabelt sind und man API-Latenz/Kosten reduzieren will.

---

## 5. Kurzfassung und nächste Schritte

- **Veact:** HU/AU abgedeckt; **Catch:** Marketing-Modul – DRIVE kann Listen/Exporte für Kampagnen liefern.  
- **ML:** Heute Auftragsdauer; Erweiterung auf **Propensity** (Termin bucht) oder **Inspektionstyp-Klassifikation** möglich, sobald Labels/Zielgröße definiert sind.  
- **Bedrock:** Geeignet für **text_line → Inspektionstyp**, **„nächste Inspektion“-Vorschlag** und **Potenzial-Kurzbeschreibung**; keine neuen Infrastruktur nötig (eu-central-1 bereits im Einsatz).  
- **Inspektion Opel/Hyundai:** Zuerst **Locosoft labour_number/labour_operation_id** prüfen (herstellerspezifische Codes). Wenn nicht ausreichend: **Bedrock** zur Klassifikation von `text_line` + Marke nutzen, danach **regelbasiert** „nächste Inspektion“ aus Intervallen + Historie ableiten.

**Konkrete nächste Schritte (ohne Code):**  
1. Mit Werkstatt/Service klären: Sollen Potenzial-Listen für **Catch** exportiert werden (Format, Umfang)?  
2. In Locosoft prüfen: Gibt es **eindeutige Arbeitsnummern** für Opel Inspektion 1/2/3 und Hyundai 15k/30k/60k?  
3. Wenn nein: **Bedrock-Pilot** für „text_line + Marke → Inspektionstyp“ (z. B. 100 Stichproben) vorschlagen und Prompt/JSON-Schema skizzieren.
