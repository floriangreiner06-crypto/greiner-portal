# CURSOR PROMPT: Cashflow / Liquiditätsplanung – Datenbasis-Analyse

## Aufgabe

Wir wollen im DRIVE Portal ein neues Modul **„Cashflow-Status & Liquiditätsprognose"** bauen.
Bevor wir mit der Implementierung beginnen, sollst du zunächst **systematisch analysieren, welche Daten tatsächlich vorhanden und sauber zuordenbar sind** – und wo wir nachbessern oder neue Quellen erschließen müssen.

**Kein Code schreiben. Nur analysieren, prüfen, dokumentieren.**

---

## Kontext zum System

- **DRIVE Portal** = Flask-ERP für Autohaus Greiner (Opel/Stellantis, Hyundai, Leapmotor)
- **3 Standorte:** Deggendorf Stellantis (1), Deggendorf Hyundai (2), Landau (3)
- **2 Datenbanken:**
  - **`drive_portal`** (PostgreSQL, 127.0.0.1) – Banken, Konten, Transaktionen, Salden, Finanzierungen, Tilgungen. Locosoft-Daten werden hier als **Spiegel** in Tabellen mit Prefix `loco_` geführt (z. B. `loco_journal_accountings`, `loco_dealer_vehicles`, `loco_invoices`, `loco_orders`).
  - **`loco_auswertung_db`** (PostgreSQL, 10.80.80.8, read-only) – Locosoft DMS direkt; Tabellen **ohne** `loco_`-Prefix (z. B. `journal_accountings`, `dealer_vehicles`).

**Arbeitsweise (verbindlich):**
- **Server = Master:** Entwicklung auf dem Server unter `/opt/greiner-portal/`.
- **Kein SQLite:** Alle DB-Zugriffe über PostgreSQL (siehe docs/NO_SQLITE.md).
- **SSOT:** Jede Kennzahl/Berechnung hat eine definierte Quelle; keine parallelen Berechnungen.
- **Workstream:** Dieses Thema gehört zum Workstream **Controlling**. Doku: `docs/workstreams/controlling/CONTEXT.md`, `PLAN_LIQUIDITAET_KATEGORISIERUNG_TILGUNGEN.md`, `CASHFLOW_VORSCHAU_WEBANALYSE.md`.
- **Output:** Audit-Dokument in **`docs/workstreams/controlling/CASHFLOW_DATA_AUDIT.md`** (nicht in `docs/` root).

### DB-Verbindungen

```bash
# DRIVE Portal (lokal) – hier: konten, transaktionen, salden, v_aktuelle_kontostaende, fahrzeugfinanzierungen, tilgungen, loco_*
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal

# Locosoft (extern, optional für direkte Abfragen) – journal_accountings, nominal_accounts, customers_suppliers, dealer_vehicles, invoices, orders
PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db
```

**Hinweis:** Für die Analyse reicht in der Regel **drive_portal**: Dort liegen `transaktionen`, `konten`, `salden`, `fahrzeugfinanzierungen`, `tilgungen` sowie die Locosoft-Spiegel `loco_journal_accountings`, `loco_nominal_accounts`, `loco_customers_suppliers`, `loco_dealer_vehicles`, `loco_invoices`, `loco_orders`. Wenn du die **direkte** Locosoft-DB (10.80.80.8) nutzt, heißen die Tabellen **ohne** Prefix `loco_` (z. B. `journal_accountings` statt `loco_journal_accountings`).

---

## Wichtige Schema-Hinweise (DRIVE)

