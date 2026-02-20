# KI (Claude via AWS Bedrock) in DRIVE – Anwendungsanalyse

**Stand:** 2026-02-20  
**Workstream:** integrations  
**Kontext:** Claude/Bedrock ist im Modul **Fahrzeuganlage** (Fahrzeugschein-OCR, eu-central-1) bereits aktiv. Diese Analyse bewertet alle DRIVE-Features auf Mehrwert durch KI-Einsatz – **ohne Code-Änderung**, reine Analyse.

---

## 1. Bereits im Einsatz (Referenz)

| Modul | Use-Case | Technik | Mehrwert |
|-------|----------|---------|----------|
| **Fahrzeuganlage** | Zulassungsbescheinigung Teil 1 (ZB1) → strukturierte Felder (FIN, Kennzeichen, Halter, …) | AWS Bedrock (Claude), Vision + strukturiertes JSON | Ersparnis manueller Dateneingabe, weniger Tippfehler, Dublettencheck gegen Locosoft |

---

## 2. Hoher Mehrwert – klare KI-Anwendungen

### 2.1 Unfall-Rechnungsprüfung (Werkstatt) – Gutachten-Extraktion

| Aspekt | Beschreibung |
|--------|--------------|
| **Aktuell** | Sachverständigengutachten-PDF wird mit **pdfplumber** (Text) extrahiert, dann **LM Studio** (lokaler Server 46.229.10.1) für strukturierte Extraktion: Gutachten-Nr., Sachverständiger, Summe, Positionen (arbeitsposition/ersatzteil/lackierung/nebenkosten). DB: `unfall_gutachten`, `unfall_gutachten_positionen`. |
| **KI-Mehrwert** | **Umstellung auf Bedrock** statt LM Studio: gleicher Use-Case (Text → JSON), einheitliche KI-Infrastruktur, bessere Stabilität/Verfügbarkeit, DSGVO in eu-central-1. **Zusätzlich:** Bei **gescannten** Gutachten-PDFs (kein Textlayer) könnte **Claude Vision** (wie beim Fahrzeugschein) direkt das PDF-Bild analysieren und Positionen extrahieren. |
| **Aufwand** | Mittel: `_ai_extract_gutachten()` in `api/unfall_rechnungspruefung_api.py` auf Bedrock-Client umstellen (analog `FahrzeugscheinScanner`); optional Vision-Endpoint für Bild-PDFs. |
| **Priorität** | Hoch – Modul bereits auf „AI-extrahiert“ ausgelegt; LM Studio ist lokale Abhängigkeit. |

### 2.2 Bankenspiegel / Transaktionen – Kategorisierung Verwendungszweck

| Aspekt | Beschreibung |
|--------|--------------|
| **Aktuell** | Transaktionen aus MT940/PDF-Import haben oft Freitext (Verwendungszweck, payment_details). Kontenmapping/Kategorisierung teils manuell oder regelbasiert. |
| **KI-Mehrwert** | **Vorschlag Kategorie/Sachkonto** aus Verwendungszweck: Claude nimmt Verwendungszweck + optional Betrag/Empfänger und schlägt eine Kategorie oder ein Sachkonto aus dem bestehenden Kontenmapping vor. Nutzer bestätigt oder korrigiert → weniger manuelle Zuordnung, konsistentere Buchungen. |
| **Aufwand** | Mittel: Neuer API-Call (z. B. bei „Transaktion bearbeiten“ oder Batch „Unkategorisierte vorschlagen“); Prompt mit Liste der Kategorien/Konten; keine Änderung an MT940-Parser nötig. |
| **Priorität** | Hoch – direkte Zeitersparnis für Buchhaltung. |

### 2.3 WhatsApp (Integrations) – Verkauf & Teile

| Aspekt | Beschreibung |
|--------|--------------|
| **Verkauf-Chat** | Verkäufer chatten mit Kunden. **KI:** Kurze **Antwortvorschläge** auf Basis der letzten Nachricht (z. B. „Termin vorschlagen“, „Dokumente nachreichen“, „Rückruf anbieten“); optional **Zusammenfassung** langer Chats für Kollegen. |
| **Teile-Anfragen** | CONTEXT.md: „Teile-Automatik offen – keine automatische Teile-Anfrage-Erkennung/Antwort“. **KI:** Eingehende Nachricht klassifizieren (z. B. „Anfrage Ersatzteil“, „Bestellstatus“, „Sonstiges“); bei Erkennung „Teilerstatz“ strukturierte Felder (Teilenummer, Menge, Fahrzeug) extrahieren und als `whatsapp_parts_requests` anlegen oder Antwortvorschlag generieren. |
| **Aufwand** | Verkauf: gering (ein Endpoint „Vorschlag“ pro Nachricht). Teile: mittel (Klassifikation + ggf. strukturierte Extraktion + Anbindung an Teile-API). |
| **Priorität** | Verkauf: mittel. Teile: hoch, wenn Teile-Automatik gewünscht. |

