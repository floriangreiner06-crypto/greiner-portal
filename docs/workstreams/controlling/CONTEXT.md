# Controlling (BWA, Bankenspiegel, Finanzreporting) — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-28

## Beschreibung

Controlling umfasst BWA-Berechnung, Bankenspiegel mit Konten und Transaktionen, TEK (Tägliche Erfolgskontrolle), den Finanzreporting-Cube sowie Kontenmapping. MT940/CAMT/PDF-Import, Umsatz-Bereinigung, Stundensatz-Kalkulation und Zins-Optimierung gehören ebenfalls in diesen Workstream. **AfA-Modul (2026-02-16):** Automatische monatliche Abschreibung für Vorführwagen und Mietwagen (Anlagevermögen).

## Module & Dateien

### APIs
- `api/bankenspiegel_api.py` — Dashboard, Konten, Transaktionen, Einkaufsfinanzierung, Fahrzeuge mit Zinsen
- `api/controlling_api.py` — BWA, BWA v2, Drilldown, DB1-Entwicklung
- `api/controlling_data.py` — Datenlayer BWA, TEK (get_tek_data)
- `api/finanzreporting_api.py` — Finanzreporting-Cube
- `api/kontenmapping_api.py` — Kontenmapping
- `api/stundensatz_kalkulation_api.py` — Stundensatz-Kalkulation
- `api/zins_optimierung_api.py` — Zins-Optimierung
- `api/afa_api.py` — **AfA Vorführwagen/Mietwagen:** Dashboard, Fahrzeuge, Monatsberechnung, Buchungsliste, CRUD, Abgang

### Routes
- `routes/controlling_routes.py` — Controlling-Frontend
- `routes/afa_routes.py` — AfA-Dashboard (Controlling → AfA Vorführwagen/Mietwagen)

### Templates
- `templates/bankenspiegel_*.html`
- `templates/controlling/*.html` (inkl. TEK-Dashboard: `tek_dashboard.html`, `tek_dashboard_v2.html`, **`afa_dashboard.html`**)

### Parser / Daten
- `parsers/` — MT940, CAMT, PDF-Import

### Celery Tasks
- `import_mt940`, `import_hvb_pdf`, `umsatz_bereinigung`, `bwa_berechnung`, `refresh_finanzreporting_cube`, `email_tek_daily`
- **`email_afa_bestand_report`** — AfA Bestand Abgleich DRIVE/Locosoft (20:00 Mo–Fr), E-Mail an Report-Abonnenten
- **`afa_monatsberechnung`** — Monatliche AfA-Buchungen für aktive VFW/Mietwagen (z. B. am 1. des Monats für Vormonat)

## DB-Tabellen (PostgreSQL drive_portal)

