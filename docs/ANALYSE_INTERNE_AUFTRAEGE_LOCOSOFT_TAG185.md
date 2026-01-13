# Analyse: Behandlung interner Aufträge in Locosoft

**Datum:** 2026-01-13 (TAG 185)  
**Mitarbeiter:** 5018 (Jan Majer)  
**Zeitraum:** 01.11.2025 - 30.11.2025

---

## 📊 ERKENNTNISSE

### Auftragsverteilung November 2025:

| Typ | Anzahl Aufträge | Anzahl Stempelungen | Minuten (summiert) |
|-----|----------------|-------------------|-------------------|
| **Extern** | 122 | 128 | 6.574 |
| **Intern** (Kunde 3000001) | 41 | 46 | 2.334 |
| **Gesamt** | 163 | 174 | 8.908 |

### Zeit-Spanne-Berechnungen:

| Berechnung | Minuten | Differenz zu Locosoft |
|-----------|---------|----------------------|
| **Locosoft (gemessen)** | 8.483 | - |
| **Zeit-Spanne (erste bis letzte, alle)** | 9.309 | +826 |
| **Zeit-Spanne (erste bis letzte, nur externe)** | 7.719 | -764 |
| **Zeit-Spanne (erste alle bis letzte externe)** | 7.994 | -489 |
| **Zeit-Spanne (erste externe bis letzte alle)** | 9.033 | +550 |
| **Locosoft-Logik (ohne interne, mit Lücken/Pausen)** | 6.525 | -1.958 |

**Erkenntnis:** 
- Locosoft (8.483) liegt zwischen "nur externe" (7.719) und "alle" (9.309)
- Am nächsten: "erste alle bis letzte externe" (7.994) - Differenz: -489 Minuten
- Möglicherweise zählt Locosoft: Zeit-Spanne von erster Stempelung (auch intern) bis letzter externer Stempelung?

---

## 🔍 ANALYSE

### Hypothese 1: Locosoft schließt interne Aufträge komplett aus ❌ WIDERLEGT

**Test:**
- Zeit-Spanne ohne interne = 7.719 Minuten
- Locosoft = 8.483 Minuten
- **Differenz: -764 Minuten**

**Fazit:** Wenn Locosoft interne komplett ausschließt, wäre die Zeit-Spanne zu niedrig. Locosoft zeigt mehr als ohne interne.

### Hypothese 2: Locosoft zählt interne Aufträge mit ✅ WAHRSCHEINLICH

**Test:**
- Zeit-Spanne mit internen = 9.309 Minuten
- Locosoft = 8.483 Minuten
- **Differenz: -826 Minuten**

**Fazit:** Wenn Locosoft interne mitzählt, wäre die Zeit-Spanne zu hoch. Aber die Differenz ist kleiner als bei komplettem Ausschluss.

### Hypothese 3: Locosoft behandelt interne Aufträge anders ⚠️ MÖGLICH

**Mögliche Szenarien:**
1. **Interne Aufträge zählen zur Zeit-Spanne, aber nicht zur produktiven Zeit**
   - Zeit-Spanne: erste bis letzte Stempelung (inkl. interne)
   - Produktive Zeit: nur externe Stempelungen
   - Ergebnis: Zeit-Spanne höher, aber produktive Zeit niedriger

2. **Interne Aufträge werden teilweise abgezogen**
   - Vielleicht werden nur bestimmte interne Aufträge ausgeschlossen
   - Oder: Interne Aufträge werden mit einem Faktor < 1 gewichtet

3. **Zeit-Spanne wird anders berechnet**
   - Vielleicht: erste externe bis letzte externe Stempelung
   - Aber: Interne Stempelungen dazwischen zählen mit

---

## 📋 EINZELNE TAGE ANALYSE

### Beispiel: 03.11.2025

