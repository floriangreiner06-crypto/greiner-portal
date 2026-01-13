# GlobalCube Struktur-Analyse - Ergebnisse TAG 184

**Datum:** 2026-01-13  
**Status:** ✅ Struktur-Analyse abgeschlossen

---

## 🎯 ZIEL

Vollständige Analyse der GlobalCube-Strukturen (XML) und Vergleich mit DRIVE BWA-Logik, um Differenzen zu identifizieren.

---

## ✅ ERREICHTE ERGEBNISSE

### 1. Struktur_GuV.xml analysiert ✅

**BWA-Hierarchie mit Struktur-IDs:**
- **Struktur_GuV** (ID: 48)
  - **1. Umsatzerlöse** (ID: 50) - 7 Unterpositionen
    - a) Neuwagen (ID: 51)
    - b) Gebrauchtwagen (ID: 52)
    - c) Teile & Zubehör (ID: 53)
    - d) Service (ID: 54)
    - e) Mietwagen (ID: 55)
    - f) Tankstelle (ID: 56)
    - g) Umlagen (ID: 57)
  - **5. Materialaufwand** (ID: 60) - 2 Unterpositionen
  - **6. Personalaufwand** (ID: 70) - 2 Unterpositionen
    - **ad) Ausbildung** (ID: 75) ⭐
  - **8. Sonstige betriebliche Aufwendungen** (ID: 83) - 4 Unterpositionen

**Wichtigste Erkenntnis:**
- ✅ **Ausbildung (ID: 75)** ist eine **separate Position** unter Personalaufwand
- ✅ Bestätigt: **411xxx sollte NICHT in direkten Kosten sein** (bereits korrekt in DRIVE)

### 2. Struktur_Controlling.xml analysiert ✅

**Detaillierte Controlling-Struktur:**
- **Umsatz Opel** (ID: 9) - Eigenverkauf, AOV
- **EW NW Opel** (ID: 11) - Einsatzwerte Neuwagen Opel
- **Umsatz GW** (ID: 12)
- **EW GW** (ID: 13)
- **Umsatz Service** (ID: 16) - 4 Unterpositionen
- **EW Serv. ges.** (ID: 22)
- **Umsatz Teile gesamt** (ID: 25) - 3 Unterpositionen
- **EW OT/ATZ/VW/Honda Teile** (ID: 30)
- **Personalaufwand** (ID: 37)
- **Summe betriebl. Aufwand** (ID: 38) - 33 Unterpositionen

**Wichtigste Erkenntnis:**
- ✅ Controlling-Struktur ist **detaillierter** als GuV-Struktur
- ✅ Zeigt **separate Positionen** für verschiedene Bereiche

### 3. Vergleich mit DRIVE BWA-Logik ✅

**DRIVE verwendet:**
- Kontonummer-Präfixe (81xxxx, 82xxxx, 71xxxx, 72xxxx, etc.)
- Direkte Filterung nach Kontonummer-Bereichen

**GlobalCube verwendet:**
- Struktur-IDs (50, 51, 52, etc.)
- Hierarchische Struktur mit Ebenen

**Problem:**
- ⚠️ **Mapping zwischen Konten und Struktur-IDs fehlt in CSV**
- ⚠️ Kontenrahmen.csv enthält keine direkten BWA-Konten (7xxxxx/8xxxxx/4xxxxx)

---

## 🔍 WICHTIGE ERKENNTNISSE

### 1. Ausbildung (411xxx) - Bestätigt ✅

**Status:** ✅ **KORREKT in DRIVE**

- GlobalCube hat separate Position "Ausbildung" (ID: 75) unter Personalaufwand
- DRIVE schließt 411xxx bereits aus direkten Kosten aus
- **Keine Änderung nötig**

### 2. Konto-Mappings - Offen ⏳

**Problem:**
- Kontenrahmen.csv enthält keine direkten BWA-Konten
- Mapping zwischen Konten (8xxxxx) und Struktur-IDs (50, 51, etc.) fehlt

**Mögliche Lösungen:**
1. **Excel-Exports analysieren** - Enthalten tatsächliche Werte
2. **Portal-Reports scrapen** - Nach Auth-Fix
3. **f_belege Cube analysieren** - Könnte Mappings enthalten

### 3. Personalaufwand - Zu prüfen ⏳

**Finding:**
- Separate Position "Personalaufwand" (ID: 37) in Controlling-Struktur
- DRIVE kategorisiert Personalaufwand-Konten in direkte/indirekte Kosten

**Empfehlung:**
- Prüfe ob Personalaufwand-Konten korrekt zugeordnet sind
- Vergleiche mit GlobalCube Excel-Exports

---

## 📊 NÄCHSTE SCHRITTE

### Priorität HOCH:
1. ⏳ **Excel-Exports analysieren**
   - Enthalten tatsächliche BWA-Werte
   - Können direkt mit DRIVE verglichen werden
   - Keine Auth-Probleme

2. ⏳ **Landau BWA-Differenzen analysieren**
   - Betriebsergebnis: -19.161,51 € Differenz
   - Neutrales Ergebnis: -127,00 € Differenz
   - Verwende Excel-Exports für Vergleich

### Priorität MITTEL:
3. ⏳ **GlobalCube Scraper Auth-Problem beheben**
   - Nachdem Struktur verstanden ist
   - Für automatische Werte-Extraktion

4. ⏳ **f_belege Cube analysieren**
   - Könnte Konto-Mappings enthalten
   - 33 MB, könnte aufwendig sein

---

## 📁 GENERIERTE DATEIEN

- `/opt/greiner-portal/docs/globalcube_analysis/struktur_vergleich_tag184.json`
- `/opt/greiner-portal/scripts/vergleiche_globalcube_struktur_drive.py`
- `/opt/greiner-portal/scripts/analyse_globalcube_kontenrahmen.py`

---

## 💡 FAZIT

**Was funktioniert:**
- ✅ Struktur-Analyse erfolgreich
- ✅ Ausbildung-Position bestätigt (411xxx korrekt ausgeschlossen)
- ✅ Hierarchie verstanden

**Was noch fehlt:**
- ⏳ Konto-Mappings (Konten → Struktur-IDs)
- ⏳ Vergleich mit tatsächlichen Werten (Excel-Exports)

**Empfehlung:**
- **Nächster Schritt:** Excel-Exports analysieren für direkten Vergleich mit DRIVE
- **Danach:** Scraper Auth-Problem beheben für automatische Extraktion

---

*Erstellt: TAG 184 | Autor: Claude AI*