- **Konten/Salden:** Salden stehen **nicht** in `konten`, sondern in der Tabelle **`salden`** (konto_id, saldo, datum) bzw. in der View **`v_aktuelle_kontostaende`** (pro Konto neuester Saldo + letztes_update). `konten` enthält u. a. id, bank_id, kontoname, iban, kontonummer, kreditlinie, aktiv, kontoinhaber, sort_order.
- **Transaktionen:** Tabelle **`transaktionen`** – Spalten u. a.: id, konto_id, buchungsdatum, valutadatum, betrag, buchungstext, verwendungszweck, gegenkonto_iban, **gegenkonto_name** (nicht „auftraggeber_empfaenger“), kategorie, unterkategorie, import_quelle, import_datei. Für Auswertungen „Auftraggeber/Empfänger“ bitte **gegenkonto_name** (und ggf. buchungstext/verwendungszweck) nutzen.
- **Locosoft FIBU (Spiegel):** Tabelle **`loco_journal_accountings`** (in drive_portal). Werte in **Cent** (`posted_value` / 100.0 = Euro). Sachkonten im DRIVE **6-stellig** (z. B. 74xxxx Personal/Lohn, 8xxxxx Erlöse). Personalkosten: `nominal_account_number BETWEEN 740000 AND 749999` (ohne 747301 Clean Park) – siehe `api/controlling_data.py`. Nicht 6xxx (4-stellig) verwenden.
- **Fahrzeugeinkauf/Erlöse:** Erlöse 8xxxxx, Einsatz/Kosten 7xxxxx. Siehe CONTEXT.md und controlling_data.py für exakte Bereiche.

---

## Was ein Cashflow-Modul braucht

### EINNAHMEN (die wir prognostizieren wollen)

| # | Kategorie | Beschreibung |
|---|-----------|--------------|
| E1 | Fahrzeugverkäufe NW/GW | Kaufpreiszahlungen bei Auslieferung |
| E2 | Werkstatt-/Serviceerlöse | Abgerechnete Aufträge |
| E3 | Teilehandel | Teileverkäufe |
| E4 | **Hersteller-Abschläge / Boni** | Monatliche/quartalsweise Abschlagszahlungen von Stellantis und Hyundai auf Jahresziele (Händlerbetriebsvergleich, Volumenziele etc.) – regelmäßige Einnahmen, die vorher absehbar sein sollten |
| E5 | Aktionsbeteiligungen / Verkaufshilfen | Einmalige Herstellerzahlungen je verkauftem Fahrzeug |
| E6 | Finanzierungs-/Leasingprovisionen | Provisionen aus Leasys, Santander etc. |
| E7 | Garantie-/Kulanz-Erstattungen | Herstellererstattungen für Garantiearbeiten |

### AUSGABEN (die wir prognostizieren wollen)

| # | Kategorie | Beschreibung |
|---|-----------|--------------|
| A1 | **Fahrzeugeinkauf** | Zahlungen an Stellantis/Hyundai für gelieferte Fahrzeuge |
| A2 | **Personal / Gehälter** | Monatliche Lohn-/Gehaltszahlungen inkl. Sozialabgaben – in Locosoft als Kostenbuchungen (74xxxx) vorhanden |
| A3 | **Einkaufsfinanzierung (Zinsen)** | Monatliche Zinsen Stellantis Bank / Santander / Hyundai Finance – in `fahrzeugfinanzierungen` abgebildet |
| A4 | Teileeinkauf | Wareneingang Ersatzteile |
| A5 | Mieten / Leasingkosten | Immobilien, Fahrzeuge, Geräte |
| A6 | USt-Voranmeldung | Monatliche/quartalsweise Umsatzsteuer-Abführung |
| A7 | Steuervorauszahlungen | Körperschaftsteuer, Gewerbesteuer (quartalsweise) |
| A8 | Versicherungen | Gewerbliche Versicherungen |
| A9 | Sonstige Betriebskosten | Energie, IT, Telefon etc. |

---

## Deine Analyse-Aufgabe (Schritt für Schritt)

### SCHRITT 1: IST-Status – Kontosalden und Aktualität

In **drive_portal** – Salden kommen aus View **v_aktuelle_kontostaende** bzw. Tabelle **salden** (nicht aus konten.aktueller_saldo):

