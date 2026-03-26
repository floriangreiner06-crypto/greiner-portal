# Garantieakte – Möglichkeiten der weiteren Automatisierung

**Stand:** 2026-03  
**Workstream:** werkstatt  
**Kontext:** Beim Klick auf „Erstellen“ wird ein Ordner im konfigurierten Verzeichnis (Hyundai/Stellantis) angelegt; darin landen Arbeitskarte-PDF, Gudat-Anhänge (einzeln), ggf. Terminblatt und `.metadata.json`. Nachfolgend Ideen für **weitere** Automatisierung – ohne Code, nur Plan.

---

## 1. Aktueller Ablauf (Kurz)

- **Auslöser:** User klickt in Garantieaufträge-Übersicht oder im Werkstatt-Live-Auftrags-Modal auf „Erstellen“.
- **Backend:** `speichere_garantieakte` → `hole_arbeitskarte_daten`, Anhänge aus Gudat, `generate_arbeitskarte_pdf`, `create_garantieakte_vollstaendig`.
- **Ergebnis:** Ordner `{Kunde}_{Auftragsnr}` mit:
  - Arbeitskarte-PDF
  - Anhänge (Bilder/PDFs aus Gudat)
  - Terminblatt-PDF (falls vorhanden)
  - `.metadata.json` (Ersteller, Datum)

---

## 2. Mögliche Erweiterungen (Priorität grob sortiert)

### 2.1 Auslöser & Zeitpunkt

| Idee | Beschreibung | Nutzen | Aufwand (grob) |
|------|--------------|--------|------------------|
| **Automatische Erstellung bei „Akte fehlt“** | Celery-Task oder täglicher Lauf: Für offene Garantieaufträge der letzten X Tage, bei denen noch **kein** Ordner existiert, Garantieakte automatisch anlegen (wie beim manuellen „Erstellen“). Optional: nur wenn Auftrag schon Stempelzeiten/Mechaniker hat. | Weniger vergessene Akten; Service muss nicht jeden Auftrag manuell prüfen. | Mittel (Task, Fehlerbehandlung, Dossier-Fallback). |
| **Erinnerung statt Auto-Erstellung** | Statt sofort zu erstellen: Liste/E-Mail „Diese Garantieaufträge haben noch keine Akte“ (z. B. täglich oder wöchentlich). User klickt weiterhin manuell „Erstellen“. | Geringerer Implementierungsaufwand, trotzdem klare Steuerung. | Gering. |
| **Batch-Erstellung** | Button „Alle fehlenden Akten der letzten 7 Tage erstellen“ (oder Filter: Marke, Zeitraum). Ein Klick → mehrere Akten nacheinander. | Weniger Klicks bei vielen neuen Aufträgen. | Gering bis mittel. |

### 2.2 Dossier & Gudat

| Idee | Beschreibung | Nutzen | Aufwand (grob) |
|------|--------------|--------|------------------|
| **Dossier-Suche robuster machen** | Heute: Bei Stellantis/Landau wird teils manuell Dossier-ID eingegeben. Suche über Kennzeichen/VIN/Zeitraum ausbauen (z. B. DA REST API für Landau), Fallback-Reihenfolge dokumentieren. | Weniger manuelle Dossier-Eingabe. | Mittel (API-Nutzung, Tests). |
| **Generierte Akte in Gudat hochladen** | Nach Erstellung: Arbeitskarte-PDF (oder Gesamt-PDF) per API in Gudat-Dossier als Dokument hochladen. | Hersteller/Abwicklung sehen die Akte direkt in Gudat. | Mittel (Upload-API, Rechte). |
| **Gudat-Status in Übersicht** | In der Garantieaufträge-Tabelle anzeigen: „Dossier gefunden“ / „Dossier nicht gefunden“ (ohne Erstellung). | Schnell sichtbar, wo manuell nachhelfen muss. | Gering. |

### 2.3 Ordner & Dateien