- `konten`, `banken`, `transaktionen`, `daily_balances`, `kategorien`, `kreditlinien`, `fibu_buchungen`, `bwa_monatswerte`
- **`afa_anlagevermoegen`** — VFW/Mietwagen-Stammdaten mit AfA-Parametern (linear 72 Monate)
- **`afa_buchungen`** — Monatliche AfA-Buchungen (Historie) pro Fahrzeug

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ **Workstream-Zuordnung (2026-02-12):** TEK dem Workstream Controlling zugeordnet (Scope, Module/Templates/Celery in CONTEXT.md; CLAUDE.md und .cursorrules angepasst).
- ✅ Bankenspiegel, BWA, TEK-Dashboard, Finanzreporting-Cube im Einsatz
- ✅ MT940/HVB-PDF-Import, Umsatz-Bereinigung
- 🔧 Kontenmapping und Stundensatz-Kalkulation je nach Projektstand
- ✅ **Kontenübersicht Locosoft (2026-02-13):** Klärung, wann Sachkonto 070101/071101 aktualisiert wird (live aus Locosoft bei jedem Aufruf; Locosoft-DB-Befüllung ca. 18–19 Uhr). Doku in CONTEXT.md ergänzt. Bestätigung: DRIVE-Saldo war korrekt, Typo in manueller Buchhaltungsauswertung.
- ✅ **Umlaut-Darstellung BWA/TEK-Modale (2026-02-13):** Zeichenfehler („ErlÄtise“ statt „Erlöse“) behoben. Ursache war Moji­bake in `routes/controlling_routes.py` (UTF-8-Zeichen fälschlich als Latin-1 gespeichert). Korrektur: alle gruppen_namen, SKR51_KONTOBEZEICHNUNGEN und weiteren Umlaute (ö, ä, ü, ß, €, Ø) in der Datei auf korrektes UTF-8 gestellt.
- ✅ **TEK Breakeven SSOT (2026-02-13):** Eine Breakeven/Prognose-Logik für Portal und PDF. SSOT: `api/controlling_data.py` (`berechne_breakeven_prognose`, `berechne_breakeven_prognose_standort`); Werktage: `utils/werktage.py` (`get_werktage_monat`). `get_tek_data` nutzt die SSOT statt eigener Formel (BWA-Kosten, echte Werktage). Projektregel: SSOT in CLAUDE.md und .cursorrules für alle Workstreams ergänzt.
- ✅ **TEK Werktage Datenstichtag (2026-02-17):** Da Locosoft-Daten erst abends (ca. 18–19 Uhr) kommen, zählt „verbleibende Werktage“ morgens den heutigen Tag mit (9 WT). Ab 19:00 Uhr gilt Kalender-Heute als vergangen (8 WT). Umsetzung: `get_werktage_monat(jahr, monat, stichtag=…)` mit Stichtag = gestern vor 19:00, sonst heute; `berechne_breakeven_prognose` und `berechne_breakeven_prognose_standort` übergeben den Stichtag. Portal und TEK-E-Mail/PDF nutzen dieselbe Logik.
- ✅ **TEK Portal = Report (2026-02-17):** Gleiche DB1 und gleiche Prognose in DRIVE und TEK-E-Mail/PDF. Ursache der Abweichung: (1) `get_tek_data` summierte nur 5 Bereiche + Clean Park, Portal zusätzlich 6-8932/9-Andere → Gesamt-DB1 in get_tek_data um 9-Andere ergänzt. (2) Hochrechnung wurde im Backend aus `operativ_db1` berechnet, im Portal aus `total_db1` → SSOT: `berechne_breakeven_prognose` nutzt jetzt `aktueller_db1` für die Hochrechnung; Frontend zeigt `prognose.hochrechnung_db1` aus der API.
- ✅ **TEK Prognose wie GlobalCube (2026-02-17):** Referenz GlobalCube: Prognose = (DB1 / **vergangene Werktage**) × Werktage gesamt. DRIVE nutzte zuvor „Tage mit Daten“ (Locosoft) als Divisor → Prognose zu schlecht. Umstellung auf **werktage_vergangen** (mit Datenstichtag vor 19:00 = gestern), damit z. B. bei 212.211 € nach 9 WT → 471.580 € (wie im GlobalCube-PDF).
- ✅ **TEK Berechnung konsistent (Reporting + Online):** Eine SSOT für DB1, Breakeven und Prognose in allen Modulen: **Portal** (api_tek → berechne_breakeven_prognose, Frontend zeigt prognose.hochrechnung_db1), **alle TEK-Reports** (tek_daily, tek_filiale, tek_nw/gw/teile/werkstatt, tek_verkauf, tek_service) über send_daily_tek.get_tek_data → tek_api_helper → api.controlling_data.get_tek_data → berechne_breakeven_prognose; **PDF** und **E-Mail** nutzen data.gesamt.prognose aus derselben Quelle. Standort-Breakevens (Deggendorf/Landau) nutzen berechne_breakeven_prognose_standort (gleiche Werktage-Formel). KST-Ziele nutzen eigene Hochrechnung (werktage_vergangen) für Zielerreichung, nicht TEK-Breakeven.
- **Session 2026-02-17:** TEK SSOT (Portal = alle Reports), Werktage-Datenstichtag (9 WT morgens), Prognose wie GlobalCube (Werktage-Divisor), Werktage/Prognose in PDF und E-Mail; Commit 2b3b4ba gepusht.
- **TEK DRIVE vs. Reporting (2026-02-17):** Analyse **ohne Code-Änderung** in `docs/workstreams/controlling/TEK_DRIVE_VS_REPORTING_ANALYSE.md`. Kern: Zwei Datenpfade (Portal = eigene Aggregation in api_tek; Report = get_tek_data); Clean Park in get_tek_data doppelt (9-Andere + cp); 4-Lohn im Report kalkulatorischer Einsatz → DB1/Prognose niedriger; Stückzahlen 68 vs. 70 vermutlich Aufrufzeit/Parameter.
- ✅ **AfA-Modul Vorführwagen/Mietwagen (2026-02-16):** Neues Sub-Modul zur automatischen Berechnung der monatlichen Abschreibung (AfA) für VFW und Mietwagen. Lineare AfA 72 Monate, monatsgenau. Dashboard unter Controlling → AfA Vorführwagen/Mietwagen; API `/api/afa/*`; Tabellen `afa_anlagevermoegen`, `afa_buchungen`; Celery-Task `afa_monatsberechnung`. Siehe `docs/workstreams/controlling/AFA_DISCOVERY.md` und `AFA_MODUL_KONZEPT.md`.
- ✅ **AfA Locosoft-Filter & Bestand (2026-02-16):** Nur eigene Mietwagen (Kennzeichen X oder `pre_owned_car_code` X/**M**); nur noch nicht verkaufte (`out_invoice_date IS NULL`). Dashboard-Filter „Bestand Geschäftsjahr“ (z. B. 2025/26). Buchhaltungs-Konten (450001/450002 an 090301/090302/090401/090402) in Monatsberechnung und CSV-Export; Abgang 090xxx an Bestandskonto dokumentiert.
- ✅ **AfA Buchhaltungs-Feedback (2026-02-16):** Konten-Mapping und Buchungslogik in `AFA_BUCHHALTUNG_FEEDBACK.md`. Excel-Anhänge in `docs/workstreams/controlling/AfA/` ausgewertet; Mietwagen-Listen nutzen Jw-Kz **M**, Filter um „M“ erweitert. Nutzungsdauer 72 Monate (in Excel keine Spalte; DATEV-Scan ist Bild-PDF, Werte manuell extrahieren).
- ✅ **AfA Monatsübersicht & CSV-Export (2026-02-16):** Berechnen/CSV: Fehlerbehandlung ergänzt (Alert bei API-Fehler, Download ins DOM); Monatsübersicht lädt als Promise, Alert erst nach Aktualisierung. Fix 500 in `monatsberechnung` (UnboundLocalError `date` durch entfernten lokalen Import); Fix 500 in `buchungsliste` (Response vs. Tupel-Rückgabe von `monatsberechnung`). Konten laut Buchhaltung: Mietwagen 090301/090302, VFW 090401/090402. Fahrgestellnr. (VIN) in Tabelle und CSV; Sortierung nach Kategorie (Mietwagen DEG/LAN/HYU, VFW DEG/LAN/HYU/Leapmotor); **Standort-Spalte** (DEG/HYU/LAN) für erkennbare Gruppierung.
- ❌ **Offen:** DATEV-Scan (Scan_20260216130905.pdf) – keine Textebene, Werte manuell extrahieren und bei Bedarf in Doku/AfA-Ordner ergänzen.
- ✅ **Export Konten-Mapping (2026-02-17):** Script `scripts/analysis/export_konten_mapping.py` – Sachkonten 800000–899999 aus `fibu_buchungen` (PostgreSQL) als CSV (Semikolon, UTF-8). Ausgabe: `data/exports/konten_mapping_export.csv`; optional Kopie in Windows-Sync (`data/exports/`). Konsolenausgabe: Zusammenfassung nach Kategorie, WARNUNG 817xxx/827xxx bei Kategorie „wareneinsatz“, Konten ohne Kategorie.
- ✅ **TEK Monatswerte & Vergleichswerte (2026-02-19):** Alle Bereiche zeigen Monatswerte (Einsatz, DB1, Marge) und Vergleichswerte (vs. VM / vs. VJ). Anpassungen: (1) `get_bereich_daten` nutzt denselben G&V-Filter und schließt Clean Park (847301/747301) aus 4-Lohn aus wie `get_tek_data`. (2) VJ pro Bereich: bei aktuellem Monat nur bis gleicher Kalendertag (wie SSOT), sonst voller Monat. (3) Frontend: vs. VM/VJ zeigt „n.a.“ wenn Vergleichsmonat Umsatz hatte aber DB1 = 0, sonst „-“ wenn keine Daten.
- ✅ **TEK Portal Monatswerte robust (2026-02-19):** Backend (api_tek) liefert Einsatz/DB1/Marge pro Bereich explizit als Zahl (kein null); Frontend nutzt `?? 0` und `Number()` sowie `fmtEuro`/`fmtPct` mit NaN-Check, damit keine „-“ mehr bei 0 oder fehlenden Keys.
- ✅ **TEK E-Mail GESAMT-Zeile = Portal (2026-02-19):** Im Gesamt-Report (build_gesamt_email_html) verwendet die GESAMT-Zeile der Tabelle für Monat jetzt `data.gesamt` (Umsatz, DB1, Marge) statt Summe der 5 Bereiche → E-Mail entspricht Portal (inkl. 9-Andere + Clean Park). Filiale-, Abteilungs-, Verkauf- und Service-Reports nutzen bereits dieselbe SSOT (get_tek_data) und waren fachlich korrekt.
- ✅ **TEK Abweichungen E-Mail vs. Portal dokumentiert (2026-02-19):** In `TEK_DRIVE_VS_REPORTING_ANALYSE.md` Abschnitt 9: verbleibende Ursachen (GESAMT-Zeile behoben, Stückzahl Zeitpunkt, Heute-Filter, Prognose) und Bestätigung dass alle Reports (Gesamt, Filiale, Abteilungen, Verkauf, Service) über tek_api_helper → get_tek_data_core denselben Datenstand haben.
- ✅ **Offene Posten Fahrzeugverkauf (2026-02-19):** SQL-Abfrage für die wöchentliche Buchhaltungsliste „offene Posten aus dem Fahrzeugverkauf“ (gruppierbar nach Verkäufer): `scripts/sql/offene_posten_fahrzeugverkauf.sql`, Doku `OFFENE_POSTEN_FAHRZEUGVERKAUF_QUERY.md`. Daten aus loco_journal_accountings (Debitoren 150000–199999), Verkäufer aus **FIBU** `employee_number` (= „Rg. schreibender Mitarbeiter“, wie Locosoft L362PR Spalte „Mitarbeiter“). Locosoft-OPOS-Export (CSV/XLS + Screenshot) im Ordner **`docs/workstreams/controlling/OPOS/`**; Mapping Doku `OPOS/README.md`. Konzept für **OPOS-Modul** (Filter, Reporting): `OPOS_MODUL_KONZEPT.md`.
- ✅ **OPOS Rollen/Rechte (2026-02-19):** Anbindung an bestehendes DRIVE-Rollenkonzept: Feature `opos` in `config/roles_config.py` (admin, buchhaltung, verkauf_leitung, verkauf). Vorschlag Daten-Sichtbarkeit: Buchhaltung/Admin/Verkaufsleitung = alle Posten; Verkäufer = nur eigene (Filter über ldap_employee_mapping → locosoft_id). Doku: **`OPOS_ROLLEN_RECHTE_VORSCHLAG.md`**.
- ✅ **OPOS-Modul umgesetzt (2026-02-19):** Route `/controlling/opos`, Template `templates/controlling/opos.html`, API `api/opos_api.py` (GET `/api/controlling/opos`, GET `/api/controlling/opos/verkaeufer`). Filter: Von/Bis, Verkäufer (nur für Berechtigte), Nur Fahrzeugverkauf. Verkäufer sehen nur eigene Posten; Navigation in base.html und DB-Migration `migrations/add_navigation_opos.sql`, Script `migrate_navigation_items.py` ergänzt.
- ✅ **OPOS Abgleich Locosoft (2026-02-19):** Wenn Kunde nicht in `loco_customers_suppliers` vorkommt, Anzeige „Kunde Nr. &lt;Nummer&gt;“ statt leer. Hinweis im Template und Doku **`OPOS/OPOS_ABGLEICH_LOCOSOFT.md`** für Vergleich mit Locosoft L362PR (Stichtag, Zeilen pro Buchung vs. pro Rechnung).
- ✅ **OPOS Auszifferung (2026-02-27):** DRIVE erkennt ausgezifferte Posten wie Locosoft: Offene Posten = „OP“ (clearing_number leer/0), bezahlte = Auszifferungsnummer. In `api/opos_api.py` werden nur noch Buchungszeilen mit **`clearing_number IS NULL OR clearing_number = 0`** in Kundensaldo und Offene-Posten-Liste einbezogen; Spalte „Art“ zeigt „OP“ + Fz/Sonst. Doku in `OPOS/OPOS_ABGLEICH_LOCOSOFT.md` ergänzt.
- ✅ **TEK Breakeven 4-Monats-Schnitt (2026-02-28):** Breakeven-Kosten („Ø Kosten“) basieren auf den **letzten 4 abgeschlossenen Kalendermonaten** (z. B. Februar → Okt, Nov, Dez, Jan). Statt rollierend „heute − 3 Monate bis heute“ → stabil ab Monatsanfang, schwankungsärmer. SSOT: `api/controlling_data.py` (`_letzte_4_abgeschlossene_monate()`, `berechne_breakeven_prognose`, `berechne_breakeven_prognose_standort`). Return-Keys: `kosten_4m_schnitt`, `kostenverteilung.kosten_gesamt_4m`; Template/Label: „4 Monate“ / „4M“.
- ✅ **TEK Datumsbug 2025-02-29 (2026-02-28):** Beim Vorjahr-Vergleich (VJ) „bis gleicher Tag“ wurde für den aktuellen Monat `vj_bis = vj_jahr-monat-(heute.day+1)` gebaut. An Tagen 28./29. Februar (z. B. 2026) entstand so das ungültige Datum 2025-02-29 (2025 kein Schaltjahr) → PostgreSQL „date/time field value out of range“. Fix: Letzten Tag im VJ-Monat per `calendar.monthrange(vj_jahr, monat)[1]` begrenzen, `vj_tag = min(heute.day, last_day_vj)`, dann `vj_bis = (date(vj_jahr, monat, vj_tag) + timedelta(days=1)).strftime(...)`. Angepasst in `api/controlling_data.py` (get_tek_data) und `routes/controlling_routes.py` (api_tek: vj_bis_bereich, vj_bis).
- ✅ **OPOS Stellantis Bank Verkäufer-Zuordnung (2026-02-27):** Für Kunde 1007422 (Stellantis Bank) steht in `sales` oft der Endkunde, nicht die Bank. Bei mehreren Verkäufen am gleichen Datum wird der Verkäufer per **Betragsnähe** (out_sale_price ~ saldo_eur) ermittelt, damit z. B. „Stellantis Bank / Petra Cornely 19.500 €“ korrekt Rafael zugeordnet wird. Doku in `OPOS/OPOS_ABGLEICH_LOCOSOFT.md`.
- ✅ **OPOS Rechnungsdetail-Modal (2026-02-27):** Klick auf Rechnungsnr. öffnet Modal mit Locosoft-Infos: FIBU-Buchungszeilen (loco_journal_accountings) und optional Rechnungskopf aus loco_invoices. API GET `/api/controlling/opos/rechnung-detail`; Response enthält `customer_number` für Detail-Aufruf.
- ✅ **TEK vs. VM / vs. VJ gleicher Zeitraum (2026-02-20):** Abweichungen „vs. VM“ und „vs. VJ“ waren zuvor irreführend (Teilmonat aktuell vs. Vollmonat VM/VJ). Anpassung in `routes/controlling_routes.py`: **VM** bei aktuellem Monat = erste N Tage des Vormonats (N = heutiger Kalendertag); **VJ** für Gesamt-Box und GESAMT-Zeile = bis gleicher Kalendertag (wie bereits pro Bereich). Abschnitt „TEK vs. VM / vs. VJ“ in CONTEXT.md auf „gleicher Zeitraum“ aktualisiert.
- ✅ **AfA Buchhaltung Christian (2026-02-20):** Option A bestätigt (Haben-Buchung manuell in Locosoft). **Abgang im Fahrzeug-Detail:** Bereich „Abgang buchen“ mit Abgangsdatum und optional Verkaufspreis; bei Datumseingabe zeigt DRIVE **aufgelaufene AfA** und Restbuchwert (API GET `/api/afa/fahrzeug/<id>/abgang-vorschau?datum=`); nach „Abgang buchen“ Erfolgsmeldung mit aufgelaufene AfA für Locosoft. CSV: „CSV exportieren“ = nur Opel/Leapmotor (ohne Hyundai), „CSV exportieren (Hyundai)“ = nur Betrieb 2. Doku `AfA/UMSETZUNGSVORSCHLAG_ABGANG_BUCHUNGEN.md` mit Konten-Matrix Verkauf/Umbuchung GW und Status-Update.
- ✅ **AfA Bestand E-Mail-Report (2026-02-25):** Automatischer Abgleich AfA-Bestand DRIVE/Locosoft mit E-Mail-Report umgesetzt. Report **„AfA Bestand Abgleich“** in Report-Verwaltung; Abonnenten konfigurierbar. Celery-Task `email_afa_bestand_report` (20:00 Mo–Fr); Script `scripts/send_afa_bestand_report.py`; Daten aus `api/afa_api.get_locosoft_kandidaten_data` und `get_abgangs_kontrolle_data`. Konzept: `AfA/UMSETZUNGSVORSCHLAG_AFA_BESTAND_EMAIL_REPORT.md`. Testversand und manueller Start (Admin → Celery → AfA Bestand Report) bestätigt.
- ✅ **TEK KST Detail-Modal: Vortag + Kumuliert (2026-02-26):** In den TEK-Bereichs-Detail-Modals (Umsatz-/Einsatz-Tabs) werden pro Erlös- bzw. Kostengruppe **Vortag** und **Kumuliert** mit je Einsatz, Erlös, DB1, DB% dargestellt. **Kontenbezogen wie GlobalCube:** Die aufgeklappte Konten-Tabelle (Konto, Bezeichnung) zeigt pro Konto ebenfalls Vortag- und Kumuliert-Spalten (Einsatz, Erlös, DB1, DB%). Backend: `vortag` mit `mit_konten=True`, sodass `vortag.umsatz.gruppen[].konten` und `vortag.einsatz.gruppen[].konten` pro Konto verfügbar sind. Frontend: innere Tabelle mit zwei Spaltenblöcken (Vortag | Kumuliert) pro Zeile.
- ✅ **Tagesumsätze/Erträge Locosoft 272/273 (2026-02-26):** Prüfung, ob die für L272PR (Fakturaanalyse Dienstleistung+ET) und L273PR (Fahrzeugrechnungen) benötigten Daten in der Locosoft-PostgreSQL verfügbar sind oder über SOAP SST bezogen werden können. **Ergebnis:** Die Rohdaten liegen in der Locosoft-PostgreSQL in den Tabellen `invoices`, `labours`, `parts`, `dealer_vehicles`; SOAP liefert keine 272/273. **Aktualität:** Für FIBU (`journal_accountings`) ist dokumentiert: Befüllung **täglich ca. 18–19 Uhr** – Buchungen vom heutigen Tag sind vor dem Abend-Lauf in der Regel **nicht** sichtbar. Ob `invoices`/`dealer_vehicles`/`labours`/`parts` tagesaktuell oder im gleichen Lauf befüllt werden, ist **nicht dokumentiert** – Klärung bei Locosoft empfohlen. Doku: **`TAGESUMSATZ_ERTRAG_LOCOSOFT_272_273_ANALYSE.md`** (inkl. Abschnitt „Aktualität“).
- ✅ **Session 2026-02-25 (Fahrzeugfinanzierungen / Zinsfreiheit):** (1) **Zinsfreiheit-Doku:** `ZINSFREIHEIT_STELLANTIS_HYUNDAI.md` – Stellantis (zinsfreiheit_tage aus Excel, Zinsen 9,03 % berechnet), Santander (Zins Startdatum + Zinsen aus CSV), Hyundai (Zinsbeginn aus CSV, zinsfreiheit_tage nicht in DB). (2) **Fahrzeugdetails „Typ“:** Anzeige aus Locosoft `out_sale_type` / `pre_owned_car_code` / `is_rental_or_school_vehicle` (wie Provisions-/AfA-Modul), nicht nur `dealer_vehicle_type`. (3) **Modell in Listen:** Stellantis/Santander/Hyundai-Listen und Warnungen/Top10/Fahrzeuge-mit-Zinsen mit Modell aus Locosoft angereichert, wenn DB leer. (4) **Kennzeichen:** Spalte `kennzeichen` in `fahrzeugfinanzierungen` (Migration), Sync aus Locosoft in `sync_stammdaten`/`sync_fahrzeug_stammdaten`. (5) **Hyundai CSV:** Spalte 9 = „Zinsbeginn“ auf Mount bestätigt, im Import bereits genutzt. (6) **Seite „nicht aufrufbar“ als Gast:** Erwartbar – APIs liefern bei nicht eingeloggt HTML (Login) statt JSON → Frontend-Fehler „is not valid JSON“. Nach Login funktioniert die Seite.

## Offene Entscheidungen

- (Keine festgehalten)

## TEK 4-Lohn: Rollierender Schnitt (SSOT)
- **Vereinbarung:** 4-Lohn-Einsatz im laufenden Monat = **rollierender 6-Monats-Schnitt** (Einsatz_aktuell = Umsatz_aktuell × (Einsatz_6M / Umsatz_6M)). SSOT: `api/controlling_data.get_tek_data`; siehe CLAUDE.md (SSOT für alle KPIs/Berechnungen) und `docs/TEK_LOHNKOSTEN_LOCOSOFT_6_MONATE.md`.
- **SSOT umgesetzt (2026-02-17):** Portal (api_tek) bezieht alle TEK-KPIs aus get_tek_data; 4-Lohn = rollierender Schnitt wie in Reports. Standort-DB1 (Deggendorf/Landau) ebenfalls aus get_tek_data(standort=1/2). Prognose aus api_data.prognose_detail.

## TEK 4-Lohn vs. Globalcube 40 % (2026-02)
- **Verbleibende Abweichung:** Globalcube nutzt **statisch 40 %** Einsatzquote (EW) für Service; Drive nutzt den **rollierenden 6-Monats-Schnitt**. Die Zahlenabweichung ist damit fachlich plausibel. Optional: 40 %-Option in Drive anbieten, wenn Abgleich gewünscht.

## TEK DB1 vs. Globalcube (2026-02-13)

- **Ausgangslage:** Erlöse/Umsätze Drive = Globalcube; DB1 weicht ab.
- **Analyse (ohne Code-Änderung):** `docs/workstreams/controlling/TEK_DB1_ABWEICHUNG_DRIVE_VS_GLOBALCUBE_ANALYSE.md`
- **Kernbefund:** Abweichung = Einsatz-Abweichung (DB1 = Umsatz − Einsatz). Drive TEK nutzt keinen G&V-Filter und schließt 743002 beim Einsatz nicht aus; BWA tut beides. 4-Lohn im laufenden Monat: Drive kalkulatorischer Einsatz (6-Monats-Quote). Nächster Schritt: Werte aus beiden PDFs pro Bereich vergleichen, Globalcube-Einsatz-Definition klären, dann ggf. get_tek_data anpassen.

## TEK vs. VM / vs. VJ (Vormonat / Vorjahr) – gleicher Zeitraum

- **Aktueller Monat (TEK):** Zeigt alle in Locosoft vorhandenen Buchungen im Monat (typ. 1. bis gestriges Datum, da Locosoft abends befüllt wird).
- **Vormonat (VM):** Im **Portal** (`controlling_routes`) wird bei **aktuellem Monat** nur der **gleiche Zeitraum** wie aktuell verwendet: erste N Tage des Vormonats (N = heutiger Kalendertag, max. letzter Tag des Vormonats). Bei vergangenen Monaten: voller Vormonat. So ist „vs. VM“ ein Vergleich gleicher Kalendertage (z. B. 1.–19. Feb vs. 1.–19. Jan).
- **Vorjahr (VJ):** Im **Portal** und in **get_tek_data (PDF/E-Mail)** wird VJ **bis zum gleichen Kalendertag** begrenzt (TAG146), wenn der anzeigende Monat der aktuelle ist; sonst voller Vorjahresmonat.
- **Fazit (Stand 2026-02-20):** Die Vergleiche „vs. VM“ und „vs. VJ“ sind im Portal auf den **gleichen Zeitraum** bezogen (erste N Tage / bis gleicher Tag), damit die Prozentabweichungen fachlich vergleichbar sind.

## TEK „Heute“ / tägliche Fakturierung (2026-02-12)

- **TEK Heute/Vortag** kommen aus **Buchungsdatum** (`journal_accountings.accounting_date`). FIBU-Buchungen NW/GW erscheinen oft mit Verzögerung (z. B. Folgetag). Daher kann „Heute“ auch dann 0/null sein, wenn am Tag tatsächlich verkauft wurde.
- **Tägliche Fakturierung** (Kundenzentrale) kommt aus **Rechnungsdatum** (`invoices.invoice_date`) – ist tagesaktuell. Diagnose-Script: `scripts/check_tek_heute_fakturierung.py`.
- **Option:** Tägliche Fakturierung (invoices) zusätzlich oder als Fallback zu „Heute“ anzeigen, damit die Anzeige nicht null bleibt (mit Kennzeichnung „Fakturierung (Rechnungsdatum)“).

## Kontenübersicht – Sachkonten Locosoft (070101, 071101)

- **Quelle:** Saldo wird bei jedem Aufruf **live** aus der Locosoft-PostgreSQL-DB geholt (`journal_accountings`, Kontonummer 70101 bzw. 71101). Kein Mirror, kein Cache.
- **Aktualität:** So aktuell wie die Locosoft-DB. Locosoft befüllt seine DB typischerweise **täglich ca. 18:00–19:00 Uhr** (externe Abhängigkeit). Danach zeigt die Kontenübersicht den Stand von Locosoft.
- **Code:** `api/bankenspiegel_api.py` (Saldo 070101/071101 per `locosoft_session()`).

## Abhängigkeiten

- Infrastruktur (PostgreSQL, Celery), ggf. auth-ldap für Berechtigungen
