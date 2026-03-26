# Vorschlag: Portal-Übersicht Modalitäten-DB (editierbar)

**Stand:** 2026-02  
**Kontext:** Einkaufsfinanzierung, Santander/Stellantis-Limits, Zinsen-Optimierung. Die Modalitäten-DB (`kredit_anbieter`, `kredit_vertragsart`, `kredit_ausfuehrungsbestimmungen`) hat bisher nur eine API, keine Übersichtsseite im Portal.

---

## 1. Ziele

- **Übersicht:** Anbieter, Vertragsarten und alle Parameter (Regeln) der Modalitäten-DB in einer Seite sichtbar.
- **Editierbarkeit:** Werte (z. B. `regel_wert`) sollen änderbar sein, um z. B.:
  - Santander-Rahmen (1,5 Mio, 500k Mobilität) anzupassen,
  - Stellantis-Zinsfreiheit oder Zinssatz zu pflegen,
  - **neue Steuerparameter** zu setzen, z. B. **Ziel Linienauslastung Stellantis** (%), die künftig in Auswertungen oder Handlungsempfehlungen genutzt werden.
- **Einordnung:** Seite im Admin-Bereich (z. B. unter Konfiguration) oder im Bereich Finanzen/Controlling, mit Berechtigung z. B. Feature `bankenspiegel` oder Rolle `admin`.

---

## 2. Datenmodell (kurz)

| Tabelle | Inhalt |
|--------|--------|
| `kredit_anbieter` | Stellantis, Santander, Hyundai Finance, Genobank |
| `kredit_vertragsart` | Pro Anbieter: z. B. EK-NW, EK-GW, EK |
| `kredit_dokumente` | Quelldokumente (PDF, Referenz) |
| `kredit_ausfuehrungsbestimmungen` | **Regeln:** `regel_typ`, `regel_key`, `regel_wert`, `einheit`, `bedingung`, `volltext` |

Bestehende API: `GET /api/bankenspiegel/modalitaeten` (Filter: `anbieter`, `regel_key`, `vertragsart_id`).

---

## 3. Funktionale Anforderungen

- **Filter:** Nach Anbieter (Dropdown), optional nach Vertragsart.
- **Darstellung:** Gruppierung nach Anbieter → Vertragsart; pro Vertragsart eine Tabelle der Ausführungsbestimmungen (Regel-Typ, Key, **Wert**, Einheit, Bedingung).
- **Bearbeiten:** 
  - Inline oder per Klick „Bearbeiten“: `regel_wert` (und optional `bedingung` / Kurzinfo) ändern, Speichern pro Zeile oder pro Block.
  - Nur bestimmte Zeilen als „editierbar“ markieren (z. B. vertragsbezogene Limits und Ziele), Referenz-Texte aus PDF nur lesen.
- **Neuer Parameter:** Button „Neuer Parameter“ pro Vertragsart: `regel_typ` (z. B. `ziel`), `regel_key` (z. B. `linienauslastung_ziel`), `regel_wert`, `einheit` (z. B. `Prozent`) anlegen. So kann z. B. ein **Ziel Linienauslastung Stellantis** ohne Migration gepflegt werden.
- **Berechtigung:** Zugriff nur für Nutzer mit Feature (z. B. `bankenspiegel`) oder Admin; Schreibzugriff ggf. nur Admin.

---

## 4. Erweiterung „Ziel Linienauslastung Stellantis“

- **Regel:** In `kredit_ausfuehrungsbestimmungen` eine Zeile für Stellantis (Vertragsart EK-NW oder eigene „Steuerung“-Vertragsart) mit z. B.:
  - `regel_typ`: `ziel`
  - `regel_key`: `linienauslastung_ziel`
  - `regel_wert`: `85` (oder `85.5`)
  - `einheit`: `Prozent`
  - `bedingung`: `Stellantis EK-Finanzierung – Ziel Auslastung der Linie`
- **Nutzung:** Andere Module (z. B. Einkaufsfinanzierung, Reporting) lesen diesen Wert und vergleichen Ist-Auslastung mit Ziel oder nutzen ihn für Ampeln/Kennzahlen. Die konkrete Auslastungsberechnung (z. B. aus Bestand/Linie) bleibt in den jeweiligen Modulen; die Modalitäten-DB ist SSOT für den **Soll-Wert**.

---

## 5. Technische Umsetzung (Vorschlag)

- **Route:** z. B. `/admin/modalitaeten` oder `/bankenspiegel/modalitaeten-verwaltung` (Blueprint `bankenspiegel_routes` oder `admin_routes`).
- **Template:** `templates/admin/modalitaeten_verwaltung.html` (oder unter `templates/bankenspiegel/`).
- **API-Erweiterung:**
  - `PATCH /api/bankenspiegel/modalitaeten/<id>`: Einzelne Ausführungsbestimmung (`regel_wert`, ggf. `bedingung`) aktualisieren; Body: `{ "regel_wert": "1500000", "bedingung": "optional" }`.
  - `POST /api/bankenspiegel/modalitaeten`: Neue Regel anlegen; Body: `vertragsart_id`, `regel_typ`, `regel_key`, `regel_wert`, `einheit`, `bedingung` (optional).
- **Frontend:** JS lädt `GET /api/bankenspiegel/modalitaeten`, baut gruppierte Tabellen, Inline-Edit oder kleines Modal für Wert + Speichern; „Neuer Parameter“ öffnet Formular, sendet POST, listet danach neu.
- **Navigation:** Eintrag unter „Konfiguration“ (Admin) oder unter Bankenspiegel/Finanzen, z. B. „Modalitäten & Parameter“.

---

## 6. Mockup

Eine statische HTML-Datei zeigt das geplante Layout und die editierbaren Felder:

- **Datei:** `MODALITAETEN_UEBERSICHT_MOCKUP.html` (im gleichen Ordner)
- **Inhalt:** Filter Anbieter, Blöcke pro Anbieter/Vertragsart, Tabelle mit Spalten Regel-Typ, Key, **Wert (editierbar)**, Einheit, Bedingung, Aktionen (Speichern). Beispiel „Ziel Linienauslastung Stellantis“ als zusätzliche Zeile. Button „Neuer Parameter“.

Nach der Freigabe des Vorschlags können Route, API PATCH/POST, Template und JS schrittweise umgesetzt werden.