| Idee | Beschreibung | Nutzen | Aufwand (grob) |
|------|--------------|--------|------------------|
| **Checkliste/Platzhalter im Ordner** | Beim Anlegen automatisch leere oder Platzhalter-Dateien/Unterordner (z. B. „Fahrzeugschein“, „Gutachten“, „Foto Schaden“) anlegen – als Erinnerung, was noch reinkommt. | Einheitliche Struktur; weniger Vergessen. | Gering (Konvention pro Marke klären). |
| **Aktualisierung bestehender Akten** | Option „Akte aktualisieren“: Gleicher Ordner, Arbeitskarte/Anhänge neu holen und überschreiben bzw. ergänzen (z. B. neue Gudat-Anhänge). Versionsnummer oder Datum im Dateinamen. | Akte bleibt aktuell, ohne neuen Ordner. | Mittel (Überschreib-Regeln, Konflikte). |
| **Hersteller-Upload (Hyundai GWS / Stellantis)** | Nach Ordnererstellung: Generierte Dokumente in Hersteller-Portal hochladen (sofern API/Prozess vorhanden). | Weniger manueller Upload in GWS/Stellantis. | Hoch (APIs, Freigabe, Fehlerbehandlung). |

### 2.4 Prozess & Benachrichtigung

| Idee | Beschreibung | Nutzen | Aufwand (grob) |
|------|--------------|--------|------------------|
| **Erstellung im Hintergrund (Celery)** | „Erstellen“ startet nur einen Task; User bekommt Meldung „wird erstellt“ und optional E-Mail/Link, wenn fertig. | Kein Warten im Browser; bei vielen Anhängen stabiler. | Mittel (Task, Status, ggf. E-Mail). |
| **Benachrichtigung bei neuem Garantieauftrag ohne Akte** | Täglich oder bei bestimmten Events: „N neue Garantieaufträge (offen, in Bearbeitung) ohne Akte“ an Service/Serviceleitung. | Frühe Erinnerung. | Gering (bereits Liste vorhanden, nur Versand). |
| **Abgleich mit Locosoft** | Wenn Auftrag in Locosoft geschlossen/fakturiert wird: Optional „Akte archivieren“ oder Status „abgeschlossen“ setzen (nur Metadaten, Ordner bleibt). | Klarheit, welche Akten noch „aktiv“ sind. | Gering bis mittel (Trigger/Job, Definition „abgeschlossen“). |

### 2.5 Übersicht & Filter

| Idee | Beschreibung | Nutzen | Aufwand (grob) |
|------|--------------|--------|------------------|
| **Filter „Ohne Akte“** | In Garantieaufträge-Übersicht Filter „Nur ohne Akte“ (existiert teils schon als Anzeige; als expliziter Filter/Export). | Fokus auf offene Fälle. | Gering. |
| **Export Liste „Ohne Akte“** | CSV/Excel der Aufträge ohne Akte (Datum, Kunde, SB, Kennzeichen) für Planung/Verteilung. | Nutzbar außerhalb des Browsers. | Gering. |

---

## 3. Empfohlene Reihenfolge (ohne Festlegung)

1. **Schnell umsetzbar:** Erinnerung/Liste „ohne Akte“, Filter „Ohne Akte“, ggf. Gudat-Status-Spalte; optional Batch-Erstellung für letzte 7 Tage.
2. **Mittelfristig:** Automatische Erstellung (Celery) für „Akte fehlt“ mit klaren Regeln (Zeitraum, nur mit Stempel/Mechaniker); robusteres Dossier-Matching (v. a. Landau/Stellantis).
3. **Nach Klärung:** Upload generierter Akte in Gudat; Checkliste/Platzhalter im Ordner; optional Hersteller-Portal-Anbindung.

---

## 4. Offene Punkte

- Soll die Akte **immer** automatisch erstellt werden, sobald ein Garantieauftrag „in Bearbeitung“ ist, oder nur auf Erinnerung/Batch?
- Soll die **Arbeitskarte** (oder ein Gesamt-PDF) in **Gudat** hochgeladen werden – und erlaubt die Gudat-API das?
- Gibt es Vorgaben der Marken (Hyundai/Stellantis) zur **Ordnerstruktur** oder zu Pflichtdokumenten (Checkliste)?

---

*Nur Plan; keine Code-Änderungen. Nächster Schritt: Priorisierung mit Service/IT, danach ggf. konkrete Tickets pro Idee.*
