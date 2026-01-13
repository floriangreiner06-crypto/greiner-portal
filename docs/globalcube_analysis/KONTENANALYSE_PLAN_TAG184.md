# Kontenanalyse Plan - Variable Kosten Landau - TAG 184

**Datum:** 2026-01-13  
**Status:** ⏳ Plan erstellt, noch nicht durchgeführt

---

## ❓ SIND DIE ÄNDERUNGEN SCHON IN DRIVE?

**Antwort: NEIN** - Wir haben nur Excel-Dateien analysiert und mit DRIVE verglichen.

**Was wir gemacht haben:**
- ✅ Excel-Struktur analysiert
- ✅ Werte extrahiert und mit DRIVE verglichen
- ✅ Erkenntnisse dokumentiert

**Was wir NICHT gemacht haben:**
- ❌ Keine Änderungen an DRIVE Code
- ❌ Keine Anpassungen der Filter-Logik
- ❌ Keine Konten-Analyse durchgeführt

**DRIVE verwendet weiterhin:**
- Konten-Filter-Logik (nicht Excel-Positionen)
- Variable Kosten: 4151xx, 4355xx, 455xx-456xx, 4870x, 491xx-497xx
- Indirekte Kosten: Standard-Filter (KST 0, 424xx, 438xx, 498xx, 89xxxx)

---

## 🎯 KONTENANALYSE PLAN

### Problem:
- **Excel Landau:** "Fertigmachen" = 7.043,73 €
- **DRIVE Landau:** Variable Kosten = 6.173,95 €
- **Differenz:** -869,78 € (-12,35%)

### Ziel:
Verstehen, welche Konten in Excel "Fertigmachen" enthalten sind, aber nicht in DRIVE Variable Kosten, oder umgekehrt.

---

## 📋 SCHRITTE FÜR KONTENANALYSE

### Schritt 1: DRIVE Variable Kosten Konten extrahieren

**Query für Landau (Dez 2025):**
```sql
SELECT 
    nominal_account_number,
    SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
FROM loco_journal_accountings
WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
  AND (
    nominal_account_number BETWEEN 415100 AND 415199
    OR nominal_account_number BETWEEN 435500 AND 435599
    OR (nominal_account_number BETWEEN 455000 AND 456999
        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
    OR (nominal_account_number BETWEEN 487000 AND 487099
        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
    OR nominal_account_number BETWEEN 491000 AND 497899
  )
  AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
  AND subsidiary_to_company_ref = 1
GROUP BY nominal_account_number
ORDER BY nominal_account_number;
```

**Erwartetes Ergebnis:**
- Liste aller Konten mit ihren Werten
- Summe sollte = 6.173,95 € sein

---

### Schritt 2: Excel "Fertigmachen" Konten identifizieren

**Problem:** Excel zeigt nur Positionen, nicht einzelne Konten!

**Mögliche Ansätze:**

#### Ansatz A: GlobalCube Portal/Reports analysieren
- GlobalCube Reports zeigen möglicherweise detaillierte Konten-Aufschlüsselung
- HAR-Dateien analysieren (falls vorhanden)
- Portal-Reports scrapen (nach Auth-Fix)

#### Ansatz B: Konten-Mapping aus Struktur-Dateien
- `Kontenrahmen.csv` analysieren
- Mapping zwischen Konten und Excel-Positionen finden
- Prüfen welche Konten zu "Fertigmachen" gehören

#### Ansatz C: Reverse Engineering
- Alle Konten 491xx-497xx für Landau extrahieren
- Prüfen welche Konten in Excel "Fertigmachen" sein sollten
- Vergleichen mit DRIVE Filter

---

### Schritt 3: Konten-Vergleich

**Vergleiche:**
1. Welche Konten sind in DRIVE aber nicht in Excel "Fertigmachen"?
2. Welche Konten sind in Excel "Fertigmachen" aber nicht in DRIVE?
3. Gibt es Konten die beide enthalten, aber unterschiedliche Werte haben?

**Mögliche Ursachen:**
- Excel enthält Konten außerhalb 491xx-497xx
- DRIVE filtert bestimmte Konten aus (z.B. KST 0)
- Excel verwendet andere Filter-Logik
- Excel summiert mehrere Positionen zu "Fertigmachen"

---

### Schritt 4: Filter-Logik Analyse

