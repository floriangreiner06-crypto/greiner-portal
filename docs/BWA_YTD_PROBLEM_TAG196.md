# BWA YTD Problem-Analyse - TAG 196

**Datum:** 2026-01-16  
**Status:** 🔍 Problem identifiziert

---

## 📊 AKTUELLE SITUATION

### YTD bis Dezember 2025

| Position | DRIVE (Analyse) | GlobalCube | Differenz | Status |
|----------|----------------|------------|-----------|--------|
| Direkte Kosten YTD | 659.134,64 € | 659.229,00 € | -94,36 € | ✅ Sehr gut |
| Indirekte Kosten YTD | 838.937,55 € | 838.944,00 € | -6,45 € | ✅ Sehr gut |
| **Betriebsergebnis YTD** | **-405.863,59 €** | **-245.733,00 €** | **-160.130,59 €** | ❌ **Massive Differenz!** |

**Problem:** DRIVE zeigt deutlich zu negatives Betriebsergebnis YTD!

---

## 🔍 IDENTIFIZIERTE PROBLEME

### 1. Betriebsergebnis YTD-Differenz: -160.130,59 €

**Aktuelle Werte:**
- DRIVE BE YTD: -405.863,59 €
- GlobalCube BE YTD: -245.733,00 €
- Differenz: -160.130,59 € (DRIVE zu negativ)

**Laut TAG 188 Dokumentation (nach 498001-Korrektur):**
- DRIVE BE YTD sollte: -191.157,71 € sein
- GlobalCube BE YTD: -245.733,00 €
- Erwartete Differenz: +54.575,29 € (DRIVE zu positiv)

**Aktuelle Situation:**
- DRIVE BE YTD: -405.863,59 € (viel schlechter als erwartet!)
- Differenz: -160.130,59 € (statt +54.575,29 €)

---

## ⚠️ WICHTIGE ERKENNTNISSE

### 1. 498001 in YTD

**Aktuelle Situation:**
- 498001 YTD: 200.000,00 € (4 Monate × 50.000 €)
- 498001 ist als **SOLL** gebucht (erhöht Kosten)
- Ist **ENTHALTEN** in indirekten Kosten YTD

**Laut TAG 188 Dokumentation:**
- 498001 sollte **AUSGESCHLOSSEN** werden aus indirekten Kosten
- SQL-Filter: `AND NOT (nominal_account_number = 498001)`
- Sollte implementiert sein in Zeile 1162

**Problem:**
- 498001 wird **NICHT ausgeschlossen** in der aktuellen Implementierung!
- Das erklärt die große Differenz!

### 2. Berechnungslogik

**Wenn 498001 ausgeschlossen würde:**
- Indirekte Kosten YTD: 638.937,55 € (838.937,55 - 200.000)
- Betriebsergebnis YTD: -205.863,59 € (-405.863,59 + 200.000)
- Differenz zu GlobalCube: +39.869,41 € (noch nicht perfekt, aber besser!)

**Aber laut TAG 188 sollte BE YTD -191.157,71 € sein:**
- Das bedeutet: Es gibt noch weitere Probleme!

---

## 🔧 LÖSUNG

### 1. 498001 aus indirekten Kosten YTD ausschließen

**Aktuelle Query (Zeile 1149):**
```sql
OR nominal_account_number BETWEEN 498000 AND 499999
```

**Sollte sein:**
```sql
OR (nominal_account_number BETWEEN 498000 AND 499999
    AND NOT (nominal_account_number = 498001))
```

**Oder explizit:**
```sql
OR (nominal_account_number BETWEEN 498000 AND 499999
    AND nominal_account_number != 498001)
```

### 2. Prüfen ob weitere Korrekturen nötig sind

Nach 498001-Ausschluss sollte BE YTD -205.863,59 € sein, aber laut TAG 188 sollte es -191.157,71 € sein. Das bedeutet:
- Differenz: -14.705,88 €
- Mögliche Ursache: Umsatz-Differenz (Hyundai 89xxxx Konten)

---

## 📋 NÄCHSTE SCHRITTE

### Priorität HOCH:
1. **498001 aus indirekten Kosten YTD ausschließen**
   - Zeile 1149 in `api/controlling_api.py` korrigieren
   - Service neu starten
   - YTD-Werte erneut prüfen

2. **Nach Korrektur analysieren:**
   - Prüfen ob BE YTD jetzt -205.863,59 € ist
   - Prüfen ob weitere Korrekturen nötig sind
   - Umsatz-Differenz analysieren (14.705,88 €)

---

*Erstellt: TAG 196 | Autor: Claude AI*
