# Analyse: DB3-Abweichung Globalcube vs. DRIVE BWA

**Datum:** 2026-01-09  
**TAG:** 177  
**Ziel:** Identifizierung der Ursache für DB3-Abweichung von -100.381,57 €

---

## Zusammenfassung

**DB3-Abweichung Jahr per Aug./2025:**
- DRIVE: 2.701.120,19 €
- Globalcube: 2.801.501,76 €
- **Differenz:** -100.381,57 € (-3,58%)

**Indirekte Kosten-Abweichung:**
- DRIVE: 2.457.776,74 €
- Globalcube: 2.479.617,08 €
- **Differenz:** -21.840,34 € (-0,88%)

**Betriebsergebnis-Abweichung:**
- DRIVE: 243.343,45 €
- Globalcube: 321.884,68 €
- **Differenz:** -78.541,23 € (-24,40%)

---

## Analyse-Ergebnisse

### 1. Direkte Kosten - Kontenbereiche

**Aktuelle direkte Kosten (DRIVE):** 1.837.073,09 €

**Kontenbereiche in direkten Kosten:**
- 4100x-4110x (Lohn/Gehalt): 127.273,92 € (6,93%)
- 4150x (ohne 4151xx): 1.123.903,90 € (61,18%)
- 4300x-4320x (Lohn/Gehalt): 551.422,58 € (30,02%)
- 4360x (Lohn/Gehalt): 10.472,67 € (0,57%)
- 4690x (Sonstige Kosten): 23.351,35 € (1,27%)
- 4890x (Sonstige Kosten): 648,67 € (0,04%)

**Ausgeschlossene Bereiche (korrekt):**
- 4151xx (Variable): 81.554,55 € ✅
- 424xx (Indirekte): 19.473,48 € ✅
- 4355xx (Variable): 49.561,62 € ✅
- 438xx (Indirekte): 39.386,00 € ✅
- 455xx-456xx (Variable): 75.878,27 € ✅
- 4870x (Variable): 72.389,23 € ✅
- 491xx-497xx (Variable): 624.544,98 € ✅

**Gesamt KST 1-7 (40xxxx-48xxxx):** 2.161.191,88 €
- Davon in direkten Kosten: 1.837.073,09 €
- Differenz (ausgeschlossen): 324.118,79 €

### 2. Mögliche Ursachen

#### 2.1 Kontenbereiche fehlen nicht
✅ Alle ausgeschlossenen Bereiche sind korrekt zugeordnet (Variable/Indirekte Kosten)

#### 2.2 424xx/438xx KST 4/5
- **Status:** 0,00 € (keine Buchungen mit KST 4/5)
- **Bewertung:** Kein Problem

#### 2.3 4500xx-Konten
- **Status:** Alle 45xxxx-Konten mit KST 1-7 sind 455xx oder 456xx (Variable Kosten)
- **Bewertung:** Korrekt ausgeschlossen

#### 2.4 Filter-Logik
Die aktuelle Filter-Logik für direkte Kosten:
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

**Bewertung:** ✅ Filter-Logik ist korrekt

### 3. Hypothesen

#### Hypothese 1: Globalcube zählt bestimmte Konten anders
Möglicherweise zählt Globalcube bestimmte Kontenbereiche als direkte Kosten, die in DRIVE als Variable oder Indirekte Kosten gezählt werden.

**Zu prüfen:**
- Gibt es Kontenbereiche, die in Globalcube als direkte Kosten gezählt werden, aber in DRIVE nicht?
- Gibt es Unterschiede in der Behandlung von bestimmten Konten?

#### Hypothese 2: Zeitpunkt-Unterschiede
Möglicherweise gibt es Unterschiede im Zeitpunkt der Buchungen (Buchungsdatum vs. Wertstellungsdatum).

**Zu prüfen:**
- Werden Buchungen in Globalcube zu einem anderen Zeitpunkt erfasst?
- Gibt es Rückbuchungen oder Korrekturen, die unterschiedlich behandelt werden?

#### Hypothese 3: Rundungsdifferenzen
Die Abweichung von -100.381,57 € könnte durch kumulierte Rundungsdifferenzen entstehen.

**Bewertung:** Unwahrscheinlich, da die Abweichung zu groß ist.

#### Hypothese 4: Monat-für-Monat-Abweichungen
Die Abweichung könnte sich über mehrere Monate kumulieren.

**Nächster Schritt:** Monat-für-Monat-Vergleich durchführen (siehe `scripts/analyse_bwa_monatlich_globalcube.py`)

---

## Nächste Schritte

1. **Monat-für-Monat-Vergleich:**
   - Script ausführen: `scripts/analyse_bwa_monatlich_globalcube.py`
   - Identifizieren, in welchen Monaten die Abweichungen entstehen

2. **Globalcube CSV analysieren:**
   - CSV-Datei: `/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (17).csv`
   - Monatswerte extrahieren und mit DRIVE vergleichen

3. **Kontenbereiche prüfen:**
   - Prüfen, ob es Kontenbereiche gibt, die in Globalcube anders behandelt werden
   - Möglicherweise gibt es spezielle Konten, die in Globalcube als direkte Kosten gezählt werden

4. **Indirekte Kosten analysieren:**
   - Abweichung von -21.840,34 € analysieren
   - Prüfen, ob bestimmte Konten fehlen oder falsch zugeordnet sind

---

## Scripts

- `scripts/analyse_direkte_kosten_detailed.py` - Detaillierte Analyse direkte Kosten
- `scripts/analyse_konten_abweichung_db3.py` - Kontenbereiche-Analyse
- `scripts/analyse_4500xx_detailed.py` - 4500xx-Konten-Analyse
- `scripts/analyse_bwa_monatlich_globalcube.py` - Monat-für-Monat-Vergleich

---

## Erkenntnisse

✅ **Filter-Logik ist korrekt:** Alle ausgeschlossenen Bereiche sind korrekt zugeordnet

⚠️ **Abweichung bleibt ungeklärt:** Die DB3-Differenz von -100.381,57 € kann durch die aktuelle Analyse nicht erklärt werden

🔍 **Nächster Schritt:** Monat-für-Monat-Vergleich durchführen, um zu identifizieren, in welchen Monaten die Abweichungen entstehen

---

**Status:** Analyse abgeschlossen, weitere Untersuchung erforderlich
