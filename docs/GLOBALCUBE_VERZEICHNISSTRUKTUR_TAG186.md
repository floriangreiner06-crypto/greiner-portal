# GlobalCube Share - Verzeichnisstruktur TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Pfad:** `/mnt/globalcube` (gemountet von `//srvgc01/GlobalCube`)

---

## 📁 HAUPTVERZEICHNISSE

### 1. **Austausch** (3.3 GB) 📦
**Pfad:** `/mnt/globalcube/Austausch/`

**Unterverzeichnisse:**
- `Aftersales/` - Aftersales-Daten
- `GC Datein/` - GlobalCube Dimensionen (SQL-Definitionen)
  - GC_Activity_Codes.sql
  - GC_Calendar.sql
  - GC_Config.sql
  - GC_Customer_Group.sql
  - GC_Department.sql
  - GC_Deployment.sql
  - GC_Employee.sql
  - GC_Make.sql
  - GC_Parts_Focus.sql
  - GC_Product_Group.sql
  - GC_State_Code.sql
  - GC_Tree.sql
  - GC_Turnover_Type.sql
  - GC_Users.sql
- `GC_Kalender/` - Kalender-Daten
- `LOCOSOFT/` - Locosoft-Daten
  - `Catalogs/` - Cognos-Kataloge (.cat)
  - `Cube_out/` - Cube-Ausgaben
  - `Datenbank/` - Datenbank-Dateien
  - `Export/` - Export-Dateien (CSV, XLSX)
    - journal_accountings.csv (242 MB)
    - kontenrahmen_gc_struct_skr.csv
    - loc_belege.csv
    - loc_belege_bilanz.csv
    - LOC_Belege_NW_GW_VK.csv
    - etc.
  - `IQD/` - IQD-Daten
  - `Models/` - Model-Daten

**Wichtig:** Enthält die meisten Export-Dateien und Dimensionen-Definitionen!

---

### 2. **System** (4.9 GB) 🔧
**Pfad:** `/mnt/globalcube/System/`

**Unterverzeichnisse:**
- `LOCOSOFT/` - Locosoft-System-Dateien
  - `SQL/` - SQL-Definitionen
    - `batch/` - Batch-Scripts (.bat)
    - `config/` - Konfigurationsdateien (.csv, .json)
    - `dtsx/` - SSIS-Pakete
    - `exec/` - Ausführbare SQL-Scripts
    - `postgresql/` - PostgreSQL-Schema
    - `schema/` - Schema-Definitionen
      - `GC/` - GlobalCube Views
      - `LOCOSOFT/` - Locosoft Views/Tables
    - `temp/` - Temporäre Dateien

**Wichtig:** Enthält die SQL-Definitionen für Views und Tabellen!

---

### 3. **Cubes** (762 MB) 📊
**Pfad:** `/mnt/globalcube/Cubes/`

**Cube-Definitionen (.mdc):**
- `dashboard_gesamt.mdc` - Dashboard-Gesamt
- `f_belege.mdc` - Belege-Cube
- `f_Belege_Plan_CSV.mdc` - Belege-Plan CSV
- `f_forderungen.mdc` - Forderungen-Cube
- `s_aftersales.mdc` - Aftersales-Cube
- `s_offene_auftraege.mdc` - Offene Aufträge
- `v_auftragseingang.mdc` - Auftragseingang
- `v_bestand.mdc` - Bestand
- `v_verkauf.mdc` - Verkauf
- `z_monteure.mdc` - Monteure

**Unterverzeichnisse:**
- Jeder Cube hat Versionierungs-Ordner (z.B. `f_belege__20250211193823/`)

**Wichtig:** Enthält die Cognos-Cube-Definitionen (binär, .mdc)!

---

### 4. **GCStruct** (12 MB) 🏗️
**Pfad:** `/mnt/globalcube/GCStruct/`

**Unterverzeichnisse:**
- `config/` - Konfiguration
- `Export/` - Export-Dateien
- `Kontenrahmen/` - Kontenrahmen-Dateien
- `Strukturen/` - Struktur-Definitionen
- `Xml/` - XML-Dateien

**Wichtig:** Enthält Struktur-Definitionen und Kontenrahmen!

---

### 5. **GCStruct_ori** (6.0 MB) 📁
**Pfad:** `/mnt/globalcube/GCStruct_ori/`

**Unterverzeichnisse:**
- `config/` - Konfiguration (Original)
- `Export/` - Export-Dateien (Original)
- `Kontenrahmen/` - Kontenrahmen (Original)
- `Strukturen/` - Struktur-Definitionen (Original)
- `Xml/` - XML-Dateien (Original)

**Wichtig:** Original-Version von GCStruct!

---

### 6. **GCStruct_SKR51_ori** (78 MB) 📁
**Pfad:** `/mnt/globalcube/GCStruct_SKR51_ori/`

**Unterverzeichnisse:**
- `config/` - Konfiguration (SKR51 Original)
- `Export/` - Export-Dateien (SKR51 Original)
- `Kontenrahmen/` - Kontenrahmen (SKR51 Original)
- `Strukturen/` - Struktur-Definitionen (SKR51 Original)
- `Xml/` - XML-Dateien (SKR51 Original)

**Wichtig:** Original-Version mit SKR51-Struktur!

---

