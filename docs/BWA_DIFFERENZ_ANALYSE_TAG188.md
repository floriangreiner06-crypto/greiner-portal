# BWA Differenz-Analyse - TAG 188

**Datum:** 2026-01-XX  
**Status:** 🔍 Analyse abgeschlossen - Differenzen identifiziert

---

## 📊 AKTUELLE SITUATION

### Monat Dezember 2025

| Position | DRIVE (API) | GlobalCube | Differenz | Status |
|----------|-------------|------------|-----------|--------|
| Betriebsergebnis | -66.147,37 € | -116.248,00 € | +50.100,63 € | ⚠️ Zu positiv |

**Problem:** DRIVE zeigt deutlich zu positives Betriebsergebnis.

### YTD bis Dezember 2025

| Position | DRIVE (API) | GlobalCube | Differenz | Status |
|----------|-------------|------------|-----------|--------|
| Betriebsergebnis | -191.157,71 € | -245.733,00 € | +54.575,29 € | ⚠️ Zu positiv |

**Problem:** DRIVE zeigt deutlich zu positives Betriebsergebnis.

---

## 🔍 IDENTIFIZIERTE PROBLEME

### 1. 498001 (Umlagekosten) - ✅ BEHOBEN

**Problem:** 498001 wurde nicht aus indirekten Kosten ausgeschlossen.

**Lösung:** 498001 wurde an allen relevanten Stellen ausgeschlossen:
- ✅ Monat indirekte Kosten
- ✅ YTD indirekte Kosten
- ✅ v2 API indirekte Kosten
- ✅ Drill-Down indirekte Kosten

**Ergebnis:** Indirekte Kosten korrigiert (50.000 €/Monat × 4 Monate = 200.000 € YTD).

---

### 2. Monat Dezember 2025 - Differenz: 50.100,63 €

**Aktuelle Werte (nach 498001-Korrektur):**
- DRIVE BE: -66.147,37 €
- GlobalCube BE: -116.248,00 €
- Differenz: +50.100,63 € (DRIVE zu positiv)

**Mögliche Ursachen:**
1. Weitere Konten die ausgeschlossen werden sollten
2. Filter-Unterschiede zwischen DRIVE und GlobalCube
3. Rundungsunterschiede

---

### 3. YTD bis Dezember 2025 - Differenz: 54.575,29 €

**Aktuelle Werte (nach 498001-Korrektur):**
- DRIVE BE: -191.157,71 €
- GlobalCube BE: -245.733,00 €
- Differenz: +54.575,29 € (DRIVE zu positiv)

**Mögliche Ursachen:**
1. Umsatz-Differenz: 14.705,88 € (Hyundai 89xxxx Konten)
2. Weitere Positionen die GlobalCube anders behandelt
3. Filter-Unterschiede

---

## 📋 NÄCHSTE SCHRITTE

### Priorität HOCH:
1. **Monat Dezember analysieren:**
   - Warum 50.100,63 € Differenz?
   - Prüfen, ob weitere Konten ausgeschlossen werden sollten
   - Vergleich mit GlobalCube Position für Position

2. **YTD analysieren:**
   - Warum 54.575,29 € Differenz?
   - Umsatz-Differenz von 14.705,88 € prüfen
   - Weitere Positionen identifizieren

### Priorität MITTEL:
3. **Dokumentation aktualisieren:**
   - 498001-Ausschluss dokumentieren
   - Alle Änderungen dokumentieren

---

## 🔧 TECHNISCHE DETAILS

### 498001-Ausschluss implementiert in:
- `api/controlling_api.py` Zeile 602 (Monat)
- `api/controlling_api.py` Zeile 1162 (YTD)
- `api/controlling_api.py` Zeile 1855, 1876, 1899 (v2 API)
- `api/controlling_api.py` Zeile 3032 (Drill-Down)

### SQL-Filter:
```sql
AND NOT (nominal_account_number = 498001)
```

---

*Erstellt: TAG 188 | Autor: Claude AI*
