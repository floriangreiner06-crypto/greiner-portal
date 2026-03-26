# Konzept: KI-Befüllung (Bedrock), Freigabe-Prozess, Schulung nach Rolle

**Stand:** 2026-02-24  
**Workstream:** Hilfe

---

## 1. Ausgangslage

- DRIVE wurde weitgehend mit Claude entwickelt; eine manuelle Befüllung aller Hilfe-Inhalte ist nicht realistisch.
- **Ziel:** KI (AWS Bedrock, bestehende Anbindung) nutzen, um Artikel zu erzeugen bzw. zu erweitern, mit **Freigabe durch einen Menschen** vor der Veröffentlichung.
- **Zusätzlich:** Eine **Schulung nach Rolle**, damit User (z. B. Verkauf, Buchhaltung, Service) eine auf sie zugeschnittene „Lern-/Onboarding-Ansicht“ bekommen.

---

## 2. KI-Befüllung mit Bedrock

### 2.1 Bestehende Anbindung nutzen

- **Fahrzeuganlage** nutzt bereits AWS Bedrock (eu-central-1) über `config/credentials.json` → `aws_bedrock` (region, access_key_id, secret_access_key, model_id).
- **Gleiche Credentials** für das Hilfe-Modul verwenden; nur **Text-API** (kein Bild), z. B. `client.converse()` mit reinem Text-Prompt.

### 2.2 Zwei Nutzungsszenarien

| Szenario | Auslöser | Eingabe | Ausgabe |
|----------|----------|---------|---------|
| **Erweitern** | Admin klickt „Mit KI erweitern“ bei bestehendem Artikel | Titel + aktueller Inhalt (Markdown) | Längerer Artikel (gleiche Struktur: Kurz-Antwort, Schritt für Schritt, Hinweise), als **Vorschlag** |
| **Neu generieren** | Admin klickt „Mit KI erstellen“ (z. B. in Kategorie, nur Titel/Stichpunkte) | Kategorie-Name + Titel + optionale Stichpunkte | Neuer Artikel als **Vorschlag** (Entwurf) |

In beiden Fällen: **Kein automatisches Speichern**. Der Vorschlag wird im Admin angezeigt; der Mensch übernimmt, passt an und speichert (dann greift der Freigabe-Prozess).

### 2.3 Technik (kurz)

- **Neues Modul** z. B. `api/hilfe_bedrock_service.py`: lädt `aws_bedrock` aus `credentials.json`, baut Prompt, ruft `bedrock-runtime.converse()` auf, gibt Markdown-Text zurück.
- **Prompt:** System-Prompt + User-Prompt mit Kontext („DRIVE ist ein internes Portal für Autohaus Greiner. Zielgruppe: Mitarbeiter. …“) und konkretem Auftrag („Erweitere folgenden Hilfe-Artikel …“ / „Erstelle einen Hilfe-Artikel zu …“). Antwort nur in Markdown, gleiche Abschnittsstruktur.
- **API:** Z. B. `POST /api/hilfe/ki/erweitern` (Body: artikel_id) und `POST /api/hilfe/ki/erstellen` (Body: kategorie_id, titel, stichpunkte?). Nur für Admins (`@admin_required`). Antwort: `{ "inhalt": "…" }` oder Fehler.

### 2.4 UI im Hilfe-Admin

- Beim **Bearbeiten** eines Artikels: Button **„Mit KI erweitern“** → Backend holt aktuellen Inhalt, ruft Bedrock auf, Frontend zeigt Vorschlag in einem zweiten Textfeld oder Modal; User kann übernehmen/bearbeiten/speichern.
- Beim **Neuen Artikel**: Optional Button **„Mit KI aus Titel erstellen“** → Backend sendet Kategorie + Titel an Bedrock, Vorschlag wird in das Inhalt-Feld übernommen (oder in Modal), User passt an und speichert.

---

## 3. Freigabe-Prozess

### 3.1 Idee

