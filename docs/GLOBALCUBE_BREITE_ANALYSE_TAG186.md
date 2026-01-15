# GlobalCube Share - Breite Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **ANALYSE**

---

## 📁 GEFUNDENE STRUKTUR

### 1. SQL-Definitionen

**Pfad:** `/mnt/globalcube/System/LOCOSOFT/SQL/`

**Wichtige Dateien:**
- `schema/LOCOSOFT/views/locosoft.LOC_Belege.sql` - Haupt-View für Belege
- `config/LOCOSOFT.csv` - Konfiguration für Datenimport (keine Filter!)

**Erkenntnis:** Die `LOCOSOFT.csv` zeigt, dass `journal_accountings` OHNE Filter importiert wird:
```
journal_accountings;journal_accountings;;;
```

### 2. Export-Dateien

**Pfad:** `/mnt/globalcube/Austausch/LOCOSOFT/Export/`

**Wichtige Dateien:**
- `kontenrahmen_gc_struct_skr.csv` - Kontenstruktur mit SKR51
- `loc_belege.csv` - Belege-Daten
- `loc_belege_bilanz.csv` - Bilanz-Belege
- `journal_accountings.csv` - Rohdaten (242 MB!)

**Erkenntnis:** Es gibt separate Dateien für Bilanz und G&V-Belege.

### 3. GC-Dimensionen

**Pfad:** `/mnt/globalcube/Austausch/GC Datein/`

**Wichtige SQL-Dateien:**
- `GC_Turnover_Type.sql` - Umsatzarten
- `GC_Product_Group.sql` - Produktgruppen
- `GC_Department.sql` - Abteilungen
- `GC_Tree.sql` - Hierarchie-Struktur

**Erkenntnis:** GlobalCube verwendet Dimensionen für Kategorisierung.

---

## 🔍 WICHTIGE ERKENNTNISSE

### 1. LOC_Belege View

**HABEN-Buchungen werden negativ behandelt:**
```sql
case
    when T1."debit_or_credit" = 'H' then (CAST(T1."posted_value" AS FLOAT) / 100) * -1
    else CAST(T1."posted_value" AS FLOAT) / 100
end as "Betrag",
```

**Filter: Nur G&V-Konten:**
```sql
where 
    T2."is_profit_loss_account" = 'J'
```

**Erkenntnis:** ✅ GlobalCube behandelt HABEN-Buchungen genauso wie DRIVE.

### 2. Datenimport

**Keine Filter beim Import:**
- `journal_accountings` wird OHNE Filter importiert
- Alle Buchungen werden importiert
- Filterung erfolgt in den Views/Cubes

**Erkenntnis:** ✅ Die Filter-Logik muss in den Cognos-Cubes oder Views liegen.

### 3. Separate Dateien

**Bilanz vs. G&V:**
- `loc_belege.csv` - G&V-Belege
- `loc_belege_bilanz.csv` - Bilanz-Belege

**Erkenntnis:** GlobalCube trennt Bilanz- und G&V-Belege.

---

## ❓ OFFENE FRAGEN

### 1. Einsatz-Filter in Cubes

**Frage:** Wie filtert GlobalCube die Einsatz-Konten in den Cognos-Cubes?

**Mögliche Ansätze:**
- Filter in Cube-Definitionen (.mdc)
- Filter in Cognos-Reports (F02.txt, F03.txt)
- Filter in Views (nicht gefunden)

### 2. Konten-Ausschlüsse

**Frage:** Werden bestimmte Konten (z.B. 717001, 727001) in den Cubes ausgeschlossen?

**Mögliche Ansätze:**
- Prüfe Cube-Definitionen
- Prüfe Cognos-Report-Definitionen
- Prüfe Kontenrahmen-Struktur

### 3. Dimensionen

**Frage:** Verwendet GlobalCube Dimensionen (Turnover_Type, Product_Group) für Filter?

**Mögliche Ansätze:**
- Prüfe GC_Turnover_Type.sql
- Prüfe GC_Product_Group.sql
- Prüfe Cube-Definitionen

---

## 💡 HYPOTHESEN

### Hypothese 1: Filter in Cognos-Cubes

**Möglichkeit:** Die Filter-Logik für Einsatz-Konten liegt in den Cognos-Cube-Definitionen (.mdc), die binär sind und nicht direkt lesbar.

**Test:** Prüfe Cognos-Report-Definitionen (F02.txt, F03.txt) auf SQL-Queries.

### Hypothese 2: Dimensionen-basierte Filter

**Möglichkeit:** GlobalCube verwendet Dimensionen (Turnover_Type, Product_Group) für Filter, nicht direkte Konten-Filter.

**Test:** Prüfe GC-Dimensionen-Definitionen.

### Hypothese 3: Kontenrahmen-Struktur

**Möglichkeit:** Die `kontenrahmen_gc_struct_skr.csv` zeigt, welche Konten in GlobalCube verwendet werden.

**Test:** Analysiere Kontenrahmen-Struktur.

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Kontenrahmen-Struktur analysieren:**
   - Prüfe, welche Konten in `kontenrahmen_gc_struct_skr.csv` enthalten sind
   - Prüfe, ob 717001, 727001, 727501 enthalten sind

2. ⏳ **GC-Dimensionen analysieren:**
   - Prüfe GC_Turnover_Type.sql
   - Prüfe GC_Product_Group.sql
   - Prüfe, ob Dimensionen für Filter verwendet werden

3. ⏳ **Cognos-Reports analysieren:**
   - Suche nach SQL-Queries in F02.txt, F03.txt
   - Prüfe, ob Filter in Reports definiert sind

---

## 📊 STATUS

- ✅ LOC_Belege View analysiert
- ✅ Datenimport-Struktur erfasst
- ✅ GC-Dimensionen identifiziert
- ⏳ Kontenrahmen-Struktur analysieren
- ⏳ GC-Dimensionen analysieren
- ⏳ Cognos-Reports analysieren

---

**Ergebnis:** Die Filter-Logik liegt wahrscheinlich in den Cognos-Cubes oder Dimensionen, nicht in den SQL-Views.
