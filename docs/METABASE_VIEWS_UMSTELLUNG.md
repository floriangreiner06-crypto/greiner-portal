# Metabase: Umstellung auf Materialized Views

**Datum:** TAG 215  
**Status:** ✅ Abgeschlossen

---

## Was wurde gemacht?

### 1. Migration ausgeführt

**Materialized Views erstellt:**
- `dim_zeit`: 855 Zeilen (Zeit-Dimension)
- `dim_standort`: 3 Standorte (1=DEG, 2=HYU, 3=LAN) – Zeilenanzahl abhängig von vorhandenen Buchungen
- `dim_kostenstelle`: 6 Zeilen (Kostenstellen-Dimension)
- `dim_konto`: 958 Zeilen (Konten-Dimension)
- `fact_bwa`: 632,819 Zeilen (Fact-Table für BWA-Daten)

**Refresh-Funktion:**
- `refresh_finanzreporting_cube()` - Aktualisiert alle Views

### 2. Metabase-Queries aktualisiert

**TEK-Queries:**
- ✅ `TEK Gesamt - Monat kumuliert` (ID: 42)
- ✅ `TEK nach Standort` (ID: 43)
- ✅ `TEK Verlauf` (ID: 44)

**BWA-Queries:**
- ✅ `BWA Monatswerte` (ID: 49)
- ✅ `BWA Verlauf` (ID: 50)
- ✅ `BWA Vergleich Vorjahr` (ID: 51)

**Alle Queries nutzen jetzt:**
- `fact_bwa` statt `loco_journal_accountings`
- Vorgeaggregierte Daten (bessere Performance)
- Zentrale BWA-Logik (wartbar)

### 3. Automatisches Refresh

**Celery-Task:**
- **Task:** `refresh_finanzreporting_cube`
- **Schedule:** Täglich um 19:20
- **Queue:** `controlling`
- **Zweck:** Aktualisiert alle Materialized Views nach Locosoft-Sync (19:00)

---

## Vorteile

### ✅ Wartbarkeit
- **Vorher:** BWA-Logik in 6+ Queries dupliziert
- **Jetzt:** Zentrale Logik in `fact_bwa` Materialized View
- **Änderungen:** Nur in einer Stelle nötig

### ✅ Performance
- **Vorher:** Komplexe Queries auf `loco_journal_accountings` (632k+ Zeilen)
- **Jetzt:** Vorgeaggregierte Daten in `fact_bwa`
- **Geschwindigkeit:** Deutlich schneller

### ✅ Konsistenz
- **Vorher:** Risiko von Inkonsistenzen zwischen Queries
- **Jetzt:** Einheitliche Datenquelle für alle Queries
- **DRIVE & Metabase:** Nutzen dieselbe Logik

### ✅ Einfachheit
- **Vorher:** Komplexe SQL-Queries mit vielen WHERE-Klauseln
- **Jetzt:** Einfache Queries auf vorgeaggregierte Daten
- **Wartung:** Deutlich einfacher

---

## Technische Details

### fact_bwa Struktur

**Spalten:**
- `zeit_id` (DATE) - Buchungsdatum
- `standort_id` (INTEGER) - Standort (1=DEG, 2=HYU, 3=LAN)
- `kst_id` (INTEGER) - Kostenstelle (aus skr51_cost_center oder 5. Stelle)
- `konto_id` (INTEGER) - Kontonummer
- `betrag` (NUMERIC) - Bereits bereinigter Betrag (SOLL/HABEN-Netto, /100.0)
- `debit_or_credit` (TEXT) - 'S' oder 'H'
- `posting_text`, `document_number`, etc. - Metadaten

**Filter bereits angewendet:**
- ✅ G&V-Abschlussbuchungen ausgeschlossen
- ✅ SOLL/HABEN-Netto-Logik angewendet
- ✅ Betrag bereits durch 100.0 geteilt

### Query-Beispiel

**Vorher (direkt auf loco_journal_accountings):**
```sql
SELECT SUM(
    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
) / 100.0
FROM loco_journal_accountings
WHERE accounting_date >= ...
  AND nominal_account_number BETWEEN 800000 AND 889999
  AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
```

**Jetzt (mit fact_bwa):**
```sql
SELECT SUM(betrag)
FROM fact_bwa
WHERE zeit_id >= ...
  AND konto_id BETWEEN 800000 AND 889999
  AND debit_or_credit = 'H'
```

**Vorteil:** Deutlich einfacher, keine duplizierte Logik!

---

## Refresh-Zeitplan

**Ablauf:**
1. **19:00** - Locosoft Mirror (Daten werden gespiegelt)
2. **19:20** - Refresh Finanzreporting Cube (Views werden aktualisiert)
3. **19:30** - BWA Berechnung (nutzt aktualisierte Views)

**Manuelles Refresh:**
```sql
SELECT refresh_finanzreporting_cube();
```

---

## Nächste Schritte

1. ✅ **Abgeschlossen:** Migration ausgeführt
2. ✅ **Abgeschlossen:** Metabase-Queries aktualisiert
3. ✅ **Abgeschlossen:** Celery-Task konfiguriert
4. ⏳ **Optional:** DRIVE API auch auf Views umstellen (langfristig)

---

## Dokumentation

- **Migration:** `migrations/create_finanzreporting_cube_tag178.sql`
- **Celery-Task:** `celery_app/tasks.py` → `refresh_finanzreporting_cube()`
- **Update-Script:** `scripts/update_metabase_queries_to_views.py`
- **Architektur-Analyse:** `docs/METABASE_ARCHITEKTUR_ANALYSE.md`
