# GlobalCube BWA Analyse - Ergebnisse TAG 182

**Datum:** 2026-01-12  
**Status:** 🔍 Analyse läuft

---

## 🎯 ZIEL

Die tatsächliche GlobalCube BWA-Logik durch direkte Analyse der GlobalCube-Strukturen, Cubes und Portal-Reports extrahieren.

---

## ✅ DURCHGEFÜHRTE ANALYSEN

### 1. GlobalCube Strukturen analysiert

**Gefundene Strukturen:**
- ✅ `Struktur_GuV.xml` - GUV/BWA-Hierarchie mit Struktur-IDs
- ✅ `Struktur_Controlling.xml` - Controlling-Struktur (Umsatz, Einsatz, Kosten nach Bereichen)
- ✅ `Kontenrahmen/Kontenrahmen.csv` - Konto-Mapping (Format: Konto_Nr, Konto_Bezeichnung, Konto_Art, Kostenstelle, STK)

**Wichtige Erkenntnisse:**
- GuV-Struktur zeigt **exakte BWA-Hierarchie** mit Struktur-IDs
- Separate "Ausbildung"-Position (ID: 75) unter Personalaufwand
- Controlling-Struktur zeigt Umsatz/Einsatz nach Bereichen (NW, GW, Service, Teile)

### 2. Konto-Mappings

**Problem:** Kontenrahmen CSV enthält keine Konten im Format 7xxxxx/8xxxxx/4xxxxx
- Mögliche Ursachen:
  - Konten sind anders formatiert (z.B. mit führenden Nullen: 000800001)
  - CSV enthält nur eine Teilmenge
  - Mapping erfolgt über andere Mechanismen

**Nächste Schritte:**
- Kontenrahmen CSV genauer analysieren (verschiedene Formate prüfen)
- Nach Mapping-Tabellen in anderen Dateien suchen
- GlobalCube Portal-Reports analysieren

### 3. Vorhandene Analyse-Scripts

**Gefundene Scripts:**
- `entschluessle_globalcube_filter.py` - Filter-Logik für Stückzahlen
- `entschluessle_globalcube_final.py` - Finale Filter-Logik für Stückzahlen
- `vergleiche_bwa_globalcube.py` - BWA-Vergleich (zu prüfen)
- `analyse_globalcube_filter.py` - Filter-Analyse

**Erkenntnis:** Vorhandene Scripts analysieren hauptsächlich **Stückzahlen**, nicht die **BWA-Kosten-Logik**.

---

## 🔍 WICHTIGE ERKENNTNISSE

### 1. GuV-Struktur zeigt BWA-Hierarchie

```
Struktur_GuV (ID: 48)
└── GuV (ID: 49)
    ├── 1. Umsatzerlöse (ID: 50)
    │   ├── a) Neuwagen (ID: 51)
    │   ├── b) Gebrauchtwagen (ID: 52)
    │   └── ...
    ├── 5. Materialaufwand (ID: 60)
    │   ├── a) Aufwendungen für Roh-,Hilfs- und Betriebsstoffe... (ID: 61)
    │   └── b) Aufwendungen für bezogene Leistungen (ID: 69)
    ├── 6. Personalaufwand (ID: 70)
    │   ├── a) Löhne und Gehälter (ID: 71)
    │   │   ├── ad) Ausbildung (ID: 75) ⭐
    │   │   └── ...
    │   └── ...
    └── 8. Sonstige betriebliche Aufwendungen (ID: 83)
```

**Hypothese:** 411xxx (Ausbildungsvergütung) könnte in "ad) Ausbildung" (ID: 75) sein, **NICHT in direkten Kosten**.

### 2. Controlling-Struktur zeigt Bereichs-Mappings

```
Struktur_Controlling (ID: 1)
├── Umsatz Opel (ID: 9)
├── EW NW Opel (ID: 11)
├── Umsatz GW (ID: 12)
├── EW GW (ID: 13)
├── Umsatz Service (ID: 16)
├── EW Serv. ges. (ID: 22)
├── Personalaufwand (ID: 37)
└── Summe betriebl. Aufwand (ID: 38)
    ├── Fremdarbeiten (ID: 54)
    ├── Miete und Pacht (ID: 55)
    ├── Reisekosten (ID: 67)
    ├── Kfz-Kosten (ID: 68)
    ├── Werbekosten (ID: 69)
    ├── Fortbildungskosten (ID: 77) ⭐
    └── ...
```

**Erkenntnis:** Controlling-Struktur zeigt detaillierte Kosten-Positionen, die möglicherweise direkten/indirekten Kosten zugeordnet werden.

