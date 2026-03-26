# Design-Audit DRIVE Portal (ohne MCP)

**Stand:** 2026-03-13 · Erstellt aus Codebasis (Templates, CSS). Basis für Figma-Redesign und zentrales Theme.

---

## 1. Kurzfassung

- **Primärfarbe** der App (Navi, Dashboard, Akzente) ist ein **Lila-Violett** (`#6B7FDB` → `#8B9AE0`). Daneben existieren **unterschiedliche „Primary“-Farben** in Modulen (Blau #0d6efd, #2563eb, #0056b3, #667eea), **keine einheitliche Design-Sprache**.
- **Typografie:** System-Stack überall (`-apple-system, Segoe UI, Roboto, …`), konsistent. Schriftgrößen und -gewichte variieren pro Modul.
- **Abstände & Radien:** border-radius 4px–12px, padding/margin uneinheitlich. Karten, Header und Buttons folgen keinem durchgängigen Raster.
- **Empfehlung:** In Figma ein **zentrales Theme** mit Farben, Typo und Spacing definieren; Rechteverwaltung und Startseite als erste Anwendung; danach schrittweise Module angleichen.

---

## 2. Farben (aktuell)

### 2.1 Haupt-Navigation & globale Akzente

| Verwendung        | Farbe(n) | Datei / Kontext        |
|-------------------|----------|-------------------------|
| Navbar            | `#6B7FDB` → `#8B9AE0` (Gradient 135deg) | `navbar.css` |
| Navbar Hover      | `rgba(255,255,255,0.12)` / `0.18` (active) | `navbar.css` |
| Body-Hintergrund  | `#f8f9fa` | `navbar.css`, viele Module |
| Footer            | `#f8f9fa`, Border `#e0e0e0` | `navbar.css` |
| Dropdown Hover    | Gradient wie Navbar | `navbar.css` |
| User-Dropdown Text | `#2d3748`, `#718096` | `navbar.css` |
| Logout Hover      | `#dc3545` | `navbar.css` |

### 2.2 Dashboard & Willkommensbereich

| Verwendung     | Farbe(n) | Datei |
|----------------|----------|--------|
| Container BG   | `#f5f7fa` → `#e8ecf1` (Gradient) | `dashboard.css` |
| Welcome-Header | `#6B7FDB` → `#8B9AE0` (wie Navbar) | `dashboard.css` |
| User-Name Akzent | `#FFD93D` (Gelb) | `dashboard.css` |
| KPI-Titel      | `#2d3748` | `dashboard.css` |
| KPI-Beschreibung | `#718096` | `dashboard.css` |
| Section-Titel Border | `#6B7FDB` | `dashboard.css` |

### 2.3 Rechteverwaltung (inline in Template)

| Verwendung     | Farbe(n) | Kontext |
|----------------|----------|---------|
| Page-Header    | `#0f172a` → `#1e293b` (dunkel) | `.rechte-header` |
| Card-Header Admin | `#667eea` → `#764ba2` (Lila-Purple) | `.card-header-admin` |
| Info-Banner   | `#eff6ff` → `#f0fdf4`, Border `#bfdbfe` | `.rechte-info-banner` |
| Stat OK       | `#059669` | `.stat-ok` |
| Stat Warn     | `#dc2626` | `.stat-warn` |
| Role-Badges   | Viele Einzelfarben (admin #dc2626, buchhaltung #2563eb, …) | siehe Template |

### 2.4 Weitere Module (Auszug)

| Modul / Datei   | Primary / Akzent | Hinweis |
|------------------|------------------|--------|
| `style.css` (:root) | `#2563eb`, hover `#1d4ed8` | Anderes Blau als Navbar |
| `bankenspiegel.css` | `--bs-primary: #0d6efd` | Bootstrap-Standard-Blau |
| `vacation_v2.css`   | `#0056b3` | Eigenes Blau |
| `controlling/dashboard.css` | `#667eea` → `#764ba2` | Wie Rechteverwaltung Card-Header |
| `einkaufsfinanzierung.css` | `#0d6efd`, `#e83e8c` (Pink) | Gemischt |

### 2.5 Inkonsistenzen (Farben)

- **„Primary“ ist nicht definiert:** Navbar = Lila (#6B7FDB), style.css = Blau (#2563eb), Bankenspiegel = Bootstrap-Blau (#0d6efd), Urlaub = #0056b3, Rechteverwaltung = Lila-Purple (#667eea/#764ba2). Keine gemeinsame Primärfarbe.
- **Grautöne:** teils `#f8f9fa`, `#e9ecef`, `#6c757d`, teils `#f8fafc`, `#64748b`, `#2d3748`, `#718096` – kein einheitliches Grau-Set.
- **Erfolg/Warnung/Fehler:** teils Bootstrap (`#198754`, `#ffc107`, `#dc3545`), teils Tailwind-ähnlich (`#059669`, `#dc2626`). Sollte in Figma einmal festgelegt werden.

---

## 3. Typografie

- **Font-Stack (global):** `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` (navbar.css, style.css, body).
- **Gewichte:** 400, 500, 600, 700, 800 je nach Modul (z. B. Titel 600–800, Fließtext 400–500).
- **Größen:** font-size von 0.65rem (Rechteverwaltung Badges) bis 2rem (Dashboard Welcome). Kein klares Type-Scale (z. B. 0.75 / 0.875 / 1 / 1.25 / 1.5 / 2).
- **Empfehlung:** In Figma ein Type-Scale (z. B. 12–16–20–24–32px) und feste Gewichte (Regular, Medium, Semibold, Bold) definieren.

---

## 4. Abstände, Radien, Schatten

- **border-radius:** 4px, 6px, 8px, 10px, 12px, 0.25rem–0.5rem – uneinheitlich. Navbar-Links 6px, Dropdown 8px, Karten 10px, Rechteverwaltung 0.5rem.
- **Schatten:** box-shadow teils `0 2px 4px rgba(0,0,0,0.08)`, teils `0 4px 12px rgba(0,0,0,0.12)`, teils `0 2px 8px rgba(0,0,0,0.06)` – kein klares Elevation-System.
- **Padding:** Karten 1rem–2.5rem, Buttons 0.5rem–1rem, Header 1.25rem–1.75rem – kein 4/8px-Raster durchgängig.
- **Empfehlung:** In Figma Spacing (4/8/16/24/32) und 2–3 Radien (z. B. 6px, 10px), plus 2–3 Schatten-Stufen definieren.

---

## 5. Komponenten (Überblick)

- **Navbar:** Bootstrap 5 `.navbar`, eigenes Gradient-Overwrite, sticky, Dropdowns mit eigenem Styling.
- **Karten:** Bootstrap `.card`, teils mit eigenem Header-Gradient (Rechteverwaltung, Controlling).
- **Buttons:** Bootstrap `.btn-primary`, `.btn-secondary`, teils mit `!important` Overrides in Modulen.
- **Badges:** Role-Badges in Rechteverwaltung mit vielen Einzelfarben; sonst Bootstrap-Badges.
- **Tabellen:** Bootstrap-Tables, teils mit sticky Header (Rechteverwaltung), eigene Hover-Farben.

---

## 6. Empfehlungen für Figma & Redesign

1. **Design-Tokens in Figma anlegen**
   - **Primärfarbe:** Eine festlegen (z. B. das bestehende Lila `#6B7FDB` als DRIVE-Brand oder ein neues Blau).
   - **Sekundär, Neutral, Success/Warning/Error:** Einmal definieren, in allen Screens nutzen.
   - **Typo:** Ein Type-Scale (Mindestgrößen für Barrierefreiheit), 2–3 Gewichte.
   - **Spacing & Radien:** Raster (z. B. 4/8/16/24/32) und 2–3 Radien.

2. **Rechteverwaltung als Pilot**
   - Redesign (3 Tabs, „Nach Rolle“ bearbeitbar, Filter inline) in Figma umsetzen; Farben/Typo aus den neuen Tokens.
   - Danach Umsetzung in `rechte_verwaltung.html` + CSS.

3. **Schrittweise Vereinheitlichung**
   - Navbar und Dashboard behalten aktuell das Lila – entweder als verbindliches DRIVE-Theme übernehmen oder bewusst wechseln und alle Stellen anpassen.
   - Module (Bankenspiegel, Urlaub, Einkaufsfinanzierung, Controlling) schrittweise auf die zentralen Tokens umstellen (CSS-Variablen in base oder gemeinsames Theme-CSS).

4. **Dokumentation**
   - In Figma ein Styleguide-Frame pflegen (Farben, Typo, Abstände, Beispiel-Komponenten), damit alle Beteiligten dieselbe Quelle nutzen.

---

## 7. Wichtige Dateien (Referenz)

| Bereich      | Datei(en) |
|-------------|-----------|
| Basis       | `templates/base.html`, `static/css/navbar.css` |
| Dashboard   | `static/css/dashboard.css` |
| Rechteverwaltung | `templates/admin/rechte_verwaltung.html` (viel Inline-`<style>`) |
| Bankenspiegel | `static/css/bankenspiegel.css` |
| Urlaub      | `static/css/vacation_v2.css` |
| Global/Verschiedenes | `static/css/style.css` |
| Controlling | `static/css/controlling/dashboard.css` |

---

## 8. Nächste Schritte

- In Figma: Farb- und Typo-Tokens + Spacing/Radien anlegen.
- Rechteverwaltung-Redesign (Vorschläge B/C/D aus CONTEXT.md) in Figma skizzieren und mit diesem Audit abgleichen.
- Nach Freigabe: Umsetzung im Portal (CSS-Variablen, Bereinigung doppelter Farben).
