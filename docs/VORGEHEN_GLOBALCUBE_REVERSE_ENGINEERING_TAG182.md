# Vorgehen: GlobalCube Reverse Engineering - TAG 182

**Datum:** 2026-01-12  
**Status:** 🚀 Startbereit

---

## 🎯 ZIEL

**100%ige Übereinstimmung** zwischen DRIVE BWA und GlobalCube BWA für:
- ✅ Alle Standorte/Marken
- ✅ Alle BWA-Positionen
- ✅ Stückzahlen

**Aktuelle Probleme:**
- ⚠️ Landau: Differenz von -7.546,55 € (9%)
- ⚠️ Stückzahlen: Stimmen nicht überein

---

## 📋 3-PHASEN-PLAN

### **Phase 1: Portal Scraping** (Priorität: HOCH) ⏳

**Ziel:** Exakte BWA-Werte direkt aus Cognos Portal extrahieren

**Vorgehen:**
1. ✅ Session-Management implementiert (`cognos_bwa_scraper.py`)
2. ⏳ BWA-Reports finden und navigieren
3. ⏳ Report-Daten scrapen (HTML-Tabellen oder Excel-Export)
4. ⏳ Werte extrahieren und mit DRIVE vergleichen

**Erwartetes Ergebnis:**
- Exakte BWA-Werte für alle Standorte/Marken
- Identifikation aller Differenzen
- Filter-Logik ableiten

**Zeitaufwand:** 1-2 Stunden

---

### **Phase 2: XML-Struktur-Analyse** (Priorität: HOCH) ⏳

**Ziel:** Filter-Logik aus Struktur-Dateien extrahieren

**Vorgehen:**
1. ✅ XML-Parser implementiert (`analyse_globalcube_xml_struktur.py`)
2. ⏳ `Struktur_GuV.xml` vollständig parsen
3. ⏳ Filter-Regeln extrahieren (IF-THEN-Logik)
4. ⏳ Konten-Zuordnungen dokumentieren
5. ⏳ Standort-Filter-Logik identifizieren

**Erwartetes Ergebnis:**
- Vollständige Filter-Logik-Dokumentation
- Konten-Mappings validiert
- Standort-Filter-Logik verstanden

**Zeitaufwand:** 2-3 Stunden

---

### **Phase 3: Systematischer Vergleich** (Priorität: MITTEL) ⏳

**Ziel:** Alle Differenzen identifizieren und korrigieren

**Vorgehen:**
1. ⏳ Vergleichs-Script erstellen
2. ⏳ Alle BWA-Positionen für alle Standorte/Marken vergleichen
3. ⏳ Stückzahlen vergleichen
4. ⏳ Differenzen analysieren
5. ⏳ Korrekturen implementieren

**Erwartetes Ergebnis:**
- Liste aller Differenzen
- Ursachen dokumentiert
- Alle Korrekturen implementiert

**Zeitaufwand:** 2-3 Stunden

---

## 🚀 SOFORTIGE NÄCHSTE SCHRITTE

### 1. Portal Scraping starten

```bash
cd /opt/greiner-portal
python3 scripts/cognos_report_scraper.py
```

**Erwartung:**
- BWA-Reports finden
- Report-Daten scrapen
- Werte extrahieren

---

### 2. XML-Struktur analysieren

```bash
cd /opt/greiner-portal
python3 scripts/analyse_globalcube_xml_struktur.py
```

**Erwartung:**
- GuV-Struktur vollständig geparst
- Filter-Logik extrahiert
- BWA-Positionen identifiziert

---

### 3. Vergleichs-Script erstellen

**Ziel:** Systematischer Vergleich aller Positionen

**Features:**
- Alle Standorte/Marken
- Alle BWA-Positionen
- Monat vs. YTD
- Stückzahlen

---

## 📊 ERWARTETE ERGEBNISSE

### Nach Phase 1:
- ✅ Exakte BWA-Werte für alle Standorte/Marken
- ✅ Validierung der DRIVE-Werte
- ✅ Identifikation von Differenzen

### Nach Phase 2:
- ✅ Vollständige Filter-Logik-Dokumentation
- ✅ Konten-Zuordnungen validiert
- ✅ Standort-Filter-Logik verstanden

### Nach Phase 3:
- ✅ Alle Differenzen identifiziert
- ✅ Ursachen dokumentiert
- ✅ Alle Korrekturen implementiert
- ✅ **100%ige Übereinstimmung erreicht**

---

## 🔧 TOOLS & SKRIPTE

### Bereit:
- ✅ `scripts/cognos_report_scraper.py` - Portal Scraping
- ✅ `scripts/cognos_bwa_scraper.py` - BWA-spezifischer Scraper
- ✅ `scripts/analyse_globalcube_xml_struktur.py` - XML-Analyse
- ✅ `scripts/globalcube_explorer.py` - Allgemeiner Explorer

### Zu erstellen:
- ⏳ `scripts/vergleiche_bwa_systematisch.py` - Systematischer Vergleich

---

## 💡 EMPFEHLUNG

**Start mit Phase 1 (Portal Scraping)**, da:
1. ✅ Schnellste Methode, exakte Werte zu erhalten
2. ✅ Direkter Vergleich mit DRIVE möglich
3. ✅ Filter-Logik kann aus Report-Parametern abgeleitet werden

**Parallel Phase 2 (XML-Analyse)**, da:
1. ✅ Unabhängig von Portal
2. ✅ Struktur-Dateien sind lokal verfügbar
3. ✅ Filter-Logik kann direkt extrahiert werden

---

## 📝 STATUS

- ✅ **Plan erstellt**
- ✅ **Tools vorbereitet**
- ⏳ **Bereit zum Start**

**Soll ich mit Phase 1 (Portal Scraping) beginnen?**
