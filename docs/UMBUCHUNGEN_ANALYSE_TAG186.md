# Umbuchungen zwischen Opel Deggendorf und Opel Landau - Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **ANALYSE ABGESCHLOSSEN**

---

## 🎯 ERKENNTNISSE

### 1. Buchungen mit 6. Ziffer='1' UND branch=3

**Gefunden:** 45 Buchungen, Wert: 9,219.19 €

**Analyse:**
- Diese Buchungen haben `6. Ziffer='1'` (deutet auf Deggendorf hin)
- Aber `branch=3` (deutet auf Landau hin)
- Sie werden durch **Landau-Filter** erfasst: `branch=3 AND subsidiary=1`
- Sie werden **NICHT** durch Deggendorf-Filter erfasst: `branch != 3` schließt sie aus
- **Status:** ✅ Korrekt zugeordnet (zu Landau)

---

### 2. 74xxxx Konten mit branch=1 und 6. Ziffer='2' ⚠️

**Gefunden:** 289 Buchungen, Wert: 260,160.05 €

**Analyse:**
- Diese Buchungen haben `branch=1` (Deggendorf)
- Aber `6. Ziffer='2'` (deutet auf Landau hin!)
- Sie werden durch **Deggendorf-Filter** erfasst: `74xxxx AND branch=1`
- **Problem:** Möglicherweise gehören sie zu Landau und werden fälschlicherweise Deggendorf zugeordnet!

**Aktuelle Filter-Logik:**
```sql
-- Deggendorf Opel Filter:
(6. Ziffer='1' OR (74xxxx AND branch=1)) AND subsidiary=1 AND branch != 3
```

**Das bedeutet:**
- 74xxxx Konten mit `branch=1` werden **immer** Deggendorf zugeordnet
- Auch wenn `6. Ziffer='2'` auf Landau hindeutet!

**Mögliche Lösung:**
- 74xxxx Konten mit `branch=1` UND `6. Ziffer='2'` sollten möglicherweise zu Landau gehören?
- Oder sollten sie ausgeschlossen werden?

---

### 3. Explizite Umbuchungen

**Gefunden:** 4 Buchungen, Wert: 2,212.35 €

**Beispiele:**
- "Umbuchung Fg. 42225": 23,212.35 €
- "Umbuchung L+G 01/2025": -7,000.00 €
- "Umbuchung Lohn/Gehalt 03/25": -7,000.00 €
- "Umbuchung Lohn/Gehalt 06/2025": -7,000.00 €

**Analyse:**
- Diese sind explizit als Umbuchungen markiert
- Summe: 2,212.35 € (relativ gering)
- Könnten möglicherweise ausgeschlossen werden müssen?

---

## 🔍 PROBLEM-ANALYSE

### Mögliche Doppelzählung durch 74xxxx Konten

**74xxxx Konten-Verteilung:**

| branch | 6. Ziffer | Buchungen | Wert |
|--------|-----------|-----------|------|
| 1 | 1 | 938 | 741,857.61 € |
| 1 | 2 | 289 | 260,160.05 € ⚠️ |
| 3 | 1 | 6 | 0.02 € |
| 3 | 2 | 1 | 292.80 € |

**Problem:**
- 74xxxx Konten mit `branch=1` und `6. Ziffer='2'` (260,160.05 €) werden Deggendorf zugeordnet
- Aber `6. Ziffer='2'` deutet auf Landau hin!
- Möglicherweise sollten diese zu Landau gehören?

**Aktuelle Filter-Logik:**
- Deggendorf: `74xxxx AND branch=1` (erfasst alle 74xxxx mit branch=1, unabhängig von 6. Ziffer)
- Landau: `branch=3 AND subsidiary=1` (erfasst nur branch=3)

**Frage:**
- Sollten 74xxxx Konten mit `branch=1` UND `6. Ziffer='2'` zu Landau gehören?
- Oder sollten sie ausgeschlossen werden?

---

## 📋 NÄCHSTE SCHRITTE

1. **Prüfe, ob 74xxxx Konten mit branch=1 und 6. Ziffer='2' zu Landau gehören sollten:**
   - Analysiere die posting_text dieser Buchungen
   - Prüfe, ob sie Landau-spezifisch sind

2. **Prüfe, ob GlobalCube diese Konten anders zuordnet:**
   - Werden sie in GlobalCube zu Landau zugeordnet?
   - Oder werden sie ausgeschlossen?

3. **Prüfe, ob die 260,160.05 € die Differenz erklären:**
   - GlobalCube: 9,191,864.00 €
   - DRIVE: 26,023,519.41 €
   - Differenz: 16,831,655.41 €
   - Die 260k € erklären nur einen kleinen Teil, aber es könnte ein Hinweis sein!

---

**KRITISCHE ERKENNTNIS:** 74xxxx Konten mit `branch=1` und `6. Ziffer='2'` (260,160.05 €) werden möglicherweise falsch zugeordnet! Sie sollten möglicherweise zu Landau gehören, nicht zu Deggendorf!
