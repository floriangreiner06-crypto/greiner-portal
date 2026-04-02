# Vergütung & Prämien — Arbeitskontext
## Status: Aktiv
## Letzte Aktualisierung: 2026-04-01
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

## Aktueller Stand (erledigt am 2026-04-02)
- Provisionsabrechnung Phase 1+2 komplett
- Detail-Seite Redesign: Accordion, Edit-Modal, Einkäufer-Umzuweisung, Vorbesitzer bei Kat IV
- Zusatzleistungen (Kat. V) CRUD mit Modal, Bank-Dropdown (7 Banken), Anteil-% (Default 50%, manuell änderbar)
- TW/VFW-Prämie manuell editierbar (Stückzahl + Betrag)
- 5-Stufen-Workflow mit Einspruch/Ablehnung (Pflicht-Begründung)
- PDF: Deckblatt + Detail + Kat V + Jahresübersicht, Vorbesitzer bei GW Bestand
- Neuwagen-Klassifizierung über dealer_vehicle_type (nicht mehr P1)
- Berechtigungen: Vanessa Groll dauerhaft Vollzugriff + Genehmigerin (nicht mehr temporär)
- **E-Mail-Workflow (2026-03-31):** 6 Workflow-Mails implementiert (Zur Prüfung, Freigegeben, Einspruch, Genehmigt/VKL, Abgelehnt, Endlauf). HTML-Template mit Corporate-Design, Verkäufer-Email über ldap_employee_mapping, Anzeigenamen statt E-Mail-Adressen in Texten. PROVISION_EMAIL_ENABLED = False, Mails werden geloggt. Preview: `static/provision_mail_preview.html`
- Kumulierte Zielprämie: Doppeltes Gate (kum + Monat), Spec: `docs/superpowers/specs/2026-03-30-kumulierte-zielpraemie-design.md`
- **Admin-Funktionen (2026-03-31):** Endlauf zurücksetzen (ENDLAUF → GENEHMIGT), Vorlauf komplett löschen (jeder Status), Fahrzeug manuell hinzufügen (Modal mit Kategorie, Modell, Käufer, BE, Provisionssatz)
- **Rechnungsnummer nur für Admin** sichtbar (Verkäufer sehen Spalte nicht)
- **Accordion: Mehrere Kategorien gleichzeitig öffenbar**, offene Kategorien bleiben nach Reload/Bearbeiten erhalten (sessionStorage)
- **Einzelpositionen löschen** — Lösch-Button neben Bearbeiten-Button pro Position
- **Differenzbesteuerung §25a Fix (2026-03-31):** MwSt-Fallback im Sales-Sync korrigiert: Marge = VK - Fahrzeuggrundpreis (statt VK - Einsatzwert). Alle differenzbesteuerten Fahrzeuge haben jetzt exakt den gleichen DB wie Locosoft.
- **Kat IV Bemessungsgrundlage = BE II** (nicht mehr BE I/DB1). Detail-Spalte "BE II", PDF-Header "BE II". calc_gw_bestand gibt jetzt (provision, be2) zurück.
- **DB-Verbindung Testsystem Fix:** `db_connection.py` lud hardcoded `/opt/greiner-portal/config/.env` (Prod) statt dynamisch. Testsystem arbeitete dadurch gegen Prod-DB. Jetzt dynamischer Pfad via `pathlib`. Versehentlich erstellte Prod-Vorläufe wurden bereinigt.
- **Einkäufer-Filter GW aus Bestand:** `get_sales_where_einkaeufer_only` filterte nur `out_sale_type IN ('B','G','D','T')`. Fahrzeuge mit `out_sale_type='F'` aber `dealer_vehicle_type='D'` (GW mit Regelbesteuerung) fehlten. Jetzt wird auch `dealer_vehicle_type` geprüft.
- **Vorlauf aktualisieren (2026-04-01):** "Alle aktualisieren"-Button im Dashboard-Header aktualisiert alle Vorläufe eines Monats gleichzeitig. Aktualisierung ändert NUR bestehende Positionen — gelöschte Positionen werden NICHT wieder eingefügt. Manuell bearbeitete Positionen (`manuell_geaendert`-Flag auf `provision_positionen`) werden geschützt. Migration: `migrations/add_manuell_geaendert_provision_positionen.sql`.
- **Zielprämie Auftragseingang-Zählung (2026-04-01):** IST-Stückzahl für kumulierte Zielprämie liest jetzt aus synced `sales`-Tabelle (gleiche Quelle wie Auftragseingang-Seite). N/V = immer NW, T = nur ≤1 Jahr nach EZ. Kaufmännische Rundung des Monatsziels (`math.floor(x + 0.5)`).
- **Zielprämie-Ausschluss (2026-04-01):** Daniel Fialkowski (VKB 2003) als reiner GW-Verkäufer von Zielprämie ausgeschlossen — kein Kumuliert-Block, keine Ia-Zeile in Detail/PDF, keine Stückprämie in Gesamtsumme. Konfiguriert über `ZIELPRAEMIE_AUSSCHLUSS` in `provision_service.py`.
- **PDF Stk.-Dopplung behoben (2026-04-01):** `summary_row` in `provision_pdf.py` hängt "Stk." nur noch bei Zahlen an, nicht bei Text wie "erfüllt / +3 Stk.".
- **Dashboard Monatspersistenz (2026-04-01):** Gewählter Monat wird als URL-Parameter (`?monat=YYYY-MM`) persistiert. Nach Aktionen (Vorlauf erstellen, aktualisieren, löschen) bleibt der Monat erhalten statt auf den aktuellen Monat zurückzuspringen. Detail-Seite übergibt Monat beim Zurücknavigieren ans Dashboard.

