# St-Anteil Problem Dezember - Analyse

**Datum:** 2026-01-17  
**Status:** ⚠️ **Problem identifiziert, Lösung noch offen**

---

## 🔍 Problem

Die **gleiche Implementierung** liefert unterschiedliche Ergebnisse:

| Zeitraum | DRIVE | Locosoft | Abweichung |
|----------|-------|----------|------------|
| **Januar (01.01-15.01)** | 4686 Min | 4971 Min | **-5.7%** ✅ |
| **Dezember (01.12-08.12)** | 3355 Min | 8543 Min | **-60.7%** ❌ |

---

## 📊 Datenanalyse

### Dezember (01.12-08.12)
- Positionen MIT AW: 69 (4394 Min)
- Positionen OHNE AW: 111 (6987 Min) ← **Viele nicht berücksichtigt!**
- Garantie-Positionen: 91 (5171 Min)

### Januar (01.01-15.01)
- Positionen MIT AW: 97 (6624 Min)
- Positionen OHNE AW: 202 (12027 Min) ← **Viele nicht berücksichtigt!**
- Garantie-Positionen: 187 (12957 Min)

---

## 🔧 Aktuelle Implementierung

Die Implementierung berücksichtigt Positionen OHNE AW **nur bei Garantie-Aufträgen**:

```sql
WHEN sma.ist_garantie_auftrag AND sma.auaw_minuten = 0 AND sha.anzahl_mit_aw > 0
THEN sma.dauer_minuten / NULLIF(sha.anzahl_mit_aw + sha.anzahl_ohne_aw, 0)
```

**Problem:** Im Dezember werden viele Positionen OHNE AW nicht berücksichtigt, weil sie nicht bei Garantie-Aufträgen sind.

---

## 🧪 Getestete Lösungen

### Lösung 1: Positionen OHNE AW generell berücksichtigen
**Ergebnis:** ❌ Verschlechtert die Ergebnisse
- Dezember: 3913 Min (noch -54.2% Abweichung)
- Januar: 5337 Min (jetzt +7.4% Abweichung)

### Lösung 2: 75% der Gesamt-Dauer
**Ergebnis:** ✅ Funktioniert für Dezember (8536 Min vs. 8543 Min)
**Problem:** ❌ Funktioniert nicht für Januar (13988 Min vs. 4971 Min)

---

## 💡 Mögliche Ursachen

1. **Unterschiedliche Locosoft-Logik je Zeitraum**
   - Vielleicht gibt es unterschiedliche Berechnungsregeln?
   - Oder unterschiedliche Filter?

2. **Datenqualität**
   - Vielleicht sind die Daten im Dezember anders strukturiert?
   - Oder es gibt fehlende/inkonsistente Daten?

3. **Filter-Problem**
   - Vielleicht gibt es einen Filter, der im Dezember anders wirkt?
   - Oder es gibt einen Bug in der Deduplizierung?

---

## 🎯 Nächste Schritte

1. **Weitere Analyse der Dezember-Daten**
   - Prüfe, ob es spezielle Fälle gibt
   - Prüfe, ob die Deduplizierung korrekt funktioniert

2. **Vergleich mit anderen Mechanikern**
   - Funktioniert die Implementierung für andere?
   - Oder ist es ein spezifisches Problem für Tobias?

3. **Locosoft-Dokumentation prüfen**
   - Gibt es Hinweise auf unterschiedliche Berechnungsregeln?
   - Oder auf spezielle Filter?

---

**Erstellt:** 2026-01-17  
**Status:** Problem identifiziert, Lösung noch offen
