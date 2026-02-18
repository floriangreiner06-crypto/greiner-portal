# Verkauf & Fahrzeuge — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-13

## Beschreibung

Verkauf umfasst Auftragseingang, Auslieferungen, Deckungsbeitrag, Profitabilität, Gewinnplanung V2 (GW), Fahrzeug-Daten, eAutoSeller und Ersatzwagen.

## Module & Dateien

### APIs
- `api/verkauf_api.py`, `api/verkauf_data.py` — Verkauf-Kern
- `api/profitabilitaet_api.py`, `api/profitabilitaet_data.py` — Profitabilität
- `api/fahrzeug_api.py`, `api/fahrzeug_data.py` — Fahrzeug-Daten
- `api/gewinnplanung_v2_gw_api.py`, `api/gewinnplanung_v2_gw_data.py` — Gewinnplanung V2 (GW)
- `api/eautoseller_api.py` — eAutoSeller
- `api/ersatzwagen_api.py` — Ersatzwagen
- **Provisionsmodul (geplant):** `api/provision_api.py`, `api/provision_service.py`, `api/provision_pdf.py`; Routes: `routes/provision_routes.py`; siehe `provisionsabrechnung/PROVISIONSMODUL_KONZEPT.md` und `UMSETZUNGSPLAN_PROVISIONSMODUL.md`.
- **Verkäufer-Zielplanung:** `api/verkaeufer_zielplanung_api.py` — Stückzahl, Verteilung, Saisonalität, Monatsziele, gespeicherte Ziele (GET/POST/PUT), Einzelverkäufer-Detail.

### Templates
- `templates/verkauf_*.html`
- `templates/planung/gewinnplanung_*.html`

### Celery Tasks
- `sync_sales`, `email_auftragseingang`, `sync_eautoseller_data`
- **sync_sales:** Verkauf Sync (Locosoft → Portal `sales`), Auftragseingang-Datenquelle. Läuft stündlich 7–18 Uhr Mo–Fr (`celery_app/__init__.py`). Bei fehlenden Tagesaufträgen: Sync manuell ausführen oder nächsten Lauf abwarten.

## DB-Tabellen (PostgreSQL drive_portal)

- `sales`, `vehicles`, `dealer_vehicles`, `customers_suppliers`
- `verkaeufer_ziele` — gespeicherte Jahresziele (NW/GW) pro Verkäufer für Zielplanung; Migration: `migrations/add_verkaeufer_ziele_table.sql`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Auftragseingang-Report: Testversand nutzt VerkaufData (SSOT), voller Report-Inhalt (Verkäufer-Tabellen, Werktage/Prognose) im E-Mail-Body statt nur PDF-Anhang
- ✅ Auftragseingang, Profitabilität, Gewinnplanung im Einsatz
- ✅ AHK FIN Check / Autohauskenner-Portal: Machbarkeits- und Nutzenanalyse erstellt, Portal-Check (keine API); Integration vorerst auf Eis
- ✅ mobile.de Zukauf/Neueingestellte: API-Optionen analysiert (Search-API + Ad-Stream); Scraping blockiert, offizielle APIs nutzbar. Siehe `MOBILEDE_ZUKAUF_API_OPTIONEN.md`.
- 🔧 eAutoSeller, Ersatzwagen je nach Projektstand
- ✅ Provisionsabrechnung Phase 1+2 (Teil): **Live-Preview** (Phase 1) und **Vorlauf + Dashboard** (Phase 2 Teil). SSOT: `api/provision_service.py` (berechne_live_provision, create_vorlauf, get_dashboard_daten, get_lauf_detail), `api/provision_api.py` (live-preview, vorlauf-erstellen, dashboard, lauf/<id>). Views: /provision/meine, /provision/dashboard (VKL), /provision/detail/<id>. PDF-Modul `api/provision_pdf.py` (reportlab) angelegt; bei Bedarf nach Commit-Fix prüfen. Offen: Einspruch, Endlauf freigeben, PDF-Download-URL; Phase 3 (Kat. V, Lohnbuchhaltung). Abweichung Kraus Jan 2026 mit Buchhaltung klären (VIN-Liste im Sync).
- ✅ **Verkäufer-Zielplanung (Erweiterung):** Saisonalität aus Locosoft (API `saisonalitaet/<jahr>`, Monatsverteilung), IST in Monatsverteilung (SSOT gleicher Endpoint). Monatsziele-API nutzt gespeicherte Ziele falls vorhanden.
- ✅ **Auftragseingang Zielerfüllung:** Monatsziele-API; Summary-Karten mit „Zielerfüllung (Zielplanung): NW/GW IST/Ziel (X%)“; Verkäufer-Tabelle mit Spalten Ziel NW, Ziel GW, Erfüllung % (nur Monatsansicht).
- ✅ **Workflow Zielplanung:** Tabelle `verkaeufer_ziele`, GET/POST Ziele, editierbare Tabelle (Vorschlag übernehmen, Gespeicherte Ziele laden, Speichern). Differenz-Box: Summe vereinbarte Ziele vs. Konzernziel, Hinweis auf Ausgleich in weiteren Planungsgesprächen.
- ✅ **Detailansicht pro Verkäufer (Planungsgespräch):** Route `/verkauf/zielplanung/verkaeufer/<nr>`, nur diese Person (Vorjahr, Vorschlag, Vereinbarung), PUT pro Verkäufer; Link „Detail“ in Haupttabelle. Motivierender Aufbau: Hero mit Jahresziel, Steigerung % zum Vorjahr, Badge „Über Planvorschlag“, Erfolgstext nach Speichern.
- 🔧 **Test mit Anton (Verkaufsleiter)** geplant (nächster Schritt).

## Offene Entscheidungen / Nächste Schritte

- **Verkäufer-Zielplanung:** Test mit Anton (Verkaufsleiter) durchführen; Feedback einarbeiten.
- AHK-Portal (Die Autohauskenner): Keine REST-API gefunden; Integration nur via Link/Deep-Link sinnvoll. Siehe `AHK_PORTAL_ANALYSE.md`.
- mobile.de Zukauf: API-Anfrage (Search-API / Ad-Stream) an mobile.de gestellt (Kundennr. 504661); Rückmeldung abwarten. Danach ggf. Integration in DRIVE (Celery + UI für Zukauf-Prüfung).

## Abhängigkeiten

- Integrations (eAutoSeller API), Infrastruktur (Celery)
