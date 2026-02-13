# Controlling (BWA, Bankenspiegel, Finanzreporting) — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-13

## Beschreibung

Controlling umfasst BWA-Berechnung, Bankenspiegel mit Konten und Transaktionen, TEK (Tägliche Erfolgskontrolle), den Finanzreporting-Cube sowie Kontenmapping. MT940/CAMT/PDF-Import, Umsatz-Bereinigung, Stundensatz-Kalkulation und Zins-Optimierung gehören ebenfalls in diesen Workstream.

## Module & Dateien

### APIs
- `api/bankenspiegel_api.py` — Dashboard, Konten, Transaktionen, Einkaufsfinanzierung, Fahrzeuge mit Zinsen
- `api/controlling_api.py` — BWA, BWA v2, Drilldown, DB1-Entwicklung
- `api/controlling_data.py` — Datenlayer BWA, TEK (get_tek_data)
- `api/finanzreporting_api.py` — Finanzreporting-Cube
- `api/kontenmapping_api.py` — Kontenmapping
- `api/stundensatz_kalkulation_api.py` — Stundensatz-Kalkulation
- `api/zins_optimierung_api.py` — Zins-Optimierung

### Templates
- `templates/bankenspiegel_*.html`
- `templates/controlling/*.html` (inkl. TEK-Dashboard: `tek_dashboard.html`, `tek_dashboard_v2.html`)

### Parser / Daten
- `parsers/` — MT940, CAMT, PDF-Import

### Celery Tasks
- `import_mt940`, `import_hvb_pdf`, `umsatz_bereinigung`, `bwa_berechnung`, `refresh_finanzreporting_cube`, `email_tek_daily`

## DB-Tabellen (PostgreSQL drive_portal)

- `konten`, `banken`, `transaktionen`, `daily_balances`, `kategorien`, `kreditlinien`, `fibu_buchungen`, `bwa_monatswerte`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ **Workstream-Zuordnung (2026-02-12):** TEK dem Workstream Controlling zugeordnet (Scope, Module/Templates/Celery in CONTEXT.md; CLAUDE.md und .cursorrules angepasst).
- ✅ Bankenspiegel, BWA, TEK-Dashboard, Finanzreporting-Cube im Einsatz
- ✅ MT940/HVB-PDF-Import, Umsatz-Bereinigung
- 🔧 Kontenmapping und Stundensatz-Kalkulation je nach Projektstand
- ✅ **Kontenübersicht Locosoft (2026-02-13):** Klärung, wann Sachkonto 070101/071101 aktualisiert wird (live aus Locosoft bei jedem Aufruf; Locosoft-DB-Befüllung ca. 18–19 Uhr). Doku in CONTEXT.md ergänzt. Bestätigung: DRIVE-Saldo war korrekt, Typo in manueller Buchhaltungsauswertung.
- ✅ **Umlaut-Darstellung BWA/TEK-Modale (2026-02-13):** Zeichenfehler („ErlÄtise“ statt „Erlöse“) behoben. Ursache war Moji­bake in `routes/controlling_routes.py` (UTF-8-Zeichen fälschlich als Latin-1 gespeichert). Korrektur: alle gruppen_namen, SKR51_KONTOBEZEICHNUNGEN und weiteren Umlaute (ö, ä, ü, ß, €, Ø) in der Datei auf korrektes UTF-8 gestellt.
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## TEK 4-Lohn: 6-Monats-Quote vs. Globalcube 40 % (2026-02)
- **Verbleibende Abweichung:** Globalcube nutzt **statisch 40 %** Einsatzquote (EW) für Service; Drive nutzt die **6-Monats-Durchschnitts-Quote**. Die Zahlenabweichung ist damit fachlich plausibel. Optional: 40 %-Option in Drive anbieten, wenn Abgleich gewünscht.

## TEK DB1 vs. Globalcube (2026-02-13)

- **Ausgangslage:** Erlöse/Umsätze Drive = Globalcube; DB1 weicht ab.
- **Analyse (ohne Code-Änderung):** `docs/workstreams/controlling/TEK_DB1_ABWEICHUNG_DRIVE_VS_GLOBALCUBE_ANALYSE.md`
- **Kernbefund:** Abweichung = Einsatz-Abweichung (DB1 = Umsatz − Einsatz). Drive TEK nutzt keinen G&V-Filter und schließt 743002 beim Einsatz nicht aus; BWA tut beides. 4-Lohn im laufenden Monat: Drive kalkulatorischer Einsatz (6-Monats-Quote). Nächster Schritt: Werte aus beiden PDFs pro Bereich vergleichen, Globalcube-Einsatz-Definition klären, dann ggf. get_tek_data anpassen.

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
