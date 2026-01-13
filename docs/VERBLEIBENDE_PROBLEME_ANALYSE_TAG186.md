# Verbleibende Probleme - Detaillierte Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **IN ANALYSE**

---

## 🎯 ZIEL

Identifiziere die **genauen Konten**, die die verbleibenden Differenzen verursachen, damit wir gezielt analysieren können.

---

## 📊 VERBLEIBENDE DIFFERENZEN

### 1. GESAMTBETRIEB EINSATZ YTD 🚨

**Problem:**
- DRIVE: 9.223.769,97 €
- GlobalCube: 9.191.864,00 €
- **Differenz:** +31.905,97 € (+0,35%)

**Auswirkung:**
- Verursacht Betriebsergebnis-Differenz von -31.708,15 € (YTD)
- Verursacht DB1-Differenz von -31.912,61 € (YTD)

**Frage:** Welche Konten werden von DRIVE erfasst, die GlobalCube nicht erfasst?

### 2. LANDAU VARIABLE KOSTEN YTD 🚨

**Problem:**
- DRIVE: 25.905,53 €
- GlobalCube: 39.162,00 €
- **Differenz:** -13.256,47 € (-33,85%)

**Auswirkung:**
- Verursacht DB2-Differenz von +13.250,00 € (YTD)
- Verursacht Betriebsergebnis-Differenz von +19.255,85 € (YTD)

**Frage:** Welche Konten erfasst GlobalCube, die DRIVE nicht erfasst?

### 3. GESAMTBETRIEB BETRIEBSERGEBNIS YTD ⚠️

**Problem:**
- DRIVE: -407.613,15 €
- GlobalCube: -375.905,00 €
- **Differenz:** -31.708,15 € (-8,44%)

**Erkenntnis:**
- Die Differenz entspricht fast genau der Einsatz-Differenz (+31.905,97 €)
- **Hypothese:** Wenn Einsatz korrekt wäre, wäre Betriebsergebnis auch korrekt

---

## 🔍 ANALYSE-ANSATZ

### Schritt 1: Konten identifizieren

**Für Gesamtbetrieb Einsatz:**
- Welche Konten zwischen 700000-799999 werden von DRIVE erfasst?
- Welche davon sollten möglicherweise ausgeschlossen werden?
- Gibt es Konten mit branch_number oder subsidiary, die falsch zugeordnet sind?

**Für Landau Variable Kosten:**
- Welche Konten zwischen 415100-497899 und 891000-891099 werden von DRIVE erfasst?
- Welche Konten erfasst GlobalCube zusätzlich?
- Gibt es Konten mit 6. Ziffer='2', die nicht erfasst werden sollten?

### Schritt 2: Filter-Logik prüfen

**Gesamtbetrieb Einsatz-Filter:**
```sql
AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)
```

**Landau Variable Kosten-Filter:**
```sql
AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1
```

### Schritt 3: Konten-Listen erstellen

**Benötigte Informationen:**
1. Liste aller Konten, die DRIVE für Gesamtbetrieb Einsatz erfasst (Top 50 nach Betrag)
2. Liste aller Konten, die DRIVE für Landau Variable Kosten erfasst (Top 50 nach Betrag)
3. Vergleich mit GlobalCube: Welche Konten fehlen oder sind zu viel?

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Konten-Listen erstellen:**
   - Gesamtbetrieb Einsatz: Top 50 Konten nach Betrag
   - Landau Variable Kosten: Top 50 Konten nach Betrag

2. ⏳ **GlobalCube-Konten vergleichen:**
   - Welche Konten erfasst GlobalCube zusätzlich?
   - Welche Konten erfasst DRIVE zusätzlich?

3. ⏳ **Filter-Logik anpassen:**
   - Basierend auf Konten-Analyse Filter korrigieren

---

## 💡 HYPOTHESEN

### Hypothese 1: Gesamtbetrieb Einsatz
- Möglicherweise werden Konten mit bestimmten branch_number oder subsidiary falsch zugeordnet
- Oder: 74xxxx Konten werden doppelt gezählt
- Oder: Konten mit branch_number=3 werden falsch zugeordnet

### Hypothese 2: Landau Variable Kosten
- Möglicherweise fehlen bestimmte Konten mit 6. Ziffer='2'
- Oder: 8910xx Konten werden nicht korrekt erfasst
- Oder: Konten mit bestimmten KST-Werten werden ausgeschlossen

---

## 📊 STATUS

- ✅ Direkte Kosten gelöst (nur -16,53 € / -94,36 € Differenz)
- ⏳ Einsatz-Filter analysieren
- ⏳ Variable Kosten analysieren
- ⏳ Konten-Listen erstellen

---

**Nächster Schritt:** Konten-Listen erstellen und mit GlobalCube vergleichen.
