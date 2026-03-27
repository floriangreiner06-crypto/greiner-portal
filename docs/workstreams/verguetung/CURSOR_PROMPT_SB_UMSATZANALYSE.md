# Workstream: Vergütung — Serviceberater-Umsatzanalyse 2025

## Kontext

Lies zuerst:
1. `WORKFLOW.md` (Root) — Arbeitsregeln
2. `CLAUDE.md` (Root) — Projekt-Kontext
3. `docs/DB_SCHEMA_LOCOSOFT.md` — Locosoft-Tabellenstruktur
4. `docs/workstreams/werkstatt/CONTEXT.md` — Werkstatt-Kontext (dort sind die relevanten Tabellen dokumentiert)
5. `config/.env` — DB-Zugangsdaten

Wir arbeiten direkt auf **10.80.80.20** unter `/opt/greiner-portal/`. Kein Sync nötig.

## Aufgabe

Ermittle den Umsatz (Lohn + Teile) pro Serviceberater für den Zeitraum **Januar bis Dezember 2025** aus der Locosoft PostgreSQL-Datenbank.

Die vier Serviceberater sind:
- **Herbert Huber**
- **Valentin Salmansberger**
- **Andreas Kraus**
- **Leo Keidl**

### Hintergrund

Wir bauen ein Prämiensystem für den Service-Bereich (siehe `docs/workstreams/verguetung/`). Dafür brauchen wir Ist-Daten, wie viel Umsatz (Lohn + Teile) jeder Serviceberater erwirtschaftet. Branchenrichtwert: 800.000–1.000.000 €/Jahr pro SB (Lohn + Teile zusammen).

## Vorgehensweise

### Schritt 0: Schema lesen

```bash
cat /opt/greiner-portal/docs/DB_SCHEMA_LOCOSOFT.md
```

Prüfe: Welche Spalten haben `orders`, `labours`, `employees`? Insbesondere: Wie wird der Serviceberater dem Auftrag zugeordnet?

### Schritt 1: SB-Spalte in orders finden

Wir wissen NICHT sicher, welche Spalte in `orders` den Serviceberater referenziert. Discovery:

```sql
-- Alle Spalten von orders
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'orders'
ORDER BY ordinal_position;

-- SB-relevante Spalten suchen
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'orders'
AND (column_name ILIKE '%advisor%'
  OR column_name ILIKE '%berater%'
  OR column_name ILIKE '%service%'
  OR column_name ILIKE '%employee%'
  OR column_name ILIKE '%clerk%'
  OR column_name ILIKE '%accept%');
```

### Schritt 2: Die 4 SBs in employees finden

```sql
SELECT employee_number, first_name, last_name,
       mechanic_number, sales_advisor_number, subsidiary
FROM employees
WHERE (last_name ILIKE '%huber%' AND first_name ILIKE '%herb%')
   OR (last_name ILIKE '%salmansberger%')
   OR (last_name ILIKE '%kraus%' AND first_name ILIKE '%andr%')
   OR (last_name ILIKE '%keidl%');
```

### Schritt 3: Verknüpfung verstehen

Sobald du die SB-Spalte in `orders` kennst, prüfe mit Stichproben ob die Join-Logik stimmt:

```sql
SELECT o.order_number, o.<sb_spalte>, e.first_name, e.last_name, o.order_date
FROM orders o
JOIN employees e ON o.<sb_spalte> = e.<sb_nummer>
WHERE o.order_date >= '2025-01-01'
  AND e.last_name IN ('Huber', 'Salmansberger', 'Kraus', 'Keidl')
LIMIT 10;
```

### Schritt 4: Beträge-Format prüfen

Locosoft speichert Beträge teilweise in Cent statt Euro. Prüfe:

```sql
SELECT net_price_in_order FROM labours
WHERE net_price_in_order > 0 LIMIT 10;
-- Wenn Werte wie 12500 → Cent (÷100)
-- Wenn Werte wie 125.00 → Euro
```

### Schritt 5: Lohnumsatz pro SB

