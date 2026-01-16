# Stmp.Anteil Position-basierte Berechnung - TAG 194

**Datum:** 2026-01-16  
**Status:** ✅ Implementiert, ⚠️ Teilweise Abweichungen

---

## 📊 Implementierung

### Locosoft-Definition
> "Der Stmp Anteil ergibt sich aus der Summe aller Stempelungen des Monteurs auf Auftragspositionen. Wenn mehrere Monteure auf eine Position oder ein Monteur auf mehrere Positionen stempelt, wird dies anteilig verteilt."

### Implementierung in DRIVE

**Neue Funktion:** `get_st_anteil_position_basiert()`

**Logik:**
1. Stempelungen deduplizieren (pro Mechaniker/Auftrag/Position/Zeit)
2. Für jede Stempelung: Anteilige Verteilung nach AW
   - Wenn AW vorhanden: `St-Anteil = Stempelzeit × (AW_Position / Summe_AW_Stempelung)`
   - Wenn keine AW: Gleichmäßig auf alle Positionen der Stempelung verteilen
3. Summe pro Mechaniker

---

## 📊 Testergebnisse

### Jan Majer (5018) - 01.01-15.01.26

| Metrik | DRIVE | Locosoft | Diff |
|--------|-------|----------|------|
| Stmp.Anteil | 4038 Min (67.30h) | 4121 Min (68.68h) | -83 Min (-2.0%) ✅ |
| AW-Anteil | 90.40h | 91.55h | -1.15h (-1.3%) ✅ |
| Leistungsgrad | 134.3% | 133.3% | +1.0% ✅ |

**Status:** ✅ **Sehr nah!**

### Tobias Reitmeier (5007) - 01.01-15.01.26

| Metrik | DRIVE | Locosoft | Diff |
|--------|-------|----------|------|
| Stmp.Anteil | 3602 Min (60.04h) | 4971 Min (82.85h) | -1369 Min (-27.5%) ⚠️ |
| AW-Anteil | 53.10h | 52.58h | +0.52h (+1.0%) ✅ |
| Leistungsgrad | 88.5% | 63.5% | +25.0% ⚠️ |

**Status:** ⚠️ **Stmp.Anteil weicht noch ab**

**Analyse:**
- 300 Stempelungen auf 206 Positionen
- Gesamt Minuten (Roh): 18674 Min (311.23h)
- Stmp.Anteil (position-basiert): 3602 Min
- **Fehlende Minuten: 1369 Min**

**Mögliche Ursachen:**
1. Positionen ohne AW werden nicht richtig berücksichtigt
2. Stempelungen auf mehrere Positionen werden falsch verteilt
3. Andere Filter/Logik in Locosoft (z.B. nur fakturierte Positionen?)

---

## 🔍 Nächste Schritte

1. ⏳ Prüfe ob Locosoft auch Positionen ohne AW berücksichtigt
2. ⏳ Prüfe ob fakturierte vs. unfakturierte Positionen unterschieden werden
3. ⏳ Vergleich mit anderen Mechanikern
4. ⏳ Vollständiger Vergleich aller KPIs

---

**Status:** ✅ **Für Jan funktioniert es, für Tobias noch Abweichung**
