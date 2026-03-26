# Design-Workflow: benötigte Tools installieren

Kurze Anleitung für Figma MCP + Design-Audit in Cursor (Stand: 2026-03-13).

---

## Was denn nun: Figma Desktop oder nicht?

**Empfehlung: Ja, Figma Desktop** — wenn ihr in Cursor mit Figma-Entwürfen arbeiten wollt (Design aus Figma lesen, mit DRIVE vergleichen, Umsetzung ableiten). Die Einrichtung ist einmalig, der Desktop-MCP ist die offizielle und einfachste Variante (nur URL in Cursor eintragen, kein OAuth).

**Ihr braucht Figma (Desktop oder Browser) nicht** für den reinen **Design-Audit der laufenden DRIVE-Seite**: DRIVE im Browser öffnen, in Cursor „Analysiere diese Seite …“ — das geht mit dem Browser-MCP ohne Figma.

**Kurz:**  
- Nur Audit der Live-Seite → kein Figma nötig.  
- Figma-Entwürfe in Cursor nutzen (Redesign, Vergleich, Umsetzung) → **Figma Desktop installieren** und Desktop-MCP wie unten einrichten.

---

## 1. Cursor (bereits vorhanden)

Cursor ist deine IDE mit nativer MCP-Unterstützung. Keine zusätzliche Installation nötig.

---

## 2. Cursor IDE Browser MCP (für Design-Audit)

Damit der Agent die **laufende DRIVE-Seite** im Browser erfassen und einen Design-Audit erstellen kann, wird ein **Browser-MCP** benötigt (Seite öffnen, Snapshot, Analyse).

### Option A: Eingebauten Browser-MCP prüfen

Cursor bringt teils einen eingebauten **cursor-ide-browser** mit:

1. **Cursor** → **Einstellungen** (Datei → Einstellungen oder Cursor → Settings).
2. Zu **MCP** wechseln.
3. In der Liste prüfen, ob **„Browser“**, **„cursor-ide-browser“** oder ähnlich auftaucht.
4. Falls ja: **aktivieren** (Haken/Toggle) und Cursor **neu starten**.

Wenn danach im Chat/Agent der Browser-MCP verfügbar ist, kannst du z. B. sagen: *„Öffne http://drive und erstelle einen Design-Audit.“*

**Hinweis:** Bei einigen Setups erscheint der eingebaute Browser-MCP nicht oder meldet „No server found“. Dann **Option B** nutzen.

### Option B: Playwright MCP hinzufügen (Alternative)

**Playwright MCP** ist von Cursor dokumentiert und eignet sich für Browser-Automatisierung (Seiten öffnen, Snapshots, Tests):

