# BWA-Vergleich: Cognos (HAR) vs. DRIVE - TAG 182

**Datum:** 2026-01-12  
**Zeitraum:** Dezember 2025 (Monat)  
**Standort:** Alle Standorte (aus HAR)

---

## 📊 ERGEBNISSE

### Cognos-Werte (aus HAR-Datei)

**Extrahiert aus:** `f03_bwa_vj_vergleich_alle_beriebe_angehackt.har`

| Position | Wert (€) |
|----------|----------|
| Umsatzerlöse | 2.190.826,00 |
| Einsatzwerte | 1.862.668,00 |
| Variable Kosten | 69.374,00 |
| Direkte Kosten | 189.866,00 |
| Indirekte Kosten | 185.059,00 |
| Betriebsergebnis | -116.140,00 |

**Hinweis:** HAR-Datei enthält alle Standorte zusammen, nicht aufgedrillt.

---

### DRIVE-Werte (Dezember 2025, alle Standorte)

| Position | Wert (€) |
|----------|----------|
| Umsatz | 2.190.825,64 |
| Einsatz | 1.862.667,99 |
| Variable Kosten | 0,00 |
| Direkte Kosten | 0,00 |
| Indirekte Kosten | 0,00 |
| Betriebsergebnis | -116.140,40 |

**Hinweis:** DRIVE zeigt 0,00 für Kosten, was auf einen Filter-Fehler hindeutet.

---

## 🔍 VERGLEICH

| Position | Cognos | DRIVE | Differenz | % |
|----------|--------|-------|-----------|---|
| Umsatzerlöse | 2.190.826,00 | 2.190.825,64 | -0,36 | 0,00% |
| Einsatzwerte | 1.862.668,00 | 1.862.667,99 | -0,01 | 0,00% |
| Variable Kosten | 69.374,00 | 0,00 | -69.374,00 | -100% |
| Direkte Kosten | 189.866,00 | 0,00 | -189.866,00 | -100% |
| Indirekte Kosten | 185.059,00 | 0,00 | -185.059,00 | -100% |
| Betriebsergebnis | -116.140,00 | -116.140,40 | -0,40 | 0,00% |

---

## ⚠️ PROBLEME

1. **Umsatz/Einsatz:** ✅ Fast identisch (0,36 € / 0,01 € Differenz)
2. **Kosten:** ❌ DRIVE zeigt 0,00 für alle Kosten-Positionen
3. **Betriebsergebnis:** ✅ Fast identisch (0,40 € Differenz)

**Ursache:** DRIVE API gibt für "alle Standorte" möglicherweise keine Kosten zurück, oder Filter ist falsch.

---

## 🎯 NÄCHSTE SCHRITTE

1. ✅ HAR-Datei analysiert
2. ✅ HTML extrahiert
3. ✅ BWA-Werte geparst
4. ⏳ **DRIVE API für "alle Standorte" prüfen** (warum 0,00 für Kosten?)
5. ⏳ **Einzelne Standorte vergleichen** (Landau, Deggendorf Opel, Deggendorf Hyundai)
6. ⏳ **Drill-Down auf Kosten-Positionen** (um Details zu sehen)

---

## 📝 NOTIZEN

- HAR-Datei enthält **alle Standorte zusammen**
- Cognos zeigt korrekte Werte für alle Positionen
- DRIVE zeigt 0,00 für Kosten bei "alle Standorte"
- Umsatz/Einsatz stimmen überein (✅)
- Betriebsergebnis stimmt überein (✅)

**Fazit:** DRIVE-Berechnung für Kosten bei "alle Standorte" muss korrigiert werden.
