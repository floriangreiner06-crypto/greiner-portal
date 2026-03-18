# Garantie-Bedingungen mit LM Studio: Prüfung & Empfehlung

**Stand:** 2026-03  
**Workstream:** werkstatt  
**Status:** Plan (keine Implementierung)

---

## 1. Kurzantwort

**Ja.** Ihr könnt die Garantie-Bedingungen (Handbücher/Richtlinien) als Wissensbasis nutzen und mit **LM Studio** (eure lokale KI im RZ) eine **Prüfung** und **Empfehlung** pro Garantieauftrag ableiten. LM Studio ist im Portal bereits im Einsatz (Hilfe „Mit KI erweitern“, Transaktions-Kategorisierung, Unfall-Gutachten, Verkaufsprogramm-Regelwerk, Fahrzeugschein-OCR). Dieselbe Infrastruktur kann für Garantie genutzt werden.

**Hinweis:** Im Projekt heißt die Integration durchgängig **LM Studio** (nicht „ML Studio“). Siehe z. B. `docs/workstreams/integrations/KONZEPT_NATURSPRACHLICHE_ANALYSEN_DRIVE_DATEN.md`.

---

## 2. Was ihr bereits habt

| Baustein | Stand |
|----------|--------|
| **LM Studio** | Server (z. B. 46.229.10.1:4433), Config in `config/credentials.json` → `lm_studio`. Client: `api/ai_api.py` → `lm_studio_client.chat_completion()` (Text/JSON). |
| **Garantie-Handbücher** | PDFs in `docs/workstreams/werkstatt/garantie/` (Richtlinie 01-2026, Hyundai 02-2024, Opel Mai 2025, Leapmotor). Seite „Handbücher & Richtlinien“ verlinkt sie. |
| **Strukturierte Analysen** | `docs/stellantis/STELLANTIS_GARANTIE_HANDBUECH_ANALYSE_TAG189.md` – Abschnitte 10.1–10.5, 11.1–11.4 (Dokumentation, Belege, Fristen). Ähnlich für Hyundai möglich. |
| **Auftragsdaten** | Locosoft (Auftrag, Positionen, Diagnose-Text, Gudat-Anhänge/Fotos), Garantieakte-Ordner (welche Dateien vorhanden). |
| **Vergleichbare Use-Cases** | Unfall: PDF-Text → LM Studio → strukturierter Vorschlag; Verkaufsprogramm: PDF → Chunks → LM Studio → Regelwerk (JSON). |

---

## 3. Was „Prüfung / Empfehlung“ bedeuten kann

- **Prüfung:** Zu einem konkreten Garantieauftrag: Wird die Dokumentation den Anforderungen der Garantie-Bedingungen gerecht? (z. B. „Diagnose dokumentiert?“, „Fotos vorhanden?“, „Kundenunterschrift?“ – abhängig von Marke/Handbuch.)
- **Empfehlung:** Kurze, konkrete Hinweise: „Noch fehlend: …“, „Vorabfreigabe einholen“, „Frist 21 Tage beachten“, „Nächster Schritt: …“.

Eingabe: **Auftragsnummer** (oder bereits geladene Auftragsdaten + Marke).  
Ausgabe: **Strukturierte Prüfung** (z. B. Checkliste erfüllt/fehlt) + **Freitext-Empfehlung**.

---

## 4. Optionen der Umsetzung

### Option A: Fester Prompt mit Bedingungen als Kontext (pragmatisch)

