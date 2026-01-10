# Materialized Views - Bewertung für DB3-Differenz-Analyse

**Datum:** 2026-01-10  
**TAG:** 177  
**Frage:** Sollten wir Materialized Views erstellen, um die Differenzen schneller zu finden?

---

## Aktuelle Situation

### Performance-Analyse
- **Query-Dauer (direkte Kosten):** 0.019 Sekunden ✅
- **Anzahl relevanter Buchungen:** 8.272 (Sep 2024 - Aug 2025)
- **Datenvolumen:** Klein bis mittel
- **Performance-Problem:** ❌ Keines vorhanden

### Aktuelles Problem
- **DB3-Differenz:** -100.381,57 € (-3,58%)
- **Hauptursache:** Filter-Logik-Unterschied (nicht Performance!)
  - DRIVE: Verwendet 5. Stelle von `nominal_account_number` für KST
  - Globalcube: Verwendet `skr51_cost_center` (aber alle = 0 → Fallback?)
- **Ziel:** Filter-Logik verstehen, nicht Performance optimieren

---

## Materialized Views - Pro & Contra

### ✅ PRO (Vorteile)

1. **Schnellere Varianten-Tests**
   - Wenn wir viele Filter-Varianten testen müssen
   - Vorgeaggregierte Daten nach Dimensionen (Zeit, Standort, KST)
   - Aktuell: Wir testen ~10-20 Varianten pro Script

2. **Dimensionale Analyse**
   - Monat-für-Monat-Vergleich schneller
   - Standort-Vergleich einfacher
   - KST-Vergleich möglich

3. **Zukunftssicherheit**
   - Wenn Datenvolumen wächst (aktuell nur 8k Buchungen)
   - Wenn mehr User gleichzeitig abfragen
   - Wenn komplexere Analysen nötig werden

### ❌ CONTRA (Nachteile)

1. **Löst nicht das Hauptproblem**
   - Filter-Logik-Unterschied bleibt bestehen
   - Materialized Views helfen nicht, die richtige Filter-Logik zu finden
   - Wir müssen erst verstehen, wie Globalcube filtert

2. **Overhead**
   - Erstellung: ~30-60 Minuten Entwicklungszeit
   - Wartung: Refresh-Logik bei Datenänderungen
   - Komplexität: Mehr Code zu warten

3. **Performance nicht nötig**
   - Aktuelle Queries: 0.019 Sekunden (sehr schnell!)
   - Datenvolumen: Nur 8.272 Buchungen
   - Kein Performance-Problem vorhanden

4. **Risiko falscher Aggregation**
   - Wenn wir die Filter-Logik noch nicht verstehen
   - Materialized Views könnten falsche Daten aggregieren
   - Dann müssen wir sie neu bauen

---

## Empfehlung: **JETZT NEIN, SPÄTER JA**

### Phase 1: Filter-Logik verstehen (JETZT)
**Priorität:** 🔴 HOCH

1. **skr51_cost_center Fallback-Logik analysieren**
   - Warum sind alle direkten Kosten `skr51_cost_center = 0`?
   - Wie filtert Globalcube, wenn `skr51_cost_center = 0`?
   - Gibt es eine Fallback-Logik (5. Stelle)?

2. **Kontenbereiche identifizieren**
   - Welche Konten zählt Globalcube als direkte Kosten?
   - Welche Konten zählt DRIVE, die Globalcube nicht zählt?
   - 411xxx wurde als Kandidat identifiziert (100k€ Differenz)

3. **Monat-für-Monat-Analyse**
   - Wann entsteht die Differenz?
   - Ist sie konstant oder variabel?
   - Gibt es Monate mit 100% Übereinstimmung?

**Tools:** Analyse-Scripts (bereits vorhanden)
- `analyse_skr51_cost_center.py`
- `analyse_100k_differenz_konten.py`
- `analyse_bwa_monatlich_globalcube.py`

### Phase 2: Materialized Views (SPÄTER)
**Priorität:** 🟡 MITTEL (nach Filter-Logik-Verständnis)

