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

### 2. Verkäufer-Provisionen (Phase 1+2 live, Workflow live, Phase 3 offen)
- Live-Preview, Vorlauf, Dashboard, Vorlauf-Detail
- Kategorien I–IV mit Bemessungsgrundlage (rg_netto/db), Min/Max-Grenzen
- Endlauf-Workflow (GENEHMIGT → ENDLAUF), Belegnummer VK{id}-{YYYY}-{MM}
- PDF-Generierung (ReportLab) mit Deckblatt + Detail + Jahresübersicht
- Position bearbeiten/löschen mit automatischer Summen-Neuberechnung
- Dashboard-Redesign (Sidebar, moderne Tabellen)
- Detail-Redesign (Accordion, Edit-Modal mit Berechnungszeile, Einkäufer-Umzuweisung)
- Zusatzleistungen (Kat. V) CRUD mit Modal (Bank, Name, Datum, Betrag)
- 5-Stufen-Workflow: VORLAUF → ZUR_PRUEFUNG → FREIGEGEBEN → GENEHMIGT → ENDLAUF
- Einspruch/Ablehnung mit Pflicht-Begründung
- Status-Tooltips mit Zeitstempeln
- Datenquelle: Locosoft sales/Deckungsbeitrag, SSOT: `api/provision_service.py`

### 3. Jahresprämie (Migration aus HR-Workstream)
- Bereits vorhanden: api/jahrespraemie_api.py
- Migration hierher geplant

## Module & Dateien
### APIs
- `api/provision_api.py` — REST-Endpunkte (Live-Preview, Vorlauf, Endlauf, Position bearbeiten/löschen, Workflow, Zusatzleistungen CRUD, Config)
- `api/provision_service.py` — SSOT Berechnungslogik (berechne_live_provision, create_vorlauf, get_dashboard_daten, get_lauf_detail, get_aktive_verkaeufer)
- `api/provision_pdf.py` — PDF-Generierung (ReportLab, A4, Deckblatt + Detail + Jahresübersicht)
- api/praemien_api.py (Werkstatt-Prämien, geplant)
- api/jahrespraemie_api.py (Migration aus HR)
### Routes
- `routes/provision_routes.py` — HTML-Views (Meine Provision, Dashboard, Detail, PDF-Download)
### Templates
- `templates/provision/provision_dashboard.html` — VKL-Dashboard (Sidebar, Läufe/Verkäufer-Tabellen, Status-Badges mit Tooltips)
- `templates/provision/provision_detail.html` — Lauf-Detail (Accordion, Edit-Modal, Einspruch-Modal, Workflow-Buttons, Zusatzleistungen, Summentabelle)
- templates/verguetung/werkstatt_praemien.html (geplant)
### Celery Tasks (geplant)
- monatliche Prämienberechnung Werkstatt
### Scripts
- Import Locosoft CSV (geplant)

## DB-Tabellen (PostgreSQL drive_portal)
- `provision_config` — Provisionsarten (Kategorien, Sätze, Min/Max, Zielprämie)
- `provision_laeufe` — Läufe pro Verkäufer/Monat (Status, Summen, Belegnummer, PDF-Pfade, Workflow-Felder, Einspruch-Felder)
- `provision_positionen` — Einzelpositionen pro Lauf (Fahrzeug, Provision, Einspruch)
- `provision_zusatzleistungen` — Kat. V Finanzdienstleistungen (Bank, Name, Datum, Betrag)
- praemien_config (KPI-Schwellwerte, Stufen, Beträge pro Gruppe — geplant)
- praemien_berechnungen (monatliche Ergebnisse pro Mitarbeiter — geplant)

## Aktueller Stand (erledigt am 2026-03-30)
- Provisionsabrechnung Phase 1+2: Live-Preview, Vorlauf, Dashboard, Detail, Kat I–IV, Bemessungsgrundlage, Min/Max, Locosoft Memo P1, VFW/NW > 1 Jahr → GW-Regel, DB2-Operatoren
- Endlauf-Workflow: GENEHMIGT → ENDLAUF, Belegnummer, automatische PDF-Generierung
- Position bearbeiten (Provisionssatz, Bemessungsgrundlage, Provision final) mit Min/Max-Clamping aus provision_config
- Position löschen mit automatischer Summen-Neuberechnung
- Detail-Seite Redesign: Accordion-Kategorien, Edit-Modal mit Berechnungszeile, Einkäufer-Dropdown
- Einkäufer-Umzuweisung bei GW aus Bestand (Position wird verschoben + Summen neu berechnet)
- Bei Auswahl VKL/GL als Einkäufer: Position wird gelöscht (kein Provisions-Lauf vorhanden)
- Zusatzleistungen (Kat. V) CRUD: Modal mit Bank/Name/Datum/Betrag, summe_kat_v automatisch berechnet
- Summentabelle unter Accordion: alle Kategorien I-V + Zielprämie + Gesamt
- 5-Stufen-Workflow: VORLAUF → ZUR_PRUEFUNG → FREIGEGEBEN → GENEHMIGT → ENDLAUF
- Einspruch (Verkäufer) und Ablehnung (Genehmiger) mit Pflicht-Begründung, zurück auf VORLAUF
- Status-Tooltips mit Zeitstempel und Name (nicht E-Mail) bei Mouseover (Detail + Dashboard)
- PDF komplett überarbeitet: Deckblatt (Zusammenfassung) + Detail-Positionen + Kat V + Jahresübersicht
- PDF Design: Clean/modern mit blauer Akzentfarbe, Helvetica, graue Zebra-Zeilen, Gesamt pro Kategorie
- Berechtigungen: Vollzugriff nur Florian Greiner, Peter Greiner, Vanessa Groll (username-basiert)
- Genehmiger: Anton Süß, Florian Greiner + Vanessa Groll (temporär für Testphase)
- E-Mail-Stubs vorbereitet (PROVISION_EMAIL_ENABLED = False), aktivierbar nach Testphase

## Offene Punkte / Nächste Schritte
- E-Mail-Benachrichtigungen aktivieren (nach Testphase, Flag umschalten)
- Einspruch-Workflow: Verkäufer kann Einspruch gegen Position einlegen, VKL bearbeitet
- Phase 3: Lohnbuchhaltung-Export
- Abweichung Kraus Jan 2026 (230,61 €) mit Buchhaltung klären
- GW-Bestand DB2 Abgleich mit Referenzabrechnung
- Belegnummer Uniqueness: Kein DB-Constraint; durch ENDLAUF-Sperre im Endpunkt verhindert
- Rolle `personalbüro` im LDAP noch nicht eingeführt; Fallback über `buchhaltung`
- Vanessa Groll als Genehmigerin ist temporär (für Testphase) — nach Go-Live entfernen
- Test mit Anton (Verkaufsleiter) geplant
- Werkstatt-Prämien: Konzept in Excel vorhanden, Umsetzung steht aus
- Jahresprämie: Existiert in HR, Migration geplant

## Abhängigkeiten
- werkstatt (TEK-Daten, Stunden, Anwesenheit)
- verkauf (Deckungsbeitrag, Aufträge für Provisionen, SSOT: `api/provision_service.py`)
- hr (Mitarbeiter-Stammdaten, Funktionen/Gruppen)
- controlling (Kostenauswirkung, Reporting)
