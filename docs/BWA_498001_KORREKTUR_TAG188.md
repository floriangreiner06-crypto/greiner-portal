# BWA 498001 Korrektur - TAG 188

**Datum:** 2026-01-XX  
**Status:** ✅ Korrigiert - 498001 wieder eingeschlossen

---

## 🐛 PROBLEM

**Falsche Annahme:** 498001 wurde fälschlicherweise aus indirekten Kosten ausgeschlossen.

**Korrekte Situation:**
- Auto Greiner (Hyundai) **ZAHLT** 50.000 €/Monat Umlage an Autohaus Greiner (Stellantis)
- 498001 ist eine **ECHTE Kostenposition** und sollte in der normalen BWA **ENTHALTEN** sein
- Nur bei "ohne Umlage" sollte 498001 ausgeschlossen werden

---

## ✅ KORREKTUR

**Änderung:** 498001-Ausschluss wurde RÜCKGÄNGIG gemacht.

**498001 ist jetzt wieder in indirekten Kosten enthalten:**
- ✅ Monat indirekte Kosten (`_berechne_bwa_werte`)
- ✅ YTD indirekte Kosten (`_berechne_bwa_ytd`)
- ✅ v2 API indirekte Kosten (alle Filter-Varianten)
- ✅ Drill-Down indirekte Kosten

**Hinweis:** 498001 wird als HABEN gebucht (Kostenminderung), was in der Logik `SOLL - HABEN` zu einer Kostenreduzierung um 50.000 € führt. Das ist korrekt, da es eine interne Verrechnung ist.

---

## 📋 KONTEXT

### Umlage-Struktur:

```
STELLANTIS (Autohaus Greiner) ERHÄLT:
  817051 = Umlage-Erlös Neuwagen        +12.500 €/Monat (HABEN)
  827051 = Umlage-Erlös Gebrauchtwagen  +12.500 €/Monat (HABEN)
  837051 = Umlage-Erlös Werkstatt       +12.500 €/Monat (HABEN)
  847051 = Umlage-Erlös Teile           +12.500 €/Monat (HABEN)
  ─────────────────────────────────────────────────────────────
  SUMME ERLÖSE:                         +50.000 €/Monat

HYUNDAI (Auto Greiner) ZAHLT:
  498001 = Umlage-Kosten                -50.000 €/Monat (HABEN!)
  ─────────────────────────────────────────────────────────────
  KONZERN-EFFEKT:                              0 €  ← Nullsumme!
```

### Buchungslogik:

- 498001 wird als **HABEN** gebucht (Kostenminderung)
- In der Kosten-Logik: `SOLL - HABEN` → HABEN wird **negativ**
- Ergebnis: Die indirekten Kosten werden **um 50.000 € gemindert**
- Das ist korrekt, da es eine interne Verrechnung ist (Nullsumme im Konzern)

---

## 🔧 TECHNISCHE DETAILS

### Entfernte Ausschlüsse:

**Vorher (FALSCH):**
```sql
AND NOT (nominal_account_number = 498001)
```

**Nachher (KORREKT):**
```sql
-- 498001 ist enthalten in 498000-499999 Bereich
```

### Betroffene Stellen:

- `api/controlling_api.py` Zeile 602 (Monat) - ✅ Korrigiert
- `api/controlling_api.py` Zeile 1162 (YTD) - ✅ Korrigiert
- `api/controlling_api.py` Zeile 1855, 1876, 1899 (v2 API) - ✅ Korrigiert
- `api/controlling_api.py` Zeile 3032 (Drill-Down) - ✅ Korrigiert

---

## 📊 ERWARTETE AUSWIRKUNG

**Nach Korrektur:**
- Indirekte Kosten werden um 50.000 €/Monat **reduziert** (weil 498001 als HABEN gebucht wird)
- Betriebsergebnis wird um 50.000 €/Monat **verbessert**
- YTD: 4 Monate × 50.000 € = 200.000 € Auswirkung

**Vergleich mit GlobalCube:**
- Die Werte sollten jetzt näher an GlobalCube sein
- 498001 ist eine echte Kostenposition und sollte enthalten sein

---

*Erstellt: TAG 188 | Autor: Claude AI*