### 2.4 Einkaufsfinanzierung / Fahrzeugfinanzierungen (Controlling/Finanzen)

| Aspekt | Beschreibung |
|--------|--------------|
| **Aktuell** | **Einkaufsfinanzierung** = gleiche Oberfläche wie Fahrzeugfinanzierungen (Stellantis, Santander, Hyundai Finance, Genobank). Daten kommen aus **CSV/Excel-Imports** (Scripts: `import_santander_bestand.py`, `import_hyundai_finance.py`, `import_stellantis.py`, Genobank aus Locosoft). Zins-Optimierung (`api/zins_optimierung_api.py`) erzeugt **regelbasierte Handlungsempfehlungen** (z. B. „Umfinanzierung Stellantis → Santander“, „Konten-Umbuchung gegen Sollzinsen“). Konditionen in `ek_finanzierung_konditionen` (Zinssatz, Limit pro Institut). |
| **KI-Mehrwert 1 – Import aus PDF** | Wenn Banken nur **PDF** liefern (Kontoauszug, Bestandsliste, Schreiben mit Tabelle): **Claude Vision** kann Tabellen aus PDF/Scan extrahieren → strukturierte Zeilen (VIN, Saldo, Institut, Zinsfreiheit, Betrag, …) wie beim CSV-Import. Einmal-Upload oder regelmäßiger „PDF-Import“-Schritt statt manuelles CSV-Exportieren der Bank. **Hoher Mehrwert**, sobald PDF als Quelle vorkommt. |
| **KI-Mehrwert 2 – Empfehlungen verständlich** | Die Empfehlungen haben heute `typ`, `betrag`, `beschreibung`, `ersparnis_monat`. **KI:** Pro Empfehlung 1–2 Sätze in Alltagssprache („Warum?“ / „So gehen Sie vor“) generieren → Tooltip oder Abschnitt „Erklärung“ im Zinsen-Dashboard/Report. **Mittlerer Mehrwert** (Komfort, Schulung neuer Nutzer). |
| **KI-Mehrwert 3 – Konditionen aus VertragspDFs** | Rahmenverträge oder Zinssatz-Änderungsschreiben der Bank als PDF: Claude extrahiert **Zinssatz, Kreditlimit, Laufzeit, Kündigungsfrist** und schlägt vor, `ek_finanzierung_konditionen` zu aktualisieren. **Mittlerer Mehrwert**, wenn solche PDFs regelmäßig ankommen. |
| **Aufwand** | PDF-Import: mittel (Upload-Endpoint, Vision-Call, Mapping auf `fahrzeugfinanzierungen`-Felder, optional Abgleich mit bestehendem Bestand). Erklärungen: gering (ein Bedrock-Text-Call pro Empfehlung). Konditionen: mittel (PDF-Upload, Extraktion, Vorschlag-UI). |
| **Priorität** | PDF-Import: hoch, sobald PDF-Quellen genutzt werden sollen. Erklärungen/Konditionen: mittel. |

---

## 3. Mittlerer Mehrwert – sinnvolle Erweiterungen

### 3.1 Controlling – DATEV/AfA & sonstige PDFs

| Aspekt | Beschreibung |
|--------|--------------|
| **AfA (CONTEXT.md)** | „DATEV-Scan (Scan_20260216130905.pdf) – keine Textebene, Werte manuell extrahieren.“ **KI:** Gescannte DATEV-PDFs oder Inventarlisten per **Claude Vision** (wie ZB1) analysieren und Tabellenwerte (Konto, Bezeichnung, Betrag, AfA-Parameter) als strukturierte Daten zurückgeben → Import in AfA-Modul oder Abgleich mit Bestand. |
| **Allgemein** | Weitere Bank-/Buchhaltungs-PDFs mit ungewöhnlichem Layout: KI als Fallback-Parser, wenn reguläre Parser (pdfplumber, regex) scheitern. |
| **Aufwand** | Hoch (neue Upload-Pipeline, Schema für DATEV/Inventar); AfA nur bei tatsächlichem Bedarf. |
| **Priorität** | Mittel – nur wenn manuelle Extraktion wegfällt. |

