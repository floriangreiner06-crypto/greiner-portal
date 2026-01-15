# Q:\System\LOCOSOFT\Export Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Pfad:** `/mnt/globalcube/Austausch/LOCOSOFT/Export/` (entspricht `Q:\System\LOCOSOFT\Export`)

---

## 📁 GEFUNDENE DATEIEN

### Wichtige CSV-Dateien:

1. **kontenrahmen_gc_struct_skr.csv** (5.9 MB) ⭐⭐⭐⭐⭐
   - **Wichtigste Datei!**
   - Enthält Kontenstruktur mit SKR51
   - 12.827 Zeilen
   - 106 Spalten (inkl. Ebene1-Ebene20+)
   - Verwendet 5-stellige Konten (z.B. 7000, 71700, 72700)

2. **journal_accountings.csv** (242 MB)
   - Rohdaten aller Buchungen
   - Enthält 6-stellige Kontonummern

3. **loc_belege.csv** (248 MB)
   - Belege-Daten (aus LOC_Belege View)
   - Enthält 6-stellige Kontonummern

4. **LOC_Belege_NW_GW_VK.csv** (83 MB)
   - Neuwagen/Gebrauchtwagen Verkaufsdaten

---

## 🔍 ERKENNTNISSE

### 1. Kontenrahmen-Struktur

**Format:**
- **5-stellige Konten** (z.B. 71700, 72700, 72750)
- **NICHT 6-stellige Konten** (717001, 727001, 727501 sind nicht enthalten!)

**Erkenntnis:**
- GlobalCube verwendet wahrscheinlich die **ersten 5 Stellen** der 6-stelligen Konten für die Kategorisierung
- 717001 → 71700
- 727001 → 72700
- 727501 → 72750

### 2. Gefundene Konten

**71700 (EW Sonstige Erlöse Neuwagen):**
- In GCStruct/Kontenrahmen/Kontenrahmen.csv gefunden!
- Bezeichnung: "EW Sonstige Erlöse Neuwagen"
- Hat "_H" Variante (Hyundai)

**72700 (Sonstige Einsatzwerte GW):**
- In GCStruct/Kontenrahmen/Kontenrahmen.csv gefunden!
- Bezeichnung: "Sonstige Einsatzwerte GW"
- Hat "_H" Variante (Hyundai)

**72750 (GIVIT Garantien GW):**
- Möglicherweise in GCStruct/Kontenrahmen/Kontenrahmen.csv
- Bezeichnung: "GIVIT Garantien GW" oder ähnlich

### 3. Ebene-Zuordnungen

**Struktur:**
- Ebene1-Ebene20+ Spalten zeigen die Hierarchie-Zuordnung
- Könnte zeigen, in welche BWA-Positionen die Konten gemappt werden

**Zu prüfen:**
- Welche Ebene-Zuordnungen haben 71700, 72700, 72750?
- Werden sie in "nicht benötigte Konten" oder "keine Zuordnung" kategorisiert?

---

## 💡 HYPOTHESEN

### Hypothese 1: Mapping über erste 5 Stellen

**Möglichkeit:** GlobalCube mappt 6-stellige Konten zu 5-stelligen Konten:
- 717001 → 71700
- 727001 → 72700
- 727501 → 72750

**Test:** Prüfe Ebene-Zuordnungen für 71700, 72700, 72750 in GCStruct/Kontenrahmen/Kontenrahmen.csv

### Hypothese 2: Ausschluss über Ebene-Zuordnungen

**Möglichkeit:** Konten werden über Ebene-Zuordnungen ausgeschlossen:
- "nicht benötigte Konten"
- "keine Zuordnung"
- "Bilanz" (statt G&V)

**Test:** Prüfe, ob 71700, 72700, 72750 in "nicht benötigte Konten" kategorisiert sind

### Hypothese 3: Filter in Cognos-Cubes

**Möglichkeit:** Die Filter-Logik liegt in den Cognos-Cubes (.mdc), nicht in den CSV-Dateien.

**Test:** Prüfe Cube-Definitionen (schwierig, da binär)

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Ebene-Zuordnungen prüfen:**
   - Prüfe, welche Ebene-Zuordnungen 71700, 72700, 72750 in GCStruct/Kontenrahmen/Kontenrahmen.csv haben
   - Prüfe, ob sie in "nicht benötigte Konten" kategorisiert sind

2. ⏳ **Mapping-Logik verstehen:**
   - Wie werden 6-stellige Konten zu 5-stelligen Konten gemappt?
   - Gibt es eine Mapping-Tabelle?

3. ⏳ **Struktur-Dateien prüfen:**
   - Prüfe Struktur_GuV.csv, Struktur_Controlling.csv
   - Prüfe, ob 71700, 72700, 72750 dort enthalten sind

---

## 📊 STATUS

- ✅ Export-Verzeichnis gefunden
- ✅ kontenrahmen_gc_struct_skr.csv analysiert
- ✅ 71700, 72700 gefunden (aber nicht 72750)
- ⏳ Ebene-Zuordnungen prüfen
- ⏳ Mapping-Logik verstehen

---

**Nächster Schritt:** Ebene-Zuordnungen für 71700, 72700, 72750 in GCStruct/Kontenrahmen/Kontenrahmen.csv prüfen!