```sql
-- View-Struktur prüfen (falls vorhanden)
SELECT * FROM v_aktuelle_kontostaende LIMIT 5;

-- Konten mit Kreditlinien (Saldo aus View/Subquery)
SELECT k.id, k.kontoname, k.iban, k.kontonummer, k.kreditlinie,
       v.saldo AS aktueller_saldo, v.letztes_update
FROM konten k
LEFT JOIN v_aktuelle_kontostaende v ON v.konto_id = k.id
WHERE k.aktiv = true
ORDER BY k.kontoname;

-- Tagesaktueller Gesamtsaldo
SELECT
    SUM(saldo) AS gesamtsaldo,
    SUM(COALESCE(kreditlinie, 0)) AS gesamte_kreditlinien,
    MAX(letztes_update) AS zuletzt_aktualisiert
FROM v_aktuelle_kontostaende;
```

**Frage:** Sind die Salden tagesfrisch? Wie weit hinken die Bankimporte (MT940/PDF) hinterher? Quelle der Salden: MT940-Import schreibt in `transaktionen` und aktualisiert `salden` (siehe `api/bankenspiegel_utils.create_snapshot_from_saldo`).

---

### SCHRITT 2: Transaktionen – Kategorisierung und Muster

**Spalten in `transaktionen`:** id, konto_id, buchungsdatum, valutadatum, betrag, buchungstext, verwendungszweck, gegenkonto_iban, **gegenkonto_name**, kategorie, unterkategorie, import_quelle, import_datei. Kein „auftraggeber_empfaenger“ – stattdessen **gegenkonto_name** verwenden.

```sql
-- Struktur prüfen
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'transaktionen'
ORDER BY ordinal_position;

-- Zeitraum und Volumen
SELECT
    MIN(buchungsdatum) AS erste_buchung,
    MAX(buchungsdatum) AS letzte_buchung,
    COUNT(*) AS gesamt,
    COUNT(CASE WHEN kategorie IS NOT NULL AND kategorie != '' THEN 1 END) AS kategorisiert,
    COUNT(CASE WHEN kategorie IS NULL OR kategorie = '' THEN 1 END) AS unkategorisiert
FROM transaktionen;

-- Top-Ausgaben-Empfänger (gegenkonto_name; wiederkehrend = gut für Prognose)
SELECT
    gegenkonto_name,
    COUNT(*) AS anzahl_buchungen,
    ROUND(AVG(ABS(betrag))::numeric, 2) AS durchschnittsbetrag,
    MIN(buchungsdatum) AS erste,
    MAX(buchungsdatum) AS letzte,
    kategorie
FROM transaktionen
WHERE betrag < 0
GROUP BY gegenkonto_name, kategorie
HAVING COUNT(*) >= 6
ORDER BY COUNT(*) DESC
LIMIT 40;

-- Top-Einnahmen-Quellen
SELECT
    gegenkonto_name,
    COUNT(*) AS anzahl_buchungen,
    ROUND(AVG(betrag)::numeric, 2) AS durchschnittsbetrag,
    kategorie
FROM transaktionen
WHERE betrag > 0
GROUP BY gegenkonto_name, kategorie
HAVING COUNT(*) >= 3
ORDER BY COUNT(*) DESC
LIMIT 30;
```

**Frage:** Sind Stellantis/Opel-Zahlungseingänge (Hersteller-Abschläge) im Bankenspiegel erkennbar? Wenn ja, mit welchem Gegenkonto-Namen und Verwendungszweck?

---

### SCHRITT 3: Locosoft – Personalkosten (Gehälter)

In **drive_portal** Tabelle **loco_journal_accountings** (oder direkt Locosoft: journal_accountings). Personalkosten: **nominal_account_number BETWEEN 740000 AND 749999** (ohne 747301 Clean Park). `posted_value` in **Cent** → `/ 100.0` für Euro.