### 3.2 Urlaubsplaner / HR – Anträge & Begründungen

| Aspekt | Beschreibung |
|--------|--------------|
| **Aktuell** | Urlaubsanträge mit optionalem Freitext (Begründung). Genehmiger sieht Liste mit Datum/MA/Begriff. |
| **KI-Mehrwert** | **Kategorisierung** von Begründungen (z. B. „Hochzeit“, „Umzug“, „Krankheit Angehöriger“) für Auswertungen; oder **Kurz-Zusammenfassung** bei sehr langen Begründungen. Kein Muss, eher Komfort. |
| **Priorität** | Niedrig. |

### 3.3 Planung – Kommentare & Annahmen

| Aspekt | Beschreibung |
|--------|--------------|
| **Aktuell** | Abteilungsleiter-Planung, KST-Ziele, Budget mit Freitext-Kommentaren/Annahmen (z. B. in `docs/workstreams/planung/PLANUNGSVORSCHLAG.md`). |
| **KI-Mehrwert** | **Strukturierung** von Freitext-Annahmen in Planungsmasken (z. B. „Annahme: Absatz +5 %“ → strukturiertes Feld); oder **Jahresbericht** aus Kommentaren generieren. |
| **Priorität** | Niedrig – erst bei starkem Freitext-Gebrauch. |

### 3.4 Werkstatt – text_line → Standardarbeit (Arbeitszeitenkatalog)

| Aspekt | Beschreibung |
|--------|--------------|
| **Aktuell** | `loco_labours.text_line` enthält Freitexte; ARBEITSZEITKATALOG_ANALYSE.md: „Optionale Erweiterung: Freitext-Muster → neue Standardarbeit, Mapping text_line → arbeitsnummer“. |
| **KI-Mehrwert** | Claude schlägt für neue/unbekannte `text_line`-Texte eine Zuordnung zu bestehenden Standardarbeiten (labour_operation_id / Katalog) vor → weniger manuelle Nachpflege. |
| **Priorität** | Mittel – abhängig von Entscheidung „Greiner-Katalog/DRIVE-Modul“ (CONTEXT: zuerst Locosoft sauber pflegen). |

---

### 3.5 BWA (Betriebswirtschaftliche Auswertung) – Erklärungen & Kurzfassung

| Aspekt | Beschreibung |
|--------|--------------|
| **Aktuell** | BWA wird aus **loco_journal_accountings** (Locosoft FIBU) berechnet: feste Kontenbereiche (Umsatz 8xxxxx, Einsatz 7xxxxx, variable/direkte/indirekte Kosten, neutrales Ergebnis) → DB1, DB2, DB3, BE, UE. SSOT in `api/controlling_api.py` / `controlling_data.py`; keine Dokumente, kein Freitext – nur Zahlen. |
| **KI-Mehrwert 1 – Erklärung** | Auf Knopfdruck oder in einem Modal: **„Warum hat sich DB1/BE zum Vorjahr verändert?“** – KI erhält die BWA-Zahlen (aktuell + Vorjahr + ggf. YTD) und formuliert 2–4 Sätze in Alltagssprache (z. B. „Umsatz ist um 5 % gestiegen, der Einsatz jedoch um 12 %, daher ist der Bruttoertrag (DB1) gefallen.“). **Reporting/UX**, keine Änderung an Berechnungslogik. |
| **KI-Mehrwert 2 – Kurzfassung** | **Executive Summary** für einen Monat: ein Absatz für die Geschäftsführung („Januar 2026: Umsatz +3 %, DB1 −2 % wegen gestiegenem Einsatz; Betriebsergebnis leicht positiv. YTD liegt über Vorjahr.“). Optional als Baustein für E-Mail/PDF-Reports. |
| **KI-Mehrwert 3 – Anomalie-Hinweis** | Auffällige Abweichungen automatisch kommentieren (z. B. „Variable Kosten dieses Monats +40 % zum Vorjahr – bitte prüfen.“). Optional als Badge oder Tooltip in der BWA-UI. |
| **Aufwand** | Gering bis mittel: ein API-Endpoint (z. B. `POST /api/controlling/bwa/erklaerung`), der aktuelle BWA-Daten + Vorjahr/YTD als Kontext an Bedrock schickt und strukturierten Text (Erklärung oder Kurzfassung) zurückgibt; Frontend zeigt Ergebnis in Modal oder Abschnitt. Anomalie-Logik: einfache Schwellen (z. B. Abweichung &gt; 30 %) + KI-Satz dazu. |
| **Priorität** | Niedrig bis mittel – reiner Komfort und bessere Verständlichkeit, keine Kerndaten. Sinnvoll, wenn BWA stark genutzt wird und Führungskräfte „die Story“ zum Monat wollen. |

