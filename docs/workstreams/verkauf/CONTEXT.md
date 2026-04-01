# Verkauf & Fahrzeuge — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-03-25

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
- **VFW-Vermarktung (geplant):** Siehe `VFW_VERMARKTUNG_IMPLEMENTIERUNGSPLAN.md`; geplante API: `api/vfw_api.py`, `api/vfw_kalkulation_service.py`, `api/vfw_pdf.py`.

### Templates
- `templates/verkauf_*.html`
- `templates/planung/gewinnplanung_*.html`

### Celery Tasks
- `sync_sales`, `email_auftragseingang`, `sync_eautoseller_data`
- **sync_sales:** Verkauf Sync (Locosoft → Portal `sales`), Auftragseingang-Datenquelle. Läuft stündlich 7–18 Uhr Mo–Fr (`celery_app/__init__.py`). Bei fehlenden Tagesaufträgen: Sync manuell ausführen oder nächsten Lauf abwarten. **Fix 2026-03-09:** INSERT hatte 30 %s bei 31 Spalten → neue Verträge schlugen mit „not all arguments converted“ fehl; behoben (31. %s ergänzt, Parameter robust mit _scalar).

## DB-Tabellen (PostgreSQL drive_portal)

- `sales`, `vehicles`, `dealer_vehicles`, `customers_suppliers`
- `verkaeufer_ziele` — gespeicherte Jahresziele (NW/GW) pro Verkäufer für Zielplanung; Migration: `migrations/add_verkaeufer_ziele_table.sql`
- `zielplanung_stand` — Planungsstand pro Zieljahr (Parameter + Status entwurf/freigegeben); Migration: `migrations/add_zielplanung_stand_table.sql`. Monatsziele/Auftragseingang nutzen `verkaeufer_ziele` nur bei Status „freigegeben“.

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ **Auftragseingang E-Mail (Celery `email_auftragseingang`):** `scripts/send_daily_auftragseingang.py` nutzt nur noch `reports/auftragseingang_report_builder.build_auftragseingang_report_package` (SSOT = `VerkaufData`) – gleiches Layout wie zuvor korrekt: Werktage, Ø AE/Tag, Prognose, Verkäufer-/Marken-Tabellen im Body, volles PDF. Ursache des „alten“ Mails war die **im Script duplizierte SQL-Zählung** (nur `dealer_vehicle_type`), nicht der Task selbst. Admin-Testversand (`reports/send_test.py`) ruft denselben Builder auf.
- ✅ **VKL-Dashboard (`/verkauf/dashboard`):** Nach Rollback wieder angebunden: Routen Dashboard/Zielauswertung/Motocost, `GET /api/verkauf/dashboard-vkl`, `api/verkauf_vkl_dashboard_service.py`, VKL-Hilfsmethoden in `api/verkauf_data.py` (`_NW_SUM_CASE`/`_GW_SUM_CASE`, Segmente, Forecast, Marken-Split).
- ✅ Auftragseingang, Profitabilität, Gewinnplanung im Einsatz
- ✅ AHK FIN Check / Autohauskenner-Portal: Machbarkeits- und Nutzenanalyse erstellt, Portal-Check (keine API); Integration vorerst auf Eis
- ✅ mobile.de Zukauf/Neueingestellte: API-Optionen analysiert (Search-API + Ad-Stream); Scraping blockiert, offizielle APIs nutzbar. Siehe `MOBILEDE_ZUKAUF_API_OPTIONEN.md`.
- 🔧 eAutoSeller, Ersatzwagen je nach Projektstand
- ✅ Provisionsabrechnung Phase 1+2 (Teil): **Live-Preview** (Phase 1) und **Vorlauf + Dashboard** (Phase 2 Teil). SSOT: `api/provision_service.py` (berechne_live_provision, create_vorlauf, get_dashboard_daten, get_lauf_detail), `api/provision_api.py` (live-preview, vorlauf-erstellen, dashboard, lauf/<id>). Views: /provision/meine, /provision/dashboard (VKL), /provision/detail/<id>. PDF-Modul `api/provision_pdf.py` (reportlab); PDF-Pfad wird nach Generierung in DB gespeichert. **Bemessungsgrundlage Kat. I (NW):** provision_config.bemessungsgrundlage wird ausgewertet: bei `rg_netto` erfolgt Provision = Rechnungsnetto × Satz (mit Min/Max) pro Position wie bei II/III; bei `db` wie bisher DB-Summe × Satz. **Locosoft Memo P1:** Pr. 132 Verkauf/Memo „P1“ → DRIVE bucht in Kat. II (VFW/TW), 1 % Rg.Netto; Feld `dealer_vehicles.memo` → `sales.memo` (sync_sales). Doku: `provisionsabrechnung/LOCOSOFT_MEMO_P1_NW_PROVISION.md`. **Max-Grenzen wie Excel:** II_testwagen max 500 €, III_gebrauchtwagen max 300 € (Migration `fix_provision_max_ii_iii_excel.sql`); Vergleich Punzmann: `provisionsabrechnung/VERGLEICH_PUNZMANN_EXCEL_VS_VORLAUF.md`. **VFW/NW > 1 Jahr nach EZ = GW:** Fahrzeuge mit out_sale_type NW/VFW (Kat. I oder II), die zum Rechnungsdatum älter als 1 Jahr nach Erstzulassung sind, werden unter III (Gebrauchtwagen) geführt und mit cfg_iii (1 % Rg.Netto, Min/Max) abgerechnet; `sales.first_registration_date` + `out_invoice_date` in provision_service. **Rechnungsnetto vs. Fahrzeugnetto:** Für Kat. II (VFW/TW) und I (rg_netto) wird `rechnungsbetrag_netto` (invoices.total_net) verwendet; für Kat. III (GW) `netto_vk_preis` (Fahrzeugnetto), da Rechnung Zusätze enthalten kann. **DB2 (GW Bestand) konfigurierbar:** provision_config um `gw_bestand_operator_abzug` und `gw_bestand_operator_komponenten` ergänzt (Migration `add_provision_config_gw_bestand_operators.sql`); Modal Admin/Provisionsarten mit Überschrift „DB2 = DB1 minus …“, sprechenden Feldern (Anteil, Verkaufskostenpauschale) und Operatoren in zwei Schritten. **Vorlauf-Detail:** Kategorien aufsteigend (I→II→III→IV), Kategorie nur einmal als Überschrift, Summenzeile pro Kategorie, Gesamtsumme unten. **Offen:** Einspruch, Endlauf freigeben, PDF-Download-URL; Phase 3 (Kat. V, Lohnbuchhaltung). Abweichung Kraus Jan 2026 (230,61 €) mit Buchhaltung klären. **Minimale Abweichungen** bei GW-Bestand-DB2-Provision: nochmal Abgleich mit Referenzabrechnung geplant. n8n als Workflow-Tool für Provision: optional später für Benachrichtigungen/Freigabe-Ketten; Kernlogik bleibt in DRIVE.
- ❌ **VFW-Vermarktung (geplant):** Modul für Kalkulation Vorführwagen, Tageszulassungen und Mietwagen (Verkauf + Geschäftsleitung). Phasenplan: 1) Datenbasis & Bestand-Dashboard, 2) Rundschreiben-Manager, 3) Kalkulationsengine + PDF, 4) KI/Alerts. Detaillierter Plan: **`VFW_VERMARKTUNG_IMPLEMENTIERUNGSPLAN.md`**. Bestehende Bausteine: `FahrzeugData.get_vfw_bestand()`, `fahrzeugfinanzierungen`, AfA VFW/Mietwagen, Provisionslogik Block II.
- ✅ **Verkäufer-Zielplanung (Erweiterung):** Saisonalität aus Locosoft (API `saisonalitaet/<jahr>`, Monatsverteilung), IST in Monatsverteilung (SSOT gleicher Endpoint). Monatsziele-API nutzt gespeicherte Ziele **nur bei freigegebener Planung** (Tabelle `zielplanung_stand`, Status `freigegeben`).
- ✅ **Auftragseingang Zielerfüllung:** Monatsziele-API; Summary-Karten mit „Zielerfüllung (Zielplanung): NW/GW IST/Ziel (X%)“; Verkäufer-Tabelle mit Spalten Ziel NW, Ziel GW, Erfüllung % (nur Monatsansicht).
- ✅ **Auftragseingang Zeitraum-Filter Kalenderjahr/Geschäftsjahr (TAG 223):** Auftragseingang unterstützt jetzt `zeitraum=calendar_year|fiscal_year|month|day`; Geschäftsjahr ist verbindlich **Sep–Aug** (`year` = Startjahr, z. B. 2025 → GJ 2025/26). Verkäufer-Übersicht für Besprechung mit klaren Spalten **NW / TVFW / GW / Gesamt** in einem Klick auf Kalenderjahr oder Geschäftsjahr.
- ✅ **Auslieferungen analog Zeitraum-Filter + kompakte Jahresdarstellung (TAG 223):** Auslieferungen unterstützen jetzt ebenfalls `zeitraum=calendar_year|fiscal_year|month|day` auf Rechnungsdatum. Bei Kalenderjahr/Geschäftsjahr sind Verkäufer standardmäßig eingeklappt (Summenzeile), Details per Klick; bei Tag/Monat standardmäßig geöffnet.
- ✅ **UI-Angleichung Auftragseingang/Auslieferungen (TAG 223):** Auslieferungen wurden auf dieselbe Filter-Bedienlogik wie Auftragseingang gebracht (Quick-Buttons inkl. Kalenderjahr/Geschäftsjahr, Standort-Tabs statt Dropdown). Tabellenköpfe und Kennzahl-Spalten wurden visuell vereinheitlicht; große Zeiträume zeigen kompakte Summenzeilen mit optionalen Details.
- ✅ **Workflow Zielplanung:** Tabelle `verkaeufer_ziele`, GET/POST Ziele, editierbare Tabelle (Vorschlag übernehmen, Gespeicherte Ziele laden, Speichern). Differenz-Box: Summe vereinbarte Ziele vs. Konzernziel, Hinweis auf Ausgleich in weiteren Planungsgesprächen.
- ✅ **Speicherkonzept & Freigabe:** Tabelle `zielplanung_stand` speichert pro Zieljahr Parameter (Referenz, Konzernziel NW/GW, NW nach Marke) und Status (`entwurf`/`freigegeben`). Beim Seitenaufruf wird Planungsstand geladen → Formular und Tabelle wiederhergestellt. „Ziele speichern“ schreibt Entwurf (Parameter + Ziele). „Planung freigeben“ setzt Status auf `freigegeben`; ab dann sind Ziele verbindlich für Monatsziele und Auftragseingang. Siehe `VERKAEUFER_ZIELPLANUNG_SPEICHERKONZEPT_FREIGABE.md`.
- ✅ **Detailansicht pro Verkäufer (Planungsgespräch):** Route `/verkauf/zielplanung/verkaeufer/<nr>`, nur diese Person (Vorjahr, Vorschlag, Vereinbarung), PUT pro Verkäufer; Link „Detail“ in Haupttabelle. Motivierender Aufbau: Hero mit Jahresziel, Steigerung % zum Vorjahr, Badge „Über Planvorschlag“, Erfolgstext nach Speichern.
- ✅ **Auftragseingang & Auslieferungen – Verkäufer-Filter (konfigurierbar):** Filter-Modus pro Rolle in Rechteverwaltung (Tab Feature-Zugriff → Nach Rolle → „Filter-Verhalten für Listen“): **Nur eigene** (Filter fix, wie bisher für Rolle verkauf), **Eigene, Filter auflösbar**, **Alle, kann filtern**. API nutzt `api/feature_filter_mode.get_filter_mode(role, feature)`; bei `own_only` wird `verkaufer` aus `ldap_employee_mapping.locosoft_id` erzwungen. Betrifft: `api/verkauf_api.py` (_filter_mode_force_own), `api/verkauf_data.py` (Parameter `verkaufer`), Routes/Templates Auftragseingang und Auslieferung, OPOS (`api/opos_api.py`, `templates/controlling/opos.html`, Route `/controlling/opos`).
- ✅ **Sync_sales INSERT-Bug (2026-03-09):** Auftragseingang zeigte nur 2 statt aller März-2026-Aufträge. Ursache: INSERT in `scripts/sync/sync_sales.py` hatte 30 Platzhalter bei 31 Spalten; neue Verträge (nur INSERT, kein UPDATE) schlugen mit „not all arguments converted during string formatting“ fehl. Fix: 31. %s ergänzt, Parameter mit _scalar() gegen Tuple-Werte aus Locosoft abgesichert, out_subsidiary=0 korrekt (nicht zu None). 31 neue Aufträge danach fehlerfrei übernommen (u. a. Debitor 3008888 / Kaufvertrag 71731).
- ✅ **Dedup V/T→G/D + EZ-Regel für V (2026-04-01):** Locosoft legt bei VFW-Verkauf zwei Datensätze an (V-Abgang + G-Verkauf) → Doppelzählung in Verkäufer-Übersicht. Fix: `DEDUP_FILTER` um V/T→G/D erweitert (gleiche VIN + Vertragsdatum); 12-Monats-EZ-Regel nun auch für V (nicht nur T): VFW > 12 Monate ab EZ = GW. Betrifft `_NW_GW_CASE_ART`, `_NW_SUM_CASE`, `_GW_SUM_CASE`, alle Inline-Dedups in `get_auftragseingang_detail`, `get_auslieferung_detail`, `get_verkaufer_performance`, `get_db_marken_split_monat`. Python-Kategorisierung in Detail-Funktionen nutzt jetzt SQL `CASE` mit EZ-Regel statt harter `dealer_vehicle_type`-Zuordnung.
- 🔧 **Test mit Anton (Verkaufsleiter)** geplant (nächster Schritt).

