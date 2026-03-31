# Vergütung & Prämien — Arbeitskontext
## Status: Aktiv
## Letzte Aktualisierung: 2026-03-30
## Beschreibung
Zentrales Modul für alle leistungsbasierten Vergütungskomponenten:
Werkstatt-Prämien (TEK-KPIs), Verkäufer-Provisionen (Locosoft/Deckungsbeitrag),
und Jahresprämie (Migration aus HR). Einheitliche Berechnung, Konfiguration und Abrechnung.

## Geplante Module
### 1. Werkstatt-Prämien (als erstes umsetzen)
- 3 KPIs: Produktivität, Leistungsgrad, Effektivität
- Stufen-Prämien (Mechaniker: 50/100/150€, Azubis: 25/50/75€)
- Monatliche Team-Berechnung
- Datenquelle: werkstatt DB (times, orders, labours, absence_calendar)

### 2. Verkäufer-Provisionen (Phase 1+2 live, Workflow live)
- Live-Preview, Vorlauf, Dashboard, Vorlauf-Detail
- Kategorien I–IV mit Bemessungsgrundlage, Min/Max-Grenzen
- Neuwagen-Klassifizierung über dealer_vehicle_type (N=NW, T/V=TW, D/G=GW)
- Endlauf-Workflow (GENEHMIGT → ENDLAUF), Belegnummer VK{id}-{YYYY}-{MM}
- PDF-Generierung (ReportLab) mit Deckblatt + Detail + Jahresübersicht
- Position bearbeiten/löschen mit Min/Max-Clamping aus provision_config
- Detail-Redesign (Accordion, Edit-Modal mit Berechnungszeile, Einkäufer-Umzuweisung)
- Zusatzleistungen (Kat. V) CRUD mit Modal (Bank, Name, Datum, Betrag)
- TW/VFW-Prämie (manuell editierbar, eigenes Stückzahl-Feld)
- 5-Stufen-Workflow: VORLAUF → ZUR_PRUEFUNG → FREIGEGEBEN → GENEHMIGT → ENDLAUF
- Einspruch/Ablehnung mit Pflicht-Begründung
- Status-Tooltips mit Zeitstempeln und Namen
- Vorbesitzer bei GW aus Bestand (aus Locosoft dealer_vehicles → customers_suppliers)
- Datenquelle: Locosoft sales/Deckungsbeitrag, SSOT: `api/provision_service.py`

### 3. Jahresprämie (Migration aus HR-Workstream)
- Bereits vorhanden: api/jahrespraemie_api.py
- Migration hierher geplant

## Module & Dateien
### APIs
- `api/provision_api.py` — REST-Endpunkte (Live-Preview, Vorlauf, Endlauf, Workflow, Positionen, Zusatzleistungen, Prämien, Config)
- `api/provision_service.py` — SSOT Berechnungslogik (berechne_live_provision, create_vorlauf, get_dashboard_daten, get_lauf_detail, get_aktive_verkaeufer, _get_vorbesitzer_fuer_vins)
- `api/provision_pdf.py` — PDF-Generierung (ReportLab, A4, Deckblatt + Detail + Jahresübersicht)
### Routes
- `routes/provision_routes.py` — HTML-Views (Meine Provision, Dashboard, Detail, PDF-Download)
### Templates
- `templates/provision/provision_dashboard.html` — VKL-Dashboard (Sidebar, Status-Badges mit Tooltips)
- `templates/provision/provision_detail.html` — Lauf-Detail (Accordion, Edit-Modal, Einspruch-Modal, Workflow-Buttons, Zusatzleistungen, Summentabelle mit editierbaren Prämien)

## DB-Tabellen (PostgreSQL drive_portal)
- `provision_config` — Provisionsarten (Kategorien, Sätze, Min/Max, Zielprämie)
- `provision_laeufe` — Läufe pro Verkäufer/Monat (Status, Summen, Workflow-Felder, Einspruch, TW-Prämie, Belegnummer, PDF-Pfade)
- `provision_positionen` — Einzelpositionen pro Lauf (Fahrzeug, Provision, Vorbesitzer, Einspruch)
- `provision_zusatzleistungen` — Kat. V Finanzdienstleistungen (Bank, Name, Datum, Betrag)

