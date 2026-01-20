# Analyse: Verschobene Stempelpositionen - Auftrag 38590

**Datum:** 2026-01-16  
**TAG:** 195  
**Problem:** Locosoft zeigt 17 Stunden, unsere Berechnung zeigt 1.63 Stunden

---

## 🔍 Problem-Identifikation

### Auftrag 38590 (Tobias 5007)

**Stempelungen:**
- **Zeitblock 1:** 02.12.25 16:13 - 17:10 (56 Min) auf Position 2/4 **UND** 2/6
- **Zeitblock 2:** 03.12.25 08:02 - 08:45 (42 Min) auf Position 2/4 **UND** 2/6

**Locosoft-Warnung:**
> "Es liegen automatisch verschobene Stempelpositionen vor!"

---

## 📊 Berechnungs-Unterschiede

### Unsere aktuelle Berechnung (anteilig):

**Zeitblock 1 (56 Min auf 2 Positionen):**
- Position 2/4: 28 Min (anteilig)
- Position 2/6: 28 Min (anteilig)

**Zeitblock 2 (42 Min auf 2 Positionen):**
- Position 2/4: 21 Min (anteilig)
- Position 2/6: 21 Min (anteilig)

**Gesamt:**
- Position 2/4: 28 + 21 = 49 Min (0.82 Stunden)
- Position 2/6: 28 + 21 = 49 Min (0.82 Stunden)
- **Gesamt (dedupliziert): 98 Min (1.63 Stunden)**

### Locosoft-Berechnung (vollständig pro Position):

**Zeitblock 1 (56 Min auf 2 Positionen):**
- Position 2/4: **56 Min** (vollständig)
- Position 2/6: **56 Min** (vollständig)

**Zeitblock 2 (42 Min auf 2 Positionen):**
- Position 2/4: **42 Min** (vollständig)
- Position 2/6: **42 Min** (vollständig)

**Gesamt:**
- Position 2/4: 56 + 42 = 98 Min (1.63 Stunden)
- Position 2/6: 56 + 42 = 98 Min (1.63 Stunden)
- **Gesamt (summiert): 196 Min (3.27 Stunden)**

---

## ❓ Was zeigt Locosoft im Screenshot?

**Position 2.06 (Tobias):**
- Eintrag 1: Zeitbasis 9.50 Stunden
- Eintrag 2: Zeitbasis 7.17 Stunden
- **Summe: 16.67 Stunden**

**Das entspricht NICHT unserer Berechnung!**

**Mögliche Erklärungen:**

1. **Locosoft summiert die Zeit vollständig pro Position:**
   - 56 Min + 42 Min = 98 Min = 1.63 Stunden ❌ (zu wenig)

2. **Locosoft verwendet eine andere Zeitbasis:**
   - Vielleicht "Realzeit" statt "Zeitbasis"?
   - Realzeit 1: 17:10 (1 Stunde 10 Min?)
   - Realzeit 2: 8:45 (8 Stunden 45 Min?)

3. **Locosoft berücksichtigt verschobene Positionen anders:**
   - Vielleicht werden verschobene Positionen mehrfach gezählt?
   - Oder gibt es historische Stempelungen, die verschoben wurden?

---

## 🔧 Nächste Schritte

1. **Prüfe `order_positions` Feld:**
   - In der DB gibt es `order_positions: X` - was bedeutet das?
   - Ist das ein Hinweis auf verschobene Positionen?

2. **Prüfe historische Stempelungen:**
   - Gibt es `is_historic = true` Einträge?
   - Werden diese in Locosoft anders behandelt?

3. **Prüfe Locosoft "Realzeit" vs "Zeitbasis":**
   - Was ist der Unterschied?
   - Welche verwendet Locosoft für die Summe?

4. **Prüfe andere Aufträge mit verschobenen Positionen:**
   - Gibt es ein Muster?
   - Wie werden diese in Locosoft berechnet?

---

## 📝 Erkenntnisse

1. **Verschobene Positionen sind das Problem:**
   - Wenn eine Stempelung auf mehrere Positionen gleichzeitig geht
   - Locosoft behandelt diese anders als unsere Berechnung

2. **Unsere anteilige Verteilung ist falsch:**
   - Locosoft summiert die Zeit **vollständig pro Position**
   - Nicht anteilig!

3. **16.67 Stunden sind nicht erklärbar:**
   - Weder durch vollständige noch durch anteilige Summierung
   - Möglicherweise andere Zeitbasis oder historische Daten?

---

**Erstellt:** TAG 195 (16.01.2025)  
**Status:** 🔍 **Weitere Analyse erforderlich**