- Nicht jeder KI- oder Redaktions-Entwurf soll sofort für alle sichtbar sein.
- **Zustände:** z. B. **Entwurf** (nur in Admin sichtbar, ggf. für bestimmte Rollen sichtbar) und **Freigegeben** (für alle berechtigten User in der normalen Hilfe sichtbar).

### 3.2 DB-Erweiterung (Vorschlag)

- Tabelle **hilfe_artikel** um folgende Spalten ergänzen (Migration):
  - **freigabe_status:** `'entwurf' | 'freigegeben'` (Default: `'entwurf'` für neu angelegte, `'freigegeben'` für bestehende Seed-Artikel).
  - **freigegeben_am:** TIMESTAMP NULL (wann freigegeben).
  - **freigegeben_von:** VARCHAR NULL (User, der freigegeben hat).

- **Regel:** In der **öffentlichen** Hilfe (Übersicht, Kategorie, Artikel, Suche) werden nur Artikel mit `freigabe_status = 'freigegeben'` und `aktiv = true` angezeigt. Im **Admin** werden alle Artikel angezeigt; bei Entwürfen wird ein Hinweis „Entwurf – nicht sichtbar“ angezeigt.

### 3.3 Ablauf

1. Admin erstellt/erweitert Artikel (manuell oder mit KI-Vorschlag) → Speichern → Status bleibt **Entwurf** (oder wird auf Entwurf gesetzt, wenn gewünscht).
2. Redaktion/Admin prüft den Inhalt im Admin-Bereich.
3. Admin klickt **„Freigeben“** → `freigabe_status = 'freigegeben'`, `freigegeben_am = NOW()`, `freigegeben_von = current_user.username` → Artikel erscheint in der Hilfe.
4. Optional: **„Zurück auf Entwurf“** setzt Status wieder auf Entwurf (z. B. bei Korrekturbedarf).

### 3.4 API

- `PATCH /api/hilfe/admin/artikel/<id>` oder dediziert: `POST /api/hilfe/admin/artikel/<id>/freigeben` und `POST /api/hilfe/admin/artikel/<id>/entwurf`.
- Alle Lese-Endpoints (kategorien, kategorie, artikel, suche, beliebt) filtern nach `freigabe_status = 'freigegeben'` (und aktiv, ggf. sichtbar_fuer_rollen).

---

## 4. Schulung nach Rolle

### 4.1 Ziel

- User sollen eine **Schulungs- bzw. Onboarding-Ansicht** sehen, die **auf ihre Rolle zugeschnitten** ist (z. B. Verkauf sieht „Auftragseingang“, „Zielplanung“, „Provision“; Buchhaltung sieht „TEK“, „Bankenspiegel“, „OPOS“).
- Keine doppelte Inhaltepflege: Es sollen **dieselben Hilfe-Artikel** genutzt werden, nur **gefiltert und anders gruppiert**.

### 4.2 Variante A: Schulung = gefilterte Hilfe (empfohlen)

- **Neue Route** z. B. `/hilfe/schulung` (oder „Meine Schulung“ im Menü).
- **Inhalt:** Liste von **Kategorien** und **Artikeln**, die für die **Rolle des aktuellen Users** relevant sind.
  - **Relevanz** entweder über bestehendes Feld **sichtbar_fuer_rollen** (kommagetrennt): Artikel, die diese Rolle enthalten oder leer (alle), werden angezeigt.
  - Oder neues optionales Feld **schulung_rollen** (kommagetrennt): Nur wenn gesetzt, erscheint der Artikel in der Schulung für diese Rollen; wenn leer, erscheint er in der Schulung für alle (oder nicht in Schulung – je nach Regel).
- **Darstellung:** Gleiche Artikel wie in der Hilfe, aber z. B.:
  - Überschrift „Meine Schulung – [Rolle]“
  - Gruppierung nach Kategorien (wie Hilfe)
  - Optional: **„Als gelesen“** abhaken (siehe unten)

### 4.3 Optional: Fortschritt „Als gelesen“