## Fahrzeug-Klassifizierung (SSOT)
Über `dealer_vehicle_type` aus Locosoft (Kommissionsnummer):
- **N** → Kat. I (Neuwagen) — Erstzulassung auf Kunde
- **T, V** → Kat. II (Testwagen/VFW) — war auf Autohaus zugelassen
- **D, G** → Kat. III (Gebrauchtwagen)
- Zusätzlich: Fahrzeuge > 365 Tage nach Erstzulassung → Kat. III
- P1-Memo wird NICHT mehr für Klassifizierung verwendet

## Berechtigungen
### Vollzugriff (Dashboard, alle Läufe, Bearbeiten)
- Florian Greiner, Peter Greiner, Vanessa Groll (username-basiert in `_PROVISION_VOLLZUGRIFF_USERS`)
### Genehmiger
- Anton Süß, Florian Greiner + Vanessa Groll (temporär für Testphase)
### Verkäufer
- Sehen nur eigene Provision über "Meine Provision"
- Können bei ZUR_PRUEFUNG freigeben oder Einspruch einlegen

## Aktueller Stand (erledigt am 2026-03-31)
- Provisionsabrechnung Phase 1+2 komplett
- Detail-Seite Redesign: Accordion, Edit-Modal, Einkäufer-Umzuweisung, Vorbesitzer bei Kat IV
- Zusatzleistungen (Kat. V) CRUD mit Modal, Bank-Dropdown (7 Banken), Anteil-% (Default 50%, manuell änderbar)
- TW/VFW-Prämie manuell editierbar (Stückzahl + Betrag)
- 5-Stufen-Workflow mit Einspruch/Ablehnung (Pflicht-Begründung)
- PDF: Deckblatt + Detail + Kat V + Jahresübersicht, Vorbesitzer bei GW Bestand
- Neuwagen-Klassifizierung über dealer_vehicle_type (nicht mehr P1)
- Berechtigungen: Vanessa Groll dauerhaft Vollzugriff + Genehmigerin (nicht mehr temporär)
- E-Mail-Stubs vorbereitet (PROVISION_EMAIL_ENABLED = False)
- Kumulierte Zielprämie: Doppeltes Gate (kum + Monat), Spec: `docs/superpowers/specs/2026-03-30-kumulierte-zielpraemie-design.md`
- **Admin-Funktionen (2026-03-31):** Endlauf zurücksetzen (ENDLAUF → GENEHMIGT), Vorlauf komplett löschen (jeder Status), Fahrzeug manuell hinzufügen (Modal mit Kategorie, Modell, Käufer, BE, Provisionssatz)
- **Rechnungsnummer nur für Admin** sichtbar (Verkäufer sehen Spalte nicht)
- **Accordion: Mehrere Kategorien gleichzeitig öffenbar**, offene Kategorien bleiben nach Reload/Bearbeiten erhalten (sessionStorage)
- **Einzelpositionen löschen** — Lösch-Button neben Bearbeiten-Button pro Position
- **Differenzbesteuerung §25a Fix (2026-03-31):** MwSt-Fallback im Sales-Sync korrigiert: Marge = VK - Fahrzeuggrundpreis (statt VK - Einsatzwert). Alle differenzbesteuerten Fahrzeuge haben jetzt exakt den gleichen DB wie Locosoft.
- **Kat IV Bemessungsgrundlage = BE II** (nicht mehr BE I/DB1). Detail-Spalte "BE II", PDF-Header "BE II". calc_gw_bestand gibt jetzt (provision, be2) zurück.

## Offene Punkte / Nächste Schritte
- E-Mail-Benachrichtigungen aktivieren (nach Testphase)
- Test mit Anton Süß (Verkaufsleiter) geplant
- Lohnbuchhaltung-Export (Phase 3)
- Werkstatt-Prämien: Konzept in Excel vorhanden, Umsetzung steht aus
- Jahresprämie: Existiert in HR, Migration geplant
- Kumulierte Zielprämie: Config-Validität prüfen (gueltig_bis der Zielerfüllung-Zeile muss ganzjährig gelten)
- Bestehende März-Vorläufe löschen und neu erstellen (korrigierte DB-Werte nach §25a-Fix)

## Abhängigkeiten
- werkstatt (TEK-Daten, Stunden, Anwesenheit)
- verkauf (Deckungsbeitrag, Aufträge für Provisionen)
- hr (Mitarbeiter-Stammdaten, Funktionen/Gruppen)
- controlling (Kostenauswirkung, Reporting)
- locosoft (dealer_vehicles für Vorbesitzer, vehicles für Klassifizierung)
