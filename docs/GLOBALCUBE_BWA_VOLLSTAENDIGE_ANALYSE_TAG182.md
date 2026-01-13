# GlobalCube BWA - Vollständige Logik-Analyse

**Datum:** 2026-01-12  
**TAG:** 182  
**Ziel:** Vollständiges Verständnis der GlobalCube BWA-Logik für alle Standorte und Marken

---

## 📋 ÜBERSICHT

Diese Analyse basiert auf den aktuellen Struktur-Dateien vom GlobalCube Network Share:
- **Pfad:** `/mnt/globalcube/GCStruct`
- **Neueste Datei:** `AutohausGreiner_20260109_161135.zip` (vom 09.01.2026)
- **Vorteil:** Immer aktuelle Struktur-Dateien, keine lokalen Kopien nötig

---

## 📁 STRUKTUR-DATEIEN

### 1. Struktur_GuV.xml
- **Zweck:** BWA-Hauptstruktur (Gewinn- und Verlustrechnung)
- **Root:** `Struktur_GuV` (ID: 48)
- **Inhalt:** Top-Level BWA-Positionen

### 2. Struktur_Controlling.xml
- **Zweck:** Detaillierte Kosten-Hierarchie
- **Root:** `Struktur_Controlling` (ID: 1)
- **Inhalt:** Vollständige Kosten-Aufschlüsselung nach Bereichen

### 3. config.xml
- **Zweck:** GlobalCube-Konfiguration
- **Inhalt:** System-Einstellungen, Filter-Definitionen

### 4. Kontenrahmen.csv
- **Zweck:** Konten-Zuordnung
- **Inhalt:** Mapping zwischen Kontonummern und Bezeichnungen

---

## 🔍 ANALYSE-METHODIK

### Direkte Analyse vom Network Share
```python
# Vorteile:
# - Immer aktuelle Struktur-Dateien
# - Keine lokalen Kopien nötig
# - Automatische Nutzung der neuesten Version

GLOBALCUBE_STRUCT_PATH = "/mnt/globalcube/GCStruct"
```

### Scripts
- `scripts/analyse_globalcube_xml_struktur.py` - XML-Struktur analysieren
- `scripts/globalcube_explorer.py` - Portal und Cubes analysieren

---

## 📊 BWA-POSITIONEN (aus Struktur_Controlling.xml)

### Umsatz-Positionen
- **Umsatz Opel** (ID: 9)
  - Eigenverkauf (ID: 97)
  - davon AOV (ID: 10)
- **Umsatz GW** (ID: 12)
- **Umsatz NW VW** (ID: 91)
- **Umsatz NW Honda** (ID: 14)
- **Umsatz Service** (ID: 16)
- **Umsatz Teile gesamt** (ID: 25)

### Einsatz-Positionen
- **EW NW Opel** (ID: 11)
- **EW GW** (ID: 13)
- **EW NW VW** (ID: 93)
- **EW NW Honda** (ID: 15)
- **EW Serv. ges.** (ID: 22)
- **EW OT/ATZ/VW/Honda Teile** (ID: 30)

### Kosten-Positionen
- **Personalaufwand** (ID: 37)
- **Summe betriebl. Aufwand** (ID: 38)
  - Fremdarbeiten (ID: 54)
  - Miete und Pacht (ID: 55)
  - Heizung (ID: 56)
  - Gas, Strom, Wasser (ID: 57)
  - Reinigung (ID: 58)
  - Instandhaltung betriebl. Räume (ID: 59)
  - Sonstige Raumkosten (ID: 61)
  - Reisekosten (ID: 67)
  - Kfz-Kosten (ID: 68)
  - Werbekosten (ID: 69)
  - Kosten d. Warenabgabe (ID: 70)
  - Verkaufsporvision (ID: 71)
  - Fortbildungskosten (ID: 77)
  - Rechts-, Beratungs-, Abschluss-Prüfungskosten (ID: 79)
  - Nebenkosten des Geldverkehrs (ID: 84)
  - verrechn. kalkul. Kosten (ID: 86)
