# Metabase Architektur-Analyse

**Datum:** TAG 215  
**Zweck:** Beantwortung kritischer Fragen zur Metabase-Integration

---

## Frage 1: Gegen welche Datenbank laufen die Queries?

### ✅ Antwort: Direkt gegen PostgreSQL mit `loco_*` Tabellen

**Metabase-Konfiguration:**
- **Datenbank-ID:** 2
- **Name:** DRIVE Portal
- **Engine:** PostgreSQL
- **Host:** localhost:5432
- **Database:** `drive_portal`
- **User:** `drive_user`
- **Tabellen:** Direkt auf `loco_journal_accountings` und andere `loco_*` Tabellen

**✅ Keine separate Metabase-Datenquelle** - Metabase greift direkt auf die gleiche PostgreSQL-Datenbank zu wie DRIVE Portal.

---

## Frage 2: Ist die BWA-Logik in SQL-Queries oder Views abgebildet?

### ⚠️ Antwort: Komplette Logik in SQL-Queries (PROBLEM!)

**Aktueller Zustand:**

1. **Materialized Views existieren** (`fact_bwa`, `dim_zeit`, `dim_standort`, etc.)
   - Erstellt in TAG 178 (`migrations/create_finanzreporting_cube_tag178.sql`)
   - **ABER:** Metabase-Queries nutzen diese **NICHT**!

2. **Metabase-Queries greifen direkt auf `loco_journal_accountings` zu**
   - Komplette BWA-Logik ist in jedem Query dupliziert:
     - G&V-Filter: `AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')`
     - Umsatz-Bereinigung: Konten-Ranges (800000-889999, 893200-893299)
     - SOLL/HABEN-Netto-Logik: `CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END`
     - Kosten-Kategorisierung: Variable, Direkte, Indirekte Kosten (komplexe WHERE-Klauseln)
     - Standort-Filter: `branch_number`, `subsidiary_to_company_ref`, Konto-Endziffern

3. **Wartbarkeitsproblem:**
   - **6+ Metabase-Queries** enthalten identische Logik
   - Änderungen müssen in **allen Queries** manuell aktualisiert werden
   - Keine zentrale Wartung möglich
   - Hohe Fehleranfälligkeit

---

## Vergleich: DRIVE vs. Metabase

### ✅ Werte stimmen überein

**Grund:** Beide nutzen:
- Dieselbe Datenbank (`drive_portal`)
- Dieselbe Tabelle (`loco_journal_accountings`)
- Dieselbe Logik (direkt in SQL)

**Test-Ergebnis:**
- TEK Gesamt - Umsatz: ✅ Identisch
- BWA Monatswerte - Umsatz: ✅ Identisch

**ABER:** Metabase-Queries sind **nicht wartbar** - Logik ist dupliziert!

---

## Empfehlungen

### Option A: Materialized Views nutzen (EMPFOHLEN)

**Vorteile:**
- ✅ Zentrale Wartung der BWA-Logik
- ✅ Konsistenz zwischen DRIVE und Metabase
- ✅ Bessere Performance (vorgeaggregiert)
- ✅ Einfache Metabase-Queries

**Umsetzung:**
1. Materialized Views bereits vorhanden (`fact_bwa`, `dim_*`)
2. Metabase-Queries umschreiben auf Views
3. Views regelmäßig refreshen (z.B. täglich via Celery)

**Beispiel:**
```sql
-- Statt:
SELECT SUM(...) FROM loco_journal_accountings WHERE ...

-- Nutze:
SELECT SUM(betrag) FROM fact_bwa 
WHERE zeit_id >= ... AND zeit_id < ...
```

### Option B: Views statt Materialized Views

**Vorteile:**
- ✅ Immer aktuell (kein Refresh nötig)
- ✅ Zentrale Logik

**Nachteile:**
- ⚠️ Langsamer (keine Vorgeaggregation)

### Option C: Aktueller Zustand beibehalten

**Nachteile:**
- ❌ Logik in 6+ Queries dupliziert
- ❌ Wartungsaufwand bei Änderungen
- ❌ Fehleranfälligkeit

---

## Nächste Schritte

1. **Kurzfristig:**
   - ✅ Metabase-Queries funktionieren
   - ✅ Werte stimmen mit DRIVE überein
   - ⚠️ Wartbarkeit ist problematisch

2. **Mittelfristig (EMPFOHLEN):**
   - Materialized Views in Metabase-Queries integrieren
   - Zentrale Wartung der BWA-Logik
   - Automatisches Refresh der Views (Celery-Task)

3. **Langfristig:**
   - DRIVE API auch auf Materialized Views umstellen
   - Einheitliche Datenquelle für alle Systeme

---

## Technische Details

### Materialized Views (vorhanden, aber ungenutzt)

**`fact_bwa`:**
- Enthält: `zeit_id`, `standort_id`, `kst_id`, `konto_id`, `betrag`, `menge`
- Filter: G&V-Abschluss bereits ausgeschlossen
- Indizes: Optimiert für Zeitraum-Abfragen

**`dim_zeit`:**
- Enthält: `datum`, `jahr`, `monat`, `tag`, `quartal`, etc.
- Indizes: `jahr_monat`, `jahr_quartal`

**`dim_standort`:**
- Enthält: `standort_id`, `standort_name`, `firma_id`, etc.

**`dim_kostenstelle`:**
- Enthält: `kst_id`, `kst_name`, `kst_typ`, etc.

**`dim_konto`:**
- Enthält: `konto_id`, `konto_name`, `konto_typ`, etc.

### Aktuelle Metabase-Queries

**TEK-Queries:**
- `TEK Gesamt - Monat kumuliert` (ID: 42)
- `TEK nach Standort` (ID: 43)
- `TEK Verlauf` (ID: 44)

**BWA-Queries:**
- `BWA Monatswerte` (ID: 49)
- `BWA Verlauf` (ID: 50)
- `BWA Vergleich Vorjahr` (ID: 51)

**Alle nutzen:** Direkt `loco_journal_accountings` mit duplizierter Logik

---

## Fazit

✅ **Frage 1:** Metabase läuft direkt gegen PostgreSQL (`drive_portal`) mit `loco_*` Tabellen  
⚠️ **Frage 2:** Komplette BWA-Logik ist in SQL-Queries dupliziert - **nicht wartbar!**

**Empfehlung:** Materialized Views nutzen für zentrale Wartung und bessere Performance.