```sql
-- Personalkosten-Konten (6-stellig, 74xxxx)
SELECT DISTINCT
    ja.nominal_account_number,
    na.account_description,
    COUNT(*) AS buchungen,
    SUM(ja.posted_value) / 100.0 AS summe_euro
FROM loco_journal_accountings ja
LEFT JOIN loco_nominal_accounts na
    ON ja.nominal_account_number = na.nominal_account_number
   AND ja.subsidiary_to_company_ref = na.subsidiary_to_company_ref
WHERE ja.nominal_account_number BETWEEN 740000 AND 749999
  AND ja.nominal_account_number != 747301
  AND ja.accounting_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY ja.nominal_account_number, na.account_description
ORDER BY SUM(ABS(ja.posted_value)) DESC
LIMIT 20;

-- Monatliche Lohnkosten (letzte 12 Monate) – für Prognose-Baseline
SELECT
    EXTRACT(YEAR FROM accounting_date) AS jahr,
    EXTRACT(MONTH FROM accounting_date) AS monat,
    subsidiary_to_company_ref AS standort_ref,
    SUM(posted_value) / 100.0 AS lohnkosten_euro
FROM loco_journal_accountings
WHERE nominal_account_number BETWEEN 740000 AND 749999
  AND nominal_account_number != 747301
  AND accounting_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2 DESC, 3
LIMIT 50;
```

**Hinweis:** `subsidiary_to_company_ref` in Locosoft entspricht nicht zwingend 1/2/3 wie in DRIVE – Mapping ggf. prüfen (siehe CONTEXT.md Standort-Mapping).

**Frage:** Sind die monatlichen Lohnkosten stabil genug für eine Prognose? An welchem Tag des Monats werden die Gehälter typischerweise gebucht (Buchungsdatum)?

---

### SCHRITT 4: Locosoft – Hersteller-Abschläge (KRITISCH)

Stellantis und Hyundai zahlen regelmäßige **Abschlagszahlungen auf Jahresziele**. In der FIBU als Erlös oder Erlösschmälerung gebucht. Sachkonten für Erlöse/Boni im DRIVE typisch **8xxxxx** (siehe controlling_data.py). Suche nach Konten und Buchungstexten:

```sql
-- Konten mit nennenswerten Beträgen (Erlöse/Boni-Bereich, 6-stellig)
SELECT DISTINCT
    ja.nominal_account_number,
    na.account_description,
    SUM(ja.posted_value) / 100.0 AS jahressumme_euro,
    COUNT(*) AS buchungen
FROM loco_journal_accountings ja
LEFT JOIN loco_nominal_accounts na
    ON ja.nominal_account_number = na.nominal_account_number
   AND ja.subsidiary_to_company_ref = na.subsidiary_to_company_ref
WHERE ja.accounting_date >= CURRENT_DATE - INTERVAL '12 months'
  AND ABS(ja.posted_value) > 100000
GROUP BY ja.nominal_account_number, na.account_description
ORDER BY ABS(SUM(ja.posted_value)) DESC
LIMIT 50;

-- Buchungstexte, die auf Hersteller-Abschläge hindeuten
SELECT
    nominal_account_number,
    accounting_date,
    posting_text,
    free_form_accounting_text,
    vehicle_reference,
    posted_value / 100.0 AS betrag_euro,
    subsidiary_to_company_ref
FROM loco_journal_accountings
WHERE (
    LOWER(COALESCE(posting_text,'')) LIKE '%abschlag%' OR
    LOWER(COALESCE(posting_text,'')) LIKE '%bonus%' OR
    LOWER(COALESCE(posting_text,'')) LIKE '%nachverg%' OR
    LOWER(COALESCE(posting_text,'')) LIKE '%jahresboni%' OR
    LOWER(COALESCE(posting_text,'')) LIKE '%stellantis%' OR
    LOWER(COALESCE(posting_text,'')) LIKE '%opel%' OR
    LOWER(COALESCE(posting_text,'')) LIKE '%hyundai%' OR
    LOWER(COALESCE(free_form_accounting_text,'')) LIKE '%abschlag%' OR
    LOWER(COALESCE(free_form_accounting_text,'')) LIKE '%bonus%'
)
AND accounting_date >= CURRENT_DATE - INTERVAL '24 months'
ORDER BY accounting_date DESC
LIMIT 30;

-- Kunden/Lieferanten-Seite: Hersteller als Gegenpartei
SELECT
    cs.family_name AS name,
    COUNT(*) AS buchungen,
    SUM(ja.posted_value) / 100.0 AS summe
FROM loco_journal_accountings ja
LEFT JOIN loco_customers_suppliers cs ON ja.customer_number = cs.customer_number
WHERE (
    LOWER(COALESCE(cs.family_name,'')) LIKE '%stellantis%' OR
    LOWER(COALESCE(cs.family_name,'')) LIKE '%opel%' OR
    LOWER(COALESCE(cs.family_name,'')) LIKE '%hyundai%' OR
    LOWER(COALESCE(cs.family_name,'')) LIKE '%automobil%'
)
AND ja.accounting_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY cs.family_name
ORDER BY SUM(ABS(ja.posted_value)) DESC
LIMIT 20;
```

