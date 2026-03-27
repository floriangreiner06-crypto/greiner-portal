# Entwicklungs-Log: AS Gutachter Website (asgutachter.de)

**Kunde:** Alexander Ströher (AS Gutachter)  
**Website:** www.asgutachter.de  
**Projektstart:** 2025-12-29 (TAG 145)  
**Status:** In Entwicklung

---

## 📋 Projekt-Übersicht

### Zielsetzung
Entwicklung einer modernen, conversion-optimierten Website für den KFZ-Gutachter Alexander Ströher mit Fokus auf Lead-Generierung und lokales SEO.

### Hauptziele
1. ✅ Analyse des IST-Zustands der bestehenden Website
2. ✅ Entwicklung einer Lead-Generation Strategie
3. ✅ Erstellung von Homepage-Mockups
4. ✅ Setup der Staging-Umgebung auf Strato
5. 🔄 Implementierung in WordPress (in Arbeit)
6. ⏳ Go-Live (ausstehend)

---

## 📅 Entwicklungs-Chronologie

### TAG 145 (2025-12-29) - Projektstart

#### Phase 1: Analyse & Strategie
- **IST-Analyse der bestehenden Website durchgeführt**
  - Stärken identifiziert: Breites Leistungsspektrum, regionaler Fokus, professionelles Erscheinungsbild
  - Schwächen identifiziert:
    - 🔴 Kein Lead-Capture-Formular auf Homepage
    - 🔴 Telefonnummer nicht prominent
    - 🟠 Keine Google-Bewertungen sichtbar
    - 🟠 Kein "Jetzt anrufen" CTA-Button
    - 🟡 Keine Reaktionszeit-Garantie
    - 🟡 Kein FAQ-Bereich

- **Benchmark-Analyse der Konkurrenten**
  - Gutachterix.de analysiert (Marktführer)
  - Caring KFZ-Gutachter München analysiert
  - MEISTERWERK Gutachten analysiert
  - Best Practices identifiziert

- **Lead-Generation Plan erstellt**
  - Dokument: `docs/KFZ_GUTACHTER_LEADGEN_PLAN.md`
  - Quick Wins definiert
  - Software-Tools ausgewählt (HubSpot, Tidio, Calendly, etc.)
  - Content-Strategie für lokales SEO
  - Google Ads Strategie
  - Automatisierungs-Workflows
  - ROI-Rechnung: 380% bei empfohlener Variante

#### Phase 2: Design & Mockups
- **Corporate Identity definiert**
  - Farben:
    - Primary Blue: #1a4d7c
    - Gold/Accent: #c9a227
    - Dark Blue: #0d2840
    - Light Gray: #f8f9fa
  - Typografie: System Sans-Serif (Segoe UI, Roboto)
  - Logo-Varianten benötigt: Hell/Dunkel, mit/ohne Slogan

- **Homepage Mockup v2 erstellt**
  - Datei: `mockups/asgutachter_homepage_v2.html`
  - Hero-Section mit prominentem CTA
  - Lead-Capture-Formular
  - Service-Cards
  - Trust-Signale
  - Testimonials-Bereich
  - Mobile-optimiert

- **Weitere Mockup-Varianten**
  - `content/startseite_v2.html`
  - `content/startseite_v3_ultra_compact.html`
  - `content/startseite_v4_mockup.html`

#### Phase 3: Technische Vorbereitung
- **Strato Account analysiert**
  - Paket: STRATO Hosting Ultimate (30 EUR/Monat)
  - Kundennummer: 12004202
  - Auftragsnummer: 1358056
  - PHP-Version: 8.3 (8.4 empfohlen)
  - Datenbanken: 1/100 verwendet
  - Subdomains: 2/2500 verwendet

- **Staging-Umgebung eingerichtet**
  - URL: http://neu.asgutachter.de
  - WP-Admin: http://neu.asgutachter.de/wp-admin
  - Benutzername: asgutachter_admin
  - Passwort: AS!Gutachter2025#Neu
  - E-Mail: asgutachter.de@gmail.com
  - Datenbank: dbs15120362
  - DB-User: dbu5040836
  - Installationsverzeichnis: STRATO-apps/wordpress_01/app