- **Bedingungen:** Text aus den Garantie-Handbüchern **einmalig** aufbereiten (z. B. aus den bestehenden Analysen wie Stellantis-Garantie-Handbuch oder per PDF-Extraktion mit pdfplumber) und als **Kontext-Text** im Backend halten (Datei oder DB-Snippet pro Marke).
- **Pro Prüfung:** Auftragsdaten (Auftragsnr, Marke, Kennzeichen, VIN, „Diagnose vorhanden: ja/nein“, „Fotos in Gudat: ja/nein“, „Garantieakte-Ordner: Anzahl Dateien“, ggf. Ausschnitt Diagnose-Text) als strukturierter Text + der passende Bedingungen-Kontext (je nach Marke) an LM Studio senden.
- **Prompt:** „Prüfe den folgenden Garantieauftrag anhand der angegebenen Garantie-Bedingungen. Antworte in JSON: { checkliste: [{ punkt, erfuellt, hinweis }], empfehlung: \"…\" }. Erfinde keine Fakten.“
- **Vorteil:** Einfach, keine Embeddings, gleiches Muster wie Unfall/Regelwerk. Token-Limit beachten (Kontext kürzen oder nur relevante Abschnitte mitschicken).

### Option B: RAG (Retrieval-Augmented Generation)

- **Bedingungen:** PDF-Text extrahieren, in **Abschnitte/Chunks** zerlegen, optional mit LM Studio **Embeddings** speichern (Tabelle `garantie_handbuch_chunks` mit text, marke, kapitel, embedding).
- **Pro Prüfung:** Auftragsdaten + **Suche** (z. B. „Diagnose Dokumentation Fotos Fristen“ oder aus Auftragstext) → relevante Chunks aus DB holen → Kontext aus Chunks + Auftrag an LM Studio → Prüfung/Empfehlung.
- **Vorteil:** Immer aktuelle Handbuch-Inhalte, nur Relevantes im Prompt. **Nachteil:** Mehr Aufwand (Embedding-Pipeline, Speicher, Chunk-Größe).

### Option C: Hybrid (Checkliste fest, Empfehlung per KI)

- **Checkliste:** Aus Handbüchern **einmalig** eine feste Checkliste ableiten (manuell oder per LM Studio aus PDF-Text: „Extrahiere alle Prüfpunkte für Garantie-Dokumentation als JSON-Liste“) und in DB oder Config pflegen (analog Unfall M1).
- **Prüfung:** Deterministisch (Auftragsdaten gegen Checkliste abgleichen: Diagnose vorhanden? Fotos? etc.).
- **Empfehlung:** Nur der **Freitext-Teil** („Was fehlt?“ / „Nächste Schritte“) wird von LM Studio formuliert – mit Kontext „Checkliste-Ergebnis“ + optional Ausschnitt Bedingungen.
- **Vorteil:** Prüfung nachvollziehbar und stabil; KI nur für Formulierung.

---

## 5. Empfohlene Reihenfolge (ohne Code)

1. **Quellen festlegen:** Welche Garantie-Bedingungen fließen ein? (PDFs in `garantie/` + ggf. bestehende Markdown-Analysen.) Pro Marke (Hyundai, Stellantis, Leapmotor) einen **Kontext-Text** definieren (entweder manuell aus Analysen oder PDF → pdfplumber → Text pro Kapitel).
2. **Eingabe pro Prüfung:** Welche Auftragsdaten braucht die KI? (Auftragsnr, Marke, Diagnose ja/nein, Fotos ja/nein, Garantieakte vorhanden, ggf. Ausschnitt Diagnose-Text aus Locosoft/Gudat.) Diese Daten liefern bestehende APIs (Garantieaufträge, Arbeitskarte, Gudat-Anhänge).
3. **Prompt-Design:** Fester System- und User-Prompt mit (1) Bedingungen-Kontext (Marke), (2) Auftragsdaten, (3) gewünschtem Ausgabeformat (JSON: Prüfpunkte + Empfehlung). Länge unter LM-Studio-Limit halten (z. B. 6–8k Zeichen wie beim Verkaufsprogramm).
4. **API:** Neuer Endpoint z. B. `POST /api/garantie/pruefung` oder `POST /api/ai/garantie-pruefung` mit `order_number` (und ggf. Marke). Backend: Auftragsdaten laden, Bedingungen-Kontext laden, LM Studio aufrufen, Antwort parsen (JSON), zurückgeben.
5. **UI:** In der Garantieaufträge-Übersicht oder im Auftrags-Modal Button „Prüfung / Empfehlung“ → Aufruf API → Anzeige (Checkliste + Empfehlung). Optional: nur Empfehlung als Kurztext.

---

## 6. Grenzen & Hinweise

- **Rechtssicherheit:** Die KI-Ausgabe dient als **Unterstützung**, nicht als verbindliche Rechtsauskunft. Klar kommunizieren: „KI-Vorschlag – bitte anhand der offiziellen Handbücher prüfen.“
- **Token/Zeit:** Große Handbücher komplett im Prompt = schnell am Limit. Besser: gekürzte Zusammenfassung oder nur relevante Abschnitte (z. B. „Dokumentation“, „Belege“, „Fristen“).
- **Marken-Unterschiede:** Pro Marke eigenen Kontext verwenden (Hyundai vs. Stellantis vs. Leapmotor), damit die Prüfung markengerecht bleibt.
- **LM Studio Verfügbarkeit:** Wie bei anderen KI-Funktionen: Bei Ausfall oder Timeout Fallback (z. B. „Prüfung derzeit nicht verfügbar“) und ggf. Retry mit kürzerem Kontext.

---

## 7. Nächster Schritt

- **Priorisierung** mit Service/IT: Option A (fester Prompt) vs. B (RAG) vs. C (Hybrid).
- **Kontext-Text** pro Marke erstellen (aus PDFs oder aus `STELLANTIS_GARANTIE_HANDBUECH_ANALYSE_TAG189.md` / vergleichbar Hyundai).
- Danach: konkrete Spezifikation (Eingabe-Felder, JSON-Schema für Prüfung/Empfehlung) und Umsetzung (API + UI).

---

*Nur Plan; keine Code-Änderungen. Referenzen: `api/ai_api.py` (lm_studio_client), `docs/workstreams/werkstatt/GARANTIE_HANDBUECHER_WISSENSBASIS_MACHBARKEIT.md`, Unfall-Modul (M1/M4), Verkaufsprogramm-Regelwerk (PDF → LM Studio).*
