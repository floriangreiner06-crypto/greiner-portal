# GlobalCube Export-Anleitung für BWA-Differenz-Analyse

**Datum:** 2026-01-14  
**Zweck:** Systematische Analyse der BWA-Differenzen zwischen DRIVE und GlobalCube

---

## 📋 ÜBERSICHT

**Aktuelle Differenzen (TAG 188):**
- **Monat Dezember 2025:** Betriebsergebnis +50.100,63 € (DRIVE zu positiv)
- **YTD Sep-Dez 2025:** Betriebsergebnis +54.575,29 € (DRIVE zu positiv)

**Ziel:** Position-für-Position-Vergleich um Ursachen zu identifizieren

---

## 🎯 EMPFOHLENES DATEIFORMAT

### ✅ **Excel Daten (mit Filter)** - **EMPFOHLEN**

**Warum:**
- ✅ Strukturierte Daten (Tabellenformat)
- ✅ Filter bereits angewandt (spart Zeit)
- ✅ Einfach in Python zu verarbeiten
- ✅ Kann direkt mit DRIVE-Werten verglichen werden

**Alternative:** Excel (normales Excel) - auch OK, aber weniger strukturiert

**NICHT empfohlen:** XML, CSV (schwerer zu verarbeiten)

---

## 📊 REPORT 1: BWA Gesamtbetrieb - Monat Dezember 2025

### Filter:
- **Zeitraum:** Dezember 2025 (01.12.2025 - 31.12.2025)
- **Filiale:** Alle (Gesamtbetrieb)
- **KST:** Alle

### Drill-Down erforderlich:
1. ✅ **Umsatz** (8xxxxx Konten)
2. ✅ **Einsatz** (7xxxxx Konten)
3. ✅ **Bruttoertrag (DB1)** = Umsatz - Einsatz
4. ✅ **Variable Kosten** (4xxxxx mit KST-Filter)
5. ✅ **Bruttoertrag II (DB2)** = DB1 - Variable Kosten
6. ✅ **Direkte Kosten** (4xxxxx bestimmte Bereiche)
7. ✅ **Deckungsbeitrag (DB3)** = DB2 - Direkte Kosten
8. ✅ **Indirekte Kosten** (4xxxxx bestimmte Bereiche)
9. ✅ **Betriebsergebnis** = DB3 - Indirekte Kosten
10. ✅ **Neutrales Ergebnis** (2xxxxx Konten)
11. ✅ **Unternehmensergebnis** = BE + Neutrales Ergebnis

### Dateiname:
```
GlobalCube_BWA_Gesamtbetrieb_Monat_Dez2025.xlsx
```

---

## 📊 REPORT 2: BWA Gesamtbetrieb - YTD Sep-Dez 2025

### Filter:
- **Zeitraum:** September 2025 - Dezember 2025 (01.09.2025 - 31.12.2025)
- **Filiale:** Alle (Gesamtbetrieb)
- **KST:** Alle

### Drill-Down erforderlich:
**Gleiche Positionen wie Report 1** (nur YTD-Werte)

### Dateiname:
```
GlobalCube_BWA_Gesamtbetrieb_YTD_SepDez2025.xlsx
```

---

## 📊 REPORT 3: BWA Konten-Details - Monat Dezember 2025

### Filter:
- **Zeitraum:** Dezember 2025 (01.12.2025 - 31.12.2025)
- **Filiale:** Alle (Gesamtbetrieb)
- **KST:** Alle

### Drill-Down auf Konten-Ebene:
**WICHTIG:** Für jede BWA-Position die einzelnen Konten exportieren:

1. **Umsatz-Konten (8xxxxx):**
   - Alle Konten 800000-899999
   - Besonders: 89xxxx Konten (Hyundai)

2. **Einsatz-Konten (7xxxxx):**
   - Alle Konten 700000-799999
   - Besonders: 743002 (sollte ausgeschlossen sein)

3. **Variable Kosten (4xxxxx):**
   - Konten 415100-415199
   - Konten 435500-435599
   - Konten 455000-456999 (mit KST!=0)
   - Konten 487000-487099 (mit KST!=0)
   - Konten 491000-497899
   - **Besonders:** 891000-891099 (sollte für Hyundai ausgeschlossen sein)

4. **Direkte Kosten (4xxxxx):**
   - Alle relevanten Konten-Bereiche
   - Besonders: 411xxx, 489xxx, 410021 (historisch problematisch)

5. **Indirekte Kosten (4xxxxx):**
   - Alle relevanten Konten-Bereiche
   - **Besonders:** 498001 (sollte ausgeschlossen sein)

6. **Neutrales Ergebnis (2xxxxx):**
   - Alle Konten 200000-299999

### Dateiname:
```
GlobalCube_BWA_Konten_Details_Monat_Dez2025.xlsx
```

