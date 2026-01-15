# Cognos Cubes (.mdc) Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **ANALYSE IN ARBEIT**

---

## 📁 GEFUNDENE COGNOS CUBES

### Dateien im `/mnt/globalcube/Cubes/` Verzeichnis:

- `f_belege.mdc` - Belege-Cube (wichtig für BWA!)
- `dashboard_gesamt.mdc` - Dashboard-Cube
- Weitere .mdc-Dateien

---

## 🔍 ANALYSE-METHODEN

### 1. Strings-Extraktion

**Methode:** `strings` Befehl extrahiert alle lesbaren Text-Strings aus binären Dateien.

**Ergebnis:** Tausende von Strings gefunden (z.B. f_belege.mdc hat viele Strings)

### 2. Suche nach Kontonummern

**Pattern:** `71700[0-9]?|72700[0-9]?|72750[0-9]?|717001|727001|727501`

**Ergebnis:** ⏳ In Analyse...

### 3. Suche nach SQL-Strukturen

**Keywords:** SELECT, FROM, WHERE, AND, OR, NOT, IN, LIKE, BETWEEN

**Ergebnis:** ⏳ In Analyse...

### 4. Suche nach "zurückgestellt"

**Pattern:** `zurückgestellt|zurueckgestellt`

**Ergebnis:** ⏳ In Analyse...

### 5. Suche nach Tabellen/Views

**Pattern:** `LOC_Belege|journal_accountings|nominal_account|GC_|data\.|schema\.`

**Ergebnis:** ⏳ In Analyse...

### 6. Suche nach Spaltennamen

**Pattern:** `nominal_account_number|posted_value|debit_or_credit|branch_number|subsidiary|firma|standort`

**Ergebnis:** ⏳ In Analyse...

---

## 📊 ERGEBNISSE

### Gefundene Tabellen/Views:
- ⏳ In Analyse...

### Gefundene Spalten:
- ⏳ In Analyse...

### WHERE-Bedingungen:
- ⏳ In Analyse...

### Kontonummern:
- ⏳ In Analyse...

### "Zurückgestellt" Treffer:
- ⏳ In Analyse...

---

## 💡 HYPOTHESEN

### Hypothese 1: Filter in WHERE-Bedingungen

**Möglichkeit:** Die Filter-Logik für "zurückgestellt" Konten liegt in WHERE-Bedingungen der SQL-Queries.

**Test:** Prüfe WHERE-Bedingungen in den Cubes

### Hypothese 2: Ebene-Zuordnungen in Cubes

**Möglichkeit:** Die Ebene-Zuordnungen (z.B. Ebene11: zurückgestellt) werden in den Cubes verwendet, um Konten zu filtern.

**Test:** Suche nach "Ebene11" oder "zurückgestellt" in den Cubes

### Hypothese 3: Kontonummern-Filter

**Möglichkeit:** Spezifische Kontonummern (717001, 727001, 727501) werden explizit ausgeschlossen.

**Test:** Suche nach diesen Kontonummern in den Cubes

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Strings aus allen .mdc-Dateien extrahieren**
2. ⏳ **SQL-ähnliche Strukturen identifizieren**
3. ⏳ **Kontonummern und Filter-Logik finden**
4. ⏳ **"Zurückgestellt" Verwendung prüfen**

---

## 📊 STATUS

- ✅ .mdc-Dateien gefunden
- ✅ Strings-Extraktion gestartet
- ⏳ Analyse läuft...

---

**NÄCHSTER SCHRITT:** Warte auf Analyse-Ergebnisse!