**DRIVE Variable Kosten Filter (Landau):**
- 4151xx: Provisionen Finanz-Vermittlung
- 4355xx: Trainingskosten
- 455xx-456xx: Fahrzeugkosten (nur KST 1-7, 5. Ziffer != '0')
- 4870x: Werbekosten direkt (nur KST 1-7, 5. Ziffer != '0')
- 491xx-497xx: Fertigmachen, Provisionen, Kulanz
- **Landau-spezifisch:** 6. Ziffer='2' AND subsidiary_to_company_ref = 1

**Excel "Fertigmachen":**
- Vermutlich: 491xx-497xx (aber möglicherweise andere Filter?)

**Fragen:**
1. Filtert Excel auch nach 6. Ziffer='2'?
2. Gibt es Konten außerhalb 491xx-497xx in Excel "Fertigmachen"?
3. Werden KST 0 Konten in Excel "Fertigmachen" enthalten?

---

## 🚀 UMSETZUNG

### Option 1: SQL-Analyse (Empfohlen)

**Script erstellen:**
```python
# scripts/analyse_variable_kosten_landau.py
# 1. Extrahiere alle Konten aus DRIVE Variable Kosten Query
# 2. Zeige Konten-Aufschlüsselung
# 3. Prüfe welche Konten-Bereiche verwendet werden
```

**Vorteile:**
- ✅ Direkter Zugriff auf Locosoft Daten
- ✅ Exakte Konten-Liste
- ✅ Schnell umsetzbar

**Nachteile:**
- ⚠️ Excel-Konten müssen anders identifiziert werden

---

### Option 2: GlobalCube Portal Analyse

**Vorgehen:**
1. GlobalCube Scraper Auth-Problem beheben
2. Portal-Reports für Landau scrapen
3. Detaillierte Konten-Aufschlüsselung extrahieren
4. Mit DRIVE vergleichen

**Vorteile:**
- ✅ Exakte Excel/GlobalCube Konten
- ✅ Vollständige Aufschlüsselung

**Nachteile:**
- ⚠️ Auth-Problem muss zuerst gelöst werden
- ⚠️ Mehr Aufwand

---

### Option 3: Kontenrahmen.csv Analyse

**Vorgehen:**
1. `Kontenrahmen.csv` analysieren
2. Mapping zwischen Konten und Excel-Positionen finden
3. Prüfen welche Konten zu "Fertigmachen" gehören

**Vorteile:**
- ✅ Nutzt vorhandene Struktur-Dateien
- ✅ Kein Scraping nötig

**Nachteile:**
- ⚠️ Mapping möglicherweise nicht vollständig
- ⚠️ Excel-Positionen möglicherweise nicht direkt mappbar

---

## 💡 EMPFEHLUNG

**Schritt 1: SQL-Analyse (sofort umsetzbar)**
1. Script erstellen: `scripts/analyse_variable_kosten_landau.py`
2. DRIVE Variable Kosten Konten extrahieren
3. Konten-Aufschlüsselung anzeigen
4. Prüfen welche Konten-Bereiche verwendet werden

**Schritt 2: Kontenrahmen.csv Analyse**
1. `Kontenrahmen.csv` analysieren
2. Prüfen ob Mapping zu "Fertigmachen" vorhanden
3. Konten-Liste extrahieren

**Schritt 3: Vergleich**
1. DRIVE Konten vs. Kontenrahmen.csv "Fertigmachen"
2. Differenzen identifizieren
3. Filter-Logik anpassen (falls nötig)

**Schritt 4: GlobalCube Portal (optional)**
1. Auth-Problem beheben
2. Portal-Reports scrapen
3. Detaillierte Aufschlüsselung vergleichen

---

## 📁 ZU ERSTELLENDE DATEIEN

1. `scripts/analyse_variable_kosten_landau.py` - SQL-Analyse Script
2. `docs/globalcube_analysis/kontenanalyse_landau_tag184.md` - Ergebnisse
3. `docs/globalcube_analysis/kontenvergleich_landau_tag184.json` - Konten-Vergleich

---

## ❓ OFFENE FRAGEN

1. **Sollen wir die Kontenanalyse jetzt durchführen?**
   - Ja → Schritt 1 (SQL-Analyse) starten
   - Nein → Später, wenn nötig

2. **Sollen wir DRIVE Filter anpassen?**
   - Nur wenn Kontenanalyse zeigt, dass Excel-Filter korrekter ist
   - Oder wenn GlobalCube Filter-Logik anders ist

3. **Ist die -12,35% Differenz akzeptabel?**
   - Wenn ja → Keine Änderungen nötig
   - Wenn nein → Kontenanalyse durchführen

---

*Erstellt: TAG 184 | Autor: Claude AI*
