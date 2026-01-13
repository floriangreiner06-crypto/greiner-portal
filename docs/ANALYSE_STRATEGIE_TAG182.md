# BWA-Analyse Strategie - TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Strategie definiert

---

## 🎯 ZIEL

Die tatsächliche GlobalCube BWA-Filter-Logik verstehen, um DRIVE-Berechnungen zu korrigieren.

---

## ❓ IST REPORT-SCRAPING NOTWENDIG?

### Problem mit Excel-Exporten

**Problem:** Excel-Exporte sind abhängig vom "Drill-Grad" im Report
- Verschiedene Drill-Level → verschiedene Werte
- Nicht zuverlässig für Filter-Logik-Analyse

**Frage:** Müssen wir Reports direkt scrapen?

---

## ✅ ALTERNATIVE: STRUKTUR-BASIERTE ANALYSE

### Was wir bereits haben:

1. **Struktur-Dateien analysiert** ✅
   - `Struktur_GuV.xml` → BWA-Hierarchie mit Struktur-IDs
   - `Struktur_Controlling.xml` → Controlling-Struktur
   - Separate "Ausbildung"-Position (ID: 75) gefunden

2. **f_belege Cube analysiert** ✅
   - Enthält Beleg-Daten
   - 411xxx Konten gefunden

3. **Excel-Exporte vorhanden** ✅
   - Enthalten BWA-Werte
   - Können für Vergleich verwendet werden

### Was wir brauchen:

1. **Konto-Mappings zu Struktur-IDs**
   - Welche Konten gehören zu welcher Struktur-ID?
   - Gibt es eine Mapping-Tabelle?

2. **Filter-Logik für direkte/indirekte Kosten**
   - Wie werden Konten den Struktur-Positionen zugeordnet?
   - Welche Filter werden verwendet?

---

## 💡 STRATEGIE: WERTE-VERGLEICH STATT REPORT-SCRAPING

### Ansatz 1: Excel-Werte korrekt extrahieren ⏳

**Warum:**
- Excel enthält die tatsächlichen GlobalCube-Werte
- Unabhängig vom Drill-Grad (wenn wir die richtigen Spalten finden)
- Vergleich mit DRIVE möglich

**Schritte:**
1. Excel-Spalten-Header identifizieren (Monat, YTD, Vorjahr)
2. Werte für Dezember 2025 und YTD Sep-Dez 2025 extrahieren
3. Vergleich mit DRIVE durchführen
4. Unterschiede analysieren → Filter-Logik ableiten

**Vorteile:**
- ✅ Excel ist bereits vorhanden
- ✅ Enthält tatsächliche Werte
- ✅ Vergleich möglich
- ✅ Kein Scraping nötig

**Nachteile:**
- ⚠️ Spalten müssen korrekt identifiziert werden
- ⚠️ Werte müssen korrekt interpretiert werden

---

### Ansatz 2: Struktur-Dateien vertiefen ⏳

**Warum:**
- Struktur-Dateien enthalten die Filter-Logik
- Bereits teilweise analysiert
- Könnte Konto-Mappings enthalten

**Schritte:**
1. Alle XML-Strukturen vollständig analysieren
2. Nach Konto-Mappings suchen
3. Filter-Regeln extrahieren
4. Ausbildung-Position (411xxx) validieren

**Vorteile:**
- ✅ Direkte Filter-Logik
- ✅ Kein Scraping nötig
- ✅ Bereits begonnen

**Nachteile:**
- ⚠️ Keine direkten Konto-Mappings gefunden (bisher)
- ⚠️ Komplexe Struktur

---

### Ansatz 3: Report-Scraping (nur wenn nötig) ⚠️

**Warum:**
- Reports enthalten die tatsächliche Filter-Logik
- Könnte JavaScript mit Filter-Parametern enthalten

**Schritte:**
1. Reports im Portal finden
2. HTML scrapen
3. JavaScript analysieren
4. Filter-Parameter extrahieren

**Vorteile:**
- ✅ Direkte Filter-Logik aus Reports
- ✅ Aktuelle Werte

**Nachteile:**
- ⚠️ Komplex (HTML-Parsing, JavaScript-Analyse)
- ⚠️ Reports müssen gefunden werden
- ⚠️ Portal-Struktur muss verstanden werden

---

## 🎯 EMPFEHLUNG

### Priorität 1: Excel-Werte korrekt extrahieren ✅

**Warum:**
- Excel enthält die tatsächlichen GlobalCube-Werte
- Vergleich mit DRIVE möglich
- Kein Scraping nötig

**Nächste Schritte:**
1. Excel-Spalten-Header identifizieren
2. Werte für Dezember 2025 und YTD Sep-Dez 2025 extrahieren
3. Vergleich mit DRIVE durchführen
4. Unterschiede analysieren

### Priorität 2: Struktur-Dateien vertiefen ✅

**Warum:**
- Struktur-Dateien enthalten Filter-Logik
- Bereits teilweise analysiert

**Nächste Schritte:**
1. Alle XML-Strukturen vollständig analysieren
2. Nach Konto-Mappings suchen
3. Filter-Regeln extrahieren

### Priorität 3: Report-Scraping (nur wenn nötig) ⚠️

**Warum:**
- Nur wenn Ansatz 1 und 2 nicht ausreichen

**Nächste Schritte:**
1. Reports im Portal finden
2. HTML scrapen
3. JavaScript analysieren

---

## 📊 FAZIT

**Report-Scraping ist NICHT notwendig, wenn wir:**
1. ✅ Excel-Werte korrekt extrahieren können
2. ✅ Struktur-Dateien vollständig analysieren
3. ✅ Werte mit DRIVE vergleichen und Filter-Logik ableiten

**Report-Scraping ist notwendig, wenn:**
- Excel-Werte nicht korrekt extrahiert werden können
- Struktur-Dateien keine ausreichenden Informationen enthalten
- Filter-Logik nicht ableitbar ist

---

## 🚀 NÄCHSTE SCHRITTE

1. ⏳ **Excel-Spalten-Header identifizieren**
   - Welche Spalte = Monat Dezember 2025?
   - Welche Spalte = YTD Sep-Dez 2025?
   - Welche Spalte = Vorjahr?

2. ⏳ **Werte extrahieren und mit DRIVE vergleichen**
   - Direkte Kosten
   - Indirekte Kosten
   - Betriebsergebnis

3. ⏳ **Unterschiede analysieren**
   - Welche Konten fehlen in DRIVE?
   - Welche Konten sind zusätzlich in DRIVE?
   - Filter-Logik ableiten

---

**Status:** Strategie definiert, Excel-Analyse als Priorität 1
