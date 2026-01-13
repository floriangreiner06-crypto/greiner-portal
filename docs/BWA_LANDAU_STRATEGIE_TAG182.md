# BWA Landau - Strategie zur Lösung

**Datum:** 2026-01-12  
**Status:** ⚠️ Verbleibende Differenz von 19.152,43 €

---

## 🎯 AUSGANGSLAGE

- **DRIVE BE YTD:** -63.160,91 €
- **GlobalCube BE YTD:** -82.219,00 €
- **Differenz:** 19.152,43 €

---

## ✅ WAS WIR BEREITS KORRIGIERT HABEN

1. ✅ **Alle Kosten-Filter:** Variable, Direkte, Indirekte verwenden jetzt `6. Ziffer='2'`
2. ✅ **Umsatz/Einsatz:** Verwenden `branch_number=3`
3. ✅ **Stückzahlen:** Funktionieren korrekt

---

## 🔍 SYSTEMATISCHER ANSATZ

### Option 1: Position-für-Position Analyse

Für jede BWA-Position einzeln berechnen und mit GlobalCube vergleichen:

1. **Umsatz** - Prüfe ob korrekt
2. **Einsatz** - Prüfe ob korrekt
3. **Variable Kosten** - Prüfe ob korrekt
4. **Direkte Kosten** - Prüfe ob korrekt
5. **Indirekte Kosten** - Prüfe ob korrekt
6. **Neutrales Ergebnis** - Prüfe ob korrekt

### Option 2: HAR-Datei erneut analysieren

- Landau HAR-Datei vollständig extrahieren
- Alle Werte aus HAR mit DRIVE vergleichen
- Systematisch jede Differenz identifizieren

### Option 3: GlobalCube direkt abfragen

- Selenium-Scraper für Landau verwenden
- Direkt aus GlobalCube Portal extrahieren
- Live-Vergleich durchführen

### Option 4: Akzeptieren und dokumentieren

- Aktuelle Differenz dokumentieren
- Als "bekannte Abweichung" markieren
- Später mit mehr Daten analysieren

---

## 💡 EMPFEHLUNG

**Option 1 + 2 kombinieren:**
1. Position-für-Position Analyse durchführen
2. HAR-Datei erneut genau prüfen
3. Systematisch jede Differenz aufklären

**Vorteile:**
- Systematisch und nachvollziehbar
- Identifiziert genau die Problem-Position
- Kann dann gezielt korrigiert werden

---

## 📝 NÄCHSTE SCHRITTE

1. **Position-für-Position Script erstellen**
   - Berechnet jede Position einzeln
   - Vergleicht mit GlobalCube-Werten
   - Zeigt genau, wo die Differenz liegt

2. **HAR-Datei erneut analysieren**
   - Extrahiert alle Werte
   - Vergleicht mit DRIVE
   - Identifiziert Abweichungen

3. **Korrektur durchführen**
   - Basierend auf Analyse
   - Systematisch und gezielt

---

## 🤔 ALTERNATIVE

Wenn wir nicht weiterkommen:
- Aktuelle Differenz dokumentieren
- Als "bekannte Abweichung" markieren
- Später mit mehr Zeit/Informationen analysieren
- Fokus auf andere Standorte/Marken legen
