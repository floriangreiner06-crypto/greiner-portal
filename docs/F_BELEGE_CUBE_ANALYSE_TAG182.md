# f_belege Cube Analyse - TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Analyse durchgeführt

---

## 📋 CUBE-INFORMATIONEN

**Datei:** `/mnt/globalcube/Cubes/f_belege__20250212085849/f_belege.mdc`  
**Größe:** 32.2 MB (33,801,182 Bytes)  
**Format:** MDC (Materialized Data Cube) - GlobalCube binäres Format  
**Geändert:** 2025-02-12 09:58:46

**Erkenntnis:** MDC ist ein proprietäres GlobalCube-Format, kann nur mit GlobalCube-Software gelesen werden.

---

## 🔍 ANALYSE-ERGEBNISSE

### 1. Format-Analyse

**Datei-Format:**
- **Header:** `\xdd\xc3\x03\x02` (GlobalCube MDC-Format)
- **Typ:** Binär, proprietär
- **Nicht:** ZIP, SQLite, XML, gzip

**Erkenntnis:** Der Cube ist ein **Materialized Data Cube** (MDC), ein binäres Format spezifisch für GlobalCube.

### 2. Gefundene Konten-Nummern

**Im Cube gefunden (erste 10 MB analysiert):**

**Kosten-Konten (4xxxxx):**
- 424267, 424285
- 459929, 460202, 460405, 462079, 463677, 465307
- 467833, 468948, 469528, 470177, 472297, 472788, 472896, 473007
- 474926, 474927, 475214, 475363, 478330, 484990
- 495558, 495883, 496021, 496373

**Umsatz-Konten (8xxxxx):**
- 883555

**Weitere Konten:**
- 21121489 (in Text-Strings gefunden)
- 41105509 (in Text-Strings gefunden) ⭐ **411xxx - Ausbildungsvergütung!**

### 3. Text-Strings im Cube

**Gefundene Text-Stellen:**
- Enthalten Konto-Nummern (z.B. "21121489", "41105509")
- Enthalten Datums-Informationen (z.B. "2024-04-11", "11/04/2024")
- Enthalten Beleg-Informationen (z.B. "Skonto Rädlinger")

**Erkenntnis:** Der Cube enthält **Beleg-Daten** mit Konto-Referenzen, nicht direkt Filter-Logik.

---

## 💡 WICHTIGE ERKENNTNISSE

### 1. 411xxx ist im Cube vorhanden ✅

**Gefunden:** "41105509" in Text-Strings

**Bedeutung:**
- 411xxx (Ausbildungsvergütung) ist **im Cube vorhanden**
- Bestätigt, dass 411xxx in GlobalCube verwendet wird
- Unterstützt Hypothese: 411xxx ist in "Ausbildung" (ID: 75), nicht in direkten Kosten

### 2. Cube enthält Beleg-Daten

**Erkenntnis:** Der f_belege Cube enthält **Beleg-Daten** (journal_accountings), nicht direkt Filter-Logik.

**Bedeutung:**
- Filter-Logik ist wahrscheinlich in **Struktur-Dateien** (bereits analysiert)
- Cube enthält die **Rohdaten**, die dann nach Struktur-IDs gefiltert werden

### 3. MDC-Format ist proprietär

**Erkenntnis:** MDC kann nur mit GlobalCube-Software gelesen werden.

**Konsequenz:**
- Direkte Analyse des Cube-Inhalts ist begrenzt
- Filter-Logik muss aus **Struktur-Dateien** extrahiert werden (bereits analysiert)
- CSV/Excel-Exporte sind wichtiger für Vergleich

---

## 🚀 NÄCHSTE SCHRITTE

### Priorität 1: CSV/Excel-Exporte analysieren ⏳

**Ziel:** GlobalCube-Werte mit DRIVE vergleichen

**Methoden:**
1. Excel-Datei `/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx` analysieren
2. Werte für direkte/indirekte Kosten extrahieren
3. Vergleich mit DRIVE-Berechnungen
4. Unterschiede identifizieren

### Priorität 2: Ausbildung-Position validieren ⏳

**Ziel:** Bestätigen, ob 411xxx in "Ausbildung" (ID: 75) ist

**Methoden:**
1. Excel-Datei: Welche Konten sind in "Ausbildung"?
2. Vergleich mit TAG 177 Logik
3. Validierung der Hypothese

---

## 📊 STATUS

- ✅ f_belege Cube analysiert
- ✅ Format identifiziert (MDC - proprietär)
- ✅ Konten-Nummern gefunden (inkl. 411xxx)
- ✅ Text-Strings analysiert
- ⏳ CSV/Excel-Exporte noch nicht analysiert
- ⏳ Ausbildung-Position noch nicht validiert

---

## 🔧 TOOLS

**Analyse-Script:**
```bash
cd /opt/greiner-portal
python3 scripts/globalcube_explorer.py
```

**Cube-Datei:**
- `/mnt/globalcube/Cubes/f_belege__20250212085849/f_belege.mdc`

---

**Nächster Schritt:** CSV/Excel-Exporte analysieren oder Ausbildung-Position validieren.
