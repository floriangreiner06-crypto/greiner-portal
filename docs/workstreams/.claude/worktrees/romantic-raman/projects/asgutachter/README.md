# AS Gutachter Website Redesign

**Kunde:** Alexander Ströher (AS Gutachter)
**Website:** www.asgutachter.de
**Hosting:** Strato (Kundennummer: 12004202)

---

## Projekt-Status

| Phase | Status |
|-------|--------|
| Analyse IST-Zustand | Fertig |
| Lead-Gen Strategie | Fertig |
| Homepage Mockup | Fertig |
| Strato-Zugang | Fertig |
| Staging-Setup | Fertig |
| Implementierung | In Arbeit |
| Go-Live | Ausstehend |

---

## Strato Account Details

| Eigenschaft | Wert |
|-------------|------|
| **Paket** | STRATO Hosting Ultimate |
| **Preis** | 30 EUR/Monat |
| **Kundennummer** | 12004202 |
| **Auftragsnummer** | 1358056 |
| **PHP-Version** | 8.3 (8.4 empfohlen) |
| **Datenbanken** | 1/100 verwendet |
| **Subdomains** | 2/2500 verwendet |

---

## Staging-Umgebung (NEU!)

| Eigenschaft | Wert |
|-------------|------|
| **URL** | http://neu.asgutachter.de |
| **WP-Admin** | http://neu.asgutachter.de/wp-admin |
| **Benutzername** | asgutachter_admin |
| **Passwort** | AS!Gutachter2025#Neu |
| **E-Mail** | asgutachter.de@gmail.com |
| **Datenbank** | dbs15120362 |
| **DB-User** | dbu5040836 |
| **Installationsverzeichnis** | STRATO-apps/wordpress_01/app |

---

## Projektstruktur

```
asgutachter/
├── README.md           # Diese Datei
├── STRATO_SETUP.md     # Anleitung für Strato-Setup
├── assets/             # Bilder, Logo, Icons
├── css/
│   └── custom.css      # CI-Stylesheet (fertig)
├── js/
│   └── custom.js       # Tracking, Chat-Widget (fertig)
├── mockups/
│   └── asgutachter_homepage_v2.html
└── wordpress/          # WordPress Theme Files (später)
```

---

## CI / Corporate Identity

### Farben
| Name | Hex | Verwendung |
|------|-----|------------|
| Primary Blue | #1a4d7c | Headlines, Buttons, Links |
| Gold/Accent | #c9a227 | CTAs, Highlights, Hover |
| Dark Blue | #0d2840 | Footer, Dark Sections |
| Light Gray | #f8f9fa | Backgrounds |
| White | #ffffff | Text auf dunklem Hintergrund |

### Typografie
- **Headlines:** System Sans-Serif (Segoe UI, Roboto)
- **Body:** System Sans-Serif
- **Font-Weight:** 700 für Headlines, 400 für Body

### Logo
- Aktuelles Logo: Goldene Schrift auf dunklem Grund
- Varianten benötigt: Hell/Dunkel, mit/ohne Slogan

---

## Domains (18 aktiv)

Haupt-Domains:
- **asgutachter.de** - Hauptseite
- asgutachter.com
- alexanderströher.de
- gutachter-deggendorf.de
- kfzgutachterdeggendorf.de
- unfallgutachten-deggendorf.de

Spezial-Domains:
- ebikegutachten.de/at/com
- mtbgutachten.de
- motorradbewertung.com

---

## Wichtige Kontakte

- **Alex (Inhaber):** Kontakt über User
- **Strato Support:** 030 300 146 0

---

## Referenz-Dateien

- Lead-Gen Plan: `../../docs/KFZ_GUTACHTER_LEADGEN_PLAN.md`
- Homepage Mockup: `../../docs/mockups/asgutachter_homepage_v2.html`
- Mockup (lokal): `mockups/asgutachter_homepage_v2.html`

---

## Naechste Schritte

1. [x] Strato-Zugang pruefen
2. [x] Subdomain neu.asgutachter.de anlegen
3. [x] WordPress installieren
4. [ ] Theme auswaehlen (GeneratePress/Astra empfohlen)
5. [ ] Custom CSS einspielen
6. [ ] Kontaktformular einrichten (Contact Form 7)
7. [ ] Seiten erstellen nach Mockup
8. [ ] SSL aktivieren fuer Staging
9. [ ] Testen
10. [ ] Go-Live (Verzeichnisse tauschen)

---

## Quick Wins (nach Theme-Setup)

1. [ ] Kontaktformular auf Homepage
2. [ ] Click-to-Call Button prominent
3. [ ] Google-Bewertungen einbinden
4. [ ] Meta-Tags optimieren
5. [ ] SSL pruefen/aktivieren
6. [ ] 404-Fehler auf Kontaktseite fixen

---

*Erstellt: 2025-12-29*
*Letzte Aktualisierung: 2025-12-29 - Staging eingerichtet*