- **PDF Jahresübersicht: nur ENDLAUF (2026-04-02):** Stückzahlen (NW, TW/VFW, GW) und Provisionssumme in der Jahresübersicht zählen nur Läufe mit `status = 'ENDLAUF'`. Vorläufe werden nicht mitgezählt — erst nach Endlauf-Erstellung fließen Fahrzeuge und Provision in die Jahresübersicht ein.
- **Bemessungsgrundlage §25a-Fix (2026-04-02):** Bei Differenzbesteuerung (§25a) speichert Locosoft teilweise den Brutto als `invoices.total_net`. Fix: Wenn `rechnungsbetrag_netto == out_sale_price` (Brutto = "Netto"), wird `netto_vk_preis` (VK - Margin-MwSt) als Bemessungsgrundlage verwendet. Sonst `rechnungsbetrag_netto`. Betrifft alle Kategorien. Vorlauf-Aktualisierung schreibt jetzt auch `rg_netto` mit (vorher nur `bemessungsgrundlage`).
- **Zielprämie: nur Monatsziel als Gate (2026-04-02):** Kumulierte 2-Gate-Regel entfernt. Gate prüft nur noch `monats_ist >= monats_ziel`. Kumulierte Daten (Kum. Ziel/IST) werden weiterhin angezeigt, sind aber kein Gate mehr. Wenn Monatsziel erreicht: Zielerreichung (200€) + Übererfüllung (je 100€/Stk.).
- **Zielprämie live in Detail-API (2026-04-02):** `summe_stueckpraemie` und `summe_gesamt` in der Lauf-Detail-API werden live aus `kum_daten` berechnet, nicht nur aus DB gelesen. Summentabelle zeigt immer den aktuellen Wert, auch ohne Vorlauf-Aktualisierung.
- **Endlauf-Summen Rundung (2026-04-02):** Alle Summenfelder im Endlauf-Bereich (Kat. I–V + Gesamt) werden auf 2 Dezimalstellen kaufmännisch gerundet (`toFixed(2)`).
- **P1-Memo deaktiviert (bestätigt 2026-04-02):** `memo_p1_kategorie` in `provision_config` ist leer → P1-Handling komplett deaktiviert. N-Fahrzeuge mit P1 bleiben Kat. I, T/V bleiben Kat. II, G/D bleiben Kat. III. Keine Umkategorisierung.
- **HTML-Preview Route (2026-04-01, WIP):** `/provision/pdf-preview/<lauf_id>` zeigt Provisionsabrechnung als HTML (Deckblatt + Detail + Jahresübersicht). Template: `templates/provision/provision_pdf_preview.html`. **FEHLER:** Route wirft aktuell einen Fehler — muss noch debuggt werden.

## Offene Punkte / Nächste Schritte
- E-Mail-Benachrichtigungen aktivieren: Mails sind fertig implementiert, nur `PROVISION_EMAIL_ENABLED = True` setzen + Links von `drive:5002` auf `drive` ändern (nach Testphase/Prod-Deploy)
- Test mit Anton Süß (Verkaufsleiter) geplant
- Lohnbuchhaltung-Export (Phase 3)
- Werkstatt-Prämien: Konzept in Excel vorhanden, Umsetzung steht aus
- Jahresprämie: Existiert in HR, Migration geplant
- **WICHTIG:** Vor Deploy nach Prod: `db_connection.py`-Fix und §25a-Sync-Fix prüfen — Prod hat noch alten Code

## Abhängigkeiten
- werkstatt (TEK-Daten, Stunden, Anwesenheit)
- verkauf (Deckungsbeitrag, Aufträge für Provisionen)
- hr (Mitarbeiter-Stammdaten, Funktionen/Gruppen)
- controlling (Kostenauswirkung, Reporting)
- locosoft (dealer_vehicles für Vorbesitzer, vehicles für Klassifizierung)
