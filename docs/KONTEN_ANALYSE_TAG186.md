# Konten-Analyse - Identifizierte Probleme TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **PROBLEME IDENTIFIZIERT**

---

## 🎯 IDENTIFIZIERTE PROBLEME

### 1. LANDAU VARIABLE KOSTEN ✅ **LÖSUNG GEFUNDEN!**

**Problem:**
- DRIVE (mit 6. Ziffer='2'): 25.905,53 €
- GlobalCube: 39.162,00 €
- **Fehlend:** 13.256,47 €

**Gefundene Konten:**
- **497031** (branch=3, 6. Ziffer='1'): 7.494,13 €
- **497061** (branch=3, 6. Ziffer='1'): 2.940,69 €
- **497211** (branch=3, 6. Ziffer='1'): 1.903,64 €
- **497221** (branch=3, 6. Ziffer='1'): 874,16 €
- **497011** (branch=3, 6. Ziffer='1'): 43,82 €
- **Summe:** 13.256,44 € ✅ (entspricht genau der fehlenden Differenz!)

**Lösung:**
- Landau Variable Kosten sollte **branch_number=3 OR 6. Ziffer='2'** verwenden
- **Erwartetes Ergebnis:** 39.161,97 € (fast genau GlobalCube 39.162,00 €!)

**Konten, die hinzugefügt werden müssen:**
- 497031, 497061, 497211, 497221, 497011 (alle mit branch=3, aber 6. Ziffer='1')

---

### 2. GESAMTBETRIEB EINSATZ ⚠️ **ANALYSE ERFORDERLICH**

**Problem:**
- DRIVE: 9.223.769,97 €
- GlobalCube: 9.191.864,00 €
- **Differenz:** +31.905,97 €

**Aufschlüsselung nach Filter:**
- Konten mit branch=3 (Landau): 1.133.115,18 €
- Konten mit 6.Ziffer=1, branch != 3 (Deggendorf Stellantis): 5.023.125,03 €
- Konten mit 6.Ziffer=1, subsidiary=2 (Hyundai): 2.994.133,88 €
- **Summe:** 9.150.374,09 €

**Differenz:** 9.223.769,97 - 9.150.374,09 = **73.395,88 €**

**Mögliche Ursachen:**
1. Doppelzählungen (Konten werden mehrfach erfasst)
2. 74xxxx Konten mit branch=1 werden doppelt gezählt
3. Konten mit bestimmten branch_number werden falsch zugeordnet

**Top 10 Konten (nach Betrag):**
1. 724201: 1.010.388,99 € (157 Buchungen)
2. 721201: 615.241,58 € (141 Buchungen)
3. 718001: 602.145,96 € (100 Buchungen)
4. 723101: 574.517,95 € (143 Buchungen)
5. 720301: 435.159,66 € (107 Buchungen)
6. 721202: 396.255,90 € (51 Buchungen)
7. 713111: 363.996,53 € (47 Buchungen)
8. 730301: 254.984,04 € (1164 Buchungen)
9. 710631: 250.767,76 € (31 Buchungen)
10. 730001: 238.767,14 € (1400 Buchungen)

**Frage:** Welche dieser Konten werden möglicherweise doppelt gezählt oder sollten ausgeschlossen werden?

---

## 💡 LÖSUNGSVORSCHLÄGE

### Lösung 1: Landau Variable Kosten

**Aktuell:**
```python
variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
```

**Korrigiert:**
```python
variable_kosten_filter = "AND (branch_number = 3 OR substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2') AND subsidiary_to_company_ref = 1"
```

**Erwartetes Ergebnis:**
- Vorher: 25.905,53 €
- Nachher: 39.161,97 €
- GlobalCube: 39.162,00 €
- **Differenz:** -0,03 € ✅

### Lösung 2: Gesamtbetrieb Einsatz

**Benötigte Informationen:**
1. Welche Konten erfasst GlobalCube für Gesamtbetrieb Einsatz?
2. Gibt es Konten, die ausgeschlossen werden sollten?
3. Gibt es Doppelzählungen in der aktuellen Filter-Logik?

**Mögliche Ursachen:**
- 74xxxx Konten mit branch=1 werden möglicherweise doppelt gezählt
- Konten mit bestimmten branch_number werden falsch zugeordnet

---

## 📋 BENÖTIGTE INFORMATIONEN VOM BENUTZER

### Für Landau Variable Kosten:
✅ **GEFUNDEN!** Konten 497031, 497061, 497211, 497221, 497011 müssen hinzugefügt werden.

### Für Gesamtbetrieb Einsatz:
❓ **Benötigt:** Liste der Konten, die GlobalCube für Gesamtbetrieb Einsatz erfasst
❓ **Benötigt:** Prüfen, ob bestimmte Konten ausgeschlossen werden sollten
❓ **Benötigt:** Prüfen, ob es Doppelzählungen gibt

**Konkrete Fragen:**
1. Welche Konten erfasst GlobalCube für Gesamtbetrieb Einsatz (YTD Sep-Dez 2025)?
2. Sollen bestimmte Konten ausgeschlossen werden?
3. Gibt es Konten mit branch_number, die falsch zugeordnet sind?

---

## 📊 STATUS

- ✅ Landau Variable Kosten: Lösung gefunden (Konten identifiziert)
- ⏳ Gesamtbetrieb Einsatz: Analyse erforderlich (Konten-Liste benötigt)

---

**Nächster Schritt:** Landau Variable Kosten korrigieren, dann Gesamtbetrieb Einsatz analysieren.
