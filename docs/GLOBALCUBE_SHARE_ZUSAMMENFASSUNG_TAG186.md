# GlobalCube Share Analyse - Zusammenfassung TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **ANALYSE ABGESCHLOSSEN**

---

## 📁 GLOBALCUBE SHARE

**Share-Pfad:** `/mnt/globalcube` (gemountet von `//srvgc01/GlobalCube`)

**Wichtige Erkenntnisse:**

### 1. LOC_Belege View

**Pfad:** `/mnt/globalcube/System/LOCOSOFT/SQL/schema/LOCOSOFT/views/locosoft.LOC_Belege.sql`

**HABEN-Buchungen werden negativ behandelt:**
```sql
case
    when T1."debit_or_credit" = 'H' then (CAST(T1."posted_value" AS FLOAT) / 100) * -1
    else CAST(T1."posted_value" AS FLOAT) / 100
end as "Betrag",
```

**Erkenntnis:** ✅ GlobalCube behandelt HABEN-Buchungen genauso wie DRIVE (negativ).

**Filter: Nur G&V-Konten:**
```sql
where 
    T2."is_profit_loss_account" = 'J'
```

**Erkenntnis:** ✅ GlobalCube filtert nur G&V-Konten, genau wie DRIVE mit `get_guv_filter()`.

---

## ❓ OFFENE FRAGEN

### 1. Einsatz-Filter-Logik

**Problem:** Die LOC_Belege View zeigt keine spezifische Filter-Logik für Einsatz-Konten (700000-799999).

**Mögliche Ansätze:**
- Filtert GlobalCube bestimmte Konten in den Cubes aus (z.B. 717001, 727001)?
- Gibt es zusätzliche Filter für HABEN-Buchungen in den Cubes?
- Werden bestimmte Buchungstexte in den Cubes ausgeschlossen?

### 2. Cube-Definitionen

**Gefundene Cubes:**
- `f_belege.mdc` - Belege-Cube
- `dashboard_gesamt.mdc` - Dashboard-Cube
- `f_forderungen.mdc` - Forderungen-Cube

**Problem:** Die `.mdc`-Dateien sind binäre Cognos-Cube-Definitionen und können nicht direkt als Text gelesen werden.

**Lösung:** Die Filter-Logik muss in den Cognos-Report-Definitionen (F02.txt, F03.txt) oder in den Cube-Metadaten gesucht werden.

---

## 💡 HYPOTHESEN

### Hypothese 1: GlobalCube schließt bestimmte Konten in den Cubes aus

**Kandidaten:**
- **717001** (EW Sonstige Erlöse Neuwagen): 906.983,78 € HABEN
- **727001** (Sonstige Einsatzwerte GW): 87.018,58 € HABEN
- **727501** (GIVIT Garantien GW): -13.917,40 € NETTO (nur HABEN)

**Test:** Prüfe Cognos-Report-Definitionen auf Ausschlüsse für diese Konten.

### Hypothese 2: GlobalCube filtert nach Buchungstext

**Möglichkeit:** GlobalCube könnte Buchungen mit bestimmten Texten ausschließen (z.B. "Hersteller-Boni", "Gutschrift").

**Test:** Prüfe Cognos-Report-Definitionen auf Text-Filter.

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Cognos-Report-Definitionen analysieren:**
   - F02.txt (Kostenstellenbericht) auf Einsatz-Filter prüfen
   - F03.txt (BWA VJ/Soll/Ist-Vergleich) auf BWA-Filter prüfen

2. ⏳ **SQL-Queries in Reports suchen:**
   - Nach Filter-Logik für 700000-799999 suchen
   - Nach Ausschlüssen für bestimmte Konten suchen

3. ⏳ **Cube-Metadaten analysieren:**
   - Cube-Definitionen auf Filter prüfen (falls möglich)

---

## 📊 STATUS

- ✅ LOC_Belege View analysiert (HABEN-Buchungen werden negativ behandelt)
- ✅ GlobalCube Share-Struktur erfasst
- ⏳ Cognos-Report-Definitionen analysieren (F02.txt, F03.txt)
- ⏳ SQL-Queries in Reports suchen

---

**Ergebnis:** Die LOC_Belege View zeigt, dass GlobalCube HABEN-Buchungen genauso behandelt wie DRIVE. Die spezifische Filter-Logik für Einsatz muss in den Cognos-Reports oder Cube-Definitionen gesucht werden.
