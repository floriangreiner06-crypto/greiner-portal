# Komplette BWA-Analyse - Zusammenfassung TAG 186

**Datum:** 2026-01-13  
**Status:** 🔍 **SYSTEMATISCHE ANALYSE ABGESCHLOSSEN**

---

## 🎯 ZIEL

Systematische Analyse **ALLER** BWA-Positionen (nicht nur Einsatzwerte!), um die Ursachen der Differenzen zu identifizieren.

---

## ✅ KORREKTE POSITIONEN

### 1. Direkte Kosten ✅
- **Monat:** -16,53 € Differenz (0,01%) ✅
- **YTD:** -94,36 € Differenz (0,01%) ✅
- **Status:** Perfekt!

### 2. Indirekte Kosten ✅
- **Monat:** -0,01 € Differenz (0,00%) ✅
- **YTD:** -6,45 € Differenz (0,00%) ✅
- **Status:** Perfekt!

### 3. Neutrales Ergebnis ✅
- **Monat:** -0,32 € Differenz (0,00%) ✅
- **YTD:** -0,11 € Differenz (0,00%) ✅
- **Status:** Perfekt!

---

## 🚨 PROBLEME IDENTIFIZIERT

### 1. EINSATZ 🚨 **HAUPTPROBLEM**

**Differenzen:**
- **Monat:** +3.222,36 € (0,17%)
- **YTD:** +31.905,97 € (0,35%)

**Aufschlüsselung nach Standort (YTD):**
- Deggendorf Stellantis: 5.096.520,91 €
- Landau: 1.133.115,18 €
- Hyundai: 2.994.133,88 €
- **GESAMT:** 9.223.769,97 €
- **GlobalCube:** 9.191.864,00 €
- **Differenz:** +31.905,97 €

**Prüfung:**
- ✅ Keine Doppelzählungen
- ✅ Filter-Logik korrekt
- ✅ 74xxxx Konten korrekt erfasst

**Fazit:** DRIVE erfasst **31.905,97 € MEHR** als GlobalCube. Die Ursache liegt **NICHT** in der Filter-Logik, sondern möglicherweise:
- GlobalCube schließt bestimmte Konten aus
- GlobalCube verwendet andere Filter-Kriterien
- GlobalCube hat manuelle Anpassungen

---

### 2. VARIABLE KOSTEN 🚨

**Differenzen:**
- **Monat:** -103,64 € (-0,15%) ✅ (akzeptabel)
- **YTD:** -14.809,53 € (-4,87%) 🚨

**Aufschlüsselung nach Kontenbereichen (YTD):**
- 415100-415199: 18.779,51 €
- 435500-435599: 13.286,12 €
- 455000-456999 (KST!=0): 19.593,19 €
- 487000-487099 (KST!=0): 18.613,10 €
- 491000-497899: 233.892,43 €
- **891000-891099: -14.705,88 €** ⚠️ (NEGATIV!)

**Erkenntnis:**
- 891000-891099 hat einen **negativen Wert** (-14.705,88 €)
- Dies reduziert die Variable Kosten fälschlicherweise
- Die Differenz (-14.809,53 €) entspricht fast genau dem negativen 8910xx-Wert

**Fazit:** 8910xx sollte möglicherweise **AUSGESCHLOSSEN** werden aus Variable Kosten für Gesamtbetrieb, oder es gibt ein Problem mit der Zuordnung.

---

### 3. UMSATZ YTD ⚠️

**Differenzen:**
- **Monat:** +0,01 € (0,00%) ✅
- **YTD:** -14.712,52 € (-0,14%) ⚠️

**Erkenntnis:**
- Monat ist perfekt
- YTD hat eine kleine Differenz
- Möglicherweise Rundungsunterschiede oder Zeitpunkt-Unterschiede

---

## 📊 AUSWIRKUNG AUF BERECHNETE WERTE

### Monat (Dezember 2025):
- **DB1:** -3.222,35 € (durch Einsatz verursacht)
- **DB2:** -3.118,71 € (durch Einsatz + Variable Kosten)
- **DB3:** -3.102,18 €
- **BE:** -3.102,17 €
- **UE:** -3.102,49 €

### YTD (Sep-Dez 2025):
- **DB1:** -46.618,49 € (durch Einsatz verursacht)
- **DB2:** -131.808,96 € (durch Einsatz + Variable Kosten)
- **DB3:** -31.714,60 €
- **BE:** -31.708,15 € (entspricht fast genau der Einsatz-Differenz!)
- **UE:** -31.708,26 €

