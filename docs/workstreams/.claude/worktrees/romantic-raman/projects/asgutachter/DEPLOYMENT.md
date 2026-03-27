# Deployment-Anleitung: AS Gutachter Website

## Automatisiertes Deployment mit Playwright

### Voraussetzungen

1. **Node.js installiert** (Version 14+)
2. **Playwright installiert**

### Installation

```bash
cd projects/asgutachter
npm install
npx playwright install chromium
```

### Verwendung

#### Option 1: Playwright (Empfohlen für komplexe Updates)

```bash
npm run deploy
# oder
node update_wp_playwright.js
```

**Vorteile:**
- ✅ Visuelles Feedback (Browser sichtbar)
- ✅ Screenshots für Debugging
- ✅ Funktioniert auch bei komplexen Gutenberg-Editoren
- ✅ Automatisches Login
- ✅ Fehlerbehandlung

**Nachteile:**
- ⚠️ Benötigt Node.js und Playwright
- ⚠️ Langsamer als REST API

#### Option 2: PowerShell REST API (Schnell)

```powershell
powershell -ExecutionPolicy Bypass -File update_wp_page.ps1
```

**Vorteile:**
- ✅ Sehr schnell
- ✅ Keine Browser-Abhängigkeit
- ✅ Funktioniert überall wo PowerShell läuft

**Nachteile:**
- ⚠️ Benötigt Application Password in WordPress
- ⚠️ Weniger visuelles Feedback

---

## WordPress-Zugangsdaten

- **URL:** http://neu.asgutachter.de/wp-admin
- **Benutzername:** asgutachter_admin
- **Passwort:** AS!Gutachter2025#Neu
- **Page ID:** 7 (Startseite)

---

## Troubleshooting

### Playwright: "Browser nicht gefunden"
```bash
npx playwright install chromium
```

### Playwright: "Login fehlgeschlagen"
- Prüfe Benutzername/Passwort
- Prüfe ob WordPress erreichbar ist
- Screenshots in `screenshot_*.png` ansehen

### REST API: "401 Unauthorized"
- Application Password in WordPress erstellen
- Passwort in `update_wp_page.ps1` aktualisieren

### REST API: "404 Not Found"
- Prüfe Page ID (aktuell: 7)
- Prüfe WordPress REST API ist aktiviert

---

## Dateien

- `update_wp_playwright.js` - Playwright Deployment Script
- `update_wp_page.ps1` - PowerShell REST API Script
- `content/startseite_v4_mockup.html` - HTML Content

---

*Erstellt: 2025-12-29*







