# Einschätzung: DRIVE am Mockup-Design-Stil ausrichten

**Frage:** Wie aufwendig ist es, das gesamte DRIVE-Portal (nicht nur Startseite) an den Design-Stil des Startseiten-Mockups anzupassen – alle Farben, Grafiken und Schriften nach dem gleichen Schema?  
**Basis:** Mockup „Ultimative Startseite“ (DM Sans, #1e3a5f, neutrale Grautöne, klare Karten, nicht verspielt).

---

## 1. Aktueller Zustand (Kurz)

| Bereich | Befund |
|--------|--------|
| **Basis-Layout** | `base.html` lädt Bootstrap 5.3 + **nur** `navbar.css`. Kein zentrales „Theme“-CSS. |
| **Navbar** | Eigene Farbwelt in `navbar.css`: Verlauf `#6B7FDB` → `#8B9AE0` (Lila), weiße Links. |
| **Schrift** | System-Stack (`-apple-system, BlinkMacSystemFont, Segoe UI, Roboto...`), keine DM Sans. |
| **Farben** | Keine zentrale Palette: Bootstrap-Defaults (z. B. `btn-primary` = Bootstrap-Blau), Navbar übersteuert mit Lila. `static/css/style.css` definiert Variablen (--primary-color etc.), wird aber **nicht** in `base.html` eingebunden. |
| **Templates** | Ca. **163** HTML-Dateien; viele mit **eigenen** `<style>` oder `extra_css`: Gradients, Hex-Farben, teils eigene „Karten“-Styles. |
| **Statische CSS-Dateien** | 9 Dateien (navbar, dashboard, bankenspiegel, vacation_v2, hilfe, …), teils modul-spezifisch. |

**Fazit:** Es gibt **keine einzige Design-Source**. Farben und Schriften sind über Base, Navbar-CSS und viele Template-inline-Styles verteilt.

---

## 2. Aufwand – grobe Einschätzung

### Option A: Nur „Globaler Look“ (Navbar + Basis-Token)

- **Umfang:** Eine zentrale Theme-Datei (z. B. `static/css/drive-theme.css`) mit:
  - CSS Custom Properties (Farben, Schatten, Radius wie im Mockup)
  - Schrift: DM Sans (Google Font) als `font-family` für `body`
  - Bootstrap-Overrides: `--bs-primary`, `--bs-body-bg`, `--bs-body-color` etc.
- **Navbar:** `navbar.css` auf Mockup-Farben umstellen (z. B. #1e3a5f statt Lila).
- **Einbindung:** Theme in `base.html` nach Bootstrap, vor `navbar.css`.

**Aufwand:** **klein** (ca. 0,5–1 Tag).  
**Ergebnis:** Einheitliche Navbar, Buttons, Links, Hintergründe und Schrift global; viele Seiten behalten aber noch eigene Karten/Gradients in Inline-Styles (optisch „gemischt“, aber erkennbar ein Stil).

---

### Option B: Globaler Look + Startseite + wenige Kerntemplates

- Wie Option A, plus:
  - Startseite (`dashboard.html`) vollständig auf Mockup-Stil (Badges, Karten, Hero).
  - 3–5 stark genutzte Seiten (z. B. Urlaubsplaner, Auftragseingang, eine Controlling-Übersicht) auf Theme-Klassen/Token umgestellt.

**Aufwand:** **mittel** (ca. 2–4 Tage).  
**Ergebnis:** Klar sichtbarer neuer Stil auf Einstieg und wichtigen Seiten; Rest schrittweise nachziehbar.

---

### Option C: Durchgängige Anpassung (ganzes Portal)

- Theme wie A/B.
- **Alle** Templates durchgehen: Inline-Farben/Gradients durch Theme-Variablen oder -Klassen ersetzen; Karten/Badges vereinheitlichen.
- Modul-CSS (bankenspiegel, vacation_v2, hilfe, controlling/dashboard, …) auf gleiche Token umstellen.
- Chart.js und andere Bibliotheken: Farbpaletten auf Theme-Farben umstellen (z. B. zentrale JS-Config oder Data-Attribute).

**Aufwand:** **hoch** (ca. 1–3 Wochen, abhängig von Priorisierung und Test).  
**Ergebnis:** Durchgängig einheitlicher Look; Wartung künftig über eine Theme-Datei und wenige Ausnahmen.

---

## 3. Risiken

| Risiko | Beschreibung | Mitigation |
|--------|--------------|------------|
| **Inkonsistenz** | Nur Option A: Navbar und Buttons „neu“, viele Seiten behalten alte Karten/Farben. | Option B/C schrittweise; klare Prioritätenliste (Startseite, Top-5-Seiten). |
| **Kontrast/Barrierefreiheit** | Neue Farben (z. B. #1e3a5f für Navbar) müssen ausreichend Kontrast behalten (weißer Text). | Prüfung mit Kontrast-Checker; ggf. Navbar etwas aufhellen. |
| **Bootstrap-Overrides** | Zu starke Überschreibungen können Komponenten (Dropdowns, Modals, Alerts) ungewollt verändern. | Theme nur auf definierte Variablen beschränken; nach Einführung gezielt testen. |
| **Charts/Diagramme** | Chart.js etc. nutzen oft feste Hex-Werte in Templates/JS. | Zentrale Farbpalette (z. B. in `drive-theme.js` oder als data-Attribute) und in Charts referenzieren. |
| **Regression** | Änderungen an globalem CSS betreffen alle Seiten. | Nach Theme-Einführung: Smoke-Tests (Login, Nav, 2–3 Kerntemplates); gezielte Prüfung mobil. |
| **Drittbibliotheken** | Bootstrap 5, Bootstrap Icons, Chart.js – Updates können Defaults ändern. | Theme nach Bootstrap laden; nur notwendige Variablen überschreiben; Versions-Upgrades testen. |

---

## 4. Empfehlung

1. **Kurzfristig (Option A):** Ein zentrales **Drive-Theme** (eine CSS-Datei + Font) einführen und **nur** Navbar + Bootstrap-Basis (Primärfarbe, Body, Buttons) anpassen. Geringer Aufwand, sofort sichtbarer Effekt, keine großen Risiken.
2. **Mittelfristig (Option B):** Startseite und wenige Kerntemplates auf denselben Stil umstellen; Rest bei Gelegenheit.
3. **Langfristig (Option C):** Bei Bedarf schrittweise alle Templates und Modul-CSS auf Theme umstellen; Chart-Farben zentral konfigurieren.

**Technisch:** Theme als **einzige** Quelle für Farben und Schrift (CSS Custom Properties + Bootstrap-Overrides); keine neuen „Grafiken“ nötig, nur Farb- und Typo-Anpassungen. Icons (Bootstrap Icons) bleiben; ggf. einheitliche Icon-Farben über Theme-Klassen.

---

## 5. Kurzfassung

| Frage | Antwort |
|-------|--------|
| **Aufwand nur Startseite** | Bereits geplant (Badge-Konfiguration); Design-Anpassung der Startseite selbst ist **klein** (1 Tag), wenn Theme existiert. |
| **Aufwand ganzes Portal** | **Global (Navbar + Basis):** klein (0,5–1 Tag). **Durchgängig (alle Farben/Grafiken/Schriften):** hoch (1–3 Wochen). |
| **Risiken** | Überschaubar bei Option A/B; bei Option C: Regressionstests und Chart-Farben im Blick behalten. |
| **Sinnvoller Einstieg** | Zentrales Theme (drive-theme.css) + Navbar + Bootstrap-Token; dann Startseite; dann schrittweise Kerntemplates. |