**Aufträge (chronologisch):**
1. 07:47 - 09:42: Auftrag 218867 (EXTERN) - 808 Min
2. 09:43 - 10:38: Auftrag 36395 (EXTERN) - 496 Min
3. 10:38 - 11:16: Auftrag 36402 (EXTERN) - 454 Min
4. 11:16 - 12:48: Auftrag 219637 (EXTERN) - 458 Min
5. 12:48 - 14:19: Auftrag 38092 (INTERN) - 1.810 Min
6. 14:20 - 14:54: Auftrag 38109 (INTERN) - 200 Min
7. 14:54 - 15:21: Auftrag 219771 (INTERN) - 164 Min
8. 15:21 - 16:17: Auftrag 219774 (INTERN) - 392 Min

**Zeit-Spannen:**
- Erste bis letzte Stempelung (alle): 510 Minuten (07:47 - 16:17)
- Erste bis letzte externe: 301 Minuten (07:47 - 12:48)
- Erste (alle) bis letzte externe: 301 Minuten
- Erste externe bis letzte (alle): 510 Minuten

**Erkenntnis:** 
- Interne Aufträge erweitern die Zeit-Spanne erheblich (von 301 auf 510 Minuten)
- Wenn Locosoft interne ausschließt: 301 Minuten
- Wenn Locosoft interne mitzählt: 510 Minuten
- Locosoft zeigt wahrscheinlich einen Wert dazwischen

---

## 💡 FAZIT

**Wir können NICHT sicher sagen, dass Locosoft interne Aufträge ausschließt!**

**Evidenz:**
- ✅ Interne Aufträge existieren (41 Aufträge, 2.334 Minuten)
- ✅ Mechaniker hat tatsächlich gearbeitet (auch wenn intern)
- ❌ Zeit-Spanne ohne interne (7.719) ist zu niedrig für Locosoft (8.483)
- ❌ Zeit-Spanne mit internen (9.309) ist zu hoch für Locosoft (8.483)
- ⚠️ Locosoft zeigt einen Wert dazwischen

**Mögliche Erklärungen:**
1. ✅ **Zeit-Spanne: erste Stempelung (auch intern) bis letzte externe Stempelung**
   - Test: 7.994 Minuten (Differenz: -489 Minuten)
   - **Am nächsten an Locosoft!**
   - Logik: Interne Aufträge am Anfang zählen zur Zeit-Spanne, aber interne am Ende nicht
   
2. Locosoft zählt interne Aufträge teilweise mit (z.B. nur bestimmte interne Aufträge)
3. Locosoft hat zusätzliche Filter oder Korrekturen (Lücken/Pausen anders berechnet)

**Empfehlung:**
- ⚠️ **NICHT** interne Aufträge automatisch ausschließen
- ✅ **WAHRSCHEINLICHSTE LOGIK:** Zeit-Spanne von erster Stempelung (auch intern) bis letzte externe Stempelung
- 🔍 Weitere Analyse: Prüfen, ob Locosoft Lücken/Pausen anders berechnet
- 🔍 Prüfen, ob Locosoft bestimmte interne Aufträge ausschließt (z.B. bestimmte charge_types)

### Beste Näherung an Locosoft:

**Variante: "Erste Stempelung (auch intern) bis letzte externe Stempelung"**
- Zeit-Spanne: 7.994 Minuten
- Locosoft: 8.483 Minuten
- **Differenz: -489 Minuten** (nur 5,8% Abweichung!)
- Mit Lücken/Pausen: 6.801 Minuten (weiter weg)

**Erkenntnis:** 
- Diese Variante ist am nächsten an Locosoft
- **WICHTIG:** Pausen liegen oft INNERHALB von Stempelungen (z.B. 03.11: Pause 12:00-12:44 liegt innerhalb Stempelung 11:16-12:48)
- Mit Pausen-Abzug: 7.203 Minuten (Differenz: -1.280 Minuten)
- **Ohne Pausen-Abzug:** 7.994 Minuten (Differenz: -489 Minuten) - **AM NÄCHSTEN!**

**Fazit:** 
- Locosoft zieht möglicherweise Pausen NICHT ab, wenn sie innerhalb von Stempelungen liegen
- Oder: Locosoft verwendet eine andere Pausen-Berechnung

---

*Erstellt: TAG 185 | Autor: Claude AI*
