# Controlling (BWA, Bankenspiegel, Finanzreporting) — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-19

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

## TEK vs. VM / vs. VJ (Vormonat / Vorjahr) – Werktagestand

- **Aktueller Monat (TEK):** Zeigt alle in Locosoft vorhandenen Buchungen im Monat (typ. 1. bis gestriges Datum, da Locosoft abends befüllt wird).
- **Vormonat (VM):** Im Portal und in `get_tek_data` wird der **komplette** Vormonat verwendet (alle Tage Januar, nicht „erste N Werktage“).
- **Vorjahr (VJ):** Im **Portal** (`controlling_routes`) wird der **komplette** Vorjahresmonat verwendet. In **get_tek_data (PDF/E-Mail)** wird VJ **bis zum gleichen Kalendertag** begrenzt (TAG146).
- **Fazit:** Die Vergleiche „vs. VM“ und „vs. VJ“ sind **nicht** auf den gleichen Werktagestand bezogen: aktueller Monat = Teilmonat (z. B. 12 Werktage), VM/VJ = Vollmonat. Für einen werktage-basierten Vergleich (z. B. „erste 12 WT Feb 26“ vs. „erste 12 WT Jan 26“ vs. „erste 12 WT Feb 25“) müsste die Logik in `controlling_routes` und ggf. in `get_tek_data` erweitert werden.

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
