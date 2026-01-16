# Detaillierte Analyse: Stmp.Anteil für Tobias (5007) - TAG 194

**Datum:** 2026-01-16  
**Status:** ⚠️ Problem identifiziert, Lösung noch nicht gefunden

---

## 📊 Analyse-Ergebnisse

### Rohdaten für Tobias (5007) - 01.01-15.01.26

| Metrik | Wert |
|--------|------|
| Alle Stempelungen (Roh) | 300 Stempelungen, 18674 Min (311.23h) |
| Deduplizierte Stempelungen | 300 Stempelungen, 18674 Min |
| Minuten mit AW | 6624 Min (110.41h) |
| Minuten ohne AW | 12049 Min (200.82h) |
| Positionen gesamt | 206 |
| Positionen mit AW | 64 |
| Positionen ohne AW | 142 |
| Stempelungen auf mehrere Positionen | 54 Stempelungen (18358 Min) |

### Vergleich DRIVE vs. Locosoft

| Metrik | DRIVE | Locosoft | Diff |
|--------|-------|----------|------|
| Stmp.Anteil | 3602 Min (60.04h) | 4971 Min (82.85h) | -1369 Min (-27.5%) ⚠️ |
| AW-Anteil | 53.10h | 52.58h | +0.52h (+1.0%) ✅ |
| Leistungsgrad | 88.5% | 63.5% | +25.0% ⚠️ |

---

## 🔍 Problem-Identifikation

**Fehlende Minuten: 1369 Min**

**Aktuelle Logik in DRIVE:**
- Positionen MIT AW: Anteilig nach AW verteilen
- Positionen OHNE AW: Werden IGNORIERT wenn es auch Positionen mit AW gibt
- Positionen OHNE AW: Gleichmäßig verteilen wenn ALLE Positionen 0 AW haben

**Versuchte Lösungen:**

1. **Positionen ohne AW vollständig zählen:**
   - Ergebnis: 5755 Min (+15.8% Diff) ❌ Zu hoch!

2. **Positionen ohne AW ignorieren (aktuelle Logik):**
   - Ergebnis: 3602 Min (-27.5% Diff) ❌ Zu niedrig!

3. **Positionen ohne AW teilweise zählen:**
   - Noch nicht getestet

---

## 💡 Hypothesen

### Hypothese 1: Positionen ohne AW zählen nur wenn EINZIGE Position
- Wenn eine Stempelung auf mehrere Positionen geht (mit und ohne AW), werden Positionen ohne AW ignoriert
- Wenn eine Stempelung NUR auf Positionen ohne AW geht, werden diese gleichmäßig verteilt

### Hypothese 2: Locosoft verwendet andere Filter
- Nur fakturierte Positionen?
- Nur Positionen mit bestimmten Status?
- Andere Zeitraum-Definition?

### Hypothese 3: Locosoft verwendet andere Logik für anteilige Verteilung
- Vielleicht wird die Verteilung anders berechnet?
- Vielleicht gibt es eine Obergrenze pro Position?

---

## 📝 Nächste Schritte

1. ⏳ Prüfe ob Locosoft nur fakturierte Positionen berücksichtigt
2. ⏳ Prüfe ob Positionen ohne AW nur zählen wenn sie EINZIGE Position sind
3. ⏳ Prüfe ob es andere Filter gibt (Status, Typ, etc.)
4. ⏳ Vergleich mit anderen Mechanikern (Jan funktioniert, Tobias nicht)

---

**Status:** ⚠️ **Problem identifiziert, aber Lösung noch nicht gefunden**
