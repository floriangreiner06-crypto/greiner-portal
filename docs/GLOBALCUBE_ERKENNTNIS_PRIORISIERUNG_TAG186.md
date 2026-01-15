# GlobalCube Share - Erkenntnis-Priorisierung TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Ziel:** Filter-Logik für Einsatz-Konten (700000-799999) finden

---

## 🎯 PRIORISIERUNG NACH ERKENNTNIS-CHANCEN

### 1. **GCStruct/** (12 MB) ⭐⭐⭐⭐⭐
**Chance:** **SEHR HOCH**

**Warum:**
- Enthält Kontenrahmen-Struktur
- Könnte Mapping zwischen 6-stelligen Konten und GlobalCube-Struktur zeigen
- Könnte zeigen, welche Konten wie kategorisiert werden
- Struktur-Definitionen könnten Filter-Regeln enthalten

**Zu prüfen:**
- `GCStruct/Kontenrahmen/` - Kontenrahmen-Dateien
- `GCStruct/Strukturen/` - Struktur-Definitionen
- `GCStruct/Xml/` - XML-Definitionen
- `GCStruct/config/` - Konfigurationsdateien

**Nächster Schritt:** Kontenrahmen-Dateien analysieren!

---

### 2. **Austausch/GC Datein/** ⭐⭐⭐⭐
**Chance:** **HOCH**

**Warum:**
- Enthält Dimensionen-Definitionen (GC_Turnover_Type, GC_Product_Group)
- Könnte zeigen, wie Konten in Dimensionen gruppiert werden
- Könnte Filter-Regeln für Konten enthalten

**Zu prüfen:**
- `GC_Turnover_Type.sql` - Umsatzarten-Dimension
- `GC_Product_Group.sql` - Produktgruppen-Dimension
- `GC_Tree.sql` - Hierarchie-Struktur
- `GC_Config.sql` - Konfiguration

**Nächster Schritt:** Dimensionen-Definitionen analysieren!

---

### 3. **System/LOCOSOFT/SQL/schema/** ⭐⭐⭐⭐
**Chance:** **HOCH**

**Warum:**
- Enthält SQL-Views (bereits LOC_Belege gefunden)
- Könnte weitere Views mit Filter-Logik enthalten
- Könnte Views für BWA/Einsatz enthalten

**Zu prüfen:**
- `schema/GC/views/` - GlobalCube Views
- `schema/LOCOSOFT/views/` - Locosoft Views
- Weitere Views außer LOC_Belege

**Nächster Schritt:** Alle Views durchsuchen!

---

### 4. **Tasks/** (1.0 GB) ⭐⭐⭐
**Chance:** **MITTEL-HOCH**

**Warum:**
- Enthält Automatisierungs-Scripts
- Könnte Filter-Logik in Python/PHP-Scripts enthalten
- Könnte SQL-Queries mit Filter-Logik enthalten

**Zu prüfen:**
- `Tasks/Python/` - Python-Scripts
- `Tasks/scripts/` - Scripts
- `Tasks/sql_load/` - SQL-Load-Scripts

**Nächster Schritt:** Scripts nach Filter-Logik durchsuchen!

---

### 5. **Cubes/** (762 MB) ⭐⭐
**Chance:** **NIEDRIG-MITTEL**

**Warum:**
- Enthält Cognos-Cube-Definitionen (.mdc)
- Binär-Format, schwer lesbar
- Könnte Filter-Logik enthalten, aber schwer zu extrahieren

**Zu prüfen:**
- `f_belege.mdc` - Belege-Cube (wichtig für BWA!)
- `dashboard_gesamt.mdc` - Dashboard-Cube

**Nächster Schritt:** Versuche, .mdc-Dateien zu lesen (schwierig)!

---

### 6. **Austausch/LOCOSOFT/Export/** ⭐⭐
**Chance:** **NIEDRIG**

**Warum:**
- Enthält Export-Dateien (CSV)
- Daten, nicht Logik
- Könnte aber zeigen, welche Konten exportiert werden

**Zu prüfen:**
- `kontenrahmen_gc_struct_skr.csv` - Kontenstruktur
- `loc_belege.csv` - Belege-Daten (könnte zeigen, welche Konten enthalten sind)

**Nächster Schritt:** Kontenrahmen-CSV analysieren!

---

## 🎯 EMPFOHLENE REIHENFOLGE

### Phase 1: Struktur-Definitionen (HÖCHSTE PRIORITÄT)
1. ✅ **GCStruct/Kontenrahmen/** - Kontenrahmen-Dateien analysieren
2. ✅ **GCStruct/Strukturen/** - Struktur-Definitionen analysieren
3. ✅ **GCStruct/Xml/** - XML-Definitionen analysieren

### Phase 2: Dimensionen (HOHE PRIORITÄT)
4. ✅ **Austausch/GC Datein/GC_Turnover_Type.sql** - Umsatzarten analysieren
5. ✅ **Austausch/GC Datein/GC_Product_Group.sql** - Produktgruppen analysieren
6. ✅ **Austausch/GC Datein/GC_Tree.sql** - Hierarchie analysieren

### Phase 3: SQL-Views (HOHE PRIORITÄT)
7. ✅ **System/LOCOSOFT/SQL/schema/GC/views/** - Alle GC-Views durchsuchen
8. ✅ **System/LOCOSOFT/SQL/schema/LOCOSOFT/views/** - Alle Locosoft-Views durchsuchen

### Phase 4: Scripts (MITTEL-HOHE PRIORITÄT)
9. ✅ **Tasks/Python/** - Python-Scripts nach Filter-Logik durchsuchen
10. ✅ **Tasks/scripts/** - Scripts nach Filter-Logik durchsuchen

### Phase 5: Export-Dateien (NIEDRIGE PRIORITÄT)
11. ✅ **Austausch/LOCOSOFT/Export/kontenrahmen_gc_struct_skr.csv** - Kontenstruktur analysieren

---

## 💡 HYPOTHESEN

### Hypothese 1: Kontenrahmen-Struktur
**Möglichkeit:** Die Kontenrahmen-Struktur in `GCStruct/Kontenrahmen/` zeigt, welche 6-stelligen Konten wie kategorisiert werden und welche ausgeschlossen werden.

**Test:** Analysiere Kontenrahmen-Dateien!

### Hypothese 2: Dimensionen-Mapping
**Möglichkeit:** Die Dimensionen (GC_Turnover_Type, GC_Product_Group) zeigen, welche Konten in welche Dimensionen gemappt werden, und bestimmte Dimensionen werden ausgeschlossen.

**Test:** Analysiere Dimensionen-Definitionen!

### Hypothese 3: Weitere Views
**Möglichkeit:** Es gibt weitere SQL-Views außer LOC_Belege, die spezifische Filter für Einsatz-Konten enthalten.

**Test:** Durchsuche alle Views!

---

## 📋 NÄCHSTER SCHRITT

**STARTE MIT:** `GCStruct/Kontenrahmen/` - Das hat die höchste Chance, die Filter-Logik zu zeigen!
