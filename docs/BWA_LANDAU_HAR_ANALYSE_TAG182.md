# BWA Landau - HAR-Analyse TAG 182

**Datum:** 2026-01-12  
**HAR-Datei:** `f03_bwa_vj_vergleich_landau_weiter_aufgedrillt.har`  
**Zeitraum:** Dezember 2025 (Monat) + YTD Sep-Dez 2025  
**Standort:** Landau

---

## 📊 ERGEBNISSE

### Hauptpositionen (Cognos)

| Position | Monat | Vorjahr | YTD |
|----------|-------|---------|-----|
| Umsatzerlöse | 320.121,00 € | 175.211,00 € | 1.385.360,00 € |
| Einsatzwerte | 270.455,00 € | 127.974,00 € | 1.133.115,00 € |
| Variable Kosten | - | - | - |
| Direkte Kosten | - | - | - |
| Indirekte Kosten | - | - | - |
| Betriebsergebnis | -36.875,00 € | -39.988,00 € | -82.219,00 € |

---

### Vergleich: Cognos vs. DRIVE

| Position | Cognos | DRIVE | Differenz | % | Status |
|----------|--------|-------|-----------|---|--------|
| Umsatz | 320.121,00 € | 320.120,53 € | -0,47 € | -0,00% | ✅ |
| Einsatz | 270.455,00 € | 285.635,28 € | +15.180,28 € | +5,61% | ⚠️ |
| Variable Kosten | *berechnet* | 6.173,95 € | ? | ? | ⏳ |
| Direkte Kosten | *berechnet* | 38.723,80 € | ? | ? | ⏳ |
| Indirekte Kosten | *berechnet* | 39.304,39 € | ? | ? | ⏳ |
| Betriebsergebnis | -36.875,00 € | -49.716,89 € | -12.841,89 € | +34,83% | ❌ |

**⚠️ PROBLEM:** Einsatz-Differenz von 15.180,28 € (5,61%) führt zu falschem Betriebsergebnis!

**✅ LÖSUNG (TAG182):** Filter geändert von `6. Ziffer = '2'` zu `branch_number = 3` (wie bei Umsatz)

---

### Aufgedrillte Details

**Variable Kosten:**
- Trainingskosten: 539,00 €
- Fahrzeugkosten: 818,00 €
- Werbekosten: 120,00 €

**Direkte Kosten:**
- Personalkosten: 38.446,00 €
- Gemeinkosten: 278,00 €

**Indirekte Kosten:**
- Raumkosten: 599,00 €
- Kalk. Kosten: 14.750,00 €

---

## 📝 NOTIZEN

- HAR-Datei enthält **256 Zeilen** in Tabelle 3 (viel mehr Details als "alle Standorte")
- Betriebsergebnis YTD: **-82.219,00 €** (Cognos)
- Viele aufgedrillte Positionen vorhanden

---

## 🔍 NÄCHSTE SCHRITTE

1. ⏳ Vergleich mit DRIVE durchführen
2. ⏳ Alle Details extrahieren
3. ⏳ Differenzen analysieren
