# BWA KST-Logik: Warum funktioniert es trotz Fehler?

**Datum:** 2026-01-12  
**TAG:** 181  
**Frage:** Warum zeigt die BWA trotz falscher KST-Logik die richtigen Werte?

---

## 🔍 DAS PROBLEM

### 1. Einsatzwert- und Erlöskonten (7xxxxx und 8xxxxx)

**KORRIGIERT nach Buchhaltung (TAG 181):**
- **Kostenstelle** = **2. Ziffer** (nicht 6. Ziffer!)
- **Filiale** = **6. Ziffer** (letzte Ziffer)

**Beispiel: 810001**
- 8 = Erlöskonto
- **1** (2. Ziffer) = **Kostenstelle** (1 = NW)
- 0 = ohne Bedeutung
- 0 = ohne Bedeutung  
- 0 = Absatzweg
- **1** (6. Ziffer) = **Filiale** (1 = DEG bei Opel, oder Hyundai; 2 = Landau bei Opel)

### 2. Kostenkonten (4xxxxx)

**Richtig:** Kostenstelle in 5. Ziffer  
**ABER:** KST 6 (T+Z) und KST 7 (Mietwagen) werden nicht erkannt

**Kostenstellen-Mapping:**
- 1 = NW
- 2 = GW
- 3 = Service/Werkstatt
- **6 = T+Z** (fehlt!)
- **7 = Mietwagen** (fehlt!)

---

## ✅ WARUM FUNKTIONIERT ES TROTZDEM?

### Die BWA filtert nach Kontonummer-Bereichen, NICHT nach Kostenstellen!

**Aktuelle Logik:**
```python
BEREICHE_CONFIG = {
    'NW': {
        'erlos_prefix': '81',    # 81xxxx = ALLE NW-Erlöse
        'einsatz_prefix': '71',  # 71xxxx = ALLE NW-Einsätze
    },
    'GW': {
        'erlos_prefix': '82',    # 82xxxx = ALLE GW-Erlöse
        'einsatz_prefix': '72',  # 72xxxx = ALLE GW-Einsätze
    },
    # etc.
}
```

**Das bedeutet:**
- ✅ **81xxxx** erfasst ALLE Neuwagen-Erlöse (egal welche Kostenstelle in Ziffer 6)
- ✅ **82xxxx** erfasst ALLE Gebrauchtwagen-Erlöse
- ✅ Die Kontonummer-Bereiche decken automatisch die richtigen Bereiche ab

**Warum funktioniert das?**
- In Locosoft sind die Kontonummern so strukturiert, dass:
  - 81xxxx = immer Neuwagen (unabhängig von Kostenstelle)
  - 82xxxx = immer Gebrauchtwagen
  - Die Kostenstelle in Ziffer 6 unterscheidet nur die Filiale, nicht den Bereich!

---

## ⚠️ ABER: WANN FUNKTIONIERT ES NICHT?

### 1. KST-Filter für Umsatz/Einsatz

**KORRIGIERT (TAG 181):**
- ✅ **Kostenstelle** = 2. Ziffer (korrekt implementiert in Kontenmapping)
- ✅ **Filiale** = 6. Ziffer (wird zusätzlich angezeigt)

**Beispiel:**
- Konto 810001: KST = 1 (2. Ziffer), Filiale = 1 (6. Ziffer)
- Kontenmapping zeigt jetzt korrekt: KST = 1, Filiale = 1

### 2. Kosten-Konten: KST 6 und 7 fehlen

**Problem:** 
- KST 6 = T+Z wird nicht erkannt
- KST 7 = Mietwagen wird nicht erkannt

**Aktuell:**
```python
# Nur KST 1-7, aber 6 und 7 fehlen in manchen Filtern!
substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
```

**ABER:** In manchen Filtern fehlen 6 und 7:
```python
# FALSCH - fehlt 6 und 7:
substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7')  # Nur in speziellen Bereichen
```

---

## 🎯 FAZIT

### Warum zeigt die BWA die richtigen Werte?

1. ✅ **Bereiche werden nach Kontonummer-Präfix gefiltert** (81xxxx, 82xxxx)
   - Das funktioniert unabhängig von der Kostenstelle
   - Die Kostenstelle in Ziffer 6 unterscheidet nur die Filiale, nicht den Bereich

2. ✅ **Gesamtwerte sind korrekt**
   - Alle 81xxxx = NW (egal welche KST)
   - Alle 82xxxx = GW (egal welche KST)

3. ⚠️ **ABER: KST-Filter funktioniert nicht korrekt**
   - Wenn wir nach KST filtern wollen, müssen wir die 6. Ziffer prüfen
   - Aktuell prüfen wir die 5. Ziffer (falsch für Umsatz/Einsatz)

### Sind das nur Bezeichnungsfehler?

**Teilweise:**
- ✅ Für Gesamt-BWA: Ja, nur Bezeichnungsfehler (funktioniert trotzdem)
- ❌ Für KST-Filter: Nein, mathematische Auswirkung (Filter funktioniert nicht korrekt)

---

## 🔧 WAS WURDE KORRIGIERT? (TAG 181)

1. ✅ **Kontenmapping-Export:** KST-Stelle korrekt anzeigen
   - Umsatz/Einsatz: **2. Ziffer** (Kostenstelle), **6. Ziffer** (Filiale)
   - Kosten: 5. Ziffer (unverändert)

2. ✅ **Filiale wird zusätzlich angezeigt:**
   - Neue Spalte `filiale` (6. Ziffer)
   - Neue Spalte `filiale_name` (DEG/Landau)

3. ✅ **Kostenstellen-Mapping korrigiert:**
   - Umsatz/Einsatz: 2. Ziffer = KST (1=NW, 2=GW, 3=T+Z, 4=Service, 6=Mietwagen)
   - Kosten: 5. Ziffer = KST (unverändert: 0=Gemeinkosten, 1=NW, 2=GW, 3=Service, 6=T+Z, 7=Mietwagen)
