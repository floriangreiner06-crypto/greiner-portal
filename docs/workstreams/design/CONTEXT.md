# Design & Redesign — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-03-13

## Beschreibung

Dieser Workstream bündelt **Portal-UI-Redesign**, **zentrales DRIVE-Theme** (Farben, Schriften, Startseite) und **UX der Rechteverwaltung**. Design und Mockups werden mit **Figma** erstellt; Umsetzung erfolgt in den betroffenen Modulen (Templates, CSS, ggf. Komponenten).

**Abgrenzung zu auth-ldap:** auth-ldap bleibt zuständig für Login, LDAP/AD, RBAC, Rollen-Config und fachliche Rechte-Logik. Dieser Workstream fokussiert auf **Look & Feel**, **Layout**, **Rechteverwaltung-UI** (Tabs, Pills, Lesbarkeit) und **Theme-System**. Rechte-Inhalte (welche Rolle, welche Features) werden in auth-ldap definiert; wie die Rechteverwaltung aussieht und bedient wird, gehört hierher.

## Design-Tool: Figma

- **Entscheidung (2026-03-13):** Nach Rücksprache mit Claude wird **Figma** für alle Design- und Redesign-Mockups genutzt.
- Nutzung: Rechteverwaltung-Redesign (Tabs, Feature-Zugriff, Filter inline), DRIVE-Theme (Farben, Typo, Startseite), weitere UI-Entwürfe. Abstimmung mit Stakeholdern über Figma.
- Bestehende HTML-Mockups in auth-ldap (MOCKUP_THEME_*.html etc.) bleiben als Referenz; neue Entwürfe und Freigaben laufen über Figma.

## Vorgehensweise: Figma MCP + Design-Audit (empfohlen)

Cursor hat native MCP-Unterstützung; damit ist der Ablauf ohne zusätzliche Tools nutzbar. **Installation der Tools:** siehe `ANLEITUNG_TOOLS_INSTALL.md` (Figma Desktop, Cursor MCP-Konfiguration, Checkliste).

1. **Figma MCP in Cursor einrichten** — In Cursor Settings (MCP) den Figma-MCP aktivieren (einmalig, ca. 5 Min.). Danach können Figma-Dateien/Projekte aus Cursor angebunden werden.
2. **DRIVE im Browser öffnen** — Bestehendes Portal unter `http://drive` (oder localhost/Server-IP) im Browser öffnen, Seite die auditiert werden soll anzeigen (z. B. Startseite, Rechteverwaltung).
3. **Design-Audit aus Cursor** — In Cursor z. B. anfragen: *„Analysiere diese laufende Seite und erstelle einen Design-Audit.“* Der Agent kann die UI (z. B. per Browser-MCP) erfassen und **Farben, Schriften, Inkonsistenzen** auswerten und dokumentieren.
4. **Optional: Vergleich mit Mockup** — Gegen das Startseiten- oder Rechteverwaltungs-Mockup vergleichen lassen; Abweichungen und Verbesserungsvorschläge festhalten.

Ergebnis: belastbare Basis für Figma-Entwürfe und spätere Umsetzung (Theme, Rechteverwaltung-UI).

## Geplantes Redesign (Rechteverwaltung)

Vorschläge aus auth-ldap, Umsetzung/UI-Detailierung hier:

- **Vorschlag B:** Nur Sicht „Nach Rolle“ bearbeitbar; „Nach Feature“ und „Matrix“ nur Übersicht (read-only). Speichern nur aus „Nach Rolle“. Feature-Karten ohne Stift-Button.
- **Vorschlag C:** Filter-Verhalten für Listen (Auftragseingang, Auslieferungen, OPOS, Leistungsübersicht Werkstatt) **inline**: kleines Dropdown neben dem Feature-Haken in der Rollen-Ansicht; separate Karte „Filter-Verhalten für Listen“ entfällt.
- **Vorschlag D:** Haupt-Tabs auf 3 reduziert:
  - **User & Rollen** — User-Liste + Rollen & Module/Feature-Zugriff in einem Tab
  - **Mitarbeiter & Urlaub** — Pills: Mitarbeiter-Konfig, Urlaubsverwaltung, Mitarbeiterverwaltung
  - **Einstellungen** — Pills: Navigation, Title-Mapping, E-Mail Reports, Architektur