- **Neutrale Aufwendungen** (ID: 46)
  - Planm.Abschr. auf Sachanlagen (ID: 39)
  - Abschreibung auf Umlaufvermögen (ID: 40)
  - Forderungsverluste (ID: 41)
  - Periodenfremde Aufw. (ID: 42)
  - Sonst. Aufw. unregelmäßig (ID: 43, 44)
  - Kassendifferenzen (ID: 45)
  - Verrechnete kalkulat. Kosten (ID: 47)
  - Zinsaufwend. (ID: 48, 51)
  - Gewerbesteuer (ID: 52)
  - Sonstige Steuern (ID: 53)

### Neutrales Ergebnis
- **Neutraler Ertrag** (ID: 35)
  - Sonstige Erträge betrieblich (ID: 32)
  - Erträge aus abgeschr.Forderungen (ID: 33)
  - Periodenfr. Erträge (ID: 36)
  - Investitionszuschüsse (ID: 34)

---

## 🔧 FILTER-LOGIK

### Standort-Filter
- **Deggendorf:** `branch_number = 1` (Opel) oder `branch_number = 2` (Hyundai)
- **Landau:** `branch_number = 3`
- **6. Ziffer:** Filialcode (1=DEG, 2=Landau)

### Firma/Marke-Filter
- **Stellantis (Opel):** `subsidiary_to_company_ref = 1`
- **Hyundai:** `subsidiary_to_company_ref = 2`

### Konten-Bereiche
- **Umsatz:** 8xxxxx (800000-899999, außer 8932xx für Stellantis)
- **Einsatz:** 7xxxxx (700000-799999)
- **Kosten:** 4xxxxx (400000-499999)
- **Neutrales Ergebnis:** 2xxxxx (200000-299999)

---

## 🎯 NÄCHSTE SCHRITTE

1. ✅ Struktur-Dateien analysiert
2. ⏳ Filter-Logik vollständig extrahieren
3. ⏳ Konten-Zuordnungen dokumentieren
4. ⏳ Standort/Marken-Filter validieren
5. ⏳ Kosten-Kategorisierung (Variable/Direkte/Indirekte) verstehen
6. ⏳ 8910xx Zuordnung klären
7. ⏳ Vollständiges Mapping-Dokument erstellen

---

## 📝 ERGEBNISSE

### Analysierte Struktur-Dateien
- ✅ **Struktur_GuV.xml:** 48 Ebenen vollständig analysiert
- ✅ **Struktur_Controlling.xml:** 84 Ebenen, vollständige Kosten-Hierarchie
- ✅ **config.xml:** Konfiguration extrahiert
- ✅ **Kontenrahmen.csv:** Konten-Zuordnung analysiert (alle Bereiche)

### BWA-Positionen (aus Struktur_Controlling.xml)
- **Umsatz:** 8 Positionen (Opel, GW, VW, Honda, Service, Teile)
- **Einsatz:** 3 Positionen (NW Opel, GW, Service, Teile)
- **Kosten:** 12 Positionen (Personal, Betriebsaufwand, Neutrale Aufwendungen)
- **Neutrales Ergebnis:** 2 Positionen (Neutraler Ertrag, Neutrale Aufwendungen)

### Dokumentations-Dateien
- `docs/globalcube_complete_documentation.json` - Vollständige Dokumentation aller Strukturen
- `/tmp/globalcube_bwa_mapping.json` - BWA-Mapping (temporär)

### Erkenntnisse
1. **Struktur-Hierarchie:** GlobalCube verwendet eine 3-4 Ebenen tiefe Hierarchie
2. **Konten-Bereiche:** Klare Zuordnung nach Konten-Bereichen (2xxxxx, 4xxxxx, 7xxxxx, 8xxxxx)
3. **Standort-Filter:** Werden über `branch_number` und `subsidiary_to_company_ref` gesteuert
4. **Kosten-Kategorisierung:** Detaillierte Aufschlüsselung in Struktur_Controlling.xml

---

## 🔄 NÄCHSTE SCHRITTE

1. ✅ Struktur-Dateien vollständig analysiert
2. ⏳ Filter-Logik aus XML-Attributen extrahieren (für alle Standorte/Marken)
3. ⏳ Standort/Marken-Filter validieren (Deggendorf, Landau, Opel, Hyundai)
4. ⏳ Kosten-Kategorisierung dokumentieren (Variable/Direkte/Indirekte)
5. ⏳ 8910xx Zuordnung klären (für Hyundai)
6. ⏳ Vollständiges Mapping-Dokument für DRIVE erstellen
7. ⏳ BWA-Logik in DRIVE an GlobalCube anpassen