**Wenn:**
- ✅ Filter-Logik vollständig verstanden
- ✅ 100% Übereinstimmung erreicht
- ✅ Performance wird zum Problem (mehr User, mehr Daten)
- ✅ Komplexere Analysen nötig (z.B. Drill-Down nach KST)

**Dann:**
- Materialized Views für Performance-Optimierung
- Vorgeaggregierte Daten nach Dimensionen
- Schnellere Abfragen für Frontend

---

## Alternative: Hybrid-Ansatz

### Option A: Temporäre Views (nicht Materialized)
```sql
-- Schnelle Tests ohne Overhead
CREATE VIEW v_direkte_kosten_test AS
SELECT 
    accounting_date,
    nominal_account_number,
    skr51_cost_center,
    substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_5_stelle,
    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END / 100.0 as betrag
FROM loco_journal_accountings
WHERE accounting_date >= '2024-09-01'
  AND nominal_account_number BETWEEN 400000 AND 489999;
```

**Vorteil:** Schnelle Tests, kein Refresh nötig, einfach zu ändern

### Option B: CTEs in Scripts
```python
# In Analyse-Scripts: Common Table Expressions
cursor.execute("""
    WITH direkte_kosten AS (
        SELECT 
            accounting_date,
            nominal_account_number,
            skr51_cost_center,
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_5_stelle,
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END / 100.0 as betrag
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
    )
    SELECT 
        kst_5_stelle,
        SUM(betrag) as gesamt
    FROM direkte_kosten
    WHERE kst_5_stelle IN ('1','2','3','4','5','6','7')
    GROUP BY kst_5_stelle
""", (datum_von, datum_bis))
```

**Vorteil:** Keine DB-Änderungen, flexibel, schnell zu testen

---

## Fazit

### ❌ Materialized Views JETZT: **NICHT EMPFOHLEN**

**Gründe:**
1. Performance ist bereits sehr gut (0.019 Sekunden)
2. Hauptproblem ist Filter-Logik, nicht Performance
3. Risiko falscher Aggregation, wenn Logik noch unklar
4. Overhead (Entwicklung + Wartung) ohne Nutzen

### ✅ Nächste Schritte (Priorität):

1. **skr51_cost_center Fallback-Logik verstehen**
   - Script: `analyse_skr51_cost_center.py` erweitern
   - Prüfen: Wie filtert Globalcube bei `skr51_cost_center = 0`?

2. **411xxx Kontenbereich analysieren**
   - Script: `analyse_100k_differenz_konten.py` erweitern
   - Prüfen: Welche 411xxx-Konten zählt Globalcube nicht?

3. **Monat-für-Monat-Vergleich**
   - Script: `analyse_bwa_monatlich_globalcube.py` erweitern
   - Prüfen: Wann entsteht die Differenz?

### ✅ Materialized Views SPÄTER: **EMPFOHLEN**

**Wenn:**
- Filter-Logik vollständig verstanden
- 100% Übereinstimmung erreicht
- Performance wird zum Problem
- Komplexere Analysen nötig

**Dann:**
- Materialized Views für Performance-Optimierung
- Vorgeaggregierte Daten nach Dimensionen
- Schnellere Abfragen für Frontend

---

## Zusammenfassung

| Aspekt | Jetzt | Später |
|--------|-------|--------|
| **Performance-Problem** | ❌ Nein (0.019s) | ✅ Möglicherweise |
| **Filter-Logik verstanden** | ❌ Nein | ✅ Ja (Ziel) |
| **Datenvolumen** | ✅ Klein (8k) | ✅ Kann wachsen |
| **Nutzen** | ❌ Gering | ✅ Hoch |
| **Risiko** | ⚠️ Falsche Aggregation | ✅ Gering |
| **Empfehlung** | ❌ **NICHT JETZT** | ✅ **SPÄTER JA** |

**Entscheidung:** ❌ **Materialized Views JETZT NICHT erstellen**

**Begründung:** Wir müssen zuerst die Filter-Logik verstehen. Materialized Views würden nur falsche Daten aggregieren, wenn wir die Logik noch nicht verstanden haben.