---

## 📊 REPORT 4: BWA Konten-Details - YTD Sep-Dez 2025

### Filter:
- **Zeitraum:** September 2025 - Dezember 2025 (01.09.2025 - 31.12.2025)
- **Filiale:** Alle (Gesamtbetrieb)
- **KST:** Alle

### Drill-Down:
**Gleiche Konten-Details wie Report 3** (nur YTD-Werte)

### Dateiname:
```
GlobalCube_BWA_Konten_Details_YTD_SepDez2025.xlsx
```

---

## 📊 REPORT 5 (OPTIONAL): BWA nach Standort - Monat Dezember 2025

**Nur wenn Zeit vorhanden** - hilft bei Standort-spezifischen Problemen:

### Filter:
- **Zeitraum:** Dezember 2025 (01.12.2025 - 31.12.2025)
- **Filiale:** Einzeln exportieren:
  1. Deggendorf Opel (Filiale 1)
  2. Deggendorf Hyundai (Filiale 2)
  3. Landau (Filiale 3)
- **KST:** Alle

### Drill-Down:
**Gleiche Positionen wie Report 1** (pro Standort)

### Dateinamen:
```
GlobalCube_BWA_DeggendorfOpel_Monat_Dez2025.xlsx
GlobalCube_BWA_DeggendorfHyundai_Monat_Dez2025.xlsx
GlobalCube_BWA_Landau_Monat_Dez2025.xlsx
```

---

## 🔍 WICHTIGE HINWEISE

### 1. Konten-Bereiche die besonders wichtig sind:

**Einsatz (7xxxxx):**
- ⚠️ **743002** - "EW Fremdleistungen für Kunden" (sollte ausgeschlossen sein, TAG 187)

**Variable Kosten (4xxxxx):**
- ⚠️ **891000-891099** - Sollte für Hyundai ausgeschlossen sein (TAG 182)

**Indirekte Kosten (4xxxxx):**
- ⚠️ **498001** - "Umlagekosten" (sollte ausgeschlossen sein, TAG 188)

**Direkte Kosten (4xxxxx):**
- ⚠️ **411xxx** - "Ausbildungsvergütung" (historisch problematisch, TAG 182)
- ⚠️ **489xxx** - (historisch problematisch, TAG 182)
- ⚠️ **410021** - (historisch problematisch, TAG 182)

**Umsatz (8xxxxx):**
- ⚠️ **89xxxx** - Hyundai-Umsatz (außer 8932xx, TAG 182)
- ⚠️ **8932xx** - Sonderumsatz (TAG 182)

### 2. Format-Anforderungen:

**Excel Spalten sollten enthalten:**
- Kontonummer (nominal_account_number)
- Kontobezeichnung
- Soll (debit)
- Haben (credit)
- Saldo (balance)
- Datum (accounting_date) - wenn verfügbar
- Filiale/Standort - wenn verfügbar
- KST (Kostenstelle) - wenn verfügbar

### 3. Vergleich mit DRIVE:

**Nach Export:**
- Excel-Dateien in `/mnt/greiner-portal-sync/docs/` speichern
- Python-Script wird erstellt um automatisch zu vergleichen
- Position-für-Position-Differenzen werden identifiziert

---

## 📁 SPEICHERORT

**Alle Excel-Dateien speichern in:**
```
\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\
```

**Oder auf Server:**
```
/mnt/greiner-portal-sync/docs/
```

---

## ✅ CHECKLISTE

### Priorität HOCH (MUSS):
- [ ] Report 1: BWA Gesamtbetrieb - Monat Dezember 2025
- [ ] Report 2: BWA Gesamtbetrieb - YTD Sep-Dez 2025
- [ ] Report 3: BWA Konten-Details - Monat Dezember 2025
- [ ] Report 4: BWA Konten-Details - YTD Sep-Dez 2025

### Priorität MITTEL (SOLLTE):
- [ ] Report 5: BWA nach Standort - Monat Dezember 2025 (optional)

---

## 🚀 NÄCHSTE SCHRITTE NACH EXPORT

1. **Excel-Dateien prüfen:**
   - Struktur validieren
   - Werte mit bekannten GlobalCube-Werten abgleichen

2. **Python-Vergleichs-Script erstellen:**
   - Automatischer Vergleich DRIVE vs. GlobalCube
   - Position-für-Position-Differenzen identifizieren

3. **Differenzen analysieren:**
   - Welche Konten fehlen in DRIVE?
   - Welche Konten sind in DRIVE zu viel?
   - Filter-Unterschiede identifizieren

4. **Korrekturen implementieren:**
   - Fehlende Ausschlüsse hinzufügen
   - Filter anpassen
   - Code-Korrekturen in `api/controlling_api.py`

---

*Erstellt: TAG 192 | Autor: Claude AI*
