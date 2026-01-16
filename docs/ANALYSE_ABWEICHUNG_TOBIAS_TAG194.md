# Analyse: Warum ist die Abweichung bei Tobias größer? - TAG 194

**Datum:** 2026-01-16  
**Vergleich:** Tobias (5007) vs. Litwin (5014)

---

## 📊 Vergleich der Datenstruktur

| Metrik | Tobias (5007) | Litwin (5014) |
|--------|---------------|---------------|
| **Stempelungen** | 300 | 176 |
| **Positionen** | 206 | 148 |
| **Aufträge** | 39 | 20 |
| **Stempelungen auf mehrere Positionen** | 43 von 57 (75.4%) | 19 von 24 (79.2%) |
| **Stempelzeit auf mehrere Positionen** | 2585 Min | 1935 Min |
| **Position-basierte St-Anteil** | 3360 Min | 2257 Min |
| **Locosoft St-Anteil** | 4971 Min | 2078 Min |
| **Differenz** | 1611 Min (32.4%) | 179 Min (8.6%) |

---

## 🔍 Erkenntnisse

### 1. Tobias hat mehr Stempelungen auf mehrere Positionen
- **Tobias:** 43 von 57 Stempelungen (75.4%) gehen auf mehrere Positionen
- **Litwin:** 19 von 24 Stempelungen (79.2%) gehen auf mehrere Positionen
- **Stempelzeit auf mehrere Positionen:** Tobias 2585 Min vs. Litwin 1935 Min

### 2. Die anteilige Verteilung reduziert die Stempelzeit stärker bei Tobias
- **Tobias:** Position-basiert 3360 Min vs. OHNE Verteilung ~4971 Min
- **Litwin:** Position-basiert 2257 Min vs. OHNE Verteilung ~2078 Min

**Fazit:** Bei Tobias wird durch die anteilige Verteilung mehr Stempelzeit "verloren" als bei Litwin.

### 3. Mögliche Ursache: Locosoft berechnet St-Anteil OHNE anteilige Verteilung?
- Wenn eine Stempelung auf mehrere Positionen geht, wird die **GESAMTE** Stempelzeit gezählt
- Nicht die anteilig verteilte Stempelzeit pro Position

---

## 💡 Hypothese

**Locosoft "St-Anteil" wird OHNE anteilige Verteilung berechnet:**
- Wenn eine Stempelung auf mehrere Positionen geht, wird die gesamte Stempelzeit gezählt
- Nicht die anteilig verteilte Stempelzeit pro Position

**Beispiel:**
- Mechaniker stempelt 60 Min auf Position 1.1 und 1.2 (beide mit 10 AW)
- **Mit anteiliger Verteilung:** 30 Min pro Position = 30 Min St-Anteil
- **OHNE anteilige Verteilung:** 60 Min St-Anteil

---

## 📝 Nächste Schritte

1. ⚠️ **Prüfe ob Locosoft St-Anteil OHNE anteilige Verteilung berechnet:**
   - Teste: St-Anteil = Summe aller Stempelungen (dedupliziert pro Auftrag/Zeit)
   - Vergleiche mit Locosoft-Werten

2. 🔧 **Falls bestätigt:**
   - Anpassung der DRIVE-Berechnung für "St-Anteil" (Anzeige)
   - "St-Anteil" OHNE anteilige Verteilung berechnen
   - "AW-Anteil" MIT anteiliger Verteilung berechnen (bleibt wie bisher)

---

**Status:** ⚠️ **Hypothese: Locosoft berechnet St-Anteil OHNE anteilige Verteilung**
