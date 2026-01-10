# Erkenntnisse: DB3-Abweichung Globalcube vs. DRIVE BWA

**Datum:** 2026-01-09  
**TAG:** 177  
**Status:** Analyse läuft

---

## Zusammenfassung

**DB3-Abweichung Jahr per Aug./2025:**
- DRIVE: 2.701.120,19 €
- Globalcube: 2.801.501,76 €
- **Differenz:** +100.381,57 € (Globalcube HÖHER)

**Bedeutung:**
- Globalcube hat **100.381,57 € WENIGER direkte Kosten** als DRIVE
- Globalcube zählt bestimmte Konten **NICHT als direkte Kosten**, die DRIVE als direkte Kosten zählt

---

## Analyse-Ergebnisse

### 1. Vollständigkeit des Imports ✅

**Ergebnis:** Alle Buchungen werden aus Locosoft importiert
- Locosoft (QUELLE): 250.202 Buchungen
- DRIVE Portal (ZIEL): 250.202 Buchungen
- **Differenz:** 0 Buchungen ✅

**Direkte Kosten Werte:**
- Locosoft (QUELLE): 1.837.073,09 €
- DRIVE Portal (ZIEL): 1.837.073,09 €
- **Differenz:** 0,00 € ✅

**Fazit:** Die Abweichung kommt **NICHT** durch fehlende Buchungen!

### 2. Filter-Logik Unterschiede

**Aktuelle DRIVE Filter-Logik (direkte Kosten):**
```sql
nominal_account_number BETWEEN 400000 AND 489999
AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
AND NOT (
    nominal_account_number BETWEEN 415100 AND 415199  -- Variable
    OR nominal_account_number BETWEEN 424000 AND 424999  -- Indirekte
    OR nominal_account_number BETWEEN 435500 AND 435599  -- Variable
    OR nominal_account_number BETWEEN 438000 AND 438999  -- Indirekte
    OR nominal_account_number BETWEEN 455000 AND 456999  -- Variable
    OR nominal_account_number BETWEEN 487000 AND 487099  -- Variable
    OR nominal_account_number BETWEEN 491000 AND 497999  -- Variable
)
```

**Getestete Varianten:**
- ❌ Aktuell (DRIVE): Diff 100.381,57 €
- ❌ Ohne 424xx/438xx Ausschluss: Diff 159.241,05 €
- ❌ Nur KST 1-3,6-7: Diff 100.381,57 €
- ❌ Alle KST 1-7 (keine Ausschlüsse): Diff 424.500,36 €

**Fazit:** Keine der getesteten Varianten passt genau!

### 3. Kontenbereiche-Analyse

**Größte Kontenbereiche in direkten Kosten (DRIVE):**
- 415xxx: 1.123.903,90 € (61,18%)
- 430xxx: 517.923,09 € (28,19%)
- 411xxx: 95.789,70 € (5,21%)
- 432xxx: 33.499,49 € (1,82%)
- 410xxx: 31.484,22 € (1,71%)
- 469xxx: 23.351,35 € (1,27%)
- 436xxx: 10.472,67 € (0,57%)
- 489xxx: 648,67 € (0,04%)

**Nahe an der Differenz:**
- 411xxx: 95.789,70 € (Diff: 4.591,87 € zu 100.381,57 €)

**Fazit:** Die Differenz kommt wahrscheinlich aus einer **Kombination mehrerer Bereiche** oder einem **Teilbereich** von 415xxx oder 430xxx.

---

## Hypothesen

### Hypothese 1: Globalcube zählt Teilbereiche als Variable Kosten
Möglicherweise zählt Globalcube bestimmte Teilbereiche von 415xxx oder 430xxx als Variable Kosten, die DRIVE als direkte Kosten zählt.

**Zu prüfen:**
- Gibt es Teilbereiche von 415xxx, die in Globalcube als Variable Kosten gezählt werden?
- Gibt es Teilbereiche von 430xxx, die in Globalcube als Variable Kosten gezählt werden?

### Hypothese 2: Globalcube verwendet andere KST-Filter
Möglicherweise verwendet Globalcube andere KST-Filter (z.B. nur bestimmte KST-Werte).

**Zu prüfen:**
- Welche KST-Werte verwendet Globalcube für direkte Kosten?
- Gibt es Unterschiede in der KST-Filterung?

### Hypothese 3: Globalcube hat manuelle Anpassungen
Möglicherweise hat Globalcube manuelle Anpassungen oder Korrekturen, die nicht in Locosoft sind.

**Bewertung:** Unwahrscheinlich, da Globalcube nur Locosoft als Quelle hat.

---

## Nächste Schritte

1. **Detaillierte Analyse von 415xxx und 430xxx:**
   - Prüfe, ob es Teilbereiche gibt, die in Globalcube anders zugeordnet werden
   - Prüfe, ob bestimmte Konten in Globalcube als Variable Kosten gezählt werden

2. **KST-Filter-Analyse:**
   - Prüfe, ob Globalcube andere KST-Filter verwendet
   - Teste verschiedene KST-Kombinationen

3. **Monat-für-Monat-Vergleich:**
   - Identifiziere, in welchen Monaten die Abweichungen entstehen
   - Prüfe, ob es monatsspezifische Unterschiede gibt

---

## Scripts

- `scripts/analyse_import_vollstaendigkeit.py` - ✅ Import-Vollständigkeit geprüft
- `scripts/analyse_globalcube_filter_varianten.py` - Filter-Varianten getestet
- `scripts/analyse_was_globalcube_nicht_zaehlt.py` - Kontenbereiche analysiert
- `scripts/analyse_100k_differenz_konten.py` - Detaillierte Kontenanalyse

---

**Status:** Analyse läuft - Filter-Unterschiede müssen noch identifiziert werden