**Frage:** Unter welchem Kontonamen/Buchungstext tauchen die Stellantis-Abschläge auf? Monatlich oder quartalsweise? Stellantis und Hyundai trennbar?

---

### SCHRITT 5: Locosoft – Fahrzeugeinkauf und geplante Lieferungen

Wareneinkauf Fahrzeuge: Sachkonten typisch **2xxxxx** (SKR51) oder im DRIVE 6-stellig – zuerst Kontenbereich in loco_nominal_accounts prüfen. Geplante Anlieferungen: **loco_dealer_vehicles** (bzw. dealer_vehicles auf 10.80.80.8).

```sql
-- Monatliche Einkaufskosten (Kontenklasse 2 – Wareneinkauf; ggf. 6-stellig anpassen)
SELECT
    ja.nominal_account_number,
    na.account_description,
    EXTRACT(YEAR FROM ja.accounting_date) AS jahr,
    EXTRACT(MONTH FROM ja.accounting_date) AS monat,
    SUM(ja.posted_value) / 100.0 AS summe_euro
FROM loco_journal_accountings ja
LEFT JOIN loco_nominal_accounts na
    ON ja.nominal_account_number = na.nominal_account_number
   AND ja.subsidiary_to_company_ref = na.subsidiary_to_company_ref
WHERE ja.nominal_account_number::text LIKE '2%'
  AND LENGTH(ja.nominal_account_number::text) >= 5
  AND ja.accounting_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY 1, 2, 3, 4
ORDER BY ABS(SUM(ja.posted_value)) DESC
LIMIT 20;

-- Geplante Fahrzeuganlieferungen (loco_dealer_vehicles in drive_portal)
SELECT
    in_expected_arrival_date,
    in_buy_list_price,
    in_order_status,
    in_subsidiary
FROM loco_dealer_vehicles
WHERE in_expected_arrival_date >= CURRENT_DATE
  AND in_order_status IS NOT NULL
ORDER BY in_expected_arrival_date
LIMIT 30;
```

---

### SCHRITT 6: Locosoft – Werkstatt-Erlöse (Prognose-Basis)

```sql
-- Monatliche Werkstatt-Ist-Erlöse (loco_invoices; Spaltennamen ggf. prüfen)
SELECT
    EXTRACT(YEAR FROM invoice_date) AS jahr,
    EXTRACT(MONTH FROM invoice_date) AS monat,
    subsidiary,
    COUNT(*) AS rechnungen,
    SUM(total_gross) AS umsatz_brutto,
    AVG(total_gross) AS durchschnitt_rechnung
FROM loco_invoices
WHERE invoice_date >= CURRENT_DATE - INTERVAL '24 months'
  AND is_canceled = false
  AND total_gross > 0
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2 DESC, 3
LIMIT 36;

-- Offene Aufträge (loco_orders; Spalten ggf. prüfen)
SELECT
    subsidiary,
    COUNT(*) AS offene_auftraege,
    COUNT(CASE WHEN estimated_outbound_time <= NOW() + INTERVAL '7 days' THEN 1 END) AS faellig_7_tage,
    COUNT(CASE WHEN estimated_outbound_time <= NOW() + INTERVAL '30 days' THEN 1 END) AS faellig_30_tage
FROM loco_orders
WHERE has_open_positions = true
  AND has_closed_positions = false
GROUP BY subsidiary;
```

