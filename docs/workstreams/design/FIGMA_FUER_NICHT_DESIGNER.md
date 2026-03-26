# Figma mit Agent-Unterstützung nutzen (ohne Designer zu sein)

Du musst nicht selbst designen – der Agent liefert die Werte und Spezis, du nutzt Figma als Ablage und für Abnahme.

---

## 1. Deine Rolle

- **Du:** Figma öffnen, Tokens importieren (einmalig), Frames/Screens anlegen wenn nötig, mit Stakeholdern teilen und Feedback sammeln.
- **Der Agent (Cursor):** Design-Entscheidungen (Farben, Typo, Spacing), Token-Dateien, detaillierte Spezis und ggf. HTML-Mockups als Vorlage – du übernimmst nur die Werte in Figma oder nutzt die Vorlagen.

---

## 2. Tokens in Figma bringen (einmalig)

Es gibt eine **Token-Datei** im Design-Workstream: **`DRIVE_design_tokens.json`**. Darin stehen die DRIVE-Farben, Abstände, Radien, Typo und Schatten – vom Agent aus dem Audit abgeleitet.

### Option A: Plugin „Tokens Studio for Figma“

1. In Figma: **Resources** → **Plugins** → nach **„Tokens Studio“** suchen und installieren (oder [Tokens Studio for Figma](https://www.figma.com/community/plugin/843461159747178978)).
2. Plugin starten → **Import** → **From file** (oder Paste) → **`DRIVE_design_tokens.json`** auswählen bzw. Inhalt einfügen.
3. Tokens werden als Figma-Variables (oder Plugin-Variablen) angelegt. Danach kannst du in Figma diese Werte beim Zeichnen von Rechtecken, Text, Frames nutzen (über Variables / lokale Styles).

### Option B: Ohne Plugin (manuell, aber wenig Aufwand)

1. In Figma: Rechte Seite **Design** → **Local variables** (oder **Variables**).
2. Neue **Variable collection** anlegen, z. B. „DRIVE“.
3. **Farben:** Aus `DRIVE_design_tokens.json` die Werte unter `drive.color` abtippen oder copy-pasten (z. B. `primary` = #6B7FDB, `background` = #f8f9fa, …).
4. **Zahlen** (Spacing, Radius, Font-Size) optional als Number-Variables anlegen.

Der Agent hat die Werte schon festgelegt – du überträgst sie nur einmal.

---

## 3. Wenn du „Screens“ oder Mockups brauchst

Du musst keine Layouts erfinden. Du kannst den Agent bitten:

- **Fertiges Mockup:** Es gibt bereits **`MOCKUP_Rechteverwaltung_3Tabs.html`** im Design-Ordner. Im Browser öffnen (Doppelklick oder `Datei → Öffnen`). Du kannst es als Vorlage in Figma nutzen (Screenshot als Hintergrund, dann Frames/Shapes drüber) oder als Spez an einen Designer geben.

- **„Beschreibe genau das Layout der Rechteverwaltung für Figma: Abstände, Reihenfolge der Blöcke, Tab-Struktur.“**  
  → Du bekommst eine textuelle Spez, die du (oder jemand) in Figma umsetzt – ohne eigene Design-Entscheidungen.

- **„Liste die genauen Farben und Schriftgrößen für die Rechteverwaltung-Header und die User-Tabelle.“**  
  → Du trägst sie in Figma ein oder nutzt die Token-Datei.

Figma ist dann das **Werkzeug**, in dem das Ergebnis liegt und geteilt wird – die **Entscheidungen** kommen aus dem Audit und vom Agent.

---

## 4. Kurz: Was du in Figma tust

| Aufgabe | Wer macht was |
|--------|----------------|
| Farben, Abstände, Typo definieren | **Agent** (steht in `DRIVE_design_tokens.json` und im Audit) |
| Tokens in Figma anlegen | **Du** (einmalig: Plugin-Import oder Variables manuell aus der JSON) |
| Screens/Layouts entwerfen | **Agent** (HTML-Mockup oder detaillierte Beschreibung); du übernimmst in Figma oder gibst die Spez weiter |
| Frames in Figma bauen | **Du** (oder Designer), anhand der Agent-Vorlagen und Tokens |
| Mit Team/Stakeholdern abstimmen | **Du** (Figma-Links, Kommentare, Export) |

---

## 5. Nächster Schritt

- **Jetzt:** `DRIVE_design_tokens.json` in Figma importieren (Tokens Studio oder Variables manuell).
- **Dann:** Im Chat z. B. sagen: *„Erstelle ein HTML-Mockup für die Rechteverwaltung mit 3 Tabs (User & Rollen, Mitarbeiter & Urlaub, Einstellungen) nach dem Design-Audit.“*  
  → Du nutzt das Mockup als Vorlage in Figma oder zum Abgleichen mit dem Agent.

So nutzt du Figma als Design-Tool **mit** Agent-Unterstützung, ohne selbst Designer zu sein.
