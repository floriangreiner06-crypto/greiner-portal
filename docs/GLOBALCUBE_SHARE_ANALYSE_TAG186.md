# GlobalCube Share Analyse - Einsatz HABEN-Buchungen TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **ANALYSE**

---

## 📁 GLOBALCUBE SHARE STRUKTUR

**Share-Pfad:** `/mnt/globalcube` (gemountet von `//srvgc01/GlobalCube`)

**Wichtige Verzeichnisse:**
- `/mnt/globalcube/System/LOCOSOFT/SQL/` - SQL-Definitionen
- `/mnt/globalcube/Cubes/` - Cube-Definitionen (.mdc)
- `/mnt/globalcube/Austausch/` - Austausch-Dateien

---

## 🔍 GEFUNDENE INFORMATIONEN

### 1. LOC_Belege View (`locosoft.LOC_Belege.sql`)

**Pfad:** `/mnt/globalcube/System/LOCOSOFT/SQL/schema/LOCOSOFT/views/locosoft.LOC_Belege.sql`

**Wichtigste Erkenntnisse:**

#### HABEN-Buchungen werden negativ behandelt:
```sql
case
    when T1."debit_or_credit" = 'H' then (CAST(T1."posted_value" AS FLOAT) / 100) * -1
    else CAST(T1."posted_value" AS FLOAT) / 100
end as "Betrag",
```

**Erkenntnis:** GlobalCube behandelt HABEN-Buchungen genauso wie DRIVE (negativ). ✅

#### Filter: Nur G&V-Konten
```sql
where 
    T2."is_profit_loss_account" = 'J'
```

**Erkenntnis:** GlobalCube filtert nur G&V-Konten, genau wie DRIVE mit `get_guv_filter()`. ✅

---

## ❓ OFFENE FRAGEN

### 1. Einsatz-Filter-Logik

**Frage:** Wie filtert GlobalCube die Einsatz-Konten (700000-799999)?

**Mögliche Ansätze:**
- Filtert GlobalCube bestimmte Konten aus (z.B. 717001, 727001)?
- Gibt es zusätzliche Filter für HABEN-Buchungen?
- Werden bestimmte Buchungstexte ausgeschlossen?

### 2. Cube-Definitionen

**Gefundene Cubes:**
- `f_belege.mdc` - Belege-Cube
- `dashboard_gesamt.mdc` - Dashboard-Cube
- `f_forderungen.mdc` - Forderungen-Cube

**Frage:** Enthalten diese Cubes die BWA-Filter-Logik?

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Cube-Definitionen analysieren:**
   - `f_belege.mdc` auf Einsatz-Filter prüfen
   - `dashboard_gesamt.mdc` auf BWA-Filter prüfen

2. ⏳ **SQL-Queries in Cubes suchen:**
   - Nach Filter-Logik für 700000-799999 suchen
   - Nach Ausschlüssen für bestimmte Konten suchen

3. ⏳ **Austausch-Dateien prüfen:**
   - `F02.txt` und `F03.txt` auf BWA-Definitionen prüfen

---

## 💡 HYPOTHESEN

### Hypothese 1: GlobalCube schließt bestimmte Konten aus

**Kandidaten:**
- **717001** (EW Sonstige Erlöse Neuwagen): 906.983,78 € HABEN
- **727001** (Sonstige Einsatzwerte GW): 87.018,58 € HABEN
- **727501** (GIVIT Garantien GW): -13.917,40 € NETTO (nur HABEN)

**Test:** Prüfe, ob diese Konten in GlobalCube-Cubes ausgeschlossen werden.

### Hypothese 2: GlobalCube filtert nach Buchungstext

**Möglichkeit:** GlobalCube könnte Buchungen mit bestimmten Texten ausschließen (z.B. "Hersteller-Boni", "Gutschrift").

**Test:** Prüfe Cube-Definitionen auf Text-Filter.

---

## 📊 STATUS

- ✅ LOC_Belege View analysiert (HABEN-Buchungen werden negativ behandelt)
- ⏳ Cube-Definitionen analysieren
- ⏳ SQL-Queries in Cubes suchen
- ⏳ Austausch-Dateien prüfen

---

**Nächster Schritt:** Cube-Definitionen analysieren, besonders `f_belege.mdc` und `dashboard_gesamt.mdc`.