**Hinweis:** Exakte Spaltennamen in `loco_invoices` und `loco_orders` in `docs/DB_SCHEMA_LOCOSOFT.md` prüfen (z. B. total_gross, estimated_outbound_time, has_open_positions).

---

### SCHRITT 7: DRIVE Portal – Einkaufsfinanzierung (Zinsen)

In **drive_portal** (kein Locosoft):

```sql
-- Monatliche Zinslast (Spaltennamen in fahrzeugfinanzierungen prüfen)
SELECT
    finanzinstitut AS bank,
    COUNT(*) AS fahrzeuge,
    SUM(finanzierungsbetrag) AS gesamtvolumen,
    AVG(zins_aktuell) AS durchschnittszins,
    SUM(finanzierungsbetrag * NULLIF(zins_aktuell, 0) / 100.0 / 12) AS zinsen_pro_monat_geschaetzt
FROM fahrzeugfinanzierungen
WHERE status = 'aktiv' OR aktiv = true
GROUP BY finanzinstitut;

-- Tilgungsplan (tilgungen)
SELECT MIN(faellig_am), MAX(faellig_am), COUNT(*), SUM(betrag)
FROM tilgungen
WHERE faellig_am >= CURRENT_DATE;
```

**Hinweis:** Spalten in `fahrzeugfinanzierungen` können `finanzinstitut` oder `bank` heißen; `aktiv` oder `status` – zuerst Struktur abfragen.

---

### SCHRITT 8: Mieten und sonstige Fixkosten – aus Transaktionen

Wiederkehrende Ausgaben aus **transaktionen** (gegenkonto_name, verwendungszweck):

```sql
SELECT
    gegenkonto_name,
    LEFT(verwendungszweck, 80) AS verwendungszweck,
    COUNT(*) AS buchungen_gesamt,
    ROUND(AVG(ABS(betrag))::numeric, 2) AS ø_betrag,
    MIN(buchungsdatum) AS erste,
    MAX(buchungsdatum) AS letzte
FROM transaktionen
WHERE betrag < 0
  AND buchungsdatum >= CURRENT_DATE - INTERVAL '24 months'
GROUP BY gegenkonto_name, LEFT(verwendungszweck, 80)
HAVING COUNT(*) >= 12
ORDER BY AVG(ABS(betrag)) DESC
LIMIT 30;
```

---

### SCHRITT 9: USt-Voranmeldungen

USt-Konten in FIBU (Locosoft): typisch 1776, 1771, 1780, 1790 oder Bezeichnungen mit „Umsatzsteuer“/„Vorsteuer“. In Locosoft 6-stellig möglich – zuerst nominal_accounts sichten.

```sql
SELECT
    ja.nominal_account_number,
    na.account_description,
    EXTRACT(YEAR FROM ja.accounting_date) AS jahr,
    EXTRACT(MONTH FROM ja.accounting_date) AS monat,
    SUM(ja.posted_value) / 100.0 AS summe_euro
FROM loco_journal_accountings ja
LEFT JOIN loco_nominal_accounts na
    ON ja.nominal_account_number = na.nominal_account_number
   AND ja.subsidiary_to_company_ref = na.subsidiary_to_company_ref
WHERE (
    na.account_description ILIKE '%umsatzsteuer%' OR
    na.account_description ILIKE '%vorsteuer%' OR
    na.account_description ILIKE '%finanzamt%' OR
    ja.nominal_account_number IN (1776, 1771, 1780, 1790)
)
AND ja.accounting_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY 1, 2, 3, 4
ORDER BY 3 DESC, 4 DESC, 1
LIMIT 30;
```