## Offene Entscheidungen / Nächste Schritte

- **VFW-Vermarktung:** Offene Punkte aus `VFW_VERMARKTUNG_IMPLEMENTIERUNGSPLAN.md` klären (VFW-Definition V/D/T, Ampelschwellen, LBO/CSI-Quellen, Snapshot vs. Live); danach Phase 1 starten.
- **Verkäufer-Zielplanung:** Test mit Anton (Verkaufsleiter) durchführen; Feedback einarbeiten.
- AHK-Portal (Die Autohauskenner): Keine REST-API gefunden; Integration nur via Link/Deep-Link sinnvoll. Siehe `AHK_PORTAL_ANALYSE.md`.
- mobile.de Zukauf: API-Anfrage (Search-API / Ad-Stream) an mobile.de gestellt (Kundennr. 504661); Rückmeldung abwarten. Danach ggf. Integration in DRIVE (Celery + UI für Zukauf-Prüfung).
- **UI-Feinschliff Verkäufer-Tabellen:** Optional „Alle auf/zu“ auch in Auftragseingang ergänzen (wie Auslieferungen), falls im VKL-Review gewünscht.
- Optional: `get_auftragseingang_nw_marke_modell` in `VerkaufData` ergänzen (PDF-Abschnitt „Neuwagen nach Marke und Modell“ im Builder derzeit nur wenn Methode existiert).

## SSOT Verkauf / Zielplanung / Provision

Damit Verkäufer-Zielplanung und Provisionsabrechnung ohne Redundanzen nebeneinander laufen:
- **Verkäufer-ID:** überall Locosoft-Mitarbeiternummer (VKB).
- **Ziele:** nur `verkaeufer_ziele` + `zielplanung_stand`; Provision nutzt keine Ziele (bei Zielerfüllung in Provision nur bestehende Monatsziele-API).
- **Provisionslogik:** SSOT `api/provision_service.py`; Rohdaten aus `sales` (out_invoice_date).
- **Auftragseingang:** VerkaufData nutzt `sales` (Vertragsdatum); Zielplanung nutzt Locosoft direkt (Vertragsdatum). **T-Regel Verkaufsleitung:** T = NW nur bis 1 Jahr ab Erstzulassung; älter = GW. `sales.first_registration_date` (Sync aus Locosoft); Zielplanung: JOIN auf `vehicles.first_registration_date`. Details: **`SSOT_VERKAUF_ZIELPLANUNG_PROVISION.md`**.

## Abhängigkeiten

- Integrations (eAutoSeller API), Infrastruktur (Celery)
