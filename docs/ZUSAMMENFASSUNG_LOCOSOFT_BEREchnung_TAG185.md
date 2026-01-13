# Zusammenfassung: Locosoft-Berechnungslogik für Stempelzeiten

**Datum:** 2026-01-13 (TAG 185)  
**Mitarbeiter:** 5018 (Jan Majer)  
**Zeitraum:** 01.11.2025 - 30.11.2025

---

## 🎯 ERKENNTNISSE

### Locosoft verwendet unterschiedliche Stempelzeiten für unterschiedliche Zwecke:

1. **"Stmp.Anteil" (angezeigt):** 8.483 Minuten
   - Zeit-Spanne: Erste bis letzte Stempelung (alle Aufträge)
   - Minus: Lücken zwischen Stempelungen
   - Minus: Konfigurierte Pausenzeiten (wenn innerhalb Zeit-Spanne)

2. **Leistungsgrad-Berechnung:** 7.846 Minuten
   - Zeit-Spanne: Erste Stempelung (auch intern) bis letzte externe Stempelung
   - Minus: Lücken zwischen externen Stempelungen (nur 10-60 Minuten)
   - **KEINE Pausen-Abzüge!**

---

## 📊 FORMELN

### 1. "Stmp.Anteil" (angezeigte Stempelzeit)

```
Stmp.Anteil = Zeit-Spanne (erste bis letzte Stempelung, alle Aufträge)
            - Lücken zwischen Stempelungen
            - Konfigurierte Pausenzeiten (wenn innerhalb Zeit-Spanne)
```

**Beispiel November:**
- Zeit-Spanne (alle) = 9.309 Minuten
- Lücken = ~400 Minuten
- Pausen = ~426 Minuten
- **Stmp.Anteil = 8.483 Minuten**

### 2. Leistungsgrad-Stempelzeit

```
Leistungsgrad-Stempelzeit = Zeit-Spanne (erste Stempelung bis letzte externe Stempelung)
                          - Lücken zwischen externen Stempelungen (nur 10-60 Minuten)
```

**Beispiel November:**
- Zeit-Spanne (erste alle bis letzte externe) = 7.994 Minuten
- Lücken (10-60 Min, nur extern) = 146 Minuten
- **Leistungsgrad-Stempelzeit = 7.846 Minuten**

**Leistungsgrad = (AW / Stempelzeit_AW) × 100**
- AW = 1.904
- Stempelzeit_AW = 7.846 / 6 = 1.307,7 AW
- **Leistungsgrad = 145,6%** ✅

---

## 🔍 WICHTIGE DETAILS

### Lücken-Berechnung für Leistungsgrad:
- ✅ Nur Lücken zwischen **externen** Stempelungen
- ✅ Nur Lücken zwischen **10-60 Minuten**
- ❌ Lücken < 10 Minuten werden ignoriert (normale Wechselzeiten)
- ❌ Lücken > 60 Minuten werden ignoriert (Pausen oder andere Gründe)
- ❌ Lücken zu/von internen Aufträgen werden ignoriert

### Pausen-Berechnung:
- ✅ Pausen werden für "Stmp.Anteil" abgezogen
- ❌ Pausen werden **NICHT** für Leistungsgrad abgezogen
- ⚠️ Pausen innerhalb von Stempelungen werden möglicherweise nicht abgezogen

### Interne Aufträge:
- ✅ Interne Aufträge zählen zur Zeit-Spanne (erste Stempelung)
- ❌ Interne Aufträge zählen **NICHT** zur letzten Stempelung (nur externe)
- ⚠️ Interne Aufträge werden für Leistungsgrad anders behandelt

---

## 📋 VERGLEICH DRIVE vs. LOCOSOFT

| KPI | DRIVE | Locosoft | Differenz |
|-----|-------|----------|-----------|
| **Stempelzeit (angezeigt)** | 8.115 Min | 8.483 Min | +368 Min |
| **Stempelzeit (Leistungsgrad)** | 8.115 Min | 7.846 Min | -269 Min |
| **Leistungsgrad** | 140,8% | 145,6% | +4,8% |
| **AW** | 1.904 | 1.904 | 0 |

**Erkenntnis:**
- DRIVE verwendet die gleiche Stempelzeit für Anzeige und Leistungsgrad
- Locosoft verwendet unterschiedliche Stempelzeiten
- Daher ist der Leistungsgrad in Locosoft höher (weniger Stempelzeit = höherer Leistungsgrad)

---

## 💡 EMPFEHLUNG

**Für DRIVE-Anpassung:**
1. **"Stmp.Anteil" (angezeigt):** 
   - Zeit-Spanne (erste bis letzte, alle) - Lücken - Pausen
   - ✅ Bereits implementiert (TAG 185)

2. **Leistungsgrad-Stempelzeit:**
   - Zeit-Spanne (erste alle bis letzte externe) - Lücken (10-60 Min, nur extern)
   - ⚠️ **Noch nicht implementiert!**

**Nächste Schritte:**
- [ ] Leistungsgrad-Stempelzeit separat berechnen
- [ ] Lücken-Filter (10-60 Min, nur extern) implementieren
- [ ] Validierung mit Locosoft-Werten

---

*Erstellt: TAG 185 | Autor: Claude AI*