### 7. **GCHR** (19 MB) 👥
**Pfad:** `/mnt/globalcube/GCHR/`

**Unterverzeichnisse:**
- `config/` - Konfiguration
- `data/` - Daten
- `export/` - Export-Dateien
- `img/` - Bilder
- `logs/` - Log-Dateien

**Wichtig:** HR (Human Resources) Modul!

---

### 8. **GCHRStruct_SKR51** (11 MB) 👥
**Pfad:** `/mnt/globalcube/GCHRStruct_SKR51/`

**Unterverzeichnisse:**
- `Hyundai/` - Hyundai-Daten
- `Hyundai_Export/` - Hyundai-Export
- `HyundaiV1/` - Hyundai Version 1

**Wichtig:** HR-Struktur mit SKR51 für Hyundai!

---

### 9. **GCStarter** (37 MB) 🚀
**Pfad:** `/mnt/globalcube/GCStarter/`

**Unterverzeichnisse:**
- `batch/` - Batch-Scripts
- `config/` - Konfiguration
- `data/` - Daten
- `img/` - Bilder
- `logs/` - Log-Dateien
- `pcvisit/` - PC-Visit-Daten
- `remote/` - Remote-Daten

**Wichtig:** Starter-Modul für GlobalCube!

---

### 10. **Content** (178 MB) 📄
**Pfad:** `/mnt/globalcube/Content/`

**Unterverzeichnisse:**
- `Deployment/` - Deployment-Dateien

**Wichtig:** Cognos Content Store!

---

### 11. **Tasks** (1.0 GB) ⚙️
**Pfad:** `/mnt/globalcube/Tasks/`

**Unterverzeichnisse:**
- `config/` - Konfiguration
- `logs/` - Log-Dateien
- `php/` - PHP-Scripts
- `Python/` - Python-Scripts
- `scripts/` - Scripts
- `sql_load/` - SQL-Load-Scripts
- `unlocker/` - Unlocker-Scripts

**Wichtig:** Enthält Automatisierungs-Scripts!

---

### 12. **ReportOutput** (80 KB) 📊
**Pfad:** `/mnt/globalcube/ReportOutput/`

**Unterverzeichnisse:**
- `leer/` - Leerer Ordner
- `test/` - Test-Reports

**Wichtig:** Ausgabe-Verzeichnis für Reports!

---

## 📊 GRÖSSENÜBERSICHT

| Verzeichnis | Größe | Beschreibung |
|-------------|-------|--------------|
| **System** | 4.9 GB | SQL-Definitionen, Batch-Scripts |
| **Austausch** | 3.3 GB | Export-Dateien, Dimensionen |
| **Tasks** | 1.0 GB | Automatisierungs-Scripts |
| **Cubes** | 762 MB | Cognos-Cube-Definitionen |
| **Content** | 178 MB | Cognos Content Store |
| **GCStruct_SKR51_ori** | 78 MB | SKR51 Original-Struktur |
| **GCStarter** | 37 MB | Starter-Modul |
| **GCHR** | 19 MB | HR-Modul |
| **GCStruct** | 12 MB | Struktur-Definitionen |
| **GCHRStruct_SKR51** | 11 MB | HR SKR51-Struktur |
| **GCStruct_ori** | 6.0 MB | Original-Struktur |

---

## 🔍 WICHTIGE DATEIEN

### SQL-Definitionen:
- `/mnt/globalcube/System/LOCOSOFT/SQL/schema/LOCOSOFT/views/locosoft.LOC_Belege.sql`
- `/mnt/globalcube/System/LOCOSOFT/SQL/config/LOCOSOFT.csv`

### Export-Dateien:
- `/mnt/globalcube/Austausch/LOCOSOFT/Export/journal_accountings.csv` (242 MB)
- `/mnt/globalcube/Austausch/LOCOSOFT/Export/kontenrahmen_gc_struct_skr.csv`
- `/mnt/globalcube/Austausch/LOCOSOFT/Export/loc_belege.csv`

### Cube-Definitionen:
- `/mnt/globalcube/Cubes/f_belege.mdc` - Belege-Cube
- `/mnt/globalcube/Cubes/dashboard_gesamt.mdc` - Dashboard

### Dimensionen:
- `/mnt/globalcube/Austausch/GC Datein/GC_Turnover_Type.sql`
- `/mnt/globalcube/Austausch/GC Datein/GC_Product_Group.sql`

---

## 💡 ERKENNTNISSE

1. **System/** enthält die SQL-Definitionen (Views, Tabellen)
2. **Austausch/** enthält die Export-Dateien und Dimensionen
3. **Cubes/** enthält die Cognos-Cube-Definitionen (binär, .mdc)
4. **GCStruct/** enthält Struktur-Definitionen und Kontenrahmen
5. **Tasks/** enthält Automatisierungs-Scripts

**Für BWA-Analyse relevant:**
- ✅ `System/LOCOSOFT/SQL/` - SQL-Definitionen
- ✅ `Austausch/LOCOSOFT/Export/` - Export-Dateien
- ✅ `Cubes/` - Cube-Definitionen (binär, schwer lesbar)
- ✅ `Austausch/GC Datein/` - Dimensionen-Definitionen

---

**Nächster Schritt:** Welche Verzeichnisse sollen genauer analysiert werden?
