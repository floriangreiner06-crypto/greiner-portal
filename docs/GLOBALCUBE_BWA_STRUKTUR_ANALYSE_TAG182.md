# GlobalCube BWA-Struktur Analyse - TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Struktur analysiert

---

## 🎯 ERGEBNIS

Die GlobalCube GuV-Struktur wurde erfolgreich analysiert. Sie zeigt die **exakte BWA-Hierarchie**, die GlobalCube verwendet.

---

## 📋 GUV-STRUKTUR (aus `Struktur_GuV.xml`)

```
Struktur_GuV (ID: 48)
└── GuV (ID: 49)
    ├── 1. Umsatzerlöse (ID: 50)
    │   ├── a) Neuwagen (ID: 51)
    │   ├── b) Gebrauchtwagen (ID: 52)
    │   ├── c) Teile & Zubehör (ID: 53)
    │   ├── d) Service (ID: 54)
    │   ├── e) Mietwagen (ID: 55)
    │   ├── f) Tankstelle (ID: 56)
    │   └── g) Umlagen (ID: 57)
    ├── 2. Erhöhung oder Verminderung des Bestands...
    ├── 4. Sonstige betriebliche Erträge (ID: 59)
    ├── 5. Materialaufwand (ID: 60)
    │   ├── a) Aufwendungen für Roh-,Hilfs- und Betriebsstoffe... (ID: 61)
    │   │   ├── aa) Neuwagen (ID: 62)
    │   │   ├── ab) Gebrauchtwagen (ID: 63)
    │   │   ├── ac) Teile & Zubehör (ID: 64)
    │   │   ├── ad) Service (ID: 65)
    │   │   ├── ae) Mietwagen (ID: 66)
    │   │   ├── af) Tankstelle (ID: 67)
    │   │   └── ag) Umlagen (ID: 68)
    │   └── b) Aufwendungen für bezogene Leistungen (ID: 69)
    ├── 6. Personalaufwand (ID: 70)
    │   ├── a) Löhne und Gehälter (ID: 71)
    │   │   ├── aa) Lohn (ID: 72)
    │   │   ├── ab) Gehalt (ID: 73)
    │   │   ├── ac) Urlaubsgeld (ID: 74)
    │   │   ├── ad) Ausbildung (ID: 75)
    │   │   └── ae) Fertigungslohn (ID: 76)
    │   └── b) soziale Abgaben... (ID: 77)
    │       ├── ba) soziale Abgaben (ID: 78)
    │       └── bb) Aufwendungen für Altersvorsorge (ID: 79)
    ├── 7. Abschreibungen (ID: 80)
    ├── 8. Sonstige betriebliche Aufwendungen (ID: 83)
    │   ├── a) Betriebsaufwendungen (ID: 84)
    │   ├── b) Vertriebsaufwendungen (ID: 85)
    │   ├── c) Verwaltungsaufwendungen (ID: 86)
    │   └── d) Übrige Aufwendungen (ID: 87)
    ├── 9. Zinsen und ähnliche Erträge (ID: 88)
    ├── 10. Zinsen und ähnliche Aufwendungen (ID: 89)
    ├── 12. Außerordentliche Erträge (ID: 90)
    ├── 13. Außerordentliche Aufwendungen (ID: 91)
    ├── 14. Steuern vom Einkommen... (ID: 92)
    ├── 15. sonstige Steuern (ID: 93)
    ├── keine Zuordnung (ID: 94)
    └── nicht benötigte Konten (ID: 98)
```

---

## 🔍 WICHTIGE ERKENNTNISSE

### 1. BWA-Positionen

Die Struktur zeigt die **exakte BWA-Hierarchie**:
- **Umsatzerlöse** nach Bereichen (NW, GW, T+Z, Service, Mietwagen, Tankstelle, Umlagen)
- **Materialaufwand** nach Bereichen (entspricht Einsatzwerten)
- **Personalaufwand** mit Details (Lohn, Gehalt, Urlaubsgeld, **Ausbildung**, Fertigungslohn)
- **Sonstige betriebliche Aufwendungen** nach Kategorien

### 2. Ausbildung (ID: 75)

**Wichtig:** Es gibt eine separate Position "ad) Ausbildung" (ID: 75) unter "6. Personalaufwand" → "a) Löhne und Gehälter".

**Hypothese:** 411xxx (Ausbildungsvergütung) könnte in dieser Position sein, nicht in direkten Kosten!

### 3. Struktur-IDs

Jede Position hat eine eindeutige `StrukturId`, die für Filter und Mapping verwendet werden könnte.

---

## 🚀 NÄCHSTE SCHRITTE

1. ⏳ **Konto-Mappings zu Struktur-IDs finden**
   - Welche Konten gehören zu welcher Struktur-ID?
   - Gibt es eine Mapping-Tabelle?

2. ⏳ **Filter-Logik extrahieren**
   - Wie werden Konten den Struktur-Positionen zugeordnet?
   - Welche Filter werden für direkte/indirekte Kosten verwendet?

3. ⏳ **Ausbildung-Position analysieren**
   - Ist 411xxx wirklich in "Ausbildung" (ID: 75)?
   - Oder in direkten Kosten?

4. ⏳ **Controlling-Struktur analysieren**
   - Gibt es eine separate BWA-Struktur in `Struktur_Controlling.xml`?

---

## 📝 HYPOTHESEN

### Hypothese 1: Ausbildung (411xxx)

**Möglichkeit A:** 411xxx ist in "Ausbildung" (ID: 75) → **NICHT in direkten Kosten**
- Würde erklären, warum GlobalCube 411xxx nicht in direkten Kosten hat
- TAG 177 Logik (411xxx ausschließen) wäre korrekt

**Möglichkeit B:** 411xxx ist in direkten Kosten, aber GlobalCube filtert es anders
- Würde erklären, warum wir 411xxx ausschließen müssen

### Hypothese 2: Struktur-basierte Filterung

GlobalCube könnte **struktur-basiert** filtern:
- Konten werden Struktur-IDs zugeordnet
- Filter basieren auf Struktur-IDs, nicht direkt auf Konten-Nummern

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
```

---

**Status:** ✅ Struktur analysiert, weitere Analyse erforderlich