- **Dokumentation erstellt**
  - `README.md` - Projekt-Übersicht und Status
  - `STRATO_SETUP.md` - Anleitung für Strato-Setup
  - `docs/KFZ_GUTACHTER_LEADGEN_PLAN.md` - Lead-Generation Strategie

#### Phase 4: Assets & Code
- **Custom CSS erstellt**
  - Datei: `css/custom.css`
  - CI-Farben als CSS-Variablen
  - Responsive Design
  - Button-Styles
  - Hero-Section
  - CTA-Box
  - Service-Cards
  - Trust-Section
  - Testimonials
  - Footer
  - Contact-Strip (sticky bottom für Mobile)
  - Chat-Widget Platzhalter
  - Form-Styles (Contact Form 7 / WPForms)
  - Print-Styles

- **Custom JavaScript erstellt**
  - Datei: `js/custom.js`
  - Sticky Header
  - Smooth Scroll
  - Phone Click Tracking (für Analytics)
  - Form Tracking (Google Analytics Events)
  - Chat Widget Integration (Tidio/WhatsApp Fallback)
  - Mobile Menu
  - Lazy Load Images (optional)
  - Scroll Animations (optional)
  - Cookie Consent Check (DSGVO)

- **Logo-Varianten erstellt**
  - `assets/logo_icon.svg`
  - `assets/logo_modern_white.svg`
  - `assets/logo_modern.svg`
  - `assets/logo_v2_checkmark.svg`
  - `assets/logo_v3_magnifier.svg`
  - `assets/logo_v4_shield.svg`
  - `assets/logo_v5_document.svg`
  - `assets/logo_v6_minimal.svg`
  - `assets/logo.jpg`
  - `assets/logo_preview.html`

---

## 📁 Projektstruktur

```
projects/asgutachter/
├── README.md                    # Projekt-Übersicht und Status
├── STRATO_SETUP.md              # Anleitung für Strato-Setup
├── ENTWICKLUNGS_LOG.md          # Diese Datei (Entwicklungs-Chronologie)
├── assets/                      # Bilder, Logo, Icons
│   ├── logo_*.svg               # Logo-Varianten
│   └── logo.jpg                 # Original-Logo
├── css/
│   └── custom.css               # CI-Stylesheet (fertig)
├── js/
│   └── custom.js                # Tracking, Chat-Widget (fertig)
├── mockups/
│   └── asgutachter_homepage_v2.html  # Haupt-Mockup
├── content/
│   ├── startseite_v2.html
│   ├── startseite_v3_ultra_compact.html
│   └── startseite_v4_mockup.html
├── inject_header_css.php        # PHP für WordPress Header-Injection
├── update_wp_page.ps1           # PowerShell-Script für WordPress-Update
└── wordpress/                   # WordPress Theme Files (später)
```

---

## 🎯 Nächste Schritte (TODO)

### Implementierung (aktuell in Arbeit)
- [ ] Theme auswählen (GeneratePress/Astra empfohlen)
- [ ] Custom CSS in WordPress einspielen
- [ ] Custom JavaScript in WordPress einspielen
- [ ] Kontaktformular einrichten (Contact Form 7)
- [ ] Seiten erstellen nach Mockup
- [ ] SSL aktivieren für Staging
- [ ] Testen aller Funktionen

### Quick Wins (nach Theme-Setup)
- [ ] Kontaktformular auf Homepage
- [ ] Click-to-Call Button prominent platzieren
- [ ] Google-Bewertungen einbinden
- [ ] Meta-Tags optimieren
- [ ] SSL prüfen/aktivieren
- [ ] 404-Fehler auf Kontaktseite fixen

