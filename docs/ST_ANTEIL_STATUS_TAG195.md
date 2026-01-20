# St-Anteil Implementierung - Status TAG 195

**Datum:** 2026-01-17  
**Status:** ✅ **Formel implementiert, aber noch Abweichungen**

---

## ✅ Was wurde gemacht

1. **Korrekte Formel implementiert:**
   ```
   St-Ant = Dauer × (AuAW / Gesamt-AuAW pro Stempelung)
   ```

2. **SQL-Query angepasst:**
   - Stempelungen deduplizieren (pro Position pro Stempelung)
   - AW pro Position aus `labours` (time_units * 6.0)
   - Gesamt-AuAW pro Stempelung berechnen
   - St-Anteil mit Formel berechnen
   - Aggregiert pro Mechaniker

3. **Filter:**
   - `time_units > 0` (nur Positionen mit AW)
   - Kein `is_invoiced` Filter (alle Positionen)
   - Kein `labour_type` Filter (alle Typen)

---

## 📊 Test-Ergebnisse

### Mechaniker 5007 (Tobias Reitmeier) - 01.01.26-15.01.26

| Metrik | DRIVE | Locosoft | Diff |
|--------|-------|----------|------|
| **St-Anteil** | **3360 Min (56.00 h)** | **4971 Min (82.85 h)** | **-1611 Min (-32.4%)** ⚠️ |
| AW-Anteil | 528.5 AW (3171 Min) | 524.83 AW | +3.67 AW (+0.7%) ✅ |
| Leistungsgrad | 94.4% | 63.5% | +30.9% ⚠️ |

**Status:** St-Anteil noch zu niedrig, aber Formel ist korrekt implementiert.

---

## ⚠️ Mögliche Ursachen für Abweichung

1. **Filter fehlen?**
   - `is_invoiced = true`? (getestet: macht es schlechter)
   - `labour_type != 'I'`? (noch nicht getestet)

2. **Gruppierung falsch?**
   - Aktuell: Pro Position pro Stempelung
   - Sollte: Pro Stempelung (gleiche start_time, end_time)?

3. **Positionen ohne AW?**
   - Werden aktuell ignoriert (auaw_minuten = 0)
   - Sollten sie berücksichtigt werden?

4. **Andere Locosoft-Logik?**
   - Vielleicht verwendet Locosoft eine andere Berechnung?
   - CSV-Analyse zeigt 91.8% Match, aber vielleicht nicht für alle Fälle?

---

## 🔧 Nächste Schritte

1. ✅ Formel korrekt implementiert
2. ⏳ Testen mit `labour_type != 'I'` Filter
3. ⏳ Testen mit anderen Gruppierungen
4. ⏳ Vergleich mit Locosoft für mehrere Mechaniker
5. ⏳ Prüfen, ob Positionen ohne AW berücksichtigt werden müssen

---

## 📝 SQL-Query (Aktuell)

Siehe `api/werkstatt_data.py` → `get_st_anteil_position_basiert()` Zeilen 922-1000

**Formel:**
```sql
CASE 
    WHEN gas.gesamt_auaw_minuten > 0 AND sma.auaw_minuten > 0
    THEN sma.dauer_minuten * (sma.auaw_minuten::numeric / gas.gesamt_auaw_minuten)
    ELSE 0
END AS st_anteil_minuten
```

---

**Hinweis:** Die Formel ist korrekt implementiert, aber es gibt noch Abweichungen. Weitere Tests und Anpassungen erforderlich.