- Tabelle **hilfe_schulung_fortschritt:** (user_id, artikel_id, gelesen_am).
- In der Schulungs-Ansicht: Pro Artikel Checkbox oder Button **„Als gelesen markieren“** → Eintrag in dieser Tabelle.
- Anzeige: z. B. Häkchen oder „Gelesen am …“ neben Artikeln, die der User bereits markiert hat; optional Fortschrittsbalken („3 von 8 gelesen“).

### 4.4 Rollen-Mapping

- **portal_role** des Users (z. B. verkauf, buchhaltung, serviceberater, admin) kommt aus dem bestehenden Auth-System.
- Artikel mit `sichtbar_fuer_rollen = 'verkauf,verkauf_leitung'` erscheinen in der Schulung für User mit Rolle **verkauf** oder **verkauf_leitung**.
- Artikel mit leerem `sichtbar_fuer_rollen` können in der Schulung entweder für **alle** Rollen angezeigt werden oder nur in der normalen Hilfe (je nach gewünschter Logik). Empfehlung: In der Schulung alle Artikel anzeigen, die der User **berechtigungsmäßig** sehen darf (wie in der Hilfe), aber **sortiert/nur die für „Schulung“ vorgesehenen** – dazu reicht ggf. ein neues Flag **für_schulung** (boolean) pro Artikel oder pro Kategorie.

### 4.5 Einfache Umsetzung (Phase 1)

- **Schulung** = eine Seite, die dieselbe API wie die Hilfe nutzt, aber:
  - Nur Kategorien/Artikel, bei denen **sichtbar_fuer_rollen** die aktuelle User-Rolle enthält **oder** leer ist („für alle“).
  - Titel der Seite: **„Meine Schulung“** oder **„Schulung – [Rollenname]“**.
- **Kein** eigenes „Kurs“-Konzept zunächst; keine Pflicht „alle lesen“. Optional später: Fortschritt (gelesen) und Hinweis „Noch X Artikel für Ihre Rolle“.

### 4.6 Navigation

- Neuer Eintrag in **navigation_items** z. B. „Meine Schulung“ mit URL `/hilfe/schulung` (oder unter „Hilfe“ als Unterpunkt). Für alle sichtbar (requires_feature leer), da jeder seine rollenspezifische Ansicht bekommt.

---

## 5. Reihenfolge der Umsetzung (Vorschlag)

| Phase | Inhalt |
|-------|--------|
| **1** | **Freigabe-Prozess:** Migration (freigabe_status, freigegeben_am, freigegeben_von), API anpassen (Filter + Endpoints Freigeben/Entwurf), Admin-UI (Button „Freigeben“ / „Zurück auf Entwurf“). Bestehende Artikel auf `freigegeben` setzen. |
| **2** | **Bedrock-Integration:** Service `hilfe_bedrock_service.py`, Prompts für „Erweitern“ und „Erstellen“, API `POST /api/hilfe/ki/erweitern` und `.../ki/erstellen`, Buttons im Hilfe-Admin. |
| **3** | **Schulung nach Rolle:** Route `/hilfe/schulung`, Ansicht gefiltert nach portal_role + sichtbar_fuer_rollen, optional Fortschritt (hilfe_schulung_fortschritt), Navi-Eintrag „Meine Schulung“. |

---

## 6. Kurzfassung

- **KI:** Bedrock wie in der Fahrzeuganlage; „Mit KI erweitern“ und „Mit KI erstellen“ im Hilfe-Admin, Ergebnis nur Vorschlag → Mensch speichert und gibt frei.
- **Freigabe:** Status **Entwurf/Freigegeben**, nur freigegebene Artikel in der Hilfe sichtbar; Admin kann freigeben oder zurück auf Entwurf.
- **Schulung:** Eigene Seite „Meine Schulung“ mit denselben Hilfe-Artikeln, gefiltert nach **Rolle** (sichtbar_fuer_rollen / portal_role), optional „Als gelesen“-Fortschritt.

Wenn du mit dieser Reihenfolge einverstanden bist, kann als Nächstes **Phase 1 (Freigabe)** konkret umgesetzt werden (Migration + API + Admin-UI).