### Go-Live Vorbereitung
- [ ] Alle Formulare getestet
- [ ] Mobile-Ansicht geprüft
- [ ] SSL funktioniert (https://)
- [ ] 404-Seiten gefixt
- [ ] Meta-Tags gesetzt
- [ ] Google Search Console verbunden
- [ ] Favicon aktualisiert
- [ ] Impressum & Datenschutz aktuell
- [ ] Cookie-Banner funktioniert
- [ ] Backup der alten Seite gespeichert

### Phase 1: Foundation (Woche 1-2)
- [ ] HubSpot Free Account einrichten
- [ ] Lead-Formular auf Website integrieren
- [ ] Google My Business optimieren
- [ ] WhatsApp Business einrichten
- [ ] Calendly für Terminbuchung

### Phase 2: Automation (Woche 3-4)
- [ ] Tidio Chatbot installieren
- [ ] Make.com Workflows bauen
- [ ] Auto-E-Mails für Bewertungsanfragen
- [ ] SMS-Benachrichtigung bei neuen Leads

### Phase 3: Content & SEO (Monat 2)
- [ ] 5 Stadt-Landing-Pages erstellen
- [ ] 3 Blog-Artikel schreiben
- [ ] Google Ads Testkampagne starten (300€ Budget)
- [ ] Verzeichnis-Einträge anlegen

### Phase 4: Skalierung (Monat 3+)
- [ ] Google Ads optimieren
- [ ] Weitere Landing Pages
- [ ] Video-Testimonials sammeln
- [ ] Empfehlungsprogramm starten

---

## 🔧 Technische Details

### Hosting
- **Provider:** Strato
- **Paket:** STRATO Hosting Ultimate
- **Kosten:** 30 EUR/Monat
- **PHP-Version:** 8.3 (8.4 empfohlen)

### Staging
- **URL:** http://neu.asgutachter.de
- **WordPress Admin:** http://neu.asgutachter.de/wp-admin
- **Datenbank:** dbs15120362

### Domains (18 aktiv)
- **Haupt-Domains:**
  - asgutachter.de (Hauptseite)
  - asgutachter.com
  - alexanderströher.de
  - gutachter-deggendorf.de
  - kfzgutachterdeggendorf.de
  - unfallgutachten-deggendorf.de
- **Spezial-Domains:**
  - ebikegutachten.de/at/com
  - mtbgutachten.de
  - motorradbewertung.com

---

## 📊 Lead-Generation Strategie

### Software-Tools (empfohlen)
- **CRM:** HubSpot Free (0€)
- **Chat:** Tidio (0€ Free Tier)
- **Terminbuchung:** Calendly (0€ Free)
- **Bewertungen:** Grade.us (25$/Mo) oder Google Review Link Generator (0€)
- **Automation:** Make.com (9€/Mo)
- **Werbung:** Google Ads (450€/Mo empfohlen)

### ROI-Rechnung
- Durchschnittlicher Gutachten-Auftrag: ~300€
- Bei 15 Leads/Monat und 50% Abschlussrate: 7-8 Aufträge
- Umsatz: ~2.400€
- Kosten: ~500€
- **ROI: 380%**

---

## 📝 Wichtige Kontakte

- **Alex (Inhaber):** Kontakt über User
- **Strato Support:** 030 300 146 0

---

## 📚 Referenz-Dateien

- Lead-Gen Plan: `docs/KFZ_GUTACHTER_LEADGEN_PLAN.md`
- Homepage Mockup: `mockups/asgutachter_homepage_v2.html`
- Strato Setup: `STRATO_SETUP.md`
- Projekt-README: `README.md`

---

## 🔄 Änderungsprotokoll

### 2025-12-29 (TAG 145)
- Projekt gestartet
- IST-Analyse durchgeführt
- Lead-Generation Plan erstellt
- Mockups erstellt
- Staging-Umgebung eingerichtet
- Custom CSS und JavaScript erstellt
- Logo-Varianten erstellt

---

*Dieses Entwicklungs-Log wird kontinuierlich aktualisiert.*