Erst in Figma ausarbeiten, dann mit auth-ldap abgleichen (API/Features unverändert), danach Umsetzung in Templates/JS.

## Theme & DRIVE-Erscheinungsbild

- Zentrales Theme: Farben, Schriften, Startseite, ggf. Badges pro Rolle.
- Alte Referenz-Docs liegen in auth-ldap (MOCKUP_THEME_*.html, EINSCHAETZUNG_DRIVE_DESIGN_ANPASSUNG.md, README_THEME_MOCKUPS.md); können bei Bedarf hierher verlinkt oder verschoben werden.
- Figma als zentrale Quelle für verbindliche Design-Entscheidungen.

## Module & Dateien (betroffen bei Umsetzung)

### Templates
- `templates/admin/rechte_verwaltung*.html` — Rechteverwaltung (Hauptziel Redesign)
- `templates/base.html` — Layout, Navi-Container, Theme-Basis
- Weitere Admin-/Dashboard-Templates je nach Theme-Rollout

### Static
- `static/css/` — Theme-Variablen, überarbeitete Komponenten

### Doku (dieser Workstream)
- `ANLEITUNG_TOOLS_INSTALL.md` — Installation: Figma Desktop, Figma MCP in Cursor, Browser/Playwright MCP, Checkliste
- `DESIGN_AUDIT_DRIVE.md` — Design-Audit aus Code (ohne MCP): Farben, Typo, Inkonsistenzen, Empfehlungen für Figma
- `FIGMA_FUER_NICHT_DESIGNER.md` — Figma mit Agent-Unterstützung nutzen (Rolle User vs. Agent, Tokens importieren, Mockups anfordern)
- `DRIVE_design_tokens.json` — Importierbare Design-Tokens (Farben, Spacing, Radius, Typo, Schatten) für Figma (z. B. Tokens Studio Plugin)
- `MOCKUP_Rechteverwaltung_3Tabs.html` — Klickbares HTML-Mockup (3 Tabs, User & Rollen mit inline-Filter, Pills für Mitarbeiter/Einstellungen); im Browser öffnen, als Vorlage für Figma nutzen

### Referenz (auth-ldap)
- `docs/workstreams/auth-ldap/VORSCHLAG_RECHTEVERWALTUNG_VEREINFACHUNG.md`
- `docs/workstreams/auth-ldap/MOCKUP_THEME_*.html`, `EINSCHAETZUNG_DRIVE_DESIGN_ANPASSUNG.md`, `README_THEME_MOCKUPS.md`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Workstream angelegt, Figma als Tool festgelegt (2026-03-13)
- ✅ **Design-Audit ohne MCP** erstellt (2026-03-13): `DESIGN_AUDIT_DRIVE.md` – Farben, Typo, Inkonsistenzen, Empfehlungen für Figma; Basis für Theme und Redesign.
- ❌ Figma-Projekt/Dateien anlegen und Rechteverwaltung-Redesign (B/C/D) skizzieren
- ❌ DRIVE-Theme in Figma definieren (Farben, Typo, Startseite) – Audit als Referenz nutzen
- ❌ Umsetzung Redesign in `rechte_verwaltung*.html` nach Figma-Freigabe
- ❌ Theme-Umsetzung im Portal (CSS/Templates) nach Freigabe

## Nächster Schritt

- **Design-Audit liegt vor:** `DESIGN_AUDIT_DRIVE.md` (ohne MCP, aus Code erstellt). Als Basis für Figma nutzen.
- **Danach:** Figma-Projekt für DRIVE anlegen; Farb-/Typo-Tokens und erste Frames für Rechteverwaltung (3 Tabs, „Nach Rolle“ mit inline-Filter) und Theme-Styleguide erstellen. Mit auth-ldap abgleichen und Umsetzung planen.

## Abhängigkeiten

- **auth-ldap:** Rollen, Features, API für Rechteverwaltung unverändert; nur UI/Layout werden hier geändert. Enge Abstimmung bei Rechteverwaltung-Änderungen.
- **CLAUDE.md / .cursorrules:** Workstream „design“ beim Arbeiten am Redesign/Theme laden.