---

## HINWEISE & CONSTRAINTS

- **posted_value** in loco_journal_accountings: **Cent** (Integer) → immer `/ 100.0` für Euro.
- **loco_journal_accountings** hat ~600.000 Zeilen → immer sinnvolles `WHERE` + `LIMIT`.
- **debit_or_credit:** 'D' = Soll, 'C' = Haben (Bedeutung je Kontenart unterschiedlich).
- **subsidiary_to_company_ref** in Locosoft ≠ direkt 1/2/3 wie in DRIVE – Mapping in CONTEXT.md prüfen.
- **transaktionen:** Kein `auftraggeber_empfaenger` → **gegenkonto_name** (und buchungstext, verwendungszweck) nutzen.
- **Salden:** Aus **salden** bzw. **v_aktuelle_kontostaende**, nicht aus konten.aktueller_saldo.
- **Sachkonten:** Im DRIVE/Locosoft-Spiegel **6-stellig** (74xxxx Lohn, 8xxxxx Erlöse). Siehe `api/controlling_data.py` und `docs/DB_SCHEMA_LOCOSOFT.md`.
- **Cash-Relevanz:** Fokus auf tatsächlichen Geldfluss. Buchungsdatum kann vom Zahlungsdatum abweichen.

---

## Erwartetes Output-Dokument

Erstelle **`docs/workstreams/controlling/CASHFLOW_DATA_AUDIT.md`** mit folgender Struktur:

```markdown
# Cashflow Data Audit – DRIVE Portal
**Datum:** [heute]

## ✅ VORHANDEN & DIREKT NUTZBAR
Für jede Kategorie: Quelle, Tabelle/Spalte, Datenqualität, Beispielwerte

## ⚠️ VORHANDEN, ABER AUFBEREITUNG NÖTIG
Für jede Kategorie: Problem, vorgeschlagene Lösung, Aufwand

## ❌ NICHT AUTOMATISIERBAR – MANUELLE PFLEGE NÖTIG
Für jede Kategorie: Warum nicht automatisch, was müsste einmalig konfiguriert werden

## ❓ UNGEKLÄRT – RÜCKFRAGEN AN FLORIAN
Offene Fragen (z. B. "Unter welchem Namen bucht Stellantis die monatlichen Abschläge?")

## 📊 DATENQUALITÄTS-ZUSAMMENFASSUNG
Kurze Tabelle: Kategorie | Quelle | Verfügbar | Qualität (1-5) | Anmerkung

## 🗓️ EMPFOHLENE IMPLEMENTIERUNGS-REIHENFOLGE
Phase 1 (sofort umsetzbar): ...
Phase 2 (nach manueller Konfiguration): ...
Phase 3 (mittelfristig): ...
```

**Wichtig:** Nur echte Befunde dokumentieren – mit Zeilenzahlen, Datumsräumen und konkreten Beispielwerten aus den Daten. Keine Annahmen oder Vermutungen.

---

## Weitere Lektüre im Projekt

- `docs/workstreams/controlling/PLAN_LIQUIDITAET_KATEGORISIERUNG_TILGUNGEN.md` – Kategorisierung, Tilgungsmuster, nächste Schritte.
- `docs/workstreams/controlling/CASHFLOW_VORSCHAU_WEBANALYSE.md` – Warum wir keine fertigen Tools übernehmen, sondern im DRIVE bauen.
- `docs/DB_SCHEMA_POSTGRESQL.md` – drive_portal Tabellenübersicht.
- `docs/DB_SCHEMA_LOCOSOFT.md` – Locosoft-Spalten (journal_accountings, dealer_vehicles, invoices, orders).