**Erkenntnis:** Die Betriebsergebnis-Differenz (-31.708,15 €) entspricht fast genau der Einsatz-Differenz (+31.905,97 €). Wenn der Einsatz korrekt wäre, wäre das Betriebsergebnis auch korrekt!

---

## 🔍 URSACHEN-ANALYSE

### 1. Einsatz-Differenz (+31.905,97 €)

**Mögliche Ursachen:**
1. **GlobalCube schließt bestimmte Konten aus:**
   - Möglicherweise werden bestimmte 7xxxxx Konten von GlobalCube nicht erfasst
   - Oder: GlobalCube verwendet andere Filter-Kriterien

2. **GlobalCube verwendet andere Filter-Logik:**
   - Möglicherweise verwendet GlobalCube andere Kriterien für Standort-Zuordnung
   - Oder: GlobalCube hat manuelle Anpassungen

3. **Buchungstext-Filter:**
   - Möglicherweise schließt GlobalCube Buchungen mit bestimmten Texten aus
   - Oder: GlobalCube verwendet andere G&V-Filter

**Nächste Schritte:**
- GlobalCube-Konten-Liste für Gesamtbetrieb Einsatz besorgen
- Vergleich: Welche Konten erfasst GlobalCube, die DRIVE nicht erfasst?
- Vergleich: Welche Konten erfasst DRIVE, die GlobalCube nicht erfasst?

---

### 2. Variable Kosten-Differenz (-14.809,53 €)

**Erkenntnis:**
- 891000-891099 hat einen **negativen Wert** (-14.705,88 €)
- Dies reduziert die Variable Kosten fälschlicherweise
- Die Differenz entspricht fast genau dem negativen 8910xx-Wert

**Mögliche Ursachen:**
1. **8910xx sollte ausgeschlossen werden:**
   - Für Gesamtbetrieb sollte 8910xx möglicherweise ausgeschlossen werden
   - Oder: 8910xx gehört zu einer anderen Kategorie

2. **8910xx Zuordnung falsch:**
   - Möglicherweise gehört 8910xx zu indirekten Kosten oder neutralem Ergebnis
   - Oder: 8910xx sollte nur für bestimmte Standorte/Firmen erfasst werden

**Nächste Schritte:**
- Prüfen, ob 8910xx für Gesamtbetrieb ausgeschlossen werden sollte
- Vergleich mit GlobalCube: Wie behandelt GlobalCube 8910xx?

---

## 📋 ZUSAMMENFASSUNG

### ✅ Was funktioniert:
- Direkte Kosten: Perfekt (nur -16,53 € / -94,36 € Differenz)
- Indirekte Kosten: Perfekt (nur -0,01 € / -6,45 € Differenz)
- Neutrales Ergebnis: Perfekt (nur -0,32 € / -0,11 € Differenz)
- Filter-Logik: Keine Doppelzählungen, korrekt implementiert

### 🚨 Was nicht funktioniert:
- **Einsatz:** +31.905,97 € YTD Differenz (verursacht BE-Differenz)
- **Variable Kosten:** -14.809,53 € YTD Differenz (verursacht DB2-Differenz)
- **Umsatz YTD:** -14.712,52 € Differenz (kleines Problem)

### 💡 Erkenntnisse:
1. **Die Filter-Logik ist korrekt** - keine Doppelzählungen
2. **Die Hauptprobleme sind:**
   - Einsatz: DRIVE erfasst 31.905,97 € mehr als GlobalCube
   - Variable Kosten: 8910xx hat negativen Wert, reduziert Kosten fälschlicherweise
3. **Die Betriebsergebnis-Differenz** (-31.708,15 €) entspricht fast genau der Einsatz-Differenz (+31.905,97 €)

---

## 🎯 NÄCHSTE SCHRITTE

1. **GlobalCube-Konten-Liste besorgen:**
   - Welche Konten erfasst GlobalCube für Gesamtbetrieb Einsatz (YTD Sep-Dez 2025)?
   - Vergleich mit DRIVE: Welche Konten fehlen oder sind zu viel?

2. **8910xx Zuordnung klären:**
   - Soll 8910xx für Gesamtbetrieb ausgeschlossen werden?
   - Wie behandelt GlobalCube 8910xx?

3. **Umsatz YTD analysieren:**
   - Warum gibt es eine -14.712,52 € Differenz?
   - Möglicherweise Rundungsunterschiede oder Zeitpunkt-Unterschiede?

---

**Status:** Systematische Analyse abgeschlossen. Hauptprobleme identifiziert. Benötigt: GlobalCube-Konten-Listen für Vergleich.