### 3. Keine direkten Konto-Mappings in XML-Strukturen

**Problem:** Die XML-Strukturen enthalten **keine direkten Konto-Mappings** (z.B. "411xxx → Struktur-ID 75").

**Mögliche Erklärungen:**
1. Mapping erfolgt über **andere Dateien** (z.B. in Cubes oder Datenbank)
2. Mapping erfolgt **dynamisch** im GlobalCube Portal
3. Mapping erfolgt über **Filter-Regeln** (z.B. "alle Konten 411xxx → Ausbildung")

---

## 🚀 NÄCHSTE SCHRITTE

### Priorität 1: GlobalCube Portal Reports analysieren

**Ziel:** BWA-Reports im Portal finden und Filter-Logik extrahieren

**Methoden:**
1. Portal-Zugriff testen (Login erforderlich?)
2. BWA-Reports identifizieren
3. Filter-Parameter extrahieren
4. JavaScript-Logik analysieren (falls vorhanden)

### Priorität 2: Konto-Mappings finden

**Ziel:** Welche Konten gehören zu welcher Struktur-ID?

**Methoden:**
1. Kontenrahmen CSV genauer analysieren (verschiedene Formate)
2. Nach Mapping-Tabellen in anderen Dateien suchen
3. f_belege Cube analysieren (könnte Mapping enthalten)
4. Andere XML-Strukturen prüfen

### Priorität 3: Ausbildung-Position (411xxx) analysieren

**Ziel:** Bestätigen, ob 411xxx in "Ausbildung" (ID: 75) ist

**Methoden:**
1. GlobalCube Portal: BWA-Report für "Ausbildung" prüfen
2. Welche Konten sind in "Ausbildung" enthalten?
3. Vergleich mit TAG 177 Logik (411xxx ausschließen)

### Priorität 4: Filter-Logik für direkte/indirekte Kosten

**Ziel:** Wie werden direkte/indirekte Kosten gefiltert?

**Methoden:**
1. GlobalCube Portal: BWA-Report für direkte/indirekte Kosten prüfen
2. Welche Filter werden verwendet?
3. Vergleich mit aktueller DRIVE-Logik

---

## 📝 HYPOTHESEN

### Hypothese 1: Ausbildung (411xxx)

**Möglichkeit A:** 411xxx ist in "Ausbildung" (ID: 75) → **NICHT in direkten Kosten**
- ✅ Würde TAG 177 Logik erklären (411xxx ausschließen)
- ✅ Struktur zeigt separate "Ausbildung"-Position

**Möglichkeit B:** 411xxx ist in direkten Kosten, aber GlobalCube filtert es anders
- ⚠️ Würde nicht erklären, warum wir 411xxx ausschließen müssen

### Hypothese 2: Struktur-basierte Filterung

GlobalCube könnte **struktur-basiert** filtern:
- Konten werden Struktur-IDs zugeordnet
- Filter basieren auf Struktur-IDs, nicht direkt auf Konten-Nummern
- Erklärt, warum keine direkten Konto-Mappings in XML gefunden wurden

### Hypothese 3: Zeitraum-abhängige Logik

**Problem:** TAG 177 Logik war für August 2025 korrekt, aber für Dezember 2025 nicht.

**Möglichkeit:** GlobalCube verwendet **zeitraum-abhängige Filter** oder **verschiedene Strukturen** für verschiedene Zeiträume.

---

## 🔧 TOOLS

**Explorer-Script:**
```bash
cd /opt/greiner-portal
python3 scripts/globalcube_explorer.py
```

**Manuelle Analyse:**
```bash
# GuV-Struktur extrahieren
unzip -p /mnt/globalcube/GCStruct/AutohausGreiner_20260109_161135.zip Xml/Struktur_GuV.xml > /tmp/guv.xml
cat /tmp/guv.xml

# Controlling-Struktur extrahieren
unzip -p /mnt/globalcube/GCStruct/AutohausGreiner_20260109_161135.zip Xml/Struktur_Controlling.xml > /tmp/controlling.xml
cat /tmp/controlling.xml
```

---

## 📊 STATUS

- ✅ GlobalCube Strukturen analysiert
- ✅ GuV-Hierarchie identifiziert
- ✅ Controlling-Struktur identifiziert
- ⏳ Konto-Mappings noch nicht gefunden
- ⏳ Filter-Logik noch nicht extrahiert
- ⏳ Portal-Reports noch nicht analysiert

---

**Nächster Schritt:** GlobalCube Portal Reports analysieren oder Konto-Mappings in anderen Dateien suchen.