```sql
SELECT
    e.first_name || ' ' || e.last_name AS serviceberater,
    COUNT(DISTINCT o.order_number) AS anzahl_auftraege,
    ROUND(SUM(l.time_units) / 10.0, 1) AS verkaufte_stunden,
    ROUND(SUM(l.net_price_in_order) / <faktor>, 2) AS lohnumsatz_eur
FROM orders o
JOIN labours l ON o.order_number = l.order_number AND o.subsidiary = l.subsidiary
JOIN employees e ON o.<sb_spalte> = e.<sb_nummer>
WHERE o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
  AND l.is_invoiced = true
  AND e.last_name IN ('Huber', 'Salmansberger', 'Kraus', 'Keidl')
GROUP BY e.first_name, e.last_name
ORDER BY lohnumsatz_eur DESC;
```

### Schritt 6: Teileumsatz pro SB

Prüfe ob Teile in einer eigenen Tabelle liegen oder über `labour_type` unterschieden werden:

```sql
-- Welche labour_types gibt es?
SELECT DISTINCT labour_type, COUNT(*) FROM labours GROUP BY labour_type;

-- Gibt es eine parts-Tabelle?
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND (table_name ILIKE '%part%' OR table_name ILIKE '%spare%'
  OR table_name ILIKE '%teil%' OR table_name ILIKE '%material%');
```

Falls Teile separat liegen, analog den Teileumsatz pro SB berechnen.

### Schritt 7: Gesamtauswertung — Jahresübersicht

Erstelle eine Übersicht pro SB:
- Jahresumsatz Lohn
- Jahresumsatz Teile (falls separat ermittelbar)
- Jahresumsatz Gesamt
- Anzahl Aufträge
- Verkaufte Stunden
- Ø Stunden pro Auftrag
- Ø Aufträge pro Arbeitstag (~220 Tage)
- Vergleich zum Branchenrichtwert (800k–1 Mio. €/Jahr)

### Schritt 8: Monatsweise Aufschlüsselung

```sql
SELECT
    e.first_name || ' ' || e.last_name AS serviceberater,
    TO_CHAR(o.order_date, 'YYYY-MM') AS monat,
    COUNT(DISTINCT o.order_number) AS auftraege,
    ROUND(SUM(l.time_units) / 10.0, 1) AS verkaufte_stunden,
    ROUND(SUM(l.net_price_in_order) / <faktor>, 2) AS umsatz
FROM orders o
JOIN labours l ON o.order_number = l.order_number AND o.subsidiary = l.subsidiary
JOIN employees e ON o.<sb_spalte> = e.<sb_nummer>
WHERE o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
  AND l.is_invoiced = true
  AND e.last_name IN ('Huber', 'Salmansberger', 'Kraus', 'Keidl')
GROUP BY e.first_name, e.last_name, TO_CHAR(o.order_date, 'YYYY-MM')
ORDER BY serviceberater, monat;
```

### Schritt 9: Ergebnis ablegen

Speichere die fertige Auswertung als Markdown:

```
docs/workstreams/verguetung/SB_UMSATZANALYSE_2025.md
```

## Wichtige Hinweise

1. **Subsidiary:** Betrieb 1 = Deggendorf Stellantis, 2 = Hyundai, 3 = Landau. Nach Betrieb aufschlüsseln ODER zusammenfassen — beides zeigen.
2. **Doppelzählung vermeiden:** `COUNT(DISTINCT order_number)` für Aufträge.
3. **Garantie/Kulanz:** `charge_type` in labours kann Garantie sein — trotzdem mitzählen (Arbeit wurde geleistet).
4. **invoices-Tabelle:** Alternativ den fakturierten Betrag über `invoices` prüfen. Stichprobe: Stimmt labours-Summe ≈ invoices-Summe?
5. **Kein Sync nötig** — wir arbeiten direkt auf dem Server.
6. **Kein Code deployen** — reine Analyse-Aufgabe. Ergebnis als .md in den Workstream-Ordner.