---

## 4. Geringer Mehrwert / später

| Bereich | Begründung |
|---------|------------|
| **OPOS (Offene Posten)** | Strukturierte Daten (Rechnungsnr., Betrag, Verkäufer); Kategorisierung/Kommentar optional, kein Kernnutzen. |
| **TEK/BWA-Dashboard** | Berechnungen bleiben SSOT in `controlling_data.py`; KI nur für **Text aus Zahlen** (Erklärung, Kurzfassung, Anomalie-Hinweis) – siehe Abschnitt 3.5 BWA. |
| **Provisionsmodul** | Klare Regeln (Kategorien I–V, Sätze); keine Freitext-Interpretation nötig. |
| **Verkäufer-Zielplanung** | Zahlen und Saisonalität; KI für Kommentare in Planungsgesprächen optional. |
| **Navigation/Rechte** | Kein KI-Bedarf. |

---

## 5. Übersicht nach Priorität

| Priorität | Modul | Use-Case | Technik (Vorschlag) |
|-----------|--------|----------|----------------------|
| **Hoch** | Unfall-Rechnungsprüfung | Gutachten-PDF → strukturierte Positionen | Bedrock (Text wie heute; optional Vision für Scans) |
| **Hoch** | Bankenspiegel | Verwendungszweck → Kategorie/Sachkonto-Vorschlag | Bedrock (Text, einmal pro Transaktion oder Batch) |
| **Hoch** | WhatsApp Teile | Erkennung Teile-Anfrage + strukturierte Extraktion | Bedrock (Text pro eingehender Nachricht) |
| **Hoch** | Einkaufsfinanzierung | Bestandslisten/Kontoauszüge als PDF → Import (VIN, Saldo, Zinsen) | Bedrock Vision (Tabellen-Extraktion wie ZB1) |
| **Mittel** | WhatsApp Verkauf | Antwortvorschläge / Chat-Zusammenfassung | Bedrock (Text) |
| **Mittel** | Einkaufsfinanzierung | Empfehlungen verständlich erklären; Konditionen aus VertragspDFs | Bedrock (Text / Vision) |
| **Mittel** | Controlling/AfA | DATEV/gescannte PDFs → strukturierte Werte | Bedrock Vision (analog ZB1) |
| **Mittel** | Werkstatt | text_line → Standardarbeit-Vorschlag | Bedrock (Text) |
| **Niedrig** | **BWA** | Erklärung „Warum DB1/BE?“; Kurzfassung; Anomalie-Hinweis | Bedrock (Text aus Zahlen) |
| **Niedrig** | Urlaub/Planung | Kategorisierung/Zusammenfassung Freitext | Bedrock (Text) |

---

## 6. Technische Hinweise

- **SSOT für Bedrock:** Credentials in `config/credentials.json` unter `aws_bedrock`; Region eu-central-1 (DSGVO). Referenz-Implementierung: `api/fahrzeugschein_scanner.py`, `api/fahrzeuganlage_api.py`.
- **Bestehende KI:** Unfall nutzt **LM Studio** (`api/ai_api.py`, `lm_studio_client`). Umstellung auf Bedrock reduziert Abhängigkeit von lokalem Server und vereinheitlicht KI-Stack.
- **Vision:** Nur dort einsetzen, wo echte Bilder/Scans vorliegen (ZB1, gescannte Gutachten, DATEV-Scans). Reine Text-PDFs weiter mit pdfplumber + Bedrock Text.

---

## 7. Nächste Schritte (empfohlen)

1. **Unfall-Gutachten:** `_ai_extract_gutachten()` auf Bedrock umstellen (gleiche JSON-Schnittstelle), LM Studio optional als Fallback belassen oder entfernen.
2. **Bankenspiegel:** Kleiner Endpoint „Kategorie vorschlagen“ für eine Transaktion (Verwendungszweck + ggf. Betrag) mit Rückgabe Kategorie/Sachkonto; in UI „Vorschlag übernehmen“.
3. **WhatsApp Teile:** Mit Fachbereich klären, ob Teile-Automatik gewünscht; wenn ja: Klassifikation + Extraktion mit Bedrock, Anbindung an `whatsapp_parts_requests` und Teile-API.

Kein Code in dieser Analyse – nur Bewertung und Empfehlung für weitere KI-Einsatzstellen in DRIVE.
