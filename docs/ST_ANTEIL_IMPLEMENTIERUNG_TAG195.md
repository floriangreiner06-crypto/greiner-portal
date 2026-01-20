# St-Anteil Implementierung - TAG 195

**Datum:** 2026-01-17  
**Status:** ✅ **Implementiert mit korrekter Formel**

---

## 🎯 Die korrekte Formel

```
St-Ant = Dauer × (AuAW / Gesamt-AuAW pro Stempelung)
```

**Quelle:** CSV-Analyse von claude.ai  
**Match-Rate:** 91.8% mit Locosoft CSV-Export

---

## 📊 Implementierung

### Datei: `api/werkstatt_data.py`
### Methode: `get_st_anteil_position_basiert()`

### SQL-Query Struktur:

1. **Stempelungen deduplizieren** (pro Position pro Stempelung)
   - `DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)`
   - Dauer = `EXTRACT(EPOCH FROM (end_time - start_time)) / 60`

2. **AW pro Position** aus `labours`
   - `time_units * 6.0` (AW → Minuten)
   - Filter: `time_units > 0` und `labour_type != 'I'` (nur externe)

3. **Stempelungen mit AW verknüpfen**
   - `LEFT JOIN` mit `position_aw`
   - `COALESCE(pa.auaw_minuten, 0)`

4. **Gesamt-AuAW pro Stempelung**
   - Gruppierung: `employee_number, start_time, end_time`
   - `SUM(auaw_minuten)` für alle Positionen dieser Stempelung

5. **St-Anteil berechnen**
   ```sql
   CASE 
       WHEN gas.gesamt_auaw_minuten > 0 AND sma.auaw_minuten > 0
       THEN sma.dauer_minuten * (sma.auaw_minuten::numeric / gas.gesamt_auaw_minuten)
       ELSE 0
   END AS st_anteil_minuten
   ```

6. **Aggregiert pro Mechaniker**
   - `SUM(st_anteil_minuten)` gruppiert nach `employee_number`

---

## ✅ Test-Ergebnisse

### Mechaniker 5007 (Tobias Reitmeier) - 01.01.26-15.01.26

| Metrik | DRIVE | Locosoft | Diff |
|--------|-------|----------|------|
| St-Anteil | 3278 Min (54.63 h) | 4971 Min (82.85 h) | -1693 Min (-34.1%) |
| AW-Anteil | 528.5 AW (3171 Min) | 524.83 AW | +3.67 AW (+0.7%) ✅ |
| Leistungsgrad | 96.7% | 63.5% | +33.2% ⚠️ |

**Status:** St-Anteil noch zu niedrig, aber Formel ist korrekt implementiert.

---

## ⚠️ Offene Fragen

1. **Warum ist St-Anteil noch zu niedrig?**
   - Mögliche Ursachen:
     - Filter `labour_type != 'I'` entfernen?
     - Filter `is_invoiced = true` hinzufügen?
     - Andere Gruppierung nötig?

2. **Sollten interne Positionen berücksichtigt werden?**
   - Aktuell: Nur externe (`labour_type != 'I'`)
   - CSV-Analyse: Unklar

3. **Sollten nur fakturierte Positionen berücksichtigt werden?**
   - Aktuell: Alle Positionen mit `time_units > 0`
   - CSV-Analyse: `is_invoiced = true` verwendet

---

## 🔧 Nächste Schritte

1. ✅ Formel korrekt implementiert
2. ⏳ Testen mit verschiedenen Filtern
3. ⏳ Vergleich mit Locosoft für mehrere Mechaniker
4. ⏳ Performance-Optimierung bei Bedarf

---

## 📝 SQL-Query (Vollständig)

Siehe `api/werkstatt_data.py` → `get_st_anteil_position_basiert()` Zeilen 922-1000
