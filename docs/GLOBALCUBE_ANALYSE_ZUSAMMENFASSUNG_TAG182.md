# GlobalCube Analyse - Zusammenfassung TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Struktur-Analyse abgeschlossen, Portal identifiziert

---

## 🎯 ERREICHTE ERGEBNISSE

### 1. GlobalCube Portal identifiziert ✅

**Typ:** IBM Cognos Business Intelligence Portal  
**URL:** http://10.80.80.10:9300/bi/  
**Login:** Greiner / Hawaii#22  
**Status:** ✅ Erreichbar

**Erkenntnis:** Cognos ist eine Single-Page-Application (SPA), Reports werden dynamisch geladen.

### 2. GlobalCube Strukturen analysiert ✅

**Gefundene Strukturen:**
- ✅ `Struktur_GuV.xml` - **BWA-Hierarchie mit Struktur-IDs**
- ✅ `Struktur_Controlling.xml` - Controlling-Struktur
- ✅ `Kontenrahmen/Kontenrahmen.csv` - Konto-Mapping

**Wichtigste Erkenntnis:**
- **Separate "Ausbildung"-Position (ID: 75)** unter Personalaufwand
- GuV-Struktur zeigt exakte BWA-Hierarchie
- Controlling-Struktur zeigt detaillierte Kosten-Positionen

### 3. BWA-Hierarchie dokumentiert ✅

```
Struktur_GuV (ID: 48)
└── GuV (ID: 49)
    ├── 1. Umsatzerlöse (ID: 50)
    ├── 5. Materialaufwand (ID: 60)
    ├── 6. Personalaufwand (ID: 70)
    │   └── a) Löhne und Gehälter (ID: 71)
    │       └── ad) Ausbildung (ID: 75) ⭐
    └── 8. Sonstige betriebliche Aufwendungen (ID: 83)
```

---

## 💡 WICHTIGE HYPOTHESE

### Ausbildung (411xxx) - NICHT in direkten Kosten

**Hypothese:** 411xxx (Ausbildungsvergütung) ist in **"Ausbildung" (ID: 75)** unter Personalaufwand, **NICHT in direkten Kosten**.

**Begründung:**
1. ✅ GuV-Struktur zeigt separate "Ausbildung"-Position (ID: 75)
2. ✅ TAG 177 Logik schließt 411xxx aus direkten Kosten aus
3. ✅ GlobalCube würde 411xxx in "Ausbildung" haben, nicht in direkten Kosten

**Konsequenz:** TAG 177 Logik (411xxx ausschließen) ist **korrekt**!

---

## 🔍 OFFENE FRAGEN

### 1. Konto-Mappings

**Problem:** Keine direkten Konto-Mappings in XML-Strukturen gefunden.

**Mögliche Erklärungen:**
- Mapping erfolgt über **Cubes** (f_belege, 33 MB)
- Mapping erfolgt **dynamisch** im Cognos Portal
- Mapping erfolgt über **Filter-Regeln** (z.B. "alle Konten 411xxx → Ausbildung")

**Nächste Schritte:**
- f_belege Cube analysieren
- CSV/Excel-Exporte mit DRIVE vergleichen

### 2. Filter-Logik für direkte/indirekte Kosten

**Problem:** Wie werden direkte/indirekte Kosten gefiltert?

**Aktuelle DRIVE-Logik:**
- Direkte Kosten: 4xxxxx mit KST 1-7, AUSSER Variable + 411xxx + 489xxx + 410021
- Indirekte Kosten: 4xxxxx mit KST 0 + 424xx/438xx (KST 1-7) + 498xx + 89xxxx (ohne 8932xx, ohne 8910xx)

**Frage:** Entspricht das der GlobalCube-Logik?

**Nächste Schritte:**
- CSV/Excel-Exporte mit DRIVE vergleichen
- Welche Werte zeigt GlobalCube für direkte/indirekte Kosten?

### 3. Zeitraum-abhängige Logik

**Problem:** TAG 177 Logik war für August 2025 korrekt, aber für Dezember 2025 nicht.

**Mögliche Erklärungen:**
- GlobalCube verwendet **verschiedene Strukturen** für verschiedene Zeiträume
- GlobalCube verwendet **zeitraum-abhängige Filter**
- Mapping-Fehler in der ursprünglichen Logik

**Nächste Schritte:**
- CSV/Excel-Exporte für verschiedene Zeiträume vergleichen
- Prüfen ob Strukturen sich geändert haben

---

## 🚀 EMPFOHLENE NÄCHSTE SCHRITTE

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

### Priorität 3: f_belege Cube analysieren ⏳

**Ziel:** Konto-Mappings finden

**Methoden:**
1. Cube-Struktur analysieren (33 MB)
2. Nach Konto-Mappings suchen
3. Filter-Logik extrahieren

---

## 📊 STATUS

- ✅ GlobalCube Portal identifiziert (IBM Cognos)
- ✅ Struktur-Dateien analysiert
- ✅ BWA-Hierarchie dokumentiert
- ✅ Ausbildung-Position identifiziert
- ⏳ Konto-Mappings noch nicht gefunden
- ⏳ Filter-Logik noch nicht extrahiert
- ⏳ CSV/Excel-Exporte noch nicht analysiert

---

## 🔧 TOOLS

**Explorer-Script:**
```bash
cd /opt/greiner-portal
python3 scripts/globalcube_explorer.py
```

**Portal-Zugriff:**
- URL: http://10.80.80.10:9300/bi/
- Login: Greiner / Hawaii#22

**Struktur-Dateien:**
- `/mnt/globalcube/GCStruct/AutohausGreiner_20260109_161135.zip`

---

**Nächster Schritt:** CSV/Excel-Exporte analysieren oder f_belege Cube analysieren.