1. **Node.js** muss installiert sein (für `npx`). Unter Windows: [nodejs.org](https://nodejs.org/) (LTS).
2. **Cursor** → **Einstellungen** → **MCP** → **„Add new global MCP server“** / „Neuen MCP-Server hinzufügen“.
3. Konfiguration eintragen (je nach Cursor-UI):
   - **Typ:** `command` (oder „Run command“).
   - **Command:** `npx`
   - **Args:** `-y`, `@playwright/mcp@latest`
   Oder in **mcp.json** (z. B. `~/.cursor/mcp.json`) neben dem bestehenden Figma-Eintrag ergänzen:

```json
{
  "mcpServers": {
    "figma-desktop": {
      "url": "http://127.0.0.1:3845/mcp"
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

4. **Speichern**, Cursor **neu starten**. Beim ersten Mal lädt `npx` das Playwright-MCP-Paket (Internet nötig).

**Doku:** [Cursor MCP – Playwright](https://cursor.com/docs/mcp) (in der Server-Tabelle: Playwright, „End-to-end browser testing“).

---

## 3. Figma MCP in Cursor einrichten

**Empfohlen:** Option A (Figma Desktop). Option B nur, wenn ihr keine Desktop-App nutzen wollt.

### Option A: Figma Desktop + Desktop-MCP (empfohlen)

**Voraussetzungen:**

- **Figma-Desktop-App** (neueste Version)  
  - Download: [Figma Desktop](https://www.figma.com/downloads/)  
  - Unter Windows: Installer ausführen und Figma starten.

**Schritte:**

1. Figma-Desktop-App öffnen (nicht im Browser – echte Desktop-App). Eine **Figma-Design-Datei** öffnen oder anlegen (keine FigJam-Datei).
2. **Dev Mode einschalten:**
   - Tastatur: **Umschalt + D** (Shift + D), oder
   - In der **Toolbar** den Schalter „Dev Mode“ suchen – je nach Version **oben rechts** in der Leiste oder in einer **unteren** Toolbar. Oft als Toggle/Label „Dev Mode“ neben den anderen Modi.
3. Rechts öffnet sich das **Inspect-Panel**. Darin nach dem Abschnitt **„MCP“** oder **„Desktop MCP server“** suchen und **„Enable desktop MCP server“** (bzw. „MCP-Server aktivieren“) anklicken.
4. Die angezeigte Adresse kopieren – in der Regel: **`http://127.0.0.1:3845/mcp`**
5. In **Cursor**:
   - **Einstellungen** öffnen (z. B. `Ctrl+,` / `Cmd+,`).
   - Zu **MCP** wechseln (oder nach „MCP“ suchen).
   - **„Add new global MCP server“** / „Neuen MCP-Server hinzufügen“ wählen.
   - Folgende Konfiguration eintragen (Name kann z. B. `figma-desktop` sein):

```json
{
  "mcpServers": {
    "figma-desktop": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

6. Speichern. Cursor ggf. neu starten.  
7. **Wichtig:** Der Figma-Desktop-MCP funktioniert nur, **wenn die Figma-Desktop-App läuft** und der MCP-Server dort aktiviert ist.

**RDS / Remote Desktop:** Wenn du Cursor in einer **RDS-** oder **Citrix-Sitzung** nutzt, zeigt `127.0.0.1` auf den Remote-Server, nicht auf deinen Rechner. Figma Desktop läuft typischerweise lokal → Verbindung zu `127.0.0.1:3845` schlägt fehl (ECONNREFUSED). In dem Fall **Figma Remote MCP** verwenden (Option B, URL z. B. `https://mcp.figma.com/mcp`, OAuth) – der funktioniert von überall.

**Offizielle Hilfe:** [Figma: Desktop MCP Server einrichten](https://help.figma.com/hc/en-us/articles/35281186390679)

**Dev Mode / MCP wird nicht angezeigt?**

- **Nur in Design-Dateien:** Dev Mode gibt es nur in **Figma Design** („Design“ beim Öffnen/Anlegen), nicht in FigJam.
- **Lizenz:** Der **Desktop-MCP-Server** erfordert ein **kostenpflichtiges Abo** mit **Dev-** oder **Full-Sitz** (Organization/Professional). Bei reinem Free-Plan ist Dev Mode/MCP unter Umständen nicht verfügbar. Dann: **Option B (Remote MCP)** nutzen – der ist für alle Lizenzen nutzbar.
- **App aktualisieren:** Figma Desktop auf die neueste Version bringen (Hilfe → Nach Updates suchen bzw. [Figma Downloads](https://www.figma.com/downloads/)).

**Kurz: Wo ist Dev Mode?**  
Design-Datei öffnen → **Shift + D** oder Toggle „Dev Mode“ in der Toolbar (oben rechts oder unten) → rechts erscheint das Inspect-Panel → darin Abschnitt **MCP** → „Enable desktop MCP server“.

**Hinweis:** Beim ersten Mal kann ein Dialog „Willkommen im Dev Mode“ (Schritt 3: MCP-Server aktivieren) erscheinen. Die tatsächliche Aktivierung erfolgt im **rechten Inspect-Panel**: Dialog ggf. schließen (X oder „Weiter: Plugins“), dann rechts nach dem Abschnitt **MCP** suchen und dort „Enable desktop MCP server“ anklicken.

---

### Option B: Figma Remote MCP (Alternative ohne Desktop-App)

Nur wenn ihr die Figma-Desktop-App nicht installieren wollt und **nur** im Browser mit Figma arbeitet:

- Remote-MCP per OAuth einrichten.  
- Doku: [Figma: Remote MCP Server](https://help.figma.com/hc/en-us/articles/35281350665623)  
- In Cursor wieder unter **Settings → MCP** den Remote-Server hinzufügen (URL und ggf. Auth wie in der Figma-Doku beschrieben).

---

## 4. Browser für Design-Audit (DRIVE)

- **DRIVE** im Browser öffnen: `http://drive` (intern) oder `http://<Server-IP>:5000` bzw. localhost, je nach Setup.
- Die Seite, die auditiert werden soll (z. B. Startseite, Rechteverwaltung), anzeigen.
- In Cursor dann z. B.: *„Analysiere diese laufende Seite und erstelle einen Design-Audit.“*  
- Der **Cursor-IDE-Browser-MCP** (falls aktiviert) kann die geöffnete Seite erfassen; ohne ihn kannst du Screenshots oder Beschreibungen nutzen.

---

## 5. Checkliste

| Schritt | Erledigt |
|--------|----------|
| Cursor installiert / genutzt | ☐ |
| Figma-Desktop installiert (Option A) oder Remote-MCP geplant (Option B) | ☐ |
| In Figma: Dev Mode → MCP-Server aktiviert (Option A) | ☐ |
| In Cursor: MCP-Server „figma-desktop“ (oder Remote) hinzugefügt | ☐ |
| Browser-MCP: eingebaut aktiv oder Playwright MCP hinzugefügt (für Design-Audit) | ☐ |
| Cursor ggf. neu gestartet | ☐ |
| DRIVE im Browser getestet (http://drive oder localhost) | ☐ |

---

## 6. Nächster Schritt nach der Installation

1. DRIVE im Browser öffnen (Seite für Audit).
2. In Cursor: *„Analysiere diese laufende Seite und erstelle einen Design-Audit.“*
3. Optional: Vergleich mit Startseiten- oder Rechteverwaltungs-Mockup anfordern.
4. Ergebnis als Basis für Figma-Entwürfe und Redesign nutzen.

Vorgehensweise im Detail: `CONTEXT.md` (Abschnitt „Vorgehensweise: Figma MCP + Design-Audit“).
