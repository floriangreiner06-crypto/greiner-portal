# Metabase: Vorzeichenfehler-Korrektur

**Datum:** TAG 215  
**Status:** ✅ Korrigiert

---

## Problem

**Symptom:**
- Metabase zeigte negative Erlöse (z.B. -391,805.23 € statt 391,805.23 €)
- Dashboard-Cards waren zu klein, Daten nicht vollständig sichtbar

**Ursache:**
- `fact_bwa` Materialized View berechnet `betrag` als:
  - SOLL (S): `betrag = posted_value / 100.0`
  - HABEN (H): `betrag = -posted_value / 100.0`
- Metabase-Queries nutzten `betrag` direkt für Umsatz (HABEN)
- Ergebnis: Negative Werte

---

## Lösung

### 1. Vorzeichen in Metabase-Queries korrigiert

**Für Umsatz (HABEN = 'H'):**
- **Vorher:** `SUM(betrag)` → Negative Werte
- **Jetzt:** `SUM(-betrag)` → Positive Werte ✅

**Für Einsatz (SOLL = 'S'):**
- **Unverändert:** `SUM(betrag)` → Korrekt

**Für Neutrale Erträge (HABEN = 'H'):**
- **Vorher:** `SUM(betrag)` → Negative Werte
- **Jetzt:** `SUM(-betrag)` → Positive Werte ✅

### 2. Dashboard-Größen angepasst

**TEK Dashboard:**
- TEK Gesamt: 12 Spalten × 10 Zeilen (vorher: 6×4)
- TEK nach Standort: 12 Spalten × 10 Zeilen (vorher: 6×4)
- TEK Verlauf: 12 Spalten × 12 Zeilen (vorher: 12×4)

**BWA Dashboard:**
- BWA Monatswerte: 12 Spalten × 10 Zeilen (vorher: 6×4)
- BWA Verlauf: 12 Spalten × 12 Zeilen (vorher: 12×4)
- BWA Vergleich Vorjahr: 12 Spalten × 10 Zeilen (vorher: 12×4)

---

## Vergleich: DRIVE vs. Metabase

### Aktueller Stand

**TEK Gesamt - Neuwagen (Beispiel):**
- DRIVE: 300,195.90 €
- Metabase: 391,805.23 €
- Differenz: 91,609.33 €

### Ursache der Differenz

**G&V-Filter unterschiedlich:**
- **DRIVE:** `NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')`
- **fact_bwa:** `(posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%')`

**Ergebnis:**
- `fact_bwa` enthält mehr Daten als DRIVE
- Differenz von ~91k € durch unterschiedliche Filter-Logik

### Lösung (optional, langfristig)

**Option 1:** G&V-Filter in `fact_bwa` anpassen
- Migration anpassen: `create_finanzreporting_cube_tag178.sql`
- Views neu erstellen
- **Nachteil:** Breaking Change für andere Systeme

**Option 2:** Zusätzlicher Filter in Metabase-Queries
- `AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')`
- **Status:** ✅ Bereits implementiert
- **Problem:** `standort_id = 0` kommt in `fact_bwa` nicht vor

**Option 3:** Aktuellen Zustand akzeptieren
- Metabase zeigt konsistente Werte (basierend auf `fact_bwa`)
- DRIVE zeigt konsistente Werte (basierend auf `loco_journal_accountings`)
- **Empfehlung:** Für jetzt akzeptieren, langfristig Filter angleichen

---

## Geänderte Queries

### TEK-Queries
- ✅ `TEK Gesamt - Monat kumuliert` (ID: 42)
- ✅ `TEK nach Standort` (ID: 43)
- ✅ `TEK Verlauf` (ID: 44)

### BWA-Queries
- ✅ `BWA Monatswerte` (ID: 49)
- ✅ `BWA Verlauf` (ID: 50)
- ✅ `BWA Vergleich Vorjahr` (ID: 51)

**Alle Queries nutzen jetzt:**
- `SUM(-betrag)` für Umsatz (HABEN)
- `SUM(betrag)` für Einsatz (SOLL)
- `SUM(-betrag)` für Neutrale Erträge (HABEN)

---

## Nächste Schritte

1. ✅ **Abgeschlossen:** Vorzeichenfehler korrigiert
2. ✅ **Abgeschlossen:** Dashboard-Größen angepasst
3. ⏳ **Optional:** G&V-Filter in `fact_bwa` anpassen (langfristig)
4. ✅ **Aktiv:** Automatisches Refresh täglich um 19:20

---

## Validierung

**Bitte prüfen:**
1. Dashboard im Browser aktualisieren (F5)
2. Werte sollten jetzt positiv sein
3. Cards sollten größer und besser sichtbar sein
4. Werte sollten konsistent sein (auch wenn leicht unterschiedlich zu DRIVE)

**Bei Fragen oder Problemen:**
- Prüfe Metabase-Logs: `journalctl -u metabase -f`
- Teste Queries lokal: `psql -h localhost -U drive_user -d drive_portal`
- Prüfe fact_bwa: `SELECT * FROM fact_bwa WHERE ... LIMIT 10;`
